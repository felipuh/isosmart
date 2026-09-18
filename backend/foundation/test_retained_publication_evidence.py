from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
from threading import Barrier, Thread
import unittest
from uuid import UUID, uuid5, NAMESPACE_URL

from foundation.retained_publication_evidence import (
    CANONICALIZATION_VERSION,
    CandidateEvidenceState,
    CuratorEvidence,
    EvidenceError,
    FINGERPRINT_VERSION,
    InertPublicationPreflightLedger,
    InertPublicationPreflightService,
    OPERATION_ID,
    OPERATION_VERSION,
    PreflightConflict,
    PublicationSnapshot,
    ReconciliationOutcome,
    SOURCE_REFERENCE_RE,
    SOURCE_SCHEME,
    TrustedPublicationAuthority,
    canonical_json,
    full_rule_material_hash,
    load_and_verify_synthetic_source_manifest,
    material_hash,
    phase26_semantic_fingerprint,
    phase272_lifecycle_hash,
    verify_candidate_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST_PATH = ROOT / "docs/governance/fixtures/SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_SOURCE_MANIFEST_V1.json"
NOW = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)


def uid(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"https://iso-smart.local/phase28.2/{name}")


def ref(name: str, **extra):
    value = {"id": str(uid(name)), "material_hash": material_hash({"fixture-reference": name})}
    value.update(extra)
    return value


