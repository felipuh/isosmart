"""Offline, fail-closed verifier for the authoritative Retry 5 manifest."""

from __future__ import annotations

from hashlib import sha256
import ast
import json
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_5_RETRY5_OPERATIONAL_INPUT_MANIFEST_V1.json"
SCHEMA = "phase31.4.5-retry5-operational-input-manifest/v1"
V24 = "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json"
REGISTRY = "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json"
CLOSURE = "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json"


class ManifestVerificationError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and str(path) == value


def _local_import_closure(roots: list[str]) -> set[str]:
    """Resolve only project-local Python imports, never stdlib/site-packages."""
    pending = list(roots)
    closure: set[str] = set()
    while pending:
        relative = pending.pop()
        if relative in closure:
            continue
        path = ROOT / relative
        if not path.is_file() or path.suffix != ".py":
            raise ManifestVerificationError(f"invalid import root/member: {relative}")
        closure.add(relative)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        package = PurePosixPath(relative).parent
        for node in ast.walk(tree):
            candidates: list[PurePosixPath] = []
            if isinstance(node, ast.ImportFrom) and node.level:
                base = package
                for _ in range(node.level - 1):
                    base = base.parent
                if node.module:
                    candidates.append(base / (node.module.replace(".", "/") + ".py"))
                else:
                    candidates.extend(base / (alias.name + ".py") for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("foundation."):
                candidates.append(PurePosixPath("backend") / (node.module.replace(".", "/") + ".py"))
            elif isinstance(node, ast.Import):
                candidates.extend(PurePosixPath("backend") / (alias.name.replace(".", "/") + ".py")
                                  for alias in node.names if alias.name.startswith("foundation."))
            for candidate in candidates:
                normalized = candidate.as_posix()
                if (ROOT / normalized).is_file() and normalized not in closure:
                    pending.append(normalized)
    return closure


def verify_operational_manifest(expected_sha256: str, manifest_path: Path = MANIFEST) -> dict:
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise ManifestVerificationError("external expected manifest SHA-256 is required")
    if _sha(manifest_path) != expected_sha256:
        raise ManifestVerificationError("manifest byte hash differs from external authority")
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if document.get("schema") != SCHEMA:
        raise ManifestVerificationError("manifest schema mismatch")
    members = document.get("members")
    if not isinstance(members, list) or not members:
        raise ManifestVerificationError("manifest members missing")
    paths = [member.get("path") for member in members]
    if any(not isinstance(path, str) or not _safe_relative(path) for path in paths):
        raise ManifestVerificationError("unsafe manifest path")
    if len(paths) != len(set(paths)):
        raise ManifestVerificationError("duplicate manifest member")
    try:
        manifest_relative = manifest_path.relative_to(ROOT).as_posix()
    except ValueError:
        manifest_relative = None
    if manifest_relative in paths:
        raise ManifestVerificationError("manifest is self-referential")
    required = {V24, REGISTRY, CLOSURE}
    required.update(f"backend/foundation/migrations/{index:04d}_" for index in range(1, 24))
    if not {V24, REGISTRY, CLOSURE}.issubset(paths):
        raise ManifestVerificationError("authoritative contract set incomplete")
    mandatory = {
        "docs/governance/evidence/PHASE31_4_5B_V2_4_OPERATIONAL_CORRECTION_AUTHORIZATION_V1.json",
        "docs/governance/evidence/PHASE31_4_5B_V2_4_AUTHORIZATION_PROMOTION_RECORD_V1.json",
        "docs/governance/evidence/PHASE31_4_5B_V2_3_TO_V2_4_CHANGESET_V1.json",
        "docs/adr/0017-ephemeral-exact-id-governed-application-adapter.md",
        "docs/adr/0018-row-level-execution-ready-v2-contract.md",
        "docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V2.md",
        "backend/foundation/phase31_4_v2_4_support_producer.py",
        "backend/foundation/phase31_4_v2_4_execution_wiring.py",
        "backend/foundation/phase31_4_v2_4_execution_backend.py",
        "backend/foundation/phase31_4_v2_4_security_installer.py",
        "backend/foundation/phase31_4_postgres18_environment.py",
        "backend/foundation/postgres_phase31_4_clean_retry_3_harness.py",
        "backend/foundation/phase31_4_operational_manifest.py",
    }
    if not mandatory.issubset(paths):
        raise ManifestVerificationError("Retry5 governance/implementation set incomplete")
    for prefix in sorted(required - {V24, REGISTRY, CLOSURE}):
        if sum(path.startswith(prefix) for path in paths) != 1:
            raise ManifestVerificationError(f"migration member missing or ambiguous: {prefix}")
    if any(path.startswith("backend/foundation/migrations/0024") for path in paths):
        raise ManifestVerificationError("migration 0024 is forbidden")
    if any((ROOT / "backend/foundation/migrations").glob("0024*")):
        raise ManifestVerificationError("migration 0024 exists in repository")
    for member in members:
        if member.get("required") is not True or member.get("mutable_during_retry") is not False:
            raise ManifestVerificationError(f"mutable/optional member forbidden: {member['path']}")
        path = ROOT / member["path"]
        if not path.is_file() or _sha(path) != member.get("sha256"):
            raise ManifestVerificationError(f"member byte integrity failure: {member['path']}")
        for key in ("artifact_class", "execution_role", "provenance"):
            if not isinstance(member.get(key), str) or not member[key].strip():
                raise ManifestVerificationError(f"incomplete member metadata: {member['path']}")
    order_sets = document.get("order_sensitive_sets", {})
    if order_sets.get("migrations_0001_0023") != [
        next(path for path in paths if path.startswith(f"backend/foundation/migrations/{i:04d}_"))
        for i in range(1, 24)
    ]:
        raise ManifestVerificationError("migration order set mismatch")
    expected_phases = document.get("phase_machine_order")
    from .postgres_phase31_4_clean_retry_3_harness import PHASES
    if expected_phases != list(PHASES):
        raise ManifestVerificationError("phase-machine order mismatch")
    roots = document.get("import_roots")
    declared_closure = document.get("import_closure")
    if not isinstance(roots, list) or not isinstance(declared_closure, list):
        raise ManifestVerificationError("import closure declaration missing")
    observed_closure = _local_import_closure(roots)
    if observed_closure != set(declared_closure):
        raise ManifestVerificationError("project-local import closure mismatch")
    if not observed_closure.issubset(paths):
        raise ManifestVerificationError("import closure member missing from manifest")
    return document
