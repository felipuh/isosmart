"""Guarded, still-unexecuted Clean Retry 3 phase machine."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Callable, Protocol

from .phase31_4_operational_manifest import verify_operational_manifest
from .phase31_4_v2_4_security_installer import teardown_plan
from .phase31_4_v2_4_support_producer import build_support_plan
from .phase31_4_v2_4_execution_backend import V24ExecutionSession
from .phase31_4_postgres18_environment import Postgres18EnvironmentBackend


PHASES = (
    "PRECREATION_INTEGRITY", "ENVIRONMENT_CREATE", "RENDER_PROFILE", "MIGRATIONS",
    "CATALOG_ASSERTIONS", "SUPPORT_PRODUCER_INSTALL", "SECURITY_ASSERTIONS",
    "SUPPORT_FIXTURE", "FREEZE_1_5", "ROOT_BOOTSTRAP", "ROOT_DUAL_REREAD",
    "PROPOSAL_DELTA", "REVIEW", "DECISION", "AUTHORIZATION", "ADR0017_PARITY",
    "APPLICATION", "PUBLICATION_ADMISSION", "NATIVE_PUBLICATION",
    "PUBLICATION_CHECKPOINT", "B2_COMPATIBILITY", "B3_RELEASE",
    "PUBLICATION_CLOSURE", "PUBLICATION_LIVE_COMPARE", "PUBLICATION_ELIGIBILITY",
    "ACTIVATION_ADMISSION", "NATIVE_ACTIVATION", "FULL_CLOSURE", "LIVE_COMPARE",
    "TEARDOWN_GATE", "TEARDOWN", "POST_TEARDOWN_VERIFY", "TAMPER_NEGATIVE",
)


class PhaseTransitionError(RuntimeError):
    pass


_runtime_factory: Callable[[], "ConcretePhaseHandlers"] | None = None


def configure_clean_retry_runtime(factory: Callable[[], "ConcretePhaseHandlers"]) -> None:
    """Install narrow infrastructure construction; accepts no business values."""
    global _runtime_factory
    if _runtime_factory is not None:
        raise PhaseTransitionError("Clean Retry runtime is already configured")
    _runtime_factory = factory


class InstallerPort(Protocol):
    def install(self) -> str: ...
    def verify(self) -> None: ...
    def teardown(self, *, closure_complete: bool, export_matches_live: bool,
                 blockers: int) -> None: ...


@dataclass
class ConcretePhaseHandlers:
    """All 33 future phase handlers; lifecycle semantics stay in exact ports."""

    session: V24ExecutionSession
    environment: Postgres18EnvironmentBackend
    installer: InstallerPort
    closure_complete: bool = False
    final_live_export_match: bool = False
    p0: int = 0
    p1: int = 0
    teardown_eligible: bool = False

    def handle(self, phase: str) -> None:
        if phase not in PHASES:
            raise PhaseTransitionError(f"unknown phase: {phase}")
        if phase == "ENVIRONMENT_CREATE":
            self.environment.create()
        elif phase == "RENDER_PROFILE":
            self.environment.configure_database()
        elif phase == "MIGRATIONS":
            self.environment.apply_migrations()
        elif phase == "SUPPORT_PRODUCER_INSTALL":
            if self.installer.install() not in {"INSTALLED_EXACT", "ALREADY_EXACT"}:
                raise PhaseTransitionError("support installer did not reach exact state")
        elif phase in {"CATALOG_ASSERTIONS", "SECURITY_ASSERTIONS"}:
            self.installer.verify()
        elif phase == "TEARDOWN":
            self.installer.teardown(
                closure_complete=self.closure_complete,
                export_matches_live=self.final_live_export_match,
                blockers=self.p0 + self.p1,
            )
            self.environment.guarded_teardown(
                p0=self.p0, p1=self.p1, full_closure=self.closure_complete,
                final_live_export_match=self.final_live_export_match,
                teardown_eligible=self.teardown_eligible,
            )
        else:
            self.session.execute_phase(phase)

    def mapping(self) -> dict[str, Callable[[], None]]:
        # Each closure binds one frozen phase and reaches the concrete dispatcher.
        return {phase: (lambda selected=phase: self.handle(selected)) for phase in PHASES}


@dataclass
class FailureEvidence:
    current_phase: str
    blocker: str
    environment_identity: str | None = None
    database_identity: str | None = None
    container_identity: str | None = None
    retained_evidence_locations: tuple[str, ...] = ()
    closure_state: str = "INCOMPLETE"
    teardown_eligible: bool = False


@dataclass
class CleanRetry3Harness:
    """Infrastructure callbacks are internal plumbing, never business inputs."""

    handlers: dict[str, Callable[[], None]] = field(default_factory=dict, repr=False)
    completed: list[str] = field(default_factory=list, init=False)
    blocked: FailureEvidence | None = field(default=None, init=False)

    @classmethod
    def concrete(cls, implementation: ConcretePhaseHandlers) -> "CleanRetry3Harness":
        handlers = implementation.mapping()
        if len(handlers) != len(PHASES) or set(handlers) != set(PHASES):
            raise PhaseTransitionError("33-phase concrete handler closure failed")
        return cls(handlers=handlers)

    def advance(self, phase: str) -> None:
        expected = PHASES[len(self.completed)] if len(self.completed) < len(PHASES) else None
        if phase != expected:
            raise PhaseTransitionError(f"phase skipping denied: expected {expected}, got {phase}")
        if self.blocked is not None:
            raise PhaseTransitionError("protected failure is terminal")
        guards = {
            "APPLICATION": "ADR0017_PARITY",
            "NATIVE_PUBLICATION": "PUBLICATION_ADMISSION",
            "B2_COMPATIBILITY": "NATIVE_PUBLICATION",
            "B3_RELEASE": "B2_COMPATIBILITY",
            "NATIVE_ACTIVATION": "ACTIVATION_ADMISSION",
            "ACTIVATION_ADMISSION": "PUBLICATION_ELIGIBILITY",
            "TEARDOWN": "TEARDOWN_GATE",
        }
        predecessor = guards.get(phase)
        if predecessor and predecessor not in self.completed:
            raise PhaseTransitionError(f"{phase} requires {predecessor} PASS")
        try:
            if phase == "SUPPORT_FIXTURE":
                build_support_plan()
            handler = self.handlers.get(phase)
            if handler is None:
                raise PhaseTransitionError(f"concrete phase handler missing: {phase}")
            handler()
            self.completed.append(phase)
        except Exception as exc:
            self.blocked = FailureEvidence(phase, f"{type(exc).__name__}: {exc}")
            raise

    def run(self) -> None:
        for phase in PHASES:
            self.advance(phase)

    def authorize_teardown(self, *, closure_complete: bool,
                           export_matches_live: bool, blockers: int) -> tuple[str, ...]:
        if "LIVE_COMPARE" not in self.completed:
            raise PhaseTransitionError("teardown gate requires LIVE_COMPARE PASS")
        return teardown_plan(closure_complete=closure_complete,
                             export_matches_live=export_matches_live, blockers=blockers)


def run_clean_retry_3() -> None:
    """Parameterless entry. Expected manifest authority is external."""
    expected = os.environ.get("EXPECTED_OPERATIONAL_MANIFEST_SHA256", "")
    verify_operational_manifest(expected)
    if _runtime_factory is None:
        raise PhaseTransitionError("authorized Clean Retry infrastructure is not configured")
    CleanRetry3Harness.concrete(_runtime_factory()).run()
