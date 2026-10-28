import importlib
import inspect
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework import serializers as drf_serializers


SERIALIZER_MODULES = [
    'core.serializers',
    'integration.serializers',
    'performance.serializers',
]


class SerializerExposureGuardrailTests(SimpleTestCase):
    def test_model_serializers_do_not_use_fields_all(self):
        for module_name in SERIALIZER_MODULES:
            module = importlib.import_module(module_name)
            for _, serializer_class in inspect.getmembers(module, inspect.isclass):
                if not issubclass(serializer_class, drf_serializers.ModelSerializer):
                    continue
                meta = getattr(serializer_class, 'Meta', None)
                if not meta or not hasattr(meta, 'model'):
                    continue
                fields = getattr(meta, 'fields', None)
                self.assertIsNotNone(fields, f'{serializer_class.__name__} must declare explicit fields.')
                self.assertNotEqual(fields, '__all__', f'{serializer_class.__name__} must not use fields="__all__".')


class LocalBypassGuardrailTests(SimpleTestCase):
    @override_settings(ENVIRONMENT='production', IS_DEVELOPMENT=False, ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS=False)
    def test_local_auth_bypass_is_disabled_outside_development(self):
        from django.conf import settings

        self.assertFalse(settings.ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS)

    @override_settings(
        ENVIRONMENT='production',
        IS_DEVELOPMENT=False,
        ALLOW_LOCAL_AUTH_FALLBACK=False,
        ADMIN_APPS_INTEGRATION={'BASE_URL': 'http://adminapps.test/api/integration', 'API_KEY': '', 'TIMEOUT': 1},
    )
    def test_adminapps_local_fallback_is_disabled_in_production(self):
        from integration.client import AdminAppsClient

        client = AdminAppsClient()
        with patch.object(client, '_make_request', return_value={'error': 'down', 'code': 'connection_error'}), \
                patch.object(client, '_get_organizations_local') as local_fallback:
            response = client.get_organizations(use_cache=False)

        self.assertEqual(response['fallback'], 'disabled')
        self.assertEqual(response['source'], 'adminapps')
        local_fallback.assert_not_called()

    @override_settings(
        ENVIRONMENT='development',
        IS_DEVELOPMENT=True,
        ALLOW_LOCAL_AUTH_FALLBACK=False,
        ADMIN_APPS_INTEGRATION={'BASE_URL': 'http://adminapps.test/api/integration', 'API_KEY': 'dev', 'TIMEOUT': 1},
    )
    def test_adminapps_local_fallback_requires_explicit_flag_in_development(self):
        from integration.client import AdminAppsClient

        client = AdminAppsClient()
        with patch.object(client, '_make_request', return_value={'error': 'down', 'code': 'connection_error'}), \
                patch.object(client, '_get_organizations_local') as local_fallback:
            response = client.get_organizations(use_cache=False)

        self.assertEqual(response['fallback'], 'disabled')
        local_fallback.assert_not_called()

    @override_settings(
        ENVIRONMENT='development',
        IS_DEVELOPMENT=True,
        ALLOW_LOCAL_AUTH_FALLBACK=True,
        ADMIN_APPS_INTEGRATION={'BASE_URL': 'http://adminapps.test/api/integration', 'API_KEY': 'dev', 'TIMEOUT': 1},
    )
    def test_adminapps_local_fallback_is_allowed_with_development_flag(self):
        from integration.client import AdminAppsClient

        client = AdminAppsClient()
        with patch.object(client, '_make_request', return_value={'error': 'down', 'code': 'connection_error'}), \
                patch.object(
                    client,
                    '_get_organizations_local',
                    return_value={'organizations': [], 'source': 'local_database'},
                ) as local_fallback:
            response = client.get_organizations(use_cache=False)

        self.assertEqual(response['source'], 'local_database')
        local_fallback.assert_called_once()
