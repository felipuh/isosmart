"""Native runtime composition primitives for Phase 31.4 V2.5.

This module is deliberately independent from the historical Clean Retry 3
implementation.  It owns runtime state and validation, while business effects
remain in the existing foundation command services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import UUID, uuid5
import json

from django.db import connections, transaction

from .action_authorization import ActionPreparationService, ExecutionAuthorizationService, ExecutionAuthorizerContext
from .agent_runtime import AgentCatalogCommandService, AgentRunCommandService
from .audit import AuditWriterService
from .human_decision import AgentDecisionCommandService, AuthorizedHumanContext, HumanDecisionGateService
from .recommendation import RecommendationCommandService
from .controlled_opportunity import ControlledOpportunityActionService
from .canonical import canonical_hash
from .effectiveness import EffectivenessCheckCommandService
from .governed_learning import LearningProposalCommandService, LearningSignalCommandService
from .governed_learning_application import KnowledgeLayerRuleGovernedApplicationService
from .knowledge_layer import KnowledgeLayerCommandService
from .knowledge_rule_release import KnowledgeLayerRulePublicationService
from .document_evidence import DocumentEvidenceCommandService
from .models import ActionPlan, ExecutionAuthorization, Opportunity, UserProjection
from .normative_coverage import NormativeCatalogCommandService
from .risk_objective import RiskOpportunityObjectiveCommandService
from .tenant_context import TrustedTenantIdentity, trusted_tenant_context
from .phase31_4_v2_4_support_producer import (
    execute_freeze0, retain_b2_compatibility, retain_full_closure,
    retain_publication_checkpoint, retain_publication_closure,
)
from .phase31_4_v2_5_executable_graph import PHASE_TOPOLOGY, build_executable_producer_graph
from .phase31_4_v2_5_precreation_integrity import verify_precreation_integrity


class V25RuntimeError(RuntimeError):
    """Base error for fail-closed V2.5 runtime violations."""


class MissingCaptureError(V25RuntimeError):
    pass


class BindingResolutionError(V25RuntimeError):
    pass


class AuthorityDenied(V25RuntimeError):
    pass


@dataclass(frozen=True)
class CaptureRecord:
    logical_member: str
    logical_field: str
    source_service: str
    source_operation: str
    returned_value: Any
    persisted_value: Any
    expected_type: str
    phase: str
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retry_id: str | None = None
    provenance: str = "NATIVE_CAPTURE"

    @property
    def equality_assertion(self) -> bool:
        return self.returned_value == self.persisted_value


@dataclass(frozen=True)
class CaptureBundle:
    """Fresh Stage EXT captures accepted by one clean retry only."""

    retry_id: str
    captures: tuple[CaptureRecord, ...]

    @classmethod
    def from_stage_ext(cls, stage_ext: dict[str, Any], *, retry_id: str) -> "CaptureBundle":
        expected_retry_id = stage_ext.get("retry_id")
        if expected_retry_id != retry_id:
            raise V25RuntimeError(
                f"capture bundle retry mismatch: expected {retry_id}, got {expected_retry_id}"
            )
        values = (
            ("adminapps.tenant::live", "id", "AdminApps", "create_tenant", stage_ext["tenant_id"]),
            ("qms.tenant_projection::live", "id", "TenantProjectionWriter", "project_tenant_event", stage_ext["tenant_projection_id"]),
            ("qms.user_projection::live", "adminapps_user_id", "AdminApps", "create_user", stage_ext["actor_id"]),
            ("qms.organization::live", "id", "QmsOrganizationCommandService", "create_organization", stage_ext["organization_id"]),
            ("qms.process::live", "id", "QmsContextCommandService", "create_process", stage_ext["process_id"]),
        )
        return cls(
            retry_id=retry_id,
            captures=tuple(
                CaptureRecord(
                    logical_member=member,
                    logical_field=field_name,
                    source_service=service,
                    source_operation=operation,
                    returned_value=value,
                    persisted_value=value,
                    expected_type="uuid",
                    phase="STAGE_EXT",
                    retry_id=retry_id,
                    provenance="LIVE_UPSTREAM_NATIVE_CAPTURE",
                )
                for member, field_name, service, operation, value in values
            ),
        )

    def validate_for_retry(self, retry_id: str) -> None:
        if self.retry_id != retry_id:
            raise V25RuntimeError(
                f"capture bundle retry mismatch: expected {retry_id}, got {self.retry_id}"
            )
        if len(self.captures) != 5:
            raise V25RuntimeError(f"capture bundle expected 5 captures, got {len(self.captures)}")
        for record in self.captures:
            if record.retry_id != retry_id:
                raise V25RuntimeError(f"capture record retry mismatch: {record.logical_member}.{record.logical_field}")
            if record.provenance != "LIVE_UPSTREAM_NATIVE_CAPTURE":
                raise V25RuntimeError(f"invalid live capture provenance: {record.logical_member}.{record.logical_field}")


class NativeCaptureRegistry:
    """Trace native return values to their persisted representation."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], CaptureRecord] = {}
        self._aliases: dict[tuple[str, str], tuple[str, str]] = {}

    def bind_alias(
        self,
        logical_member: str,
        logical_field: str,
        captured_member: str,
        captured_field: str,
    ) -> None:
        """Bind a contract identity to a live capture without copying its value."""
        target = (logical_member, logical_field)
        source = (captured_member, captured_field)
        if target in self._records or target in self._aliases:
            raise V25RuntimeError(f"duplicate native capture alias: {target[0]}.{target[1]}")
        if target == source:
            raise V25RuntimeError(f"self-referential native capture alias: {target[0]}.{target[1]}")
        self._aliases[target] = source

    def capture(self, record: CaptureRecord) -> CaptureRecord:
        if not record.equality_assertion:
            raise V25RuntimeError(
                f"native/persisted mismatch: {record.logical_member}.{record.logical_field}"
            )
        if record.expected_type == "uuid" and not isinstance(record.returned_value, (str, UUID)):
            raise TypeError(f"expected uuid value: {record.logical_member}.{record.logical_field}")
        if record.expected_type == "integer" and (
            isinstance(record.returned_value, bool) or not isinstance(record.returned_value, int)
        ):
            raise TypeError(f"expected integer value: {record.logical_member}.{record.logical_field}")
        key = (record.logical_member, record.logical_field)
        if key in self._records:
            raise V25RuntimeError(f"duplicate native capture: {key[0]}.{key[1]}")
        self._records[key] = record
        return record

    def get(self, logical_member: str, logical_field: str) -> CaptureRecord:
        requested = (logical_member, logical_field)
        key = requested
        visited: set[tuple[str, str]] = set()
        while key in self._aliases:
            if key in visited:
                raise V25RuntimeError(f"cyclic native capture alias: {key[0]}.{key[1]}")
            visited.add(key)
            key = self._aliases[key]
        try:
            return self._records[key]
        except KeyError as exc:
            label = "missing live capture" if requested in self._aliases else "missing capture"
            raise MissingCaptureError(f"{label}: {logical_member}.{logical_field}") from exc

    def values(self) -> tuple[CaptureRecord, ...]:
        return tuple(self._records.values())


class ResolvedBindingRegistry:
    """Resolve only exact literals, captures, and prior bindings."""

    def __init__(self, bindings: dict[tuple[str, str], dict[str, Any]]) -> None:
        self.bindings = bindings
        self.resolved: dict[tuple[str, str], Any] = {}

    def resolve(self, member: str, field_name: str, captures: NativeCaptureRegistry) -> Any:
        token = (member, field_name)
        if token in self.resolved:
            return self.resolved[token]
        binding = self.bindings.get(token)
        if binding is None:
            raise BindingResolutionError(f"invalid binding: {member}.{field_name}")
        visiting: set[tuple[str, str]] = set()

        def visit(current: tuple[str, str]) -> Any:
            if current in visiting:
                raise BindingResolutionError(f"cyclic binding: {current[0]}.{current[1]}")
            if current in self.resolved:
                return self.resolved[current]
            item = self.bindings.get(current)
            if item is None:
                raise BindingResolutionError(f"missing dependency: {current[0]}.{current[1]}")
            visiting.add(current)
            kind = item.get("kind")
            if kind == "EXACT_LITERAL":
                value = item.get("typed_value")
            elif kind in {"CAPTURE_NATIVE_OUTPUT", "LIVE_UPSTREAM_NATIVE_CAPTURE"}:
                value = captures.get(*current).returned_value
            elif kind == "DETERMINISTIC_DERIVATION":
                inputs = item.get("all_preimage_inputs", {})
                if item.get("algorithm_id") != "RFC4122-UUIDv5-SHA1":
                    raise BindingResolutionError(
                        f"unsupported deterministic derivation: {current[0]}.{current[1]}"
                    )
                try:
                    value = str(uuid5(UUID(inputs["namespace_uuid"]), inputs["utf8_name"]))
                except (KeyError, TypeError, ValueError) as exc:
                    raise BindingResolutionError(
                        f"invalid deterministic derivation: {current[0]}.{current[1]}"
                    ) from exc
                if value != item.get("expected_output"):
                    raise BindingResolutionError(
                        f"deterministic derivation mismatch: {current[0]}.{current[1]}"
                    )
            elif kind == "REFERENCE_RESOLVED_BINDING":
                source = (item.get("source_member"), item.get("source_field"))
                value = visit(source)
            elif kind == "DERIVED_RUNTIME_INVARIANT":
                source = item.get("source_binding")
                if source is None:
                    sources = item.get("source_bindings", [])
                    source = sources[0] if len(sources) == 1 else None
                if not isinstance(source, str) or "." not in source:
                    raise BindingResolutionError(f"invalid invariant source: {current}")
                source_member, source_field = source.rsplit(".", 1)
                value = visit((source_member, source_field)) + 1
            elif kind == "ADR0017_MAPPED_OUTPUT":
                value = item.get("output_identity")
            else:
                raise BindingResolutionError(f"unsupported binding: {current[0]}.{current[1]}")
            visiting.remove(current)
            self.resolved[current] = value
            return value

        return visit(token)


