import importlib
import inspect

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
