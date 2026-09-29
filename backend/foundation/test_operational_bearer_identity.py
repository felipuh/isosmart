from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from core.services.health_service import HealthCheckError
from .operational_bearer_identity import OperationalBearerError, acquire_runtime_bearer


class OperationalBearerIdentityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="runtime-bearer@example.test", password=None, is_active=True
        )
        self.organization = SimpleNamespace(
            id="11111111-1111-4111-8111-111111111111",
            pk="11111111-1111-4111-8111-111111111111",
            code="UNIT",
            name="Unit Tenant",
            status="active",
        )
        self.membership = SimpleNamespace(
            user_id=self.user.pk, organization=self.organization, is_active=True, role="viewer"
        )
        self.entitlement = SimpleNamespace(
            organization_id=self.organization.id, access_allowed=True
        )

    def acquire(self):
        return acquire_runtime_bearer(
            self.user,
            self.membership,
            self.entitlement,
            token_class=AccessToken,
            issuer="https://sso.example.test",
            lifetime_seconds=900,
        )

    def test_existing_active_identity_gets_expected_subject_and_lifetime_without_password(self):
        self.assertFalse(self.user.has_usable_password())
        credential = self.acquire()
        raw = credential.authorization_value().split(" ", 1)[1]
        token = AccessToken(raw)
        self.assertEqual(str(token["user_id"]), str(self.user.pk))
        self.assertEqual(token["organization_id"], self.organization.id)
        self.assertEqual(token["role"], "viewer")
        self.assertEqual(token["exp"] - token["iat"], 900)
        self.assertEqual(credential.evidence()["token_persisted"], False)
        credential.destroy()
        with self.assertRaisesRegex(OperationalBearerError, "CREDENTIAL_DESTROYED"):
            credential.authorization_value()

    def test_missing_and_inactive_identities_fail_closed(self):
        with self.assertRaisesRegex(OperationalBearerError, "IDENTITY_NOT_FOUND"):
            acquire_runtime_bearer(None, self.membership, self.entitlement,
                                   token_class=AccessToken, issuer="https://sso.example.test")
        self.user.is_active = False
        with self.assertRaisesRegex(OperationalBearerError, "IDENTITY_INACTIVE"):
            self.acquire()

    def test_membership_and_tenant_binding_are_mandatory(self):
        mismatched = SimpleNamespace(
            user_id=999999, organization=self.organization, is_active=True, role="viewer"
        )
        with self.assertRaisesRegex(OperationalBearerError, "IDENTITY_BINDING_MISMATCH"):
            acquire_runtime_bearer(self.user, mismatched, self.entitlement,
                                   token_class=AccessToken, issuer="https://sso.example.test")
        self.entitlement.access_allowed = False
        with self.assertRaisesRegex(OperationalBearerError, "ENTITLEMENT_DENIED"):
            self.acquire()

    def test_repr_and_evidence_do_not_expose_raw_credential(self):
        credential = self.acquire()
        raw = credential.authorization_value().split(" ", 1)[1]
        rendered = repr(credential) + repr(credential.evidence())
        self.assertNotIn(raw, rendered)
        self.assertEqual(credential.evidence()["token_fingerprint"], credential.token_fingerprint)


class AuthenticatedReadinessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="readiness@example.test", password=None, is_active=True
        )
        self.client = APIClient()

    def authorize(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_valid_bearer_returns_200_and_missing_or_invalid_returns_401(self):
        self.authorize(AccessToken.for_user(self.user))
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.client.credentials()
        self.assertEqual(self.client.get("/health").status_code, 401)
        self.authorize("invalid.synthetic.token")
        self.assertEqual(self.client.get("/health").status_code, 401)

    def test_expired_bearer_fails(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=timedelta(seconds=-1))
        self.authorize(token)
        self.assertEqual(self.client.get("/health").status_code, 401)

    def test_database_failure_remains_503_for_authenticated_identity(self):
        from unittest.mock import patch

        self.authorize(AccessToken.for_user(self.user))
        with patch("core.views.check_database_connection", side_effect=HealthCheckError("database_unavailable")):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "database_unavailable")