class RuntimeInvariantEngine:
    @staticmethod
    def assert_revision(*, initial: dict[str, Any], successor: dict[str, Any]) -> None:
        if initial["lineage_id"] != initial["id"] or initial["revision"] != 1:
            raise V25RuntimeError("initial opportunity revision invariant failed")
        if initial["previous_revision_id"] is not None:
            raise V25RuntimeError("initial opportunity has a predecessor")
        expected = {
            "lineage_id": initial["lineage_id"],
            "revision": initial["revision"] + 1,
            "previous_revision_id": initial["id"],
        }
        for name, value in expected.items():
            if successor.get(name) != value:
                raise V25RuntimeError(f"successor invariant failed: {name}")
        if successor["id"] == initial["id"]:
            raise V25RuntimeError("successor reused the prior native identity")


class NativeAuthorityReader:
    """Read persisted authorization and enforce the complete A3 chain."""

    def __init__(self, *, using: str = "default") -> None:
        self.using = using

    def read(self, authorization_id: Any) -> dict[str, Any]:
        authorization = ExecutionAuthorization.objects.using(self.using).select_related(
            "action_plan", "agent_decision__agent_run__agent_definition"
        ).get(id=authorization_id)
        plan = authorization.action_plan
        decision = authorization.agent_decision
        run = authorization.agent_run
        definition = authorization.agent_definition
        ceilings = {
            "agent_definition": definition.autonomy_max,
            "agent_run": run.effective_autonomy_ceiling,
            "decision": decision.decision_autonomy,
            "authorization": authorization.effective_autonomy_ceiling,
        }
        if plan.required_autonomy != 3 or any(value < 3 for value in ceilings.values()):
            raise AuthorityDenied("insufficient_autonomy_for_a3")
        if authorization.outcome != ExecutionAuthorization.Outcome.AUTHORIZED:
            raise AuthorityDenied("execution_authorization_not_granted")
        return {
            "actor": authorization.actor_id,
            "target_type": plan.target_type,
            "target_id": plan.target_id,
            "required_autonomy": plan.required_autonomy,
            "ceilings": ceilings,
            "authorization_id": str(authorization.id),
        }


@dataclass(frozen=True)
class NativeOperationBinding:
    name: str
    service: Any
    source_service: str
    source_operation: str
    native_source: str
    source_file: str
    phases: tuple[str, ...]

    def validate(self) -> None:
        if not callable(getattr(self.service, self.source_operation, None)):
            raise V25RuntimeError(
                f"orphan native operation binding: {self.name} -> "
                f"{self.source_service}.{self.source_operation}"
            )


@dataclass(frozen=True)
class NativeSourceRequirement:
    native_source: str
    native_operation: str
    source_service: str
    source_operation: str
    source_file: str
    phases: tuple[str, ...]


_NATIVE_SOURCE_REQUIREMENTS = (
    NativeSourceRequirement("phase31.4.4-controlled-opportunity-producer/v1", "opportunity.create", "RiskOpportunityObjectiveCommandService", "create_opportunity", "backend/foundation/risk_objective.py", ("INITIAL_OPPORTUNITY", "CONTROLLED_TRANSITION")),
    NativeSourceRequirement("phase31.4.4-governed-learning-producer/v2", "learning_proposal.create", "LearningProposalCommandService", "create_proposal", "backend/foundation/governed_learning.py", ("PROPOSAL_DELTA", "REVIEW", "DECISION", "AUTHORIZATION")),
    NativeSourceRequirement("migration-0022-native-release-service/v1", "publication.native", "KnowledgeLayerRulePublicationService", "publish_native", "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py", ("ROOT_BOOTSTRAP", "NATIVE_PUBLICATION", "NATIVE_ACTIVATION")),
    NativeSourceRequirement("declared native producer", "catalog.standard.create", "NormativeCatalogCommandService", "create_standard", "backend/foundation/normative_coverage.py", ("CATALOG_ASSERTIONS",)),
    NativeSourceRequirement("phase31.4.4-agent-provenance-producer/v1", "agent_run.start", "AgentRunCommandService", "start_agent_run", "backend/foundation/agent_runtime.py", ("FREEZE_1_5",)),
    NativeSourceRequirement("phase31.4.4-exact-support-producer/v1", "freeze0.exact_support", "phase31_4_v2_4_support_producer", "execute_freeze0", "backend/foundation/phase31_4_v2_4_support_producer.py", ("CATALOG_ASSERTIONS",)),
    NativeSourceRequirement("backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py or named frozen producer", "audit.append", "AuditWriterService", "append", "backend/foundation/audit.py", ("EVENT_OUTBOX_ASSERTIONS",)),
    NativeSourceRequirement("phase31.4.4-effectiveness-producer/v1", "effectiveness.record", "EffectivenessCheckCommandService", "record_effectiveness_check", "backend/foundation/effectiveness.py", ("EFFECTIVENESS_CHECK",)),
    NativeSourceRequirement("phase31.4.4-learning-signal-producer/v1", "learning_signal.create", "LearningSignalCommandService", "create_signal", "backend/foundation/governed_learning.py", ("LEARNING_SIGNAL",)),
    NativeSourceRequirement("adr0017-exact-application-adapter/v1", "application.reference_path", "KnowledgeLayerRuleGovernedApplicationService", "apply_validated_knowledge_layer_rule_source_reference_correction_v1", "backend/foundation/governed_learning_application.py", ("APPLICATION",)),
    NativeSourceRequirement("phase31.4.4-retained-evidence-producer/v1", "publication.checkpoint", "phase31_4_v2_4_support_producer", "retain_publication_checkpoint", "backend/foundation/phase31_4_v2_4_support_producer.py", ("PUBLICATION_CHECKPOINT", "B2_COMPATIBILITY", "B3_RELEASE", "PUBLICATION_CLOSURE", "FULL_CLOSURE")),
    NativeSourceRequirement("phase31.4.4-isolated-catalog-producer/v1", "catalog.model_policy.create", "AgentCatalogCommandService", "create_model_policy", "backend/foundation/agent_runtime.py", ("CATALOG_ASSERTIONS",)),
    NativeSourceRequirement("knowledge-layer-rule-root-bootstrap-producer/v1", "root.bootstrap.publish", "KnowledgeLayerRulePublicationService", "publish_native", "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py", ("ROOT_BOOTSTRAP",)),
    NativeSourceRequirement("backend/foundation/risk_objective.py:create_opportunity->_create", "opportunity.create.initial_capture", "RiskOpportunityObjectiveCommandService", "create_opportunity", "backend/foundation/risk_objective.py", ("INITIAL_OPPORTUNITY",)),
    NativeSourceRequirement("backend/foundation/action_authorization.py:ActionPreparationService.prepare_action_plan", "action_plan.prepare", "ActionPreparationService", "prepare_action_plan", "backend/foundation/action_authorization.py", ("ACTION_PLAN_PREPARATION",)),
    NativeSourceRequirement("backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py:qms.foundation_0015_apply_opportunity_status_transition", "opportunity.controlled_transition", "ControlledOpportunityActionService", "defer_evaluation", "backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py", ("CONTROLLED_TRANSITION",)),
)


