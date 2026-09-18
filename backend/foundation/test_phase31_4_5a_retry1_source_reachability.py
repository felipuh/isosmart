"""Offline positive and negative tests for the AgentRun V2.3 correction."""

import copy
import hashlib
import json
import unittest

from foundation.phase31_4_5a_retry1_source_reachability_validator import (
    CHANGESET, CLOSURE, CLOSURE_SHA, CONTRACT, EVENTS, OUTBOXES, REGISTRY,
    REGISTRY_SHA, RUN_MEMBER, V22, V22_SHA, field_map, load_contract, metrics,
    validate, value,
)


class Phase3145ARetry1SourceReachabilityTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()

    def reject(self, mutate):
        candidate = copy.deepcopy(self.contract)
        mutate(candidate, field_map(candidate))
        self.assertTrue(validate(candidate))

    def test_positive_full_contract_and_invariant_artifacts(self):
        self.assertEqual(validate(self.contract), [])
        self.assertEqual(metrics(self.contract)["member_count"], 118)
        self.assertEqual(metrics(self.contract)["field_count"], 1664)
        self.assertEqual(metrics(self.contract)["contract_agentrun_event_member_count"], 2)
        self.assertEqual(hashlib.sha256(V22.read_bytes()).hexdigest(), V22_SHA)
        self.assertEqual(hashlib.sha256(REGISTRY.read_bytes()).hexdigest(), REGISTRY_SHA)
        self.assertEqual(hashlib.sha256(CLOSURE.read_bytes()).hexdigest(), CLOSURE_SHA)

    def test_exact_changeset_and_binding_counts(self):
        changeset = json.loads(CHANGESET.read_text())
        self.assertEqual(changeset["correction_count"], 32)
        self.assertEqual(self.contract["binding_count_reconciliation"]["deltas"], {
            "ADR0017_MAPPED_OUTPUT": 0, "DETERMINISTIC_DERIVATION": -10,
            "EXACT_LITERAL": -4, "EXECUTION_DERIVED_EXTERNAL_AUTHORITY": 0,
            "EXECUTION_DERIVED_PERSISTED": 4, "NATIVE_OUTPUT": 0,
            "REFERENCE_TO_BOUND_FIELD": 10,
        })

    def test_reject_non_native_start_event_type(self):
        self.reject(lambda _, f: value(f, "eventing.domain_event", next(iter(EVENTS)), "event_type").update(typed_value="synthetic.started"))

    def test_reject_non_native_completion_event_type(self):
        pk = next(pk for pk, event in EVENTS.items() if event.endswith("completed"))
        self.reject(lambda _, f: value(f, "eventing.domain_event", pk, "event_type").update(typed_value="agent_run.finished"))

    def test_reject_descriptive_aggregate_type(self):
        self.reject(lambda _, f: value(f, "eventing.domain_event", next(iter(EVENTS)), "aggregate_type").update(typed_value="TEST ONLY aggregate"))

    def test_reject_unrelated_aggregate_uuid(self):
        def mutate(_, f):
            binding = value(f, "eventing.domain_event", next(iter(EVENTS)), "aggregate_id")
            binding.clear(); binding.update({"kind": "EXACT_LITERAL", "typed_value": "51c9bad4-88fb-5608-b3c9-edd578efeeb9", "database_type_or_schema_type": "uuid", "canonical_representation": "x", "provenance": "x", "reason": "x"})
        self.reject(mutate)

    def test_reject_non_native_source_and_payload(self):
        pk = next(iter(EVENTS))
        self.reject(lambda _, f: value(f, "eventing.domain_event", pk, "source").update(typed_value="fixture"))
        def payload(_, f):
            binding = value(f, "eventing.domain_event", pk, "payload")
            binding.clear(); binding.update({"kind": "EXACT_LITERAL", "typed_value": {"synthetic": True}, "database_type_or_schema_type": "jsonb", "canonical_representation": "x", "provenance": "x", "reason": "x"})
        self.reject(payload)

    def test_reject_unapproved_event_and_outbox_identity_substitution(self):
        self.reject(lambda d, _: d["source_reachability_correction"].update(ADR0018_explicit_identity_exception_covers_event_id=False))
        self.reject(lambda d, _: d["source_reachability_correction"].update(ADR0018_explicit_identity_exception_covers_outbox_id=False))

    def test_reject_dangling_superseded_id_and_outbox_attempt_fiction(self):
        pk = next(iter(EVENTS))
        self.reject(lambda _, f: value(f, "eventing.domain_event", pk, "source").update(reason="51c9bad4-88fb-5608-b3c9-edd578efeeb9"))
        outbox = next(iter(OUTBOXES))
        self.reject(lambda _, f: value(f, "eventing.transactional_outbox", outbox, "publish_attempts").update(typed_value=1))

    def test_failure_writer_is_audited_but_not_added(self):
        correction = self.contract["source_reachability_correction"]
        self.assertTrue(correction["native_writer_present_agent_run_failed"])
        self.assertFalse(correction["future_contract_member_present_agent_run_failed"])
        self.assertFalse(any(row.get("purpose") == "DomainEvent:agent-run-failed" for row in self.contract["future_row_universe"]))

    def test_serialization_reproof(self):
        proof = self.contract["serialization_reproof"]
        self.assertEqual(proof["start_serialization_invariant"], "AGGREGATE_CREATION_SERIALIZED_BY_PARENT_IDENTITY")
        self.assertEqual(proof["later_writer_serialization_domain"], "AgentRun.id")
        self.assertTrue(proof["allocation_window_mutual_exclusion_proven"])
        self.assertFalse(proof["new_lock_required"])


if __name__ == "__main__":
    unittest.main()
