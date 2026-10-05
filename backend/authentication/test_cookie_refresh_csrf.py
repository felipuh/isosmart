from django.test import Client, SimpleTestCase


class RefreshCookieCsrfTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.cookies['isosmart_refresh'] = 'synthetic-invalid-refresh'

    def test_refresh_cookie_without_csrf_is_rejected(self):
        response = self.client.post('/api/auth/refresh/')

        self.assertEqual(response.status_code, 403)

    def test_refresh_cookie_with_invalid_csrf_is_rejected(self):
        self.client.cookies['csrftoken'] = 'a' * 32

        response = self.client.post(
            '/api/auth/refresh/',
            HTTP_X_CSRFTOKEN='b' * 32,
        )

        self.assertEqual(response.status_code, 403)

    def test_valid_csrf_reaches_refresh_token_validation(self):
        self.client.get('/api/auth/csrf/')
        csrf_token = self.client.cookies['csrftoken'].value

        response = self.client.post(
            '/api/auth/refresh/',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['detail'], 'Token inválido o expirado.')