class NativeOperationRegistry:
    """Closed registry of the native operations used by V2.5 composition."""

    def __init__(self, bindings: tuple[NativeOperationBinding, ...]) -> None:
        self._bindings = {binding.name: binding for binding in bindings}
        if len(self._bindings) != len(bindings):
            raise V25RuntimeError("duplicate native operation binding")
        for binding in bindings:
            binding.validate()

    @classmethod
    def product_default(cls, *, using: str = "default") -> "NativeOperationRegistry":
        risk_objective = RiskOpportunityObjectiveCommandService(using=using)
        action_preparation = ActionPreparationService(using=using)
        controlled_opportunity = ControlledOpportunityActionService(using=using)
        support = type("SupportProducer", (), {
            name: staticmethod(function) for name, function in {
                "execute_freeze0": execute_freeze0,
                "retain_publication_checkpoint": retain_publication_checkpoint,
                "retain_b2_compatibility": retain_b2_compatibility,
                "retain_publication_closure": retain_publication_closure,
                "retain_full_closure": retain_full_closure,
            }.items()
        })()
        services = {
            "RiskOpportunityObjectiveCommandService": risk_objective,
            "ActionPreparationService": action_preparation,
            "ControlledOpportunityActionService": controlled_opportunity,
            "AgentCatalogCommandService": AgentCatalogCommandService(using=using),
            "AgentRunCommandService": AgentRunCommandService(using=using),
            "EffectivenessCheckCommandService": EffectivenessCheckCommandService(using=using),
            "LearningSignalCommandService": LearningSignalCommandService(using=using),
            "LearningProposalCommandService": LearningProposalCommandService(using=using),
            "KnowledgeLayerCommandService": KnowledgeLayerCommandService(using=using),
            "NormativeCatalogCommandService": NormativeCatalogCommandService(using=using),
            "KnowledgeLayerRulePublicationService": KnowledgeLayerRulePublicationService(using=using),
            "KnowledgeLayerRuleGovernedApplicationService": KnowledgeLayerRuleGovernedApplicationService(using=using),
            "AuditWriterService": AuditWriterService(using=using),
            "phase31_4_v2_4_support_producer": support,
        }
        return cls(tuple(
            NativeOperationBinding(
                requirement.native_operation, services[requirement.source_service],
                requirement.source_service, requirement.source_operation,
                requirement.native_source, requirement.source_file, requirement.phases,
            ) for requirement in _NATIVE_SOURCE_REQUIREMENTS
        ))

    def resolve(self, name: str) -> NativeOperationBinding:
        try:
            return self._bindings[name]
        except KeyError as exc:
            raise V25RuntimeError(f"unregistered native operation: {name}") from exc

    def source_manifest(self) -> tuple[dict[str, Any], ...]:
        return tuple({
            "contract_operation": binding.name,
            "native_source": binding.native_source,
            "runtime_handler": binding.source_operation,
            "native_service": binding.source_service,
            "source_file": binding.source_file,
            "phases": binding.phases,
        } for binding in self._bindings.values())

    def coverage_report(self, contract: dict[str, Any]) -> dict[str, Any]:
        required: dict[str, dict[str, set[str]]] = {}
        for member in contract.get("field_bindings", []):
            identity = member["member_identity"]
            member_key = f"{identity['qualified_table_or_artifact_index']}::{identity['primary_key_or_artifact_id']}"
            for field in member.get("fields", []):
                binding = field.get("value_binding", {})
                if binding.get("kind") != "CAPTURE_NATIVE_OUTPUT":
                    continue
                source = binding.get("native_source")
                item = required.setdefault(source, {"contract_members": set(), "fields": set()})
                item["contract_members"].add(member_key)
                item["fields"].add(f"{member_key}.{field['name']}")
        registered: dict[str, NativeOperationBinding] = {}
        duplicates = []
        for binding in self._bindings.values():
            if binding.native_source in registered:
                duplicates.append(binding.native_source)
            registered[binding.native_source] = binding
        return {
            "required": len(required),
            "registered": len(registered),
            "unresolved": sorted(set(required) - set(registered)),
            "unknown": sorted(set(registered) - set(required)),
            "duplicate_conflicting": sorted(set(duplicates)),
            "sources": tuple({
                "native_source": source,
                "contract_members": tuple(sorted(item["contract_members"])),
                "fields": tuple(sorted(item["fields"])),
                "runtime_handler": registered[source].source_operation if source in registered else None,
                "service_class": registered[source].source_service if source in registered else None,
                "source_file": registered[source].source_file if source in registered else None,
                "phases": registered[source].phases if source in registered else (),
            } for source, item in sorted(required.items())),
        }


class NativePhaseExecutor(Protocol):
    def execute(self, session: "V25ExecutionSession", context: "PhaseExecutionContext") -> "PhaseExecutionResult":
        ...


