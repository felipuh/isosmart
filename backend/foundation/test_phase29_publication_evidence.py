import copy
import json

from django.test import SimpleTestCase

from .phase29_publication_evidence import (
    PUBLICATION_DISPOSITION_PATH,
    PUBLICATION_PATH,
    EvidenceError,
    offline_release_state,
    verify_phase28_publication_inputs,
    verify_publication_disposition,
    verify_publication_manifest,
)


class Phase29RetainedPublicationEvidenceTests(SimpleTestCase):
    def setUp(self):
        self.publication = json.loads(PUBLICATION_PATH.read_text(encoding="utf-8"))
        self.disposition = json.loads(PUBLICATION_DISPOSITION_PATH.read_text(encoding="utf-8"))

    def test_exact_phase28_inputs_and_publication_evidence_verify(self):
        creation, disposition, source = verify_phase28_publication_inputs()
        self.assertEqual(creation["candidate"]["id"], self.publication["candidate_id"])
        self.assertEqual(disposition["candidate_id"], self.publication["candidate_id"])
        self.assertEqual(source["manifest_material_hash"], self.publication["source_manifest_hash"])
        verify_publication_disposition(self.disposition, verify_publication_manifest(self.publication))

    def test_offline_release_state_has_no_activation_adoption_or_runtime_effect(self):
        self.assertEqual(offline_release_state(), {
            "candidate_id": "01a0682b-dfc8-7b49-a601-f9bda29a70a5",
            "CREATED": True, "APPLICATION_GOVERNED": True, "PUBLISHED": True,
            "ACTIVATED": False, "RUNTIME_ADOPTED": False, "RUNTIME_EFFECTIVE": False,
            "database_reconstructed": False,
        })

    def test_status_without_complete_graph_is_not_publication_evidence(self):
        tampered = copy.deepcopy(self.publication)
        del tampered["live_graph"]["audit"]
        with self.assertRaises(EvidenceError):
            verify_publication_manifest(tampered)

    def test_tampered_candidate_and_activation_fail_closed(self):
        for field, value in (("candidate_id", "da72872a-3f3c-5fcd-86f7-0ed33e453522"), ("runtime_effect_changed", True)):
            tampered = copy.deepcopy(self.publication)
            tampered[field] = value
            with self.subTest(field=field), self.assertRaises(EvidenceError):
                verify_publication_manifest(tampered)

    def test_skipped_state_fails_closed(self):
        tampered = copy.deepcopy(self.publication)
        tampered["import_state_history"].remove("PUBLICATION_PRECOMMIT_ELIGIBLE")
        with self.assertRaises(EvidenceError):
            verify_publication_manifest(tampered)
