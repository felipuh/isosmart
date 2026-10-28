import copy
import unittest

from foundation.phase31_4_4a_field_binding_validator import load_contract, validate


class Phase3144AFieldBindingTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()

    def assertRejected(self, mutate):
        candidate = copy.deepcopy(self.contract)
        mutate(candidate)
        self.assertTrue(validate(candidate))

    def tenant(self, contract):
        return next(x for x in contract["field_bindings"] if x["member_identity"]["qualified_table_or_artifact_index"] == "qms.tenant_projection")

    def field(self, member, name):
        return next(x for x in member["fields"] if x["name"] == name)

    def test_positive_complete_contract(self):
        self.assertEqual(validate(self.contract), [])
        self.assertEqual(self.contract["machine_counts"]["member_count"], 118)
        self.assertEqual(self.contract["machine_counts"]["unbound_required_field_count"], 0)

    def test_reject_each_original_tenant_blocker(self):
        for name in ("adminapps_tenant_id", "source_version", "display_name_snapshot", "lifecycle_status", "provisioning_status", "reconciliation_status"):
            with self.subTest(name=name):
                self.assertRejected(lambda d, n=name: self.tenant(d)["fields"].remove(self.field(self.tenant(d), n)))

    def test_reject_any_missing_column(self): self.assertRejected(lambda d: d["field_bindings"][1]["fields"].pop())
    def test_reject_prebound_without_value(self): self.assertRejected(lambda d: self.field(self.tenant(d), "display_name_snapshot").update(value_binding=None))
    def test_reject_two_bindings(self): self.assertRejected(lambda d: self.tenant(d)["fields"].append(copy.deepcopy(self.tenant(d)["fields"][0])))
    def test_reject_invalid_enum(self): self.assertRejected(lambda d: self.field(self.tenant(d), "lifecycle_status")["value_binding"].update(typed_value="invented"))
    def test_reject_unspecified_nullable(self): self.assertRejected(lambda d: self.field(self.tenant(d), "source_event_id").update(value_binding={"kind": "EXACT_LITERAL"}))
    def test_reject_dynamic_default_as_static(self): self.assertRejected(lambda d: self.field(self.tenant(d), "display_name_snapshot").update(value_binding={"kind":"ADOPTED_STATIC_SCHEMA_DEFAULT","migration_path":"x","schema_object":"x","column":"x","exact_default_expression":"statement_timestamp()","semantic_interpretation":"x","determinism_proof":"x"}))
    def test_reject_derivation_missing_preimage(self): self.assertRejected(lambda d: self.field(self.tenant(d), "adminapps_tenant_id").update(value_binding={"kind":"DETERMINISTIC_DERIVATION","algorithm_id":"uuid5","algorithm_version":"v1","all_preimage_inputs":{},"input_types":{},"canonical_input_encoding":"utf8","output_type":"uuid","expected_output":"","verification_rule":"x"}))
    def test_reject_reference_to_unbound(self): self.assertRejected(lambda d: self.field(d["field_bindings"][1], "tenant_id")["value_binding"].update(source_member="qms.missing::00000000-0000-0000-0000-000000000000"))
    def test_reject_reference_cycle(self):
        def mutate(d):
            f = self.field(self.tenant(d), "display_name_snapshot")
            f["value_binding"] = {"kind":"REFERENCE_TO_BOUND_FIELD","source_member":"qms.tenant_projection::daa6bb22-660c-56f5-aadf-c63f06b01731","source_field":"display_name_snapshot","required_source_freeze":"Freeze0","copy_or_transform":"copy","transform_algorithm_if_any":None}
        self.assertRejected(mutate)
    def test_reject_placeholder(self): self.assertRejected(lambda d: self.field(self.tenant(d), "display_name_snapshot")["value_binding"].update(typed_value="<synthetic>"))
    def test_reject_caller_controlled_tenant(self): self.assertRejected(lambda d: d["tenant_projection_fixture_boundary"].update(caller_controlled=True))
    def test_reject_real_adminapps(self): self.assertRejected(lambda d: d["tenant_projection_fixture_boundary"].update(adminapps_contact=True))
    def test_reject_runtime_adoption(self): self.assertRejected(lambda d: d["v2_1_promotion_predicates"].update(RuntimeAdoption=True))
    def test_reject_row_removed(self): self.assertRejected(lambda d: d["future_row_universe"].pop())
    def test_reject_row_added(self): self.assertRejected(lambda d: d["future_row_universe"].append(copy.deepcopy(d["future_row_universe"][0])))
    def test_reject_table_changed(self): self.assertRejected(lambda d: d["future_row_universe"][0].update(qualified_table="qms.changed"))
    def test_reject_primary_key_changed(self): self.assertRejected(lambda d: d["future_row_universe"][0].update(primary_key="00000000-0000-0000-0000-000000000000"))
    def test_reject_producer_changed(self): self.assertRejected(lambda d: d["future_row_universe"][0].update(producer="changed"))
    def test_reject_security_matrix_changed(self): self.assertRejected(lambda d: d["security_rls_matrix"][0].update(RLS_enabled=False))
    def test_reject_freeze_order_changed(self): self.assertRejected(lambda d: d["freeze_order"].reverse())


if __name__ == "__main__":
    unittest.main()
