"""Positive and adversarial offline tests for the complete 13-row V2.4 matrix."""

import copy
import unittest

from foundation.phase31_4_5b_source_reachability_validator import (
    EXPECTED, field_map, load_contract, metrics, validate,
)


class Phase3145BSourceReachabilityTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()

    def mutate_field(self, table, pk, name, **updates):
        candidate = copy.deepcopy(self.contract)
        field_map(candidate)[(table, pk, name)]["value_binding"].update(updates)
        return validate(candidate)

    def test_complete_positive_matrix(self):
        self.assertEqual(validate(self.contract), [])
        self.assertEqual(metrics(self.contract)["domain_event_rows"], 13)
        self.assertEqual(metrics(self.contract)["matrix_pass"], 13)

    def test_reject_wrong_event_type_aggregate_source_payload_and_causation(self):
        pk = next(iter(EXPECTED))
        self.assertTrue(any("wrong native event_type" in e for e in self.mutate_field("eventing.domain_event", pk, "event_type", typed_value="fixture.synthetic")))
        self.assertTrue(any("wrong native aggregate_type" in e for e in self.mutate_field("eventing.domain_event", pk, "aggregate_type", typed_value="unrelated")))
        self.assertTrue(any("wrong native source" in e for e in self.mutate_field("eventing.domain_event", pk, "source", typed_value="fixture")))
        self.assertTrue(any("impossible payload" in e for e in self.mutate_field("eventing.domain_event", pk, "payload", kind="EXACT_LITERAL")))
        self.assertTrue(any("unsupported causation" in e for e in self.mutate_field("eventing.domain_event", pk, "causation_id", typed_value="00000000-0000-0000-0000-000000000001")))

    def test_reject_wrong_aggregate_identity_and_outbox_link_contract(self):
        pk, (_, _, _, outbox, _) = next(iter(EXPECTED.items()))
        self.assertTrue(any("wrong aggregate identity" in e for e in self.mutate_field("eventing.domain_event", pk, "aggregate_id", kind="EXACT_LITERAL")))
        self.assertTrue(any("outbox initial attempts drift" in e for e in self.mutate_field("eventing.transactional_outbox", outbox, "publish_attempts", typed_value=1)))

    def test_reject_unapproved_event_outbox_and_audit_identity(self):
        for key in ("event_identity_authorized", "outbox_identity_authorized", "audit_identity_authorized"):
            candidate = copy.deepcopy(self.contract)
            candidate["remaining_domain_event_source_audit"]["matrix"][2][key] = False
            self.assertTrue(any("matrix row not PASS" in e for e in validate(candidate)))

    def test_reject_incomplete_writer_inventory_and_serialization_proof(self):
        for key in ("writer_inventory_complete", "serialization_proven"):
            candidate = copy.deepcopy(self.contract)
            candidate["remaining_domain_event_source_audit"]["matrix"][2][key] = False
            self.assertTrue(any("matrix row not PASS" in e for e in validate(candidate)))
        candidate = copy.deepcopy(self.contract)
        candidate["remaining_domain_event_source_audit"]["matrix"][2]["serialization_kind"] = "UNRESOLVED"
        candidate["remaining_domain_event_source_audit"]["matrix"][2]["serialization_proven"] = False
        self.assertTrue(validate(candidate))

    def test_reject_plain_index_claimed_unique_and_retry_fiction(self):
        candidate = copy.deepcopy(self.contract)
        candidate["remaining_domain_event_source_audit"]["matrix"][2]["serialization_kind"] = "UNIQUE_INDEX"
        candidate["remaining_domain_event_source_audit"]["matrix"][2]["serialization_proven"] = False
        self.assertTrue(validate(candidate))
        candidate = copy.deepcopy(self.contract)
        candidate["remaining_domain_event_source_audit"]["matrix"][2]["retry_behavior"] = "retry loop not present in source"
        candidate["remaining_domain_event_source_audit"]["matrix"][2]["serialization_proven"] = False
        self.assertTrue(validate(candidate))

    def test_reject_dangling_superseded_protocol_and_inexact_changeset(self):
        pk = next(iter(EXPECTED))
        errors = self.mutate_field("eventing.domain_event", pk, "source", typed_value="PHASE31.4.4A TEST ONLY — DomainEvent:agent-decision — source")
        self.assertTrue(any("dangling superseded" in e for e in errors))
        candidate = copy.deepcopy(self.contract)
        candidate["remaining_domain_event_source_audit"]["matrix"].pop()
        self.assertTrue(any("13-row source matrix" in e for e in validate(candidate)))


if __name__ == "__main__":
    unittest.main()
