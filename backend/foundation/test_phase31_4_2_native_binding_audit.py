"""Offline source/contract counterexamples; never an execution admission gate.

The retained vectors use historical material solely to expose the difference
between native 0022 operation hashes and the broader successor obligations.
No SQL, lifecycle service, authority resolver or database is executed.
"""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/governance/evidence/PHASE31_4_2_NATIVE_BINDING_AUDIT_V1.json"
MIGRATION = "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py"
SPEC = "docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_LIFECYCLE_SPEC_V1.json"


def forward_sql():
    tree = ast.parse((ROOT / MIGRATION).read_text())
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "FORWARD_SQL"
                        for t in node.targets))


def sql_function(name):
    source = forward_sql()
    start = source.index("CREATE FUNCTION normative." + name + "(")
    end = source.index("END $fn$;", start) + len("END $fn$;")
    return source[start:end]


def native_preimage(operation, material):
    """Exact 0022 text concatenation for these non-null offline input vectors."""
    if operation == "publication":
        fields = [material["rule_id"], material["expected_hash"], material["reason"]]
    elif operation == "activation":
        fields = [material["publication_id"], material["expected_hash"],
                  material["predecessor_id"] or "ROOT", material["compatibility_hash"],
                  material["reason"]]
    else:
        raise ValueError("only Publication and Activation source probes allowed")
    return ":".join(fields)


def native_digest(operation, material):
    return hashlib.sha256(native_preimage(operation, material).encode("utf-8")).hexdigest()


class NativeBindingAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text())

    def test_source_and_predecessor_bindings_are_unchanged(self):
        for path, digest in self.evidence["source_file_hashes"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)

    def test_native_formulas_are_exact_source_expressions(self):
        for operation, item in self.evidence["operations"].items():
            body = sql_function(item["sql_function"])
            expression = re.search(r"op_hash:=(.*?);", body).group(1)
            self.assertEqual(expression, item["sql_hash_expression"])
            expected = ({"p_rule_id", "p_expected_hash", "p_reason"}
                        if operation == "publication" else
                        {"p_publication_id", "p_expected_hash", "p_expected_predecessor",
                         "p_compatibility_hash", "p_reason"})
            self.assertEqual(set(re.findall(r"\bp_[a-z_]+\b", expression)), expected)

    def test_retained_hashes_have_exact_preimages(self):
        for operation, item in self.evidence["operations"].items():
            self.assertEqual(native_preimage(operation, item["probe_input"]), item["preimage_utf8"])
            self.assertEqual(native_digest(operation, item["probe_input"]), item["sha256"])
            self.assertFalse(item["execution_authority"])
        known = set(self.evidence["digest_provenance"])
        found = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])",
                               json.dumps(self.evidence, sort_keys=True)))
        self.assertFalse(found - known)

    def test_actor_authority_and_caller_key_are_not_native_material_hash_inputs(self):
        # This proves a limited hash projection, not a successful SQL replay.
        for operation, item in self.evidence["operations"].items():
            for field in ("actor_external_id", "authority_decision_reference",
                          "policy_id", "idempotency_key_hash", "trace_id"):
                with self.subTest(operation=operation, field=field):
                    changed = deepcopy(item["probe_input"])
                    changed[field] = "OFFLINE_CHANGED_INPUT_NOT_AN_AUTHORITY"
                    self.assertNotEqual(changed, item["probe_input"])
                    self.assertEqual(native_digest(operation, changed), item["sha256"])

    def test_release_and_closure_cannot_be_claimed_as_native_hash_bindings(self):
        for operation, item in self.evidence["operations"].items():
            changed = dict(item["probe_input"], release_evidence_hash="OFFLINE_CHANGED_RELEASE",
                           publication_closure_digest="OFFLINE_CHANGED_CLOSURE")
            self.assertEqual(native_digest(operation, changed), item["sha256"])
            params = sql_function(item["sql_function"]).split("RETURNS", 1)[0]
            self.assertNotIn("p_release", params)
            self.assertNotIn("p_closure", params)

    def test_compatibility_is_an_activation_input_only(self):
        item = self.evidence["operations"]["activation"]
        changed = dict(item["probe_input"], compatibility_hash=hashlib.sha256(b"offline mutation").hexdigest())
        self.assertNotEqual(native_digest("activation", changed), item["sha256"])
        publication = sql_function(self.evidence["operations"]["publication"]["sql_function"])
        self.assertNotIn("compatibility", publication)
        activation = sql_function(item["sql_function"])
        self.assertIn("p_expected_predecessor,p_compatibility_hash,p_actor", activation)

    def test_replay_checks_cannot_be_substituted_for_full_successor_comparison(self):
        for item in self.evidence["operations"].values():
            body = sql_function(item["sql_function"])
            branch = body.split("IF prior.id IS NOT NULL THEN", 1)[1].split(
                "existing claim cannot be stolen", 1)[0]
            self.assertIn("prior.operation_material_hash=op_hash", branch)
            self.assertNotIn("prior.authority_decision_reference", branch)
            self.assertNotIn("prior.actor_external_id", branch)
            self.assertNotIn("prior.idempotency_key_hash", branch)
            self.assertTrue(item["outer_binding_required"])

    def test_predecessor_publication_evidence_requirement_needs_versioned_replacement(self):
        spec = json.loads((ROOT / SPEC).read_text())
        required = spec["canonical_operation_contracts"]["publication"]["required_fields"]
        self.assertIn("compatibility_release_evidence_hashes", required)
        self.assertEqual(self.evidence["publication_dependency_cycle"], [
            "publication_admission", "postpublication_evidence",
            "persisted_publication", "publication_admission",
        ])

    def test_diagnostic_cannot_promote_or_broaden_adr0017(self):
        self.assertEqual(self.evidence["status"], "DIAGNOSTIC_ONLY_NOT_AUTHORIZED")
        for field in ("successor_package_complete", "database_creation_authorized",
                      "lifecycle_execution_authorized", "sql_behavior_verified"):
            self.assertIs(self.evidence[field], False)
        self.assertEqual(self.evidence["adr0017_exception"], "APPLICATION_OUTPUT_IDENTITY_ONLY")
        self.assertEqual(self.evidence["remaining_blockers"], ["B1", "B2", "B3", "B4"])


if __name__ == "__main__":
    unittest.main()
