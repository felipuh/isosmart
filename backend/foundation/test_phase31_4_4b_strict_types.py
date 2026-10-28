import copy
import json
import unittest
from pathlib import Path

from foundation.phase31_4_4b_strict_type_validator import (
    BLOCKER_PATH,
    load_contract,
    validate,
    validation_metrics,
)


class Phase3144BStrictPhysicalTypeTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()
        self.conflicts = json.loads(Path(BLOCKER_PATH).read_text())["conflicts"]

    def assertRejected(self, mutate):
        candidate = copy.deepcopy(self.contract)
        mutate(candidate)
        self.assertTrue(validate(candidate))

    @staticmethod
    def fields(contract):
        for member in contract["field_bindings"]:
            identity = member["member_identity"]
            for field in member["fields"]:
                yield identity["qualified_table_or_artifact_index"], identity["primary_key_or_artifact_id"], member, field

    def find(self, contract, table, primary_key, name):
        return next((member, field) for t, p, member, field in self.fields(contract) if (t, p, field["name"]) == (table, primary_key, name))

    @staticmethod
    def exact(value, typ):
        return {
            "kind": "EXACT_LITERAL", "typed_value": value,
            "database_type_or_schema_type": typ,
            "canonical_representation": "canonical-json-rfc8785-compatible/v1",
            "provenance": "negative test", "reason": "negative test",
        }

    def test_positive_full_contract(self):
        self.assertEqual(validate(self.contract), [])
        metrics = validation_metrics(self.contract)
        self.assertEqual(metrics["member_count"], 118)
        self.assertEqual(metrics["field_count"], 1664)
        self.assertEqual(metrics["strict_fields_checked"], 1664)
        self.assertEqual(metrics["v2_1_exact_literal_count"], 779)
        self.assertEqual(metrics["v2_2_exact_literal_count"], 753)
        self.assertEqual(metrics["reclassified_exact_literal_count"], 26)

    def test_exact_34_conflicts_are_corrected(self):
        self.assertEqual(len(self.conflicts), 34)
        for item in self.conflicts:
            key = (item["qualified_table_or_artifact"], item["primary_key_or_artifact_id"], item["field"])
            with self.subTest(key=key):
                _, field = self.find(self.contract, *key)
                if key[0] in {"eventing.domain_event", "audit.immutable_audit_log"}:
                    self.assertEqual(field["value_binding"]["kind"], "EXECUTION_DERIVED_PERSISTED")
                    self.assertNotIn("typed_value", field["value_binding"])
                    self.assertIsNone(field["value_binding"]["expected_literal_if_static"])
                else:
                    self.assertEqual(field["schema"]["type"], "CharField")
                    self.assertEqual(field["value_binding"]["typed_value"], item["typed_value"])
                    self.assertEqual(field["value_binding"]["business_identifier_semantics"], "BUSINESS IDENTIFIER TEXT")

    def first_bigint(self, contract, table):
        item = next(x for x in self.conflicts if x["qualified_table_or_artifact"] == table)
        return self.find(contract, table, item["primary_key_or_artifact_id"], item["field"])[1]

    def test_descriptive_text_cannot_be_aggregate_version(self):
        def mutate(d):
            f = self.first_bigint(d, "eventing.domain_event")
            f["taxonomy_classification"] = "PREBOUND_STATIC"
            f["value_binding"] = self.exact("descriptive version", "bigint")
        self.assertRejected(mutate)

    def test_descriptive_text_cannot_be_sequence_number(self):
        def mutate(d):
            f = self.first_bigint(d, "audit.immutable_audit_log")
            f["taxonomy_classification"] = "PREBOUND_STATIC"
            f["value_binding"] = self.exact("descriptive sequence", "bigint")
        self.assertRejected(mutate)

    def test_negative_sequence_rejected(self):
        def mutate(d):
            f = self.first_bigint(d, "audit.immutable_audit_log")
            f["taxonomy_classification"] = "PREBOUND_STATIC"
            f["value_binding"] = self.exact(-1, "bigint")
        self.assertRejected(mutate)

    def test_bool_rejected_as_integer(self):
        def mutate(d):
            f = self.first_bigint(d, "eventing.domain_event")
            f["taxonomy_classification"] = "PREBOUND_STATIC"
            f["value_binding"] = self.exact(True, "bigint")
        self.assertRejected(mutate)

    def test_integer_outside_bigint_range_rejected(self):
        def mutate(d):
            f = self.first_bigint(d, "eventing.domain_event")
            f["taxonomy_classification"] = "PREBOUND_STATIC"
            f["value_binding"] = self.exact(2**63, "bigint")
        self.assertRejected(mutate)

    def test_aggregate_version_cannot_reference_unrelated_event(self):
        self.assertRejected(lambda d: self.first_bigint(d, "eventing.domain_event")["value_binding"].update(preimage={"persisted_history": "unrelated event"}))

    def test_audit_sequence_cannot_use_unrelated_stream(self):
        self.assertRejected(lambda d: self.first_bigint(d, "audit.immutable_audit_log")["value_binding"].update(preimage={"stream_id": "unrelated"}))

    def test_execution_derived_sequence_requires_producer(self):
        self.assertRejected(lambda d: self.first_bigint(d, "audit.immutable_audit_log")["value_binding"].update(producer=""))

    def test_execution_derived_aggregate_requires_verification_rule(self):
        self.assertRejected(lambda d: self.first_bigint(d, "eventing.domain_event")["value_binding"].update(verification_rule=""))

    def test_uuid_field_rejects_arbitrary_text(self):
        def mutate(d):
            _, f = next((m, f) for t, p, m, f in self.fields(d) if f["schema"].get("type") == "UUIDField" and f["value_binding"].get("kind") == "EXACT_LITERAL" and f["value_binding"].get("typed_value") is not None)
            f["value_binding"]["typed_value"] = "not-a-uuid"
        self.assertRejected(mutate)

    def test_text_field_cannot_be_forced_to_uuid(self):
        item = next(x for x in self.conflicts if x["qualified_table_or_artifact"].startswith("qms."))
        def mutate(d):
            _, f = self.find(d, item["qualified_table_or_artifact"], item["primary_key_or_artifact_id"], item["field"])
            f["schema"].update(type="UUIDField", database_type="uuid")
            f["value_binding"]["database_type_or_schema_type"] = "uuid"
        self.assertRejected(mutate)

    def test_boolean_receiving_string_rejected(self):
        def mutate(d):
            _, f = next((m, f) for _, _, m, f in self.fields(d) if f["schema"].get("type") == "BooleanField" and f["value_binding"].get("kind") == "EXACT_LITERAL")
            f["value_binding"]["typed_value"] = "false"
        self.assertRejected(mutate)

    def test_json_object_receiving_serialized_string_rejected(self):
        def mutate(d):
            _, f = next((m, f) for _, _, m, f in self.fields(d) if f["schema"].get("type") == "JSONField" and f["value_binding"].get("kind") == "EXACT_LITERAL")
            f["value_binding"]["typed_value"] = '{"serialized":true}'
        self.assertRejected(mutate)

    def test_null_on_not_null_rejected(self):
        def mutate(d):
            _, f = next((m, f) for _, _, m, f in self.fields(d) if not f["schema"].get("nullable") and f["value_binding"].get("kind") == "EXACT_LITERAL")
            f["value_binding"]["typed_value"] = None
        self.assertRejected(mutate)

    def test_invalid_enum_check_literal_rejected(self):
        _, field = next((m, f) for t, _, m, f in self.fields(self.contract) if (t, f["name"]) == ("qms.tenant_projection", "lifecycle_status"))
        self.assertEqual(field["value_binding"]["typed_value"], "pending")
        self.assertRejected(lambda d: self.find(d, "qms.tenant_projection", "daa6bb22-660c-56f5-aadf-c63f06b01731", "lifecycle_status")[1]["value_binding"].update(typed_value="invalid"))


if __name__ == "__main__":
    unittest.main()
