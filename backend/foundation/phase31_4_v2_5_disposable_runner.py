"""Crash-safe disposable evidence runner for Phase 31.4 V2.5.

The runner deliberately separates resource allocation from PostgreSQL
startup/readiness.  An authorization is consumed before any resource command,
and every intended or observed resource is atomically persisted before the
next step.  Recovery is cleanup-only: a process reconstructed from a manifest
cannot continue the business run.

Nothing in this module is specific to a numbered retry.  Historical runs are
immutable and collide closed through their existing evidence roots.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import traceback
from typing import Any, Callable, Mapping, Protocol, Sequence

from .phase31_4_postgres18_environment import (
    POSTGRES_IMAGE_ID,
    POSTGRES_IMMUTABLE_IMAGE,
)
from .phase31_4_integrity_generations import (
    IntegrityGenerationError,
    verify_v25_current_integrity,
)
from .phase31_4_v2_5_precreation_integrity import _safe_run_slug


MANIFEST_SCHEMA = "phase31.4-v2.5-disposable-run-resource-manifest/v1"
CONSUMPTION_SCHEMA = "phase31.4-v2.5-one-shot-authorization-consumption/v1"
DIAGNOSTIC_CLASSIFICATION = "RUNNER_ENVIRONMENT_DIAGNOSTIC"
EVIDENCE_EXECUTION = "DISPOSABLE_EVIDENCE_RUN"
POSTGRES_VERSION_PREFIX = "postgres (PostgreSQL) 18.6"
MANIFEST_NAME = "RESOURCE_MANIFEST.json"
CONSUMPTION_NAME = "AUTHORIZATION_CONSUMPTION.json"
DEFAULT_REGISTRY = Path("docs/governance/evidence/authorization_consumptions")
PROTECTED_RUNNER_PATHS = (
    "backend/foundation/phase31_4_v2_5_disposable_runner.py",
    "docs/governance/tools/phase31_4_v2_5_disposable_runner.py",
)

RUN_LABEL = "io.isosmart.phase31-4.run-slug"
AUTH_LABEL = "io.isosmart.phase31-4.authorization-sha256"
ROLE_LABEL = "io.isosmart.phase31-4.resource-role"
PRECREATION_REQUIRED_ROLES = frozenset({"adminapps", "isosmart"})


class RunState(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    ALLOCATING = "ALLOCATING"
    RESOURCES_ALLOCATED = "RESOURCES_ALLOCATED"
    BOOTSTRAPPING = "BOOTSTRAPPING"
    READY = "READY"
    PRECREATION_RUNNING = "PRECREATION_RUNNING"
    PRECREATION_PASS = "PRECREATION_PASS"
    STAGE_EXT_RUNNING = "STAGE_EXT_RUNNING"
    STAGE_EXT_PASS = "STAGE_EXT_PASS"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    TEARDOWN_COMPLETE = "TEARDOWN_COMPLETE"


EVIDENCE_TRANSITIONS: Mapping[RunState, frozenset[RunState]] = {
    RunState.AUTHORIZED: frozenset({RunState.ALLOCATING, RunState.FAILED}),
    RunState.ALLOCATING: frozenset({RunState.RESOURCES_ALLOCATED, RunState.FAILED}),
    RunState.RESOURCES_ALLOCATED: frozenset({RunState.BOOTSTRAPPING, RunState.FAILED}),
    RunState.BOOTSTRAPPING: frozenset({RunState.READY, RunState.FAILED}),
    RunState.READY: frozenset({RunState.PRECREATION_RUNNING, RunState.FAILED}),
    RunState.PRECREATION_RUNNING: frozenset({RunState.PRECREATION_PASS, RunState.FAILED}),
    RunState.PRECREATION_PASS: frozenset({RunState.STAGE_EXT_RUNNING, RunState.FAILED}),
    RunState.STAGE_EXT_RUNNING: frozenset({RunState.STAGE_EXT_PASS, RunState.FAILED}),
    RunState.STAGE_EXT_PASS: frozenset({RunState.COMPLETED, RunState.FAILED}),
    RunState.COMPLETED: frozenset({RunState.TEARDOWN_COMPLETE, RunState.FAILED}),
    RunState.FAILED: frozenset({RunState.TEARDOWN_COMPLETE}),
    RunState.TEARDOWN_COMPLETE: frozenset(),
}

DIAGNOSTIC_TRANSITIONS = dict(EVIDENCE_TRANSITIONS)
DIAGNOSTIC_TRANSITIONS[RunState.READY] = frozenset(
    {
        RunState.PRECREATION_RUNNING,
        RunState.COMPLETED,
        RunState.FAILED,
    }
)


class RunnerError(RuntimeError):
    """Fail-closed error with a stable forensic classification."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        domain: str = "DISPOSABLE_EXECUTION_TOOLING_BLOCKER",
        step: str | None = None,
        command: Sequence[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.domain = domain
        self.step = step
        self.command = tuple(command) if command else None


class StateTransitionError(RunnerError):
    def __init__(self, current: RunState, requested: RunState) -> None:
        super().__init__(
            "INVALID_STATE_TRANSITION",
            f"state transition {current.value} -> {requested.value} is not allowed",
            step="state_transition",
        )


class DatabaseAuthenticationError(RuntimeError):
    pass


class DatabaseReadinessTimeout(RuntimeError):
    pass


class DatabaseQueryError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandExecutor(Protocol):
    def run(self, argv: Sequence[str]) -> CommandResult: ...


class DatabaseProbe(Protocol):
    def wait_for_select_one(
        self,
        *,
        host: str,
        port: int,
        database: str,
        user: str,
        timeout_seconds: float,
    ) -> int: ...


class SubprocessExecutor:
    """Shell-free command execution used by an explicitly authorized run."""

    def run(self, argv: Sequence[str]) -> CommandResult:
        completed = subprocess.run(
            tuple(argv),
            check=False,
            capture_output=True,
            text=True,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class PsycopgDatabaseProbe:
    """Prove a host-port connection and ``SELECT 1`` independently of Podman."""

    def __init__(
        self,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._monotonic = monotonic
        self._sleep = sleep

    def wait_for_select_one(
        self,
        *,
        host: str,
        port: int,
        database: str,
        user: str,
        timeout_seconds: float,
    ) -> int:
        try:
            import psycopg2
        except ImportError as exc:  # pragma: no cover - environment-specific
            raise RunnerError(
                "POSTGRES_CLIENT_UNAVAILABLE",
                "psycopg2 is unavailable for the PostgreSQL readiness proof",
                step="postgres_readiness",
            ) from exc

        deadline = self._monotonic() + timeout_seconds
        last_error: BaseException | None = None
        while self._monotonic() < deadline:
            connection = None
            try:
                connection = psycopg2.connect(
                    dbname=database,
                    user=user,
                    host=host,
                    port=port,
                    connect_timeout=max(1, min(3, int(timeout_seconds))),
                    sslmode="disable",
                )
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    row = cursor.fetchone()
                if row != (1,):
                    raise DatabaseQueryError(f"unexpected SELECT 1 result: {row!r}")
                return 1
            except psycopg2.OperationalError as exc:
                message = str(exc).lower()
                if getattr(exc, "pgcode", None) == "28P01" or "authentication failed" in message:
                    raise DatabaseAuthenticationError(str(exc)) from exc
                last_error = exc
                self._sleep(0.25)
            except psycopg2.Error as exc:
                raise DatabaseQueryError(str(exc)) from exc
            finally:
                if connection is not None:
                    connection.close()
        raise DatabaseReadinessTimeout(
            f"PostgreSQL readiness timed out after {timeout_seconds:g}s; "
            f"last error: {last_error}"
        )


@dataclass(frozen=True)
class RunInputs:
    repository_root: Path
    run_id: str
    authorization_artifact: Path
    expected_authorization_sha256: str
    current_integrity_generation: str
    expected_integrity_sha256: str
    evidence_root: Path
    execution_kind: str = EVIDENCE_EXECUTION
    consumption_registry: Path | None = None
    validation_attempt: int | None = None
    readiness_timeout_seconds: float = 60.0


@dataclass(frozen=True)
class VerifiedAuthorization:
    document: Mapping[str, Any]
    authorization_path: Path
    authorization_sha256: str
    integrity_path: Path
    integrity_sha256: str
    integrity_document: Mapping[str, Any]
    evidence_root: Path
    run_slug: str
    consumption_registry: Path
    integrity_reconciliation_required: bool


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def canonical_run_slug(run_id: str) -> str:
    """Return the only default directory slug for a run ID."""
    if not isinstance(run_id, str) or not run_id.strip():
        raise RunnerError("INVALID_RUN_ID", "run ID must be a non-empty string")
    if "/" in run_id or "\\" in run_id or "\x00" in run_id:
        raise RunnerError("INVALID_RUN_ID", "run ID contains a path separator")
    # PRECREATION already owns the repository's canonical transformation.  Do
    # not let allocation/bootstrap invent a second spelling of the run path.
    slug = _safe_run_slug(run_id.strip())
    if not slug or slug in {".", ".."} or len(slug) > 180:
        raise RunnerError("INVALID_RUN_SLUG", "derived run slug is invalid")
    return slug


def _validate_explicit_slug(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,179}", value):
        raise RunnerError("INVALID_RUN_SLUG", "authorization canonical_run_slug is invalid")
    if value in {".", ".."}:
        raise RunnerError("INVALID_RUN_SLUG", "authorization canonical_run_slug is invalid")
    return value


def _resolve_from(root: Path, value: Path | str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else root / path).resolve()


def _relative_display(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _require_sha256(value: str, label: str) -> str:
    normalized = value.lower() if isinstance(value, str) else ""
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        raise RunnerError("INVALID_EXPECTED_SHA256", f"{label} must be 64 lowercase hex characters")
    return normalized


def _authorization_candidates(evidence_root: Path) -> list[Path]:
    """Return immutable authorization material without treating it as execution."""
    if not evidence_root.is_dir():
        return []
    candidates = [
        path for path in evidence_root.iterdir()
        if path.is_file() and "AUTHORIZATION" in path.name.upper() and path.suffix == ".json"
    ]
    versioned = evidence_root / "authorizations"
    if versioned.is_dir():
        candidates.extend(path for path in versioned.iterdir() if path.is_file() and path.suffix == ".json")
    return sorted({path.resolve() for path in candidates})


def _supersedes(document: Mapping[str, Any], *, authorization_id: str | None,
                authorization_sha256: str, authorization_path: Path) -> bool:
    reference = document.get("supersedes")
    if not reference:
        return False
    values: set[str] = set()
    if isinstance(reference, str):
        values.add(reference)
    elif isinstance(reference, Mapping):
        values.update(str(value) for value in reference.values() if value)
    elif isinstance(reference, Sequence):
        values.update(str(value) for value in reference if value)
    return bool(values & {str(authorization_id or ""), authorization_sha256,
                          authorization_path.name, authorization_path.as_posix()})


def _reject_if_superseded(evidence_root: Path, selected_path: Path,
                          selected_document: Mapping[str, Any], selected_sha: str) -> None:
    index_path = evidence_root / "AUTHORIZATION_INDEX.json"
    if index_path.is_file():
        index = _load_object(index_path, "AUTHORIZATION_INVALID")
        entries = index.get("authorizations", [])
        if not isinstance(entries, list):
            raise RunnerError("AUTHORIZATION_INVALID", "authorization index entries are malformed")
        for entry in entries:
            if (isinstance(entry, Mapping)
                    and entry.get("authorization_sha256") == selected_sha
                    and entry.get("status") == "SUPERSEDED"):
                raise RunnerError("AUTHORIZATION_SUPERSEDED", "authorization is superseded in the immutable run index")
    selected_id = selected_document.get("authorization_id")
    for candidate in _authorization_candidates(evidence_root):
        if candidate == selected_path.resolve():
            continue
        try:
            successor = _load_object(candidate, "AUTHORIZATION_INVALID")
        except RunnerError:
            continue
        if successor.get("run_id") == selected_document.get("run_id") and _supersedes(
            successor, authorization_id=str(selected_id) if selected_id else None,
            authorization_sha256=selected_sha, authorization_path=selected_path,
        ):
            raise RunnerError("AUTHORIZATION_SUPERSEDED", f"authorization was superseded by {candidate.name}")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_json(path: Path, payload: Mapping[str, Any], *, exclusive: bool = False) -> None:
    """Durably replace JSON, or create it exactly once when ``exclusive``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if exclusive:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            os.close(descriptor)
        _fsync_directory(path.parent)
        return

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _load_object(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(code, f"unreadable JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise RunnerError(code, f"JSON artifact is not an object: {path}")
    return value


def _auth_evidence_root(document: Mapping[str, Any]) -> str | None:
    direct = document.get("evidence_root")
    if isinstance(direct, str):
        return direct
    for key in ("evidence_policy", "evidence"):
        section = document.get(key)
        if isinstance(section, Mapping) and isinstance(section.get("root"), str):
            return str(section["root"])
    return None


def _auth_integrity(document: Mapping[str, Any]) -> tuple[str | None, str | None]:
    section = document.get("integrity")
    if isinstance(section, Mapping):
        reference = section.get("artifact_path") or section.get("reference")
        digest = section.get("sha256")
        if isinstance(reference, str) or isinstance(digest, str):
            return (
                reference if isinstance(reference, str) else None,
                digest if isinstance(digest, str) else None,
            )
    reference = document.get("v4_reference")
    digest = document.get("v4_sha256")
    return (
        reference if isinstance(reference, str) else None,
        digest if isinstance(digest, str) else None,
    )


def _verify_integrity_contents(root: Path, document: Mapping[str, Any]) -> set[str]:
    sources = document.get("sources")
    migrations = document.get("migration_file_sha256", {})
    if not isinstance(sources, list) or not sources or not isinstance(migrations, Mapping):
        raise RunnerError("INTEGRITY_ARTIFACT_INVALID", "integrity artifact has no source inventory")
    protected: set[str] = set()
    for entry in sources:
        if not isinstance(entry, Mapping):
            raise RunnerError("INTEGRITY_ARTIFACT_INVALID", "invalid protected source entry")
        relative = entry.get("path")
        digest = entry.get("sha256")
        if not isinstance(relative, str) or relative in protected or not isinstance(digest, str):
            raise RunnerError("INTEGRITY_ARTIFACT_INVALID", "invalid or duplicate protected source")
        path = _resolve_from(root, relative)
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise RunnerError("INTEGRITY_ARTIFACT_INVALID", "protected source escapes repository") from exc
        if not path.is_file() or file_sha256(path) != digest:
            raise RunnerError("CURRENT_INTEGRITY_MISMATCH", f"protected source drift: {relative}")
        protected.add(relative)
    for relative, digest in migrations.items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise RunnerError("INTEGRITY_ARTIFACT_INVALID", "invalid migration integrity entry")
        path = _resolve_from(root, relative)
        if not path.is_file() or file_sha256(path) != digest:
            raise RunnerError("CURRENT_INTEGRITY_MISMATCH", f"migration drift: {relative}")
    return protected


def verify_authorization(inputs: RunInputs) -> VerifiedAuthorization:
    """Verify all immutable inputs without consuming the authorization."""
    root = inputs.repository_root.resolve()
    evidence_base = (root / "docs/governance/evidence").resolve()
    raw_evidence_root = (
        inputs.evidence_root
        if inputs.evidence_root.is_absolute()
        else root / inputs.evidence_root
    )
    if raw_evidence_root.is_symlink():
        raise RunnerError("EVIDENCE_ROOT_SYMLINK", "evidence root may not be a symlink")
    authorization = _resolve_from(root, inputs.authorization_artifact)
    evidence_root = _resolve_from(root, inputs.evidence_root)
    expected_auth = _require_sha256(inputs.expected_authorization_sha256, "authorization SHA-256")
    expected_integrity = _require_sha256(inputs.expected_integrity_sha256, "integrity SHA-256")

    for path, label in ((authorization, "authorization"), (evidence_root, "evidence root")):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise RunnerError("PATH_OUTSIDE_REPOSITORY", f"{label} is outside the repository") from exc
    try:
        evidence_root.relative_to(evidence_base)
    except ValueError as exc:
        raise RunnerError(
            "EVIDENCE_ROOT_OUTSIDE_GOVERNANCE_TREE",
            "evidence root must be under docs/governance/evidence",
        ) from exc
    if not authorization.is_file():
        raise RunnerError("AUTHORIZATION_NOT_FOUND", f"authorization does not exist: {authorization}")
    observed_auth = file_sha256(authorization)
    if observed_auth != expected_auth:
        raise RunnerError("AUTHORIZATION_SHA_MISMATCH", "authorization SHA-256 does not match")

    document = _load_object(authorization, "AUTHORIZATION_INVALID")
    # Supersession is terminal and takes precedence over stale fields in the
    # historical artifact, so callers receive the precise governance reason.
    _reject_if_superseded(evidence_root, authorization, document, observed_auth)
    authorization_id = document.get("authorization_id")
    if authorization_id is not None:
        required_identity = {
            "authorization_id": authorization_id,
            "run_id": document.get("run_id"),
            "issued_at": document.get("issued_at"),
        }
        if not all(isinstance(value, str) and value.strip() for value in required_identity.values()):
            raise RunnerError("AUTHORIZATION_INVALID", "versioned authorization identity is incomplete")
        if document.get("authorization_sha256") not in (None, observed_auth):
            raise RunnerError("AUTHORIZATION_INVALID", "authorization self-identity SHA does not match")
        generation = document.get("baseline_generation") or (document.get("integrity") or {}).get("generation")
        baseline_sha = document.get("baseline_sha256") or (document.get("integrity") or {}).get("sha256")
        if not generation or not baseline_sha:
            raise RunnerError("AUTHORIZATION_INVALID", "versioned authorization baseline identity is incomplete")
    if inputs.execution_kind not in {EVIDENCE_EXECUTION, DIAGNOSTIC_CLASSIFICATION}:
        raise RunnerError("INVALID_EXECUTION_KIND", "execution kind is not supported")
    if (
        inputs.execution_kind == DIAGNOSTIC_CLASSIFICATION
        and inputs.validation_attempt not in {1, 2, 3}
    ):
        raise RunnerError(
            "INVALID_VALIDATION_ATTEMPT",
            "runner diagnostic validation attempt must be between 1 and 3",
        )
    if inputs.execution_kind == DIAGNOSTIC_CLASSIFICATION:
        authorized_attempt = document.get("validation_attempt")
        if authorized_attempt is not None and authorized_attempt != inputs.validation_attempt:
            raise RunnerError(
                "AUTHORIZATION_VALIDATION_ATTEMPT_MISMATCH",
                "diagnostic validation attempt does not match authorization",
            )
    if document.get("run_id") != inputs.run_id:
        raise RunnerError("AUTHORIZATION_RUN_ID_MISMATCH", "authorization run ID does not match")
    status = document.get("authorization_status")
    required_status = (
        "RUNNER_ENVIRONMENT_DIAGNOSTIC_AUTHORIZED"
        if inputs.execution_kind == DIAGNOSTIC_CLASSIFICATION
        else "DISPOSABLE_EVIDENCE_RUN_AUTHORIZED"
    )
    if status != required_status:
        raise RunnerError("AUTHORIZATION_STATUS_INVALID", f"authorization status must be {required_status}")
    if document.get("run_executed") not in (None, "NO", False):
        raise RunnerError("AUTHORIZATION_ALREADY_CONSUMED", "authorization declares a prior execution")
    if document.get("one_shot") is False:
        raise RunnerError("AUTHORIZATION_STATUS_INVALID", "authorization must be one-shot")
    if document.get("consumed") not in (None, False, "NO"):
        raise RunnerError("AUTHORIZATION_ALREADY_CONSUMED", "authorization declares consumed state")
    authorized_kind = document.get("execution_kind")
    if authorized_kind is not None and authorized_kind != inputs.execution_kind:
        raise RunnerError("AUTHORIZATION_EXECUTION_KIND_MISMATCH", "execution kind does not match")

    derived_slug = canonical_run_slug(inputs.run_id)
    explicit_slug = document.get("canonical_run_slug")
    if explicit_slug is not None:
        run_slug = _validate_explicit_slug(explicit_slug)
        if run_slug != derived_slug:
            raise RunnerError(
                "CANONICAL_RUN_SLUG_MISMATCH",
                "authorization canonical_run_slug differs from the run ID slug",
            )
    else:
        run_slug = derived_slug
    if evidence_root.name != run_slug:
        raise RunnerError(
            "CANONICAL_EVIDENCE_ROOT_MISMATCH",
            f"evidence root must end in canonical run slug {run_slug}",
        )
    declared_root = _auth_evidence_root(document)
    if declared_root is None or _resolve_from(root, declared_root) != evidence_root:
        raise RunnerError("AUTHORIZATION_EVIDENCE_ROOT_MISMATCH", "authorization evidence root differs")

    reference, authorized_integrity_sha = _auth_integrity(document)
    if reference is None or authorized_integrity_sha is None:
        raise RunnerError("AUTHORIZATION_INTEGRITY_MISSING", "authorization has no integrity authority")
    integrity_path = _resolve_from(root, reference)
    try:
        integrity_path.relative_to(root)
    except ValueError as exc:
        raise RunnerError("PATH_OUTSIDE_REPOSITORY", "integrity artifact is outside repository") from exc
    if not integrity_path.is_file():
        raise RunnerError("INTEGRITY_ARTIFACT_NOT_FOUND", "current integrity artifact does not exist")
    observed_integrity = file_sha256(integrity_path)
    if observed_integrity != expected_integrity or observed_integrity != authorized_integrity_sha:
        raise RunnerError("INTEGRITY_SHA_MISMATCH", "current integrity SHA-256 does not match authority")
    integrity_document = _load_object(integrity_path, "INTEGRITY_ARTIFACT_INVALID")
    generations = {
        integrity_document.get("generation"),
        integrity_document.get("generation_id"),
    }
    if inputs.current_integrity_generation not in generations:
        raise RunnerError("INTEGRITY_GENERATION_MISMATCH", "current integrity generation differs")
    protected = _verify_integrity_contents(root, integrity_document)
    if integrity_document.get("schema") in {
        "phase31.4-v2.5-current-source-integrity/v4",
        "phase31.4-v2.5-current-source-integrity/v5",
    }:
        try:
            verify_v25_current_integrity(root, integrity_document)
        except IntegrityGenerationError as exc:
            raise RunnerError(
                "CURRENT_INTEGRITY_MISMATCH",
                f"current internal integrity verification failed: {exc}",
            ) from exc
    missing_runner_sources = set(PROTECTED_RUNNER_PATHS) - protected
    reconciliation_required = bool(missing_runner_sources)

    registry = _resolve_from(root, inputs.consumption_registry or DEFAULT_REGISTRY)
    try:
        registry.relative_to(evidence_base)
    except ValueError as exc:
        raise RunnerError(
            "CONSUMPTION_REGISTRY_OUTSIDE_GOVERNANCE_TREE",
            "authorization consumption registry must be under governance evidence",
        ) from exc
    registry_marker = registry / f"{observed_auth}.json"
    root_marker = evidence_root / CONSUMPTION_NAME
    if registry_marker.exists() or root_marker.exists():
        raise RunnerError("AUTHORIZATION_ALREADY_CONSUMED", "one-shot authorization was already consumed")

    if evidence_root.exists():
        if not evidence_root.is_dir():
            raise RunnerError(
                "EVIDENCE_ROOT_COLLISION",
                "evidence root exists and is not a directory",
            )
        if (evidence_root / MANIFEST_NAME).exists():
            raise RunnerError(
                "EXECUTION_ALREADY_STARTED",
                "evidence root contains a prior resource manifest",
            )
        allowed = set(_authorization_candidates(evidence_root))
        allowed.add(authorization.resolve())
        metadata_names = {"AUTHORIZATION_INDEX.json", "authorization_index.json"}
        collisions = [path for path in evidence_root.iterdir()
                      if path.resolve() not in allowed
                      and path.name not in metadata_names
                      and path.name != "authorizations"]
        if collisions:
            raise RunnerError(
                "EVIDENCE_ROOT_COLLISION",
                "evidence root represents a prior or foreign execution",
            )
    if inputs.execution_kind == EVIDENCE_EXECUTION and reconciliation_required:
        raise RunnerError(
            "RUNNER_SOURCE_NOT_IN_INTEGRITY_GENERATION",
            "material runner sources require an approved successor integrity generation",
        )
    return VerifiedAuthorization(
        document=document,
        authorization_path=authorization,
        authorization_sha256=observed_auth,
        integrity_path=integrity_path,
        integrity_sha256=observed_integrity,
        integrity_document=integrity_document,
        evidence_root=evidence_root,
        run_slug=run_slug,
        consumption_registry=registry,
        integrity_reconciliation_required=reconciliation_required,
    )


def _resource_prefix(run_slug: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "_", run_slug.lower()).strip("_")
    suffix = sha256(run_slug.encode("utf-8")).hexdigest()[:10]
    return f"p314_{stem[:34].rstrip('_')}_{suffix}"


def _database_name(run_slug: str, role: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "_", run_slug.lower()).strip("_")
    digest = sha256(f"{run_slug}\0{role}".encode("utf-8")).hexdigest()[:10]
    return f"p314_{stem[:20].rstrip('_')}_{role[:20]}_{digest}"


def _safe_role(role: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,30}", role):
        raise RunnerError("INVALID_RESOURCE_ROLE", f"invalid resource role: {role!r}")
    return role


class DisposableEvidenceRunner:
    """One-process authorized runner plus cleanup-only crash recovery."""

    def __init__(
        self,
        inputs: RunInputs,
        *,
        executor: CommandExecutor | None = None,
        database_probe: DatabaseProbe | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.inputs = inputs
        self.executor = executor or SubprocessExecutor()
        self.database_probe = database_probe or PsycopgDatabaseProbe()
        self.clock = clock
        self.verified: VerifiedAuthorization | None = None
        self._manifest: dict[str, Any] | None = None
        self._recovery_only = False

    @property
    def evidence_root(self) -> Path:
        if self.verified is not None:
            return self.verified.evidence_root
        return _resolve_from(self.inputs.repository_root.resolve(), self.inputs.evidence_root)

    @property
    def manifest_path(self) -> Path:
        return self.evidence_root / MANIFEST_NAME

    @property
    def manifest(self) -> Mapping[str, Any]:
        if self._manifest is None:
            raise RunnerError("RUN_NOT_PREPARED", "runner has no persisted manifest")
        return self._manifest

    def _now(self) -> str:
        return self.clock().astimezone(timezone.utc).isoformat()

    def _persist(self) -> None:
        if self._manifest is None:
            raise RunnerError("RUN_NOT_PREPARED", "runner has no manifest to persist")
        self._manifest["manifest_revision"] = self._manifest.get("manifest_revision", 0) + 1
        self._manifest["updated_at"] = self._now()
        atomic_write_json(self.manifest_path, self._manifest)

    def _assert_precreation_ready(self) -> None:
        """Fail closed unless READY represents a durable, usable environment."""
        manifest = self.manifest
        resources = manifest.get("resources")
        if manifest.get("allocation_state") != "SUCCEEDED":
            raise RunnerError(
                "PRECREATION_READINESS_INVARIANT_FAILURE",
                "PRECREATION requires successfully allocated resources",
                step="state_transition",
            )
        if not isinstance(resources, dict) or not resources:
            raise RunnerError(
                "PRECREATION_READINESS_INVARIANT_FAILURE",
                "PRECREATION requires at least one persisted PostgreSQL resource",
                step="state_transition",
            )
        missing_roles = PRECREATION_REQUIRED_ROLES - set(resources)
        if missing_roles:
            raise RunnerError(
                "PRECREATION_READINESS_INVARIANT_FAILURE",
                f"PRECREATION requires ready resources for: {', '.join(sorted(missing_roles))}",
                step="state_transition",
            )
        host_ports = manifest.get("host_ports")
        database_names = manifest.get("database_names")
        if (
            not isinstance(host_ports, list)
            or len(host_ports) != len(resources)
            or len(set(host_ports)) != len(host_ports)
            or not isinstance(database_names, list)
            or len(database_names) != len(resources)
            or len(set(database_names)) != len(database_names)
        ):
            raise RunnerError(
                "PRECREATION_READINESS_INVARIANT_FAILURE",
                "PRECREATION requires complete, unique persisted database bindings",
                step="state_transition",
            )
        for role, resource in resources.items():
            required = {
                "volume_status": "CREATED",
                "network_status": "CREATED",
                "container_status": "RUNNING",
                "postgresql_status": "READY",
                "connection_result": "PASS",
                "select_one_result": 1,
            }
            mismatches = [
                key for key, expected in required.items()
                if resource.get(key) != expected
            ]
            if (
                resource.get("host_port") not in host_ports
                or resource.get("database_name") not in database_names
                or not str(resource.get("observed_postgresql_version", "")).startswith(
                    POSTGRES_VERSION_PREFIX
                )
            ):
                mismatches.append("persisted_database_readiness")
            if mismatches:
                raise RunnerError(
                    "PRECREATION_READINESS_INVARIANT_FAILURE",
                    f"PRECREATION readiness is incomplete for {role}: {', '.join(mismatches)}",
                    step="state_transition",
                )
        try:
            persisted = _load_object(self.manifest_path, "RESOURCE_MANIFEST_INVALID")
        except (OSError, RunnerError) as exc:
            raise RunnerError(
                "PRECREATION_READINESS_INVARIANT_FAILURE",
                "PRECREATION requires a readable atomic resource manifest",
                step="state_transition",
            ) from exc
        if (
            persisted.get("current_state") != RunState.READY.value
            or persisted.get("manifest_revision") != manifest.get("manifest_revision")
            or persisted.get("resources") != resources
        ):
            raise RunnerError(
                "PRECREATION_READINESS_INVARIANT_FAILURE",
                "PRECREATION requires the READY environment manifest to be durably persisted",
                step="state_transition",
            )

    def _transition(self, requested: RunState, *, reason: str) -> None:
        current = RunState(str(self.manifest["current_state"]))
        transitions = (
            DIAGNOSTIC_TRANSITIONS
            if self.manifest["execution_kind"] == DIAGNOSTIC_CLASSIFICATION
            else EVIDENCE_TRANSITIONS
        )
        if requested not in transitions[current]:
            raise StateTransitionError(current, requested)
        if current == RunState.READY and requested == RunState.PRECREATION_RUNNING:
            self._assert_precreation_ready()
        self._manifest["state_transitions"].append(
            {
                "sequence": len(self._manifest["state_transitions"]) + 1,
                "from": current.value,
                "to": requested.value,
                "reason": reason,
                "at": self._now(),
                "run_id": self._manifest["run_id"],
                "run_slug": self._manifest["run_slug"],
                "execution_kind": self._manifest["execution_kind"],
                "validation_attempt": self._manifest["validation_attempt"],
            }
        )
        self._manifest["current_state"] = requested.value
        if requested != RunState.TEARDOWN_COMPLETE:
            self._manifest["execution_state"] = requested.value
        self._manifest["last_confirmed_state"] = requested.value
        self._persist()

    def prepare(self) -> Mapping[str, Any]:
        if self._manifest is not None:
            raise RunnerError("RUN_ALREADY_PREPARED", "runner instance is single-use")
        verified = verify_authorization(self.inputs)
        self.verified = verified
        verified.evidence_root.mkdir(parents=True, exist_ok=True)
        consumed_at = self._now()
        consumption = {
            "schema": CONSUMPTION_SCHEMA,
            "run_id": self.inputs.run_id,
            "run_slug": verified.run_slug,
            "execution_kind": self.inputs.execution_kind,
            "authorization_path": _relative_display(
                self.inputs.repository_root.resolve(), verified.authorization_path
            ),
            "authorization_sha256": verified.authorization_sha256,
            "evidence_root": _relative_display(
                self.inputs.repository_root.resolve(), verified.evidence_root
            ),
            "consumed_at": consumed_at,
            "one_shot": True,
        }
        registry_marker = verified.consumption_registry / f"{verified.authorization_sha256}.json"
        try:
            atomic_write_json(registry_marker, consumption, exclusive=True)
        except FileExistsError as exc:
            raise RunnerError(
                "AUTHORIZATION_ALREADY_CONSUMED", "one-shot authorization was already consumed"
            ) from exc
        try:
            atomic_write_json(verified.evidence_root / CONSUMPTION_NAME, consumption, exclusive=True)
        except FileExistsError as exc:
            raise RunnerError(
                "AUTHORIZATION_ALREADY_CONSUMED",
                "authorization consumption exists in the evidence root",
            ) from exc

        self._manifest = {
            "schema": MANIFEST_SCHEMA,
            "manifest_revision": 0,
            "run_id": self.inputs.run_id,
            "run_slug": verified.run_slug,
            "execution_kind": self.inputs.execution_kind,
            "validation_attempt": self.inputs.validation_attempt,
            "evidence_root": _relative_display(
                self.inputs.repository_root.resolve(), verified.evidence_root
            ),
            "authorization": {
                "artifact_path": _relative_display(
                    self.inputs.repository_root.resolve(), verified.authorization_path
                ),
                "sha256": verified.authorization_sha256,
                "consumed": True,
                "consumed_at": consumed_at,
                "registry_record": _relative_display(
                    self.inputs.repository_root.resolve(), registry_marker
                ),
            },
            "integrity": {
                "artifact_path": _relative_display(
                    self.inputs.repository_root.resolve(), verified.integrity_path
                ),
                "generation": self.inputs.current_integrity_generation,
                "sha256": verified.integrity_sha256,
                "runner_sources_protected": not verified.integrity_reconciliation_required,
                "reconciliation_required": verified.integrity_reconciliation_required,
            },
            "approved_postgres": {
                "image": POSTGRES_IMMUTABLE_IMAGE,
                "image_id": POSTGRES_IMAGE_ID,
                "version": "PostgreSQL 18.6",
            },
            "created_at": consumed_at,
            "updated_at": consumed_at,
            "current_state": RunState.AUTHORIZED.value,
            "execution_state": RunState.AUTHORIZED.value,
            "teardown_state": "NOT_STARTED",
            "last_confirmed_state": RunState.AUTHORIZED.value,
            "allocation_state": "NOT_STARTED",
            "business_outcome": "PENDING",
            "runner_step": "authorization_consumed",
            "state_transitions": [
                {
                    "sequence": 1,
                    "from": None,
                    "to": RunState.AUTHORIZED.value,
                    "reason": "authorization verified and atomically consumed",
                    "at": consumed_at,
                    "run_id": self.inputs.run_id,
                    "run_slug": verified.run_slug,
                    "execution_kind": self.inputs.execution_kind,
                    "validation_attempt": self.inputs.validation_attempt,
                }
            ],
            "resource_events": [],
            "command_history": [],
            "resources": {},
            "host_ports": [],
            "database_names": [],
            "phase_results": {},
            "failure": None,
            "cleanup": {
                "status": "PENDING",
                "remaining_resources": [],
                "errors": [],
            },
        }
        self._persist()
        return self.manifest

    def _event(self, event: str, **details: Any) -> None:
        self._manifest["resource_events"].append(
            {
                "sequence": len(self._manifest["resource_events"]) + 1,
                "event": event,
                "at": self._now(),
                **details,
            }
        )
        self._persist()

    @staticmethod
    def _bounded_output(value: str) -> str:
        return value if len(value) <= 8192 else value[:8192] + "<truncated>"

    def _execute(self, step: str, argv: Sequence[str]) -> CommandResult:
        command = tuple(str(part) for part in argv)
        entry: dict[str, Any] = {
            "sequence": len(self._manifest["command_history"]) + 1,
            "step": step,
            "argv": list(command),
            "status": "STARTED",
            "started_at": self._now(),
        }
        self._manifest["runner_step"] = step
        self._manifest["command_history"].append(entry)
        self._persist()
        try:
            result = self.executor.run(command)
        except BaseException as exc:
            entry.update(
                {
                    "status": "EXCEPTION",
                    "exception_type": type(exc).__name__,
                    "exception": str(exc),
                    "completed_at": self._now(),
                }
            )
            self._persist()
            raise
        entry.update(
            {
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "returncode": result.returncode,
                "stdout": self._bounded_output(result.stdout),
                "stderr": self._bounded_output(result.stderr),
                "completed_at": self._now(),
            }
        )
        self._persist()
        return result

    def _checked(
        self,
        step: str,
        argv: Sequence[str],
        *,
        code: str,
        domain: str = "DISPOSABLE_EXECUTION_TOOLING_BLOCKER",
    ) -> str:
        try:
            result = self._execute(step, argv)
        except RunnerError:
            raise
        except Exception as exc:
            raise RunnerError(
                code,
                f"{step} raised {type(exc).__name__}: {exc}",
                domain=domain,
                step=step,
                command=argv,
            ) from exc
        if result.returncode:
            message = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            raise RunnerError(
                code,
                f"{step} failed: {message}",
                domain=domain,
                step=step,
                command=argv,
            )
        return result.stdout.strip()

    def _verify_image(self) -> None:
        output = self._checked(
            "verify_postgres_image",
            ("podman", "image", "inspect", "--format", "{{json .}}", POSTGRES_IMMUTABLE_IMAGE),
            code="POSTGRES_IMAGE_INSPECTION_FAILURE",
        )
        try:
            observed = json.loads(output)
        except json.JSONDecodeError as exc:
            raise RunnerError(
                "POSTGRES_IMAGE_INSPECTION_FAILURE",
                "PostgreSQL image inspection did not return JSON",
                step="verify_postgres_image",
            ) from exc
        if isinstance(observed, list) and len(observed) == 1:
            observed = observed[0]
        if not isinstance(observed, Mapping):
            raise RunnerError(
                "POSTGRES_IMAGE_IDENTITY_MISMATCH",
                "PostgreSQL image inspection is ambiguous",
                step="verify_postgres_image",
            )
        repo_digests = observed.get("RepoDigests", [])
        if (
            not isinstance(repo_digests, list)
            or POSTGRES_IMMUTABLE_IMAGE not in repo_digests
            or str(observed.get("Id", "")).removeprefix("sha256:") != POSTGRES_IMAGE_ID
            or observed.get("Os") != "linux"
            or observed.get("Architecture") != "amd64"
        ):
            raise RunnerError(
                "POSTGRES_IMAGE_IDENTITY_MISMATCH",
                "local PostgreSQL image differs from approved immutable identity",
                step="verify_postgres_image",
            )

    def _new_resource(self, role: str) -> dict[str, Any]:
        assert self.verified is not None
        safe_role = _safe_role(role)
        base = f"{_resource_prefix(self.verified.run_slug)}_{safe_role}"
        labels = {
            RUN_LABEL: self.verified.run_slug,
            AUTH_LABEL: self.verified.authorization_sha256,
            ROLE_LABEL: safe_role,
        }
        return {
            "role": safe_role,
            "database_name": _database_name(self.verified.run_slug, safe_role),
            "container_name": base,
            "container_id": None,
            "container_status": "INTENDED",
            "network_name": f"{base}_net",
            "network_id": None,
            "network_status": "INTENDED",
            "volume_name": f"{base}_data",
            "volume_id": None,
            "volume_status": "INTENDED",
            "host_ip": "127.0.0.1",
            "container_port": 5432,
            "host_port": None,
            "labels": labels,
            "postgresql_status": "NOT_STARTED",
            "connection_result": "NOT_ATTEMPTED",
            "select_one_result": None,
            "cleanup_required": True,
            "created_at": None,
        }

    @staticmethod
    def _label_args(labels: Mapping[str, str]) -> tuple[str, ...]:
        parts: list[str] = []
        for key, value in sorted(labels.items()):
            parts.extend(("--label", f"{key}={value}"))
        return tuple(parts)

    def allocate(self, roles: Sequence[str]) -> Mapping[str, Any]:
        if self._recovery_only:
            raise RunnerError("RECOVERY_IS_CLEANUP_ONLY", "recovery cannot resume a business run")
        if not roles or len(set(roles)) != len(roles):
            raise RunnerError("INVALID_RESOURCE_ROLES", "resource roles must be unique and non-empty")
        self._transition(RunState.ALLOCATING, reason="resource allocation started")
        self._manifest["allocation_state"] = "IN_PROGRESS"
        self._persist()
        self._verify_image()
        planned: list[dict[str, Any]] = []
        for requested_role in roles:
            resource = self._new_resource(requested_role)
            role = resource["role"]
            self._manifest["resources"][role] = resource
            self._manifest["database_names"].append(resource["database_name"])
            self._event("RESOURCE_INTENT_PERSISTED", role=role)
            planned.append(resource)

        for resource in planned:
            role = resource["role"]
            labels = self._label_args(resource["labels"])

            volume_output = self._checked(
                f"allocate_{role}_volume",
                ("podman", "volume", "create", *labels, resource["volume_name"]),
                code="VOLUME_CREATION_FAILURE",
            )
            resource["volume_id"] = volume_output or resource["volume_name"]
            resource["volume_status"] = "CREATED"
            self._event("VOLUME_CREATED", role=role, name=resource["volume_name"])

            network_output = self._checked(
                f"allocate_{role}_network",
                (
                    "podman", "network", "create", "--disable-dns", *labels,
                    resource["network_name"],
                ),
                code="NETWORK_CREATION_FAILURE",
            )
            resource["network_id"] = network_output or resource["network_name"]
            resource["network_status"] = "CREATED"
            self._event("NETWORK_CREATED", role=role, name=resource["network_name"])

            container_output = self._checked(
                f"allocate_{role}_container",
                (
                    "podman", "create", "--pull=never", "--name", resource["container_name"],
                    *labels,
                    "--network", resource["network_name"],
                    "--publish", "127.0.0.1::5432",
                    "--volume", f"{resource['volume_name']}:/var/lib/postgresql",
                    "--env", f"POSTGRES_DB={resource['database_name']}",
                    "--env", "POSTGRES_HOST_AUTH_METHOD=trust",
                    POSTGRES_IMMUTABLE_IMAGE,
                ),
                code="CONTAINER_CREATION_FAILURE",
            )
            resource["container_id"] = container_output
            resource["container_status"] = "CREATED"
            resource["created_at"] = self._now()
            self._event("CONTAINER_CREATED", role=role, name=resource["container_name"])

            ports_output = self._checked(
                f"inspect_{role}_published_port",
                (
                    "podman", "container", "inspect", "--format",
                    "{{json .NetworkSettings.Ports}}", resource["container_name"],
                ),
                code="PORT_PUBLICATION_FAILURE",
            )
            try:
                ports = json.loads(ports_output)
                mappings = ports["5432/tcp"]
                mapping = mappings[0]
                host_port = int(mapping["HostPort"])
                host_ip = mapping["HostIp"]
            except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise RunnerError(
                    "PORT_PUBLICATION_FAILURE",
                    f"no unambiguous PostgreSQL host-port mapping for {role}",
                    step=f"inspect_{role}_published_port",
                ) from exc
            if host_ip not in ("127.0.0.1", "localhost") or not (1 <= host_port <= 65535):
                raise RunnerError(
                    "PORT_PUBLICATION_FAILURE",
                    f"unsafe PostgreSQL host-port mapping for {role}",
                    step=f"inspect_{role}_published_port",
                )
            resource["host_ip"] = "127.0.0.1"
            resource["host_port"] = host_port
            self._manifest["host_ports"].append(host_port)
            self._event("HOST_PORT_CONFIRMED", role=role, host_port=host_port)

        if len(set(self._manifest["host_ports"])) != len(self._manifest["host_ports"]):
            raise RunnerError(
                "PORT_PUBLICATION_FAILURE",
                "container engine returned duplicate dynamic host ports",
                step="confirm_unique_host_ports",
            )
        self._manifest["allocation_state"] = "SUCCEEDED"
        self._persist()
        self._transition(
            RunState.RESOURCES_ALLOCATED,
            reason="containers, networks, volumes, and host ports persisted",
        )
        return self.manifest

    def _collect_container_logs(self, role: str) -> None:
        resource = self._manifest["resources"][role]
        try:
            result = self._execute(
                f"collect_{role}_postgres_logs",
                ("podman", "logs", resource["container_name"]),
            )
            resource["postgres_logs"] = self._bounded_output(result.stdout + result.stderr)
            self._persist()
        except BaseException as exc:
            resource["postgres_logs_collection_error"] = f"{type(exc).__name__}: {exc}"
            self._persist()

    def bootstrap(self) -> Mapping[str, Any]:
        if self._recovery_only:
            raise RunnerError("RECOVERY_IS_CLEANUP_ONLY", "recovery cannot resume a business run")
        self._transition(RunState.BOOTSTRAPPING, reason="PostgreSQL startup/readiness started")
        for role, resource in self._manifest["resources"].items():
            try:
                self._checked(
                    f"start_{role}_postgres",
                    ("podman", "start", resource["container_name"]),
                    code="POSTGRES_STARTUP_FAILURE",
                    domain="POSTGRESQL_RUNTIME_BLOCKER",
                )
                resource["container_status"] = "RUNNING"
                resource["postgresql_status"] = "STARTED"
                self._persist()
                version = self._checked(
                    f"verify_{role}_postgres_version",
                    (
                        "podman", "exec", resource["container_name"],
                        "postgres", "--version",
                    ),
                    code="POSTGRES_STARTUP_FAILURE",
                    domain="POSTGRESQL_RUNTIME_BLOCKER",
                )
                if not version.startswith(POSTGRES_VERSION_PREFIX):
                    raise RunnerError(
                        "POSTGRES_VERSION_MISMATCH",
                        f"unexpected PostgreSQL version for {role}: {version}",
                        domain="POSTGRESQL_RUNTIME_BLOCKER",
                        step=f"verify_{role}_postgres_version",
                    )
                resource["observed_postgresql_version"] = version
                resource["postgresql_status"] = "VERSION_VERIFIED"
                self._persist()
                try:
                    selected = self.database_probe.wait_for_select_one(
                        host="127.0.0.1",
                        port=int(resource["host_port"]),
                        database=resource["database_name"],
                        user="postgres",
                        timeout_seconds=self.inputs.readiness_timeout_seconds,
                    )
                except DatabaseAuthenticationError as exc:
                    raise RunnerError(
                        "DB_AUTHENTICATION_FAILURE",
                        f"PostgreSQL authentication failed for {role}: {exc}",
                        domain="POSTGRESQL_RUNTIME_BLOCKER",
                        step=f"wait_{role}_postgres_readiness",
                    ) from exc
                except DatabaseReadinessTimeout as exc:
                    raise RunnerError(
                        "POSTGRES_READINESS_TIMEOUT",
                        f"PostgreSQL readiness timed out for {role}: {exc}",
                        domain="POSTGRESQL_RUNTIME_BLOCKER",
                        step=f"wait_{role}_postgres_readiness",
                    ) from exc
                except DatabaseQueryError as exc:
                    raise RunnerError(
                        "POSTGRES_QUERY_FAILURE",
                        f"SELECT 1 failed for {role}: {exc}",
                        domain="POSTGRESQL_RUNTIME_BLOCKER",
                        step=f"select_one_{role}",
                    ) from exc
                except RunnerError:
                    raise
                except Exception as exc:
                    raise RunnerError(
                        "POSTGRES_CONNECTION_FAILURE",
                        f"PostgreSQL connection proof failed for {role}: {exc}",
                        domain="POSTGRESQL_RUNTIME_BLOCKER",
                        step=f"wait_{role}_postgres_readiness",
                    ) from exc
                if selected != 1:
                    raise RunnerError(
                        "POSTGRES_QUERY_FAILURE",
                        f"SELECT 1 returned {selected!r} for {role}",
                        domain="POSTGRESQL_RUNTIME_BLOCKER",
                        step=f"select_one_{role}",
                    )
                resource["postgresql_status"] = "READY"
                resource["connection_result"] = "PASS"
                resource["select_one_result"] = 1
                resource["ready_at"] = self._now()
                self._persist()
            except Exception:
                self._collect_container_logs(role)
                raise
        self._transition(RunState.READY, reason="all PostgreSQL resources accept SELECT 1")
        return self.manifest

    def _failure_details(self, exc: BaseException) -> dict[str, Any]:
        current = RunState(str(self.manifest["current_state"]))
        if isinstance(exc, KeyboardInterrupt):
            code = "RUNNER_PROCESS_INTERRUPTION"
            domain = "DISPOSABLE_EXECUTION_TOOLING_BLOCKER"
            step = self._manifest.get("runner_step")
            command = None
        elif isinstance(exc, RunnerError):
            code, domain, step, command = exc.code, exc.domain, exc.step, exc.command
        else:
            before_bootstrap = current in {
                RunState.AUTHORIZED,
                RunState.ALLOCATING,
                RunState.RESOURCES_ALLOCATED,
            }
            code = (
                "TOOLING_EXCEPTION_BEFORE_BOOTSTRAP"
                if before_bootstrap
                else "UNCLASSIFIED_RUNNER_FAILURE"
            )
            domain = "DISPOSABLE_EXECUTION_TOOLING_BLOCKER"
            step = self._manifest.get("runner_step")
            command = None
        return {
            "domain": domain,
            "code": code,
            "runner_step": step or self._manifest.get("runner_step"),
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            "command": list(command) if command else None,
            "state_at_failure": current.value,
            "at": self._now(),
        }

    def record_failure(self, exc: BaseException) -> None:
        if self._manifest is None:
            return
        self._manifest["failure"] = self._failure_details(exc)
        self._manifest["business_outcome"] = "FAILED"
        if self._manifest.get("allocation_state") == "IN_PROGRESS":
            self._manifest["allocation_state"] = "FAILED"
        current = RunState(str(self._manifest["current_state"]))
        if current not in (RunState.FAILED, RunState.TEARDOWN_COMPLETE):
            self._transition(RunState.FAILED, reason=str(self._manifest["failure"]["code"]))
        else:
            self._persist()

    def start_to_ready(self, roles: Sequence[str]) -> Mapping[str, Any]:
        """Consume a fresh authorization and reach READY in this process only."""
        self.prepare()
        try:
            self.allocate(roles)
            self.bootstrap()
        except BaseException as exc:
            self.record_failure(exc)
            raise
        return self.manifest

    def run_evidence(
        self,
        *,
        precreation: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        stage_ext: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        roles: Sequence[str] = ("adminapps", "isosmart"),
    ) -> Mapping[str, Any]:
        """Run future authorized phases without offering a crash-resume path."""
        try:
            self.start_to_ready(roles)
            self._transition(RunState.PRECREATION_RUNNING, reason="PRECREATION callback started")
            precreation_result = dict(precreation(self.manifest))
            self._manifest["phase_results"]["PRECREATION"] = precreation_result
            self._persist()
            if precreation_result.get("status") != "PASS":
                raise RunnerError(
                    "PRECREATION_FAILURE",
                    "PRECREATION callback did not return PASS",
                    domain="EVIDENCE_PHASE_BLOCKER",
                    step="precreation",
                )
            self._transition(RunState.PRECREATION_PASS, reason="PRECREATION evidence persisted")
            self._transition(RunState.STAGE_EXT_RUNNING, reason="Stage EXT callback started")
            stage_result = dict(stage_ext(self.manifest))
            self._manifest["phase_results"]["STAGE_EXT"] = stage_result
            self._persist()
            if stage_result.get("status") != "PASS":
                raise RunnerError(
                    "STAGE_EXT_FAILURE",
                    "Stage EXT callback did not return PASS",
                    domain="EVIDENCE_PHASE_BLOCKER",
                    step="stage_ext",
                )
            self._transition(RunState.STAGE_EXT_PASS, reason="Stage EXT evidence persisted")
            self._manifest["business_outcome"] = "COMPLETED"
            self._persist()
            self._transition(RunState.COMPLETED, reason="authorized evidence phases completed")
        except BaseException as exc:
            self.record_failure(exc)
            try:
                self.cleanup()
            except BaseException:
                pass
            raise
        self.cleanup()
        return self.manifest

    def run_diagnostic(self, *, role: str = "diagnostic") -> Mapping[str, Any]:
        if self.inputs.execution_kind != DIAGNOSTIC_CLASSIFICATION:
            raise RunnerError(
                "DIAGNOSTIC_AUTHORIZATION_REQUIRED",
                "diagnostic execution kind is required",
            )
        try:
            self.start_to_ready((role,))
            self._manifest["diagnostic"] = {
                "classification": DIAGNOSTIC_CLASSIFICATION,
                "connection_result": "PASS",
                "select_one_result": 1,
                "completed_at": self._now(),
            }
            self._manifest["business_outcome"] = "COMPLETED"
            self._persist()
            self._transition(RunState.COMPLETED, reason="minimal environment diagnostic passed")
        except BaseException as exc:
            self.record_failure(exc)
            try:
                self.cleanup()
            except BaseException:
                pass
            raise
        self.cleanup()
        return self.manifest

    def _resource_exists(self, kind: str, name: str) -> bool:
        result = self._execute(
            f"cleanup_exists_{kind}_{name}",
            ("podman", kind, "exists", name),
        )
        if result.returncode == 0:
            return True
        if result.returncode == 1:
            return False
        raise RunnerError(
            "CLEANUP_INSPECTION_FAILURE",
            f"cannot determine whether {kind} {name} exists",
            step=f"cleanup_exists_{kind}",
            command=("podman", kind, "exists", name),
        )

    def _inspect_labels(self, kind: str, name: str) -> Mapping[str, str] | None:
        if not self._resource_exists(kind, name):
            return None
        expression = "{{json .Config.Labels}}" if kind == "container" else "{{json .Labels}}"
        result = self._execute(
            f"cleanup_inspect_{kind}_{name}",
            ("podman", kind, "inspect", "--format", expression, name),
        )
        if result.returncode:
            raise RunnerError(
                "CLEANUP_INSPECTION_FAILURE",
                f"cannot inspect {kind} {name}: {result.stderr.strip()}",
                step=f"cleanup_inspect_{kind}",
            )
        try:
            labels = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RunnerError(
                "CLEANUP_INSPECTION_FAILURE",
                f"invalid labels for {kind} {name}",
                step=f"cleanup_inspect_{kind}",
            ) from exc
        if not isinstance(labels, Mapping):
            raise RunnerError(
                "CLEANUP_LABEL_MISMATCH",
                f"missing run labels for {kind} {name}",
                step=f"cleanup_inspect_{kind}",
            )
        return {str(key): str(value) for key, value in labels.items()}

    def _cleanup_one(self, resource: dict[str, Any], kind: str) -> None:
        name = str(resource[f"{kind}_name"])
        role = _safe_role(str(resource.get("role", "")))
        expected_base = f"{_resource_prefix(str(self.manifest['run_slug']))}_{role}"
        expected_names = {
            "container": expected_base,
            "volume": f"{expected_base}_data",
            "network": f"{expected_base}_net",
        }
        if name != expected_names[kind]:
            raise RunnerError(
                "CLEANUP_MANIFEST_IDENTITY_MISMATCH",
                f"refusing cleanup for non-canonical {kind} name {name}",
                step=f"cleanup_{kind}",
            )
        expected = {
            RUN_LABEL: str(self.manifest["run_slug"]),
            AUTH_LABEL: str(self.manifest["authorization"]["sha256"]),
            ROLE_LABEL: role,
        }
        if resource.get("labels") != expected:
            raise RunnerError(
                "CLEANUP_MANIFEST_IDENTITY_MISMATCH",
                f"persisted labels differ for {kind} {name}",
                step=f"cleanup_{kind}",
            )
        labels = self._inspect_labels(kind, name)
        if labels is None:
            resource[f"{kind}_status"] = "ABSENT_VERIFIED"
            self._event("RESOURCE_ABSENT", kind=kind, name=name, role=resource["role"])
            return
        if any(labels.get(key) != value for key, value in expected.items()):
            raise RunnerError(
                "CLEANUP_LABEL_MISMATCH",
                f"refusing to remove unscoped {kind} {name}",
                step=f"cleanup_{kind}",
            )
        command = (
            ("podman", "rm", "--force", name)
            if kind == "container"
            else ("podman", kind, "rm", name)
        )
        self._checked(
            f"cleanup_remove_{kind}_{name}",
            command,
            code="CLEANUP_REMOVAL_FAILURE",
        )
        if self._inspect_labels(kind, name) is not None:
            raise RunnerError(
                "CLEANUP_ABSENCE_VERIFICATION_FAILURE",
                f"{kind} remains after cleanup: {name}",
                step=f"cleanup_verify_{kind}",
            )
        resource[f"{kind}_status"] = "REMOVED_VERIFIED"
        self._event("RESOURCE_REMOVED", kind=kind, name=name, role=resource["role"])

    def cleanup(self) -> Mapping[str, Any]:
        """Remove only manifest-named, label-matching resources and prove absence."""
        if self._manifest is None:
            raise RunnerError("RUN_NOT_PREPARED", "cleanup requires a persisted manifest")
        current = RunState(str(self._manifest["current_state"]))
        if current not in {
            RunState.FAILED,
            RunState.COMPLETED,
            RunState.TEARDOWN_COMPLETE,
        }:
            self.record_failure(
                RunnerError(
                    "RUNNER_PROCESS_INTERRUPTION",
                    "cleanup recovered a run that had not reached a business terminal state",
                    step="recovery_cleanup",
                )
            )
        cleanup = self._manifest["cleanup"]
        cleanup["status"] = "IN_PROGRESS"
        self._manifest["teardown_state"] = "IN_PROGRESS"
        cleanup["started_at"] = self._now()
        cleanup["errors"] = []
        self._manifest["runner_step"] = "cleanup"
        self._persist()
        remaining: list[str] = []
        for resource in self._manifest["resources"].values():
            for kind in ("container", "volume", "network"):
                try:
                    self._cleanup_one(resource, kind)
                except BaseException as exc:
                    cleanup["errors"].append(
                        {
                            "kind": kind,
                            "name": resource[f"{kind}_name"],
                            "exception_type": type(exc).__name__,
                            "exception": str(exc),
                        }
                    )
                    remaining.append(resource[f"{kind}_name"])
                    self._persist()
        cleanup["remaining_resources"] = remaining
        cleanup["completed_at"] = self._now()
        cleanup["post_teardown_absence_verified"] = not remaining
        cleanup["status"] = "PASS" if not remaining else "FAIL"
        self._manifest["teardown_state"] = "TEARDOWN_COMPLETE" if not remaining else "TEARDOWN_FAILED"
        for resource in self._manifest["resources"].values():
            resource["cleanup_required"] = any(
                resource[f"{kind}_status"] not in {"REMOVED_VERIFIED", "ABSENT_VERIFIED"}
                for kind in ("container", "volume", "network")
            )
        self._persist()
        if remaining:
            failure = RunnerError(
                "CLEANUP_INCOMPLETE",
                f"run-scoped resources remain: {', '.join(remaining)}",
                step="cleanup",
            )
            if self._manifest.get("failure") is None:
                self.record_failure(failure)
            raise failure
        current = RunState(str(self._manifest["current_state"]))
        if current != RunState.TEARDOWN_COMPLETE:
            self._transition(RunState.TEARDOWN_COMPLETE, reason="run-scoped resource absence verified")
        return self.manifest

    @classmethod
    def recover_for_cleanup(
        cls,
        *,
        repository_root: Path,
        evidence_root: Path,
        executor: CommandExecutor | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> "DisposableEvidenceRunner":
        """Load only enough state to clean up; never revalidate phases or resume."""
        root = repository_root.resolve()
        resolved_evidence = _resolve_from(root, evidence_root)
        manifest_path = resolved_evidence / MANIFEST_NAME
        document = _load_object(manifest_path, "RESOURCE_MANIFEST_INVALID")
        if document.get("schema") != MANIFEST_SCHEMA:
            raise RunnerError("RESOURCE_MANIFEST_INVALID", "unsupported resource manifest schema")
        declared = document.get("evidence_root")
        if not isinstance(declared, str) or _resolve_from(root, declared) != resolved_evidence:
            raise RunnerError("RESOURCE_MANIFEST_INVALID", "manifest evidence root differs")
        authorization = document.get("authorization")
        if not isinstance(authorization, Mapping) or not authorization.get("consumed"):
            raise RunnerError("RESOURCE_MANIFEST_INVALID", "manifest lacks consumed authorization")
        runner = cls.__new__(cls)
        runner.inputs = RunInputs(
            repository_root=root,
            run_id=str(document.get("run_id")),
            authorization_artifact=Path(str(authorization.get("artifact_path", "missing"))),
            expected_authorization_sha256=str(authorization.get("sha256")),
            current_integrity_generation=str(document.get("integrity", {}).get("generation")),
            expected_integrity_sha256=str(document.get("integrity", {}).get("sha256")),
            evidence_root=resolved_evidence,
            execution_kind=str(document.get("execution_kind")),
        )
        runner.executor = executor or SubprocessExecutor()
        runner.database_probe = None
        runner.clock = clock
        runner.verified = None
        runner._manifest = document
        runner._recovery_only = True
        return runner


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    diagnostic = subparsers.add_parser("diagnostic")
    diagnostic.add_argument("--repository-root", type=Path, required=True)
    diagnostic.add_argument("--run-id", required=True)
    diagnostic.add_argument("--authorization", type=Path, required=True)
    diagnostic.add_argument("--authorization-sha256", required=True)
    diagnostic.add_argument("--current-integrity-generation", required=True)
    diagnostic.add_argument("--integrity-sha256", required=True)
    diagnostic.add_argument("--evidence-root", type=Path, required=True)
    diagnostic.add_argument("--consumption-registry", type=Path)
    diagnostic.add_argument("--validation-attempt", type=int, required=True)
    diagnostic.add_argument("--readiness-timeout", type=float, default=60.0)

    evidence = subparsers.add_parser("evidence")
    evidence.add_argument("--repository-root", type=Path, required=True)
    evidence.add_argument("--run-id", required=True)
    evidence.add_argument("--authorization", type=Path, required=True)
    evidence.add_argument("--authorization-sha256", required=True)
    evidence.add_argument("--current-integrity-generation", required=True)
    evidence.add_argument("--integrity-sha256", required=True)
    evidence.add_argument("--evidence-root", type=Path, required=True)
    evidence.add_argument("--consumption-registry", type=Path)
    evidence.add_argument("--readiness-timeout", type=float, default=60.0)

    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument("--repository-root", type=Path, required=True)
    cleanup.add_argument("--evidence-root", type=Path, required=True)
    return parser


def cli_main(argv: Sequence[str] | None = None) -> int:
    arguments = build_cli_parser().parse_args(argv)
    if arguments.command == "cleanup":
        runner = DisposableEvidenceRunner.recover_for_cleanup(
            repository_root=arguments.repository_root,
            evidence_root=arguments.evidence_root,
        )
        manifest = runner.cleanup()
    elif arguments.command == "diagnostic":
        runner = DisposableEvidenceRunner(
            RunInputs(
                repository_root=arguments.repository_root,
                run_id=arguments.run_id,
                authorization_artifact=arguments.authorization,
                expected_authorization_sha256=arguments.authorization_sha256,
                current_integrity_generation=arguments.current_integrity_generation,
                expected_integrity_sha256=arguments.integrity_sha256,
                evidence_root=arguments.evidence_root,
                execution_kind=DIAGNOSTIC_CLASSIFICATION,
                consumption_registry=arguments.consumption_registry,
                validation_attempt=arguments.validation_attempt,
                readiness_timeout_seconds=arguments.readiness_timeout,
            )
        )
        manifest = runner.run_diagnostic()
    else:
        # Imports stay local so cleanup and environment diagnostics never load
        # application execution machinery.
        from .phase31_4_v2_5_live_executor import (
            Phase31_4V25LiveEvidenceExecutor,
            build_live_execution_context,
        )
        from .phase31_4_v2_5_operational_adapters import (
            SubprocessOperationalAdapter,
            repository_operational_environment,
        )

        runner = DisposableEvidenceRunner(
            RunInputs(
                repository_root=arguments.repository_root,
                run_id=arguments.run_id,
                authorization_artifact=arguments.authorization,
                expected_authorization_sha256=arguments.authorization_sha256,
                current_integrity_generation=arguments.current_integrity_generation,
                expected_integrity_sha256=arguments.integrity_sha256,
                evidence_root=arguments.evidence_root,
                execution_kind=EVIDENCE_EXECUTION,
                consumption_registry=arguments.consumption_registry,
                readiness_timeout_seconds=arguments.readiness_timeout,
            )
        )
        holder: dict[str, Any] = {}

        def live_executor() -> Any:
            if "executor" not in holder:
                context = build_live_execution_context(
                    repository_root=arguments.repository_root,
                    runner=runner,
                    evidence_root=arguments.evidence_root,
                    authorization_reference=str(arguments.authorization),
                    integrity_generation=arguments.current_integrity_generation,
                )
                holder["executor"] = Phase31_4V25LiveEvidenceExecutor(
                    runner=runner,
                    context=context,
                    adapter=SubprocessOperationalAdapter(
                        environment=repository_operational_environment(
                            arguments.repository_root, os.environ
                        ),
                        timeout_seconds=arguments.readiness_timeout,
                    ),
                    mode="evidence",
                    allow_runtime_execution=True,
                )
            return holder["executor"]

        def precreation_callback(current_manifest: Mapping[str, Any]) -> Mapping[str, Any]:
            return live_executor().precreation(current_manifest)

        def stage_ext_callback(current_manifest: Mapping[str, Any]) -> Mapping[str, Any]:
            executor = live_executor()
            try:
                result = executor.stage_ext(current_manifest)
                runtime = executor.prepare_runtime()
                result = dict(result)
                result["capture_bundle"] = "PASS"
                result["runtime_handoff"] = "PASS"
                result["runtime_phase_count"] = len(runtime.session.phases)
                return result
            finally:
                executor.stop_services()

        manifest = runner.run_evidence(
            precreation=precreation_callback,
            stage_ext=stage_ext_callback,
        )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli_main())
