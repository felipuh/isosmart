from contextlib import nullcontext
from unittest.mock import Mock, patch
from uuid import uuid4

import requests
from django.test import SimpleTestCase, override_settings

from foundation.qms_organization import QmsOrganizationCommandService
from foundation.tenant_context import TrustedTenantIdentity
from integration.client import AdminAppsClient


class AdminAppsEndpointRemediationTests(SimpleTestCase):
    def _client(self, base_url):
        return override_settings(
            ADMIN_APPS_INTEGRATION={
                'BASE_URL': base_url,
                'API_KEY': 'test-key',
                'TIMEOUT': 1,
            },
            ALLOW_LOCAL_AUTH_FALLBACK=False,
            IS_PRODUCTION=False,
        )

    @patch('integration.client.requests.get')
    def test_run_specific_dynamic_endpoint_is_used_for_entitlement(self, get):
        response = Mock()
        response.json.return_value = {'allowed': True}
        response.raise_for_status.return_value = None
        get.return_value = response

        with self._client('http://127.0.0.1:41491/api/integration'):
            result = AdminAppsClient().validate_product_access('tenant-1', 'ISO_SMART', use_cache=False)

        self.assertTrue(result['allowed'])
        self.assertEqual(
            get.call_args.args[0],
            'http://127.0.0.1:41491/api/integration/organizations/tenant-1/products/ISO_SMART/validate/',
        )

    @patch('integration.client.requests.get')
    def test_run_specific_endpoint_overrides_localhost_default(self, get):
        response = Mock()
        response.json.return_value = {'allowed': True}
        response.raise_for_status.return_value = None
        get.return_value = response

        with self._client('http://127.0.0.1:49123/api/integration'):
            AdminAppsClient().validate_product_access('tenant-1', 'ISO_SMART', use_cache=False)

        self.assertNotIn('8000', get.call_args.args[0])
        self.assertIn('49123', get.call_args.args[0])

    @override_settings(ADMIN_APPS_INTEGRATION={'API_KEY': 'test-key'})
    def test_missing_endpoint_fails_closed(self):
        result = AdminAppsClient().validate_product_access('tenant-1', 'ISO_SMART', use_cache=False)

        self.assertFalse(result['allowed'])
        self.assertEqual(result['source'], 'fail_closed')
        self.assertEqual(result['reason'], 'invalid_adminapps_endpoint')

    @override_settings(
        ADMIN_APPS_INTEGRATION={'BASE_URL': 'not-a-url', 'API_KEY': 'test-key'},
        ALLOW_LOCAL_AUTH_FALLBACK=False,
        IS_PRODUCTION=False,
    )
    def test_malformed_endpoint_fails_closed_without_local_fallback(self):
        result = AdminAppsClient().validate_product_access('tenant-1', 'ISO_SMART', use_cache=False)

        self.assertFalse(result['allowed'])
        self.assertEqual(result['source'], 'fail_closed')
        self.assertFalse(result['fallback'])

    @patch('integration.client.requests.get')
    def test_unreachable_endpoint_fails_closed(self, get):
        get.side_effect = requests.exceptions.ConnectionError('unreachable')

        with self._client('http://127.0.0.1:49123/api/integration'):
            result = AdminAppsClient().validate_product_access('tenant-1', 'ISO_SMART', use_cache=False)

        self.assertFalse(result['allowed'])
        self.assertEqual(result['source'], 'fail_closed')

    @patch('integration.client.requests.get')
    def test_denied_entitlement_is_preserved(self, get):
        response = Mock()
        response.json.return_value = {'allowed': False, 'reason': 'product_not_entitled'}
        response.raise_for_status.return_value = None
        get.return_value = response

        with self._client('http://127.0.0.1:49123/api/integration'):
            result = AdminAppsClient().validate_product_access('tenant-1', 'ISO_SMART', use_cache=False)

        self.assertFalse(result['allowed'])
        self.assertEqual(result['source'], 'adminapps')
        self.assertEqual(result['reason'], 'product_not_entitled')

    @patch('integration.client.requests.get')
    def test_allowed_entitlement_is_returned(self, get):
        response = Mock()
        response.json.return_value = {'allowed': True, 'product': {'billing_status': 'active'}}
        response.raise_for_status.return_value = None
        get.return_value = response

        with self._client('http://127.0.0.1:49123/api/integration'):
            result = AdminAppsClient().validate_product_access('tenant-1', 'ISO_SMART', use_cache=False)

        self.assertTrue(result['allowed'])
        self.assertEqual(result['source'], 'adminapps')

    @patch('foundation.qms_organization.AuditWriterService')
    @patch('foundation.qms_organization.TransactionalOutbox')
    @patch('foundation.qms_organization.DomainEvent')
    @patch('foundation.qms_organization.Organization')
    @patch('foundation.qms_organization.connections')
    @patch('foundation.qms_organization.TenantProjection')
    @patch('foundation.qms_organization.trusted_tenant_context')
    def test_allowed_entitlement_allows_qms_creation(
        self, trusted_context, tenant_projection, connections, organization,
        domain_event, outbox, audit_writer,
    ):
        tenant_id = uuid4()
        actor_id = uuid4()
        tenant = Mock(lifecycle_status='active', adminapps_tenant_id=tenant_id)
        tenant_projection.objects.using.return_value.get.return_value = tenant
        created = Mock(id=uuid4())
        organization.objects.using.return_value.create.return_value = created
        outbox.Status.PENDING = 'pending'
        outbox.objects.using.return_value.create.return_value = Mock(id=uuid4())
        audit_writer.return_value.append.return_value = uuid4()
        cursor = Mock()
        cursor.fetchone.return_value = None
        connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = cursor
        trusted_context.return_value = nullcontext()
        authority = Mock()
        authority.validate_product_access.return_value = {
            'allowed': True, 'source': 'adminapps', 'fallback': False,
        }
        authority.get_user.return_value = {
            'id': str(actor_id), 'is_active': True,
            'organizations': [{'id': str(tenant_id), 'role': 'admin'}],
        }

        service = QmsOrganizationCommandService(using='app', authority=authority)
        result = service.create_organization(
            identity=TrustedTenantIdentity('subject', tenant_id),
            display_name='QMS', actor_id=actor_id, trace_id=uuid4(), request_key=uuid4(),
        )

        self.assertEqual(result.organization_id, created.id)
        authority.validate_product_access.assert_called_once_with(
            str(tenant_id), 'ISO_SMART', use_cache=False, allow_local_fallback=False,
        )