"""Database-independent contract tests for the Phase 27.2 service boundary."""

import ast
import inspect
from pathlib import Path
import textwrap
from uuid import uuid4
from unittest.mock import patch

from django.test import SimpleTestCase

from .knowledge_rule_release import (
    PUBLICATION_PERMISSION,
    InertRuntimeAdoptionResolver,
    KnowledgeLayerRuleActivationService,
    KnowledgeLayerRulePublicationService,
    KnowledgeLayerRuleRuntimeAdoptionService,
    TrustedPublicationAuthority,
)


class InertKnowledgeRuleReleaseContractTests(SimpleTestCase):
    _P32_S2_LIFECYCLE_METHODS = (
        (KnowledgeLayerRulePublicationService.publish_native, "publication_id",
         "publish_knowledge_layer_rule_v1"),
        (KnowledgeLayerRuleActivationService.activate, "activation_id",
         "activate_knowledge_layer_rule_v1"),
        (KnowledgeLayerRuleRuntimeAdoptionService.adopt, "runtime_adoption_id",
         "adopt_knowledge_layer_rule_runtime_v1"),
    )
    _P32_S2_PROHIBITED_SCOPE_PARAMETERS = frozenset({
        "environment", "organization", "tenant", "agent", "target",
        "target_type", "scope", "current", "latest", "selector",
    })
    _P32_S2_DISPATCH_PARAMETERS = frozenset({"operation", "payload"})
    _P32_S2_ALLOWLIST = frozenset({
        "backend/foundation/test_knowledge_rule_release.py",
        "docs/transformation/phase32/evidence/"
        "P32-S2_LIFECYCLE_SCOPE_STATIC_CONFORMANCE_EXECUTION_EVIDENCE_2026-10-01.json",
    })

    @staticmethod
    def _p32_s2_method_tree(method):
        return ast.parse(textwrap.dedent(inspect.getsource(method)))

    @staticmethod
    def _p32_s2_repository_root():
        return Path(__file__).resolve().parents[2]

    def test_p32_s2_ac_01_lifecycle_entry_points_are_distinct_and_not_dispatchers(self):
        """AC-S2-01: entry points have separate artifact IDs and no dispatcher input."""
        entry_points = []
        for method, artifact_id_parameter, _ in self._P32_S2_LIFECYCLE_METHODS:
            parameters = set(inspect.signature(method).parameters)
            entry_points.append((method.__qualname__, artifact_id_parameter))
            self.assertIn(artifact_id_parameter, parameters)
            self.assertFalse(parameters & self._P32_S2_DISPATCH_PARAMETERS)
            self.assertFalse(parameters & self._P32_S2_PROHIBITED_SCOPE_PARAMETERS)

        self.assertEqual(entry_points, [
            ("KnowledgeLayerRulePublicationService.publish_native", "publication_id"),
            ("KnowledgeLayerRuleActivationService.activate", "activation_id"),
            ("KnowledgeLayerRuleRuntimeAdoptionService.adopt", "runtime_adoption_id"),
        ])

    def test_p32_s2_ac_02_lifecycle_methods_do_not_call_the_next_fact(self):
        """AC-S2-02: each entry point targets only its own named SQL function."""
        lifecycle_names = {"publish_native", "activate", "adopt"}
        for method, _, sql_target in self._P32_S2_LIFECYCLE_METHODS:
            tree = self._p32_s2_method_tree(method)
            called_attributes = {
                node.func.attr for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            source = inspect.getsource(method)
            self.assertFalse(called_attributes & lifecycle_names)
            self.assertIn(f"normative.{sql_target}", source)

    def test_p32_s2_ac_03_public_signatures_preserve_global_lineage_scope(self):
        """AC-S2-03: scope inputs are absent; policy sources remain the fixed boundary."""
        for method, _, _ in self._P32_S2_LIFECYCLE_METHODS:
            parameters = set(inspect.signature(method).parameters)
            self.assertFalse(parameters & self._P32_S2_PROHIBITED_SCOPE_PARAMETERS)

        root = self._p32_s2_repository_root()
        adr = (root / "docs/adr/0014-separate-knowledge-layer-rule-publication-activation-runtime-adoption.md")
        policy = (root / "docs/governance/KNOWLEDGE_LAYER_RULE_PUBLICATION_ACTIVATION_RUNTIME_ADOPTION_POLICY_V1.md")
        self.assertIn("global", adr.read_text(encoding="utf-8").lower())
        self.assertIn("global_knowledge_layer_runtime", policy.read_text(encoding="utf-8"))

    def test_p32_s2_ac_04_agentrun_and_recommendation_have_no_release_dependency(self):
        """AC-S2-04: the two runtime sources have no release import or resolver call."""
        root = self._p32_s2_repository_root()
        for relative_path in (
            "backend/foundation/agent_runtime.py",
            "backend/foundation/recommendation.py",
        ):
            source = (root / relative_path).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported_modules = {
                node.module for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            imported_names = {
                alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                for alias in node.names
            }
            self.assertFalse(any(
                module.endswith("knowledge_rule_release")
                for module in imported_modules | imported_names
            ))
            self.assertFalse(any(
                isinstance(node, ast.Name) and node.id == "InertRuntimeAdoptionResolver"
                for node in ast.walk(tree)
            ))

    def test_p32_s2_ac_05_static_contract_has_no_lifecycle_or_database_setup(self):
        """AC-S2-05: P32-S2 assertions are SimpleTestCase source inspection only."""
        self.assertTrue(issubclass(InertKnowledgeRuleReleaseContractTests, SimpleTestCase))
        for name in (
            "test_p32_s2_ac_01_lifecycle_entry_points_are_distinct_and_not_dispatchers",
            "test_p32_s2_ac_02_lifecycle_methods_do_not_call_the_next_fact",
            "test_p32_s2_ac_03_public_signatures_preserve_global_lineage_scope",
            "test_p32_s2_ac_04_agentrun_and_recommendation_have_no_release_dependency",
        ):
            source = inspect.getsource(getattr(self, name))
            self.assertNotIn(".publish_native(", source)
            self.assertNotIn(".activate(", source)
            self.assertNotIn(".adopt(", source)
            self.assertNotIn("connections[", source)
            self.assertNotIn("transaction.", source)

    def test_p32_s2_ac_06_declares_the_exact_execution_allowlist(self):
        """AC-S2-06: the execution evidence audits this immutable two-path allowlist."""
        self.assertEqual(self._P32_S2_ALLOWLIST, frozenset({
            "backend/foundation/test_knowledge_rule_release.py",
            "docs/transformation/phase32/evidence/"
            "P32-S2_LIFECYCLE_SCOPE_STATIC_CONFORMANCE_EXECUTION_EVIDENCE_2026-10-01.json",
        }))

    def test_resolver_has_only_exact_runtime_adoption_identifier(self):
        signature = inspect.signature(InertRuntimeAdoptionResolver.resolve)
        self.assertEqual(set(signature.parameters), {"self", "runtime_adoption_id"})

    def test_resolver_rejects_selector_and_fallback_tokens_before_database_access(self):
        resolver = InertRuntimeAdoptionResolver()
        connection = _RecordingConnection(row=None)
        with patch("foundation.knowledge_rule_release.connections", {"rule_resolver": connection}):
            for invalid in (
                None, "", "current", "latest", "27", "2026-09-02T00:00:00Z",
                "not-a-uuid",
            ):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    resolver.resolve(runtime_adoption_id=invalid)

        self.assertEqual(connection.cursor_calls, 0)
        self.assertEqual(connection.recording_cursor.execute_calls, [])

    def test_resolver_maps_exact_uuid_using_one_process_local_sql_call(self):
        runtime_adoption_id = uuid4()
        activation_id = uuid4()
        publication_id = uuid4()
        rule_id = uuid4()
        lineage_id = uuid4()
        connection = _RecordingConnection(
            row=(
                str(runtime_adoption_id), str(activation_id), str(publication_id),
                str(rule_id), str(lineage_id), "2026.10", "a" * 64,
            )
        )

        with patch("foundation.knowledge_rule_release.connections", {"rule_resolver": connection}):
            resolved = InertRuntimeAdoptionResolver().resolve(
                runtime_adoption_id=runtime_adoption_id,
            )

        self.assertEqual(resolved.runtime_adoption_id, runtime_adoption_id)
        self.assertEqual(resolved.activation_id, activation_id)
        self.assertEqual(resolved.publication_id, publication_id)
        self.assertEqual(resolved.knowledge_layer_rule_id, rule_id)
        self.assertEqual(resolved.lineage_id, lineage_id)
        self.assertEqual(resolved.rule_version, "2026.10")
        self.assertEqual(resolved.rule_material_hash, "a" * 64)
        self.assertEqual(connection.cursor_calls, 1)
        self.assertEqual(connection.recording_cursor.execute_calls, [
            (
                "SELECT runtime_adoption_id,activation_id,publication_id,knowledge_layer_rule_id,"
                "lineage_id,rule_version,rule_material_hash "
                "FROM normative.resolve_knowledge_layer_rule_runtime_adoption_v1(%s)",
                [str(runtime_adoption_id)],
            ),
        ])


class _RecordingCursor:
    """Process-local cursor double; it never opens a database connection."""

    def __init__(self, row):
        self.row = row
        self.execute_calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, sql, params):
        self.execute_calls.append((sql, params))

    def fetchone(self):
        return self.row


class _RecordingConnection:
    """Process-local connection double used only by resolver contract tests."""

    def __init__(self, row):
        self.recording_cursor = _RecordingCursor(row)
        self.cursor_calls = 0

    def cursor(self):
        self.cursor_calls += 1
        return self.recording_cursor

    def test_authority_revocation_is_checked_fresh_before_database_access(self):
        revoked = TrustedPublicationAuthority(
            uuid4(), frozenset({PUBLICATION_PERMISSION}), True, False, True,
            "adminapps-context/v2", "revoked-decision", "release-policy/v1",
        )
        with self.assertRaises(PermissionError):
            KnowledgeLayerRulePublicationService().publish_native(
                authority=revoked, publication_id=uuid4(), rule_id=uuid4(),
                expected_rule_material_hash="0" * 64, idempotency_key_hash="1" * 64,
                reason="must be denied", trace_id=uuid4(),
            )

    def test_command_signatures_do_not_offer_generic_dispatch_or_runtime_fallback(self):
        forbidden = {"target_type", "operation", "payload", "current", "latest", "version", "revision"}
        methods = (
            KnowledgeLayerRulePublicationService.publish_native,
            KnowledgeLayerRuleActivationService.activate,
            KnowledgeLayerRuleRuntimeAdoptionService.adopt,
        )
        for method in methods:
            with self.subTest(method=method.__name__):
                self.assertFalse(forbidden & set(inspect.signature(method).parameters))
