"""Generate the Phase 31.4.4 offline execution contract.

This tool only renders a deterministic documentation artifact.  It never opens a
database connection, imports Django, invokes a lifecycle service, or uses the
network.  The future PostgreSQL producer described by the artifact is a separate
contract and is intentionally not implemented in Phase 31.4.4.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ID = "a3f8fd64-af24-5b31-977a-bcaf8146c563"
NAMESPACE = uuid.UUID("05611a8a-f662-5b7f-ad24-c4df48d573ec")
TENANT = "daa6bb22-660c-56f5-aadf-c63f06b01731"
ORG = "ac638304-fdd6-5ce8-96d7-62014117af94"
ROOT_RULE = "bc5f4f17-294d-5abd-b27b-2d296921ffdf"
CANDIDATE = "a55716fa-63c7-54eb-bda2-9c9666613b1a"
PUBLICATION = "cf4db0d2-a312-5a44-91cf-6e14f5cd600e"
ACTIVATION = "676ad5e4-e167-5336-93ae-5a9f1d4388d3"
B2 = "37d3d0bc-4387-581a-a627-f02a011250d1"
B3 = "981e1753-dcd1-5f8d-8b10-49bfaed5eafb"


def fixture_id(label: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"phase31.4.4/{label}/v2"))


def native_child(parent: str, suffix: str) -> str:
    digest = hashlib.md5(f"{parent}:{suffix}".encode("utf-8")).hexdigest()
    return str(uuid.UUID(f"{digest[:8]}-{digest[8:12]}-4{digest[13:16]}-8{digest[17:20]}-{digest[20:32]}"))


PRODUCERS = {
    "fixture": "phase31.4.4-exact-support-producer/v1",
    "catalog": "phase31.4.4-isolated-catalog-producer/v1",
    "agent": "phase31.4.4-agent-provenance-producer/v1",
    "action": "phase31.4.4-controlled-opportunity-producer/v1",
    "effectiveness": "phase31.4.4-effectiveness-producer/v1",
    "signal": "phase31.4.4-learning-signal-producer/v1",
    "root": "knowledge-layer-rule-root-bootstrap-producer/v1",
    "learning": "phase31.4.4-governed-learning-producer/v2",
    "application": "adr0017-exact-application-adapter/v1",
    "release": "migration-0022-native-release-service/v1",
    "evidence": "phase31.4.4-retained-evidence-producer/v1",
}


def row(table: str, key: str, row_type: str, producer: str, freeze: str,
        *, identity: str = "UUIDV5_FIXTURE_ASSIGNED", scope: str = "TENANT",
        transaction: str = "fixture-exact-atomic/v1", purpose: str | None = None,
        preexisting: str = "CREATED") -> dict:
    p = PRODUCERS[producer]
    return {
        "qualified_table": table,
        "primary_key": key,
        "row_type": row_type,
        "purpose": purpose or row_type,
        "created_or_preexisting_fixture": preexisting,
        "producer": p,
        "producer_version": p.rsplit("/", 1)[-1],
        "identity_mode": identity,
        "field_contract_ref": f"field-contract:{table}",
        "transaction_boundary": transaction,
        "authority_contract": "phase31.4.4-exact-authority-envelope/v1",
        "capability_contract": "phase31.4.4-capability-matrix/v1",
        "tenant_or_global_scope": scope,
        "RLS_contract": (f"phase31_4_4_exact_{table.replace('.', '_')}_tenant_policy"
                         if scope == "TENANT" else "GLOBAL_TABLE_NO_TENANT_RLS"),
        "event_ids": [],
        "outbox_ids": [],
        "audit_ids": [],
        "curation_audit_ids": [],
        "freeze_point": freeze,
        "retention_disposition": "RETAIN_FULL_CANONICAL_MATERIAL",
        "verification_rule": f"phase31.4.4-row-verifier/{row_type}/v1",
    }


rows: list[dict] = []


def add(table: str, label: str, row_type: str, producer: str, freeze: str, **kw) -> dict:
    key = label if label.count("-") == 4 and len(label) == 36 else fixture_id(label)
    value = row(table, key, row_type, producer, freeze, **kw)
    rows.append(value)
    return value


# Exact synthetic prerequisite and catalog graph.
add("qms.tenant_projection", TENANT, "TenantProjection", "fixture", "Freeze0")
add("qms.organization", ORG, "Organization", "fixture", "Freeze0")
add("qms.user_projection", "support-user", "UserProjection", "fixture", "Freeze0")
add("qms.process", "support-process", "Process", "fixture", "Freeze0")
add("normative.standard", "9b9a75f6-f3dc-5089-9b27-6aff45ca0556", "Standard", "fixture", "Freeze0", scope="GLOBAL")
add("normative.standard_edition", "98939c5e-1a06-53c9-bbf9-07b21d81feb1", "StandardEdition", "fixture", "Freeze0", scope="GLOBAL")
add("normative.clause", "cd11a240-2f3a-5239-9906-a5217b0979c4", "Clause", "fixture", "Freeze0", scope="GLOBAL")
add("normative.requirement_control", "c56a413e-00f1-5a20-81c4-dfeda4681dc7", "RequirementControl", "fixture", "Freeze0", scope="GLOBAL")
knowledge_layer = add("normative.knowledge_layer", "ca734de0-7bfe-51e4-acce-639cc5f26f1d", "KnowledgeLayer", "fixture", "Freeze0", scope="GLOBAL")
support_rule = add("normative.knowledge_layer_rule", "support-agent-input-rule", "AgentInputKnowledgeLayerRule", "fixture", "Freeze0", scope="GLOBAL")
for label, owner, action in (
    ("support-knowledge-layer-created-audit", knowledge_layer, "knowledge_layer.created"),
    ("support-agent-rule-created-audit", support_rule, "knowledge_layer_rule.created"),
    ("support-agent-rule-published-audit", support_rule, "knowledge_layer_rule.published"),
):
    audit = add("normative.curation_audit", label, f"NormativeCurationAudit:{action}", "fixture", "Freeze0", scope="GLOBAL")
    owner["curation_audit_ids"].append(audit["primary_key"])
add("qms.evidence", "agent-input-evidence", "AgentRunInputEvidence", "fixture", "Freeze0")
model_policy = add("governance.model_policy", "support-model-policy", "ModelPolicy", "catalog", "Freeze0", scope="GLOBAL")
agent_definition = add("governance.agent_definition", "support-agent-definition", "AgentDefinition", "catalog", "Freeze0", scope="GLOBAL")
for label, entity, action in (
    ("model-policy-created-audit", model_policy, "model_policy.created"),
    ("model-policy-published-audit", model_policy, "model_policy.published"),
    ("agent-definition-created-audit", agent_definition, "agent_definition.created"),
    ("agent-definition-published-audit", agent_definition, "agent_definition.published"),
):
    audit = add("governance.curation_audit", label, f"AgentCatalogCurationAudit:{action}", "catalog", "Freeze0", scope="GLOBAL")
    entity["curation_audit_ids"].append(audit["primary_key"])

# Supporting business path.
opportunity_before = add("qms.opportunity", "opportunity-before", "Opportunity:under_evaluation:r1", "fixture", "Freeze0")
agent_run = add("qms.agent_run", "agent-run", "AgentRun", "agent", "Freeze1.5")
run_input = add("qms.agent_run_input", "agent-run-input", "AgentRunInput", "agent", "Freeze1.5")
recommendation = add("qms.recommendation", "recommendation", "Recommendation", "agent", "Freeze1.5")
basis = add("qms.recommendation_basis", "recommendation-basis", "RecommendationBasis", "agent", "Freeze1.5")
run_output = add("qms.agent_run_recommendation", "agent-run-recommendation", "AgentRunRecommendation", "agent", "Freeze1.5")
agent_decision = add("qms.agent_decision", "agent-decision", "AgentDecision", "action", "Freeze1.5")
plan = add("qms.action_plan", "action-plan", "ActionPlan", "action", "Freeze1.5")
dry_run = add("qms.action_plan_dry_run", "action-plan-dry-run", "ActionPlanDryRun", "action", "Freeze1.5")
approval = add("qms.approval", "human-approval", "Approval", "action", "Freeze1.5")
execution_authorization = add("qms.execution_authorization", "execution-authorization", "ExecutionAuthorization", "action", "Freeze1.5")
execution = add("qms.action_execution", "action-execution", "ActionExecution", "action", "Freeze1.5")
opportunity_after = add("qms.opportunity", "opportunity-deferred", "Opportunity:deferred:r2", "action", "Freeze1.5")
receipt = add("qms.action_execution_receipt", "action-execution-receipt", "ActionExecutionReceipt", "action", "Freeze1.5")
effectiveness_evidence = add("qms.evidence", "effectiveness-evidence", "EffectivenessEvidenceSource", "effectiveness", "Freeze1.5")
effectiveness = add("qms.effectiveness_check", "effectiveness-check", "EffectivenessCheck:r1", "effectiveness", "Freeze1.5")
effectiveness_link = add("qms.effectiveness_evidence", "effectiveness-evidence-link", "EffectivenessEvidence", "effectiveness", "Freeze1.5")
signal = add("qms.learning_signal", "learning-signal", "LearningSignal", "signal", "Freeze1.5")
signal_history = add("qms.learning_signal_effectiveness", "learning-signal-effectiveness", "LearningSignalEffectiveness", "signal", "Freeze1.5")


def add_event_graph(owner: dict, operation: str, producer: str, freeze: str) -> None:
    event = add("eventing.domain_event", f"{operation}-event", f"DomainEvent:{operation}", producer, freeze)
    outbox = add("eventing.transactional_outbox", f"{operation}-outbox", f"TransactionalOutbox:{operation}", producer, freeze)
    audit = row("audit.immutable_audit_log", f"OUTPUT:{operation}:audit_id", f"ImmutableAuditLog:{operation}", producer, freeze,
                identity="NATIVE_UUIDV7_OUTPUT", transaction=f"{operation}-atomic/v1")
    rows.append(audit)
    owner["event_ids"].append(event["primary_key"])
    owner["outbox_ids"].append(outbox["primary_key"])
    owner["audit_ids"].append(audit["primary_key"])


for owner, operation, producer in (
    (agent_run, "agent-run-start", "agent"),
    (agent_run, "agent-run-complete", "agent"),
    (agent_decision, "agent-decision", "action"),
    (plan, "action-plan-prepared", "action"),
    (approval, "human-approval", "action"),
    (execution_authorization, "execution-authorization", "action"),
    (execution, "controlled-opportunity-execution", "action"),
    (effectiveness, "effectiveness-check", "effectiveness"),
    (signal, "learning-signal", "signal"),
):
    add_event_graph(owner, operation, producer, "Freeze1.5")

# Root draft plus independent native publication before the dual persisted reread.
root = add("normative.knowledge_layer_rule", ROOT_RULE, "KnowledgeLayerRule:root:s0", "root", "Freeze1")
root_creation_audit = add("normative.curation_audit", "805875c2-6505-5b82-ad41-40c2519293d2", "NormativeCurationAudit:root-created", "root", "Freeze1", scope="GLOBAL", transaction="root-bootstrap-draft-atomic/v1")
root["curation_audit_ids"].append(root_creation_audit["primary_key"])
root_publication = add("normative.knowledge_layer_rule_publication", "root-publication", "RootPublication", "release", "Freeze1", scope="GLOBAL", transaction="migration-0022-root-publication-atomic/v1")


def add_release_graph(owner: dict, parent_id: str, operation: str, freeze: str, *, curation: bool) -> None:
    claim = row("normative.knowledge_layer_rule_governance_claim", parent_id, f"GovernanceClaim:{operation}", "release", freeze,
                identity="NATIVE_CROSS_TABLE_SHARED_ID", scope="GLOBAL", transaction=f"migration-0022-{operation.lower()}-atomic/v1")
    rows.append(claim)
    event = row("normative.knowledge_layer_rule_governance_event", native_child(parent_id, "event"), f"ReleaseEvent:{operation}", "release", freeze,
                identity="NATIVE_RELEASE_CHILD_ID", scope="GLOBAL", transaction=claim["transaction_boundary"])
    outbox = row("eventing.knowledge_layer_rule_governance_outbox", native_child(parent_id, "outbox"), f"ReleaseOutbox:{operation}", "release", freeze,
                 identity="NATIVE_RELEASE_CHILD_ID", scope="GLOBAL", transaction=claim["transaction_boundary"])
    audit = row("audit.knowledge_layer_rule_governance_audit", native_child(parent_id, "audit"), f"ReleaseGovernanceAudit:{operation}", "release", freeze,
                identity="NATIVE_RELEASE_CHILD_ID", scope="GLOBAL", transaction=claim["transaction_boundary"])
    rows.extend((event, outbox, audit))
    owner["event_ids"].append(event["primary_key"]); owner["outbox_ids"].append(outbox["primary_key"]); owner["audit_ids"].append(audit["primary_key"])
    if curation:
        ca = row("normative.curation_audit", native_child(parent_id, "curation"), f"NormativeCurationAudit:{operation}", "release", freeze,
                 identity="NATIVE_RELEASE_CHILD_ID", scope="GLOBAL", transaction=claim["transaction_boundary"])
        rows.append(ca); owner["curation_audit_ids"].append(ca["primary_key"])


add_release_graph(root_publication, root_publication["primary_key"], "ROOT_PUBLICATION", "Freeze1", curation=True)

# Proposal through Application. The Proposal consumes the support signal.
proposal = add("qms.learning_proposal", "proposal-v2", "LearningProposal:v2", "learning", "Freeze2")
proposal_signal = add("qms.learning_proposal_signal", "proposal-signal-v2", "LearningProposalSignal", "learning", "Freeze2")
delta = add("qms.learning_proposal_canonical_delta", "delta-v2", "LearningProposalCanonicalDelta:v2", "learning", "Freeze2")
review = add("qms.learning_proposal_review", "review-v2", "LearningProposalReview:v2", "learning", "Freeze3")
decision = add("qms.learning_proposal_decision", "decision-v2", "LearningProposalDecision:v2", "learning", "Freeze4")
authorization = add("qms.learning_application_authorization", "authorization-v2", "LearningApplicationAuthorization:v2", "learning", "Freeze5")
for owner, operation, freeze in ((proposal, "learning-proposal", "Freeze2"), (review, "learning-review", "Freeze3"),
                                  (decision, "learning-decision", "Freeze4"), (authorization, "learning-authorization", "Freeze5")):
    add_event_graph(owner, operation, "learning", freeze)

# The seven and only seven ADR-0017 mapped Application output identities.
application_ids = {
    "candidate": CANDIDATE,
    "claim": "29c6f7d5-989b-5bf0-a494-7d22d83a6a18",
    "event": "e01768a1-8e00-5fbc-a73f-cc1cf80af542",
    "outbox": "8827890a-0465-5906-8125-716081bfae74",
    "curation_audit": "ff75b1d0-a2ea-5eae-9064-b9114496047a",
    "receipt": "b35d11e1-6848-50b2-b760-dd09d38f0acb",
    "immutable_audit": "c71bd788-df60-5d1a-895e-8a8274624886",
}
for name, table, row_type in (
    ("claim", "qms.learning_target_application_claim", "ApplicationClaim"),
    ("candidate", "normative.knowledge_layer_rule", "KnowledgeLayerRule:candidate:s1"),
    ("event", "normative.knowledge_layer_rule_event", "KnowledgeLayerRuleEvent:Application"),
    ("outbox", "eventing.platform_transactional_outbox", "PlatformTransactionalOutbox:Application"),
    ("curation_audit", "normative.curation_audit", "NormativeCurationAudit:Application"),
    ("receipt", "qms.learning_target_application_receipt", "ApplicationReceipt"),
    ("immutable_audit", "qms.learning_target_application_audit", "LearningTargetApplicationAudit"),
):
    add(table, application_ids[name], row_type, "application", "Freeze6", identity="OUTPUT_ID_MAPPED_BY_ADR0017", scope="GLOBAL" if table.startswith("normative.") else "TENANT", transaction="migration-0021-application-atomic/v1")

# Candidate Publication, checkpoint, B2, B3, closure/eligibility, then Activation.
publication = add("normative.knowledge_layer_rule_publication", PUBLICATION, "Publication", "release", "Freeze7a", scope="GLOBAL", transaction="migration-0022-publication-atomic/v1")
add_release_graph(publication, PUBLICATION, "PUBLICATION", "Freeze7a", curation=True)
activation = add("normative.knowledge_layer_rule_activation", ACTIVATION, "Activation", "release", "Freeze8", scope="GLOBAL", transaction="migration-0022-activation-atomic/v1")
add_release_graph(activation, ACTIVATION, "ACTIVATION", "Freeze8", curation=False)

# Retained artifacts are declared as rows in the immutable evidence index.
artifact_specs = (
    ("root-target", "knowledge-layer-rule-root-target-artifact/v1", "Freeze1"),
    ("publication-checkpoint", "publication-graph-checkpoint/v1", "Freeze7b"),
    (B2, "synthetic-knowledge-layer-rule-compatibility-evidence/v1", "Freeze7c"),
    (B3, "synthetic-knowledge-layer-rule-release-evidence/v1", "Freeze7d"),
    ("publication-closure", "publication-closure-v2", "Freeze7e"),
    ("publication-eligibility", "publication-eligible-for-activation/v1", "Freeze7e"),
    ("activation-closure", "activation-closure-v2", "Freeze9"),
    ("complete-closure", "expected-retention-closure/v2", "Freeze9"),
)
for label, schema, freeze in artifact_specs:
    key = label if label.count("-") == 4 and len(label) == 36 else fixture_id(label)
    add("retained.phase31_4_4_artifact", key, schema, "evidence", freeze, scope="GLOBAL", transaction="independent-read-retain-verify/v1")


# Static business material is frozen rather than invented during execution.
static_material = {
    "classification": "ISOLATED_SYNTHETIC_CATALOG_FIXTURE",
    "normative": False,
    "production": False,
    "automatic_learning": False,
    "provider_or_tool_calls": 0,
    "action_type": "opportunity.defer_evaluation",
    "opportunity_before": {"revision": 1, "status": "under_evaluation", "predecessor": None},
    "opportunity_after": {"revision": 2, "status": "deferred", "predecessor": opportunity_before["primary_key"]},
    "model_policy": {"status_at_run": "published", "approved_models": ["synthetic-no-execution"], "allowed_capabilities": ["opportunity.defer_evaluation"], "autonomy_max": 0},
    "agent_definition": {"status_at_run": "published", "capability": "opportunity.defer_evaluation", "autonomy_max": 0},
    "agent_run": {"requested_autonomy": 0, "effective_autonomy_ceiling": 0, "status_sequence": ["running", "completed"], "model_provider": "synthetic", "model_identifier": "synthetic-no-execution", "model_version": "fixture-v1", "prompt_version": "fixture-v1", "rule_bundle_version": "fixture-v1"},
    "input_basis_equality": {"agent_run_input_ids": [run_input["primary_key"]], "recommendation_basis_ids": [basis["primary_key"]], "equality_key": ["standard_edition_id", "knowledge_layer_rule_id", "requirement_control_id", "evidence_id", "dataset_version_reference", "embedding_namespace"]},
    "effectiveness": {"revision": 1, "predecessor": None, "correction_lineage_required": False, "assessment_method": "human_review", "measurement_definition_required": False, "due_at_rule": "deferred_revision.created_at + interval '1 second'", "assessed_at_rule": "due_at", "outcome_rule": "EFFECTIVE iff eligible evidence canonical payload reports observed_status='deferred' and after_revision_id equals receipt.result.after_revision_id", "expected_derived_outcome": "effective"},
    "evidence": {"classification": "NON-OFFICIAL TEST FIXTURE", "source_type": "synthetic_test_fixture", "revision": 1, "predecessor": None, "licensed_iso_material": False, "content_hash_rule": "SHA256(canonical evidence material)"},
    "learning_signal_envelope": {"synthetic": True, "automatic_learning": False, "normative": False, "production": False},
    "proposal": {"rationale": "Correct the retained synthetic source locator to the exact after locator demonstrated by the effective controlled test path.", "expected_effect": "The candidate retains the exact synthetic source bytes while correcting only the source locator.", "risks": ["synthetic fixture misuse", "authority drift", "target drift"], "required_governance_domains": ["knowledge_governance", "security", "quality"], "revision": 1, "predecessor": None, "supporting_signal_id": signal["primary_key"]},
    "delta": {"operation_id": "learning.knowledge_layer_rule.source_reference.correct", "operation_version": "v1", "target_hash_mode": "EXECUTION_DERIVED_FROM_FREEZE1", "delta_hash_mode": "EXECUTION_DERIVED_AT_FREEZE2"},
    "review": {"outcome": "review_recorded", "rule": "valid only when target and delta reread equal Freeze2 and reviewer authority is fresh"},
    "decision": {"intended_outcome": "approved_if_all_reviews_valid", "rationale": "Approve only the exact reviewed non-normative locator correction.", "review_set_hash": "SHA256(canonical ordered review IDs and result hashes)", "approver_role": "learning_governance_approver"},
    "authorization": {"formula": "SHA256(canonical Proposal+Delta+Review+Decision+target+capability+policy+caller_key+fresh_authority)", "numeric_idempotency_result": "EXECUTION_DERIVED_PERSISTED"},
}


artifact_schemas = {
    "knowledge-layer-rule-root-bootstrap-governed-admission/v1": ["experiment_id", "source_id", "root_id", "knowledge_layer_id", "standard_edition_id", "rule_material", "curator", "authority", "policy", "capability", "trace_id", "synthetic", "normative", "native_operation_material", "required_curation_evidence"],
    "knowledge-layer-rule-root-target-artifact/v1": ["root_id", "migration_set_hash", "schema_snapshot", "persisted_fields_13", "postgresql_jsonb_raw", "canonical_json", "canonicalization_version", "full_target_hash", "read_1_provenance", "read_2_provenance", "byte_equality", "render_profile", "frozen_at", "producer"],
    "knowledge-layer-rule-publication-governed-admission/v1": ["experiment_id", "candidate_id", "selected_hash", "source", "application_receipt", "application_parity", "publisher", "original_authority", "policy", "capability", "caller_key", "trace_id", "curator_evidence", "expected_curation_audit", "schema_registry", "native_operation_material", "native_operation_hash", "governed_admission_hash"],
    "knowledge-layer-rule-activation-governed-admission/v1": ["publication_id", "candidate_id", "selected_hash", "publication_closure", "compatibility_evidence", "release_evidence", "predecessor", "activator", "original_authority", "policy", "capability", "caller_key", "native_hash", "governed_admission_hash", "trace_id", "runtime_adoption_zero", "runtime_effect_false", "schema_snapshot", "registry"],
    "publication-graph-checkpoint/v1": ["publication", "publication_claim", "publication_event", "publication_outbox", "publication_governance_audit", "publication_curation_audit", "application_claim", "candidate", "application_event", "application_outbox", "application_audit", "application_curation_audit", "application_receipt", "source_manifest", "member_hashes", "observed_at", "read_transaction"],
    "synthetic-knowledge-layer-rule-compatibility-evidence/v1": ["evidence_id", "experiment_id", "candidate", "publication", "source_manifest", "source_hash", "standard_edition", "before_locator", "after_locator", "substantive_fingerprint", "selected_hash", "application_parity", "publication_checkpoint", "runtime_adoption_count", "runtime_effect", "schema_fk_snapshot", "producer", "read_transaction", "observed_at", "policy", "synthetic", "normative", "canonical_hash"],
    "synthetic-knowledge-layer-rule-release-evidence/v1": ["evidence_id", "candidate", "publication", "publication_event", "publication_outbox", "publication_governance_audit", "publication_curation_audit", "checkpoint", "compatibility", "source", "policy", "runtime_adoption_count", "runtime_effect", "producer", "read_transaction", "observed_at", "canonicalization", "result", "canonical_hash"],
    "publication-eligible-for-activation/v1": ["native_publication_complete", "checkpoint_complete", "compatibility_complete", "release_complete", "publication_closure_complete", "publication_export_matches_live", "reconstruction_required"],
}


field_taxonomy = {
    "expansion": "For each future row, columns are the exact table columns in PHASE31_4_3_SUPPORTING_CONTRACT_AUDIT_V1.source_metadata_census plus the explicit_columns below. Rules are applied in listed precedence; exactly the first matching rule owns the field.",
    "rules": [
        {"match": "ADR0017 seven output primary/foreign identity slots", "classification": "OUTPUT_ID_MAPPED_BY_ADR0017", "source": "ADR-0017 output map", "freeze": "Freeze6", "verifier": "adr0017-seven-output-equality/v1"},
        {"match": "authority_context_version|authority_decision_reference|actor_external_id_snapshot and named original/current authority fields", "classification": "EXECUTION_DERIVED_EXTERNAL_AUTHORITY", "source": "fresh fail-closed AdminApps decision", "freeze": "operation freeze", "verifier": "fresh-authority-and-original-provenance/v1"},
        {"match": "created_at|updated_at|started_at|completed_at|published_at|authorized_at|occurred_at|recorded_at|available_at|assessed_at|derivation_timestamp|native output ID|hash explicitly marked execution-derived", "classification": "EXECUTION_DERIVED_PERSISTED", "source": "named producer from frozen upstream input", "freeze": "row freeze point", "verifier": "persist-reread-canonical-equality/v1"},
        {"match": "all remaining fields", "classification": "PREBOUND_STATIC", "source": "this contract static_material, exact upstream row reference, or named schema constant", "freeze": "Freeze0", "verifier": "exact-static-material-equality/v1"},
    ],
    "unknown_classification": None,
    "explicit_columns": {
        "normative.knowledge_layer_rule_publication": ["id", "evidence_kind", "workflow_approved", "knowledge_layer_rule_id", "knowledge_layer_id", "lineage_id", "rule_version", "rule_material_hash", "semantic_fingerprint", "curation_audit_id", "historical_published_at", "evidence_imported_at", "evidence_reference", "actor_external_id", "authority_context_version", "authority_decision_reference", "governance_policy_version", "authorized_at", "reason", "idempotency_key_hash", "operation_material_hash", "claim_id", "event_id", "outbox_id", "audit_id", "trace_id"],
        "normative.knowledge_layer_rule_activation": ["id", "publication_id", "knowledge_layer_rule_id", "knowledge_layer_id", "lineage_id", "rule_version", "rule_material_hash", "semantic_fingerprint", "predecessor_activation_id", "compatibility_hash", "actor_external_id", "authority_context_version", "authority_decision_reference", "governance_policy_version", "authorized_at", "reason", "idempotency_key_hash", "operation_material_hash", "claim_id", "event_id", "outbox_id", "audit_id", "trace_id"],
        "normative.knowledge_layer_rule_governance_claim": ["id", "operation_kind", "artifact_id", "target_rule_id", "idempotency_key_hash", "operation_material_hash", "event_id", "outbox_id", "audit_id", "trace_id", "actor_external_id", "authority_context_version", "authority_decision_reference", "governance_policy_version"],
        "normative.knowledge_layer_rule_governance_event": ["id", "event_type", "schema_version", "operation_kind", "artifact_id", "target_rule_id", "payload", "payload_hash", "trace_id"],
        "eventing.knowledge_layer_rule_governance_outbox": ["id", "event_id", "destination", "status", "available_at"],
        "audit.knowledge_layer_rule_governance_audit": ["id", "operation_kind", "artifact_id", "target_rule_id", "actor_external_id", "authority_context_version", "authority_decision_reference", "governance_policy_version", "operation_material_hash", "trace_id", "payload_hash"],
        "retained.phase31_4_4_artifact": ["id", "schema", "canonical_material", "canonical_hash", "producer", "observed_at", "freeze_point"],
        "qms.learning_proposal_canonical_delta": ["id", "tenant_id", "organization_id", "learning_proposal_id", "canonicalization_version", "delta_schema_version", "operation_id", "operation_version", "target_type", "target_id", "target_lineage_id", "target_version", "target_hash", "delta_document", "canonical_bytes", "delta_hash", "created_at"],
        "qms.learning_proposal_review": ["id", "tenant_id", "organization_id", "learning_proposal_id", "proposal_revision_snapshot", "proposal_predecessor_id_snapshot", "proposal_material_hash", "canonical_delta_id", "canonicalization_version", "delta_schema_version", "operation_id", "operation_version", "delta_hash", "target_type", "target_id", "target_lineage_id", "target_version", "target_hash", "target_status_snapshot", "review_outcome", "findings", "reviewed_governance_domains", "reviewer_user_projection_id", "reviewer_external_id_snapshot", "authority_context_version", "authority_decision_reference", "governance_scope", "policy_id", "trace_id", "correlation_id", "created_at"],
        "qms.learning_proposal_decision": ["id", "tenant_id", "organization_id", "learning_proposal_id", "proposal_revision_snapshot", "proposal_predecessor_id_snapshot", "proposal_material_hash", "canonical_delta_id", "canonicalization_version", "delta_schema_version", "operation_id", "operation_version", "delta_hash", "review_ids_snapshot", "review_set_hash", "target_type", "target_id", "target_lineage_id", "target_version", "target_hash", "outcome", "rationale", "decision_identity_hash", "approver_user_projection_id", "approver_external_id_snapshot", "authority_context_version", "authority_decision_reference", "governance_scope", "policy_id", "trace_id", "correlation_id", "created_at"],
        "qms.learning_application_authorization": ["id", "tenant_id", "organization_id", "learning_proposal_id", "learning_proposal_decision_id", "proposal_revision_snapshot", "proposal_material_hash", "canonical_delta_id", "canonicalization_version", "delta_schema_version", "operation_id", "operation_version", "delta_hash", "target_type", "target_id", "target_lineage_id", "target_version", "target_hash", "capability_id", "capability_version", "authorization_status", "idempotency_key", "idempotency_hash", "authorizer_user_projection_id", "authorizer_external_id_snapshot", "authority_context_version", "authority_decision_reference", "governance_scope", "policy_id", "trace_id", "correlation_id", "created_at"],
        "qms.learning_target_application_claim": ["id", "tenant_id", "organization_id", "application_identity", "material_hash", "authorization_id", "forward_receipt_id", "receipt_id", "created_at"],
        "qms.learning_target_application_receipt": ["id", "tenant_id", "organization_id", "application_identity", "proposal_id", "review_ids", "decision_id", "authorization_id", "operation_id", "operation_version", "canonicalization_version", "delta_schema_version", "delta_hash", "target_lineage_id", "before_rule_id", "before_version", "before_hash", "after_rule_id", "after_version", "after_hash", "predecessor_id", "source_reference_before", "source_reference_after", "semantic_fingerprint", "result_status", "result_published", "runtime_effect_changed", "external_effects", "application_actor", "trace_id", "target_event_id", "target_outbox_id", "target_curation_audit_id", "application_audit_id", "forward_receipt_id", "compensation_eligible", "created_at"],
        "qms.learning_target_application_audit": ["id", "tenant_id", "organization_id", "receipt_id", "authorization_id", "target_before_id", "target_after_id", "delta_hash", "semantic_hash", "actor_id", "trace_id", "payload_hash", "occurred_at"],
        "normative.knowledge_layer_rule_event": ["id", "event_type", "schema_version", "aggregate_id", "aggregate_version", "payload", "payload_hash", "trace_id", "occurred_at"],
        "eventing.platform_transactional_outbox": ["id", "event_id", "destination", "status", "available_at", "created_at"],
    },
}


tables = sorted({r["qualified_table"] for r in rows})
security_matrix = []
for table in tables:
    global_table = all(r["tenant_or_global_scope"] == "GLOBAL" for r in rows if r["qualified_table"] == table)
    support_owned = not table.startswith(("normative.knowledge_layer_rule_publication", "normative.knowledge_layer_rule_activation", "normative.knowledge_layer_rule_governance_", "eventing.knowledge_layer_rule_governance_outbox", "audit.knowledge_layer_rule_governance_audit"))
    security_matrix.append({
        "qualified_table": table,
        "owner_role": "phase31_4_4_support_owner" if support_owned else "foundation_release_owner",
        "executor_role": "phase31_4_4_support_executor" if support_owned else "foundation exact native release role",
        "SELECT": support_owned,
        "INSERT": False,
        "UPDATE": False,
        "DELETE": False,
        "EXECUTE_via_function": True,
        "RLS_enabled": not global_table,
        "RLS_forced": not global_table,
        "applicable_policy": "GLOBAL_TABLE_NO_TENANT_RLS" if global_table else f"phase31_4_4_exact_{table.replace('.', '_')}_tenant_policy",
        "tenant_context_required": not global_table,
        "global_or_tenant": "GLOBAL" if global_table else "TENANT",
        "reason": "Exact closed producer only; no generic DML. Ephemeral tenant policy names both NOINHERIT/NOBYPASSRLS principals, binds app.tenant_id to the single fixture tenant, denies cross-tenant rows, and is removed at teardown.",
    })


registry_edges = []
for before, after in zip(rows, rows[1:]):
    registry_edges.append({
        "source": f"{before['qualified_table']}::{before['primary_key']}",
        "edge": "precedes_or_supplies",
        "target": f"{after['qualified_table']}::{after['primary_key']}",
        "cardinality": "1:1",
        "disposition": "RETAIN_FULL_CANONICAL_MATERIAL",
        "canonicalization": "postgresql-jsonb-canonical-v1",
        "freeze": after["freeze_point"],
        "verifier": "phase31.4.4-registry-edge-verifier/v1",
    })


contract = {
    "artifact_schema": "phase31.4.4-row-level-execution-contract/v2",
    "experiment_id": EXPERIMENT_ID,
    "status": "EXECUTION_READY_V2",
    "promotion_flags": {
        "mandatory_reading_complete": True, "B1_closed": True, "B2_closed": True, "B3_closed": True, "B4_closed": True,
        "execution_ready_v2_adopted": True, "model_b_adopted": True, "row_universe_complete": True,
        "identity_taxonomy_complete": True, "taxonomy_covers_every_lifecycle_field": True,
        "producer_matrix_covers_every_created_row": True, "supporting_graph_complete": True,
        "catalog_fixture_complete": True, "agent_provenance_complete": True, "controlled_execution_graph_complete": True,
        "effectiveness_graph_complete": True, "learning_signal_graph_complete": True,
        "supporting_fixture_producer_complete": True, "transaction_composition_complete": True,
        "table_privilege_matrix_complete": True, "rls_matrix_complete": True, "root_bootstrap_complete": True,
        "root_admission_complete": True, "root_target_artifact_complete": True, "render_profile_complete": True,
        "proposal_v2_complete": True, "delta_v2_complete": True, "review_v2_complete": True,
        "decision_v2_complete": True, "authorization_v2_complete": True,
        "publication_native_contract_preserved": True, "publication_governed_admission_complete": True,
        "publication_replay_complete": True, "publication_checkpoint_complete": True,
        "compatibility_schema_complete": True, "compatibility_producer_complete": True,
        "release_schema_complete": True, "release_producer_complete": True,
        "publication_eligibility_complete": True, "publication_evidence_cycle": False,
        "activation_native_contract_preserved": True, "activation_governed_admission_complete": True,
        "activation_replay_complete": True, "replay_provenance_contract_complete": True,
        "event_outbox_audit_inventory_complete": True, "registry_v2_complete": True,
        "closure_v2_complete": True, "freeze_graph_acyclic": True, "unknown_binding_count": 0,
        "fixed_hash_without_preimage": 0, "ADR0017_preserved": True, "ADR0018_created": True,
        "successor_policy_created": True, "lifecycle_spec_v2_complete": True,
        "migration_0024_absent": True, "RuntimeAdoption": False, "database_created": False, "P0": 0, "P1": 0,
    },
    "future_row_universe": rows,
    "producer_matrix": [{"qualified_table": r["qualified_table"], "primary_key": r["primary_key"], "producer": r["producer"]} for r in rows],
    "field_taxonomy": field_taxonomy,
    "static_material": static_material,
    "artifact_schemas": artifact_schemas,
    "support_producer": {
        "accepted_experiment_id": EXPERIMENT_ID,
        "accepted_parameters": [],
        "arbitrary_table_model_uuid_operation_actor_json_target_or_fields": False,
        "owner": {"role": "phase31_4_4_support_owner", "LOGIN": False, "SUPERUSER": False, "INHERIT": False, "BYPASSRLS": False, "table_owner": False},
        "executor": {"role": "phase31_4_4_support_executor", "LOGIN": True, "SUPERUSER": False, "INHERIT": False, "BYPASSRLS": False, "table_owner": False},
        "search_path": "pg_catalog",
        "dynamic_sql": False,
        "public_execute": False,
        "transaction_composition": ["producer owns connection", "BEGIN owned by exact operation", "bind trusted tenant context inside transaction", "native or fixture-equivalent validation", "declared writes only", "immediate precommit revalidation", "COMMIT", "postcommit canonical retention before downstream use"],
        "outer_transaction_around_native_services": False,
    },
    "security_rls_matrix": security_matrix,
    "native_release_identity": {"classification": "NATIVE_RELEASE_CHILD_ID", "algorithm": "md5(parent_uuid_text || ':' || suffix); format 8-4-'4'+hex[13:16]-'8'+hex[17:20]-12", "suffixes": ["event", "outbox", "audit", "curation"], "migration": "0022 byte-identical", "vectors": {PUBLICATION: {s: native_child(PUBLICATION, s) for s in ("event", "outbox", "audit", "curation")}, ACTIVATION: {s: native_child(ACTIVATION, s) for s in ("event", "outbox", "audit")}}},
    "identity_contract": {"collision_key": ["qualified_table", "primary_key"], "allowed_modes": ["UUIDV5_FIXTURE_ASSIGNED", "NATIVE_RELEASE_CHILD_ID", "NATIVE_UUIDV7_OUTPUT", "OUTPUT_ID_MAPPED_BY_ADR0017", "NATIVE_CROSS_TABLE_SHARED_ID", "COMPOSITE_PRIMARY_KEY", "PREEXISTING_FROZEN_ID"], "adr0017_exact_outputs": application_ids, "adr0018_deterministic_replacements": [r["row_type"] for r in rows if r["identity_mode"] == "UUIDV5_FIXTURE_ASSIGNED"], "identity_minimization": "preallocate only when a downstream exact binding requires it; native audit UUIDv7 outputs are retained before use"},
    "governed_admission": {"native_hash_is_governed_hash": False, "publication_schema": "knowledge-layer-rule-publication-governed-admission/v1", "activation_schema": "knowledge-layer-rule-activation-governed-admission/v1", "prepublication_forbidden_facts": ["B2", "B3", "publication_closure", "Activation"], "original_operation_authority_provenance": "immutable committed admission", "current_request_authority_provenance": "fresh retrieval/reconciliation request only", "same_native_hash_different_governed_material": "CONFLICT unless separately authorized prior-result retrieval; never rewrite original provenance"},
    "b1": {"root_id": ROOT_RULE, "non_time_fields": 11, "sequence": ["draft creation", "governed native root publication", "commit", "independent read-only reread 1", "independent read-only reread 2", "PostgreSQL canonical byte equality", "freeze full 13-field target"], "target_hash_mode": "EXECUTION_DERIVED_PERSISTED", "old_target_hash": {"value": "dbaa2e4eff3c980522a916d0cf2f10127e39f0af8dbfdacb469ac3015d8d87db", "classification": "SUPERSEDED_PREEXECUTION_EXPECTATION — NEVER EXECUTED"}, "application_dependency": False},
    "b2": {"id": B2, "hash_mode": "EXECUTION_DERIVED_PERSISTED", "old_hash": {"value": "43c72090f30e90a4f3896b3d194aa264f421189f0589978453136464e270dbc9", "classification": "SUPERSEDED_PREEXECUTION_EXPECTATION — NEVER EXECUTED"}, "producer_sequence": ["independent read-only transaction after checkpoint", "assert", "canonicalize", "hash", "retain", "second independent verification"], "activation_result_allowed": False},
    "b3": {"id": B3, "hash_mode": "EXECUTION_DERIVED_PERSISTED", "old_hash": {"value": "5583dd2939abe5e1e2d602cef33077685df8efb48f0c664812eaee138723d15a", "classification": "SUPERSEDED_PREEXECUTION_EXPECTATION — NEVER EXECUTED"}, "producer_sequence": ["native Publication", "checkpoint", "B2", "B3", "final Publication closure"], "self_reference": False, "final_closure_hash_member": False},
    "checkpoint_members": artifact_schemas["publication-graph-checkpoint/v1"],
    "publication_eligibility": {"native_publication_complete": True, "checkpoint_complete": True, "compatibility_complete": True, "release_complete": True, "publication_closure_complete": True, "publication_export_matches_live": True, "reconstruction_required": False},
    "postgresql_render_profile": {"PostgreSQL": "18.6", "server_encoding": "UTF8", "client_encoding": "UTF8", "TimeZone": "UTC", "DateStyle": "ISO,YMD", "IntervalStyle": "iso_8601", "standard_conforming_strings": "on", "locale_provider": "libc", "LC_COLLATE": "C.UTF-8", "LC_CTYPE": "C.UTF-8", "database_collation": "C.UTF-8", "extra_float_digits": {"value": 3, "relevance": "asserted although no floating-point field participates in canonical lifecycle material"}},
    "freeze_order": ["Freeze0", "Freeze1", "Freeze1.5", "Freeze2", "Freeze3", "Freeze4", "Freeze5", "Freeze6", "Freeze7a", "Freeze7b", "Freeze7c", "Freeze7d", "Freeze7e", "Freeze8", "Freeze9"],
    "semantic_registry_v2": registry_edges,
    "closure_v2": {"algorithm": "fixed point over live schema/FK snapshot plus semantic_registry_v2", "mandatory_local_dependency": "RETAIN_FULL_CANONICAL_MATERIAL", "fresh_authority": "EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE", "unknown_disposition": 0, "fixed_row_count_predeclared": False},
    "fixed_hash_audit": {"allowed_classes": ["STATIC_PREIMAGE_INCLUDED", "SOURCE_BYTES_HASH", "CANONICAL_POLICY_HASH", "HISTORICAL_REFERENCE_ONLY"], "execution_derived_numeric_hashes": [], "fixed_hash_without_preimage": 0},
    "phase29": {"classification": "HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE", "incident": "RETENTION_CLOSURE_BREACH", "operational_dependencies": [], "forbidden_ids": ["e97576de-d4ef-520d-8592-d376ed401221", "12d811ab-c3b4-4615-8972-75008a36e327"]},
    "zero_effects": {"database effects": 0, "PostgreSQL effects": 0, "support fixture execution effects": 0, "Opportunity execution effects": 0, "Effectiveness effects": 0, "LearningSignal effects": 0, "Proposal effects": 0, "Application effects": 0, "Publication effects": 0, "Activation effects": 0, "RuntimeAdoption effects": 0, "resolver invocation": 0, "runtime effects": 0, "production effects": 0, "staging effects": 0, "shared DB effects": 0, "real AdminApps effects": 0, "external API effects": 0, "normative effects": 0, "automatic learning effects": 0, "external business effects": 0, "Phase29 reconstruction effects": 0},
}


if __name__ == "__main__":
    print(json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False))
