"""Offline Retry5 manifest integrity and representative tamper matrix."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from foundation.phase31_4_operational_manifest import (
    MANIFEST, ManifestVerificationError, verify_operational_manifest,
)


REPRESENTATIVES = (
    "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json",
    "docs/governance/evidence/PHASE31_4_5B_V2_4_OPERATIONAL_CORRECTION_AUTHORIZATION_V1.json",
    "docs/governance/evidence/PHASE31_4_5B_V2_4_AUTHORIZATION_PROMOTION_RECORD_V1.json",
    "docs/adr/0017-ephemeral-exact-id-governed-application-adapter.md",
    "docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V2.md",
    "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json",
    "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json",
    "backend/foundation/phase31_4_v2_4_support_producer.py",
    "backend/foundation/governed_learning_application.py",
    "backend/foundation/phase31_4_v2_4_execution_wiring.py",
    "backend/foundation/phase31_4_v2_4_security_installer.py",
    "backend/foundation/phase31_4_postgres18_environment.py",
    "backend/foundation/postgres_phase31_4_clean_retry_3_harness.py",
    "backend/foundation/phase31_4_operational_manifest.py",
    "backend/foundation/migrations/0001_foundation_tenant_projection.py",
    "backend/foundation/fixtures/adminapps_projection_events.json",
    "backend/backend/settings.py",
)


class Retry5ManifestTests(unittest.TestCase):
    def test_authoritative_manifest_and_external_hash(self):
        expected = sha256(MANIFEST.read_bytes()).hexdigest()
        document = verify_operational_manifest(expected)
        self.assertEqual(document["counts"]["migrations"], 23)
        self.assertEqual(document["counts"]["phases"], 33)
        self.assertEqual(document["counts"]["named_operations"], 29)

    def test_representative_17_member_tamper_matrix_fails_closed(self):
        original = json.loads(MANIFEST.read_text(encoding="utf-8"))
        indexed = {member["path"]: member for member in original["members"]}
        self.assertTrue(set(REPRESENTATIVES) <= set(indexed))
        with tempfile.TemporaryDirectory() as directory:
            for index, representative in enumerate(REPRESENTATIVES):
                tampered = json.loads(json.dumps(original))
                by_path = {member["path"]: member for member in tampered["members"]}
                by_path[representative]["sha256"] = "0" * 64
                candidate = Path(directory) / f"tampered-{index}.json"
                candidate.write_text(json.dumps(tampered, sort_keys=True), encoding="utf-8")
                expected = sha256(candidate.read_bytes()).hexdigest()
                with self.assertRaises(ManifestVerificationError, msg=representative):
                    verify_operational_manifest(expected, candidate)

    def test_wrong_external_hash_fails_before_member_inspection(self):
        with self.assertRaises(ManifestVerificationError):
            verify_operational_manifest("0" * 64)