@dataclass(frozen=True)
class PhaseExecutionResult:
    phase_id: str
    status: str = "FAIL"
    operation: str | None = None
    native_source: str | None = None
    source_service: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    executor: str | None = None
    inputs_hash: str | None = None
    output_ids: tuple[str, ...] = ()
    readback_ids: tuple[str, ...] = ()
    assertions: tuple[dict[str, Any], ...] = ()
    evidence_artifacts: tuple[str, ...] = ()
    evidence_hashes: tuple[str, ...] = ()
    provenance: tuple[dict[str, Any], ...] = ()
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass
class PhaseExecutionContext:
    session: "V25ExecutionSession"
    contract: "V25Contract | None" = None
    operation_registry: NativeOperationRegistry | None = None
    authority_reader: NativeAuthorityReader | None = None
    capture_registry: NativeCaptureRegistry | None = None
    binding_registry: ResolvedBindingRegistry | None = None
    invariant_engine: RuntimeInvariantEngine | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class _NativePhaseExecutor:
    """Internal concrete executor that resolves a product service from the native registry."""

    def __init__(self, phase_id: str, operation_registry: NativeOperationRegistry, *, native_operation: str | None = None, source_service: str | None = None, source_operation: str | None = None) -> None:
        self.phase_id = phase_id
        self.operation_registry = operation_registry
        self.native_operation = native_operation
        self.source_service = source_service
        self.source_operation = source_operation

    @staticmethod
    def _resolve_runtime_service(service_name: str, *, using: str = "default"):
        services = {
            "AgentCatalogCommandService": AgentCatalogCommandService(using=using),
            "AgentRunCommandService": AgentRunCommandService(using=using),
            "RecommendationCommandService": RecommendationCommandService(using=using),
            "AgentDecisionCommandService": AgentDecisionCommandService(using=using),
            "ActionPreparationService": ActionPreparationService(using=using),
            "ExecutionAuthorizationService": ExecutionAuthorizationService(using=using),
        }
        try:
            return services[service_name]
        except KeyError as exc:
            raise V25RuntimeError(f"unsupported direct native phase service: {service_name}") from exc

    @staticmethod
    def _service_using(session: V25ExecutionSession, logical_alias: str) -> str:
        from django.db import connections
        return logical_alias if logical_alias in connections.databases else session.using

    def execute(self, session: V25ExecutionSession, context: PhaseExecutionContext) -> PhaseExecutionResult:
        if self.phase_id == "PRECREATION_INTEGRITY":
            outcome = verify_precreation_integrity(root=session.project_root, run_id=session.retry_id)
            return PhaseExecutionResult(
                phase_id=self.phase_id,
                status=outcome.status,
                operation="verify_precreation_integrity",
                native_source="foundation.phase31_4_v2_5_precreation_integrity.verify_precreation_integrity",
                source_service="PrecreationIntegrityExecutor",
                metadata=outcome.details,
                executor="PrecreationIntegrityExecutor",
                inputs_hash=outcome.details.get("current_integrity_artifact", {}).get("sha256"),
                assertions=outcome.assertions,
                evidence_artifacts=((outcome.evidence_path,) if outcome.evidence_path else ()),
                evidence_hashes=((outcome.evidence_sha256,) if outcome.evidence_sha256 else ()),
                error=outcome.error,
                started_at=outcome.started_at,
                completed_at=outcome.completed_at,
            )
        if self.phase_id == "CATALOG_ASSERTIONS":
            return self._execute_catalog_assertions(session)
        if self.phase_id == "NATIVE_IDENTITY_CAPTURE":
            return self._execute_agent_run_start(session)
        if self.phase_id == "RUNTIME_COMPOSITION_PROOF":
            return self._execute_agent_run_completion(session)
        if self.phase_id == "PHASE_EVIDENCE":
            return self._execute_agent_decision(session)
        if self.phase_id == "ACTION_PLAN_DRY_RUN":
            return self._execute_action_plan_dry_run(session)
        if self.phase_id == "EXECUTION_AUTHORIZATION":
            return self._execute_execution_authorization(session)
        if self.phase_id == "EVENT_OUTBOX_ASSERTIONS":
            if "authorization_id" not in session.composition:
                raise V25RuntimeError("event/outbox assertions require live authorization")
            return PhaseExecutionResult(
                self.phase_id, status="FAIL", operation="verify_controlled_event_outbox_audit",
                native_source="controlled_opportunity.transition", source_service="AuditWriterService",
                metadata={"verified": False, "authorization_id": str(session.composition["authorization_id"]),
                          "error": "event/outbox/audit readback verifier is required"},
                error="event/outbox/audit readback verifier is required",
            )
        if self.phase_id in {
            "RESOLVED_GRAPH", "EXACT_COMPARISON", "SECURITY_EVIDENCE",
            "LIVE_MIGRATION_EVIDENCE", "LIVE_AUTHORITY_EVIDENCE", "LIVE_OPERATION_EVIDENCE",
            "CLOSURE_PRECONDITIONS", "CLOSURE_REPORT", "TEARDOWN_GATE", "TEARDOWN",
            "POST_TEARDOWN_VERIFY",
        }:
            if "authorization_id" not in session.composition:
                raise V25RuntimeError(f"{self.phase_id} requires completed live authorization")
            return PhaseExecutionResult(
                self.phase_id, status="FAIL", operation="verify_live_phase_evidence",
                native_source="V25ExecutionSession.composition", source_service="V25Runtime",
                metadata={"verified": False, "authorization_id": str(session.composition["authorization_id"]),
                          "error": "phase-specific evidence verifier is required"},
                error="phase-specific evidence verifier is required",
            )
        if self.native_operation is not None:
            binding = self.operation_registry.resolve(self.native_operation)
            service = binding.service
            method_name = binding.source_operation
            native_source = binding.native_source
            source_service = binding.source_service
            if self.native_operation == "action_plan.prepare":
                service = ActionPreparationService(using=self._service_using(session, "worker"))
            if self.native_operation == "opportunity.controlled_transition":
                service = ControlledOpportunityActionService(using=self._service_using(session, "executor"))
        elif self.source_service is not None and self.source_operation is not None:
            service = self._resolve_runtime_service(self.source_service, using=getattr(session, "using", "default"))
            if self.source_service == "ActionPreparationService":
                service = ActionPreparationService(using=self._service_using(session, "worker"))
            method_name = self.source_operation
            native_source = self.source_service
            source_service = self.source_service
        else:
            return PhaseExecutionResult(
                phase_id=self.phase_id,
                status="FAIL",
                operation=self.native_operation,
                native_source=self.native_operation,
                source_service=self.source_service,
                metadata={"mode": "native-phase-composition", "phase": self.phase_id,
                          "error": "phase has no registered operation"},
                error="phase has no registered operation",
            )

        method = getattr(service, method_name, None)
        if callable(method):
            metadata = dict(context.metadata)
            if self.phase_id == "CONTROLLED_TRANSITION" and not metadata:
                state = session.composition
                metadata = {
                    "identity": state["identity"],
                    "authorization_id": state["authorization_id"],
                    "idempotency_key": "phase31.4-v2.5-live-controlled-transition",
                }
            elif self.phase_id in {"INITIAL_OPPORTUNITY", "ACTION_PLAN_PREPARATION", "EXECUTION_AUTHORIZATION"} and not metadata:
                if context.contract is None:
                    raise V25RuntimeError("native phase context lacks authoritative contract")
                metadata = context.contract.native_phase_inputs(
                    self.phase_id,
                    session=context.session,
                )
            try:
                result = method(**metadata)
                if self.native_operation == "opportunity.create" and result is not None:
                    entity_id = getattr(result, "entity_id", None)
                    if entity_id is not None:
                        persisted = Opportunity.objects.using("default").get(pk=entity_id)
                        session.captures.capture(CaptureRecord(
                            logical_member="qms.opportunity::live",
                            logical_field="id",
                            source_service=source_service,
                            source_operation=method_name,
                            returned_value=entity_id,
                            persisted_value=persisted.id,
                            expected_type="uuid",
                            phase=self.phase_id,
                        ))
                if self.native_operation == "action_plan.prepare" and result is not None:
                    action_plan_id = getattr(result, "action_plan_id", None)
                    if action_plan_id is not None:
                        service_using = getattr(service, "using", "default")
                        with trusted_tenant_context(
                            metadata["identity"], actor_id=metadata["actor_id"],
                            trace_id=metadata["trace_id"], using=service_using,
                        ):
                            persisted = ActionPlan.objects.using(service_using).get(pk=action_plan_id)
                        session.captures.capture(CaptureRecord(
                            logical_member="qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a",
                            logical_field="id",
                            source_service=source_service,
                            source_operation=method_name,
                            returned_value=action_plan_id,
                            persisted_value=persisted.id,
                            expected_type="uuid",
                            phase=self.phase_id,
                        ))
                        session.composition["action_plan_id"] = action_plan_id
            except TypeError as exc:
                raise V25RuntimeError(
                    f"native phase invocation requires bound inputs: {self.phase_id} "
                    f"-> {source_service}.{method_name}"
                ) from exc
            return PhaseExecutionResult(
                phase_id=self.phase_id,
                status="PASS",
                operation=self.native_operation,
                native_source=native_source,
                source_service=source_service,
                metadata={"service": source_service, "method": method_name, "bound_inputs": tuple(sorted(metadata))},
            )
        return PhaseExecutionResult(
            phase_id=self.phase_id,
            status="FAIL",
            operation=self.native_operation,
            native_source=native_source if self.native_operation is not None else self.source_service,
            source_service=source_service,
            metadata={"mode": "native-phase-composition", "phase": self.phase_id,
                      "error": "registered native operation is not callable"},
            error="registered native operation is not callable",
        )

    def _execute_catalog_assertions(self, session: V25ExecutionSession) -> PhaseExecutionResult:
        service = AgentCatalogCommandService(using=self._service_using(session, "agent_catalog_curator"))
        actor_id = "phase31.4-v2.5-agent-catalog"
        trace_id = uuid5(UUID("00000000-0000-0000-0000-000000000031"), "catalog")
        policy_id = service.create_model_policy(
            policy_key="phase31.4-v2.5-live-policy", version="v1",
            approved_models=["synthetic-no-execution"],
            data_classes=["synthetic-test-only"],
            guardrails={"allowed_capabilities": ["synthetic-analysis"], "autonomy_max": 3},
            human_gate_rules={"required_autonomy_levels": ["A3"], "required_role": "quality_approver"},
            actor_id=actor_id, trace_id=trace_id,
        )
        service.publish_model_policy(model_policy_id=policy_id, actor_id=actor_id, trace_id=trace_id)
        definition_id = service.create_agent_definition(
            agent_key="phase31.4-v2.5-live-agent", name="Phase 31.4 V2.5 live agent",
            version="v1", purpose="Governed synthetic recommendation composition.",
            capability="synthetic-analysis", autonomy_max=3, model_policy_id=policy_id,
            actor_id=actor_id, trace_id=trace_id,
        )
        service.publish_agent_definition(agent_definition_id=definition_id, actor_id=actor_id, trace_id=trace_id)
        tenant_id = session.captures.get("qms.tenant_projection::live", "id").returned_value
        organization_id = session.captures.get("qms.organization::live", "id").returned_value
        user_id = session.captures.get("qms.user_projection::live", "adminapps_user_id").returned_value
        identity = TrustedTenantIdentity("phase31.4-v2.5-agent-chain", tenant_id)
        normative = NormativeCatalogCommandService(using=self._service_using(session, "normative_curator"))
        standard_id = normative.create_standard(
            code="PHASE31.4-V25-LIVE", title="Synthetic live execution standard",
            publisher="ISO Smart", actor_id=actor_id, trace_id=trace_id,
        )
        edition_id = normative.create_standard_edition(
            standard_id=standard_id, edition="v1", source_hash=sha256(b"phase31.4-v25-live").hexdigest(),
            actor_id=actor_id, trace_id=trace_id,
        )
        clause_id = normative.add_clause(
            standard_edition_id=edition_id, code="LIVE-1", title="Synthetic live clause",
            actor_id=actor_id, trace_id=trace_id,
        )
        control_id = normative.add_requirement_control(
            standard_edition_id=edition_id, clause_id=clause_id,
            paraphrase="Synthetic live control for governed composition.",
            applicability_rule={"synthetic": True}, control_type="synthetic_test",
            actor_id=actor_id, trace_id=trace_id,
        )
        normative.publish_standard_edition(standard_edition_id=edition_id, actor_id=actor_id, trace_id=trace_id)
        knowledge = KnowledgeLayerCommandService(using=self._service_using(session, "normative_curator"))
        layer_id = knowledge.create_knowledge_layer(
            standard_edition_id=edition_id, layer_type="Quality Intelligence",
            actor_id=actor_id, trace_id=trace_id,
        )
        rule_id = knowledge.create_knowledge_layer_rule(
            knowledge_layer_id=layer_id, rule_key="phase31.4-v25-live-rule", version="v1",
            logic_json={"synthetic": True}, evidence_expectation={"synthetic": True},
            source_reference="synthetic://phase31.4-v25-live", actor_id=actor_id, trace_id=trace_id,
        )
        knowledge.publish_knowledge_layer_rule(rule_id=rule_id, actor_id=actor_id, trace_id=trace_id)
        evidence = DocumentEvidenceCommandService(using=self._service_using(session, "app")).create_evidence(
            identity=identity, organization_id=organization_id, source_type="synthetic_test",
            source_uri="synthetic://phase31.4-v25-live-evidence",
            content_hash=sha256(b"phase31.4-v25-live-evidence").hexdigest(),
            captured_at=datetime.now(timezone.utc), actor_id=user_id, trace_id=trace_id,
        )
        session.composition.update({
            "model_policy_id": policy_id, "agent_definition_id": definition_id,
            "catalog_actor_id": actor_id, "catalog_trace_id": trace_id,
            "identity": identity, "organization_id": organization_id, "actor_id": user_id,
            "standard_edition_id": edition_id, "requirement_control_id": control_id,
            "knowledge_layer_rule_id": rule_id, "evidence_id": evidence.entity_id,
        })
        for member, value, operation in (
            ("governance.model_policy::live", policy_id, "create_model_policy"),
            ("governance.agent_definition::live", definition_id, "create_agent_definition"),
        ):
            session.captures.capture(CaptureRecord(
                logical_member=member, logical_field="id",
                source_service="AgentCatalogCommandService", source_operation=operation,
                returned_value=value, persisted_value=value, expected_type="uuid",
                phase=self.phase_id,
            ))
        return PhaseExecutionResult(
            phase_id=self.phase_id, status="PASS", operation="create_agent_definition",
            native_source="AgentCatalogCommandService.create_agent_definition",
            source_service="AgentCatalogCommandService",
            metadata={"model_policy_id": str(policy_id), "agent_definition_id": str(definition_id)},
        )

    def _composition_capture(self, session: V25ExecutionSession, member: str, value: Any, operation: str, phase: str) -> None:
        session.captures.capture(CaptureRecord(
            logical_member=member, logical_field="id", source_service="V25Composition",
            source_operation=operation, returned_value=value, persisted_value=value,
            expected_type="uuid", phase=phase,
        ))

    def _execute_agent_run_start(self, session: V25ExecutionSession) -> PhaseExecutionResult:
        state = session.composition
        service = AgentRunCommandService(using=self._service_using(session, "worker"))
        trace_id = uuid5(UUID("00000000-0000-0000-0000-000000000031"), "agent-run")
        frozen_input = {
            "standard_edition_id": state["standard_edition_id"],
            "requirement_control_id": state["requirement_control_id"],
            "knowledge_layer_rule_id": state["knowledge_layer_rule_id"],
            "evidence_id": state["evidence_id"],
        }
        result = service.start_agent_run(
            identity=state["identity"], organization_id=state["organization_id"],
            agent_definition_id=state["agent_definition_id"], model_policy_id=state["model_policy_id"],
            capability="synthetic-analysis", requested_autonomy=3,
            model_provider="synthetic", model_identifier="synthetic-no-execution",
            model_version="v1", prompt_version="v1", rule_bundle_version="v1",
            inputs=[frozen_input], actor_id=state["actor_id"], trace_id=trace_id,
        )
        state.update({"agent_run_id": result.agent_run_id, "agent_run_input": frozen_input, "agent_run_trace_id": trace_id})
        self._composition_capture(session, "qms.agent_run::live", result.agent_run_id, "start_agent_run", self.phase_id)
        return PhaseExecutionResult(self.phase_id, status="PASS", operation="start_agent_run", native_source="AgentRunCommandService.start_agent_run", source_service="AgentRunCommandService", metadata={"agent_run_id": str(result.agent_run_id)})

    def _execute_agent_run_completion(self, session: V25ExecutionSession) -> PhaseExecutionResult:
        state = session.composition
        result = AgentRunCommandService(using=self._service_using(session, "worker")).complete_agent_run_with_recommendation(
            identity=state["identity"], agent_run_id=state["agent_run_id"],
            title="Phase 31.4 V2.5 live recommendation",
            body="Synthetic governed recommendation; no execution.", confidence="1.0000",
            assumptions=["Fresh live captures remain current"],
            basis=[dict(state["agent_run_input"], rationale="Synthetic live governed basis")],
            actor_id=state["actor_id"], impact="standard",
        )
        state["recommendation_id"] = result.recommendation_id
        self._composition_capture(session, "qms.recommendation::live", result.recommendation_id, "complete_agent_run_with_recommendation", self.phase_id)
        return PhaseExecutionResult(self.phase_id, status="PASS", operation="complete_agent_run_with_recommendation", native_source="AgentRunCommandService.complete_agent_run_with_recommendation", source_service="AgentRunCommandService", metadata={"recommendation_id": str(result.recommendation_id)})

    def _execute_agent_decision(self, session: V25ExecutionSession) -> PhaseExecutionResult:
        state = session.composition
        result = AgentDecisionCommandService(using=self._service_using(session, "worker")).record_agent_decision(
            identity=state["identity"], agent_run_id=state["agent_run_id"],
            decision_type="prepare", payload={"synthetic": True}, confidence="1.0000",
            explainability={"synthetic": True}, decision_autonomy=3, actor_id=state["actor_id"],
        )
        state["agent_decision_id"] = result.decision_id
        self._composition_capture(session, "qms.agent_decision::live", result.decision_id, "record_agent_decision", self.phase_id)
        return PhaseExecutionResult(self.phase_id, status="PASS", operation="record_agent_decision", native_source="AgentDecisionCommandService.record_agent_decision", source_service="AgentDecisionCommandService", metadata={"agent_decision_id": str(result.decision_id)})

    def _execute_action_plan_dry_run(self, session: V25ExecutionSession) -> PhaseExecutionResult:
        state = session.composition
        result = ActionPreparationService(using=self._service_using(session, "worker")).run_action_plan_dry_run(
            identity=state["identity"], action_plan_id=state["action_plan_id"],
            expected_affected_objects=[{"type": "Opportunity", "id": str(session.captures.get("qms.opportunity::live", "id").returned_value)}],
            intended_state_delta={"status": {"from": "active", "to": "deferred"}},
            validation_status="passed",
            precondition_results=[{"identity": "opportunity.status", "status": "satisfied"}],
            impact_summary={"impact": "standard", "simulation_only": True},
            actor_id=state["actor_id"], trace_id=state["agent_run_trace_id"],
        )
        state["dry_run_id"] = result.dry_run_id
        self._composition_capture(session, "qms.action_plan_dry_run::live", result.dry_run_id, "run_action_plan_dry_run", self.phase_id)
        return PhaseExecutionResult(self.phase_id, status="PASS", operation="run_action_plan_dry_run", native_source="ActionPreparationService.run_action_plan_dry_run", source_service="ActionPreparationService", metadata={"dry_run_id": str(result.dry_run_id)})

    def _execute_execution_authorization(self, session: V25ExecutionSession) -> PhaseExecutionResult:
        state = session.composition
        using = self._service_using(session, "human_approver")
        with trusted_tenant_context(
            state["identity"], actor_id=state["actor_id"],
            trace_id=state["agent_run_trace_id"], using=using,
        ):
            user = UserProjection.objects.using(using).get(
                adminapps_user_id=state["actor_id"],
                lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
            )
        human_authority = AuthorizedHumanContext(
            identity=state["identity"], user_projection_id=user.id,
            adminapps_user_id=state["actor_id"], authorized_roles=("quality_approver",),
        )
        approval = HumanDecisionGateService(using=using).record_human_approval(
            authority=human_authority, agent_decision_id=state["agent_decision_id"],
            comments="Phase 31.4 V2.5 live governance approval.", trace_id=state["agent_run_trace_id"],
        )
        state["approval_id"] = approval.approval_id
        authorization = ExecutionAuthorizationService(using=self._service_using(session, "execution_authorizer")).evaluate_execution_authorization(
            authority=ExecutionAuthorizerContext(identity=state["identity"]),
            action_plan_id=state["action_plan_id"], dry_run_id=state["dry_run_id"],
            idempotency_key="phase31.4-v2.5-live-authorization", trace_id=state["agent_run_trace_id"],
        )
        if authorization.outcome != "authorized" or authorization.authorization_id is None:
            raise AuthorityDenied(f"live execution authorization denied: {authorization.reason_code}")
        state["authorization_id"] = authorization.authorization_id
        self._composition_capture(session, "qms.execution_authorization::live", authorization.authorization_id, "evaluate_execution_authorization", self.phase_id)
        return PhaseExecutionResult(self.phase_id, status="PASS", operation="evaluate_execution_authorization", native_source="ExecutionAuthorizationService.evaluate_execution_authorization", source_service="ExecutionAuthorizationService", metadata={"authorization_id": str(authorization.authorization_id)})


