"""Focused fail-closed tests for PRECREATION_INTEGRITY."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from .phase31_4_integrity_generations import (
    BASELINE_ADOPTION_MANIFEST,
    CURRENT_V12_MANIFEST,
    CURRENT_V12_SHA256,
    ROOT,
    file_sha256,
)
from .phase31_4_v2_5_precreation_integrity import (
    PHASE_ID,
    verify_precreation_integrity,
)
from .phase31_4_v2_5_runtime import (
    NativeOperationRegistry,
    PhaseExecutionContext,
    V25ExecutionSession,
    build_v25_native_phase_registry,
    build_v25_runtime,
)


class PrecreationIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self._copy("docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_4_HISTORICAL_MIGRATION_MANIFEST_V1.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V2.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V3.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V4.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V5.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V6.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V7.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V8.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V9.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V10.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V11.json")
        self._copy("docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V12.json")
        for migration in sorted((ROOT / "backend/foundation/migrations").glob("[0-9][0-9][0-9][0-9]_*.py")):
            self._copy(migration.relative_to(ROOT).as_posix())
        approval = self.root / "approval.md"
        approval.write_text("approved test fixture\n", encoding="utf-8")
        predecessor = json.loads(CURRENT_V12_MANIFEST.read_text(encoding="utf-8"))
        sources = []
        changed_sources = []
        for old_source in predecessor["sources"]:
            self._copy(old_source["path"])
            source = dict(old_source)
            source["sha256"] = file_sha256(self.root / source["path"])
            source["approval_evidence"] = ["approval.md"]
            if source["sha256"] != old_source["sha256"]:
                source["predecessor_sha256"] = old_source["sha256"]
                changed_sources.append({
                    "path": source["path"],
                    "predecessor_sha256": old_source["sha256"],
                })
            sources.append(source)
        migration_hashes = dict(predecessor["migration_file_sha256"])
        new_migrations = []
        for migration in sorted((ROOT / "backend/foundation/migrations").glob("[0-9][0-9][0-9][0-9]_*.py")):
            relative = migration.relative_to(ROOT).as_posix()
            if int(migration.name[:4]) <= 24:
                continue
            migration_hashes[relative] = file_sha256(self.root / relative)
            new_migrations.append({"path": relative, "sha256": migration_hashes[relative]})
        self.manifest = {
            "schema": "phase31.4-v2.5-current-source-integrity/v13",
            "generation": "V2.5_CURRENT_SOURCE_SUCCESSOR_V13",
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
            "migration_file_sha256": migration_hashes,
            "new_migrations": new_migrations,
            "provenance_continuity": predecessor["provenance_continuity"],
            "provenance_discontinuity_status": predecessor["provenance_discontinuity_status"],
            "provenance_discontinuity_artifact": predecessor["provenance_discontinuity_artifact"],
            "retry_20_executed": False,
        }
        self.manifest_path = self.root / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V13.json"
        self.adoption_path = self.root / BASELINE_ADOPTION_MANIFEST.relative_to(ROOT)
        self._write_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def _copy(self, relative: str) -> None:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)

    def _write_manifest(self) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.adoption_path.parent.mkdir(parents=True, exist_ok=True)
        adoption = {
            "schema": "phase31.4-v2.5-baseline-adoption/v1",
            "decision": "ADOPT_BASELINE",
            "decision_id": "OFFLINE-TEST-PRECREATION-V13",
            "adopted_by": "offline-test-fixture",
            "adopted_at": "2026-09-30T12:00:00Z",
            "rationale": "PRECREATION offline verification fixture.",
            "manifest_path": self.manifest_path.relative_to(self.root).as_posix(),
            "manifest_sha256": file_sha256(self.manifest_path),
            "generation": self.manifest["generation"],
        }
        self.adoption_path.write_text(json.dumps(adoption), encoding="utf-8")

    def _run(self, run_id: str = "Phase 31.4 V2.5 Clean Retry TEST"):
        return verify_precreation_integrity(root=self.root, run_id=run_id)

    def test_valid_precreation_state_passes_and_serializes_evidence(self):
        result = self._run()
        self.assertEqual(result.status, "PASS")
        self.assertEqual({item["name"] for item in result.assertions}, {
            "current_source_integrity", "historical_v2_4_integrity", "protected_source_set",
            "migration_material_integrity", "contract_integrity", "verifier_integrity",
            "run_identity_uniqueness", "authority_configuration", "evidence_serialized",
        })
        evidence = json.loads((self.root / result.evidence_path).read_text(encoding="utf-8"))
        self.assertEqual(evidence["status"], "PASS")
        self.assertTrue(evidence["read_only_domain_operation"])
        selection = evidence["baseline_selection"]
        self.assertEqual(selection["kind"], "EXPLICIT_SUCCESSOR_ADOPTION")
        adoption_path = selection["adoption_decision"]["path"]
        self.assertEqual(
            evidence["evidence_hashes"][adoption_path],
            file_sha256(self.root / adoption_path),
        )

    def test_current_integrity_hash_mismatch_fails(self):
        self.manifest["sources"][0]["sha256"] = "0" * 64
        self._write_manifest()
        self.assertEqual(self._run().status, "FAIL")

    def test_missing_protected_source_fails(self):
        (self.root / "backend/foundation/phase31_4_v2_5_verifier_remediation.py").unlink()
        self.assertEqual(self._run().status, "FAIL")

    def test_historical_v24_mismatch_fails(self):
        path = self.root / "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertEqual(self._run().status, "FAIL")

    def test_missing_contract_fails(self):
        (self.root / "docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json").unlink()
        self.assertEqual(self._run().status, "FAIL")

    def test_malformed_integrity_artifact_fails(self):
        self.manifest_path.write_text("{not-json", encoding="utf-8")
        self.assertEqual(self._run().status, "FAIL")

    def test_duplicate_run_evidence_directory_fails(self):
        self.assertEqual(self._run().status, "PASS")
        duplicate = self._run()
        self.assertEqual(duplicate.status, "FAIL")
        self.assertIsNone(duplicate.evidence_path)

    def test_missing_evidence_reference_fails(self):
        (self.root / "approval.md").unlink()
        self.assertEqual(self._run().status, "FAIL")

    def test_returned_fail_propagates_as_fail(self):
        registry = NativeOperationRegistry.product_default()
        phase_registry = build_v25_native_phase_registry(registry, required_phase_ids=(PHASE_ID,))
        session = V25ExecutionSession(
            retry_id="Phase 31.4 V2.5 Clean Retry 17",
            project_root=self.root,
        )
        result = phase_registry.execute(PHASE_ID, session, PhaseExecutionContext(session=session))
        record = session.run_phase(PHASE_ID, lambda: result)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(record.status, "FAIL")
        self.assertIn("collides", record.error)

    def test_failed_precreation_stops_before_initial_opportunity(self):
        runtime = build_v25_runtime(
            project_root=self.root,
            retry_id="Phase 31.4 V2.5 Clean Retry 17",
        )
        runtime.run_clean_retry()
        self.assertEqual([record.name for record in runtime.session.phases], [PHASE_ID])
        self.assertEqual(runtime.session.phases[0].status, "FAIL")
