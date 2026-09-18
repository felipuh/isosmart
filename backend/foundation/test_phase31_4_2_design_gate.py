"""Offline diagnostic checks, not an operational V2 fixture or SQL acceptance test.

These probes check necessary conditions only. Passing them cannot authorize a
successor package: complete field bindings and a governed producer are separate
requirements. No lifecycle command, database, or resolver is invoked.
"""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest
from uuid import UUID, uuid5


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/governance/evidence/PHASE31_4_2_SUCCESSOR_DESIGN_DIAGNOSTIC_V1.json"
MODES = {
    "PREBOUND_STATIC", "EXECUTION_DERIVED_PERSISTED",
    "EXECUTION_DERIVED_EXTERNAL_AUTHORITY", "OUTPUT_ID_MAPPED_BY_ADR0017",
}
DISPOSITIONS = {
    "RETAIN_FULL_CANONICAL_MATERIAL",
    "EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE",
}
HISTORICAL_ONLY = {
    "e97576de-d4ef-520d-8592-d376ed401221",
    "12d811ab-c3b4-4615-8972-75008a36e327",
}


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate_descriptor(item):
    mode = item.get("value_mode")
    if mode not in MODES:
        raise ValueError("unclassified value")
    for field in ("derivation_contract", "source", "canonicalization", "policy",
                  "provenance", "consumers"):
        if not item.get(field):
            raise ValueError(f"missing {field}")
    start, end = item.get("available_after"), item.get("required_before")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= 10:
        raise ValueError("invalid freeze points")
    if item.get("disposition") not in DISPOSITIONS:
        raise ValueError("missing disposition")
    if mode != "PREBOUND_STATIC" and ("value" in item or "hash" in item):
        raise ValueError("derived value must not be numerically prebound")
    if mode == "PREBOUND_STATIC":
        if "preimage" not in item or "hash" not in item:
            raise ValueError("static hash needs its exact preimage")
        if hashlib.sha256(canonical_bytes(item["preimage"])).hexdigest() != item["hash"]:
            raise ValueError("static preimage mismatch")
    if mode == "EXECUTION_DERIVED_EXTERNAL_AUTHORITY":
        if item.get("approved_outcome") is not None:
            raise ValueError("future authority outcome is not static approval")
        if item["disposition"] != "EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE":
            raise ValueError("external authority provenance required")


def validate_order(dependencies, sequence):
    if len(sequence) != len(set(sequence)) or set(sequence) != set(dependencies):
        raise ValueError("sequence must cover each node exactly once")
    done = set()
    for node in sequence:
        if not set(dependencies[node]).issubset(done):
            raise ValueError(f"unsatisfied prerequisite for {node}")
        done.add(node)


def validate_operational_members(members, required):
    """Necessary lower-bound check; not a complete retention closure verifier."""
    names = {member["name"] for member in members}
    if len(names) != len(members) or not set(required).issubset(names):
        raise ValueError("missing or duplicated mandatory support member")
    for member in members:
        if member.get("id") in HISTORICAL_ONLY:
            raise ValueError("Phase 29 cannot be an operational dependency")
        if member["name"] == "RuntimeAdoption" or member.get("operation") == "RUNTIME_ADOPTION":
            raise ValueError("RuntimeAdoption prohibited")
        if member.get("disposition") not in DISPOSITIONS:
            raise ValueError("unclassified closure member")


def function_ast(path, class_name, method):
    tree = ast.parse((ROOT / path).read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method)