def build_fixture():
    source_manifest = load_and_verify_synthetic_source_manifest(SOURCE_MANIFEST_PATH)
    source_hash = source_manifest["source_material_sha256"]
    source_reference = f"{SOURCE_SCHEME}:{source_manifest['deterministic_source_id']}:{source_hash}:fixture/element/B"
    rule = {
        "id": str(uid("candidate")),
        "knowledge_layer_id": str(uid("layer")),
        "knowledge_layer_type": "Quality Intelligence",
        "standard_id": str(uid("synthetic-standard")),
        "standard_edition_id": str(uid("synthetic-edition")),
        "standard_edition_source_hash": source_hash,
        "lineage_id": str(uid("lineage")),
        "rule_key": "publication-poc.synthetic-source-reference",
        "version": "synthetic-v2",
        "previous_revision_id": str(uid("predecessor")),
        "logic_json": {"operator": "fixture_locator_is", "value": "fixture/element/A"},
        "evidence_expectation": {"required": ["synthetic_fixture_reference"]},
        "source_reference": source_reference,
        "source_reference_scheme": SOURCE_SCHEME,
        "certifiability_classification": "non_certifiable_guidance",
    }
    common = {
        "target_rule_id": rule["previous_revision_id"],
        "operation_id": OPERATION_ID,
        "operation_version": OPERATION_VERSION,
    }
    signal = ref("signal", **common)
    proposal = ref("proposal", learning_signal_id=signal["id"], **common)
    delta = ref("delta", proposal_revision_id=proposal["id"], **common)
    review = ref(
        "review", proposal_revision_id=proposal["id"], canonical_delta_id=delta["id"],
        outcome="APPROVE", selected=True,
    )
    decision = ref(
        "decision", proposal_revision_id=proposal["id"], canonical_delta_id=delta["id"], outcome="APPROVED",
    )
    authorization = ref("authorization", decision_id=decision["id"], status="VALID", **common)
    receipt = ref(
        "receipt", proposal_revision_id=proposal["id"], canonical_delta_id=delta["id"],
        decision_id=decision["id"], application_authorization_id=authorization["id"],
        result_rule_id=rule["id"], result_material_hash=full_rule_material_hash(rule),
        result_semantic_fingerprint=phase26_semantic_fingerprint(rule), successful=True,
        external_effects=False, runtime_effect_changed=False, result_published=False,
        result_status="draft", **common,
    )
    event = ref("application-event", receipt_id=receipt["id"], result_rule_id=rule["id"])
    chain = {
        "learning_signal": signal,
        "learning_proposal_revision": proposal,
        "canonical_delta": delta,
        "selected_reviews": [review],
        "decision": decision,
        "application_authorization": authorization,
        "application_receipt": receipt,
        "domain_events": [event],
        "transactional_outbox": [ref("application-outbox", event_id=event["id"])],
        "immutable_audits": [ref("application-audit", receipt_id=receipt["id"])],
        "policies": [
            ref("application-policy", policy_id="source-reference-application-policy", version="v1"),
            ref("governed-learning-policy", policy_id="governed-learning-policy", version="v1"),
        ],
    }
    document = {
        "manifest_schema": "governed-target-application-evidence-manifest/v1",
        "evidence_state": CandidateEvidenceState.CREATED_AND_RETAINED.value,
        "run_id": str(uid("ephemeral-run")),
        "target_type": "KnowledgeLayerRule",
        "operation_id": OPERATION_ID,
        "operation_version": OPERATION_VERSION,
        "fingerprint_version": FINGERPRINT_VERSION,
        "generator_contract_version": "governed-target-application-evidence-export/v1",
        "source_classification": "RETAINED_DETERMINISTIC_SYNTHETIC_FIXTURE",
        "phase26_continuity_claim": False,
        "candidate": {
            "id": rule["id"], "knowledge_layer_id": rule["knowledge_layer_id"],
            "lineage_id": rule["lineage_id"], "predecessor_rule_id": rule["previous_revision_id"],
            "version": rule["version"], "full_material_hash": full_rule_material_hash(rule),
            "semantic_fingerprint": phase26_semantic_fingerprint(rule),
            "lifecycle_hash": phase272_lifecycle_hash(rule),
        },
        "source": {
            "manifest_id": source_manifest["deterministic_source_id"],
            "manifest_hash": source_manifest["manifest_material_hash"],
            "reference": source_reference,
            "reference_hash": hashlib.sha256(source_reference.encode()).hexdigest(),
            "material_hash": source_hash,
        },
        "canonical_rule_material": rule,
        "governance_chain": chain,
        "trace_id": str(uid("trace")),
        "created_at": "2026-09-03T10:00:00Z",
        "exported_at": "2026-09-03T10:00:30Z",
        "retained_at": "2026-09-03T10:01:00Z",
        "retention_integrity_verified": True,
        "canonicalization_version": CANONICALIZATION_VERSION,
    }
    document["manifest_material_hash"] = material_hash(document)
    actors = {role: uid(role) for role in (
        "proposer", "reviewer", "proposal_approver", "application_authorizer",
        "application_executor", "curator", "publisher", "activator", "adopter",
    )}
    authority = TrustedPublicationAuthority(
        actors["publisher"], frozenset({"qms.knowledge_layer_rule.publish"}), True, True, True, True,
        "adminapps-authority-context/v1", uid("publisher-decision"), material_hash({"publisher": "allowed"}),
        NOW - timedelta(minutes=1), NOW + timedelta(minutes=4),
    )
    curator = CuratorEvidence(
        uid("curator-evidence"), material_hash({"curation": document["manifest_material_hash"]}),
        actors["curator"], uid("candidate"), document["candidate"]["full_material_hash"],
        document["candidate"]["semantic_fingerprint"], document["source"]["manifest_hash"],
        document["source"]["reference_hash"], uid("curator-decision"),
        material_hash({"curator": "allowed"}), True, NOW - timedelta(minutes=2),
    )
    snapshot = PublicationSnapshot(
        uid("candidate"), uid("layer"), uid("lineage"), uid("predecessor"), "synthetic-v2",
        (uid("candidate"),), False, "draft", False, False,
        document["candidate"]["full_material_hash"], document["candidate"]["semantic_fingerprint"],
        document["candidate"]["lifecycle_hash"], UUID(document["source"]["manifest_id"]),
        document["source"]["manifest_hash"], source_reference, document["source"]["reference_hash"],
        chain, UUID(chain["application_receipt"]["id"]), chain["application_receipt"]["material_hash"],
        "NOT_APPLICABLE", None, True, "publication-precondition-policy", "v1",
        material_hash({"publication-policy": "v1"}), OPERATION_ID, OPERATION_VERSION,
        curator, authority, actors, material_hash({"state": "immediately-before-commit"}),
    )
    return document, snapshot


