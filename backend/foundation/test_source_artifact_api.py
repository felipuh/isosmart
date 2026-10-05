from datetime import datetime, timezone
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import yaml
from django.conf import settings
from django.test import SimpleTestCase
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from foundation.api_views import (
    ApprovalDecisionView,
    DomainEventPublishView,
    EvidenceCreateView,
    FoundationAttemptCreateView,
    OnboardingEvidenceReferencesCreateView,
    OnboardingOrganizationsView,
    OnboardingStatusView,
    OrganizationalProfileCreateView,
    RecommendationBasisView,
    RecommendationListView,
)
from foundation.source_artifact_api import (
    SourceArtifactAPIError,
    SourceArtifactPrincipal,
    _public_options,
    foundation_database_alias,
    resolve_source_artifact_principal,
)
from foundation.tenant_context import TrustedTenantIdentity


TENANT_ID = uuid4()
USER_ID = uuid4()
ACTOR_ID = uuid4()
TRACE_ID = uuid4()
PRINCIPAL = SourceArtifactPrincipal(
    identity=TrustedTenantIdentity(str(ACTOR_ID), TENANT_ID),
    tenant_id=TENANT_ID,
    user_projection_id=USER_ID,
    actor_id=ACTOR_ID,
    roles=("quality_manager",),
    role_code="quality_manager",
    industry_code="manufacturing",
    client_id="contract-test-publisher",
    scopes=frozenset({"domain:events:publish"}),
)


class SourceArtifactRouteTests(SimpleTestCase):
    def test_source_routes_are_available_through_the_browser_api_gateway(self):
        routes = (
            "/api/v1/onboarding/status",
            "/api/v1/onboarding/organizations",
            "/api/v1/onboarding/organizational-profile",
            "/api/v1/onboarding/document-references",
            "/api/v1/learning/iso9000/attempts",
        )
        for route in routes:
            with self.subTest(route=route):
                self.assertIsNotNone(resolve(route).func.view_class)

    def test_all_documented_routes_resolve_with_the_contract_method(self):
        routes = (
            ("/v1/onboarding/status", "get"),
            ("/v1/onboarding/organizations", "get"),
            ("/v1/onboarding/organizational-profile", "post"),
            ("/v1/onboarding/document-references", "post"),
            ("/v1/recommendations", "get"),
            (f"/v1/recommendations/{uuid4()}/basis", "get"),
            (f"/v1/approvals/{uuid4()}/decision", "post"),
            ("/v1/events", "post"),
            ("/v1/evidence", "post"),
            ("/v1/learning/iso9000/attempts", "post"),
        )
        for route, method in routes:
            with self.subTest(route=route):
                match = resolve(route)
                self.assertEqual(match.func.view_class.__name__, {
                    "/v1/onboarding/status": "OnboardingStatusView",
                    "/v1/onboarding/organizations": "OnboardingOrganizationsView",
                    "/v1/onboarding/organizational-profile": "OrganizationalProfileCreateView",
                    "/v1/onboarding/document-references": "OnboardingEvidenceReferencesCreateView",
                    "/v1/recommendations": "RecommendationListView",
                    "/v1/events": "DomainEventPublishView",
                    "/v1/evidence": "EvidenceCreateView",
                    "/v1/learning/iso9000/attempts": "FoundationAttemptCreateView",
                }.get(route, match.func.view_class.__name__))
                self.assertIn(method, match.func.view_class.http_method_names)

    def test_onboarding_options_do_not_leak_question_answer_material(self):
        public = _public_options([
            {"id": "a", "label": "Choice A", "correct": True, "answer_key": ["a"]},
        ])
        self.assertEqual(public, [{"id": "a", "label": "Choice A"}])

    def test_unverified_session_identity_cannot_resolve_a_trusted_principal(self):
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True), auth=None)
        with self.assertRaises(SourceArtifactAPIError) as caught:
            resolve_source_artifact_principal(request)
        self.assertEqual(caught.exception.status_code, 403)

    def test_principal_uses_signed_tenant_claim_and_matching_user_projection(self):
        tenant_external_id = uuid4()
        actor_id = uuid4()
        tenant = SimpleNamespace(id=TENANT_ID)
        projection = SimpleNamespace(id=USER_ID)
        tenant_manager = SimpleNamespace(get=Mock(return_value=tenant))
        user_manager = SimpleNamespace(get=Mock(return_value=projection))
        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, pk=actor_id),
            auth={"organization_id": str(tenant_external_id), "user_id": str(actor_id), "role": "quality_manager"},
            user_profile=None,
        )
        with patch("foundation.source_artifact_api.TenantProjection.objects.using", return_value=tenant_manager), \
             patch("foundation.source_artifact_api.UserProjection.objects.using", return_value=user_manager), \
               patch("foundation.source_artifact_api._resolve_tenant_projection_id", return_value=TENANT_ID) as tenant_resolver, \
             patch("foundation.source_artifact_api.trusted_tenant_context", return_value=nullcontext()):
            principal = resolve_source_artifact_principal(request)

        self.assertEqual(principal.tenant_id, TENANT_ID)
        self.assertEqual(principal.user_projection_id, USER_ID)
        tenant_resolver.assert_called_once()
        self.assertEqual(tenant_resolver.call_args.args[0], tenant_external_id)
        tenant_manager.get.assert_called_once_with(
            id=TENANT_ID,
            adminapps_tenant_id=tenant_external_id,
            lifecycle_status="active",
            provisioning_status="complete",
            reconciliation_status="in_sync",
        )
        user_manager.get.assert_called_once_with(
            adminapps_user_id=actor_id,
            tenant_id=TENANT_ID,
            lifecycle_status="active",
        )

    def test_postgresql_alias_fallback_is_development_sqlite_only(self):
        sqlite_databases = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
        with patch.object(settings, "DATABASES", sqlite_databases), \
            patch.object(settings, "IS_DEVELOPMENT", True), \
            patch.object(settings, "IS_PRODUCTION", False):
            self.assertEqual(foundation_database_alias("app"), "default")
        with patch.object(settings, "DATABASES", sqlite_databases), \
            patch.object(settings, "IS_DEVELOPMENT", False), \
            patch.object(settings, "IS_PRODUCTION", True):
            with self.assertRaises(SourceArtifactAPIError) as caught:
                foundation_database_alias("app")
        self.assertEqual(caught.exception.status_code, 503)

    def test_runtime_openapi_has_exact_operations_and_bearer_auth(self):
        path = Path(__file__).with_name("source_artifact_openapi.yaml")
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        methods = {route: next(iter(operations)) for route, operations in spec["paths"].items()}
        self.assertEqual(methods, {
            "/v1/onboarding/status": "get",
            "/v1/onboarding/organizations": "get",
            "/v1/onboarding/organizational-profile": "post",
            "/v1/onboarding/document-references": "post",
            "/v1/recommendations": "get",
            "/v1/recommendations/{id}/basis": "get",
            "/v1/approvals/{id}/decision": "post",
            "/v1/events": "post",
            "/v1/evidence": "post",
            "/v1/learning/iso9000/attempts": "post",
        })
        self.assertEqual(spec["security"], [{"BearerAuth": []}])


class SourceArtifactViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=USER_ID)

    def invoke(self, view, method, path, data=None, **kwargs):
        request = getattr(self.factory, method)(path, data, format="json")
        force_authenticate(request, user=self.user)
        return view(request, **kwargs)

    def test_get_onboarding_status_delegates_and_returns_gate_contract(self):
        expected = {"foundation_gate": {"required": True, "status": "not_started"}}
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.onboarding_status", return_value=expected):
            response = self.invoke(OnboardingStatusView.as_view(), "get", "/v1/onboarding/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

    def test_get_onboarding_organizations_is_tenant_scoped_by_service(self):
        expected = {"organizations": [{"id": str(uuid4()), "display_name": "QMS"}]}
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.onboarding_organizations", return_value=expected) as service:
            response = self.invoke(OnboardingOrganizationsView.as_view(), "get", "/v1/onboarding/organizations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)
        service.assert_called_once_with(PRINCIPAL)

    def test_post_organizational_profile_uses_tenant_scoped_command(self):
        organization_id, event_id = uuid4(), uuid4()
        expected = {"workflow_id": str(uuid4()), "step": "organizational_profile", "status": "complete"}
        payload = {
            "organization_id": str(organization_id), "event_id": str(event_id),
            "role": "quality_manager", "expertise_level": "intermediate",
            "size_range": "10-50", "sites_count": 1, "countries": ["CR"],
            "sector": "manufacturing", "certification_status": "first_time",
        }
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.save_organizational_profile", return_value=expected) as service:
            response = self.invoke(
                OrganizationalProfileCreateView.as_view(), "post",
                "/v1/onboarding/organizational-profile", payload,
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, expected)
        self.assertEqual(service.call_args.args[0], PRINCIPAL)
        self.assertEqual(service.call_args.args[1]["organization_id"], organization_id)
        self.assertEqual(service.call_args.args[1]["event_id"], event_id)
        self.assertEqual(service.call_args.args[1]["profile"]["role"], "quality_manager")

    def test_post_document_references_stays_metadata_only(self):
        organization_id, event_id, item_event_id = uuid4(), uuid4(), uuid4()
        expected = {"workflow_id": str(uuid4()), "content_bytes_read": False}
        payload = {
            "organization_id": str(organization_id), "event_id": str(event_id),
            "items": [{
                "event_id": str(item_event_id), "source_type": "document",
                "source_uri": "controlled://document/1", "content_hash": "a" * 64,
                "captured_at": datetime.now(timezone.utc).isoformat(),
            }],
        }
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.ingest_onboarding_evidence_references", return_value=expected) as service:
            response = self.invoke(
                OnboardingEvidenceReferencesCreateView.as_view(), "post",
                "/v1/onboarding/document-references", payload,
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, expected)
        self.assertFalse(service.call_args.args[1]["items"][0].get("content_bytes"))

    def test_get_recommendations_supports_clause_filter(self):
        result = [{"id": str(uuid4()), "title": "Improve control"}]
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.list_recommendations", return_value=result) as service:
            response = self.invoke(RecommendationListView.as_view(), "get", "/v1/recommendations?clause=6.1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"results": result})
        self.assertEqual(service.call_args.kwargs["clause"], "6.1")

    def test_get_recommendation_basis_is_tenant_scoped_by_application_service(self):
        recommendation_id = uuid4()
        expected = {"recommendation_id": str(recommendation_id), "basis": []}
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.recommendation_basis", return_value=expected):
            response = self.invoke(
                RecommendationBasisView.as_view(), "get",
                f"/v1/recommendations/{recommendation_id}/basis",
                recommendation_id=recommendation_id,
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

    def test_post_approval_decision_calls_human_gate(self):
        decision_id = uuid4()
        outcome = SimpleNamespace(
            approval_id=uuid4(), decision="approve", event_id=uuid4(),
            outbox_id=uuid4(), audit_id=uuid4(),
        )
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.record_approval_decision", return_value=outcome) as service:
            response = self.invoke(
                ApprovalDecisionView.as_view(), "post",
                f"/v1/approvals/{decision_id}/decision",
                {"decision": "approve", "comments": "Reviewed"},
                decision_id=decision_id,
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["decision"], "approve")
        self.assertEqual(service.call_args.args[1], decision_id)

    def test_post_events_rejects_external_and_internal_only_event_types(self):
        response = self.invoke(
            DomainEventPublishView.as_view(), "post", "/v1/events",
            {"event_type": "payment.confirmed"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "REQUEST_INVALID")

    def test_post_events_requires_signed_publisher_scope(self):
        principal = SourceArtifactPrincipal(**{
            **PRINCIPAL.__dict__, "scopes": frozenset(),
        })
        payload = {
            "event_id": str(uuid4()),
            "event_type": "context.signal.detected",
            "aggregate_type": "context_item",
            "aggregate_id": str(uuid4()),
            "aggregate_version": 1,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "trace_id": str(TRACE_ID),
            "payload": {"signal": "captured"},
        }
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=principal):
            response = self.invoke(DomainEventPublishView.as_view(), "post", "/v1/events", payload)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "EVENT_PUBLISH_FORBIDDEN")

    def test_post_evidence_requires_hash_or_document_version(self):
        payload = {
            "organization_id": str(uuid4()),
            "source_type": "inspection",
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        response = self.invoke(EvidenceCreateView.as_view(), "post", "/v1/evidence", payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "REQUEST_INVALID")

    def test_post_evidence_persists_through_domain_service(self):
        outcome = SimpleNamespace(
            entity_id=uuid4(), aggregate_id=uuid4(), event_id=uuid4(),
            outbox_id=uuid4(), audit_id=uuid4(), trace_id=TRACE_ID,
        )
        payload = {
            "organization_id": str(uuid4()),
            "source_type": "inspection",
            "content_hash": "a" * 64,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.create_evidence", return_value=outcome):
            response = self.invoke(EvidenceCreateView.as_view(), "post", "/v1/evidence", payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["evidence_id"], str(outcome.entity_id))

    def test_post_foundation_attempt_returns_server_evaluated_result(self):
        path_id = uuid4()
        outcome = SimpleNamespace(
            attempt_id=uuid4(), learning_path_id=path_id, standard_edition_id=uuid4(),
            score=Decimal("100.00"), passed=True, weak_concepts=(), feedback=(),
            provenance_hash="b" * 64, event_id=uuid4(), outbox_id=uuid4(),
            audit_id=uuid4(), completed_at=datetime.now(timezone.utc),
        )
        payload = {
            "learning_path_id": str(path_id),
            "answers": [{"question_id": str(uuid4()), "selected_option_ids": ["yes"]}],
        }
        with patch("foundation.api_views.resolve_source_artifact_principal", return_value=PRINCIPAL), \
             patch("foundation.api_views.submit_foundation_attempt", return_value=outcome):
            response = self.invoke(
                FoundationAttemptCreateView.as_view(), "post",
                "/v1/learning/iso9000/attempts", payload,
            )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["passed"])
        self.assertEqual(response.data["score"], "100.00")

    def test_unauthenticated_request_is_rejected(self):
        response = OnboardingStatusView.as_view()(
            self.factory.get("/v1/onboarding/status"),
        )
        self.assertEqual(response.status_code, 401)
