"""Read-only regressions for the discovered Phase 31 import blocker."""

from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

import json

from . import phase31_activation_preflight as preflight


class Phase31ActivationPreflightTests(TestCase):
    def test_retained_publication_state_is_not_activation(self):
        result = preflight.inspect_exact_publication_import_dependency()
        state = result["retained_release_state"]
        for key in ("CREATED", "APPLICATION_GOVERNED", "PUBLISHED"):
            self.assertIs(state[key], True)
        for key in ("ACTIVATED", "RUNTIME_ADOPTED", "RUNTIME_EFFECTIVE", "database_reconstructed"):
            self.assertIs(state[key], False)

    def test_required_historical_row_is_absent(self):
        result = preflight.inspect_exact_publication_import_dependency()
        self.assertEqual(result["required_row_id"], preflight.CURATION_AUDIT_ID)
        self.assertEqual(result["complete_retained_row_occurrences"], 0)
        self.assertIs(result["dependency_material_present"], False)
        self.assertIs(result["database_creation_authorized"], False)

    def test_no_database_or_runtime_modules_are_dependencies(self):
        # Run the actual check while rejecting any new DB/runtime imports.
        import builtins
        original = builtins.__import__

        def guarded(name, *args, **kwargs):
            self.assertNotIn(name.split(".")[0], {"django", "psycopg", "psycopg2"})
            self.assertNotIn(name, {"foundation.agent_runtime", "foundation.knowledge_rule_release"})
            return original(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guarded):
            preflight.inspect_exact_publication_import_dependency()

    def test_pinned_manifest_cannot_be_substituted(self):
        with patch.object(preflight, "PUBLICATION_HASH", "0" * 64):
            with self.assertRaisesRegex(preflight.EvidenceError, "manifest hash mismatch"):
                preflight.inspect_exact_publication_import_dependency()

    def test_pinned_disposition_cannot_be_substituted(self):
        with patch.object(preflight, "DISPOSITION_HASH", "0" * 64):
            with self.assertRaisesRegex(preflight.EvidenceError, "disposition hash mismatch"):
                preflight.inspect_exact_publication_import_dependency()

    def test_pinned_activation_policy_cannot_be_substituted(self):
        with patch.object(preflight, "POLICY_HASH", "0" * 64):
            with self.assertRaisesRegex(preflight.EvidenceError, "policy file hash mismatch"):
                preflight.inspect_exact_publication_import_dependency()

    def test_cli_fails_closed_with_hashed_diagnostic(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(preflight.main(), 1)
        result = json.loads(output.getvalue())
        digest = result.pop("diagnostic_material_hash")
        self.assertEqual(digest, preflight.material_hash(result))
        self.assertEqual(result["blocker"], "MISSING_RETAINED_PUBLICATION_CURATION_AUDIT")
        self.assertIs(result["activation_invoked"], False)

    def test_verification_exception_never_authorizes_database(self):
        with patch.object(preflight, "offline_release_state", side_effect=preflight.EvidenceError("invalid evidence")):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(preflight.main(), 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result["blocker"], "RETAINED_INPUT_VERIFICATION_FAILED")
            self.assertIs(result["database_creation_authorized"], False)
