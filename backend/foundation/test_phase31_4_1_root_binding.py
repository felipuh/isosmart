"""Offline B1 diagnostics, not an execution adapter or approved fixture.

The probe timestamps are test inputs. They are never attributed to the frozen
root, never used to search for its preimage, and never authorize an operation.
"""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
from unittest import TestCase

from .canonical import canonical_hash, canonical_json
from .learning_delta import canonical_delta_bytes


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_LIFECYCLE_SPEC_V1.json"
VECTOR_PATH = ROOT / "docs/governance/evidence/PHASE31_4_1_ROOT_BINDING_DIAGNOSTIC_VECTORS_V1.json"
FIELDS = (
    "id", "knowledge_layer_id", "lineage_id", "rule_key", "version",
    "previous_revision_id", "status", "logic_json", "evidence_expectation",
    "source_reference", "certifiability_classification", "published_at", "created_at",
)


def validate_probe(row, expected_hash):
    """Test-only strict profile over already-rendered JSON, not PostgreSQL emulation."""
    if set(row) != set(FIELDS):
        raise ValueError("complete 13-field row required")
    for key in ("created_at", "published_at"):
        text = row[key]
        if not isinstance(text, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00", text
        ):
            raise ValueError("exact probe UTC timestamp text required")
        datetime.fromisoformat(text)
    if row["status"] != "published" or row["previous_revision_id"] is not None:
        raise ValueError("published root required")
    if row["lineage_id"] != row["id"]:
        raise ValueError("root lineage identity required")
    if datetime.fromisoformat(row["created_at"]) > datetime.fromisoformat(row["published_at"]):
        raise ValueError("probe causality required")
    if canonical_hash(row) != expected_hash:
        raise ValueError("full-row hash mismatch")


def validate_probe_bindings(row, delta, authorization):
    """Only hash links; not the promoted authority/governance/SQL validator."""
    validate_probe(row, delta["target_hash"])
    delta_hash = hashlib.sha256(canonical_delta_bytes(delta)).hexdigest()
    if authorization["delta_hash"] != delta_hash or authorization["target_hash"] != delta["target_hash"]:
        raise ValueError("stale authorization binding")


