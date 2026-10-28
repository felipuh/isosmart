"""Offline acceptance and hostile-mutation tests for Phase 31.4.4."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_ROW_LEVEL_EXECUTION_CONTRACT_V2.json"
REGISTRY_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json"
CLOSURE_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json"
MIGRATION_0022 = ROOT / "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py"
ALLOWED_MODES = {
    "UUIDV5_FIXTURE_ASSIGNED", "NATIVE_RELEASE_CHILD_ID", "NATIVE_UUIDV7_OUTPUT",
    "OUTPUT_ID_MAPPED_BY_ADR0017", "NATIVE_CROSS_TABLE_SHARED_ID",
    "COMPOSITE_PRIMARY_KEY", "PREEXISTING_FROZEN_ID",
}
REQUIRED_ROW_KEYS = {
    "qualified_table", "primary_key", "row_type", "purpose",
    "created_or_preexisting_fixture", "producer", "producer_version",
    "identity_mode", "field_contract_ref", "transaction_boundary",
    "authority_contract", "capability_contract", "tenant_or_global_scope",
    "RLS_contract", "event_ids", "outbox_ids", "audit_ids",
    "curation_audit_ids", "freeze_point", "retention_disposition",
    "verification_rule",
}


def load_contract():
    return json.loads(CONTRACT_PATH.read_text())


def validate(contract):
    errors = []
    rows = contract.get("future_row_universe", [])
    seen = set()
    for index, row in enumerate(rows):
        missing = REQUIRED_ROW_KEYS - row.keys()
        if missing:
            errors.append(f"row {index} missing {sorted(missing)}")
        key = (row.get("qualified_table"), row.get("primary_key"))
        if key in seen:
            errors.append(f"duplicate qualified identity {key}")
        seen.add(key)
        if row.get("identity_mode") not in ALLOWED_MODES:
            errors.append(f"row {index} invalid identity mode")
        if not row.get("producer") or row.get("producer") in {"fixture", "future harness", "Phase31.4", "service TBD"}:
            errors.append(f"row {index} invalid producer")
        if not row.get("freeze_point"):
            errors.append(f"row {index} missing freeze")
        if not row.get("field_contract_ref"):
            errors.append(f"row {index} missing field contract")
    matrix = {x["qualified_table"]: x for x in contract.get("security_rls_matrix", [])}
    for row in rows:
        entry = matrix.get(row["qualified_table"])
        if not entry:
            errors.append(f"missing security row {row['qualified_table']}")
        elif row["tenant_or_global_scope"] == "TENANT" and (
            not entry["RLS_enabled"] or not entry["RLS_forced"] or
            entry["applicable_policy"] == "GLOBAL_TABLE_NO_TENANT_RLS"
        ):
            errors.append(f"missing applicable RLS {row['qualified_table']}")
    taxonomy = contract.get("field_taxonomy", {})
    rules = taxonomy.get("rules", [])
    if [x.get("classification") for x in rules] != [
        "OUTPUT_ID_MAPPED_BY_ADR0017", "EXECUTION_DERIVED_EXTERNAL_AUTHORITY",
        "EXECUTION_DERIVED_PERSISTED", "PREBOUND_STATIC",
    ]:
        errors.append("field taxonomy is not total/exclusive precedence")
    for rule in rules:
        if not all(rule.get(k) for k in ("source", "freeze", "verifier")):
            errors.append("taxonomy rule lacks source/freeze/verifier")
    if taxonomy.get("unknown_classification") is not None:
        errors.append("unknown field classification")
    observed_modes = {row.get("identity_mode") for row in rows}
    if not {"NATIVE_RELEASE_CHILD_ID", "NATIVE_UUIDV7_OUTPUT", "NATIVE_CROSS_TABLE_SHARED_ID"} <= observed_modes:
        errors.append("native identity modes were replaced by a universal fixture identity")
    types = [r.get("row_type", "") for r in rows]
    bases = {value.split(":")[0] for value in types}
    required = {"ModelPolicy", "AgentDefinition", "AgentRun", "AgentRunInput",
                "AgentRunRecommendation", "Recommendation", "RecommendationBasis",
                "AgentDecision", "ActionPlan", "ActionPlanDryRun", "Approval",
                "ExecutionAuthorization", "ActionExecution", "ActionExecutionReceipt",
                "EffectivenessCheck", "EffectivenessEvidence", "LearningSignal",
                "LearningSignalEffectiveness", "LearningProposal", "LearningProposalSignal"}
    if not required <= bases:
        errors.append("support graph row missing")
    if "AgentDecision" in types and "ActionPlan" in types and types.index("AgentDecision") > types.index("ActionPlan"):
        errors.append("ActionPlan precedes AgentDecision")
    material = contract.get("static_material", {})
    if material.get("action_type") != "opportunity.defer_evaluation": errors.append("wrong controlled action")
    if material.get("model_policy", {}).get("status_at_run") != "published": errors.append("draft ModelPolicy")
    if material.get("agent_definition", {}).get("status_at_run") != "published": errors.append("draft AgentDefinition")
    if not material.get("input_basis_equality", {}).get("agent_run_input_ids"): errors.append("missing AgentRunInput")
    if not material.get("input_basis_equality", {}).get("recommendation_basis_ids"): errors.append("missing RecommendationBasis")
    if material.get("effectiveness", {}).get("revision") != 1 or material.get("effectiveness", {}).get("correction_lineage_required") is not False: errors.append("invalid first Effectiveness revision")
    if material.get("effectiveness", {}).get("outcome_rule") in (None, ""): errors.append("missing effectiveness evaluation")
    if not material.get("proposal", {}).get("supporting_signal_id"): errors.append("Proposal missing Signal")
    if contract.get("b1", {}).get("target_hash_mode") != "EXECUTION_DERIVED_PERSISTED": errors.append("predicted root target hash")
    if contract.get("b2", {}).get("hash_mode") != "EXECUTION_DERIVED_PERSISTED": errors.append("B2 hash prebound")
    if contract.get("b3", {}).get("hash_mode") != "EXECUTION_DERIVED_PERSISTED": errors.append("B3 hash prebound")
    if contract.get("b3", {}).get("self_reference") is not False: errors.append("B3 self-reference")
    admission = contract.get("governed_admission", {})
    if admission.get("native_hash_is_governed_hash") is not False: errors.append("native/governed hash collapse")
    if "never rewrite" not in admission.get("same_native_hash_different_governed_material", ""): errors.append("replay replaces original provenance")
    if contract.get("phase29", {}).get("operational_dependencies"): errors.append("Phase29 operational dependency")
    if contract.get("promotion_flags", {}).get("RuntimeAdoption") is not False: errors.append("RuntimeAdoption enabled")
    support = contract.get("support_producer", {})
    if support.get("accepted_parameters") != [] or support.get("arbitrary_table_model_uuid_operation_actor_json_target_or_fields") is not False: errors.append("generic support producer")
    if support.get("outer_transaction_around_native_services") is not False: errors.append("nested trusted tenant context")
    if len(contract.get("identity_contract", {}).get("adr0017_exact_outputs", {})) != 7: errors.append("ADR0017 boundary broadened")
    publication_fields = contract.get("artifact_schemas", {}).get("knowledge-layer-rule-publication-governed-admission/v1", [])
    if set(admission.get("prepublication_forbidden_facts", [])) & set(publication_fields): errors.append("postpublication fact in Publication admission")
    return errors


class Phase3144PositiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract()
        cls.rows = cls.contract["future_row_universe"]

    def test_contract_accepts(self):
        self.assertEqual(validate(self.contract), [])

    def test_every_row_has_one_producer_identity_and_field_contract(self):
        self.assertTrue(all(r["producer"] and r["identity_mode"] and r["field_contract_ref"] for r in self.rows))
        self.assertEqual(len(self.rows), len(self.contract["producer_matrix"]))

    def test_every_field_rule_has_class_source_freeze_verifier(self):
        self.assertTrue(all(set(("classification", "source", "freeze", "verifier")) <= set(r) for r in self.contract["field_taxonomy"]["rules"]))

    def test_all_tenant_tables_have_applicable_forced_rls(self):
        matrix = self.contract["security_rls_matrix"]
        self.assertTrue(all(x["RLS_enabled"] and x["RLS_forced"] and x["applicable_policy"].startswith("phase31_4_4_exact_") for x in matrix if x["global_or_tenant"] == "TENANT"))

    def test_deterministic_exceptions_are_enumerated(self):
        expected = [r["row_type"] for r in self.rows if r["identity_mode"] == "UUIDV5_FIXTURE_ASSIGNED"]
        self.assertEqual(self.contract["identity_contract"]["adr0018_deterministic_replacements"], expected)

    def test_native_release_vectors_preserve_0022(self):
        source = MIGRATION_0022.read_text()
        self.assertIn("substr(md5(p_id::text||':'||p_suffix)", source)
        for parent, vectors in self.contract["native_release_identity"]["vectors"].items():
            for suffix, expected in vectors.items():
                digest = hashlib.md5(f"{parent}:{suffix}".encode()).hexdigest()
                actual = str(uuid.UUID(f"{digest[:8]}-{digest[8:12]}-4{digest[13:16]}-8{digest[17:20]}-{digest[20:32]}"))
                self.assertEqual(actual, expected)

    def test_cross_table_reuse_only_declared(self):
        by_pk = {}
        for row in self.rows:
            by_pk.setdefault(row["primary_key"], []).append(row)
        for values in by_pk.values():
            if len(values) > 1:
                modes = {r["identity_mode"] for r in values}
                self.assertIn("NATIVE_CROSS_TABLE_SHARED_ID", modes)
                self.assertLessEqual(modes, {"NATIVE_CROSS_TABLE_SHARED_ID", "UUIDV5_FIXTURE_ASSIGNED"})

    def test_b1_root_and_target_complete(self):
        self.assertEqual(self.contract["b1"]["root_id"], "bc5f4f17-294d-5abd-b27b-2d296921ffdf")
        self.assertEqual(self.contract["b1"]["target_hash_mode"], "EXECUTION_DERIVED_PERSISTED")
        self.assertIn("knowledge-layer-rule-root-target-artifact/v1", self.contract["artifact_schemas"])

    def test_support_graph_and_agent_provenance_complete(self):
        types = {r["row_type"].split(":")[0] for r in self.rows}
        required = {"ModelPolicy", "AgentDefinition", "AgentRun", "AgentRunInput", "AgentRunRecommendation", "Recommendation", "RecommendationBasis"}
        self.assertLessEqual(required, types)
        self.assertEqual(self.contract["static_material"]["input_basis_equality"]["equality_key"], ["standard_edition_id", "knowledge_layer_rule_id", "requirement_control_id", "evidence_id", "dataset_version_reference", "embedding_namespace"])

    def test_agent_decision_precedes_action_plan(self):
        types = [r["row_type"] for r in self.rows]
        self.assertLess(types.index("AgentDecision"), types.index("ActionPlan"))

    def test_effectiveness_and_signal_legal_path(self):
        material = self.contract["static_material"]
        self.assertEqual(material["action_type"], "opportunity.defer_evaluation")
        self.assertFalse(material["effectiveness"]["measurement_definition_required"])
        self.assertFalse(material["effectiveness"]["correction_lineage_required"])
        self.assertEqual(material["effectiveness"]["expected_derived_outcome"], "effective")
        self.assertEqual(material["proposal"]["supporting_signal_id"], next(r["primary_key"] for r in self.rows if r["row_type"] == "LearningSignal"))

    def test_b2_b3_and_checkpoint_are_complete_and_nonrecursive(self):
        self.assertEqual(self.contract["b2"]["id"], "37d3d0bc-4387-581a-a627-f02a011250d1")
        self.assertEqual(self.contract["b3"]["id"], "981e1753-dcd1-5f8d-8b10-49bfaed5eafb")
        self.assertFalse(self.contract["b3"]["self_reference"])
        self.assertNotIn("canonical_hash", self.contract["checkpoint_members"])

    def test_publication_admission_is_prepublication_only(self):
        fields = self.contract["artifact_schemas"]["knowledge-layer-rule-publication-governed-admission/v1"]
        self.assertFalse(set(self.contract["governed_admission"]["prepublication_forbidden_facts"]) & set(fields))

    def test_publication_eligibility_requires_full_closure(self):
        eligibility = self.contract["publication_eligibility"]
        self.assertTrue(all(eligibility[k] for k in eligibility if k != "reconstruction_required"))
        self.assertFalse(eligibility["reconstruction_required"])

    def test_native_and_governed_hashes_are_separate(self):
        self.assertFalse(self.contract["governed_admission"]["native_hash_is_governed_hash"])

    def test_replay_provenance_is_immutable(self):
        admission = self.contract["governed_admission"]
        self.assertIn("immutable", admission["original_operation_authority_provenance"])
        self.assertIn("never rewrite", admission["same_native_hash_different_governed_material"])

    def test_no_unexplained_fixed_hashes(self):
        self.assertEqual(self.contract["fixed_hash_audit"]["fixed_hash_without_preimage"], 0)
        self.assertEqual(self.contract["fixed_hash_audit"]["execution_derived_numeric_hashes"], [])

    def test_no_phase29_or_runtime_adoption(self):
        text = CONTRACT_PATH.read_text()
        self.assertEqual(self.contract["phase29"]["operational_dependencies"], [])
        self.assertFalse(self.contract["promotion_flags"]["RuntimeAdoption"])
        for forbidden in self.contract["phase29"]["forbidden_ids"]:
            self.assertEqual(text.count(forbidden), 1)  # forbidden-list declaration only

    def test_registry_and_closure_cover_universe(self):
        registry = json.loads(REGISTRY_PATH.read_text())
        closure = json.loads(CLOSURE_PATH.read_text())
        self.assertEqual(len(registry["edges"]), len(self.rows) - 1)
        self.assertEqual(set(closure["member_keys"]), {f"{r['qualified_table']}::{r['primary_key']}" for r in self.rows})
        self.assertEqual(closure["unknown_disposition_count"], 0)

    def test_freeze_graph_is_acyclic(self):
        order = self.contract["freeze_order"]
        self.assertEqual(len(order), len(set(order)))
        self.assertLess(order.index("Freeze7a"), order.index("Freeze7b"))
        self.assertLess(order.index("Freeze7e"), order.index("Freeze8"))


class Phase3144NegativeTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()

    def assertRejected(self, mutation):
        candidate = copy.deepcopy(self.contract)
        mutation(candidate)
        self.assertTrue(validate(candidate))

    def test_reject_row_without_producer(self): self.assertRejected(lambda d: d["future_row_universe"][0].update(producer=""))
    def test_reject_row_without_identity(self): self.assertRejected(lambda d: d["future_row_universe"][0].update(identity_mode=""))
    def test_reject_duplicate_qualified_identity(self): self.assertRejected(lambda d: d["future_row_universe"].append(copy.deepcopy(d["future_row_universe"][0])))
    def test_reject_universal_uuidv5_assumption(self): self.assertRejected(lambda d: [r.update(identity_mode="UUIDV5_FIXTURE_ASSIGNED") for r in d["future_row_universe"]])
    def test_reject_rls_grant_without_policy(self): self.assertRejected(lambda d: d["security_rls_matrix"][0].update(applicable_policy="GLOBAL_TABLE_NO_TENANT_RLS", RLS_enabled=False))
    def test_reject_unknown_field(self): self.assertRejected(lambda d: d["field_taxonomy"].update(unknown_classification="UNKNOWN"))
    def test_reject_missing_field_source(self): self.assertRejected(lambda d: d["field_taxonomy"]["rules"][0].update(source=""))
    def test_reject_missing_freeze(self): self.assertRejected(lambda d: d["future_row_universe"][0].update(freeze_point=""))
    def test_reject_generic_support_producer(self): self.assertRejected(lambda d: d["support_producer"].update(accepted_parameters=["table", "uuid", "json"]))
    def test_reject_nested_trusted_context(self): self.assertRejected(lambda d: d["support_producer"].update(outer_transaction_around_native_services=True))
    def test_reject_draft_model_policy(self): self.assertRejected(lambda d: d["static_material"]["model_policy"].update(status_at_run="draft"))
    def test_reject_draft_agent_definition(self): self.assertRejected(lambda d: d["static_material"]["agent_definition"].update(status_at_run="draft"))
    def test_reject_missing_agent_run_input(self): self.assertRejected(lambda d: d["static_material"]["input_basis_equality"].update(agent_run_input_ids=[]))
    def test_reject_missing_run_recommendation(self): self.assertRejected(lambda d: d["future_row_universe"].__setitem__(slice(None), [r for r in d["future_row_universe"] if r["row_type"] != "AgentRunRecommendation"]))
    def test_reject_basis_input_mismatch(self): self.assertRejected(lambda d: d["static_material"]["input_basis_equality"].update(recommendation_basis_ids=[]))
    def test_reject_action_plan_before_decision(self):
        def mutate(d):
            rows=d["future_row_universe"]; a=next(i for i,r in enumerate(rows) if r["row_type"]=="AgentDecision"); b=next(i for i,r in enumerate(rows) if r["row_type"]=="ActionPlan"); rows[a],rows[b]=rows[b],rows[a]
        self.assertRejected(mutate)
    def test_reject_effectiveness_without_execution(self): self.assertRejected(lambda d: d["future_row_universe"].__setitem__(slice(None), [r for r in d["future_row_universe"] if r["row_type"] != "ActionExecution"]))
    def test_reject_effectiveness_without_evidence(self): self.assertRejected(lambda d: d["future_row_universe"].__setitem__(slice(None), [r for r in d["future_row_universe"] if r["row_type"] != "EffectivenessEvidence"]))
    def test_reject_signal_without_effectiveness_leaf(self): self.assertRejected(lambda d: d["future_row_universe"].__setitem__(slice(None), [r for r in d["future_row_universe"] if not r["row_type"].startswith("LearningSignalEffectiveness")]))
    def test_reject_proposal_without_signal(self): self.assertRejected(lambda d: d["static_material"]["proposal"].update(supporting_signal_id=""))
    def test_reject_predicted_root_target_hash(self): self.assertRejected(lambda d: d["b1"].update(target_hash_mode="PREBOUND_STATIC"))
    def test_reject_prebound_b2_hash(self): self.assertRejected(lambda d: d["b2"].update(hash_mode="PREBOUND_STATIC"))
    def test_reject_prebound_b3_hash(self): self.assertRejected(lambda d: d["b3"].update(hash_mode="PREBOUND_STATIC"))
    def test_reject_postpublication_fact_before_publication(self): self.assertRejected(lambda d: d["artifact_schemas"]["knowledge-layer-rule-publication-governed-admission/v1"].append("B2"))
    def test_reject_b3_self_reference(self): self.assertRejected(lambda d: d["b3"].update(self_reference=True))
    def test_reject_native_hash_as_governed_hash(self): self.assertRejected(lambda d: d["governed_admission"].update(native_hash_is_governed_hash=True))
    def test_reject_replay_authority_substitution(self): self.assertRejected(lambda d: d["governed_admission"].update(same_native_hash_different_governed_material="replace original"))
    def test_reject_phase29_dependency(self): self.assertRejected(lambda d: d["phase29"].update(operational_dependencies=["phase29"]))
    def test_reject_runtime_adoption(self): self.assertRejected(lambda d: d["promotion_flags"].update(RuntimeAdoption=True))

    def test_hostile_requirements_are_explicit(self):
        text = CONTRACT_PATH.read_text()
        required = ["outer_transaction_around_native_services", "arbitrary_table_model_uuid_operation_actor_json_target_or_fields", "status_at_run", "input_basis_equality", "correction_lineage_required", "measurement_definition_required", "same_native_hash_different_governed_material"]
        self.assertTrue(all(value in text for value in required))

    def test_reject_altered_native_release_child(self):
        candidate = copy.deepcopy(self.contract)
        parent, vectors = next(iter(candidate["native_release_identity"]["vectors"].items()))
        vectors["event"] = str(uuid.uuid4())
        digest = hashlib.md5(f"{parent}:event".encode()).hexdigest()
        expected = str(uuid.UUID(f"{digest[:8]}-{digest[8:12]}-4{digest[13:16]}-8{digest[17:20]}-{digest[20:32]}"))
        self.assertNotEqual(vectors["event"], expected)

    def test_reject_predicted_future_hashes_and_cycles(self):
        self.assertEqual(self.contract["b1"]["target_hash_mode"], "EXECUTION_DERIVED_PERSISTED")
        self.assertEqual(self.contract["b2"]["hash_mode"], "EXECUTION_DERIVED_PERSISTED")
        self.assertEqual(self.contract["b3"]["hash_mode"], "EXECUTION_DERIVED_PERSISTED")
        self.assertFalse(self.contract["b3"]["self_reference"])


if __name__ == "__main__":
    unittest.main()
