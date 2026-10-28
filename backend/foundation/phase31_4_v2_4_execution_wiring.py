"""Closed V2.4 member-to-phase/native-operation wiring.

The registry is executable metadata for Clean Retry 3.  Validation is source
only: it proves that every declared target is present in the frozen project
source while opening no connection and importing no Django model module.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
from pathlib import Path
from typing import Mapping

from .phase31_4_v2_4_support_producer import ContractIntegrityError, _contract


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class NativeOperation:
    phase: str
    operation_id: str
    source_path: str
    symbol: str
    transaction_owner: str
    retention_reread: bool = True
    immediate_precommit_revalidation: bool = True

    @property
    def entry_function(self) -> str:
        return f"{self.source_path}:{self.symbol}"


OPERATIONS = (
    NativeOperation("SUPPORT_FIXTURE", "freeze0.exact_support",
                    "backend/foundation/phase31_4_v2_4_support_producer.py",
                    "execute_freeze0", "fixture-exact-atomic/v1"),
    NativeOperation("SUPPORT_FIXTURE", "catalog.model_policy.create",
                    "backend/foundation/agent_runtime.py", "create_model_policy",
                    "agent_catalog_curator"),
    NativeOperation("SUPPORT_FIXTURE", "catalog.model_policy.publish",
                    "backend/foundation/agent_runtime.py", "publish_model_policy",
                    "agent_catalog_curator"),
    NativeOperation("SUPPORT_FIXTURE", "catalog.agent_definition.create",
                    "backend/foundation/agent_runtime.py", "create_agent_definition",
                    "agent_catalog_curator"),
    NativeOperation("SUPPORT_FIXTURE", "catalog.agent_definition.publish",
                    "backend/foundation/agent_runtime.py", "publish_agent_definition",
                    "agent_catalog_curator"),
    NativeOperation("SUPPORT_FIXTURE", "agent_run.start",
                    "backend/foundation/agent_runtime.py", "start_agent_run", "worker"),
    NativeOperation("SUPPORT_FIXTURE", "agent_run.complete",
                    "backend/foundation/agent_runtime.py",
                    "complete_agent_run_with_recommendation", "worker"),
    NativeOperation("SUPPORT_FIXTURE", "agent_decision.record",
                    "backend/foundation/human_decision.py", "record_agent_decision", "worker"),
    NativeOperation("SUPPORT_FIXTURE", "action_plan.prepare",
                    "backend/foundation/action_authorization.py", "prepare_action_plan", "worker"),
    NativeOperation("SUPPORT_FIXTURE", "action_plan.dry_run",
                    "backend/foundation/action_authorization.py", "run_action_plan_dry_run", "worker"),
    NativeOperation("SUPPORT_FIXTURE", "human_approval.record",
                    "backend/foundation/human_decision.py", "record_human_approval", "human_approver"),
    NativeOperation("SUPPORT_FIXTURE", "execution_authorization.grant",
                    "backend/foundation/action_authorization.py", "evaluate_execution_authorization",
                    "execution_authorizer"),
    NativeOperation("SUPPORT_FIXTURE", "opportunity.defer_evaluation",
                    "backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py",
                    "foundation_0015_controlled_opportunity_execution", "executor"),
    NativeOperation("SUPPORT_FIXTURE", "effectiveness.record",
                    "backend/foundation/effectiveness.py", "record_effectiveness_check",
                    "human_approver"),
    NativeOperation("SUPPORT_FIXTURE", "learning_signal.create",
                    "backend/foundation/governed_learning.py", "create_signal",
                    "learning_governance"),
    NativeOperation("ROOT_BOOTSTRAP", "root.bootstrap.publish",
                    "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py",
                    "publish_knowledge_layer_rule_v1", "rule_publisher"),
    NativeOperation("PROPOSAL_DELTA", "learning_proposal.create",
                    "backend/foundation/governed_learning.py", "create_proposal",
                    "learning_governance"),
    NativeOperation("REVIEW", "learning_proposal.review",
                    "backend/foundation/learning_proposal_governance.py",
                    "record_learning_proposal_review", "learning_reviewer"),
    NativeOperation("DECISION", "learning_proposal.decide",
                    "backend/foundation/learning_proposal_governance.py",
                    "record_learning_proposal_decision", "learning_approver"),
    NativeOperation("AUTHORIZATION", "learning_application.authorize",
                    "backend/foundation/learning_proposal_governance.py",
                    "authorize_learning_proposal_application", "learning_authorizer"),
    NativeOperation("ADR0017_PARITY", "application.reference_path",
                    "backend/foundation/governed_learning_application.py",
                    "apply_validated_knowledge_layer_rule_source_reference_correction_v1",
                    "learning_application"),
    NativeOperation("APPLICATION", "application.adr0017_exact_id",
                    "backend/foundation/migrations/0023_retained_synthetic_source_reference_application.py",
                    "apply_validated_knowledge_layer_rule_source_reference_correction_v1",
                    "learning_application"),
    NativeOperation("NATIVE_PUBLICATION", "publication.native",
                    "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py",
                    "publish_knowledge_layer_rule_v1", "rule_publisher"),
    NativeOperation("PUBLICATION_CHECKPOINT", "publication.checkpoint",
                    "backend/foundation/phase31_4_v2_4_support_producer.py",
                    "retain_publication_checkpoint", "read_only"),
    NativeOperation("B2_COMPATIBILITY", "publication.b2",
                    "backend/foundation/phase31_4_v2_4_support_producer.py",
                    "retain_b2_compatibility", "read_only"),
    NativeOperation("B3_RELEASE", "publication.b3",
                    "backend/foundation/phase31_4_v2_4_support_producer.py",
                    "retain_b3_release", "read_only"),
    NativeOperation("PUBLICATION_CLOSURE", "publication.closure",
                    "backend/foundation/phase31_4_v2_4_support_producer.py",
                    "retain_publication_closure", "read_only"),
    NativeOperation("NATIVE_ACTIVATION", "activation.native",
                    "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py",
                    "activate_knowledge_layer_rule_v1", "rule_activator"),
    NativeOperation("FULL_CLOSURE", "activation.closure",
                    "backend/foundation/phase31_4_v2_4_support_producer.py",
                    "retain_full_closure", "read_only"),
)


PRODUCER_PHASES: Mapping[str, tuple[str, ...]] = {
    "phase31.4.4-exact-support-producer/v1": ("SUPPORT_FIXTURE",),
    "phase31.4.4-isolated-catalog-producer/v1": ("SUPPORT_FIXTURE",),
    "phase31.4.4-agent-provenance-producer/v1": ("SUPPORT_FIXTURE",),
    "phase31.4.4-controlled-opportunity-producer/v1": ("SUPPORT_FIXTURE",),
    "phase31.4.4-effectiveness-producer/v1": ("SUPPORT_FIXTURE",),
    "phase31.4.4-learning-signal-producer/v1": ("SUPPORT_FIXTURE",),
    "knowledge-layer-rule-root-bootstrap-producer/v1": ("ROOT_BOOTSTRAP", "ROOT_DUAL_REREAD"),
    "phase31.4.4-governed-learning-producer/v2":
        ("PROPOSAL_DELTA", "REVIEW", "DECISION", "AUTHORIZATION"),
    "adr0017-exact-application-adapter/v1": ("ADR0017_PARITY", "APPLICATION"),
    "migration-0022-native-release-service/v1":
        ("ROOT_BOOTSTRAP", "NATIVE_PUBLICATION", "NATIVE_ACTIVATION"),
    "phase31.4.4-retained-evidence-producer/v1":
        ("PUBLICATION_CHECKPOINT", "B2_COMPATIBILITY", "B3_RELEASE",
         "PUBLICATION_CLOSURE", "FULL_CLOSURE"),
}


def _source_symbols(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        tree = ast.parse(text, filename=str(path))
        return {
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        } | {word for word in text.split() if word.startswith("foundation_")}
    return set()


def validate_execution_wiring() -> dict[str, tuple[str, ...]]:
    contract = _contract()
    producers = {row["producer"] for row in contract["producer_matrix"]}
    if producers != set(PRODUCER_PHASES):
        raise ContractIntegrityError("producer-to-phase wiring is not exact")
    by_phase = {operation.phase for operation in OPERATIONS}
    missing = {
        phase for phases in PRODUCER_PHASES.values() for phase in phases
        if phase not in by_phase and phase != "ROOT_DUAL_REREAD"
    }
    if missing:
        raise ContractIntegrityError(f"phases lack native operations: {sorted(missing)}")
    for operation in OPERATIONS:
        path = ROOT / operation.source_path
        if not path.is_file():
            raise ContractIntegrityError(f"native source missing: {operation.source_path}")
        text = path.read_text(encoding="utf-8")
        if operation.symbol not in text:
            raise ContractIntegrityError(
                f"native symbol missing: {operation.source_path}:{operation.symbol}"
            )
        if not operation.retention_reread or not operation.immediate_precommit_revalidation:
            raise ContractIntegrityError(f"incomplete operation envelope: {operation.operation_id}")
    members = {
        f"{row['qualified_table']}::{row['primary_key']}": PRODUCER_PHASES[row["producer"]]
        for row in contract["producer_matrix"]
    }
    if len(members) != 118:
        raise ContractIntegrityError("execution wiring does not cover 118 qualified members")
    return members
