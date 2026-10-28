"""Anti-regression tests for historical and current integrity generations."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from .phase31_4_integrity_generations import (
    BASELINE_ADOPTION_MANIFEST,
    CURRENT_MANIFEST,
    CURRENT_V2_MANIFEST,
    CURRENT_V3_MANIFEST,
    CURRENT_V12_MANIFEST,
    CURRENT_V12_SHA256,
    CURRENT_V7_MANIFEST,
    CURRENT_V7_SHA256,
    HISTORICAL_MANIFEST,
    IntegrityGenerationError,
    ROOT,
    V24_CONTRACT,
    V24_CONTRACT_SHA256,
    file_sha256,
    select_v25_current_baseline,
    verify_v24_historical_integrity,
    verify_v25_v1_historical_record,
    verify_v25_v2_historical_record,
    verify_v25_v4_historical_record,
    verify_v25_current_integrity,
    verify_v25_v5_current_integrity,
    verify_v25_v6_current_integrity,
    verify_v25_v7_current_integrity,
    verify_v25_v12_current_integrity,
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
    def test_v12_is_immutable_and_unadopted_source_drift_fails_closed(self):
        self.assertEqual(file_sha256(CURRENT_V12_MANIFEST), CURRENT_V12_SHA256)
        with self.assertRaisesRegex(IntegrityGenerationError, "V12 protected source drift"):
            select_v25_current_baseline(ROOT)

    def _install_v13_fixture(
        self,
        root: Path,
        *,
        adopt: bool,
        include_new_migration: bool = False,
        declare_new_migration: bool = True,
    ) -> Path:
        predecessor = json.loads(CURRENT_V12_MANIFEST.read_text(encoding="utf-8"))
        predecessor_path = root / CURRENT_V12_MANIFEST.relative_to(ROOT)
        predecessor_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CURRENT_V12_MANIFEST, predecessor_path)
        previous_path = root / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V11.json"
        previous_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V11.json", previous_path)
        approval = root / "approval.md"
        approval.write_text("explicit offline test fixture\n", encoding="utf-8")

        sources = []
        changed_sources = []
        for old_entry in predecessor["sources"]:
            relative = old_entry["path"]
            source = ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            entry = deepcopy(old_entry)
            entry["sha256"] = file_sha256(target)
            entry["approval_evidence"] = ["approval.md"]
            for evidence in old_entry.get("approval_evidence", ()):
                evidence_target = root / evidence
                evidence_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / evidence, evidence_target)
            if entry["sha256"] != old_entry["sha256"]:
                entry["predecessor_sha256"] = old_entry["sha256"]
                changed_sources.append({"path": relative, "predecessor_sha256": old_entry["sha256"]})
            sources.append(entry)
        migrations = dict(predecessor["migration_file_sha256"])
        new_migrations = []
        if include_new_migration:
            for relative in (
                "backend/foundation/migrations/0025_iso9000_foundation_gate.py",
                "backend/foundation/migrations/0026_question_bank_versioning.py",
                "backend/foundation/migrations/0027_onboarding_workflow.py",
                "backend/foundation/migrations/0028_capability_activation.py",
            ):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
                migrations[relative] = file_sha256(target)
                if declare_new_migration:
                    new_migrations.append({"path": relative, "sha256": migrations[relative]})

        for relative in predecessor["migration_file_sha256"]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

        generation = "V2.5_CURRENT_SOURCE_SUCCESSOR_V13"
        manifest_relative = "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V13.json"
        manifest_path = root / manifest_relative
        manifest = {
            "schema": "phase31.4-v2.5-current-source-integrity/v13",
            "generation": generation,
            "generation_id": "PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V13",
            "governance_predecessor": "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V12.json",
            "governance_predecessor_sha256": CURRENT_V12_SHA256,
            "protected_source_count": len(sources),
            "predecessor_protected_source_count": len(predecessor["sources"]),
            "sources": sources,
            "changed_sources": changed_sources,
            "new_sources": [],
            "removed_sources": [],
            "missing_sources": [],
            "unexpected_sources": [],
            "migration_file_sha256": migrations,
            "new_migrations": new_migrations,
            "provenance_continuity": predecessor["provenance_continuity"],
            "provenance_discontinuity_status": predecessor["provenance_discontinuity_status"],
            "provenance_discontinuity_artifact": predecessor["provenance_discontinuity_artifact"],
            "retry_20_executed": False,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if adopt:
            adoption_path = root / BASELINE_ADOPTION_MANIFEST.relative_to(ROOT)
            adoption_path.parent.mkdir(parents=True, exist_ok=True)
            adoption = {
                "schema": "phase31.4-v2.5-baseline-adoption/v1",
                "decision": "ADOPT_BASELINE",
                "decision_id": "OFFLINE-TEST-V13-ADOPTION",
                "adopted_by": "offline-test-fixture",
                "adopted_at": "2026-09-30T12:00:00Z",
                "rationale": "Verify explicit selection behavior offline.",
                "manifest_path": manifest_relative,
                "manifest_sha256": file_sha256(manifest_path),
                "generation": generation,
            }
            adoption_path.write_text(json.dumps(adoption, indent=2) + "\n", encoding="utf-8")
        return manifest_path

    def test_v13_requires_explicit_adoption_and_validates_producer_hash(self):
        self.assertEqual(
            file_sha256(ROOT / "docs/governance/tools/phase31_4_v2_5_operational_actions.py"),
            "8f09299e98c5581b2a2a08f5731b80b583535a6b20cb5cd09670a4a94d6d2e1a",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = self._install_v13_fixture(root, adopt=True)
            selected_path, selected = select_v25_current_baseline(root)
            self.assertEqual(selected_path, manifest_path)
            self.assertEqual(selected["generation"], "V2.5_CURRENT_SOURCE_SUCCESSOR_V13")

    def test_successor_manifest_without_adoption_is_never_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._install_v13_fixture(root, adopt=False)
            with self.assertRaisesRegex(IntegrityGenerationError, "V12 protected source drift"):
                select_v25_current_baseline(root)

    def test_successor_accepts_declared_new_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = self._install_v13_fixture(
                root,
                adopt=True,
                include_new_migration=True,
            )
            selected_path, selected = select_v25_current_baseline(root)
            self.assertEqual(selected_path, manifest_path)
            self.assertIn(
                "backend/foundation/migrations/0025_iso9000_foundation_gate.py",
                selected["migration_file_sha256"],
            )

    def test_successor_rejects_undeclared_new_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._install_v13_fixture(
                root,
                adopt=True,
                include_new_migration=True,
                declare_new_migration=False,
            )
            with self.assertRaisesRegex(
                IntegrityGenerationError,
                "successor migration additions are not explicitly declared",
            ):
                select_v25_current_baseline(root)

    def test_successor_rejects_duplicate_migration_declaration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = self._install_v13_fixture(
                root,
                adopt=True,
                include_new_migration=True,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["new_migrations"].append(dict(manifest["new_migrations"][0]))
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            adoption_path = root / BASELINE_ADOPTION_MANIFEST.relative_to(ROOT)
            adoption = json.loads(adoption_path.read_text(encoding="utf-8"))
            adoption["manifest_sha256"] = file_sha256(manifest_path)
            adoption_path.write_text(json.dumps(adoption), encoding="utf-8")
            with self.assertRaisesRegex(
                IntegrityGenerationError,
                "duplicate successor migration declaration",
            ):
                select_v25_current_baseline(root)

    def test_adoption_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._install_v13_fixture(root, adopt=True)
            adoption_path = root / BASELINE_ADOPTION_MANIFEST.relative_to(ROOT)
            adoption = json.loads(adoption_path.read_text(encoding="utf-8"))
            adoption["manifest_sha256"] = "0" * 64
            adoption_path.write_text(json.dumps(adoption), encoding="utf-8")
            with self.assertRaisesRegex(IntegrityGenerationError, "adopted baseline manifest digest mismatch"):
                select_v25_current_baseline(root)

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
        manifest = json.loads(CURRENT_V12_MANIFEST.read_text(encoding="utf-8"))
        changed = deepcopy(manifest)
        changed["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(IntegrityGenerationError, "protected source drift"):
            verify_v25_v12_current_integrity(document=changed)

    def test_historical_and_current_manifests_are_not_substitutable(self):
        historical = json.loads(HISTORICAL_MANIFEST.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(IntegrityGenerationError, "current manifest schema mismatch"):
            verify_v25_current_integrity(manifest=historical)

    def test_discontinuity_artifact_is_explicit(self):
        current = verify_v25_v12_current_integrity(
            ROOT,
            json.loads(CURRENT_V12_MANIFEST.read_text(encoding="utf-8")),
            validate_sources=False,
        )
        self.assertEqual(current["provenance_discontinuity_artifact"], "docs/governance/evidence/PHASE31_4_V2_5_RUNTIME_PROVENANCE_DISCONTINUITY_V1.json")
        self.assertEqual(current["provenance_discontinuity_status"], "PROVENANCE_DISCONTINUITY")