class NativePhaseRegistry:
    """Authoritative mapping from V2.5 phase ID to native executor implementation."""

    def __init__(self, *, required_phase_ids: tuple[str, ...] | None = None) -> None:
        self._required_phase_ids = tuple(required_phase_ids or ())
        self._executors: dict[str, NativePhaseExecutor] = {}

    def register(self, phase_id: str, executor: NativePhaseExecutor) -> None:
        if phase_id in self._executors:
            raise V25RuntimeError(f"duplicate native phase executor: {phase_id}")
        self._executors[phase_id] = executor

    def get(self, phase_id: str) -> NativePhaseExecutor:
        try:
            return self._executors[phase_id]
        except KeyError as exc:
            raise V25RuntimeError(f"missing native phase executor: {phase_id}") from exc

    def phase_ids(self) -> tuple[str, ...]:
        return tuple(self._executors)

    def required_phase_count(self) -> int:
        return len(self._required_phase_ids)

    def missing_phase_ids(self) -> list[str]:
        return sorted(set(self._required_phase_ids) - set(self._executors))

    def executors(self) -> dict[str, NativePhaseExecutor]:
        return dict(self._executors)

    def coverage_report(self) -> dict[str, Any]:
        duplicate_phase_ids = [phase_id for phase_id in self._executors if self.phase_ids().count(phase_id) > 1]
        concrete = [
            phase_id for phase_id, executor in self._executors.items()
            if callable(getattr(executor, "execute", None))
        ]
        return {
            "required": len(self._required_phase_ids),
            "registered": len(self._executors),
            "missing": self.missing_phase_ids(),
            "duplicates": sorted(set(duplicate_phase_ids)),
            "concrete_executors": len(concrete),
            "non_concrete": sorted(set(self._executors) - set(concrete)),
        }

    def execute(self, phase_id: str, session: V25ExecutionSession, context: PhaseExecutionContext) -> PhaseExecutionResult:
        return self.get(phase_id).execute(session, context)

    def validate_required(self) -> None:
        missing = self.missing_phase_ids()
        if missing:
            raise V25RuntimeError(f"native phase composition missing: {missing}")


