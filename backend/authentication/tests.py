from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
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

    def test_password_reset_confirm_rejects_recent_password_reuse(self):
        self.user.password_history = [self.user.password]
        self.user.set_password('AnotherStrongPass@123')
        self.user.save(update_fields=['password', 'password_history'])
        reset_token, raw_token = PasswordResetToken.issue_for_user(self.user)

        response = self.client.post(
            reverse('authentication:password-reset-confirm'),
            {
                'selector': reset_token.selector,
                'token': raw_token,
                'new_password': 'StrongPass@123',
                'confirm_password': 'StrongPass@123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('reciente', str(response.data.get('detail', '')).lower())


@override_settings(LOGIN_MAX_ATTEMPTS=3, LOGIN_LOCKOUT_MINUTES=15)
class LoginLockoutTests(TestCase):
    """Verify brute-force lockout: counter increments on failures and resets on success."""

    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='lockme@isosmart.local',
            password='StrongPass@123',
            first_name='Lock',
            last_name='Test',
        )
        self.org = Organization.objects.create(
            name='Lock Org', slug='lock-org', email='lock@org.com'
        )
        UserProfile.objects.create(
            user=self.user, organization=self.org, role='user', is_active=True
        )
        self.url = reverse('authentication:login')

    def _bad_login(self):
        return self.client.post(
            self.url,
            {'email': self.user.email, 'password': 'WrongPass!'},
            format='json',
        )

    def test_failed_attempt_increments_counter(self):
        self._bad_login()
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)

    def test_account_locks_after_max_attempts(self):
        for _ in range(3):
            self._bad_login()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
        self.assertIsNotNone(self.user.account_locked_until)

    def test_locked_account_rejected_even_with_correct_password(self):
        for _ in range(3):
            self._bad_login()
        response = self.client.post(
            self.url,
            {'email': self.user.email, 'password': 'StrongPass@123'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_successful_login_resets_failed_counter(self):
        self._bad_login()  # 1 failed attempt
        self.client.post(
            self.url,
            {'email': self.user.email, 'password': 'StrongPass@123'},
            format='json',
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertIsNone(self.user.account_locked_until)

    def test_expired_lockout_allows_login(self):
        from django.utils import timezone
        from datetime import timedelta

        self.user.account_locked_until = timezone.now() - timedelta(seconds=1)
        self.user.failed_login_attempts = 5
        self.user.save()
        response = self.client.post(
            self.url,
            {'email': self.user.email, 'password': 'StrongPass@123'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)


@override_settings(PASSWORD_HISTORY_COUNT=5)
class PasswordReusePolicyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='reuse@isosmart.local',
            password='StrongPass@123',
            first_name='Reuse',
            last_name='Policy',
        )
        self.org = Organization.objects.create(
            name='Reuse Org',
            slug='reuse-org',
            email='reuse@org.com',
        )
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            role='org_admin',
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_rejects_recent_reuse(self):
        self.user.password_history = [self.user.password]
        self.user.set_password('AnotherStrongPass@123')
        self.user.save(update_fields=['password', 'password_history'])

        response = self.client.post(
            reverse('authentication:change-password'),
            {
                'current_password': 'AnotherStrongPass@123',
                'new_password': 'StrongPass@123',
                'confirm_password': 'StrongPass@123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('reciente', str(response.data.get('detail', '')).lower())
        self.assertEqual(response.data.get('reason_code'), 'PASSWORD_REUSE_RECENT')


@override_settings(TEMP_PASSWORD_MAX_AGE_DAYS=7, TEMP_PASSWORD_WARNING_DAYS=2)
class TemporaryPasswordLoginPolicyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='temp-password@isosmart.local',
            password='StrongPass@123',
            first_name='Temp',
            last_name='Password',
        )
        self.org = Organization.objects.create(
            name='Temp Org',
            slug='temp-org',
            email='temp-org@isosmart.local',
        )
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            role='user',
            is_active=True,
        )
        self.login_url = reverse('authentication:login')

    def test_login_rejects_expired_temporary_password(self):
        self.user.must_change_password = True
        self.user.temporary_password_set_at = timezone.now() - timedelta(days=8)
        self.user.save(update_fields=['must_change_password', 'temporary_password_set_at'])

        response = self.client.post(
            self.login_url,
            {'email': self.user.email, 'password': 'StrongPass@123'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('TEMP_PASSWORD_EXPIRED', str(response.data.get('reason_code')))

    def test_login_includes_warning_for_soon_expiring_temporary_password(self):
        self.user.must_change_password = True
        self.user.temporary_password_set_at = timezone.now() - timedelta(days=6)
        self.user.save(update_fields=['must_change_password', 'temporary_password_set_at'])

        response = self.client.post(
            self.login_url,
            {'email': self.user.email, 'password': 'StrongPass@123'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('security_alert', response.data)
        self.assertEqual(response.data['security_alert'].get('reason_code'), 'TEMP_PASSWORD_EXPIRING')