class Phase3142DesignDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text())

    def descriptor(self):
        return deepcopy(self.evidence["design_candidates"]["root_target"]["descriptor"])

    def test_diagnostic_does_not_authorize_successor_or_execution(self):
        self.assertEqual(self.evidence["status"], "DIAGNOSTIC_ONLY_NOT_AUTHORIZED")
        self.assertFalse(self.evidence["successor_package_complete"])
        self.assertFalse(self.evidence["database_creation_authorized"])
        self.assertTrue(self.evidence["blocking_findings"])

    def test_typed_root_descriptor_has_no_predicted_hash(self):
        validate_descriptor(self.descriptor())

    def test_every_candidate_descriptor_has_a_known_mode_and_freeze(self):
        for candidate in self.evidence["design_candidates"].values():
            validate_descriptor(candidate["descriptor"])

    def test_unknown_mode_is_rejected(self):
        item = self.descriptor()
        item["value_mode"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            validate_descriptor(item)

    def test_missing_derivation_or_freeze_is_rejected(self):
        for field in ("derivation_contract", "available_after", "required_before"):
            with self.subTest(field=field):
                item = self.descriptor()
                del item[field]
                with self.assertRaises(ValueError):
                    validate_descriptor(item)

    def test_fixed_live_hash_and_placeholders_are_rejected(self):
        for value in ("0" * 64, "TBD", None, "arbitrary", "a" * 64):
            with self.subTest(value=value):
                item = self.descriptor()
                item["hash"] = value
                with self.assertRaises(ValueError):
                    validate_descriptor(item)

    def test_static_hash_requires_reproducible_preimage(self):
        item = self.descriptor()
        item.update(value_mode="PREBOUND_STATIC", hash="a" * 64)
        with self.assertRaises(ValueError):
            validate_descriptor(item)
        item["preimage"] = {"purpose": "OFFLINE_PROBE_ONLY"}
        item["hash"] = hashlib.sha256(canonical_bytes(item["preimage"])).hexdigest()
        validate_descriptor(item)
        item["preimage"]["purpose"] = "tampered"
        with self.assertRaises(ValueError):
            validate_descriptor(item)

    def test_future_authority_cannot_be_static_approval(self):
        item = self.descriptor()
        item.update(value_mode="EXECUTION_DERIVED_EXTERNAL_AUTHORITY",
                    disposition="EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE")
        validate_descriptor(item)
        item["approved_outcome"] = True
        with self.assertRaises(ValueError):
            validate_descriptor(item)

    def test_superseded_hashes_are_historical_non_executable_references(self):
        for item in self.evidence["superseded_expectations"]:
            self.assertEqual(item["classification"], "SUPERSEDED_PREEXECUTION_EXPECTATION — NEVER EXECUTED")
            self.assertFalse(item["execution_authority"])
        self.assertEqual({item["blocker"] for item in self.evidence["superseded_expectations"]}, {"B1", "B2", "B3"})

    def test_required_freeze_order(self):
        validate_order(self.evidence["necessary_dependencies"], self.evidence["candidate_sequence"])

    def test_early_proposal_delta_authorization_or_activation_is_rejected(self):
        for node in ("proposal_delta", "review", "decision", "authorization", "activation"):
            with self.subTest(node=node):
                sequence = list(self.evidence["candidate_sequence"])
                sequence.remove(node)
                sequence.insert(0, node)
                with self.assertRaises(ValueError):
                    validate_order(self.evidence["necessary_dependencies"], sequence)

    def test_postpublication_evidence_cannot_be_publication_input(self):
        dependencies = deepcopy(self.evidence["necessary_dependencies"])
        dependencies["publication"].append("compatibility_release")
        with self.assertRaises(ValueError):
            validate_order(dependencies, self.evidence["candidate_sequence"])

    def test_missing_signal_or_effectiveness_prerequisite_is_rejected(self):
        dependencies = self.evidence["necessary_dependencies"]
        self.assertIn("signal", dependencies["proposal_delta"])
        self.assertIn("effectiveness", dependencies["signal"])
        for node in ("signal", "effectiveness"):
            sequence = [n for n in self.evidence["candidate_sequence"] if n != node]
            with self.assertRaises(ValueError):
                validate_order(dependencies, sequence)

    def test_upstream_qms_graph_cannot_be_reduced_to_check_and_signal(self):
        required = self.evidence["b4_required_member_types"]
        for name in ("ActionExecution", "ActionExecutionReceipt", "ActionPlan",
                     "ExecutionAuthorization", "AgentDecision", "Recommendation",
                     "OpportunityBefore", "OpportunityDeferred", "EffectivenessEvidence",
                     "Evidence", "LearningSignalEffectiveness", "LearningProposalSignal"):
            self.assertIn(name, required)
        with self.assertRaises(ValueError):
            validate_operational_members([], required)

    def test_model_fk_lower_bound_reaches_agent_execution_provenance(self):
        from foundation import models

        observed = self.evidence["nonnull_model_fk_lower_bound"]
        pending = [getattr(models, name) for name in observed["roots"]]
        visited, edges = set(), []
        while pending:
            model = pending.pop()
            if model.__name__ in visited:
                continue
            visited.add(model.__name__)
            for field in model._meta.concrete_fields:
                if field.is_relation and not field.null:
                    target = field.remote_field.model
                    edges.append({"source": model.__name__, "column": field.column,
                                  "target": target.__name__, "target_column": field.target_field.column,
                                  "table": model._meta.db_table.replace('"', '')})
                    pending.append(target)
        self.assertEqual(sorted(visited), observed["classes"])
        self.assertEqual(sorted(edges, key=lambda e: (e["source"], e["column"])), observed["edges"])
        self.assertTrue({"AgentRun", "AgentDefinition", "ModelPolicy", "ActionPlanDryRun"}.issubset(visited))
        self.assertFalse(observed["complete_semantic_closure"])

    def test_each_missing_support_member_fails_lower_bound(self):
        required = self.evidence["b4_required_member_types"]
        members = [{"name": name, "disposition": "RETAIN_FULL_CANONICAL_MATERIAL"} for name in required]
        validate_operational_members(members, required)
        for name in required:
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_operational_members([m for m in members if m["name"] != name], required)

    def test_missing_disposition_historical_dependency_and_adoption_are_rejected(self):
        for member in ({"name": "Evidence"},
                       {"name": "Evidence", "id": next(iter(HISTORICAL_ONLY)), "disposition": "RETAIN_FULL_CANONICAL_MATERIAL"},
                       {"name": "RuntimeAdoption", "disposition": "RETAIN_FULL_CANONICAL_MATERIAL"}):
            with self.subTest(member=member), self.assertRaises(ValueError):
                validate_operational_members([member], [])

    def test_deterministic_candidate_ids_are_unique_and_reproducible(self):
        inventory = self.evidence["candidate_support_ids"]
        namespace = UUID(self.evidence["namespace_uuid"])
        self.assertEqual(len(inventory), len(set(inventory.values())))
        for label, value in inventory.items():
            self.assertEqual(str(uuid5(namespace, label)), value)
        self.assertEqual(self.evidence["candidate_id_collisions"], [])

    def test_native_identity_allocation_gap_is_source_derived(self):
        for finding in self.evidence["native_identity_findings"]:
            node = function_ast(finding["path"], finding["class"], finding["method"])
            params = {a.arg for a in node.args.args + node.args.kwonlyargs}
            self.assertNotIn(finding["missing_output_parameter"], params)
            self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                                and n.func.id == "uuid4" for n in ast.walk(node)))

    def test_adr0017_mapping_has_exactly_the_seven_application_outputs(self):
        self.assertEqual(set(self.evidence["adr0017_output_mapping"]), {
            "candidate", "claim", "receipt", "event", "outbox", "curation_audit", "application_audit",
        })
        self.assertNotIn("LearningSignal", self.evidence["adr0017_output_mapping"])

    def test_every_literal_digest_has_declared_provenance(self):
        known = set(self.evidence["digest_provenance"])
        found = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", canonical_bytes(self.evidence).decode()))
        self.assertFalse(found - known)
        self.assertTrue(all(self.evidence["digest_provenance"].values()))

    def test_root_timestamp_fields_are_retained_and_postgresql_authoritative(self):
        root = self.evidence["design_candidates"]["root_target"]
        self.assertEqual(set(root["allowed_persisted_fresh_columns"]), {"created_at", "published_at"})
        self.assertEqual(len(root["frozen_non_time_material"]), 11)
        self.assertIn("to_jsonb(r)", root["read_sql"])
        self.assertFalse(root["python_datetime_substitution_allowed"])
        self.assertFalse(root["rfc8785_claim"])

    def test_evidence_is_neither_authority_nor_capability(self):
        for name in ("compatibility", "release"):
            item = self.evidence["design_candidates"][name]
            self.assertEqual(item["authority_effects"], [])
            self.assertFalse(item["schema_complete"])
            self.assertTrue(item["required_material_fields"])


if __name__ == "__main__":
    unittest.main()