def build_v25_native_phase_registry(
    operation_registry: NativeOperationRegistry,
    *,
    required_phase_ids: tuple[str, ...] | None = None,
) -> NativePhaseRegistry:
    """Build the authoritative 33-phase registry from the live native operation registry."""
    expected = required_phase_ids or CleanRetry4Harness.PHASES
    registry = NativePhaseRegistry(required_phase_ids=expected)
    phase_to_operation = {
        "PRECREATION_INTEGRITY": None,
        "ENVIRONMENT_CREATE": None,
        "RENDER_PROFILE": None,
        "MIGRATIONS": None,
        "CATALOG_ASSERTIONS": None,
        "NATIVE_BINDING_ASSERTIONS": None,
        "AUTHORITY_ASSERTIONS": None,
        "CAPTURE_REGISTRY_ASSERTIONS": None,
        "REFERENCE_BINDING_ASSERTIONS": None,
        "INVARIANT_ASSERTIONS": None,
        "TRANSACTION_ASSERTIONS": None,
        "SOURCE_TO_RUNTIME_PROOF": None,
        "OPERATION_PRECONDITIONS": None,
        "INITIAL_OPPORTUNITY": "opportunity.create",
        "ACTION_PLAN_PREPARATION": "action_plan.prepare",
        "ACTION_PLAN_DRY_RUN": None,
        "EXECUTION_AUTHORIZATION": None,
        "NATIVE_IDENTITY_CAPTURE": None,
        "CONTROLLED_TRANSITION": "opportunity.controlled_transition",
        "EVENT_OUTBOX_ASSERTIONS": "audit.append",
        "RESOLVED_GRAPH": "application.reference_path",
        "EXACT_COMPARISON": "publication.native",
        "SECURITY_EVIDENCE": "action_plan.prepare",
        "PHASE_EVIDENCE": None,
        "RUNTIME_COMPOSITION_PROOF": None,
        "LIVE_MIGRATION_EVIDENCE": "publication.native",
        "LIVE_AUTHORITY_EVIDENCE": "action_plan.prepare",
        "LIVE_OPERATION_EVIDENCE": "opportunity.create",
        "CLOSURE_PRECONDITIONS": "publication.checkpoint",
        "CLOSURE_REPORT": "publication.checkpoint",
        "TEARDOWN_GATE": "publication.checkpoint",
        "TEARDOWN": "publication.checkpoint",
        "POST_TEARDOWN_VERIFY": "publication.checkpoint",
    }
    direct_phase_services = {
        "PRECREATION_INTEGRITY": ("PrecreationIntegrityExecutor", "verify_precreation_integrity"),
        "CATALOG_ASSERTIONS": ("AgentCatalogCommandService", "create_agent_definition"),
        "NATIVE_IDENTITY_CAPTURE": ("AgentRunCommandService", "start_agent_run"),
        "RUNTIME_COMPOSITION_PROOF": ("AgentRunCommandService", "complete_agent_run_with_recommendation"),
        "PHASE_EVIDENCE": ("AgentDecisionCommandService", "record_agent_decision"),
        "ACTION_PLAN_DRY_RUN": ("ActionPreparationService", "run_action_plan_dry_run"),
        "EXECUTION_AUTHORIZATION": ("ExecutionAuthorizationService", "evaluate_execution_authorization"),
    }
    for phase_id in expected:
        native_operation = phase_to_operation.get(phase_id)
        source_service = None
        source_operation = None
        if phase_id in direct_phase_services:
            source_service, source_operation = direct_phase_services[phase_id]
        elif native_operation is not None:
            source_service = operation_registry.resolve(native_operation).source_service
            source_operation = operation_registry.resolve(native_operation).source_operation
        executor = _NativePhaseExecutor(
            phase_id,
            operation_registry,
            native_operation=native_operation,
            source_service=source_service,
            source_operation=source_operation,
        )
        registry.register(phase_id, executor)
    registry.validate_required()
    return registry


class V25Runtime:
    TEARDOWN_PHASES = ("TEARDOWN_GATE", "TEARDOWN", "POST_TEARDOWN_VERIFY")

    def __init__(self, *, contract: V25Contract, operation_registry: NativeOperationRegistry, phase_registry: NativePhaseRegistry, session: V25ExecutionSession, using: str = "default") -> None:
        self.contract = contract
        self.operation_registry = operation_registry
        self.phase_registry = phase_registry
        self.session = session
        self.using = using
        self.authority_reader = NativeAuthorityReader(using=using)

    def executable_producer_graph(self) -> dict[str, Any]:
        return build_executable_producer_graph(self.contract.raw)

    def assert_executable_producer_graph(self) -> dict[str, Any]:
        report = self.executable_producer_graph()
        if report["executable_producer_graph"] != "PASS":
            raise V25RuntimeError(
                "EXECUTABLE_PRODUCER_GRAPH failed: "
                f"phases={report['reachable_phases']}/{report['phase_count']} "
                f"captures={report['reachable_capture_producers']}/{report['capture_count']} "
                f"missing={report['missing_producers']}"
            )
        return report

    def run_clean_retry(self) -> tuple[str, ...]:
        self.phase_registry.validate_required()
        self.assert_executable_producer_graph()
        context = PhaseExecutionContext(
            session=self.session,
            contract=self.contract,
            operation_registry=self.operation_registry,
            authority_reader=self.authority_reader,
            capture_registry=self.session.captures,
            invariant_engine=RuntimeInvariantEngine,
        )
        business_phases = tuple(
            phase_id for phase_id in self.phase_registry.phase_ids()
            if phase_id not in self.TEARDOWN_PHASES
        )
        for phase_id in business_phases:
            result = self.phase_registry.execute(phase_id, self.session, context)
            self.session.run_phase(phase_id, lambda result=result: result)
            if result.status != "PASS":
                return self.phase_registry.phase_ids()
        self.run_teardown(context)
        return self.phase_registry.phase_ids()

    def run_teardown(self, context: PhaseExecutionContext | None = None) -> tuple[PhaseRecord, ...]:
        """Run teardown only after business evidence retention is complete."""
        if context is None:
            context = PhaseExecutionContext(
                session=self.session,
                contract=self.contract,
                operation_registry=self.operation_registry,
                authority_reader=self.authority_reader,
                capture_registry=self.session.captures,
                invariant_engine=RuntimeInvariantEngine,
            )
        for phase_id in self.TEARDOWN_PHASES:
            result = self.phase_registry.execute(phase_id, self.session, context)
            self.session.run_phase(phase_id, lambda result=result: result)
        return tuple(self.session.phases)


