"""Permanent offline strict validator for the Phase 31.4.4B V2.2 contract."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID

from foundation.phase31_4_4a_field_binding_validator import ALLOWED, ENUMS, REQUIRED_BY_KIND


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4B_ROW_LEVEL_EXECUTION_CONTRACT_V2_2.json"
V21_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4A_ROW_LEVEL_EXECUTION_CONTRACT_V2_1.json"
BLOCKER_PATH = ROOT / "docs/governance/evidence/PHASE31_4_5_RETRY2_IMPLEMENTATION_FEASIBILITY_BLOCKER_V1.json"
REGISTRY_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json"
CLOSURE_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json"
V21_SHA256 = "acd9e5551a04fc60356fedc2abdc4170932274913795fb6a5a4952ebf9477d85"
REGISTRY_SHA256 = "58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb"
CLOSURE_SHA256 = "80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425"
BIGINT_MIN = -(2**63)
BIGINT_MAX = 2**63 - 1
STATIC_ALLOWED = {"EXACT_LITERAL", "DETERMINISTIC_DERIVATION", "REFERENCE_TO_BOUND_FIELD", "ADOPTED_STATIC_SCHEMA_DEFAULT"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    return json.loads(path.read_text())


def canonical_type(value: str | None) -> str:
    raw = (value or "").lower()
    if raw in {"uuidfield", "uuid"}: return "uuid"
    if raw in {"charfield", "textfield", "text"} or raw.startswith(("varchar", "char(")): return "text"
    if raw in {"positivebigintegerfield", "bigintegerfield", "bigint"}: return "bigint"
    if raw in {"integerfield", "positiveintegerfield", "integer"}: return "integer"
    if raw in {"positivesmallintegerfield", "smallintegerfield", "smallint"}: return "smallint"
    if raw in {"booleanfield", "boolean", "bool"}: return "boolean"
    if raw in {"jsonfield", "jsonb", "json"}: return "jsonb"
    if raw in {"datetimefield", "timestamptz"} or raw.startswith("timestamp"): return "timestamptz"
    if raw in {"datefield", "date"}: return "date"
    if raw in {"decimalfield", "numeric", "decimal"} or raw.startswith("numeric"): return "numeric"
    if raw in {"binaryfield", "bytea"}: return "bytea"
    if raw in {"foreignkey", "onetoonefield"}: return "uuid"
    return raw


def literal_type_error(field: dict, value) -> str | None:
    schema = field["schema"]
    declared = canonical_type(schema.get("database_type") or schema.get("type"))
    if value is None:
        return None if schema.get("nullable") else "NULL on NOT NULL field"
    if declared == "uuid":
        if not isinstance(value, str): return "UUID is not a JSON string"
        try: UUID(value)
        except (ValueError, AttributeError): return "invalid UUID literal"
    elif declared == "text":
        if not isinstance(value, str): return "text is not a JSON string"
        max_length = schema.get("max_length")
        if max_length and len(value) > max_length: return "text exceeds max_length"
    elif declared in {"bigint", "integer", "smallint"}:
        if isinstance(value, bool) or not isinstance(value, int): return "integer field requires JSON integer (bool/string prohibited)"
        low, high = (BIGINT_MIN, BIGINT_MAX)
        if declared == "integer": low, high = -(2**31), 2**31 - 1
        if declared == "smallint": low, high = -(2**15), 2**15 - 1
        if not low <= value <= high: return "integer outside physical range"
        if schema.get("type", "").startswith("Positive") and value < 0: return "negative value for positive integer field"
    elif declared == "boolean" and not isinstance(value, bool):
        return "boolean field requires JSON boolean"
    elif declared == "jsonb" and isinstance(value, str):
        return "JSON field received serialized string"
    elif declared == "numeric":
        if isinstance(value, bool): return "numeric field received bool"
        try: Decimal(str(value))
        except (InvalidOperation, ValueError): return "invalid numeric literal"
    return None


def contract_fields(contract: dict) -> dict[tuple[str, str, str], tuple[dict, dict]]:
    result = {}
    for member in contract.get("field_bindings", []):
        identity = member.get("member_identity", {})
        table = identity.get("qualified_table_or_artifact_index")
        primary_key = identity.get("primary_key_or_artifact_id")
        for field in member.get("fields", []):
            result[(table, primary_key, field.get("name"))] = (member, field)
    return result


def validate(contract: dict) -> list[str]:
    errors: list[str] = []
    v21 = json.loads(V21_PATH.read_text())
    blocker = json.loads(BLOCKER_PATH.read_text())
    conflicts = blocker.get("conflicts", [])
    conflict_keys = {
        (x["qualified_table_or_artifact"], x["primary_key_or_artifact_id"], x["field"])
        for x in conflicts
    }
    if sha(V21_PATH) != V21_SHA256 or contract.get("predecessor_contract_sha256") != V21_SHA256:
        errors.append("V2.1 predecessor hash mismatch")
    if len(conflicts) != 34 or len(conflict_keys) != 34:
        errors.append("entry conflict inventory is not exactly 34 unique fields")
    for key, expected in {
        "contract_version": "2.2",
        "predecessor_contract_version": "2.1",
        "change_scope": "STRICT_PHYSICAL_TYPE_CORRECTION_FOR_34_BINDINGS",
        "architecture_changed": False,
        "row_universe_changed": False,
        "security_changed": False,
        "freeze_model_changed": False,
        "Registry_changed": False,
        "Closure_changed": False,
    }.items():
        if contract.get(key) != expected: errors.append(f"invalid V2.2 invariant {key}")

    old_rows = v21.get("future_row_universe", [])
    rows = contract.get("future_row_universe", [])
    if rows != old_rows: errors.append("118-member row universe or producer/freeze/security material drift")
    for key in ("security_rls_matrix", "freeze_order", "identity_contract", "semantic_registry_v2", "closure_v2"):
        if contract.get(key) != v21.get(key): errors.append(f"inherited {key} drift")
    if sha(REGISTRY_PATH) != REGISTRY_SHA256: errors.append("Registry V2 hash drift")
    if sha(CLOSURE_PATH) != CLOSURE_SHA256: errors.append("Closure V2 hash drift")
    if any((ROOT / "backend/foundation/migrations").glob("0024*")): errors.append("migration 0024 appeared")

    old_fields = contract_fields(v21)
    fields = contract_fields(contract)
    if set(fields) != set(old_fields) or len(fields) != 1664:
        errors.append("field universe drift")
    for key in set(fields) - conflict_keys:
        if fields[key][1] != old_fields[key][1]: errors.append(f"unrelated field changed {key}")

    graph: dict[str, set[str]] = defaultdict(set)
    all_nodes = set()
    binding_counts = Counter()
    exact_checked = type_mismatches = null_mismatches = enum_mismatches = 0
    for key, (member, field) in fields.items():
        table, primary_key, name = key
        node = f"{table}::{primary_key}.{name}"
        all_nodes.add(node)
        binding = field.get("value_binding")
        if not isinstance(binding, dict): errors.append(f"missing binding {node}"); continue
        kind = binding.get("kind")
        binding_counts[kind] += 1
        if kind not in ALLOWED: errors.append(f"invalid binding kind {node}"); continue
        if not REQUIRED_BY_KIND[kind] <= binding.keys(): errors.append(f"incomplete {kind} binding {node}")
        if field.get("taxonomy_classification") == "PREBOUND_STATIC" and kind not in STATIC_ALLOWED:
            errors.append(f"dynamic PREBOUND_STATIC {node}")
        schema_type = canonical_type(field.get("schema", {}).get("type"))
        physical_type = canonical_type(field.get("schema", {}).get("database_type"))
        if physical_type and schema_type and physical_type != schema_type:
            errors.append(f"physical/schema type mismatch {node}")
        binding_type = canonical_type(binding.get("database_type_or_schema_type"))
        if binding_type and (physical_type or schema_type) != binding_type:
            errors.append(f"binding/schema type mismatch {node}")
        if kind == "EXACT_LITERAL":
            exact_checked += 1
            value = binding.get("typed_value")
            mismatch = literal_type_error(field, value)
            if mismatch:
                if value is None: null_mismatches += 1
                else: type_mismatches += 1
                errors.append(f"{mismatch} {node}")
            allowed = ENUMS.get((table, name))
            if allowed and value not in allowed:
                enum_mismatches += 1
                errors.append(f"invalid enum/CHECK literal {node}")
        elif kind == "DETERMINISTIC_DERIVATION" and (not binding.get("all_preimage_inputs") or not binding.get("verification_rule")):
            errors.append(f"incomplete deterministic preimage {node}")
        elif kind == "REFERENCE_TO_BOUND_FIELD":
            source = binding.get("source_member", "") + "." + binding.get("source_field", "")
            graph[source].add(node)
        elif kind == "EXECUTION_DERIVED_PERSISTED":
            if not binding.get("producer") or not binding.get("freeze_point") or not binding.get("verification_rule") or not binding.get("source_state"):
                errors.append(f"execution-derived producer/freeze incomplete {node}")

    for source in graph:
        if source not in all_nodes: errors.append(f"unresolved reference {source}")
    visiting, visited = set(), set()
    def visit(node: str) -> bool:
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        if any(visit(target) for target in graph.get(node, ())): return True
        visiting.remove(node); visited.add(node)
        return False
    if any(visit(node) for node in list(graph) if node not in visited): errors.append("reference cycle")

    for conflict in conflicts:
        key = (conflict["qualified_table_or_artifact"], conflict["primary_key_or_artifact_id"], conflict["field"])
        member, field = fields.get(key, ({}, {}))
        binding = field.get("value_binding", {})
        table, _, name = key
        if table in {"eventing.domain_event", "audit.immutable_audit_log"}:
            if field.get("taxonomy_classification") != "EXECUTION_DERIVED_PERSISTED" or binding.get("kind") != "EXECUTION_DERIVED_PERSISTED":
                errors.append(f"bigint conflict not execution-derived {key}")
            if binding.get("expected_literal_if_static") is not None or "typed_value" in binding:
                errors.append(f"fake bigint literal remains {key}")
            row = next((r for r in rows if r.get("qualified_table") == table and r.get("primary_key") == key[1]), None)
            if not row or binding.get("producer") != row.get("producer") or binding.get("freeze_point") != row.get("freeze_point"):
                errors.append(f"bigint producer/freeze drift {key}")
            preimage_text = json.dumps(binding.get("preimage", {}), sort_keys=True)
            if table == "eventing.domain_event" and ("aggregate_type" not in preimage_text or "aggregate_id" not in preimage_text):
                errors.append(f"aggregate version unrelated preimage {key}")
            if table == "audit.immutable_audit_log" and not all(x in preimage_text for x in ("tenant_id", "stream_type", "stream_id")):
                errors.append(f"audit sequence unrelated stream {key}")
        else:
            if field.get("schema", {}).get("type") != "CharField" or canonical_type(binding.get("database_type_or_schema_type")) != "text":
                errors.append(f"business identifier is not text {key}")
            if binding.get("typed_value") != conflict["typed_value"]:
                errors.append(f"business identifier value changed {key}")
            if binding.get("business_identifier_semantics") != "BUSINESS IDENTIFIER TEXT":
                errors.append(f"business identifier semantics missing {key}")

    counts = contract.get("machine_counts", {})
    expected_counts = {
        "member_count": 118, "db_row_count": 110, "artifact_count": 8,
        "field_count_total": 1664, "exact_literal_count": 753,
        "execution_derived_persisted_count": 426,
        "known_entry_type_conflicts": 34, "known_entry_type_conflicts_remaining": 0,
        "physical_type_mismatches": 0, "nullability_mismatches": 0, "enum_check_mismatches": 0,
    }
    for key, value in expected_counts.items():
        if counts.get(key) != value: errors.append(f"bad machine count {key}")
    if exact_checked != 753 or binding_counts["EXACT_LITERAL"] != 753:
        errors.append("full exact-literal count reconciliation failed")
    if type_mismatches or null_mismatches or enum_mismatches:
        errors.append("strict literal scan did not reach zero mismatches")
    if 779 - exact_checked != 26: errors.append("reclassified exact-literal count mismatch")
    if any(counts.get(name) != 0 for name in ("unbound_required_field_count", "ambiguous_binding_count", "conflicting_binding_count", "reference_cycle_count")):
        errors.append("binding defect count is nonzero")

    integrity = contract.get("frozen_source_integrity", {})
    current_migrations = {name: sha(ROOT / name) for name in integrity.get("migration_file_sha256", {}) if (ROOT / name).is_file()}
    if current_migrations != integrity.get("migration_file_sha256"): errors.append("migration hash drift")
    aggregate = hashlib.sha256("".join(f"{name}\0{digest}\n" for name, digest in current_migrations.items()).encode()).hexdigest()
    if aggregate != integrity.get("migration_set_sha256") or aggregate != integrity.get("expected_migration_set_sha256"):
        errors.append("migration-set hash drift")
    current_sources = {name: sha(ROOT / name) for name in integrity.get("authoritative_file_sha256", {}) if (ROOT / name).is_file()}
    if current_sources != integrity.get("authoritative_file_sha256"): errors.append("authoritative source hash drift")
    input_integrity = contract.get("v2_2_input_integrity", {})
    expected_input_hashes = {
        "v2_1_sha256": sha(V21_PATH), "retry2_blocker_sha256": sha(BLOCKER_PATH),
        "registry_v2_sha256": sha(REGISTRY_PATH), "closure_v2_sha256": sha(CLOSURE_PATH),
        "adr_0018_sha256": sha(ROOT / "docs/adr/0018-row-level-execution-ready-v2-contract.md"),
        "product_policy_v2_sha256": sha(ROOT / "docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V2.md"),
        "support_producer_contract_sha256": sha(ROOT / "docs/governance/PHASE31_4_4_SUPPORTING_FIXTURE_PRODUCER_CONTRACT_V1.md"),
    }
    for key, value in expected_input_hashes.items():
        if input_integrity.get(key) != value: errors.append(f"detached input hash drift {key}")

    material = json.dumps({k: v for k, v in contract.items() if k != "fixed_digest_inventory"}, sort_keys=True)
    fixed = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", material))
    inventory = contract.get("fixed_digest_inventory", [])
    if fixed != {x.get("digest") for x in inventory}: errors.append("fixed digest inventory mismatch")
    if any(x.get("classification") not in {"STATIC_PREIMAGE_INCLUDED", "SOURCE_BYTES_HASH", "CANONICAL_POLICY_HASH", "HISTORICAL_REFERENCE_ONLY"} or not x.get("preimage_or_source") for x in inventory):
        errors.append("fixed hash without preimage/classification")
    return errors


def validation_metrics(contract: dict) -> dict:
    fields = contract_fields(contract)
    counts = Counter(field["value_binding"]["kind"] for _, field in fields.values())
    return {
        "member_count": len(contract.get("field_bindings", [])),
        "field_count": len(fields),
        "strict_fields_checked": len(fields),
        "v2_1_exact_literal_count": 779,
        "v2_2_exact_literal_count": counts["EXACT_LITERAL"],
        "reclassified_exact_literal_count": 779 - counts["EXACT_LITERAL"],
        "binding_kind_counts": dict(sorted(counts.items())),
        "errors": validate(contract),
    }


if __name__ == "__main__":
    loaded = load_contract()
    metrics = validation_metrics(loaded)
    print(json.dumps({"status": "PASS" if not metrics["errors"] else "FAIL", **metrics}, indent=2, sort_keys=True))
    raise SystemExit(bool(metrics["errors"]))
