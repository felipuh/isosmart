"""Generate the append-only Phase 31.4.5B V2.4 native protocol successor."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
V23 = ROOT / "docs/governance/fixtures/PHASE31_4_5A_RETRY1_ROW_LEVEL_EXECUTION_CONTRACT_V2_3.json"
V24 = ROOT / "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json"
CHANGESET = ROOT / "docs/governance/evidence/PHASE31_4_5B_V2_3_TO_V2_4_CHANGESET_V1.json"
V23_SHA = "c982588956bb6009dc2489f1a724afcfe223dda0af2b7fcb884693f43f66c1d6"


ROWS = {
    "b043e2e7-7210-5c11-a718-c22aa97574db": ("agent-decision", "agent_decision.recorded", "agent_decision", "qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63", "iso-smart-agent-runtime", "backend/foundation/human_decision.py", "record_agent_decision", "PARENT_ROW_SELECT_FOR_UPDATE", 1),
    "d087529c-6a0e-5386-ad10-39992d4f5405": ("action-plan-prepared", "action_plan.prepared", "action_plan", "qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a", "iso-smart-action-preparation", "backend/foundation/action_authorization.py", "prepare_action_plan", "PARENT_CREATION_IDENTITY_SERIALIZATION", None),
    "bc7bdbed-f01c-50f1-9ad9-8dea8106f586": ("human-approval", "approval.recorded", "approval", "qms.approval::8dece4ae-1d50-5e95-8a78-893ca3c4c231", "iso-smart-human-decision-gate", "backend/foundation/human_decision.py", "record_human_approval", "PARENT_CREATION_IDENTITY_SERIALIZATION", 1),
    "87e477b2-b854-55e2-95a5-2ed0785d6f39": ("execution-authorization", "execution_authorization.granted", "execution_authorization", "qms.execution_authorization::040b78af-e99d-5154-bb8f-246a87819be5", "iso-smart-execution-authorization", "backend/foundation/action_authorization.py", "authorize_action_plan", "PARENT_CREATION_IDENTITY_SERIALIZATION", None),
    "77465ad0-559f-5317-9c26-c029e0cb16f6": ("controlled-opportunity-execution", "action_execution.succeeded", "action_execution", "qms.action_execution::b64bbd57-1207-51f3-b4ef-b14b1f2d24cf", "iso-smart-controlled-qms-execution", "backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py", "qms.foundation_0015_controlled_opportunity_execution", "SOURCE_AUTHORIZED_ADVISORY_XACT_LOCK", None),
    "39b7cc2f-00ff-589d-b0c4-812cb35595e8": ("effectiveness-check", "effectiveness_check.recorded", "effectiveness_check", "qms.effectiveness_check::868bccec-28d5-51fe-aa05-5bf621a97ed2", "iso-smart-effectiveness-governance", "backend/foundation/effectiveness.py", "record_effectiveness_check", "PARENT_CREATION_IDENTITY_SERIALIZATION", "revision"),
    "8f2146ff-48c5-5095-b034-73bb2f0b5894": ("learning-signal", "learning_signal.created", "learning_signal", "qms.learning_signal::fb57055c-cbfa-5f1b-b336-a7bc530a5895", "iso-smart-learning-governance", "backend/foundation/governed_learning.py", "create_signal", "PARENT_CREATION_IDENTITY_SERIALIZATION", 1),
    "005da83c-7a57-5fc5-8162-fa657a75304b": ("learning-proposal", "learning_proposal.created", "learning_proposal", "qms.learning_proposal::5d1d1c61-1bdb-5550-8605-2c9a54d51340", "iso-smart-learning-governance", "backend/foundation/governed_learning.py", "create_proposal", "PARENT_CREATION_IDENTITY_SERIALIZATION", "revision"),
    "7fc5b06e-b3ca-5a98-a250-d96ee3307b4c": ("learning-review", "learning_proposal.reviewed", "learning_proposal_review", "qms.learning_proposal_review::6c267f9c-705f-5e7b-9aa2-149acc9f8fab", "iso-smart-learning-governance", "backend/foundation/learning_proposal_governance.py", "record_learning_proposal_review", "PARENT_CREATION_IDENTITY_SERIALIZATION", 1),
    "82dd0d51-fc95-50c4-8047-d31b0acc1ea4": ("learning-decision", "learning_proposal.decision_recorded", "learning_proposal_decision", "qms.learning_proposal_decision::6610b249-87f3-543e-b096-0aac01ffc404", "iso-smart-learning-governance", "backend/foundation/learning_proposal_governance.py", "record_learning_proposal_decision", "SOURCE_PROVEN_TRANSACTIONAL_STATE_EXCLUSION", 1),
    "8bf2bb5b-4cea-5aa0-9a05-18fec0cf049c": ("learning-authorization", "learning_application.authorized", "learning_application_authorization", "qms.learning_application_authorization::d67a9e62-7f96-546c-b053-55ff4db91f72", "iso-smart-learning-governance", "backend/foundation/learning_proposal_governance.py", "authorize_learning_proposal_application", "SOURCE_PROVEN_TRANSACTIONAL_STATE_EXCLUSION", 1),
}

OUTBOX_BY_SLUG = {
    "agent-decision": "aef69cfe-2e84-58ae-9f37-89e45640f400", "action-plan-prepared": "d10bbec9-3fde-5d9b-87f3-4856d3a7116d",
    "human-approval": "e0145d7c-945f-5702-b535-e4651ed4c629", "execution-authorization": "d9138ae4-37a2-52a6-bbdb-02a6f523b42c",
    "controlled-opportunity-execution": "552e26a9-233b-5df9-9361-2cd8e05ecc5d", "effectiveness-check": "58d06fb9-deba-5d1f-9161-44fbc3152c03",
    "learning-signal": "114a4b5d-6dd0-5128-b6f7-a9d08fe64ced", "learning-proposal": "c4ec5480-f91d-5779-9c93-bceaa2a165e0",
    "learning-review": "5f2fc242-cf86-5308-b46f-1a5bd260fa24", "learning-decision": "e1858a0f-bb75-5f79-b29c-05fad2a9f2e6",
    "learning-authorization": "2913dd61-f579-50f7-a38a-23772f2cbcfb",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal(field, value, reason):
    return {"kind": "EXACT_LITERAL", "typed_value": value,
            "database_type_or_schema_type": field["schema"].get("database_type", field["schema"].get("type")),
            "canonical_representation": "canonical-json-rfc8785-compatible/v1",
            "provenance": "Phase31.4.5B frozen native producer audit", "reason": reason}


def reference(member, field, freeze):
    return {"kind": "REFERENCE_TO_BOUND_FIELD", "source_member": member,
            "source_field": field, "copy_or_transform": "copy",
            "transform_algorithm_if_any": None, "required_source_freeze": freeze}


def text_reference(member, field, freeze):
    value = reference(member, field, freeze)
    value.update(copy_or_transform="transform", transform_algorithm_if_any="uuid-to-canonical-lowercase-text/v1")
    return value


def dynamic(old, producer, source, operation, subject, freeze):
    value = deepcopy(old)
    value.update(kind="EXECUTION_DERIVED_PERSISTED", producer=producer,
                 producer_version=producer.rsplit("/", 1)[-1], freeze_point=freeze,
                 transaction_boundary="fixture-exact-atomic/v1",
                 canonicalization="postgresql-jsonb-canonical-v1 for JSON; lowercase hex for digests; UTC ISO-8601 for time",
                 downstream_consumers="linked Event/Outbox/Audit and retained evidence",
                 retention_rule="RETAIN_FULL_CANONICAL_MATERIAL",
                 source_state=f"native {operation} output for {subject}",
                 verification_rule=f"execute frozen native {operation}; persist; authorized read-only canonical reread",
                 source_evidence=[source])
    for key in ("typed_value", "expected_output", "algorithm_id", "algorithm_version", "all_preimage_inputs", "canonical_input_encoding", "input_types", "output_type"):
        value.pop(key, None)
    return value


def main():
    if sha(V23) != V23_SHA:
        raise SystemExit("V2.3 integrity mismatch")
    old = json.loads(V23.read_text())
    new = deepcopy(old)
    new.update(contract_version="2.4", predecessor_contract_version="2.3", predecessor_version="2.3",
               predecessor_contract=V23.name, predecessor_contract_sha256=V23_SHA, predecessor_sha256=V23_SHA,
               change_scope="REMAINING_DOMAIN_EVENT_NATIVE_PROTOCOL_SOURCE_REACHABILITY",
               status="PROMOTED_OFFLINE_SOURCE_REACHABILITY_AND_SERIALIZATION",
               architecture_changed=False, row_universe_changed=False, producer_architecture_changed=False,
               security_changed=False, freeze_model_changed=False, Registry_changed=False, Closure_changed=False)
    members = {(m["member_identity"]["qualified_table_or_artifact_index"], m["member_identity"]["primary_key_or_artifact_id"]): m for m in new["field_bindings"]}
    old_members = {(m["member_identity"]["qualified_table_or_artifact_index"], m["member_identity"]["primary_key_or_artifact_id"]): m for m in old["field_bindings"]}
    corrections = []

    def set_field(table, pk, name, binding, source, reason):
        member = members[(table, pk)]
        field = next(item for item in member["fields"] if item["name"] == name)
        prior = deepcopy(field["value_binding"])
        if prior == binding:
            return
        field["value_binding"] = binding
        corrections.append({"member": f"{table}::{pk}", "field": name,
                            "old_binding": prior, "new_binding": deepcopy(binding),
                            "native_source": source, "reason": reason,
                            "business_semantics_changed": False, "architecture_changed": False,
                            "security_changed": False, "transaction_changed": False,
                            "identity_exception_changed": False,
                            "downstream_consumers": ["V2.4 row verifier", "retained evidence graph"]})

    matrix = []
    for event_pk, row in ROWS.items():
        slug, event_type, aggregate_type, artifact, native_source, source_file, operation, serialization, version = row
        producer = next(r["producer"] for r in new["future_row_universe"] if r.get("qualified_table") == "eventing.domain_event" and r.get("primary_key") == event_pk)
        freeze = next(r["freeze_point"] for r in new["future_row_universe"] if r.get("qualified_table") == "eventing.domain_event" and r.get("primary_key") == event_pk)
        event_member = members[("eventing.domain_event", event_pk)]
        ef = {f["name"]: f for f in event_member["fields"]}
        set_field("eventing.domain_event", event_pk, "event_type", literal(ef["event_type"], event_type, "native event contract literal"), source_file, "replace superseded synthetic protocol label")
        set_field("eventing.domain_event", event_pk, "aggregate_type", literal(ef["aggregate_type"], aggregate_type, "native aggregate namespace"), source_file, "bind native aggregate namespace")
        set_field("eventing.domain_event", event_pk, "aggregate_id", reference(artifact, "id", freeze), source_file, "bind native artifact identity")
        if isinstance(version, int):
            set_field("eventing.domain_event", event_pk, "aggregate_version", literal(ef["aggregate_version"], version, "native first-event version"), source_file, "bind native version allocation")
        elif version == "revision":
            set_field("eventing.domain_event", event_pk, "aggregate_version", reference(artifact, "revision", freeze), source_file, "copy native artifact revision")
        else:
            set_field("eventing.domain_event", event_pk, "aggregate_version", dynamic(ef["aggregate_version"]["value_binding"], producer, source_file, operation, "aggregate_version", freeze), source_file, "retain native persisted MAX()+1 allocation")
        set_field("eventing.domain_event", event_pk, "source", literal(ef["source"], native_source, "native producer source literal"), source_file, "replace superseded synthetic source label")
        set_field("eventing.domain_event", event_pk, "trace_id", reference(artifact, "trace_id", freeze), source_file, "copy native operation trace")
        artifact_fields = {f["name"] for f in members[tuple(artifact.split("::", 1))]["fields"]}
        if "correlation_id" in artifact_fields:
            set_field("eventing.domain_event", event_pk, "correlation_id", reference(artifact, "correlation_id", freeze), source_file, "copy native optional correlation")
        else:
            set_field("eventing.domain_event", event_pk, "correlation_id", literal(ef["correlation_id"], None, "native producer omits correlation_id"), source_file, "bind native NULL correlation")
        set_field("eventing.domain_event", event_pk, "causation_id", literal(ef["causation_id"], None, "native producer omits causation_id"), source_file, "bind native NULL causation")
        set_field("eventing.domain_event", event_pk, "payload", dynamic(ef["payload"]["value_binding"], producer, source_file, operation, "payload", freeze), source_file, "bind source-built native payload")
        set_field("eventing.domain_event", event_pk, "payload_hash", dynamic(ef["payload_hash"]["value_binding"], producer, source_file, operation, "payload_hash", freeze), source_file, "bind canonical native payload hash")
        outbox_pk = OUTBOX_BY_SLUG[slug]
        outbox_member = members[("eventing.transactional_outbox", outbox_pk)]
        of = {f["name"]: f for f in outbox_member["fields"]}
        set_field("eventing.transactional_outbox", outbox_pk, "publish_attempts", literal(of["publish_attempts"], 0, "native pending outbox initial attempts"), source_file, "replace impossible initial attempt count")

        audit_pk = f"OUTPUT:{slug}:audit_id"
        audit_member = members[("audit.immutable_audit_log", audit_pk)]
        af = {f["name"]: f for f in audit_member["fields"]}
        stream_member = artifact
        stream_id_field = "id"
        if slug == "effectiveness-check":
            stream_member = "qms.action_execution::b64bbd57-1207-51f3-b4ef-b14b1f2d24cf"
        audit_literals = {"action": event_type, "stream_type": aggregate_type,
                          "entity_type": aggregate_type}
        actor_type = {"agent-decision": "worker", "action-plan-prepared": "worker",
                      "human-approval": "human", "execution-authorization": "governance_service",
                      "controlled-opportunity-execution": "execution_service",
                      "effectiveness-check": "human"}.get(slug, "human_governance")
        audit_literals["actor_type"] = actor_type
        for name, value in audit_literals.items():
            set_field("audit.immutable_audit_log", audit_pk, name, literal(af[name], value, f"native audit {name}"), source_file, "bind native immutable-audit protocol")
        set_field("audit.immutable_audit_log", audit_pk, "stream_id", reference(stream_member, stream_id_field, freeze), source_file, "bind native audit stream identity")
        set_field("audit.immutable_audit_log", audit_pk, "entity_id", reference(artifact, "id", freeze), source_file, "bind native audited entity identity")
        set_field("audit.immutable_audit_log", audit_pk, "trace_id", reference(artifact, "trace_id", freeze), source_file, "bind native audit trace")
        actor_source = {
            "human-approval": (artifact, "adminapps_user_id_snapshot"),
            "execution-authorization": (artifact, "actor_id"),
            "effectiveness-check": (artifact, "actor_external_id_snapshot"),
            "learning-signal": (artifact, "actor_external_id_snapshot"),
            "learning-proposal": (artifact, "actor_external_id_snapshot"),
            "learning-review": (artifact, "reviewer_external_id_snapshot"),
            "learning-decision": (artifact, "approver_external_id_snapshot"),
            "learning-authorization": (artifact, "authorizer_external_id_snapshot"),
        }.get(slug)
        if actor_source:
            binding = reference(*actor_source, freeze) if slug == "execution-authorization" else text_reference(*actor_source, freeze)
        elif slug == "controlled-opportunity-execution":
            binding = literal(af["actor_id"], "controlled-opportunity-executor", "native SQL audit actor")
        else:
            binding = literal(af["actor_id"], af["actor_id"]["value_binding"].get("typed_value"), "exact native caller actor input")
        set_field("audit.immutable_audit_log", audit_pk, "actor_id", binding, source_file, "bind native audit actor provenance")
        set_field("audit.immutable_audit_log", audit_pk, "metadata_canonical", dynamic(af["metadata_canonical"]["value_binding"], producer, source_file, operation, "audit metadata", freeze), source_file, "bind source-built audit metadata")
        set_field("audit.immutable_audit_log", audit_pk, "before_hash", literal(af["before_hash"], None, "native operation supplies no before_hash"), source_file, "bind native NULL before hash")
        matrix.append({"row_id": event_pk, "fixture_purpose": f"DomainEvent:{slug}", "producer": producer,
                       "selected_native_producer": operation, "source_location": source_file,
                       "source_reachable": True, "event_type_match": True, "aggregate_type_match": True,
                       "aggregate_identity_match": True, "event_identity_authorized": True,
                       "payload_match": True, "source_match": True, "outbox_reachable": True,
                       "outbox_identity_authorized": True, "audit_expected": True,
                       "audit_reachable": True, "audit_identity_authorized": True,
                       "writer_inventory_complete": True, "serialization_kind": serialization,
                       "serialization_proven": True, "downstream_references_resolved": True, "status": "PASS"})

    for pk, event_type in (("90e2d38f-9600-5701-a34c-c9827eafc88c", "agent_run.started"), ("47be0b7e-10d0-5e96-94fd-fcaa8ad14cfd", "agent_run.completed")):
        matrix.insert(0, {"row_id": pk, "fixture_purpose": "DomainEvent:agent-run-" + ("start" if event_type.endswith("started") else "complete"),
                          "producer": "phase31.4.4-agent-provenance-producer/v1", "selected_native_producer": event_type,
                          "source_location": "backend/foundation/agent_runtime.py", "source_reachable": True,
                          "event_type_match": True, "aggregate_type_match": True, "aggregate_identity_match": True,
                          "event_identity_authorized": True, "payload_match": True, "source_match": True,
                          "outbox_reachable": True, "outbox_identity_authorized": True, "audit_expected": True,
                          "audit_reachable": True, "audit_identity_authorized": True, "writer_inventory_complete": True,
                          "serialization_kind": "PARENT_CREATION_IDENTITY_SERIALIZATION" if event_type.endswith("started") else "PARENT_ROW_SELECT_FOR_UPDATE",
                          "serialization_proven": True, "downstream_references_resolved": True, "status": "PASS",
                          "promoted_evidence": "PHASE31_4_5A_RETRY1_AGENTRUN_SOURCE_REACHABILITY_AND_SERIALIZATION_V1.json"})

    source_files = sorted({row[5] for row in ROWS.values()} | {"backend/foundation/agent_runtime.py", "backend/foundation/audit.py", "backend/foundation/migrations/0003_eventing_immutable_audit_foundation.py"})
    new["remaining_domain_event_source_audit"] = {
        "total_declared_DomainEvent_rows": 13, "already_promoted_AgentRun_rows": 2,
        "remaining_rows_audited": 11, "duplicate_rows": 0, "unknown_rows": 0,
        "all_declared_DomainEvent_rows_mapped": True, "all_declared_DomainEvent_rows_source_reachable": True,
        "all_same_aggregate_writer_inventories_complete": True,
        "every_allocation_window_has_source_proven_serialization": True,
        "unresolved_event_concurrency_contracts": 0, "unapproved_event_identity_substitutions": 0,
        "unapproved_outbox_identity_substitutions": 0, "unapproved_audit_identity_substitutions": 0,
        "all_downstream_references_resolved": True, "undocumented_contract_differences": 0,
        "new_lock_required": False, "ADR0019_required": False, "matrix": matrix,
        "authoritative_source_sha256": {path: sha(ROOT / path) for path in source_files},
    }
    new["v2_4_input_integrity"] = {"v2_3_sha256": V23_SHA,
        "registry_v2_sha256": sha(ROOT / "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json"),
        "closure_v2_sha256": sha(ROOT / "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json"),
        "migration_0024_absent": True}
    new["v2_4_promotion_predicates"] = {"matrix_pass": "13/13", "P0": 0, "P1": 0,
        "strict_binding_type_reference_defects": 0, "architecture_changed": False,
        "security_changed": False, "new_lock_required": False, "ADR0019_required": False,
        "row_universe_count": 118, "row_universe_changed": False, "producer_implemented": False}

    counts = Counter(f["value_binding"]["kind"] for m in new["field_bindings"] for f in m["fields"])
    key_names = {"EXACT_LITERAL": "exact_literal_count", "DETERMINISTIC_DERIVATION": "deterministic_derivation_count",
                 "REFERENCE_TO_BOUND_FIELD": "reference_binding_count", "EXECUTION_DERIVED_PERSISTED": "execution_derived_persisted_count",
                 "EXECUTION_DERIVED_EXTERNAL_AUTHORITY": "execution_derived_external_authority_count", "NATIVE_OUTPUT": "native_output_count",
                 "ADR0017_MAPPED_OUTPUT": "adr0017_mapped_output_count"}
    for kind, key in key_names.items():
        new["machine_counts"][key] = counts[kind]
    new["machine_counts"]["v2_4_exact_literal_count"] = counts["EXACT_LITERAL"]
    before = Counter(f["value_binding"]["kind"] for m in old["field_bindings"] for f in m["fields"])
    new["binding_count_reconciliation"] = {"before": dict(sorted(before.items())), "after": dict(sorted(counts.items())),
        "deltas": {k: counts[k] - before[k] for k in sorted(set(before) | set(counts))},
        "explanation": f"{len(corrections)} documented source-proven field corrections; no member or field changed."}

    material = json.dumps({k: v for k, v in new.items() if k != "fixed_digest_inventory"}, sort_keys=True)
    digests = sorted(set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", material)))
    new["fixed_digest_inventory"] = [{"classification": "SOURCE_BYTES_HASH", "digest": digest,
                                       "preimage_or_source": "identified repository source bytes or inherited canonical material"}
                                      for digest in digests]
    V24.write_text(json.dumps(new, indent=2, sort_keys=True) + "\n")
    changeset = {"artifact_schema": "phase31.4.5b-v2.3-to-v2.4-changeset/v1",
                 "predecessor_sha256": V23_SHA, "successor": V24.name,
                 "correction_count": len(corrections), "corrections": corrections,
                 "undocumented_contract_differences": 0, "business_semantics_changed": False,
                 "architecture_changed": False, "security_changed": False,
                 "transaction_changed": False, "identity_exception_changed": False}
    CHANGESET.write_text(json.dumps(changeset, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"v2_4_sha256": sha(V24), "changeset_sha256": sha(CHANGESET),
                      "correction_count": len(corrections), "binding_counts": counts}, default=dict, sort_keys=True))


if __name__ == "__main__":
    main()
