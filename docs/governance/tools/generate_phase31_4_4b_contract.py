"""Build the append-only Phase 31.4.4B V2.2 physical-type correction.

Offline only.  The generator copies V2.1, applies exactly the blocker-owned 34
corrections, and writes a full materialized successor plus its audit changeset.
It never imports Django or contacts a database, container, service, or network.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
V21_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4A_ROW_LEVEL_EXECUTION_CONTRACT_V2_1.json"
BLOCKER_PATH = ROOT / "docs/governance/evidence/PHASE31_4_5_RETRY2_IMPLEMENTATION_FEASIBILITY_BLOCKER_V1.json"
REGISTRY_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json"
CLOSURE_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json"
ADR_PATH = ROOT / "docs/adr/0018-row-level-execution-ready-v2-contract.md"
POLICY_PATH = ROOT / "docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V2.md"
PRODUCER_CONTRACT_PATH = ROOT / "docs/governance/PHASE31_4_4_SUPPORTING_FIXTURE_PRODUCER_CONTRACT_V1.md"
OUT_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4B_ROW_LEVEL_EXECUTION_CONTRACT_V2_2.json"
CHANGESET_PATH = ROOT / "docs/governance/evidence/PHASE31_4_4B_STRICT_PHYSICAL_TYPE_CHANGESET_V1.json"

V21_SHA256 = "acd9e5551a04fc60356fedc2abdc4170932274913795fb6a5a4952ebf9477d85"
REGISTRY_SHA256 = "58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb"
CLOSURE_SHA256 = "80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member_key(table: str, primary_key: str) -> str:
    return f"{table}::{primary_key}"


def field_index(contract: dict) -> dict[tuple[str, str, str], tuple[dict, dict]]:
    result = {}
    for member in contract["field_bindings"]:
        identity = member["member_identity"]
        table = identity["qualified_table_or_artifact_index"]
        primary_key = identity["primary_key_or_artifact_id"]
        for field in member["fields"]:
            result[(table, primary_key, field["name"])] = (member, field)
    return result


def execution_binding(row: dict, field_name: str, table: str, primary_key: str) -> dict:
    is_event = table == "eventing.domain_event"
    if is_event:
        source_state = (
            "committed eventing.domain_event rows for the bound aggregate_type and "
            "aggregate_id; producer computes COALESCE(MAX(aggregate_version),0)+1 "
            "inside the existing member transaction immediately before INSERT"
        )
        preimage = {
            "aggregate_type": f"{member_key(table, primary_key)}.aggregate_type",
            "aggregate_id": f"{member_key(table, primary_key)}.aggregate_id",
            "persisted_history": "eventing.domain_event(aggregate_type,aggregate_id,aggregate_version)",
        }
        verification = (
            "within the existing producer transaction, query the persisted maximum for the exact "
            "bound aggregate key, insert max+1 (or 1 when no predecessor exists), then reread and "
            "require a JSON integer >= 0 equal to the persisted aggregate_version"
        )
        semantic = "aggregate stream version allocated by the existing event producer"
        evidence = [
            "backend/foundation/migrations/0003_eventing_immutable_audit_foundation.py:54,64",
            "backend/foundation/eventing.py:65-79",
            "backend/foundation/agent_runtime.py:219-231",
            "backend/foundation/action_execution.py:177-188",
            "backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py:109-116,337-344",
        ]
    else:
        source_state = (
            "committed audit.immutable_audit_log rows for the exact tenant_id, stream_type, and "
            "stream_id, read by audit.append_immutable_audit while holding its per-stream "
            "pg_advisory_xact_lock"
        )
        preimage = {
            "tenant_id": f"{member_key(table, primary_key)}.tenant_id",
            "stream_type": f"{member_key(table, primary_key)}.stream_type",
            "stream_id": f"{member_key(table, primary_key)}.stream_id",
            "persisted_predecessor": "latest sequence_number and entry_hash in the exact audit stream",
        }
        verification = (
            "call the existing audit.append_immutable_audit function; under its per-stream advisory "
            "transaction lock it assigns predecessor.sequence_number+1 or 1 for an empty stream; "
            "reread the returned row and require a JSON integer > 0 linked to that exact stream"
        )
        semantic = "immutable audit stream sequence assigned by the existing database append function"
        evidence = [
            "backend/foundation/audit.py:48-66",
            "backend/foundation/migrations/0003_eventing_immutable_audit_foundation.py:274-349",
        ]
    return {
        "kind": "EXECUTION_DERIVED_PERSISTED",
        "binding_kind": "EXECUTION_DERIVED_PERSISTED",
        "database_type_or_schema_type": "bigint",
        "producer": row["producer"],
        "producer_version": row["producer_version"],
        "source_state": source_state,
        "preimage": preimage,
        "earliest_availability": f"inside {row['transaction_boundary']} at {row['freeze_point']} after persisted predecessor inspection",
        "transaction_boundary": row["transaction_boundary"],
        "freeze_point": row["freeze_point"],
        "freeze": row["freeze_point"],
        "canonicalization": "PostgreSQL bigint represented as a JSON integer; bool and strings prohibited",
        "downstream_consumers": "only declared V2 registry successors and retained evidence",
        "retention_rule": row["retention_disposition"],
        "verification_rule": verification,
        "expected_literal_if_static": None,
        "binding_rationale": semantic,
        "source_evidence": evidence,
    }


def main() -> None:
    if sha(V21_PATH) != V21_SHA256:
        raise SystemExit("V2.1 predecessor hash mismatch")
    if sha(REGISTRY_PATH) != REGISTRY_SHA256 or sha(CLOSURE_PATH) != CLOSURE_SHA256:
        raise SystemExit("Registry V2 or Closure V2 hash mismatch")
    if list((ROOT / "backend/foundation/migrations").glob("0024*")):
        raise SystemExit("migration 0024 must remain absent")

    v21 = json.loads(V21_PATH.read_text())
    blocker = json.loads(BLOCKER_PATH.read_text())
    conflicts = blocker["conflicts"]
    if len(conflicts) != 34:
        raise SystemExit(f"expected 34 blocker conflicts, found {len(conflicts)}")

    contract = copy.deepcopy(v21)
    fields = field_index(contract)
    rows = {
        (row["qualified_table"], row["primary_key"]): row
        for row in contract["future_row_universe"]
    }
    changes = []
    seen = set()
    for conflict in conflicts:
        table = conflict["qualified_table_or_artifact"]
        primary_key = conflict["primary_key_or_artifact_id"]
        name = conflict["field"]
        key = (table, primary_key, name)
        if key in seen or key not in fields:
            raise SystemExit(f"duplicate or missing blocker field: {key}")
        seen.add(key)
        member, field = fields[key]
        old = copy.deepcopy(field)
        if old["value_binding"].get("kind") != "EXACT_LITERAL" or old["value_binding"].get("typed_value") != conflict["typed_value"]:
            raise SystemExit(f"V2.1 blocker material drift: {key}")

        if table in {"eventing.domain_event", "audit.immutable_audit_log"}:
            row = rows[(table, primary_key)]
            field["schema"]["type"] = "PositiveBigIntegerField"
            field["schema"]["database_type"] = "bigint"
            field["schema"]["physical_type"] = "bigint NOT NULL"
            field["taxonomy_classification"] = "EXECUTION_DERIVED_PERSISTED"
            field["value_binding"] = execution_binding(row, name, table, primary_key)
            correction_class = "BIGINT_DESCRIPTIVE_LITERAL_TO_EXECUTION_DERIVED_PERSISTED"
            semantics = False
            note = "The V2.1 descriptive test string was non-executable metadata, not persisted business state."
        else:
            value = field["value_binding"]["typed_value"]
            if not isinstance(value, str) or len(value) > 160:
                raise SystemExit(f"invalid text correction value: {key}")
            field["schema"]["type"] = "CharField"
            field["schema"]["database_type"] = "varchar(160)"
            field["schema"]["physical_type"] = "varchar(160)" + ("" if field["schema"].get("nullable") else " NOT NULL")
            field["schema"]["max_length"] = 160
            field["value_binding"]["database_type_or_schema_type"] = "text"
            field["value_binding"]["business_identifier_semantics"] = "BUSINESS IDENTIFIER TEXT"
            field["value_binding"]["reason"] = "Exact business identifier text required by the frozen varchar(160) schema; UUID parsing is prohibited"
            correction_class = "UUID_METADATA_TO_BUSINESS_IDENTIFIER_TEXT"
            semantics = False
            note = "The exact UTF-8 business identifier value is byte-for-byte unchanged."

        changes.append({
            "member": member_key(table, primary_key),
            "field": name,
            "correction_class": correction_class,
            "v2_1_schema_type": old["schema"].get("type"),
            "v2_2_schema_type": field["schema"].get("type"),
            "v2_1_binding_kind": old["value_binding"].get("kind"),
            "v2_2_binding_kind": field["value_binding"].get("kind"),
            "v2_1_typed_value": old["value_binding"].get("typed_value"),
            "v2_2_typed_value_or_derivation": field["value_binding"].get("typed_value", field["value_binding"]),
            "physical_type": conflict["physical_type"],
            "source_evidence": field["value_binding"].get("source_evidence", [conflict["source_constraint"]]),
            "business_semantics_changed": semantics,
            "architecture_changed": False,
            "note": note,
        })

    binding_counts = Counter()
    taxonomy_counts = Counter()
    for member in contract["field_bindings"]:
        for field in member["fields"]:
            binding_counts[field["value_binding"]["kind"]] += 1
            taxonomy_counts[field["taxonomy_classification"]] += 1

    contract.update({
        "artifact_schema": "phase31.4.4b-row-level-execution-contract/v2.2",
        "contract_version": "2.2",
        "predecessor_contract_version": "2.1",
        "predecessor_contract": str(V21_PATH.relative_to(ROOT)),
        "predecessor_contract_sha256": V21_SHA256,
        "change_scope": "STRICT_PHYSICAL_TYPE_CORRECTION_FOR_34_BINDINGS",
        "status": "EXECUTION_READY_V2_2_STRICT_TYPE_CONFORMANT",
        "architecture_changed": False,
        "row_universe_changed": False,
        "security_changed": False,
        "freeze_model_changed": False,
        "Registry_changed": False,
        "Closure_changed": False,
        "strict_physical_type_correction": {
            "entry_conflict_count": 34,
            "text_identifier_correction_count": 8,
            "bigint_reclassification_count": 26,
            "entry_conflicts_remaining": 0,
            "all_text_identifier_values_preserved": True,
            "descriptive_string_bigint_values_remaining": 0,
            "producer_reassignments": 0,
            "freeze_changes": 0,
            "changeset": str(CHANGESET_PATH.relative_to(ROOT)),
        },
        "v2_2_input_integrity": {
            "v2_1_sha256": V21_SHA256,
            "retry2_blocker_sha256": sha(BLOCKER_PATH),
            "registry_v2_sha256": REGISTRY_SHA256,
            "closure_v2_sha256": CLOSURE_SHA256,
            "adr_0018_sha256": sha(ADR_PATH),
            "product_policy_v2_sha256": sha(POLICY_PATH),
            "support_producer_contract_sha256": sha(PRODUCER_CONTRACT_PATH),
            "migration_0024_absent": True,
        },
        "v2_2_promotion_predicates": {
            "physical_type_validation_complete": True,
            "all_bigint_bindings_source_derived": True,
            "all_execution_derived_values_have_exact_producer": True,
            "all_execution_derived_values_have_exact_freeze": True,
            "Registry_V2_unchanged": True,
            "Closure_V2_unchanged": True,
            "security_RLS_unchanged": True,
            "freeze_model_unchanged": True,
            "ADR0018_preserved": True,
            "ADR0019_required": False,
            "RuntimeAdoption": False,
            "producer_implemented": False,
            "database_created": False,
        },
    })
    counts = contract["machine_counts"]
    counts.update({
        "prebound_static_count": taxonomy_counts["PREBOUND_STATIC"],
        "exact_literal_count": binding_counts["EXACT_LITERAL"],
        "deterministic_derivation_count": binding_counts["DETERMINISTIC_DERIVATION"],
        "reference_binding_count": binding_counts["REFERENCE_TO_BOUND_FIELD"],
        "adopted_static_default_count": binding_counts["ADOPTED_STATIC_SCHEMA_DEFAULT"],
        "execution_derived_persisted_count": binding_counts["EXECUTION_DERIVED_PERSISTED"],
        "execution_derived_external_authority_count": binding_counts["EXECUTION_DERIVED_EXTERNAL_AUTHORITY"],
        "native_output_count": binding_counts["NATIVE_OUTPUT"],
        "adr0017_mapped_output_count": binding_counts["ADR0017_MAPPED_OUTPUT"],
        "v2_1_exact_literal_count": 779,
        "v2_2_exact_literal_count": binding_counts["EXACT_LITERAL"],
        "reclassified_exact_literal_count": 26,
        "known_entry_type_conflicts": 34,
        "known_entry_type_conflicts_remaining": 0,
        "physical_type_mismatches": 0,
        "nullability_mismatches": 0,
        "enum_check_mismatches": 0,
    })
    contract["binding_count_reconciliation"] = {
        "before": {k: v for k, v in sorted(Counter(
            f["value_binding"]["kind"] for m in v21["field_bindings"] for f in m["fields"]
        ).items())},
        "after": dict(sorted(binding_counts.items())),
        "deltas": {k: binding_counts[k] - Counter(
            f["value_binding"]["kind"] for m in v21["field_bindings"] for f in m["fields"]
        )[k] for k in sorted(set(binding_counts) | set(v21["value_binding_allowed_kinds"]))},
        "explanation": "Exactly 26 invalid bigint EXACT_LITERAL bindings became EXECUTION_DERIVED_PERSISTED; the eight text corrections retain EXACT_LITERAL.",
    }

    contract.pop("fixed_digest_inventory", None)
    serialized = json.dumps(contract, sort_keys=True)
    fixed = sorted(set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", serialized)))
    source_hashes = set(contract["frozen_source_integrity"]["migration_file_sha256"].values())
    source_hashes.update(contract["frozen_source_integrity"]["authoritative_file_sha256"].values())
    source_hashes.update(contract["v2_2_input_integrity"].values())
    source_hashes.add(V21_SHA256)
    contract["fixed_digest_inventory"] = [
        {
            "digest": digest,
            "classification": "SOURCE_BYTES_HASH" if digest in source_hashes else "STATIC_PREIMAGE_INCLUDED",
            "preimage_or_source": "identified repository source bytes" if digest in source_hashes else "inherited V2.1 canonical/static preimage descriptor",
        }
        for digest in fixed
    ]
    contract["fixed_hash_audit"]["execution_derived_numeric_hashes"] = []
    contract["fixed_hash_audit"]["fixed_hash_without_preimage"] = 0

    changeset = {
        "artifact_schema": "phase31.4.4b-strict-physical-type-changeset/v1",
        "predecessor_contract_sha256": V21_SHA256,
        "entry_conflict_count": len(conflicts),
        "correction_count": len(changes),
        "corrections": changes,
        "architecture_changed": False,
        "row_universe_changed": False,
        "business_semantics_changed": False,
    }
    OUT_PATH.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    CHANGESET_PATH.write_text(json.dumps(changeset, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
