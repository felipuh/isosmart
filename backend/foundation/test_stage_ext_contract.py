"""Stage EXT boundary checks that require no synthetic database rows."""

import hashlib
from uuid import uuid4

from django.test import RequestFactory, SimpleTestCase, override_settings

from foundation.adminapps_ingress import receive_tenant_event
from foundation.projection_contract import ContractValidationError, validate_projection_event
from foundation.qms_organization import QmsOrganizationCommandService


class TenantContractTests(SimpleTestCase):
    def test_invalid_status_mapping_is_rejected_before_projection(self):
        tenant_id = uuid4()
        event = {
            'event_id': str(uuid4()), 'event_type': 'tenant.provisioned',
            'schema_version': 1, 'source': 'adminapps', 'source_version': 1,
            'occurred_at': '2026-09-18T00:00:00+00:00', 'trace_id': str(uuid4()),
            'aggregate_type': 'tenant', 'aggregate_id': str(tenant_id),
            'adminapps_tenant_id': str(tenant_id),
            'payload': {'display_name': 'Tenant', 'adminapps_status': 'suspended',
                        'lifecycle_status': 'active'},
        }
        with self.assertRaises(ContractValidationError):
            validate_projection_event(event)

    @override_settings(ADMINAPPS_TENANT_EVENT_KEY_SHA256=hashlib.sha256(b'correct').hexdigest())
    def test_service_ingress_denies_missing_or_wrong_key_before_database(self):
        factory = RequestFactory()
        missing = factory.post('/api/integration/adminapps/tenant-events/', '{}', content_type='application/json')
        wrong = factory.post('/api/integration/adminapps/tenant-events/', '{}',
                             content_type='application/json', HTTP_X_API_KEY='wrong')
        self.assertEqual(receive_tenant_event(missing).status_code, 401)
        self.assertEqual(receive_tenant_event(wrong).status_code, 401)

    def test_command_requires_trusted_identity(self):
        with self.assertRaises(TypeError):
            QmsOrganizationCommandService().create_organization(
                identity=object(), display_name='QMS', actor_id=uuid4(),
                trace_id=uuid4(), request_key=uuid4(),
            )
