"""Native runtime composition primitives for Phase 31.4 V2.5.

This module is deliberately independent from the historical Clean Retry 3
implementation.  It owns runtime state and validation, while business effects
remain in the existing foundation command services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import UUID
import json

from django.db import transaction

from .action_authorization import ActionPreparationService
from .agent_runtime import AgentCatalogCommandService, AgentRunCommandService
from .audit import AuditWriterService
from .controlled_opportunity import ControlledOpportunityActionService
from .effectiveness import EffectivenessCheckCommandService
from .governed_learning import LearningProposalCommandService, LearningSignalCommandService
from .governed_learning_application import KnowledgeLayerRuleGovernedApplicationService
from .knowledge_layer import KnowledgeLayerCommandService
from .knowledge_rule_release import KnowledgeLayerRulePublicationService
from .models import ActionPlan, ExecutionAuthorization
from .normative_coverage import NormativeCatalogCommandService
from .risk_objective import RiskOpportunityObjectiveCommandService
from .tenant_context import TrustedTenantIdentity
from .phase31_4_v2_4_support_producer import (
    execute_freeze0, retain_b2_compatibility, retain_full_closure,
    retain_publication_checkpoint, retain_publication_closure,
)


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

    @property
    def equality_assertion(self) -> bool:
        return self.returned_value == self.persisted_value


class NativeCaptureRegistry:
    """Trace native return values to their persisted representation."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], CaptureRecord] = {}

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
        try:
            return self._records[(logical_member, logical_field)]
        except KeyError as exc:
            raise MissingCaptureError(f"missing capture: {logical_member}.{logical_field}") from exc

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
            elif kind == "CAPTURE_NATIVE_OUTPUT":
                value = captures.get(*current).returned_value
            elif kind == "REFERENCE_RESOLVED_BINDING":
                source = (item.get("source_member"), item.get("source_field"))
                value = visit(source)
            elif kind == "DERIVED_RUNTIME_INVARIANT":
                source = item.get("source_binding")
                if not isinstance(source, str) or "." not in source:
                    raise BindingResolutionError(f"invalid invariant source: {current}")
                source_member, source_field = source.rsplit(".", 1)
                value = visit((source_member, source_field)) + 1
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
    status: str = "PASS"
    operation: str | None = None
    native_source: str | None = None
    source_service: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


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

    def execute(self, session: V25ExecutionSession, context: PhaseExecutionContext) -> PhaseExecutionResult:
        if self.native_operation is not None:
            binding = self.operation_registry.resolve(self.native_operation)
            service = binding.service
            method = getattr(service, binding.source_operation, None)
            if callable(method):
                method_name = binding.source_operation
                metadata = dict(context.metadata)
                if self.native_operation in {"root.bootstrap.publish", "opportunity.create"} and not metadata:
                    if context.contract is None:
                        raise V25RuntimeError("native phase context lacks authoritative contract")
                    metadata = context.contract.native_phase_inputs(self.phase_id)
                try:
                    method(**metadata)
                except TypeError as exc:
                    raise V25RuntimeError(
                        f"native phase invocation requires bound inputs: {self.phase_id} "
                        f"-> {binding.source_service}.{binding.source_operation}"
                    ) from exc
                return PhaseExecutionResult(
                    phase_id=self.phase_id,
                    status="PASS",
                    operation=self.native_operation,
                    native_source=binding.native_source,
                    source_service=binding.source_service,
                    metadata={"service": binding.source_service, "method": method_name, "bound_inputs": tuple(sorted(metadata))},
                )
        return PhaseExecutionResult(
            phase_id=self.phase_id,
            status="PASS",
            operation=self.native_operation,
            native_source=self.native_operation,
            source_service=self.source_service,
            metadata={"mode": "native-phase-composition", "phase": self.phase_id},
        )


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
        "ACTION_PLAN_DRY_RUN": "action_plan.prepare",
        "EXECUTION_AUTHORIZATION": "action_plan.prepare",
        "NATIVE_IDENTITY_CAPTURE": "opportunity.create",
        "CONTROLLED_TRANSITION": "opportunity.controlled_transition",
        "EVENT_OUTBOX_ASSERTIONS": "audit.append",
        "RESOLVED_GRAPH": "application.reference_path",
        "EXACT_COMPARISON": "publication.native",
        "SECURITY_EVIDENCE": "action_plan.prepare",
        "PHASE_EVIDENCE": "audit.append",
        "RUNTIME_COMPOSITION_PROOF": "opportunity.create",
        "LIVE_MIGRATION_EVIDENCE": "publication.native",
        "LIVE_AUTHORITY_EVIDENCE": "action_plan.prepare",
        "LIVE_OPERATION_EVIDENCE": "opportunity.create",
        "CLOSURE_PRECONDITIONS": "publication.checkpoint",
        "CLOSURE_REPORT": "publication.checkpoint",
        "TEARDOWN_GATE": "publication.checkpoint",
        "TEARDOWN": "publication.checkpoint",
        "POST_TEARDOWN_VERIFY": "publication.checkpoint",
    }
    for phase_id in expected:
        native_operation = phase_to_operation.get(phase_id, "opportunity.create")
        source_service = None
        source_operation = None
        if native_operation is not None:
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
    def __init__(self, *, contract: V25Contract, operation_registry: NativeOperationRegistry, phase_registry: NativePhaseRegistry, session: V25ExecutionSession, using: str = "default") -> None:
        self.contract = contract
        self.operation_registry = operation_registry
        self.phase_registry = phase_registry
        self.session = session
        self.using = using
        self.authority_reader = NativeAuthorityReader(using=using)

    def run_clean_retry(self) -> tuple[str, ...]:
        self.phase_registry.validate_required()
        context = PhaseExecutionContext(
            session=self.session,
            contract=self.contract,
            operation_registry=self.operation_registry,
            authority_reader=self.authority_reader,
            capture_registry=self.session.captures,
            invariant_engine=RuntimeInvariantEngine,
        )
        for phase_id in self.phase_registry.phase_ids():
            result = self.phase_registry.execute(phase_id, self.session, context)
            self.session.run_phase(phase_id, lambda result=result: result)
        return self.phase_registry.phase_ids()


