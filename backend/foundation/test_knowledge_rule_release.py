"""Database-independent contract tests for the Phase 27.2 service boundary."""

import inspect
from uuid import uuid4

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
    def test_resolver_has_only_exact_runtime_adoption_identifier(self):
        signature = inspect.signature(InertRuntimeAdoptionResolver.resolve)
        self.assertEqual(set(signature.parameters), {"self", "runtime_adoption_id"})

    def test_resolver_rejects_selector_and_fallback_tokens_before_database_access(self):
        resolver = InertRuntimeAdoptionResolver()
        for invalid in (None, "", "current", "latest", "27", "2026-09-02T00:00:00Z"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                resolver.resolve(runtime_adoption_id=invalid)

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