class RootBindingDiagnosticTests(TestCase):
    def setUp(self):
        self.spec = json.loads(SPEC_PATH.read_text())
        self.vector = json.loads(VECTOR_PATH.read_text())
        self.probe = self.vector["probe"]
        self.row = deepcopy(self.probe["row"])

    def test_frozen_input_still_fails_completeness(self):
        self.assertEqual(self.vector["status"], "DIAGNOSTIC_ONLY_NOT_AUTHORIZED")
        self.assertIsNone(self.vector["corrected_target_hash"])
        self.assertFalse(self.vector["database_creation_authorized"])
        with self.assertRaises(ValueError):
            validate_probe(self.vector["known_root_material"], self.spec["lineage"]["root"]["foundation_0021_target_hash"])

    def test_exact_probe_bytes_and_hash(self):
        validate_probe(self.row, self.probe["target_hash"])
        self.assertEqual(canonical_json(self.row), self.probe["canonical_envelope"])
        self.assertEqual(hashlib.sha256(self.probe["canonical_envelope"].encode()).hexdigest(), self.probe["target_hash"])

    def test_missing_created_at(self):
        del self.row["created_at"]
        with self.assertRaises(ValueError):
            validate_probe(self.row, self.probe["target_hash"])

    def test_missing_published_at(self):
        del self.row["published_at"]
        with self.assertRaises(ValueError):
            validate_probe(self.row, self.probe["target_hash"])

    def test_changed_created_at(self):
        self.row["created_at"] = self.vector["timestamp_tamper"]
        self.assertNotEqual(canonical_hash(self.row), self.probe["target_hash"])
        with self.assertRaises(ValueError):
            validate_probe(self.row, self.probe["target_hash"])

    def test_changed_published_at(self):
        self.row["published_at"] = self.vector["timestamp_tamper"]
        self.assertNotEqual(canonical_hash(self.row), self.probe["target_hash"])
        with self.assertRaises(ValueError):
            validate_probe(self.row, self.probe["target_hash"])

    def test_equivalent_offset_text_is_not_same_json(self):
        original = self.row["created_at"]
        self.row["created_at"] = self.vector["offset_equivalent"]
        self.assertEqual(datetime.fromisoformat(original), datetime.fromisoformat(self.row["created_at"]))
        self.assertNotEqual(canonical_hash(self.row), self.probe["target_hash"])
        with self.assertRaises(ValueError):
            validate_probe(self.row, self.probe["target_hash"])

    def test_datetime_normalization_is_not_raw_json_string_hashing(self):
        for field in ("created_at", "published_at"):
            self.row[field] = datetime.fromisoformat(self.row[field])
        self.assertNotEqual(canonical_hash(self.row), self.probe["target_hash"])
        self.assertIn("Z", canonical_json(self.row))

    def test_stale_old_target_hash_fails_probe(self):
        with self.assertRaises(ValueError):
            validate_probe(self.row, self.spec["lineage"]["root"]["foundation_0021_target_hash"])

    def test_stale_old_delta_fails_probe(self):
        with self.assertRaises(ValueError):
            validate_probe_bindings(self.row, self.spec["application"]["canonical_delta"]["material"], self.probe["authorization_binding"])

    def test_stale_authorization_fails_probe_delta(self):
        stale = dict(self.probe["authorization_binding"], delta_hash=self.spec["application"]["canonical_delta"]["delta_hash"])
        with self.assertRaises(ValueError):
            validate_probe_bindings(self.row, self.probe["delta"], stale)

    def test_selected_material_is_not_full_row(self):
        with self.assertRaises(ValueError):
            validate_probe(self.row, self.spec["lineage"]["root"]["full_material_hash"])

    def test_probe_delta_and_binding(self):
        validate_probe_bindings(self.row, self.probe["delta"], self.probe["authorization_binding"])
        self.assertEqual(canonical_delta_bytes(self.probe["delta"]).decode(), self.probe["delta_canonical_bytes_utf8"])
        self.assertEqual(hashlib.sha256(canonical_delta_bytes(self.probe["delta"])).hexdigest(), self.probe["delta_hash"])

    def test_proposal_hash_uses_promoted_helper(self):
        from .learning_proposal_governance import proposal_material_hash
        self.assertEqual(proposal_material_hash(SimpleNamespace(**self.probe["proposal_helper_input"])), self.probe["proposal_material_hash"])

    def test_downstream_hash_dependencies(self):
        for key in ("decision_identity", "authorization_idempotency"):
            self.assertEqual(canonical_hash(self.probe[key + "_material"]), self.probe[key + "_hash"])
        self.assertEqual(hashlib.sha256(self.probe["application_identity_text"].encode()).hexdigest(), self.probe["application_identity"])
        self.assertEqual(hashlib.sha256(self.probe["claim_material_text"].encode()).hexdigest(), self.probe["claim_material_hash"])

    def test_null_timestamp_and_extra_field_fail(self):
        for key in ("created_at", "published_at"):
            row = dict(self.row, **{key: None})
            with self.assertRaises(ValueError):
                validate_probe(row, self.probe["target_hash"])
        with self.assertRaises(ValueError):
            validate_probe(dict(self.row, unexpected=True), self.probe["target_hash"])

    def test_evidence_hash_preimages_are_not_supplied(self):
        for key in ("compatibility_evidence", "release_evidence"):
            self.assertEqual(set(self.spec["activation"][key]), {"id", "hash"})

    def test_frozen_schema_remains_13_columns(self):
        source = (ROOT / "backend/foundation/migrations/0009_knowledge_layer_foundation.py").read_text()
        ddl = source.split("CREATE TABLE normative.knowledge_layer_rule (", 1)[1].split("CONSTRAINT", 1)[0]
        columns = re.findall(r"^        (\w+) \w", ddl, flags=re.M)
        self.assertEqual(tuple(columns), FIELDS)

    def test_old_delta_bytes_are_intact(self):
        delta = self.spec["application"]["canonical_delta"]
        self.assertEqual(hashlib.sha256(canonical_delta_bytes(delta["material"])).hexdigest(), delta["delta_hash"])