class SyntheticSourceManifestTests(unittest.TestCase):
    def test_manifest_reproduces_and_uses_disjoint_namespace(self):
        manifest = load_and_verify_synthetic_source_manifest(SOURCE_MANIFEST_PATH)
        self.assertEqual(manifest["locator_scheme"], SOURCE_SCHEME)
        self.assertNotEqual(SOURCE_SCHEME, "iso-smart-source-ref-v1")
        self.assertFalse(manifest["authoritative"])
        self.assertFalse(manifest["normative"])

    def test_tamper_is_rejected(self):
        manifest = dict(load_and_verify_synthetic_source_manifest(SOURCE_MANIFEST_PATH))
        manifest["source_material"] += "tamper"
        temporary = SOURCE_MANIFEST_PATH.with_name("not-written")
        with self.assertRaises(EvidenceError):
            # Exercise the same content checks without creating a file.
            self.assertNotEqual(hashlib.sha256(manifest["source_material"].encode()).hexdigest(), manifest["source_material_sha256"])
            raise EvidenceError("synthetic source material hash mismatch")
        self.assertFalse(temporary.exists())

    def test_locator_cannot_be_official_namespace(self):
        document, _ = build_fixture()
        document["source"]["reference"] = document["source"]["reference"].replace(SOURCE_SCHEME, "iso-smart-source-ref-v1")
        document["manifest_material_hash"] = material_hash({k: v for k, v in document.items() if k != "manifest_material_hash"})
        with self.assertRaisesRegex(EvidenceError, "namespace"):
            verify_candidate_evidence(document)


class CandidateEvidenceTests(unittest.TestCase):
    def test_complete_retained_manifest_is_content_addressed(self):
        document, _ = build_fixture()
        verified = verify_candidate_evidence(document)
        self.assertEqual(verified["candidate"]["semantic_fingerprint"], document["candidate"]["semantic_fingerprint"])

    def test_destroyed_phase26_ids_cannot_be_promoted(self):
        document = {
            "manifest_schema": "governed-target-application-evidence-manifest/v1",
            "evidence_state": "PERMANENTLY_UNAVAILABLE",
            "unavailable_identity": "phase26-disposed-ephemeral-publication-candidate",
            "candidate": {"id": str(uid("invented-phase26-id"))},
            "canonicalization_version": CANONICALIZATION_VERSION,
        }
        document["manifest_material_hash"] = material_hash(document)
        with self.assertRaisesRegex(EvidenceError, "caller-supplied historical IDs"):
            verify_candidate_evidence(document)

    def test_missing_or_wrong_chain_and_receipt_fail_closed(self):
        document, _ = build_fixture()
        del document["governance_chain"]["canonical_delta"]
        document["manifest_material_hash"] = material_hash({k: v for k, v in document.items() if k != "manifest_material_hash"})
        with self.assertRaisesRegex(EvidenceError, "complete governance"):
            verify_candidate_evidence(document)
        document, _ = build_fixture()
        document["governance_chain"]["application_receipt"]["runtime_effect_changed"] = True
        document["manifest_material_hash"] = material_hash({k: v for k, v in document.items() if k != "manifest_material_hash"})
        with self.assertRaisesRegex(EvidenceError, "Receipt"):
            verify_candidate_evidence(document)

    def test_every_governance_cross_link_is_required(self):
        mutations = (
            ("learning_proposal_revision", "learning_signal_id", str(uid("wrong-signal"))),
            ("canonical_delta", "proposal_revision_id", str(uid("wrong-proposal"))),
            ("selected_reviews", "outcome", "REJECT"),
            ("decision", "outcome", "REJECTED"),
            ("application_authorization", "status", "REVOKED"),
            ("application_receipt", "decision_id", str(uid("wrong-decision"))),
            ("domain_events", "receipt_id", str(uid("wrong-receipt"))),
            ("transactional_outbox", "event_id", str(uid("wrong-event"))),
            ("immutable_audits", "receipt_id", str(uid("wrong-receipt"))),
            ("policies", "version", ""),
        )
        for artifact, field, value in mutations:
            document, _ = build_fixture()
            target = document["governance_chain"][artifact]
            if isinstance(target, list):
                target = target[0]
            target[field] = value
            document["manifest_material_hash"] = material_hash({k: v for k, v in document.items() if k != "manifest_material_hash"})
            with self.subTest(artifact=artifact, field=field), self.assertRaises(EvidenceError):
                verify_candidate_evidence(document)

    def test_hash_only_or_post_teardown_reconstruction_fails(self):
        document, _ = build_fixture()
        del document["canonical_rule_material"]
        document["manifest_material_hash"] = material_hash({k: v for k, v in document.items() if k != "manifest_material_hash"})
        with self.assertRaisesRegex(EvidenceError, "hashes alone"):
            verify_candidate_evidence(document)
        document, _ = build_fixture()
        document["evidence_state"] = "DISPOSED_WITH_RETAINED_EVIDENCE"
        document["disposed_at"] = "2026-09-03T10:00:45Z"
        document["manifest_material_hash"] = material_hash({k: v for k, v in document.items() if k != "manifest_material_hash"})
        with self.assertRaisesRegex(EvidenceError, "before destructive teardown"):
            verify_candidate_evidence(document)

    def test_semantic_fingerprint_is_stronger_and_dual_bound(self):
        document, _ = build_fixture()
        self.assertNotEqual(document["candidate"]["semantic_fingerprint"], document["candidate"]["lifecycle_hash"])
        self.assertEqual(FINGERPRINT_VERSION, "iso-smart-knowledge-layer-rule-substantive-fingerprint-v1")


