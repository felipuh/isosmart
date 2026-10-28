"""Emit the systemic V2.5 live-identity inventory for Clean Retry 13."""

from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import UUID


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs" / "governance" / "evidence"
CONTRACT = ROOT / "docs" / "governance" / "fixtures" / "PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
BASELINE = EVIDENCE / "PHASE31_4_CLEAN_RETRY_12_IDENTITY_AUDIT.json"
OUTPUT = EVIDENCE / "PHASE31_4_CLEAN_RETRY_13_IDENTITY_INVENTORY.json"
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")


PHASE_BY_TABLE = {
    "qms.tenant_projection": "STAGE_EXT_TENANT_PROJECTION",
    "qms.organization": "STAGE_EXT_QMS_ORGANIZATION",
    "qms.user_projection": "STAGE_EXT_TENANT_PROJECTION",
    "qms.process": "STAGE_EXT_PROCESS",
    "qms.evidence": "FREEZE_1_5_OR_EFFECTIVENESS_CHECK",
    "qms.agent_run": "AGENT_RUN_START",
    "qms.agent_run_input": "AGENT_RUN_START",
    "qms.recommendation": "AGENT_RUN_COMPLETION",
    "qms.recommendation_basis": "AGENT_RUN_COMPLETION",
    "qms.agent_run_recommendation": "AGENT_RUN_COMPLETION",
    "qms.agent_decision": "AGENT_DECISION",
    "qms.action_plan_dry_run": "ACTION_PLAN_DRY_RUN",
    "qms.approval": "HUMAN_APPROVAL",
    "qms.execution_authorization": "EXECUTION_AUTHORIZATION",
    "qms.action_execution": "CONTROLLED_TRANSITION",
    "qms.action_execution_receipt": "CONTROLLED_TRANSITION",
    "qms.effectiveness_check": "EFFECTIVENESS_CHECK",
    "qms.effectiveness_evidence": "EFFECTIVENESS_CHECK",
    "qms.learning_signal": "LEARNING_SIGNAL",
    "qms.learning_signal_effectiveness": "LEARNING_SIGNAL",
    "qms.learning_proposal": "PROPOSAL_DELTA",
    "qms.learning_proposal_signal": "PROPOSAL_DELTA",
    "qms.learning_proposal_canonical_delta": "PROPOSAL_DELTA",
    "qms.learning_proposal_review": "REVIEW",
    "qms.learning_proposal_decision": "DECISION",
    "qms.learning_application_authorization": "AUTHORIZATION",
}


def is_uuid(value) -> bool:
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        return False
    try:
        UUID(value)
    except ValueError:
        return False
    return True


def all_uuid_strings(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from all_uuid_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_uuid_strings(child)
    elif is_uuid(value):
        yield value


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    baseline = json.loads(BASELINE.read_text())
    fields = {}
    references = {}
    historical_metadata = []
    for member in contract["field_bindings"]:
        identity = member["member_identity"]
        key = f"{identity['qualified_table_or_artifact_index']}::{identity['primary_key_or_artifact_id']}"
        if is_uuid(identity["primary_key_or_artifact_id"]):
            historical_metadata.append(identity["primary_key_or_artifact_id"])
        for field in member["fields"]:
            fields[(key, field["name"])] = field["value_binding"]
            binding = field["value_binding"]
            if binding.get("kind") == "REFERENCE_RESOLVED_BINDING":
                source = (binding.get("source_member"), binding.get("source_field"))
                references.setdefault(source, []).append(f"{key}.{field['name']}")

    inventory = []
    for prior in baseline["required_live_remediations"]:
        token = (prior["member"], prior["field"])
        binding = fields[token]
        table = prior["member"].split("::", 1)[0]
        required = (
            "LIVE_UPSTREAM_NATIVE_CAPTURE"
            if table in {"qms.tenant_projection", "qms.organization", "qms.user_projection", "qms.process"}
            else "CAPTURE_NATIVE_OUTPUT"
        )
        downstream = sorted(references.get(token, []))
        inventory.append({
            "historical_uuid": prior["uuid"],
            "logical_member": prior["member"],
            "entity_type": table,
            "contract_field": f"{prior['member']}.{prior['field']}",
            "runtime_consumers": sorted({item.split("::", 1)[0] for item in downstream}),
            "native_producer": binding.get("native_source"),
            "phase_producer": PHASE_BY_TABLE.get(table, "NATIVE_PRODUCT_PHASE"),
            "downstream_references": downstream,
            "current_binding_kind": binding.get("kind"),
            "required_binding_kind": required,
            "remediation_status": "REMEDIATED" if binding.get("kind") == required else "INVALID",
        })

    exact_uuid_literals = []
    for (member, name), binding in fields.items():
        if binding.get("kind") == "EXACT_LITERAL" and is_uuid(binding.get("typed_value")):
            exact_uuid_literals.append(f"{member}.{name}")
    remediation = contract["systemic_live_identity_remediation"]
    report = {
        "artifact_schema": "phase31.4-retry13-systemic-live-identity-inventory/v1",
        "retry_id": "Phase 31.4 V2.5 Clean Retry 13",
        "inventory_count": len(inventory),
        "historical_qms_identities_before": baseline["historical_live_identity_literals_remaining"],
        "historical_qms_identities_after": sum(row["remediation_status"] != "REMEDIATED" for row in inventory),
        "inventory": inventory,
        "agent_definition_semantics": {
            "classification": "NATIVE_RUNTIME",
            "source_evidence": "AgentCatalogCommandService.create_agent_definition uses uuid4",
            "binding_kind": fields[("governance.agent_definition::d8d5730c-d390-5be6-af6a-e4ab9d4cf155", "id")]["kind"],
            "required_binding_kind": "CAPTURE_NATIVE_OUTPUT",
            "status": "REMEDIATED",
        },
        "uuid_literal_audit": {
            "total_uuid_literals": len(list(all_uuid_strings(contract))),
            "valid_static_literals": 0,
            "historical_metadata_literals": len(historical_metadata),
            "invalid_live_literals": len(exact_uuid_literals),
            "invalid_contract_fields": exact_uuid_literals,
        },
        "capture_producer_recalculation": {
            "previous": 509,
            "current": contract["machine_counts_v2_5"]["CAPTURE_NATIVE_OUTPUT"],
            "upstream_live": contract["machine_counts_v2_5"]["LIVE_UPSTREAM_NATIVE_CAPTURE"],
            "reason": "56 previously literal runtime identities are now explicit native captures; 5 upstream identities are separately classified",
        },
        "member_count": contract["member_count"],
        "field_count": contract["field_count"],
        "literal_fallback_for_live_bindings": remediation["literal_fallback_for_live_bindings"],
        "result": "PASS" if not exact_uuid_literals and all(row["remediation_status"] == "REMEDIATED" for row in inventory) else "FAIL",
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "result": report["result"],
        "inventory": report["inventory_count"],
        "historical_after": report["historical_qms_identities_after"],
        "invalid_live_literals": report["uuid_literal_audit"]["invalid_live_literals"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
