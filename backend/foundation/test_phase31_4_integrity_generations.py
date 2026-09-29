"""Anti-regression tests for historical and current integrity generations."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from .phase31_4_integrity_generations import (
    CURRENT_BASELINE_MANIFEST,
    CURRENT_MANIFEST,
    CURRENT_V2_MANIFEST,
    CURRENT_V3_MANIFEST,
    CURRENT_V7_MANIFEST,
    CURRENT_V7_SHA256,
    HISTORICAL_MANIFEST,
    IntegrityGenerationError,
    ROOT,
    V24_CONTRACT,
    V24_CONTRACT_SHA256,
    file_sha256,
    verify_v24_historical_integrity,
    verify_v25_v1_historical_record,
    verify_v25_v2_historical_record,
    verify_v25_v4_historical_record,
    verify_v25_current_integrity,
    verify_v25_v5_current_integrity,
    verify_v25_v6_current_integrity,
    verify_v25_v7_current_integrity,
)


class V24HistoricalIntegrityTests(unittest.TestCase):
    def test_approved_v25_migration_does_not_change_v24_history(self):
        self.assertTrue((ROOT / "backend/foundation/migrations/0024_adminapps_ingress_receipt.py").is_file())
        manifest = verify_v24_historical_integrity()
        self.assertEqual(len(manifest["migration_paths"]), 23)

    def test_changed_v24_frozen_artifact_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / V24_CONTRACT.relative_to(ROOT)
            manifest = root / HISTORICAL_MANIFEST.relative_to(ROOT)
            contract.parent.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            shutil.copyfile(V24_CONTRACT, contract)
            shutil.copyfile(HISTORICAL_MANIFEST, manifest)
            contract.write_bytes(contract.read_bytes() + b"\n")
            with self.assertRaisesRegex(IntegrityGenerationError, "contract SHA-256 drift"):
                verify_v24_historical_integrity(root)

    def test_exact_v24_contract_sha_remains_mandatory(self):
        self.assertEqual(file_sha256(V24_CONTRACT), V24_CONTRACT_SHA256)
        self.assertEqual(verify_v24_historical_integrity()["contract_sha256"], V24_CONTRACT_SHA256)


class V25CurrentOperationalIntegrityTests(unittest.TestCase):
    def test_current_manifest_passes(self):
        manifest = verify_v25_current_integrity()
        self.assertEqual(len(manifest["migration_file_sha256"]), 24)
        self.assertEqual(manifest["provenance_continuity"], False)
        self.assertIn("backend/foundation/phase31_4_v2_5_verifier_remediation.py", {item["path"] for item in manifest["sources"]})
        self.assertIn("backend/foundation/phase31_4_v2_5_precreation_integrity.py", {item["path"] for item in manifest["sources"]})
        self.assertIn("backend/integration/client.py", {item["path"] for item in manifest["sources"]})
        self.assertIn("backend/foundation/phase31_4_v2_5_live_executor.py", {item["path"] for item in manifest["sources"]})
        self.assertIn("backend/foundation/phase31_4_v2_5_operational_adapters.py", {item["path"] for item in manifest["sources"]})
        self.assertIn("docs/governance/tools/phase31_4_v2_5_operational_actions.py", {item["path"] for item in manifest["sources"]})
        self.assertIn("backend/foundation/operational_bearer_identity.py", {item["path"] for item in manifest["sources"]})
        self.assertEqual(manifest["generation"], "V2.5_CURRENT_SOURCE_SUCCESSOR_V12")
        self.assertEqual(len(manifest["sources"]), 30)

    def test_v7_remains_an_immutable_predecessor_record(self):
        self.assertEqual(file_sha256(CURRENT_V7_MANIFEST), CURRENT_V7_SHA256)
        predecessor = verify_v25_v7_current_integrity(validate_sources=False)
        self.assertEqual(predecessor["generation"], "V2.5_CURRENT_SOURCE_SUCCESSOR_V7")
        self.assertEqual(len(predecessor["sources"]), 28)

    def test_v6_remains_an_immutable_predecessor_record(self):
        predecessor = verify_v25_v6_current_integrity(validate_sources=False)
        self.assertEqual(predecessor["generation"], "V2.5_CURRENT_SOURCE_SUCCESSOR_V6")
        self.assertEqual(len(predecessor["sources"]), 26)

    def test_v4_remains_an_immutable_predecessor_record(self):
        predecessor = verify_v25_v4_historical_record(validate_sources=False)
        self.assertEqual(predecessor["generation"], "V2.5_CURRENT_SOURCE_SUCCESSOR_V4")
        self.assertEqual(len(predecessor["sources"]), 23)

    def test_v5_requires_both_runner_sources(self):
        manifest = verify_v25_v5_current_integrity(validate_sources=False)
        paths = {entry["path"] for entry in manifest["sources"]}
        self.assertIn("backend/foundation/phase31_4_v2_5_disposable_runner.py", paths)
        self.assertIn("docs/governance/tools/phase31_4_v2_5_disposable_runner.py", paths)

    def test_v1_remains_an_independent_historical_record(self):
        historical = verify_v25_v1_historical_record()
        self.assertEqual(historical["generation"], "V2.5_CURRENT")

    def test_v2_remains_the_immutable_governance_predecessor(self):
        predecessor = verify_v25_v2_historical_record()
        self.assertEqual(predecessor["generation"], "V2.5_CURRENT_SOURCE_BASELINE")
        self.assertEqual(len(predecessor["sources"]), 21)

    def test_unapproved_current_source_change_fails(self):
        manifest = json.loads(CURRENT_BASELINE_MANIFEST.read_text(encoding="utf-8"))
        changed = deepcopy(manifest)
        changed["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(IntegrityGenerationError, "protected source drift"):
            verify_v25_current_integrity(manifest=changed)

    def test_historical_and_current_manifests_are_not_substitutable(self):
        historical = json.loads(HISTORICAL_MANIFEST.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(IntegrityGenerationError, "current manifest schema mismatch"):
            verify_v25_current_integrity(manifest=historical)

    def test_discontinuity_artifact_is_explicit(self):
        current = verify_v25_current_integrity()
        self.assertEqual(current["provenance_discontinuity_artifact"], "docs/governance/evidence/PHASE31_4_V2_5_RUNTIME_PROVENANCE_DISCONTINUITY_V1.json")
        self.assertEqual(current["provenance_discontinuity_status"], "PROVENANCE_DISCONTINUITY")