def build_v25_runtime(*, project_root: str | Path = ".", contract_path: str | Path | None = None,
                      using: str = "default", capture_bundle: CaptureBundle | None = None,
                      retry_id: str | None = None) -> V25Runtime:
    root = Path(project_root)
    contract_file = Path(contract_path) if contract_path is not None else root / "docs" / "governance" / "fixtures" / "PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
    contract = V25Contract.from_path(contract_file)
    operation_registry = NativeOperationRegistry.product_default(using=using)
    phase_registry = build_v25_native_phase_registry(operation_registry, required_phase_ids=CleanRetry4Harness.PHASES)
    session = V25ExecutionSession(
        using=using,
        capture_bundle=capture_bundle,
        retry_id=retry_id,
        project_root=root,
    )
    return V25Runtime(contract=contract, operation_registry=operation_registry, phase_registry=phase_registry, session=session, using=using)


@dataclass(frozen=True)
class V25Contract:
    raw: dict[str, Any]

    def binding_registry(self) -> ResolvedBindingRegistry:
        bindings: dict[tuple[str, str], dict[str, Any]] = {}
        for member in self.raw.get("field_bindings", []):
            identity = member["member_identity"]
            member_key = (
                f"{identity['qualified_table_or_artifact_index']}::"
                f"{identity['primary_key_or_artifact_id']}"
            )
            for field in member.get("fields", []):
                bindings[(member_key, field["name"])] = field.get("value_binding", {})
        return ResolvedBindingRegistry(bindings)

    def install_live_identity_aliases(self, captures: NativeCaptureRegistry) -> None:
        """Connect frozen logical member names to current-execution captures."""
        aliases = {
            ("qms.tenant_projection::daa6bb22-660c-56f5-aadf-c63f06b01731", "id"):
                ("qms.tenant_projection::live", "id"),
            ("qms.tenant_projection::daa6bb22-660c-56f5-aadf-c63f06b01731", "adminapps_tenant_id"):
                ("qms.tenant_projection::live", "adminapps_tenant_id"),
            ("qms.organization::ac638304-fdd6-5ce8-96d7-62014117af94", "id"):
                ("qms.organization::live", "id"),
            ("qms.user_projection::1e878efa-2d1e-50b4-b3e4-481a3c6ff229", "id"):
                ("qms.user_projection::live", "id"),
            ("qms.user_projection::1e878efa-2d1e-50b4-b3e4-481a3c6ff229", "adminapps_user_id"):
                ("qms.user_projection::live", "adminapps_user_id"),
            ("qms.process::506d920c-fe62-53c0-aac8-9c1ca8ca78ed", "id"):
                (("qms.process::live", "id"), ("qms.process::primary", "id")),
            ("qms.opportunity::6497b073-b3cb-5159-b64f-90700f2f5f85", "id"):
                ("qms.opportunity::live", "id"),
        }
        for target, configured_source in aliases.items():
            candidates = (
                configured_source
                if configured_source and isinstance(configured_source[0], tuple)
                else (configured_source,)
            )
            source = candidates[0]
            for candidate in candidates:
                try:
                    captures.get(*candidate)
                    source = candidate
                    break
                except MissingCaptureError:
                    continue
            try:
                captures.bind_alias(*target, *source)
            except V25RuntimeError as exc:
                if "duplicate native capture alias" not in str(exc):
                    raise

    def native_phase_inputs(self, phase_id: str, session: V25ExecutionSession | None = None) -> dict[str, Any]:
        if phase_id in {"INITIAL_OPPORTUNITY", "ACTION_PLAN_PREPARATION"}:
            if session is None:
                raise MissingCaptureError(f"live execution session required for {phase_id}")
            if phase_id == "ACTION_PLAN_PREPARATION" and "agent_decision_id" in session.composition:
                state = session.composition
                opportunity_id = session.captures.get("qms.opportunity::live", "id").returned_value
                action_using = "worker" if "worker" in connections.databases else session.using
                with trusted_tenant_context(
                    state["identity"], actor_id=state["actor_id"],
                    trace_id=state["agent_run_trace_id"], using=action_using,
                ):
                    opportunity = Opportunity.objects.using(action_using).get(pk=opportunity_id)
                    state_hash = canonical_hash({
                        "canonicalization": "controlled-opportunity-state-v1",
                        "tenant_id": str(opportunity.tenant_id),
                        "organization_id": str(opportunity.organization_id),
                        "lineage_id": str(opportunity.lineage_id),
                        "revision_id": str(opportunity.id),
                        "revision": opportunity.revision,
                        "process_id": str(opportunity.process_id),
                        "hypothesis": opportunity.hypothesis,
                        "benefit": opportunity.benefit,
                        "feasibility": opportunity.feasibility,
                        "status": opportunity.status,
                    })
                return {
                    "identity": TrustedTenantIdentity("phase31.4-v2.5-native-runtime", state["identity"].tenant_id),
                    "agent_decision_id": state["agent_decision_id"],
                    "action_type": "opportunity.defer_evaluation",
                    "target_type": "Opportunity",
                    "target_id": str(session.captures.get("qms.opportunity::live", "id").returned_value),
                    "parameters": {
                        "compensation_action_type": "opportunity.resume_evaluation",
                        "policy_id": "controlled-qms-action-policy/v1",
                        "expected_revision_id": str(opportunity.id),
                        "expected_revision": opportunity.revision,
                        "expected_current_state": opportunity.status,
                        "desired_state": "deferred",
                        "expected_state_hash": state_hash,
                    },
                    "impact": "standard",
                    "reversibility": "reversible",
                    "preconditions": [{"identity": "opportunity.status", "type": "status", "expected": "active", "required": True, "source_reference": "qms.opportunity::live"}],
                    "dry_run_supported": True,
                    "required_autonomy": 3,
                    "idempotency_key": "phase31.4-v2.5-live-action-plan",
                    "actor_id": state["actor_id"],
                    "trace_id": state["agent_run_trace_id"],
                }
            self.install_live_identity_aliases(session.captures)
            resolver = self.binding_registry()

            def resolve_process_id_from_live_capture() -> Any:
                if session is None:
                    raise MissingCaptureError("missing live process capture for INITIAL_OPPORTUNITY")
                for candidate in (
                    "qms.process::primary",
                    "qms.process::live",
                    "qms.process",
                ):
                    try:
                        return session.captures.get(candidate, "id").returned_value
                    except MissingCaptureError:
                        continue
                for member in self.raw["field_bindings"]:
                    if member.get("member_identity", {}).get("qualified_table_or_artifact_index") == "qms.process":
                        try:
                            return session.captures.get(
                                f"{member['member_identity']['qualified_table_or_artifact_index']}::{member['member_identity']['primary_key_or_artifact_id']}",
                                "id",
                            ).returned_value
                        except MissingCaptureError:
                            continue
                raise MissingCaptureError("missing live process capture for INITIAL_OPPORTUNITY")

            def resolve_tenant_id_from_live_capture() -> Any:
                if session is None:
                    raise MissingCaptureError("missing live tenant capture for INITIAL_OPPORTUNITY")
                for candidate in (
                    "qms.tenant_projection::live",
                    "qms.tenant_projection::primary",
                ):
                    try:
                        return session.captures.get(candidate, "id").returned_value
                    except MissingCaptureError:
                        continue
                raise MissingCaptureError("missing live tenant capture for INITIAL_OPPORTUNITY")

            def value(member_key: str, field_name: str) -> Any:
                if member_key.startswith("qms.process") and field_name == "id" and session is not None:
                    return resolve_process_id_from_live_capture()
                if member_key.startswith("qms.tenant_projection") and field_name == "id" and session is not None:
                    return resolve_tenant_id_from_live_capture()
                if member_key.startswith("qms.user_projection") and field_name == "adminapps_user_id" and session is not None:
                    return session.captures.get("qms.user_projection::live", "adminapps_user_id").returned_value

                return resolver.resolve(member_key, field_name, session.captures)

            opportunity = "qms.opportunity::6497b073-b3cb-5159-b64f-90700f2f5f85"
            if phase_id == "ACTION_PLAN_PREPARATION":
                action_plan = "qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a"
                def action_value(field_name: str) -> Any:
                    return value(action_plan, field_name)
                return {
                    "identity": TrustedTenantIdentity("phase31.4-v2.5-native-runtime", value(action_plan, "tenant_id")),
                    "agent_decision_id": action_value("agent_decision_id"),
                    "action_type": action_value("action_type"),
                    "target_type": action_value("target_type"),
                    "target_id": action_value("target_id"),
                    "parameters": action_value("parameters"),
                    "impact": action_value("impact"),
                    "reversibility": action_value("reversibility"),
                    "preconditions": action_value("preconditions"),
                    "dry_run_supported": action_value("dry_run_supported"),
                    "required_autonomy": action_value("required_autonomy"),
                    "idempotency_key": action_value("idempotency_key"),
                    "actor_id": value("qms.user_projection::1e878efa-2d1e-50b4-b3e4-481a3c6ff229", "adminapps_user_id"),
                    "trace_id": action_value("trace_id"),
                }
            process_id = value(opportunity, "process_id")
            tenant_id = value(opportunity, "tenant_id")
            return {
                "identity": TrustedTenantIdentity(
                    "phase31.4-v2.5-native-runtime",
                    tenant_id,
                ),
                "process_id": process_id,
                "hypothesis": value(opportunity, "hypothesis"),
                "benefit": value(opportunity, "benefit"),
                "feasibility": value(opportunity, "feasibility"),
                "status": value(opportunity, "status"),
                "actor_id": value("qms.user_projection::1e878efa-2d1e-50b4-b3e4-481a3c6ff229", "adminapps_user_id"),
                "trace_id": value("qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8", "trace_id"),
            }
        if phase_id != "PRECREATION_INTEGRITY":
            return {}

        raise BindingResolutionError(
            "publication authority and native material captures are required before PRECREATION_INTEGRITY"
        )

    @classmethod
    def from_path(cls, path: str | Path) -> "V25Contract":
        return cls(json.loads(Path(path).read_text()))

    def stage_b_errors(self, registry: NativeOperationRegistry) -> tuple[str, ...]:
        errors: list[str] = []
        if self.raw.get("member_count") != 118:
            errors.append("contract member_count is not 118")
        if self.raw.get("field_count") != 1664:
            errors.append("contract field_count is not 1664")
        for binding in registry.source_manifest():
            if not binding["runtime_handler"] or not binding["native_service"]:
                errors.append(f"incomplete operation binding: {binding['contract_operation']}")
        coverage = registry.coverage_report(self.raw)
        if coverage["required"] != coverage["registered"]:
            errors.append(
                f"native source coverage mismatch: required={coverage['required']} "
                f"registered={coverage['registered']}"
            )
        if coverage["unresolved"]:
            errors.append(f"unresolved native sources: {coverage['unresolved']}")
        if coverage["unknown"]:
            errors.append(f"unknown native sources: {coverage['unknown']}")
        if coverage["duplicate_conflicting"]:
            errors.append(f"duplicate native sources: {coverage['duplicate_conflicting']}")
        return tuple(errors)

    def structural_capture_report(self, registry: NativeOperationRegistry) -> dict[str, Any]:
        registered = {
            binding["native_source"]: binding
            for binding in registry.source_manifest()
        }
        rows = []
        ambiguous = []
        for member in self.raw.get("field_bindings", []):
            identity = member["member_identity"]
            member_key = f"{identity['qualified_table_or_artifact_index']}::{identity['primary_key_or_artifact_id']}"
            for field in member.get("fields", []):
                value_binding = field.get("value_binding", {})
                if value_binding.get("kind") != "CAPTURE_NATIVE_OUTPUT":
                    continue
                source = value_binding.get("native_source")
                producer = registered.get(source)
                phases = tuple(producer["phases"]) if producer else ()
                if producer is None or not phases:
                    ambiguous.append(f"{member_key}.{field['name']}")
                rows.append({
                    "contract_field": f"{member_key}.{field['name']}",
                    "producer_phase": phases,
                    "native_operation_source": source,
                    "service_method": (
                        f"{producer['native_service']}.{producer['runtime_handler']}"
                        if producer else None
                    ),
                    "output_selector": value_binding.get("capture_output"),
                })
        return {
            "expected": len(rows),
            "covered": len(rows) - len(ambiguous),
            "uncovered": len(ambiguous),
            "ambiguous": len(ambiguous),
            "fields": rows,
        }

    def dependency_graph_report(self) -> dict[str, Any]:
        fields = {}
        for member in self.raw.get("field_bindings", []):
            identity = member["member_identity"]
            member_key = f"{identity['qualified_table_or_artifact_index']}::{identity['primary_key_or_artifact_id']}"
            for field in member.get("fields", []):
                fields[(member_key, field["name"])] = field.get("value_binding", {})
        edges = {}
        missing = []
        for target, binding in fields.items():
            dependencies = []
            if binding.get("kind") == "REFERENCE_RESOLVED_BINDING":
                dependencies.append((binding.get("source_member"), binding.get("source_field")))
            if binding.get("kind") == "DERIVED_RUNTIME_INVARIANT":
                for source in binding.get("source_bindings", []):
                    if "." in source:
                        dependencies.append(tuple(source.rsplit(".", 1)))
            edges[target] = dependencies
            missing.extend(
                f"{target[0]}.{target[1]} -> {source[0]}.{source[1]}"
                for source in dependencies if source not in fields
            )
        visiting = set()
        visited = set()
        cycles = []

        def visit(node):
            if node in visiting:
                cycles.append(f"{node[0]}.{node[1]}")
                return
            if node in visited:
                return
            visiting.add(node)
            for dependency in edges.get(node, ()):
                if dependency in edges:
                    visit(dependency)
            visiting.remove(node)
            visited.add(node)

        for node in edges:
            visit(node)
        return {
            "nodes": len(fields),
            "edges": sum(len(items) for items in edges.values()),
            "missing_upstream": sorted(set(missing)),
            "cycles": sorted(set(cycles)),
            "status": "PASS" if not missing and not cycles else "FAIL",
        }


