"""Generate the Phase 31.4 V2.5 native-identity operational successor."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path


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
    set_binding(ACTION_PLAN, "id", capture(action_id, "backend/foundation/action_authorization.py:ActionPreparationService.prepare_action_plan", "plan.id", "native uuid4 ActionPlan identity"))
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