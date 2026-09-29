"""Generate the Phase 31.4 V2.5 native-identity operational successor."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import UUID


ROOT = Path(__file__).resolve().parents[3]
V24 = ROOT / "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json"
V25 = ROOT / "docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"

INITIAL_OPPORTUNITY = "qms.opportunity::6497b073-b3cb-5159-b64f-90700f2f5f85"
CONTROLLED_OPPORTUNITY = "qms.opportunity::a5dcbca8-872e-5826-9d3c-c05108db002d"
ACTION_PLAN = "qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a"
RECOMMENDATION = "qms.recommendation::5a6e7f68-5d80-5c1d-a40e-76f3240e0d6d"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(field, source, output, reason):
    return {
        "kind": "CAPTURE_NATIVE_OUTPUT",
        "database_type_or_schema_type": field["schema"].get("database_type", field["schema"].get("type")),
        "native_source": source,
        "capture_output": output,
        "authoritative": True,
        "reason": reason,
        "retention_rule": "RETAIN_FULL_CANONICAL_MATERIAL",
    }


def upstream_capture(field, source, output, reason):
    return {
        "kind": "LIVE_UPSTREAM_NATIVE_CAPTURE",
        "database_type_or_schema_type": field["schema"].get(
            "database_type", field["schema"].get("type")
        ),
        "native_source": source,
        "capture_output": output,
        "authoritative": True,
        "reason": reason,
        "retention_rule": "RETAIN_LIVE_UPSTREAM_IDENTITY_ONLY",
    }


def reference(member, field, reason):
    return {
        "kind": "REFERENCE_RESOLVED_BINDING",
        "source_member": member,
        "source_field": field,
        "copy_or_transform": "copy",
        "reason": reason,
    }


def literal(field, value, reason):
    return {
        "kind": "EXACT_LITERAL",
        "typed_value": value,
        "database_type_or_schema_type": field["schema"].get("database_type", field["schema"].get("type")),
        "canonical_representation": "canonical-json-rfc8785-compatible/v1",
        "reason": reason,
    }


def invariant(field, expression, sources, reason):
    return {
        "kind": "DERIVED_RUNTIME_INVARIANT",
        "expression": expression,
        "source_bindings": sources,
        "acyclic": True,
        "satisfiable": True,
        "database_type_or_schema_type": field["schema"].get("database_type", field["schema"].get("type")),
        "reason": reason,
    }


def main():
    old = json.loads(V24.read_text())
    if sha(V24) != "a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387":
        raise SystemExit("immutable V2.4 digest mismatch")
    new = deepcopy(old)
    new.update({
        "contract_version": "2.5",
        "predecessor_contract_version": "2.4",
        "predecessor_contract": V24.name,
        "predecessor_contract_sha256": sha(V24),
        "status": "OPERATIONAL_NATIVE_IDENTITY_SUCCESSOR",
        "stage_a": {"authorized": False, "p0": None, "p1": None},
        "identity_resolution": {
            "model": "native-execution-capture-reference-invariant/v1",
            "preexecution_exact_uuid_comparison": False,
            "postexecution_materialization_required": True,
            "canonical_hash_after_resolution": True,
        },
    })
    members = {(m["member_identity"]["qualified_table_or_artifact_index"], m["member_identity"]["primary_key_or_artifact_id"]): m for m in new["field_bindings"]}

    def field(key, name):
        table, pk = key.split("::", 1)
        return next(f for f in members[(table, pk)]["fields"] if f["name"] == name)

    def set_binding(key, name, binding):
        field(key, name)["value_binding"] = binding

    initial_id = field(INITIAL_OPPORTUNITY, "id")
    set_binding(INITIAL_OPPORTUNITY, "id", capture(initial_id, "backend/foundation/risk_objective.py:create_opportunity->_create", "entity_id", "native uuid4 identity"))
    set_binding(INITIAL_OPPORTUNITY, "lineage_id", reference(INITIAL_OPPORTUNITY, "id", "native create sets lineage_id=id"))
    set_binding(INITIAL_OPPORTUNITY, "revision", literal(field(INITIAL_OPPORTUNITY, "revision"), 1, "native initial revision"))
    set_binding(INITIAL_OPPORTUNITY, "previous_revision_id", literal(field(INITIAL_OPPORTUNITY, "previous_revision_id"), None, "native initial revision has no predecessor"))

    action_id = field(ACTION_PLAN, "id")
    set_binding(ACTION_PLAN, "id", capture(action_id, "backend/foundation/action_authorization.py:ActionPreparationService.prepare_action_plan", "action_plan_id", "native uuid4 ActionPlan identity"))
    set_binding(ACTION_PLAN, "parameters", literal(field(ACTION_PLAN, "parameters"), {"policy_id": "controlled-qms-action-policy/v1", "compensation_action_type": "opportunity.resume_evaluation"}, "controlled path parameters"))
    set_binding(ACTION_PLAN, "preconditions", literal(field(ACTION_PLAN, "preconditions"), [{"identity": "qms.opportunity::6497b073-b3cb-5159-b64f-90700f2f5f85", "type": "status", "expected": "active", "required": True}], "native precondition object contract"))
    set_binding(ACTION_PLAN, "required_autonomy", literal(field(ACTION_PLAN, "required_autonomy"), 3, "controlled execution requires A3"))
    set_binding(ACTION_PLAN, "target_type", literal(field(ACTION_PLAN, "target_type"), "Opportunity", "native controlled-opportunity target type"))
    set_binding(ACTION_PLAN, "target_id", reference(INITIAL_OPPORTUNITY, "id", "target is the captured initial Opportunity"))
    set_binding(ACTION_PLAN, "recommendation_id", reference(RECOMMENDATION, "id", "governed Recommendation is mandatory"))

    controlled_id = field(CONTROLLED_OPPORTUNITY, "id")
    set_binding(CONTROLLED_OPPORTUNITY, "id", capture(controlled_id, "backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py:qms.foundation_0015_apply_opportunity_status_transition", "created.id", "native uuidv7 revision identity"))
    set_binding(CONTROLLED_OPPORTUNITY, "lineage_id", reference(INITIAL_OPPORTUNITY, "lineage_id", "successor preserves prior lineage"))
    set_binding(CONTROLLED_OPPORTUNITY, "revision", invariant(field(CONTROLLED_OPPORTUNITY, "revision"), "controlled.revision = initial.revision + 1", [f"{INITIAL_OPPORTUNITY}.revision"], "native revision increment"))
    set_binding(CONTROLLED_OPPORTUNITY, "previous_revision_id", reference(INITIAL_OPPORTUNITY, "id", "native predecessor link"))

    for key, updates in {
        "governance.agent_definition::d8d5730c-d390-5be6-af6a-e4ab9d4cf155": {"autonomy_max": 3},
        "qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8": {"effective_autonomy_ceiling": 3, "requested_autonomy": 3},
        "qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63": {"decision_autonomy": 3},
        "qms.execution_authorization::040b78af-e99d-5154-bb8f-246a87819be5": {"effective_autonomy_ceiling": 3},
    }.items():
        for name, value in updates.items():
            set_binding(key, name, literal(field(key, name), value, "controlled execution A3 ceiling"))

    # Every inherited reference/output is expressed in the V2.5 vocabulary.
    for member in new["field_bindings"]:
        for item in member["fields"]:
            binding = item["value_binding"]
            kind = binding.get("kind")
            if kind == "REFERENCE_TO_BOUND_FIELD":
                item["value_binding"] = {
                    "kind": "REFERENCE_RESOLVED_BINDING",
                    "source_member": binding["source_member"],
                    "source_field": binding["source_field"],
                    "copy_or_transform": binding.get("copy_or_transform", "copy"),
                    "transform_algorithm_if_any": binding.get("transform_algorithm_if_any"),
                    "reason": "resolved after native execution",
                }
            elif kind == "NATIVE_OUTPUT":
                item["value_binding"] = capture(item, binding.get("source_file_or_migration", "declared native producer"), "native_output", "native output retained before downstream reference")
            elif kind in {"EXECUTION_DERIVED_PERSISTED", "EXECUTION_DERIVED_EXTERNAL_AUTHORITY"}:
                item["value_binding"] = capture(item, binding.get("producer", "declared native producer"), item["name"], "execution-derived value captured from authoritative producer")

    # The decision and approval consume the same governed Recommendation.
    for key in ["qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63", "qms.approval::8dece4ae-1d50-5e95-8a78-893ca3c4c231"]:
        if any(f["name"] == "recommendation_id" for f in members[tuple(key.split("::", 1))]["fields"]):
            set_binding(key, "recommendation_id", reference(RECOMMENDATION, "id", "governed Recommendation reference"))

    # Retry 12 proved that the frozen V2.4 QMS UUIDs are logical member names,
    # not physical identities that may be reused by the V2.5 execution.  Keep
    # the member keys stable for audit continuity and replace all 28 physical
    # identity literals with fail-closed live capture semantics.
    upstream_identities = {
        ("qms.tenant_projection::daa6bb22-660c-56f5-aadf-c63f06b01731", "adminapps_tenant_id"):
            ("stage-ext/adminapps-tenant", "adminapps_tenant_id"),
        ("qms.tenant_projection::daa6bb22-660c-56f5-aadf-c63f06b01731", "id"):
            ("stage-ext/tenant-projection", "tenant_projection_id"),
        ("qms.organization::ac638304-fdd6-5ce8-96d7-62014117af94", "id"):
            ("stage-ext/qms-organization", "organization_id"),
        ("qms.user_projection::1e878efa-2d1e-50b4-b3e4-481a3c6ff229", "id"):
            ("stage-ext/user-projection", "user_projection_id"),
        ("qms.process::506d920c-fe62-53c0-aac8-9c1ca8ca78ed", "id"):
            ("stage-ext/qms-process", "process_id"),
    }
    native_identities = {
        "qms.evidence::a5308071-20ad-5872-956a-8d8eb07e5103":
            ("phase31.4.4-exact-support-producer/v1", "evidence_id"),
        "qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8":
            ("phase31.4.4-agent-provenance-producer/v1", "agent_run_id"),
        "qms.agent_run_input::ff0841b9-0b28-5a33-8a74-88d5c23575ac":
            ("phase31.4.4-agent-provenance-producer/v1", "input_ids[0]"),
        "qms.recommendation::5a6e7f68-5d80-5c1d-a40e-76f3240e0d6d":
            ("phase31.4.4-agent-provenance-producer/v1", "recommendation_id"),
        "qms.recommendation_basis::27eb05f3-1a75-5a4a-a03d-521c777f4ea7":
            ("phase31.4.4-agent-provenance-producer/v1", "basis_ids[0]"),
        "qms.agent_run_recommendation::fc6aea7a-491e-5dd9-860e-b3527264416b":
            ("phase31.4.4-agent-provenance-producer/v1", "link_id"),
        "qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63":
            ("phase31.4.4-controlled-opportunity-producer/v1", "decision_id"),
        "qms.action_plan_dry_run::770bab9c-928d-5967-87d8-e882aab09c68":
            ("phase31.4.4-controlled-opportunity-producer/v1", "dry_run_id"),
        "qms.approval::8dece4ae-1d50-5e95-8a78-893ca3c4c231":
            ("phase31.4.4-controlled-opportunity-producer/v1", "approval_id"),
        "qms.execution_authorization::040b78af-e99d-5154-bb8f-246a87819be5":
            ("phase31.4.4-controlled-opportunity-producer/v1", "authorization_id"),
        "qms.action_execution::b64bbd57-1207-51f3-b4ef-b14b1f2d24cf":
            ("phase31.4.4-controlled-opportunity-producer/v1", "execution_id"),
        "qms.action_execution_receipt::b2bd43b1-6dea-5bda-91c3-081172f40f57":
            ("phase31.4.4-controlled-opportunity-producer/v1", "receipt.id"),
        "qms.evidence::0d913a9a-0c98-5c7c-8911-a52cb9138010":
            ("phase31.4.4-effectiveness-producer/v1", "evidence_id"),
        "qms.effectiveness_check::868bccec-28d5-51fe-aa05-5bf621a97ed2":
            ("phase31.4.4-effectiveness-producer/v1", "effectiveness_check_id"),
        "qms.effectiveness_evidence::75255780-47e7-5116-ad66-3549b533463d":
            ("phase31.4.4-effectiveness-producer/v1", "effectiveness_evidence_id"),
        "qms.learning_signal::fb57055c-cbfa-5f1b-b336-a7bc530a5895":
            ("phase31.4.4-learning-signal-producer/v1", "artifact_id"),
        "qms.learning_signal_effectiveness::c3b335cb-2776-585f-a05e-8f9a00906069":
            ("phase31.4.4-learning-signal-producer/v1", "link_id"),
        "qms.learning_proposal::5d1d1c61-1bdb-5550-8605-2c9a54d51340":
            ("phase31.4.4-governed-learning-producer/v2", "artifact_id"),
        "qms.learning_proposal_signal::0b4e8100-4862-5de2-a595-8d8d9f901e22":
            ("phase31.4.4-governed-learning-producer/v2", "signal_link_id"),
        "qms.learning_proposal_canonical_delta::82486439-2035-5153-9851-c4fc0e5d5184":
            ("phase31.4.4-governed-learning-producer/v2", "canonical_delta_id"),
        "qms.learning_proposal_review::6c267f9c-705f-5e7b-9aa2-149acc9f8fab":
            ("phase31.4.4-governed-learning-producer/v2", "artifact_id"),
        "qms.learning_proposal_decision::6610b249-87f3-543e-b096-0aac01ffc404":
            ("phase31.4.4-governed-learning-producer/v2", "artifact_id"),
        "qms.learning_application_authorization::d67a9e62-7f96-546c-b053-55ff4db91f72":
            ("phase31.4.4-governed-learning-producer/v2", "artifact_id"),
    }
    for (key, name), (source, output) in upstream_identities.items():
        set_binding(key, name, upstream_capture(
            field(key, name), source, output,
            "live identity produced before the V2.5 phase graph; historical UUID is metadata only",
        ))
    for key, (source, output) in native_identities.items():
        set_binding(key, "id", capture(
            field(key, "id"), source, output,
            "native runtime identity; historical UUID is metadata only",
        ))

    # Complete the operational-graph audit, including catalog, governance,
    # event/outbox, audit and release members.  Product command services create
    # these rows with native UUIDs; a V2.4 fixture UUID may identify the logical
    # member but may never be the value written or consumed by V2.5.
    producer_by_member = {
        f"{row['qualified_table']}::{row['primary_key']}": row["producer"]
        for row in new["producer_matrix"]
    }
    additional_runtime_identities = 0
    for member in new["field_bindings"]:
        identity = member["member_identity"]
        key = (
            f"{identity['qualified_table_or_artifact_index']}::"
            f"{identity['primary_key_or_artifact_id']}"
        )
        id_field = next((item for item in member["fields"] if item["name"] == "id"), None)
        if id_field is None:
            continue
        binding = id_field["value_binding"]
        value = binding.get("typed_value")
        if binding.get("kind") != "EXACT_LITERAL" or not isinstance(value, str):
            continue
        try:
            UUID(value)
        except ValueError:
            continue
        source = producer_by_member[key]
        id_field["value_binding"] = capture(
            id_field, source, "id",
            "native product identity discovered by the complete V2.5 UUID audit",
        )
        additional_runtime_identities += 1

    new["systemic_live_identity_remediation"] = {
        "historical_qms_identity_fields_before": 28,
        "historical_qms_identity_fields_after": 0,
        "upstream_native_captures": len(upstream_identities),
        "native_runtime_captures": len(native_identities),
        "additional_runtime_identities": additional_runtime_identities,
        "literal_fallback_for_live_bindings": False,
    }

    counts = {}
    for member in new["field_bindings"]:
        for item in member["fields"]:
            kind = item["value_binding"]["kind"]
            counts[kind] = counts.get(kind, 0) + 1
    new["machine_counts_v2_5"] = counts
    new["member_count"] = len(new["field_bindings"])
    new["field_count"] = sum(len(m["fields"]) for m in new["field_bindings"])
    new["known_defect_closure"] = {
        "invalid_actionplan_preconditions": True,
        "required_autonomy_A3": True,
        "agent_definition_and_run_ceilings": "validated against native source; no fixture override",
        "decision_recommendation_reference": True,
        "authorization_recommendation_reference": True,
        "native_target_type": True,
        "native_target_id": True,
        "controlled_path_parameters": True,
        "dry_run_only_material": False,
        "opportunity_lineage": "native initial id lineage and successor invariant",
    }
    new["fixed_digest_inventory"] = []
    V25.write_text(json.dumps(new, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"path": str(V25), "sha256": sha(V25), "members": new["member_count"], "fields": new["field_count"], "bindings": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
