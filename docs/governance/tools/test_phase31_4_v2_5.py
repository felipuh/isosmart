"""Focused offline regression for the V2.5 native identity model."""

import json
from pathlib import Path
from uuid import UUID

from phase31_4_v2_5_runtime import resolve_graph, validate


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"


def test_stage_a_has_no_p0_or_p1():
    contract = json.loads(CONTRACT.read_text())
    assert validate(contract) == []
    assert contract["member_count"] == 118
    assert contract["field_count"] == 1664


def test_native_identity_capture_and_successor_invariants():
    contract = json.loads(CONTRACT.read_text())
    captures = {
        "qms.opportunity::6497b073-b3cb-5159-b64f-90700f2f5f85.id": "11111111-1111-4111-8111-111111111111",
        "qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a.id": "22222222-2222-4222-8222-222222222222",
        "qms.opportunity::a5dcbca8-872e-5826-9d3c-c05108db002d.id": "018f0000-0000-7000-8000-000000000001",
    }
    for member in contract["field_bindings"]:
        key = f"{member['member_identity']['qualified_table_or_artifact_index']}::{member['member_identity']['primary_key_or_artifact_id']}"
        for field in member["fields"]:
            if field["value_binding"]["kind"] == "CAPTURE_NATIVE_OUTPUT":
                captures.setdefault(f"{key}.{field['name']}", f"captured:{key}.{field['name']}")
    graph, digest = resolve_graph(contract, captures)
    members = {f"{m['member_identity']['qualified_table_or_artifact_index']}::{m['member_identity']['primary_key_or_artifact_id']}": m for m in graph["field_bindings"]}
    initial = members["qms.opportunity::6497b073-b3cb-5159-b64f-90700f2f5f85"]["resolved_fields"]
    successor = members["qms.opportunity::a5dcbca8-872e-5826-9d3c-c05108db002d"]["resolved_fields"]
    assert initial["id"] == initial["lineage_id"]
    assert successor["lineage_id"] == initial["lineage_id"]
    assert successor["revision"] == initial["revision"] + 1
    assert successor["previous_revision_id"] == initial["id"]
    assert UUID(members["qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a"]["resolved_fields"]["id"])
    assert len(digest) == 64


if __name__ == "__main__":
    test_stage_a_has_no_p0_or_p1()
    test_native_identity_capture_and_successor_invariants()
    print("V2.5 focused regression: PASS")