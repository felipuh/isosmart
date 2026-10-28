from django.test import Client, SimpleTestCase, override_settings


class LivenessEndpointTests(SimpleTestCase):
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_liveness_is_public_minimal_and_not_redirected_to_https(self):
        response = Client().get('/livez')

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')

    def test_authenticated_readiness_and_business_api_remain_protected(self):
        client = Client()
        secure_request = {'HTTP_X_FORWARDED_PROTO': 'https'}

        self.assertEqual(client.get('/health', **secure_request).status_code, 401)
        self.assertEqual(client.get('/api/auth/me/', **secure_request).status_code, 401)
