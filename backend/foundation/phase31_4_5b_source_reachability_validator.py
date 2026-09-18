"""Permanent offline validator for all V2.4 DomainEvent producer contracts."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from foundation.phase31_4_4a_field_binding_validator import ALLOWED, ENUMS, REQUIRED_BY_KIND
from foundation.phase31_4_4b_strict_type_validator import canonical_type, literal_type_error


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json"
V23 = ROOT / "docs/governance/fixtures/PHASE31_4_5A_RETRY1_ROW_LEVEL_EXECUTION_CONTRACT_V2_3.json"
CHANGESET = ROOT / "docs/governance/evidence/PHASE31_4_5B_V2_3_TO_V2_4_CHANGESET_V1.json"
REGISTRY = ROOT / "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json"
CLOSURE = ROOT / "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json"
V23_SHA = "c982588956bb6009dc2489f1a724afcfe223dda0af2b7fcb884693f43f66c1d6"
REGISTRY_SHA = "58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb"
CLOSURE_SHA = "80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425"
PROMOTED = {"90e2d38f-9600-5701-a34c-c9827eafc88c", "47be0b7e-10d0-5e96-94fd-fcaa8ad14cfd"}
EXPECTED = {
    "b043e2e7-7210-5c11-a718-c22aa97574db": ("agent_decision.recorded", "agent_decision", "iso-smart-agent-runtime", "aef69cfe-2e84-58ae-9f37-89e45640f400", "agent-decision"),
    "d087529c-6a0e-5386-ad10-39992d4f5405": ("action_plan.prepared", "action_plan", "iso-smart-action-preparation", "d10bbec9-3fde-5d9b-87f3-4856d3a7116d", "action-plan-prepared"),
    "bc7bdbed-f01c-50f1-9ad9-8dea8106f586": ("approval.recorded", "approval", "iso-smart-human-decision-gate", "e0145d7c-945f-5702-b535-e4651ed4c629", "human-approval"),
    "87e477b2-b854-55e2-95a5-2ed0785d6f39": ("execution_authorization.granted", "execution_authorization", "iso-smart-execution-authorization", "d9138ae4-37a2-52a6-bbdb-02a6f523b42c", "execution-authorization"),
    "77465ad0-559f-5317-9c26-c029e0cb16f6": ("action_execution.succeeded", "action_execution", "iso-smart-controlled-qms-execution", "552e26a9-233b-5df9-9361-2cd8e05ecc5d", "controlled-opportunity-execution"),
    "39b7cc2f-00ff-589d-b0c4-812cb35595e8": ("effectiveness_check.recorded", "effectiveness_check", "iso-smart-effectiveness-governance", "58d06fb9-deba-5d1f-9161-44fbc3152c03", "effectiveness-check"),
    "8f2146ff-48c5-5095-b034-73bb2f0b5894": ("learning_signal.created", "learning_signal", "iso-smart-learning-governance", "114a4b5d-6dd0-5128-b6f7-a9d08fe64ced", "learning-signal"),
    "005da83c-7a57-5fc5-8162-fa657a75304b": ("learning_proposal.created", "learning_proposal", "iso-smart-learning-governance", "c4ec5480-f91d-5779-9c93-bceaa2a165e0", "learning-proposal"),
    "7fc5b06e-b3ca-5a98-a250-d96ee3307b4c": ("learning_proposal.reviewed", "learning_proposal_review", "iso-smart-learning-governance", "5f2fc242-cf86-5308-b46f-1a5bd260fa24", "learning-review"),
    "82dd0d51-fc95-50c4-8047-d31b0acc1ea4": ("learning_proposal.decision_recorded", "learning_proposal_decision", "iso-smart-learning-governance", "e1858a0f-bb75-5f79-b29c-05fad2a9f2e6", "learning-decision"),
    "8bf2bb5b-4cea-5aa0-9a05-18fec0cf049c": ("learning_application.authorized", "learning_application_authorization", "iso-smart-learning-governance", "2913dd61-f579-50f7-a38a-23772f2cbcfb", "learning-authorization"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract(path: Path = CONTRACT):
    return json.loads(path.read_text())


def field_map(contract):
    result = {}
    for member in contract.get("field_bindings", []):
        identity = member["member_identity"]
        table = identity["qualified_table_or_artifact_index"]
        pk = identity["primary_key_or_artifact_id"]
        for field in member["fields"]:
            result[(table, pk, field["name"])] = field
    return result


def validate(contract):
    errors = []
    old = json.loads(V23.read_text())
    changeset = json.loads(CHANGESET.read_text())
    if sha(V23) != V23_SHA or contract.get("predecessor_contract_sha256") != V23_SHA:
        errors.append("V2.3 predecessor hash mismatch")
    for key, expected in {"contract_version": "2.4", "predecessor_contract_version": "2.3",
                          "architecture_changed": False, "row_universe_changed": False,
                          "producer_architecture_changed": False, "security_changed": False,
                          "freeze_model_changed": False, "Registry_changed": False,
                          "Closure_changed": False}.items():
        if contract.get(key) != expected:
            errors.append(f"invalid V2.4 invariant {key}")
    for key in ("future_row_universe", "producer_matrix", "security_rls_matrix", "freeze_order",
                "identity_contract", "semantic_registry_v2", "closure_v2"):
        if contract.get(key) != old.get(key):
            errors.append(f"inherited {key} drift")
    if sha(REGISTRY) != REGISTRY_SHA or sha(CLOSURE) != CLOSURE_SHA:
        errors.append("Registry/Closure V2 hash drift")
    if any((ROOT / "backend/foundation/migrations").glob("0024*")):
        errors.append("migration 0024 appeared")

    fields, old_fields = field_map(contract), field_map(old)
    if set(fields) != set(old_fields) or len(fields) != 1664:
        errors.append("118-member/1664-field universe drift")
    actual_changed = {key for key in fields if fields[key] != old_fields[key]}
    declared_changed = set()
    for item in changeset.get("corrections", []):
        table, pk = item["member"].split("::", 1)
        changed_key = (table, pk, item["field"])
        declared_changed.add(changed_key)
        if changed_key in old_fields and item.get("old_binding") != old_fields[changed_key].get("value_binding"):
            errors.append(f"changeset old binding mismatch {item['member']}.{item['field']}")
        if changed_key in fields and item.get("new_binding") != fields[changed_key].get("value_binding"):
            errors.append(f"changeset new binding mismatch {item['member']}.{item['field']}")
        if any(item.get(flag) for flag in ("business_semantics_changed", "architecture_changed", "security_changed", "transaction_changed", "identity_exception_changed")):
            errors.append(f"out-of-scope changeset entry {item['member']}.{item['field']}")
    if actual_changed != declared_changed or len(declared_changed) != changeset.get("correction_count"):
        errors.append("V2.3 to V2.4 changeset is not exact")

    graph = defaultdict(set)
    nodes = {f"{t}::{pk}.{name}" for t, pk, name in fields}
    counts = Counter()
    for (table, pk, name), field in fields.items():
        node = f"{table}::{pk}.{name}"
        binding = field.get("value_binding", {})
        kind = binding.get("kind")
        counts[kind] += 1
        if kind not in ALLOWED:
            errors.append(f"invalid binding kind {node}")
            continue
        if not REQUIRED_BY_KIND[kind] <= binding.keys():
            errors.append(f"incomplete {kind} binding {node}")
        schema_type = canonical_type(field.get("schema", {}).get("database_type") or field.get("schema", {}).get("type"))
        binding_type = canonical_type(binding.get("database_type_or_schema_type"))
        if binding_type and binding_type != schema_type:
            errors.append(f"binding/schema type mismatch {node}")
        if kind == "EXACT_LITERAL":
            mismatch = literal_type_error(field, binding.get("typed_value"))
            if mismatch:
                errors.append(f"{mismatch} {node}")
            allowed = ENUMS.get((table, name))
            if allowed is not None and binding.get("typed_value") not in allowed:
                errors.append(f"enum/CHECK mismatch {node}")
        elif kind == "REFERENCE_TO_BOUND_FIELD":
            source = f"{binding.get('source_member')}.{binding.get('source_field')}"
            graph[source].add(node)
        elif kind == "DETERMINISTIC_DERIVATION" and (not binding.get("all_preimage_inputs") or not binding.get("verification_rule")):
            errors.append(f"deterministic preimage incomplete {node}")
        elif kind == "EXECUTION_DERIVED_PERSISTED" and not all(binding.get(k) for k in ("producer", "freeze_point", "source_state", "verification_rule")):
            errors.append(f"execution-derived freeze incomplete {node}")
    for source in graph:
        if source not in nodes:
            errors.append(f"unresolved reference {source}")
    visiting, visited = set(), set()
    def cycle(node):
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        if any(cycle(target) for target in graph.get(node, ())): return True
        visiting.remove(node); visited.add(node); return False
    if any(cycle(node) for node in list(graph) if node not in visited):
        errors.append("reference cycle")

    audit = contract.get("remaining_domain_event_source_audit", {})
    rows = [r for r in contract.get("future_row_universe", []) if r.get("qualified_table") == "eventing.domain_event"]
    matrix = audit.get("matrix", [])
    if len(rows) != 13 or len({r["primary_key"] for r in rows}) != 13:
        errors.append("DomainEvent universe is not 13 unique rows")
    if len(matrix) != 13 or {r.get("row_id") for r in matrix} != {r["primary_key"] for r in rows}:
        errors.append("13-row source matrix is incomplete")
    required_true = ("source_reachable", "event_type_match", "aggregate_type_match", "aggregate_identity_match",
                     "event_identity_authorized", "payload_match", "source_match", "outbox_reachable",
                     "outbox_identity_authorized", "audit_expected", "audit_reachable", "audit_identity_authorized",
                     "writer_inventory_complete", "serialization_proven", "downstream_references_resolved")
    for row in matrix:
        if any(row.get(key) is not True for key in required_true) or row.get("status") != "PASS":
            errors.append(f"matrix row not PASS {row.get('row_id')}")
        if not row.get("source_location") or not (ROOT / row["source_location"]).is_file():
            errors.append(f"missing source location {row.get('row_id')}")
    if {r["row_id"] for r in matrix if r["row_id"] in PROMOTED} != PROMOTED:
        errors.append("promoted AgentRun evidence missing")
    def binding(table, pk, name):
        return fields[(table, pk, name)]["value_binding"]
    for pk, (event_type, aggregate_type, source, outbox_pk, slug) in EXPECTED.items():
        for name, expected in (("event_type", event_type), ("aggregate_type", aggregate_type), ("source", source)):
            if binding("eventing.domain_event", pk, name).get("typed_value") != expected:
                errors.append(f"wrong native {name} {pk}")
        if binding("eventing.domain_event", pk, "aggregate_id").get("kind") != "REFERENCE_TO_BOUND_FIELD":
            errors.append(f"wrong aggregate identity {pk}")
        if binding("eventing.domain_event", pk, "payload").get("kind") != "EXECUTION_DERIVED_PERSISTED":
            errors.append(f"impossible payload {pk}")
        if binding("eventing.domain_event", pk, "causation_id").get("typed_value", "missing") is not None:
            errors.append(f"unsupported causation {pk}")
        if binding("eventing.transactional_outbox", outbox_pk, "publish_attempts").get("typed_value") != 0:
            errors.append(f"outbox initial attempts drift {pk}")
        audit_pk = f"OUTPUT:{slug}:audit_id"
        for name, expected in (("action", event_type), ("stream_type", aggregate_type), ("entity_type", aggregate_type)):
            if binding("audit.immutable_audit_log", audit_pk, name).get("typed_value") != expected:
                errors.append(f"wrong native audit {name} {pk}")
        if binding("audit.immutable_audit_log", audit_pk, "metadata_canonical").get("kind") != "EXECUTION_DERIVED_PERSISTED":
            errors.append(f"impossible audit metadata {pk}")
        row = next((item for item in matrix if item.get("row_id") == pk), {})
        if not row.get("source_location"):
            continue
        source_text = (ROOT / row["source_location"]).read_text()
        if event_type not in source_text or aggregate_type not in source_text or source not in source_text:
            errors.append(f"native producer source drift {pk}")
    for key, expected in {"total_declared_DomainEvent_rows": 13, "already_promoted_AgentRun_rows": 2,
                          "remaining_rows_audited": 11, "duplicate_rows": 0, "unknown_rows": 0,
                          "unresolved_event_concurrency_contracts": 0, "unapproved_event_identity_substitutions": 0,
                          "unapproved_outbox_identity_substitutions": 0, "unapproved_audit_identity_substitutions": 0,
                          "undocumented_contract_differences": 0, "new_lock_required": False,
                          "ADR0019_required": False}.items():
        if audit.get(key) != expected:
            errors.append(f"bad audit metric {key}")
    for key in ("all_declared_DomainEvent_rows_mapped", "all_declared_DomainEvent_rows_source_reachable",
                "all_same_aggregate_writer_inventories_complete", "every_allocation_window_has_source_proven_serialization",
                "all_downstream_references_resolved"):
        if audit.get(key) is not True:
            errors.append(f"false audit predicate {key}")

    sources = audit.get("authoritative_source_sha256", {})
    if {path: sha(ROOT / path) for path in sources if (ROOT / path).is_file()} != sources:
        errors.append("authoritative producer source hash drift")
    migration_integrity = contract.get("frozen_source_integrity", {}).get("migration_file_sha256", {})
    if {path: sha(ROOT / path) for path in migration_integrity if (ROOT / path).is_file()} != migration_integrity:
        errors.append("migrations 0001-0023 hash drift")
    migration3 = (ROOT / "backend/foundation/migrations/0003_eventing_immutable_audit_foundation.py").read_text()
    if "CREATE INDEX foundation_domain_event_aggregate_idx" not in migration3 or "CREATE UNIQUE INDEX foundation_domain_event_aggregate_idx" in migration3:
        errors.append("DomainEvent stream index classification is not PLAIN_INDEX")
    if "pg_advisory_xact_lock" not in migration3:
        errors.append("immutable audit serialization source missing")

    machine = contract.get("machine_counts", {})
    names = {"EXACT_LITERAL": "exact_literal_count", "DETERMINISTIC_DERIVATION": "deterministic_derivation_count",
             "REFERENCE_TO_BOUND_FIELD": "reference_binding_count", "EXECUTION_DERIVED_PERSISTED": "execution_derived_persisted_count",
             "EXECUTION_DERIVED_EXTERNAL_AUTHORITY": "execution_derived_external_authority_count", "NATIVE_OUTPUT": "native_output_count",
             "ADR0017_MAPPED_OUTPUT": "adr0017_mapped_output_count"}
    for kind, key in names.items():
        if machine.get(key) != counts[kind]:
            errors.append(f"binding count mismatch {key}")
    for key in ("physical_type_mismatches", "nullability_mismatches", "enum_check_mismatches", "unbound_required_field_count",
                "ambiguous_binding_count", "conflicting_binding_count", "reference_cycle_count", "deterministic_preimage_errors",
                "execution_derived_producer_freeze_errors"):
        if machine.get(key) != 0:
            errors.append(f"strict metric nonzero {key}")

    material = json.dumps({k: v for k, v in contract.items() if k != "fixed_digest_inventory"}, sort_keys=True)
    fixed = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", material))
    if fixed != {item.get("digest") for item in contract.get("fixed_digest_inventory", [])}:
        errors.append("fixed digest inventory mismatch")
    operational_event_fields = json.dumps(
        [fields[key] for key in fields if key[0] == "eventing.domain_event" and key[1] in EXPECTED],
        sort_keys=True,
    )
    if "PHASE31.4.4A TEST ONLY" in operational_event_fields and "DomainEvent:" in operational_event_fields:
        errors.append("dangling superseded DomainEvent protocol literal")
    return errors


def metrics(contract):
    errors = validate(contract)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "domain_event_rows": len([r for r in contract.get("future_row_universe", []) if r.get("qualified_table") == "eventing.domain_event"]),
            "matrix_pass": sum(r.get("status") == "PASS" for r in contract.get("remaining_domain_event_source_audit", {}).get("matrix", []))}


if __name__ == "__main__":
    result = metrics(load_contract())
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(result["status"] != "PASS")