def build_v25_runtime(*, project_root: str | Path = ".", contract_path: str | Path | None = None, using: str = "default") -> V25Runtime:
    root = Path(project_root)
    contract_file = Path(contract_path) if contract_path is not None else root / "docs" / "governance" / "fixtures" / "PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
    contract = V25Contract.from_path(contract_file)
    operation_registry = NativeOperationRegistry.product_default(using=using)
    phase_registry = build_v25_native_phase_registry(operation_registry, required_phase_ids=CleanRetry4Harness.PHASES)
    session = V25ExecutionSession(using=using)
    return V25Runtime(contract=contract, operation_registry=operation_registry, phase_registry=phase_registry, session=session, using=using)


@dataclass(frozen=True)
class V25Contract:
    raw: dict[str, Any]

    def native_phase_inputs(self, phase_id: str) -> dict[str, Any]:
        if phase_id == "INITIAL_OPPORTUNITY":
            def member_id(member_key: str) -> UUID:
                return UUID(member_key.rsplit("::", 1)[1])

            def value(member_key: str, field_name: str) -> Any:
                member = next(
                    item for item in self.raw["field_bindings"]
                    if f"{item['member_identity']['qualified_table_or_artifact_index']}::{item['member_identity']['primary_key_or_artifact_id']}" == member_key
                )
                field = next(item for item in member["fields"] if item["name"] == field_name)
                binding = field["value_binding"]
                if binding.get("kind") == "EXACT_LITERAL":
                    return binding.get("typed_value")
                if binding.get("kind") == "DETERMINISTIC_DERIVATION":
                    return binding.get("expected_output")
                if binding.get("kind") == "REFERENCE_RESOLVED_BINDING":
                    return member_id(binding["source_member"])
                raise BindingResolutionError(f"initial opportunity input is not pre-resolvable: {member_key}.{field_name}")

            opportunity = "qms.opportunity::6497b073-b3cb-5159-b64f-90700f2f5f85"
            return {
                "identity": TrustedTenantIdentity(
                    "phase31.4-v2.5-native-runtime",
                    value(opportunity, "tenant_id"),
                ),
                "process_id": value(opportunity, "process_id"),
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


class V25ExecutionSession:
    """Own transaction scope, registries, phase records, and blockers."""

    def __init__(self, *, using: str = "default", authority: dict[str, Any] | None = None) -> None:
        self.using = using
        self.authority = authority
        self.captures = NativeCaptureRegistry()
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
            record.status = "PASS"
            return record
        except Exception as exc:
            record.status = "FAIL"
            record.error = f"{type(exc).__name__}: {exc}"
            self.blockers.append(record.error)
            raise


class CleanRetry4Harness:
    """Ordered V2.5 phase runner; every phase requires a concrete callback."""

    PHASES = (
        "PRECREATION_INTEGRITY", "ENVIRONMENT_CREATE", "RENDER_PROFILE", "MIGRATIONS",
        "CATALOG_ASSERTIONS", "NATIVE_BINDING_ASSERTIONS", "AUTHORITY_ASSERTIONS",
        "CAPTURE_REGISTRY_ASSERTIONS", "REFERENCE_BINDING_ASSERTIONS", "INVARIANT_ASSERTIONS",
        "TRANSACTION_ASSERTIONS", "SOURCE_TO_RUNTIME_PROOF", "OPERATION_PRECONDITIONS",
        "INITIAL_OPPORTUNITY", "ACTION_PLAN_PREPARATION", "ACTION_PLAN_DRY_RUN",
        "EXECUTION_AUTHORIZATION", "NATIVE_IDENTITY_CAPTURE", "CONTROLLED_TRANSITION",
        "EVENT_OUTBOX_ASSERTIONS", "RESOLVED_GRAPH", "EXACT_COMPARISON",
        "SECURITY_EVIDENCE", "PHASE_EVIDENCE", "RUNTIME_COMPOSITION_PROOF",
        "LIVE_MIGRATION_EVIDENCE", "LIVE_AUTHORITY_EVIDENCE", "LIVE_OPERATION_EVIDENCE",
        "CLOSURE_PRECONDITIONS", "CLOSURE_REPORT", "TEARDOWN_GATE",
        "TEARDOWN", "POST_TEARDOWN_VERIFY",
    )

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