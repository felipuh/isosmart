from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import PasswordResetToken, UserProfile
from core.models import Organization


@override_settings(DEBUG=True, FRONTEND_BASE_URL='http://localhost:5173')
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='recovery@isosmart.local',
            password='StrongPass@123',
            first_name='Recovery',
            last_name='User',
        )
        self.organization = Organization.objects.create(
            name='Recovery Org',
            slug='recovery-org',
            email='recovery-org@isosmart.local',
        )
        UserProfile.objects.create(
            user=self.user,
            organization=self.organization,
            role='org_admin',
            is_active=True,
        )

    def test_password_reset_request_creates_token_and_sends_email(self):
        response = self.client.post(
            reverse('authentication:password-reset-request'),
            {'email': self.user.email},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PasswordResetToken.objects.filter(user=self.user).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/reset-password?selector=', mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        self.assertEqual(mail.outbox[0].alternatives[0][1], 'text/html')

    def test_password_reset_request_returns_debug_url_only_in_debug_mode(self):
        response = self.client.post(
            reverse('authentication:password-reset-request'),
            {'email': self.user.email},
            format='json',
            HTTP_X_DEBUG_RECOVERY='1',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('debug_reset_url', response.data)
        self.assertIn('/reset-password?selector=', response.data['debug_reset_url'])

    def test_password_reset_request_does_not_reveal_missing_email(self):
        response = self.client.post(
            reverse('authentication:password-reset-request'),
            {'email': 'missing@isosmart.local'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PasswordResetToken.objects.count(), 1)
        self.assertIsNone(PasswordResetToken.objects.first().user)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_updates_password_and_invalidates_token(self):
        reset_token, raw_token = PasswordResetToken.issue_for_user(self.user)

        response = self.client.post(
            reverse('authentication:password-reset-confirm'),
            {
                'selector': reset_token.selector,
                'token': raw_token,
                'new_password': 'NewStrongPass@123',
                'confirm_password': 'NewStrongPass@123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        reset_token.refresh_from_db()
        self.assertIsNotNone(reset_token.used_at)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass@123'))

    def test_password_reset_confirm_rejects_invalid_token(self):
        reset_token, _raw_token = PasswordResetToken.issue_for_user(self.user)

        response = self.client.post(
            reverse('authentication:password-reset-confirm'),
            {
                'selector': reset_token.selector,
                'token': 'invalid-token',
                'new_password': 'NewStrongPass@123',
                'confirm_password': 'NewStrongPass@123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)