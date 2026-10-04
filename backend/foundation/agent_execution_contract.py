"""Derived, generic execution contract for the source-defined agents.

The source artifact supplies identity, domain, purpose, references, and
autonomy. This module supplies only the transport and execution envelope.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

ROOT = Path(__file__).resolve().parents[2]
SOURCE_CATALOG = ROOT / "docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Datos.json"


class Autonomy(IntEnum):
    OBSERVE = 0
    ANALYZE = 1
    RECOMMEND = 2
    PREPARE = 3
    EXECUTE = 4


class ExecutionStatus(StrEnum):
    UNRESOLVED = "unresolved"
    COMPLETED = "completed"
    FAILED = "failed"


class CapabilityFamily(StrEnum):
    EVIDENCE_VALIDATION = "evidence_validation"
    APPLICABILITY_ANALYSIS = "applicability_analysis"
    REQUIREMENT_ASSESSMENT = "requirement_assessment"
    GAP_DETECTION = "gap_detection"
    RECOMMENDATION = "recommendation"
    MONITORING = "monitoring"
    ORCHESTRATION = "orchestration"
    GOVERNANCE = "governance"
    LEARNING = "learning"


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: UUID | str
    category: str = "unspecified"

    def __post_init__(self):
        if not str(self.evidence_id).strip():
            raise ValueError("evidence_id is required")
        if not self.category.strip():
            raise ValueError("evidence category is required")


@dataclass(frozen=True)
class SourceDataReference:
    reference: str
    data_type: str = "source"

    def __post_init__(self):
        if not self.reference.strip() or not self.data_type.strip():
            raise ValueError("source data references require reference and data_type")


@dataclass(frozen=True)
class ExecutionContext:
    values: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.values, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in self.values.items()
        ):
            raise TypeError("execution context values must be a string mapping")


@dataclass(frozen=True)
class AgentExecutionRequest:
    request_id: UUID | str
    tenant_id: UUID | str
    organization_id: UUID | str
    agent_definition_id: UUID | str
    agent_version: str
    capability: str
    normative_baseline: str | None
    clause_references: tuple[str, ...]
    requirement_references: tuple[str, ...]
    evidence_references: tuple[EvidenceReference, ...]
    source_data_references: tuple[SourceDataReference, ...]
    invocation_reason: str
    execution_context: ExecutionContext
    requested_operation: str
    correlation_id: UUID | str | None
    causation_id: UUID | str | None
    idempotency_key: str
    provenance_context: Mapping[str, str]
    model_policy_id: UUID | str
    requested_autonomy: int
    model_provider: str
    model_identifier: str
    model_version: str
    prompt_version: str
    rule_bundle_version: str
    inputs: tuple[Mapping[str, Any], ...]
    actor_id: str
    trace_id: UUID | str

    def __post_init__(self):
        required = {
            "request_id": self.request_id, "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "agent_definition_id": self.agent_definition_id,
            "agent_version": self.agent_version, "capability": self.capability,
            "invocation_reason": self.invocation_reason,
            "requested_operation": self.requested_operation,
            "idempotency_key": self.idempotency_key, "model_identifier": self.model_identifier,
            "model_version": self.model_version, "prompt_version": self.prompt_version,
            "rule_bundle_version": self.rule_bundle_version, "actor_id": self.actor_id,
            "trace_id": self.trace_id,
        }
        if any(value is None or (isinstance(value, str) and not value.strip()) for value in required.values()):
            raise ValueError("execution request has missing required fields")
        if (isinstance(self.requested_autonomy, bool) or not isinstance(self.requested_autonomy, int)
                or not 0 <= self.requested_autonomy <= int(Autonomy.EXECUTE)):
            raise ValueError("requested_autonomy must be A0 through A4")
        if not self.inputs:
            raise ValueError("execution request requires at least one input")
        if any(not isinstance(item, Mapping) for item in self.inputs):
            raise TypeError("execution request inputs must be mappings")
        if not isinstance(self.provenance_context, Mapping):
            raise TypeError("provenance_context must be a mapping")


@dataclass(frozen=True)
class Finding:
    code: str
    summary: str
    normative_conclusion: str | None = None

    def __post_init__(self):
        if not self.code.strip() or not self.summary.strip():
            raise ValueError("finding code and summary are required")


@dataclass(frozen=True)
class AgentExecutionResult:
    run_id: UUID | str
    agent_definition_id: UUID | str
    status: ExecutionStatus
    started_at: datetime | None
    completed_at: datetime | None
    evaluated_references: tuple[str, ...] = ()
    findings: tuple[Finding, ...] = ()
    evidence_produced: tuple[EvidenceReference, ...] = ()
    evidence_consumed: tuple[EvidenceReference, ...] = ()
    recommendations: tuple[str, ...] = ()
    recommendation_basis: tuple[Mapping[str, Any], ...] = ()
    deterministic_rule_results: tuple[Mapping[str, str], ...] = ()
    external_adapter_results: tuple[Mapping[str, str], ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    provenance: Mapping[str, str] = field(default_factory=dict)
    audit_references: tuple[str, ...] = ()
    emitted_events: tuple[str, ...] = ()
    result_scope: str | None = None
    not_normative_assessment: bool = False
    semantic_result: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.status == ExecutionStatus.COMPLETED and self.errors:
            raise ValueError("completed result cannot contain errors")
        if self.status == ExecutionStatus.FAILED and (self.recommendations or self.evidence_produced):
            raise ValueError("failed execution cannot produce recommendations or evidence")

    def assert_source_backed(self, request: AgentExecutionRequest) -> None:
        """Enforce NO_EVIDENCE_NO_ASSERTION for normative conclusions."""
        supplied = {str(item.evidence_id) for item in request.evidence_references}
        if any(str(item.evidence_id) not in supplied for item in self.evidence_consumed):
            raise ValueError("consumed evidence is outside the request provenance")
        has_evidence = bool(request.evidence_references or self.evidence_consumed)
        has_rule = bool(self.deterministic_rule_results)
        if any(finding.normative_conclusion for finding in self.findings) and not (has_evidence and has_rule):
            raise ValueError("NO_EVIDENCE_NO_ASSERTION: normative conclusion lacks evidence and rule support")


@dataclass(frozen=True)
class AgentExecutionSpec:
    agent_key: str
    source_name: str
    module: str
    purpose: str
    autonomy: str
    related_references: tuple[str, ...]
    capability_bindings: tuple[CapabilityFamily, ...]
    allowed_invocation_types: tuple[str, ...] = ("manual", "event", "workflow")
    allowed_evidence_categories: tuple[str, ...] = ("source", "document", "measurement", "event")
    required_context_categories: tuple[str, ...] = ("tenant", "organization")
    external_adapter_required: bool = False
    output_categories: tuple[str, ...] = ("finding", "recommendation", "unresolved")
    provenance_required: bool = True

    @property
    def autonomy_ceiling(self) -> int:
        levels = [int(value) for value in re.findall(r"A([0-4])", self.autonomy)]
        return max(levels) if levels else int(Autonomy.OBSERVE)


def _families(purpose: str, name: str) -> tuple[CapabilityFamily, ...]:
    text = f"{name} {purpose}".lower()
    if "evidencia" in text and "valida" in text:
        return (CapabilityFamily.EVIDENCE_VALIDATION,)
    if "requisito" in text and ("aplic" in text or "cambio" in text):
        return (CapabilityFamily.APPLICABILITY_ANALYSIS,)
    if "autonomía" in text or "supervisión" in text or "gobernance" in text:
        return (CapabilityFamily.GOVERNANCE,)
    if "aprende" in text or "eficacia" in text:
        return (CapabilityFamily.LEARNING,)
    if "mantiene" in text or "monit" in text or "detecta" in text:
        return (CapabilityFamily.MONITORING,)
    if "orchestrator" in name.lower() or "orchestrator" in purpose.lower():
        return (CapabilityFamily.ORCHESTRATION,)
    return (CapabilityFamily.REQUIREMENT_ASSESSMENT, CapabilityFamily.RECOMMENDATION)


def source_agent_specs() -> tuple[AgentExecutionSpec, ...]:
    document = json.loads(SOURCE_CATALOG.read_text(encoding="utf-8"))
    specs = []
    for name, module, references, autonomy, purpose in document["agents"]:
        key = f"source.{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}"
        specs.append(AgentExecutionSpec(
            agent_key=key, source_name=name, module=module, purpose=purpose,
            autonomy=autonomy, related_references=tuple(references.split(",")),
            capability_bindings=_families(purpose, name),
        ))
    return tuple(specs)


def require_autonomy(*, requested: int, spec: AgentExecutionSpec, operation: str) -> None:
    if isinstance(requested, bool) or not isinstance(requested, int) or not 0 <= requested <= 4:
        raise ValueError("requested autonomy must be an integer A0 through A4")
    if requested > spec.autonomy_ceiling:
        raise PermissionError(
            f"agent autonomy exceeded: requested A{requested}, ceiling A{spec.autonomy_ceiling}"
        )
    if operation in {"execute_repository_local", "execute_external"} and requested < int(Autonomy.EXECUTE):
        raise PermissionError("execution operations require A4 autonomy")
    if requested >= int(Autonomy.EXECUTE) and operation not in {"execute_repository_local", "execute_external", "evaluate_policy"}:
        raise PermissionError("A4 requires an explicit execution operation")


def execution_contract_report() -> dict[str, int]:
    specs = source_agent_specs()
    return {
        "source_defined": len(specs),
        "definitions": len({spec.agent_key for spec in specs}),
        "execution_specs": len(specs),
        "capability_bound": sum(bool(spec.capability_bindings) for spec in specs),
        "declaratively_repository_local_executable": len(specs),
        "external_adapter_ready": 0,
        "external_blocked": 0,
        "missing": 33 - len(specs),
    }
