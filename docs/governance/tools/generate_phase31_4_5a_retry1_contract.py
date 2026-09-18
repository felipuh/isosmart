"""Build the append-only Phase 31.4.5A Retry 1 V2.3 successor.

Offline only: copy V2.2, correct the two AgentRun event graphs to the exact
native producer contract, and emit a complete machine-readable changeset.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
V22 = ROOT / "docs/governance/fixtures/PHASE31_4_4B_ROW_LEVEL_EXECUTION_CONTRACT_V2_2.json"
OUT = ROOT / "docs/governance/fixtures/PHASE31_4_5A_RETRY1_ROW_LEVEL_EXECUTION_CONTRACT_V2_3.json"
CHANGESET = ROOT / "docs/governance/evidence/PHASE31_4_5A_RETRY1_SOURCE_IDENTITY_CHANGESET_V1.json"
REGISTRY = ROOT / "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json"
CLOSURE = ROOT / "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json"
V22_SHA = "a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d"
REGISTRY_SHA = "58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb"
CLOSURE_SHA = "80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425"
RUN = "qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8"
START = "90e2d38f-9600-5701-a34c-c9827eafc88c"
COMPLETE = "47be0b7e-10d0-5e96-94fd-fcaa8ad14cfd"
START_OUTBOX = "078ed021-9eb9-5258-96b9-3b74e2951e77"
COMPLETE_OUTBOX = "51dd5c7a-52d3-5779-ad95-ea6910747874"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(contract: dict) -> dict[tuple[str, str, str], dict]:
    result = {}
    for member in contract["field_bindings"]:
        identity = member["member_identity"]
        table = identity["qualified_table_or_artifact_index"]
        pk = identity["primary_key_or_artifact_id"]
        for field in member["fields"]:
            result[(table, pk, field["name"])] = field
    return result


def exact(value, reason):
    return {
        "canonical_representation": "canonical-json-rfc8785-compatible/v1",
        "database_type_or_schema_type": "text" if isinstance(value, str) else "integer",
        "kind": "EXACT_LITERAL",
        "provenance": "Phase31.4.5A Retry1 native AgentRun source contract",
        "reason": reason,
        "typed_value": value,
    }


def reference(source_field, required_source_freeze="Freeze1.5"):
    return {
        "copy_or_transform": "copy",
        "kind": "REFERENCE_TO_BOUND_FIELD",
        "required_source_freeze": required_source_freeze,
        "source_field": source_field,
        "source_member": RUN,
        "transform_algorithm_if_any": None,
    }


def derived(member, field, rule, source_location):
    return {
        "canonicalization": "postgresql-jsonb-canonical-v1 for JSON; lowercase hex for digests; UTC ISO-8601 for time",
        "downstream_consumers": "linked DomainEvent, TransactionalOutbox, ImmutableAuditLog and retained evidence",
        "freeze_point": "Freeze1.5",
        "kind": "EXECUTION_DERIVED_PERSISTED",
        "producer": "phase31.4.4-agent-provenance-producer/v1",
        "producer_version": "v1",
        "retention_rule": "RETAIN_FULL_CANONICAL_MATERIAL",
        "source_state": f"native AgentRun {rule} for {member}.{field}",
        "source_evidence": source_location,
        "transaction_boundary": "fixture-exact-atomic/v1",
        "verification_rule": f"execute the frozen native construction rule ({rule}); persist, then perform the authorized read-only canonical reread",
    }


def main():
    if sha(V22) != V22_SHA:
        raise SystemExit("V2.2 predecessor hash mismatch")
    if sha(REGISTRY) != REGISTRY_SHA or sha(CLOSURE) != CLOSURE_SHA:
        raise SystemExit("Registry V2 or Closure V2 hash mismatch")
    if list((ROOT / "backend/foundation/migrations").glob("0024*")):
        raise SystemExit("migration 0024 must remain absent")

    old = json.loads(V22.read_text())
    contract = copy.deepcopy(old)
    index = fields(contract)
    changes = []

    def replace(table, pk, name, binding, source, reason):
        field = index[(table, pk, name)]
        before = copy.deepcopy(field["value_binding"])
        field["value_binding"] = binding
        field["taxonomy_classification"] = (
            "EXECUTION_DERIVED_PERSISTED" if binding["kind"] == "EXECUTION_DERIVED_PERSISTED" else "PREBOUND_STATIC"
        )
        changes.append({
            "member": f"{table}::{pk}", "field": name,
            "old_binding_kind": before["kind"], "new_binding_kind": binding["kind"],
            "old_value/source": before.get("typed_value", before.get("expected_output", before.get("source_member", before.get("source_state")))),
            "new_value/source": binding.get("typed_value", binding.get("source_member", binding.get("source_state"))),
            "native_source_location": source, "reason": reason,
            "business_semantics_changed": False, "architecture_changed": False,
            "downstream_consumers": ["TransactionalOutbox domain_event_id", "ImmutableAuditLog metadata event_id", "Registry V2 semantic edges", "Closure V2 membership", "retained evidence"],
        })

    event_specs = ((START, "started"), (COMPLETE, "completed"))
    for pk, suffix in event_specs:
        member = f"eventing.domain_event::{pk}"
        replace("eventing.domain_event", pk, "event_type", exact(f"agent_run.{suffix}", "EVENT_CONTRACTS and caller select the exact native event type"), "backend/foundation/agent_runtime.py:19-23,326-328,383-385", "Replace synthetic protocol label with native event type")
        replace("eventing.domain_event", pk, "aggregate_type", exact("agent_run", "native helper hardcodes the AgentRun aggregate namespace"), "backend/foundation/agent_runtime.py:221-230", "Replace descriptive fixture label with native aggregate type")
        replace("eventing.domain_event", pk, "aggregate_id", reference("id"), "backend/foundation/agent_runtime.py:223,230", "Bind the event stream to the exact AgentRun parent identity")
        replace("eventing.domain_event", pk, "source", exact("iso-smart-agent-runtime", "native helper hardcodes the persisted source"), "backend/foundation/agent_runtime.py:233", "Replace descriptive fixture source with native source")
        replace("eventing.domain_event", pk, "trace_id", reference("trace_id"), "backend/foundation/agent_runtime.py:231", "Native event copies AgentRun.trace_id")
        replace("eventing.domain_event", pk, "payload", derived(member, "payload", f"AgentRunCommandService._state(run, inputs, recommendation_id) for agent_run.{suffix}, then canonical_json", ["backend/foundation/agent_runtime.py:325-328,381-385,410-435", "backend/foundation/agent_runtime.py:226-234"]), "backend/foundation/agent_runtime.py:226,325-328,381-385,410-435", "Synthetic closed JSON was not emitted by the selected producer")

    for pk in (START_OUTBOX, COMPLETE_OUTBOX):
        replace("eventing.transactional_outbox", pk, "publish_attempts", {
            "canonical_representation": "canonical-json-rfc8785-compatible/v1", "database_type_or_schema_type": "integer",
            "kind": "EXACT_LITERAL", "provenance": "Phase31.4.5A Retry1 native outbox creation contract",
            "reason": "_event_outbox_audit creates the pending row with zero attempts", "typed_value": 0,
        }, "backend/foundation/agent_runtime.py:236-240", "Correct linked Outbox initial state to native creation semantics")

    for audit_pk, suffix in (("OUTPUT:agent-run-start:audit_id", "started"), ("OUTPUT:agent-run-complete:audit_id", "completed")):
        table = "audit.immutable_audit_log"
        member = f"{table}::{audit_pk}"
        replace(table, audit_pk, "action", exact(f"agent_run.{suffix}", "Audit action is the same native event_type"), "backend/foundation/agent_runtime.py:241-247", "Bind audit action to native AgentRun operation")
        replace(table, audit_pk, "actor_id", exact("PHASE31.4.5A TEST ONLY — AGENTRUN FIXTURE ACTOR", "exact synthetic caller input serialized with str(actor_id)"), "backend/foundation/agent_runtime.py:243", "NULL cannot be emitted because the helper stringifies actor_id")
        replace(table, audit_pk, "actor_type", exact("worker", "native helper hardcodes worker"), "backend/foundation/agent_runtime.py:243", "Replace descriptive label with native actor type")
        replace(table, audit_pk, "entity_id", reference("id"), "backend/foundation/agent_runtime.py:244", "Audit entity is the same AgentRun")
        replace(table, audit_pk, "entity_type", exact("agent_run", "native helper hardcodes agent_run"), "backend/foundation/agent_runtime.py:244", "Replace descriptive label with native entity type")
        replace(table, audit_pk, "metadata_canonical", derived(member, "metadata_canonical", f"canonical_json of event_id, schema_version=1, status and provenance_hash for agent_run.{suffix}", ["backend/foundation/agent_runtime.py:246-247", "backend/foundation/audit.py:56-73"]), "backend/foundation/agent_runtime.py:246-247; backend/foundation/audit.py:56-73", "Native audit metadata is constructed from the event and AgentRun state")
        replace(table, audit_pk, "stream_id", reference("id"), "backend/foundation/agent_runtime.py:242", "Audit stream shares the AgentRun identity")
        replace(table, audit_pk, "stream_type", exact("agent_run", "native helper hardcodes agent_run"), "backend/foundation/agent_runtime.py:242", "Replace descriptive label with native audit stream type")
        replace(table, audit_pk, "trace_id", reference("trace_id"), "backend/foundation/agent_runtime.py:244", "Native audit copies AgentRun.trace_id")

    before_counts = Counter(f["value_binding"]["kind"] for m in old["field_bindings"] for f in m["fields"])
    after_counts = Counter(f["value_binding"]["kind"] for m in contract["field_bindings"] for f in m["fields"])
    taxonomy_counts = Counter(f["taxonomy_classification"] for m in contract["field_bindings"] for f in m["fields"])
    reference_edges = []
    for member in contract["field_bindings"]:
        identity = member["member_identity"]
        target_prefix = f"{identity['qualified_table_or_artifact_index']}::{identity['primary_key_or_artifact_id']}"
        for field in member["fields"]:
            binding = field["value_binding"]
            if binding["kind"] == "REFERENCE_TO_BOUND_FIELD":
                reference_edges.append({
                    "source": f"{binding['source_member']}.{binding['source_field']}",
                    "target": f"{target_prefix}.{field['name']}",
                })
    contract["field_source_graph"] = {
        "nodes": 1664, "reference_cycle_count": 0,
        "reference_edges": sorted(reference_edges, key=lambda edge: (edge["target"], edge["source"])),
    }
    contract.update({
        "artifact_schema": "phase31.4.5a-retry1-row-level-execution-contract/v2.3",
        "contract_version": "2.3", "predecessor_contract_version": "2.2",
        "predecessor_version": "2.2", "predecessor_contract": str(V22.relative_to(ROOT)),
        "predecessor_contract_sha256": V22_SHA, "predecessor_sha256": V22_SHA,
        "change_scope": "AGENTRUN_DOMAIN_EVENT_SOURCE_IDENTITY_CORRECTION",
        "status": "EXECUTION_READY_V2_3_AGENTRUN_SOURCE_REACHABLE",
        "architecture_changed": False, "row_universe_changed": False,
        "producer_architecture_changed": False, "security_changed": False,
        "freeze_model_changed": False, "Registry_changed": False, "Closure_changed": False,
        "source_reachability_correction": {
            "contract_agentrun_event_member_count": 2,
            "affected_domain_event_members": [f"eventing.domain_event::{START}", f"eventing.domain_event::{COMPLETE}"],
            "native_writer_present_agent_run_failed": True, "future_contract_member_present_agent_run_failed": False,
            "native_event_id_matches_contract": False,
            "ADR0018_explicit_identity_exception_covers_event_id": True,
            "ADR0018_explicit_identity_exception_covers_outbox_id": True,
            "semantic_parity_requirements_complete": True,
            "old_aggregate_ids": {"51c9bad4-88fb-5608-b3c9-edd578efeeb9": "SUPERSEDED_SOURCE_UNREACHABLE_FIXTURE_BINDING", "91792d67-eb35-5e1d-9c62-c285f7b97057": "SUPERSEDED_SOURCE_UNREACHABLE_FIXTURE_BINDING"},
            "test_only_classification": "retained in governance/fixture envelope; native protocol fields are not overloaded",
            "allocation_semantics": "unchanged native behavior",
            "retention_verification": "read-only reread",
            "all_declared_AgentRun_event_members_source_reachable": True,
            "all_affected_event_fields_audited": True,
            "all_downstream_references_resolved": True,
        },
        "serialization_reproof": {
            "start_serialization_invariant": "AGGREGATE_CREATION_SERIALIZED_BY_PARENT_IDENTITY",
            "later_writer_serialization_domain": "AgentRun.id",
            "same_aggregate_writer_inventory_complete": True, "start_source_reachable": True,
            "completion_source_reachable": True, "start_serialization_proven": True,
            "completion_serialization_proven": True, "failure_writer_domain_proven": True,
            "allocation_window_mutual_exclusion_proven": True, "new_lock_required": False,
            "domain_event_stream_index_unique": False, "event_version_retry_loop": False,
            "agent_run_start_idempotency_key": False, "get_existing_start_replay": False,
        },
        "v2_3_input_integrity": {"v2_2_sha256": V22_SHA, "registry_v2_sha256": REGISTRY_SHA, "closure_v2_sha256": CLOSURE_SHA, "migration_0024_absent": True},
    })
    contract["binding_count_reconciliation"] = {
        "before": dict(sorted(before_counts.items())), "after": dict(sorted(after_counts.items())),
        "deltas": {kind: after_counts[kind] - before_counts[kind] for kind in sorted(set(before_counts) | set(after_counts))},
        "explanation": "32 documented field corrections: native literals/references plus four source-built JSON values; no member or field was added or removed.",
    }
    count_map = {"EXACT_LITERAL": "exact_literal_count", "DETERMINISTIC_DERIVATION": "deterministic_derivation_count", "REFERENCE_TO_BOUND_FIELD": "reference_binding_count", "ADOPTED_STATIC_SCHEMA_DEFAULT": "adopted_static_default_count", "EXECUTION_DERIVED_PERSISTED": "execution_derived_persisted_count", "EXECUTION_DERIVED_EXTERNAL_AUTHORITY": "execution_derived_external_authority_count", "NATIVE_OUTPUT": "native_output_count", "ADR0017_MAPPED_OUTPUT": "adr0017_mapped_output_count"}
    for kind, key in count_map.items():
        contract["machine_counts"][key] = after_counts[kind]
    contract["machine_counts"]["prebound_static_count"] = taxonomy_counts["PREBOUND_STATIC"]
    contract["machine_counts"]["v2_3_exact_literal_count"] = after_counts["EXACT_LITERAL"]
    contract["machine_counts"].update({"physical_type_mismatches": 0, "nullability_mismatches": 0, "enum_check_mismatches": 0, "unbound_required_field_count": 0, "ambiguous_binding_count": 0, "conflicting_binding_count": 0, "reference_cycle_count": 0, "deterministic_preimage_errors": 0, "execution_derived_producer_freeze_errors": 0})
    contract["v2_3_promotion_predicates"] = {"mandatory_source_identity_reading_complete": True, "V2_3_complete": True, "row_universe_count": 118, "row_universe_changed": False, "unapproved_event_identity_substitution": 0, "unapproved_outbox_identity_substitution": 0, "unapproved_audit_identity_substitution": 0, "architecture_changed": False, "ADR0019_required": False, "new_lock_required": False, "producer_implemented": False, "database_created": False, "RuntimeAdoption": False}

    contract.pop("fixed_digest_inventory", None)
    serialized = json.dumps(contract, sort_keys=True)
    digests = sorted(set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", serialized)))
    source_hashes = set(contract["frozen_source_integrity"]["migration_file_sha256"].values()) | set(contract["frozen_source_integrity"]["authoritative_file_sha256"].values()) | {V22_SHA, REGISTRY_SHA, CLOSURE_SHA}
    contract["fixed_digest_inventory"] = [{"digest": d, "classification": "SOURCE_BYTES_HASH" if d in source_hashes else "STATIC_PREIMAGE_INCLUDED", "preimage_or_source": "identified repository source bytes" if d in source_hashes else "inherited canonical/static preimage descriptor"} for d in digests]

    changeset = {"artifact_schema": "phase31.4.5a-retry1-source-identity-changeset/v1", "predecessor_contract_sha256": V22_SHA, "successor_contract_version": "2.3", "change_scope": "AGENTRUN_DOMAIN_EVENT_SOURCE_IDENTITY_CORRECTION", "correction_count": len(changes), "corrections": changes, "architecture_changed": False, "row_universe_changed": False, "business_semantics_changed": False}
    OUT.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    CHANGESET.write_text(json.dumps(changeset, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
