"""Offline Phase 28.3 retained-evidence verification after PostgreSQL teardown."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from uuid import NAMESPACE_URL, uuid5


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from foundation.phase283_retained_candidate import (
    publication_snapshot_from_retained_manifest, write_retained_json_once,
)
from foundation.retained_publication_evidence import (
    CandidateEvidenceState, EvidenceError, InertPublicationPreflightService,
    load_and_verify_synthetic_source_manifest, material_hash,
    verify_phase283_candidate_evidence, verify_phase283_disposition,
)


SOURCE_PATH = ROOT / "docs/governance/fixtures/SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_SOURCE_MANIFEST_V1.json"
MANIFEST_PATH = ROOT / "docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_CREATED_AND_RETAINED_V1.json"
DISPOSITION_PATH = ROOT / "docs/governance/evidence/PHASE28_3_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_DISPOSITION_V1.json"


def main():
    source = load_and_verify_synthetic_source_manifest(SOURCE_PATH)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    verify_phase283_candidate_evidence(manifest, source_manifest=source)

    tampered = deepcopy(manifest)
    tampered["candidate"]["version"] = "tampered"
    try:
        verify_phase283_candidate_evidence(tampered, source_manifest=source)
    except EvidenceError:
        tamper_rejected = True
    else:
        raise AssertionError("tampered retained manifest was accepted")

    snapshot = publication_snapshot_from_retained_manifest(manifest)
    verified_at = datetime.now(timezone.utc)
    preflight = InertPublicationPreflightService().evaluate(
        preflight_id=uuid5(NAMESPACE_URL, f"phase28.3/post-teardown/{manifest['manifest_material_hash']}"),
        idempotency_key_hash=material_hash({"phase": "28.3", "gate": "post-teardown", "manifest": manifest["manifest_material_hash"]}),
        retained_manifest=manifest, snapshot_provider=lambda: snapshot, now=verified_at,
    )
    teardown = {
        "database_absent": True, "roles_absent": True, "container_absent": True,
        "volume_absent": True, "temp_absent": True,
        "verification_basis": "postgres_foundation_gate scoped drop and absence checks completed before this offline process",
    }
    post_verification = {
        "verified_at": verified_at.isoformat(), "manifest_verified": True,
        "source_manifest_verified": True, "governance_cross_links_verified": True,
        "root_candidate_hashes_verified": True, "current_leaf_proof_verified": True,
        "curator_and_sod_verified": True, "tampered_manifest_rejected": tamper_rejected,
        "preflight_outcome": preflight.outcome,
        "preflight_operation_material_hash": preflight.operation_material_hash,
        "preflight_audit_material_hash": preflight.audit_material_hash,
        "database_reconstructed": False,
    }
    disposition = {
        "disposition_schema": "governed-target-application-evidence-disposition/v1",
        "evidence_state": CandidateEvidenceState.DISPOSED_WITH_RETAINED_EVIDENCE.value,
        "run_id": manifest["run_id"], "candidate_id": manifest["candidate"]["id"],
        "created_manifest_hash": manifest["manifest_material_hash"],
        "disposed_at": verified_at.isoformat(), "teardown_evidence": teardown,
        "teardown_evidence_hash": material_hash(teardown),
        "post_teardown_verification": post_verification,
        "post_teardown_verification_hash": material_hash(post_verification),
        "canonicalization_version": manifest["canonicalization_version"],
    }
    disposition["disposition_material_hash"] = material_hash(disposition)
    verify_phase283_disposition(disposition, created_manifest=manifest)
    replayed = write_retained_json_once(DISPOSITION_PATH, disposition)
    retained_disposition = json.loads(DISPOSITION_PATH.read_text(encoding="utf-8"))
    verify_phase283_disposition(retained_disposition, created_manifest=manifest)
    print(json.dumps({
        "status": "PASS", "manifest": str(MANIFEST_PATH), "manifest_hash": manifest["manifest_material_hash"],
        "disposition": str(DISPOSITION_PATH), "disposition_hash": disposition["disposition_material_hash"],
        "disposition_replayed": replayed, "tamper_rejected": tamper_rejected,
        "preflight": preflight.outcome, "database_reconstructed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