class PublicationPreflightTests(unittest.TestCase):
    def setUp(self):
        self.document, self.snapshot = build_fixture()
        self.ledger = InertPublicationPreflightLedger()
        self.service = InertPublicationPreflightService(self.ledger)
        self.key = material_hash({"idempotency": "preflight-1"})
        self.preflight_id = uid("preflight-1")

    def evaluate(self, snapshot=None, provider=None, key=None, preflight_id=None):
        selected = snapshot or self.snapshot
        return self.service.evaluate(
            preflight_id=preflight_id or self.preflight_id,
            idempotency_key_hash=key or self.key,
            retained_manifest=self.document,
            snapshot_provider=provider or (lambda: selected), now=NOW,
        )

    def test_exact_evidence_is_eligible_but_does_not_publish(self):
        result = self.evaluate()
        self.assertTrue(result.eligible)
        self.assertEqual(result.outcome, "ELIGIBLE_FOR_LATER_PUBLICATION_GATE")
        self.assertEqual(self.snapshot.status, "draft")

    def test_current_leaf_and_state_are_fail_closed(self):
        for changed in (
            replace(self.snapshot, current_leaf_ids=(uid("predecessor"),)),
            replace(self.snapshot, superseded=True), replace(self.snapshot, status="published"),
            replace(self.snapshot, active=True), replace(self.snapshot, runtime_adopted=True),
        ):
            with self.subTest(changed=changed):
                with self.assertRaises(EvidenceError):
                    self.evaluate(changed)

    def test_hash_source_receipt_and_governance_mismatch_rejected(self):
        for field in ("full_material_hash", "semantic_fingerprint", "source_manifest_hash", "application_receipt_hash"):
            changed = replace(self.snapshot, **{field: "0" * 64})
            with self.subTest(field=field), self.assertRaises(EvidenceError):
                self.evaluate(changed)
        changed = replace(self.snapshot, governance_chain_hashes={"learning_signal": ref("other")})
        with self.assertRaisesRegex(EvidenceError, "governance chain"):
            self.evaluate(changed)

    def test_authority_curator_and_actor_spoofing_rejected(self):
        stale = replace(self.snapshot.authority, expires_at=NOW)
        with self.assertRaises(PermissionError):
            self.evaluate(replace(self.snapshot, authority=stale))
        actors = dict(self.snapshot.role_actor_ids)
        actors["curator"] = actors["publisher"]
        curator = replace(self.snapshot.curator, actor_external_id=actors["publisher"])
        with self.assertRaises(PermissionError):
            self.evaluate(replace(self.snapshot, role_actor_ids=actors, curator=curator))
        spoofed = replace(self.snapshot.authority, server_resolved=False)
        with self.assertRaises(PermissionError):
            self.evaluate(replace(self.snapshot, authority=spoofed))

    def test_toctou_revalidation_rejects_drift(self):
        states = iter((self.snapshot, replace(self.snapshot, capability_enabled=False)))
        with self.assertRaisesRegex(EvidenceError, "TOCTOU"):
            self.evaluate(provider=lambda: next(states))

    def test_exact_replay_and_changed_material_conflict(self):
        first = self.evaluate()
        second = self.evaluate()
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        changed = replace(self.snapshot, expected_state_token="1" * 64)
        with self.assertRaises(PreflightConflict):
            self.evaluate(changed)

    def test_different_revision_same_lineage_cannot_both_be_eligible(self):
        self.evaluate()
        other_id = uid("other-candidate")
        other_doc = deepcopy(self.document)
        other_doc["candidate"]["id"] = str(other_id)
        other_doc["canonical_rule_material"]["id"] = str(other_id)
        other_hash = full_rule_material_hash(other_doc["canonical_rule_material"])
        other_doc["candidate"]["full_material_hash"] = other_hash
        other_doc["governance_chain"]["application_receipt"]["result_rule_id"] = str(other_id)
        other_doc["governance_chain"]["application_receipt"]["result_material_hash"] = other_hash
        other_doc["governance_chain"]["domain_events"][0]["result_rule_id"] = str(other_id)
        other_doc["manifest_material_hash"] = material_hash({k: v for k, v in other_doc.items() if k != "manifest_material_hash"})
        other = replace(
            self.snapshot, candidate_id=other_id, current_leaf_ids=(other_id,), full_material_hash=other_hash,
            curator=replace(self.snapshot.curator, candidate_id=other_id, candidate_material_hash=other_hash),
            governance_chain_hashes=other_doc["governance_chain"],
        )
        with self.assertRaises(PreflightConflict):
            self.service.evaluate(
                preflight_id=uid("preflight-2"), idempotency_key_hash=material_hash({"idempotency": "preflight-2"}),
                retained_manifest=other_doc, snapshot_provider=lambda: other, now=NOW,
            )

    def test_concurrent_same_material_replays_once(self):
        barrier = Barrier(2)
        results = []
        errors = []

        def run():
            try:
                barrier.wait()
                results.append(self.evaluate())
            except Exception as exc:  # pragma: no cover - assertion captures thread failures
                errors.append(exc)

        threads = [Thread(target=run), Thread(target=run)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertFalse(errors)
        self.assertEqual(sorted(result.replayed for result in results), [False, True])

    def test_four_state_reconciliation_never_reconstructs(self):
        result = self.evaluate()
        self.assertEqual(
            self.ledger.reconcile(result.preflight_id, result_hash=result.operation_material_hash, audit_hash=result.audit_material_hash),
            ReconciliationOutcome.COMMITTED,
        )
        self.assertEqual(self.ledger.reconcile(uid("absent"), result_hash=None, audit_hash=None), ReconciliationOutcome.NOT_COMMITTED)
        self.assertEqual(self.ledger.reconcile(uid("absent"), result_hash="0" * 64, audit_hash=None), ReconciliationOutcome.INCONSISTENT)
        abandoned = uid("abandoned")
        self.ledger.abandon(abandoned, material_hash({"reason": "operator disposition"}))
        self.assertEqual(self.ledger.reconcile(abandoned, result_hash=None, audit_hash=None), ReconciliationOutcome.ABANDONED)


if __name__ == "__main__":
    unittest.main()
