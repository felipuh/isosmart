"""Future isolated PostgreSQL 18.6 environment backend.

No command is run at import time.  Tests inject a recorder; Clean Retry injects
the authorized subprocess runner only after manifest verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import subprocess
from typing import Mapping, Protocol, Sequence


POSTGRES_IMAGE = "docker.io/library/postgres:18.6"
POSTGRES_VERSION = "PostgreSQL 18.6"
IMAGE_SPEC_PATH = (Path(__file__).resolve().parents[2] /
                   "docs/governance/evidence/PHASE31_4_POSTGRES18_6_RUNTIME_IMAGE_V1.json")
POSTGRES_DIGEST = "sha256:7341002d2b8c7c5bdd7542a671a95b36196c0b5b888daf454ae4fc33ba5346d7"
POSTGRES_IMAGE_ID = "a6638641707cdf047e5d5c2781f437e2e809323cab22c70b280be8389fbb7878"
POSTGRES_IMMUTABLE_IMAGE = f"docker.io/library/postgres@{POSTGRES_DIGEST}"


class CommandRunner(Protocol):
    def run(self, argv: Sequence[str], *, env: Mapping[str, str] | None = None) -> str: ...


class EnvironmentBackendError(RuntimeError):
    """Fail-closed environment lifecycle error."""


class SubprocessCommandRunner:
    """Concrete future runner; never instantiated or invoked by offline tests."""

    def run(self, argv: Sequence[str], *, env: Mapping[str, str] | None = None) -> str:
        completed = subprocess.run(tuple(argv), check=True, capture_output=True,
                                   text=True, env=None if env is None else dict(env))
        return completed.stdout


@dataclass
class EnvironmentIdentity:
    environment_id: str
    container_name: str
    database_name: str
    evidence_locations: tuple[str, ...] = ()


@dataclass
class Postgres18EnvironmentBackend:
    runner: CommandRunner
    identity: EnvironmentIdentity
    created: bool = field(default=False, init=False)

    def verify_local_image(self) -> None:
        """Reject a missing or changed local image before any container command."""
        spec = json.loads(IMAGE_SPEC_PATH.read_text(encoding="utf-8"))
        expected = {
            "schema": "phase31.4-postgres18.6-runtime-image/v1",
            "repository": "docker.io/library/postgres", "tag": "18.6",
            "oci_digest": POSTGRES_DIGEST, "local_image_id": POSTGRES_IMAGE_ID,
            "platform": "linux", "architecture": "amd64",
            "expected_server_version": POSTGRES_VERSION,
            "pull_allowed": False, "registry_fallback_allowed": False,
            "tag_only_execution_allowed": False,
        }
        if spec != expected:
            raise EnvironmentBackendError("frozen PostgreSQL image specification differs")
        try:
            observed = json.loads(self.runner.run((
                "podman", "image", "inspect", "--format", "{{json .}}",
                POSTGRES_IMMUTABLE_IMAGE,
            )))
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            raise EnvironmentBackendError("immutable PostgreSQL image is unavailable locally") from exc
        if isinstance(observed, list):
            if len(observed) != 1:
                raise EnvironmentBackendError("local image inspection is ambiguous")
            observed = observed[0]
        if not isinstance(observed, dict):
            raise EnvironmentBackendError("local image inspection is invalid")
        digests = observed.get("RepoDigests", [])
        if (not isinstance(digests, list)
                or POSTGRES_IMMUTABLE_IMAGE not in digests
                or observed.get("Id", "").removeprefix("sha256:") != POSTGRES_IMAGE_ID
                or observed.get("Os") != "linux"
                or observed.get("Architecture") != "amd64"):
            raise EnvironmentBackendError("local PostgreSQL image identity differs")

    def creation_commands(self) -> tuple[tuple[str, ...], ...]:
        name = self.identity.container_name
        database = self.identity.database_name
        return (
            ("podman", "create", "--pull=never", "--name", name, "--network", "none",
             "--env", f"POSTGRES_DB={database}", POSTGRES_IMMUTABLE_IMAGE),
            ("podman", "start", name),
            ("podman", "exec", name, "postgres", "--version"),
        )

    def create(self) -> None:
        if self.created:
            raise EnvironmentBackendError("environment creation is single-use")
        self.verify_local_image()
        outputs = [self.runner.run(command) for command in self.creation_commands()]
        if outputs[-1].strip() != POSTGRES_VERSION:
            raise EnvironmentBackendError("PostgreSQL server version is not exactly 18.6")
        self.created = True

    def configure_database(self) -> None:
        if not self.created:
            raise EnvironmentBackendError("database configuration requires created environment")
        self.runner.run(("podman", "exec", self.identity.container_name, "psql", "--no-psqlrc",
                         "--set", "ON_ERROR_STOP=1", "--dbname", self.identity.database_name,
                         "--command", "ALTER DATABASE CURRENT_DATABASE() SET timezone TO 'UTC'"))

    def apply_migrations(self) -> None:
        if not self.created:
            raise EnvironmentBackendError("migration orchestration requires created environment")
        self.runner.run(("backend/.venv/bin/python", "backend/manage.py", "migrate",
                         "--noinput", "--database", "default"))

    def guarded_teardown(self, *, p0: int, p1: int, full_closure: bool,
                         final_live_export_match: bool, teardown_eligible: bool) -> None:
        if (p0, p1) != (0, 0) or not all((full_closure, final_live_export_match,
                                          teardown_eligible)):
            raise EnvironmentBackendError("protected environment is not teardown eligible")
        self.runner.run(("podman", "rm", "--force", self.identity.container_name))
        self.created = False
