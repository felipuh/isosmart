"""Permanent offline strict/source validator for the AgentRun V2.3 successor."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from foundation.phase31_4_4a_field_binding_validator import ALLOWED, ENUMS, REQUIRED_BY_KIND
from foundation.phase31_4_4b_strict_type_validator import STATIC_ALLOWED, canonical_type, literal_type_error


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/governance/fixtures/PHASE31_4_5A_RETRY1_ROW_LEVEL_EXECUTION_CONTRACT_V2_3.json"
V22 = ROOT / "docs/governance/fixtures/PHASE31_4_4B_ROW_LEVEL_EXECUTION_CONTRACT_V2_2.json"
CHANGESET = ROOT / "docs/governance/evidence/PHASE31_4_5A_RETRY1_SOURCE_IDENTITY_CHANGESET_V1.json"
REGISTRY = ROOT / "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json"
CLOSURE = ROOT / "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json"
RUNTIME = ROOT / "backend/foundation/agent_runtime.py"
MIGRATION_0003 = ROOT / "backend/foundation/migrations/0003_eventing_immutable_audit_foundation.py"
MIGRATION_0011 = ROOT / "backend/foundation/migrations/0011_agent_definition_run_provenance_foundation.py"
ADR0018 = ROOT / "docs/adr/0018-row-level-execution-ready-v2-contract.md"
V22_SHA = "a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d"
REGISTRY_SHA = "58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb"
CLOSURE_SHA = "80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425"
RUN_ID = "b87bdcde-c623-522f-a0ac-ff81f61df8e8"
RUN_MEMBER = f"qms.agent_run::{RUN_ID}"
EVENTS = {
    "90e2d38f-9600-5701-a34c-c9827eafc88c": "agent_run.started",
    "47be0b7e-10d0-5e96-94fd-fcaa8ad14cfd": "agent_run.completed",
}
OUTBOXES = {"078ed021-9eb9-5258-96b9-3b74e2951e77", "51dd5c7a-52d3-5779-ad95-ea6910747874"}
AUDITS = {
    "OUTPUT:agent-run-start:audit_id": "agent_run.started",
    "OUTPUT:agent-run-complete:audit_id": "agent_run.completed",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract(path: Path = CONTRACT) -> dict:
    return json.loads(path.read_text())


def field_map(contract: dict):
    result = {}
    for member in contract.get("field_bindings", []):
        identity = member["member_identity"]
        table = identity["qualified_table_or_artifact_index"]
        pk = identity["primary_key_or_artifact_id"]
        for field in member["fields"]:
            result[(table, pk, field["name"])] = (member, field)
    return result


def method_source(name: str) -> str:
    text = RUNTIME.read_text()
    tree = ast.parse(text)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AgentRunCommandService")
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)
    return ast.get_source_segment(text, method)


def value(fields, table, pk, name):
    return fields[(table, pk, name)][1]["value_binding"]


def validate(contract: dict) -> list[str]:
    errors = []
    old = json.loads(V22.read_text())
    changeset = json.loads(CHANGESET.read_text())
    if sha(V22) != V22_SHA or contract.get("predecessor_contract_sha256") != V22_SHA:
        errors.append("V2.2 predecessor hash mismatch")
    for key, expected in {
        "contract_version": "2.3", "predecessor_contract_version": "2.2",
        "predecessor_version": "2.2", "change_scope": "AGENTRUN_DOMAIN_EVENT_SOURCE_IDENTITY_CORRECTION",
        "architecture_changed": False, "row_universe_changed": False,
        "producer_architecture_changed": False, "security_changed": False,
        "freeze_model_changed": False, "Registry_changed": False, "Closure_changed": False,
    }.items():
        if contract.get(key) != expected:
            errors.append(f"invalid V2.3 invariant {key}")
    if contract.get("future_row_universe") != old.get("future_row_universe"):
        errors.append("row universe changed")
    for key in ("security_rls_matrix", "freeze_order", "identity_contract", "semantic_registry_v2", "closure_v2"):
        if contract.get(key) != old.get(key):
            errors.append(f"inherited {key} drift")
    if sha(REGISTRY) != REGISTRY_SHA or sha(CLOSURE) != CLOSURE_SHA:
        errors.append("Registry/Closure V2 hash drift")
    if any((ROOT / "backend/foundation/migrations").glob("0024*")):
        errors.append("migration 0024 appeared")

    old_fields, fields = field_map(old), field_map(contract)
    if set(fields) != set(old_fields) or len(fields) != 1664:
        errors.append("field universe drift")
    actual_changed = {key for key in fields if fields[key][1] != old_fields[key][1]}
    declared_changed = set()
    for item in changeset.get("corrections", []):
        table, pk = item["member"].split("::", 1)
        declared_changed.add((table, pk, item["field"]))
    if changeset.get("correction_count") != 32 or len(declared_changed) != 32 or actual_changed != declared_changed:
        errors.append("changeset is not an exact 32-field diff")

    graph = defaultdict(set)
    nodes = {f"{table}::{pk}.{name}" for table, pk, name in fields}
    counts = Counter()
    type_mismatches = null_mismatches = enum_mismatches = 0
    derived_errors = deterministic_errors = 0
    for (table, pk, name), (_, field) in fields.items():
        node = f"{table}::{pk}.{name}"
        binding = field.get("value_binding", {})
        kind = binding.get("kind")
        counts[kind] += 1
        if kind not in ALLOWED:
            errors.append(f"invalid binding kind {node}")
            continue
        if not REQUIRED_BY_KIND[kind] <= binding.keys():
            errors.append(f"incomplete {kind} binding {node}")
        if field.get("taxonomy_classification") == "PREBOUND_STATIC" and kind not in STATIC_ALLOWED:
            errors.append(f"dynamic PREBOUND_STATIC {node}")
        schema_type = canonical_type(field.get("schema", {}).get("type"))
        physical_type = canonical_type(field.get("schema", {}).get("database_type"))
        binding_type = canonical_type(binding.get("database_type_or_schema_type"))
        if physical_type and schema_type and physical_type != schema_type:
            type_mismatches += 1; errors.append(f"physical/schema type mismatch {node}")
        if binding_type and binding_type != (physical_type or schema_type):
            type_mismatches += 1; errors.append(f"binding/schema type mismatch {node}")
        if kind == "EXACT_LITERAL":
            mismatch = literal_type_error(field, binding.get("typed_value"))
            if mismatch:
                if binding.get("typed_value") is None: null_mismatches += 1
                else: type_mismatches += 1
                errors.append(f"{mismatch} {node}")
            allowed = ENUMS.get((table, name))
            if allowed and binding.get("typed_value") not in allowed:
                enum_mismatches += 1; errors.append(f"invalid enum/CHECK literal {node}")
        elif kind == "DETERMINISTIC_DERIVATION":
            if not binding.get("all_preimage_inputs") or not binding.get("verification_rule"):
                deterministic_errors += 1; errors.append(f"incomplete deterministic preimage {node}")
        elif kind == "REFERENCE_TO_BOUND_FIELD":
            source = f"{binding.get('source_member', '')}.{binding.get('source_field', '')}"
            graph[source].add(node)
        elif kind == "EXECUTION_DERIVED_PERSISTED":
            if not all(binding.get(x) for x in ("producer", "freeze_point", "verification_rule", "source_state")):
                derived_errors += 1; errors.append(f"execution-derived producer/freeze incomplete {node}")
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
    cycle_count = int(any(cycle(node) for node in list(graph) if node not in visited))
    if cycle_count:
        errors.append("reference cycle")
    expected_counts = {"member_count": 118, "db_row_count": 110, "artifact_count": 8, "field_count_total": 1664, "exact_literal_count": 749, "deterministic_derivation_count": 200, "reference_binding_count": 205, "execution_derived_persisted_count": 430, "physical_type_mismatches": 0, "nullability_mismatches": 0, "enum_check_mismatches": 0, "unbound_required_field_count": 0, "ambiguous_binding_count": 0, "conflicting_binding_count": 0, "reference_cycle_count": 0, "deterministic_preimage_errors": 0, "execution_derived_producer_freeze_errors": 0}
    machine = contract.get("machine_counts", {})
    for key, expected in expected_counts.items():
        if machine.get(key) != expected:
            errors.append(f"bad machine count {key}")
    if counts != Counter({"EXACT_LITERAL": 749, "EXECUTION_DERIVED_PERSISTED": 430, "REFERENCE_TO_BOUND_FIELD": 205, "DETERMINISTIC_DERIVATION": 200, "EXECUTION_DERIVED_EXTERNAL_AUTHORITY": 46, "NATIVE_OUTPUT": 27, "ADR0017_MAPPED_OUTPUT": 7}):
        errors.append("binding-kind count reconciliation failed")
    if type_mismatches or null_mismatches or enum_mismatches or deterministic_errors or derived_errors:
        errors.append("strict validation metrics did not reach zero")

    for pk, event_type in EVENTS.items():
        prefix = ("eventing.domain_event", pk)
        if value(fields, *prefix, "event_type").get("typed_value") != event_type: errors.append(f"non-native event_type {pk}")
        if value(fields, *prefix, "aggregate_type").get("typed_value") != "agent_run": errors.append(f"non-native aggregate_type {pk}")
        aggregate = value(fields, *prefix, "aggregate_id")
        if (aggregate.get("kind"), aggregate.get("source_member"), aggregate.get("source_field")) != ("REFERENCE_TO_BOUND_FIELD", RUN_MEMBER, "id"): errors.append(f"unrelated aggregate_id {pk}")
        if value(fields, *prefix, "source").get("typed_value") != "iso-smart-agent-runtime": errors.append(f"non-native source {pk}")
        if value(fields, *prefix, "payload").get("kind") != "EXECUTION_DERIVED_PERSISTED" or "_state" not in value(fields, *prefix, "payload").get("source_state", ""): errors.append(f"impossible payload {pk}")
        trace = value(fields, *prefix, "trace_id")
        if (trace.get("source_member"), trace.get("source_field")) != (RUN_MEMBER, "trace_id"): errors.append(f"event trace is not AgentRun trace {pk}")
        for nullable in ("correlation_id", "causation_id"):
            if value(fields, *prefix, nullable).get("typed_value", "missing") is not None: errors.append(f"invented {nullable} {pk}")
        version = value(fields, *prefix, "aggregate_version")
        if version.get("kind") != "EXECUTION_DERIVED_PERSISTED" or "MAX(aggregate_version)" not in version.get("source_state", ""): errors.append(f"aggregate version drift {pk}")
    for pk in OUTBOXES:
        if value(fields, "eventing.transactional_outbox", pk, "publish_attempts").get("typed_value") != 0: errors.append(f"outbox initial attempts drift {pk}")
    for pk, action in AUDITS.items():
        prefix = ("audit.immutable_audit_log", pk)
        literals = {"action": action, "actor_type": "worker", "entity_type": "agent_run", "stream_type": "agent_run"}
        for name, expected in literals.items():
            if value(fields, *prefix, name).get("typed_value") != expected: errors.append(f"audit {name} drift {pk}")
        for name, source_field in (("entity_id", "id"), ("stream_id", "id"), ("trace_id", "trace_id")):
            binding = value(fields, *prefix, name)
            if (binding.get("source_member"), binding.get("source_field")) != (RUN_MEMBER, source_field): errors.append(f"audit {name} linkage drift {pk}")
        if value(fields, *prefix, "metadata_canonical").get("kind") != "EXECUTION_DERIVED_PERSISTED": errors.append(f"audit metadata not source-derived {pk}")

    runtime = RUNTIME.read_text()
    helper = method_source("_event_outbox_audit")
    start, complete, fail = (method_source(name) for name in ("start_agent_run", "complete_agent_run_with_recommendation", "fail_agent_run"))
    required_helper = ['event_id = uuid4()', '.filter(aggregate_type="agent_run", aggregate_id=run.id)', 'aggregate_type="agent_run"', 'aggregate_id=run.id', 'source="iso-smart-agent-runtime"', 'payload=canonical_payload', 'publish_attempts=0', 'stream_type="agent_run", stream_id=run.id', 'actor_type="worker"']
    if any(snippet not in helper for snippet in required_helper): errors.append("native helper source contract drift")
    if not all(event in runtime for event in ('"agent_run.started": 1', '"agent_run.completed": 1', '"agent_run.failed": 1')): errors.append("EVENT_CONTRACTS drift")
    if start.index("AgentRun.objects") > start.index("self._event_outbox_audit"): errors.append("start parent order drift")
    if "run_id = uuid4()" not in start or "idempotency_key" in start: errors.append("start identity/retry fiction")
    if any(method.index("select_for_update") > method.index("self._event_outbox_audit") for method in (complete, fail)): errors.append("later writer lock order drift")
    migration_0003, migration_0011 = MIGRATION_0003.read_text(), MIGRATION_0011.read_text()
    if "id uuid PRIMARY KEY" not in migration_0011: errors.append("AgentRun parent PK invariant drift")
    if "UNIQUE (tenant_id,aggregate_type,aggregate_id,aggregate_version)" in migration_0003: errors.append("false event stream uniqueness claim")
    if "enumerated deterministic identity replacements" not in ADR0018.read_text(): errors.append("ADR-0018 identity exception missing")
    correction = contract.get("source_reachability_correction", {})
    if not correction.get("ADR0018_explicit_identity_exception_covers_event_id") or not correction.get("ADR0018_explicit_identity_exception_covers_outbox_id"): errors.append("unapproved ID substitution")
    serialized_fields = json.dumps([item[1] for item in fields.values()], sort_keys=True)
    for old_id in ("51c9bad4-88fb-5608-b3c9-edd578efeeb9", "91792d67-eb35-5e1d-9c62-c285f7b97057"):
        if old_id in serialized_fields: errors.append(f"dangling superseded aggregate ID {old_id}")

    integrity = contract.get("frozen_source_integrity", {})
    current_migrations = {name: sha(ROOT / name) for name in integrity.get("migration_file_sha256", {}) if (ROOT / name).is_file()}
    if current_migrations != integrity.get("migration_file_sha256"): errors.append("migration hash drift")
    current_sources = {name: sha(ROOT / name) for name in integrity.get("authoritative_file_sha256", {}) if (ROOT / name).is_file()}
    if current_sources != integrity.get("authoritative_file_sha256"): errors.append("protected source hash drift")
    material = json.dumps({k: v for k, v in contract.items() if k != "fixed_digest_inventory"}, sort_keys=True)
    fixed = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", material))
    inventory = contract.get("fixed_digest_inventory", [])
    if fixed != {item.get("digest") for item in inventory}: errors.append("fixed digest inventory mismatch")
    return errors


def metrics(contract: dict):
    result = {
        "member_count": len(contract.get("field_bindings", [])),
        "field_count": len(field_map(contract)),
        "contract_agentrun_event_member_count": len([row for row in contract.get("future_row_universe", []) if row.get("qualified_table") == "eventing.domain_event" and row.get("producer") == "phase31.4.4-agent-provenance-producer/v1"]),
        "errors": validate(contract),
    }
    return result


if __name__ == "__main__":
    result = metrics(load_contract())
    print(json.dumps({"status": "PASS" if not result["errors"] else "FAIL", **result}, indent=2, sort_keys=True))
    raise SystemExit(bool(result["errors"]))