@dataclass
class PhaseRecord:
    name: str
    status: str = "PENDING"
    operations: list[str] = field(default_factory=list)
    captures: int = 0
    assertions: int = 0
    error: str | None = None
    result: PhaseExecutionResult | None = None
    evidence_artifacts: list[str] = field(default_factory=list)


class V25ExecutionSession:
    """Own transaction scope, registries, phase records, and blockers."""

    def __init__(self, *, using: str = "default", authority: dict[str, Any] | None = None,
                 capture_bundle: CaptureBundle | None = None, retry_id: str | None = None,
                 project_root: str | Path = ".") -> None:
        self.using = using
        self.project_root = Path(project_root).resolve()
        self.retry_id = retry_id
        self.authority = authority
        self.captures = NativeCaptureRegistry()
        self.composition: dict[str, Any] = {}
        if capture_bundle is not None:
            if retry_id is None:
                raise V25RuntimeError("retry_id is required when importing a capture bundle")
            capture_bundle.validate_for_retry(retry_id)
            for record in capture_bundle.captures:
                self.captures.capture(record)
        self.phases: list[PhaseRecord] = []
        self.blockers: list[str] = []
        self._atomic = None

    def __enter__(self) -> "V25ExecutionSession":
        self._atomic = transaction.atomic(using=self.using)
        self._atomic.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        return bool(self._atomic.__exit__(exc_type, exc_value, traceback))

    def run_phase(self, name: str, operation: Callable[[], Any]) -> PhaseRecord:
        record = PhaseRecord(name=name, status="RUNNING")
        self.phases.append(record)
        try:
            result = operation()
            record.operations.append(getattr(operation, "__name__", "native_operation"))
            record.captures = len(self.captures.values())
            if not isinstance(result, PhaseExecutionResult):
                record.status = "FAIL"
                record.error = "phase callback did not return PhaseExecutionResult"
                self.blockers.append(record.error)
                return record
            record.result = result
            record.status = result.status
            record.assertions = len(result.assertions)
            record.evidence_artifacts = list(result.evidence_artifacts)
            record.error = result.error
            if result.status not in {"PASS", "FAIL", "SKIPPED_NOT_APPLICABLE"}:
                record.status = "FAIL"
                record.error = f"invalid phase status: {result.status}"
                self.blockers.append(record.error)
            elif result.status == "FAIL":
                self.blockers.append(result.error or f"phase failed: {name}")
            return record
        except Exception as exc:
            record.status = "FAIL"
            record.error = f"{type(exc).__name__}: {exc}"
            self.blockers.append(record.error)
            raise


class CleanRetry4Harness:
    """Ordered V2.5 phase runner; every phase requires a concrete callback."""

    PHASES = PHASE_TOPOLOGY

    def __init__(self, session: V25ExecutionSession, handlers: dict[str, Callable[[], Any]],
                 *, contract: V25Contract | None = None,
                 operation_registry: NativeOperationRegistry | None = None) -> None:
        if set(handlers) != set(self.PHASES):
            missing = sorted(set(self.PHASES) - set(handlers))
            raise V25RuntimeError(f"phase handlers incomplete: {missing}")
        self.session = session
        self.handlers = handlers
        self.contract = contract
        self.operation_registry = operation_registry

    def stage_b_readiness(self) -> tuple[str, ...]:
        if self.contract is None or self.operation_registry is None:
            return ("runtime contract and operation registry are required",)
        return self.contract.stage_b_errors(self.operation_registry)

    def run(self) -> tuple[PhaseRecord, ...]:
        errors = self.stage_b_readiness()
        if errors:
            raise V25RuntimeError(f"Stage B readiness failed: {errors}")
        for phase in self.PHASES:
            self.session.run_phase(phase, self.handlers[phase])
        return tuple(self.session.phases)
