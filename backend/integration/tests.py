import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from authentication.models import UserProfile
from core.models import Organization
from integration.models import (
    AssistantAuditLog,
    AssistantConversation,
    AssistantFeedback,
    AssistantMemoryItem,
    AssistantMessage,
    AssistantOrgProfile,
    AssistantPromptConfig,
)
from integration.views import _build_assistant_prompt


class _FakeStreamResponse:
    status_code = 200

    def iter_lines(self):
        yield 'data: {"choices": []}'
        yield 'data: {"choices": [{"delta": {"content": "Hola "}}]}'
        yield 'data: {"choices": [{"delta": {"content": "mundo"}}]}'
        yield 'data: [DONE]'


class _FakeStreamContext:
    def __init__(self, response):
        self.response = response

    def __enter__(self):
        return self.response

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeErrorResponse:
    status_code = 401

    def iter_lines(self):
        return iter(())


class AssistantApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()

        self.user = user_model.objects.create_user(
            email='assistant-tests@isosmart.local',
            password='StrongPass@123',
            first_name='Assistant',
            last_name='Tests',
        )
        self.organization = Organization.objects.create(
            name='Assistant Test Org',
            slug='assistant-test-org',
            email='assistant-test-org@isosmart.local',
        )
        UserProfile.objects.create(
            user=self.user,
            organization=self.organization,
            role='org_admin',
            is_active=True,
        )

        self.validate_credentials_patcher = patch('integration.client.admin_apps_client.validate_credentials')
        self.validate_product_access_patcher = patch('integration.client.admin_apps_client.validate_product_access')
        self.mock_validate_credentials = self.validate_credentials_patcher.start()
        self.mock_validate_product_access = self.validate_product_access_patcher.start()
        self.addCleanup(self.validate_credentials_patcher.stop)
        self.addCleanup(self.validate_product_access_patcher.stop)
        self.mock_validate_credentials.return_value = {
            'valid': True,
            'user': {
                'id': str(self.user.id),
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
            },
            'current_organization': {
                'id': str(self.organization.id),
                'name': self.organization.name,
                'slug': self.organization.slug,
                'is_active': True,
            },
            'organizations': [
                {
                    'id': str(self.organization.id),
                    'name': self.organization.name,
                    'slug': self.organization.slug,
                }
            ],
            'current_role': 'org_admin',
        }
        self.mock_validate_product_access.return_value = {
            'allowed': True,
            'reason': 'ok',
            'source': 'adminapps',
            'fallback': False,
            'billing_status': 'active',
            'product': {
                'code': 'ISO_SMART',
                'enabled': True,
                'access_allowed': True,
                'access_denial_reason': 'ok',
                'billing_status': 'active',
            },
        }

        login_response = self.client.post(
            '/api/auth/login/',
            {'email': self.user.email, 'password': 'StrongPass@123'},
            format='json',
        )
        self.assertEqual(login_response.status_code, 200)
        self.token = login_response.data['access']
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    def _parse_done_payload(self, response):
        body = ''.join(chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk for chunk in response.streaming_content)
        events = body.split('\n\n')
        for event in events:
            lines = event.split('\n')
            event_name = ''
            data = None
            for line in lines:
                if line.startswith('event:'):
                    event_name = line.split(':', 1)[1].strip()
                if line.startswith('data:'):
                    raw = line.split(':', 1)[1].strip()
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        data = None
            if event_name == 'done' and isinstance(data, dict):
                return data
        return None

    def test_assistant_state_returns_empty_when_no_conversation(self):
        response = self.client.get('/api/integration/assistant/state/', **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('conversation_id'), None)
        self.assertEqual(response.data.get('messages'), [])

    def test_stream_persists_conversation_and_state_returns_history(self):
        captured_payloads = []

        def fake_stream(_method, _url, headers=None, json=None, timeout=None):
            captured_payloads.append(json)
            return _FakeStreamContext(_FakeStreamResponse())

        with patch('integration.views.httpx.stream', side_effect=fake_stream), patch(
            'integration.views.AssistantVectorSearchService.search', return_value=[]
        ), patch.multiple(
            'integration.views.settings',
            AI_ASSISTANT_API_KEY='test-key',
            AI_ASSISTANT_API_URL='https://example.local/fake',
            AI_ASSISTANT_MODEL='gpt-4o-mini',
        ):
            first = self.client.post(
                '/api/integration/assistant/stream/',
                {
                    'question': 'Primera pregunta de prueba',
                    'route': '/leadership/policies',
                    'module': 'leadership',
                    'routeContext': {
                        'module': 'leadership',
                        'submodule': 'policies',
                        'pageLabel': 'politicas',
                        'clauseHints': ['5.1', '5.2'],
                        'primaryStandards': ['ISO 9001'],
                    },
                    'conversation': [],
                    'conversationId': None,
                },
                format='json',
                **self.auth_headers,
            )
            self.assertEqual(first.status_code, 200)
            first_done = self._parse_done_payload(first)
            self.assertIsNotNone(first_done)
            conversation_id = first_done.get('conversation_id')
            self.assertIsInstance(conversation_id, int)

            second = self.client.post(
                '/api/integration/assistant/stream/',
                {
                    'question': 'Segunda pregunta de prueba',
                    'route': '/leadership/policies',
                    'module': 'leadership',
                    'routeContext': {
                        'module': 'leadership',
                        'submodule': 'policies',
                        'pageLabel': 'politicas',
                        'clauseHints': ['5.2'],
                        'primaryStandards': ['ISO 9001'],
                    },
                    # Intencionalmente vacío: debe tomar historial de BD.
                    'conversation': [],
                    'conversationId': conversation_id,
                },
                format='json',
                **self.auth_headers,
            )
            self.assertEqual(second.status_code, 200)

        # Al menos una llamada debe haber llegado al proveedor remoto mockeado.
        self.assertGreaterEqual(len(captured_payloads), 1)

        state = self.client.get(
            f'/api/integration/assistant/state/?conversation_id={conversation_id}',
            **self.auth_headers,
        )
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.data.get('conversation_id'), conversation_id)
        self.assertGreaterEqual(len(state.data.get('messages', [])), 3)
        self.assertTrue(any('Primera pregunta de prueba' in m.get('content', '') for m in state.data.get('messages', [])))
        self.assertTrue(any('Segunda pregunta de prueba' in m.get('content', '') for m in state.data.get('messages', [])))
        roles = [m.get('role') for m in state.data.get('messages', [])]
        self.assertIn('user', roles)
        self.assertIn('assistant', roles)

    def test_prompt_builder_includes_org_profile_and_structured_memory(self):
        org_profile = AssistantOrgProfile(
            organization_id=self.organization.id,
            primary_standards=['ISO 9001'],
            industry='Servicios',
            risk_tolerance='media',
            organization_summary='Empresa orientada a calidad y cumplimiento.',
            preferred_response_style='pragmatic',
            forbidden_topics=['asesoria legal vinculante'],
        )
        memory_items = [
            {
                'title': 'Politica de calidad vigente',
                'content': 'La direccion revisa objetivos y comunica prioridades trimestralmente.',
                'module': 'leadership',
                'standard_code': 'ISO 9001',
                'clause_reference': '5.2',
            }
        ]
        system_prompt = _build_assistant_prompt(
            base_prompt='Base prompt',
            module_name='leadership',
            route='/leadership/policies',
            route_context={
                'module': 'leadership',
                'submodule': 'policies',
                'pageLabel': 'politicas',
                'clauseHints': ['5.2'],
                'primaryStandards': ['ISO 9001'],
            },
            question='Que debemos reforzar en liderazgo?',
            org_id=self.organization.id,
            profile_role='org_admin',
            rag_chunks=[],
            org_profile=org_profile,
            memory_items=memory_items,
        )
        self.assertIn('Contexto persistente de la organizacion', system_prompt)
        self.assertIn('Memoria estructurada relevante de la organizacion', system_prompt)
        self.assertIn('Politica de calidad vigente', system_prompt)

    def test_stream_reports_degraded_when_provider_returns_401(self):
        def fake_stream(_method, _url, headers=None, json=None, timeout=None):
            return _FakeStreamContext(_FakeErrorResponse())

        with patch('integration.views.httpx.stream', side_effect=fake_stream), patch.multiple(
            'integration.views.settings',
            AI_ASSISTANT_API_KEY='test-key',
            AI_ASSISTANT_API_URL='https://example.local/fake',
            AI_ASSISTANT_MODEL='gpt-4o-mini',
        ):
            response = self.client.post(
                '/api/integration/assistant/stream/',
                {
                    'question': 'Necesito apoyo con liderazgo',
                    'route': '/leadership/policies',
                    'module': 'leadership',
                    'routeContext': {
                        'module': 'leadership',
                        'submodule': 'policies',
                        'pageLabel': 'politicas',
                        'clauseHints': ['5.2'],
                        'primaryStandards': ['ISO 9001'],
                    },
                    'conversation': [],
                },
                format='json',
                **self.auth_headers,
            )

        self.assertEqual(response.status_code, 200)
        done_payload = self._parse_done_payload(response)
        self.assertIsNotNone(done_payload)
        self.assertEqual(done_payload.get('provider'), 'unavailable')
        self.assertTrue(done_payload.get('degraded'))
        self.assertFalse(done_payload.get('ok'))
        self.assertTrue(done_payload.get('error'))
        self.assertIsInstance(done_payload.get('conversation_id'), int)

        degraded_message = AssistantMessage.objects.filter(
            conversation_id=done_payload['conversation_id'],
            role='assistant',
        ).latest('id')
        self.assertEqual(degraded_message.model_name, 'degraded')
        self.assertIn('No se generó ninguna recomendación ni análisis normativo', degraded_message.content)
        self.assertNotIn('Consulta recibida', degraded_message.content)

    @patch('integration.assistant_memory_views.queue_memory_item_index')
    def test_memory_items_ignore_payload_tenant_and_hide_cross_tenant_objects(self, _queue_index):
        other_org = Organization.objects.create(
            name='Other Tenant',
            slug='other-tenant',
            email='other-tenant@isosmart.local',
        )
        foreign_item = AssistantMemoryItem.objects.create(
            organization_id=other_org.id,
            memory_type='fact',
            title='Tenant B private memory',
            content='Private B content',
        )

        created = self.client.post(
            '/api/integration/assistant/memory-items/',
            {
                'organization_id': other_org.id,
                'memory_type': 'fact',
                'title': 'Tenant A memory',
                'content': 'Tenant A content',
            },
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(created.status_code, 201)
        created_item = AssistantMemoryItem.objects.get(id=created.data['id'])
        self.assertEqual(created_item.organization_id, self.organization.id)

        updated = self.client.patch(
            f'/api/integration/assistant/memory-items/{created_item.id}/',
            {'organization_id': other_org.id, 'title': 'Still Tenant A'},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(updated.status_code, 200)
        created_item.refresh_from_db()
        self.assertEqual(created_item.organization_id, self.organization.id)

        listed = self.client.get('/api/integration/assistant/memory-items/', **self.auth_headers)
        self.assertEqual(listed.status_code, 200)
        listed_ids = [item['id'] for item in listed.data['results']]
        self.assertIn(created_item.id, listed_ids)
        self.assertNotIn(foreign_item.id, listed_ids)

        detail_url = f'/api/integration/assistant/memory-items/{foreign_item.id}/'
        self.assertEqual(self.client.get(detail_url, **self.auth_headers).status_code, 404)
        self.assertEqual(
            self.client.patch(detail_url, {'title': 'attacker'}, format='json', **self.auth_headers).status_code,
            404,
        )
        self.assertEqual(self.client.delete(detail_url, **self.auth_headers).status_code, 404)
        foreign_item.refresh_from_db()
        self.assertEqual(foreign_item.title, 'Tenant B private memory')

    def test_prompt_feedback_and_audit_queries_are_tenant_scoped(self):
        other_org = Organization.objects.create(
            name='Scoped Tenant B',
            slug='scoped-tenant-b',
            email='scoped-tenant-b@isosmart.local',
        )
        own_conversation = AssistantConversation.objects.create(
            organization_id=self.organization.id,
            user=self.user,
            title='Tenant A conversation',
        )
        foreign_conversation = AssistantConversation.objects.create(
            organization_id=other_org.id,
            user=self.user,
            title='Tenant B private conversation',
        )
        own_message = AssistantMessage.objects.create(
            organization_id=self.organization.id,
            conversation=own_conversation,
            role='assistant',
            content='Tenant A message',
        )
        foreign_message = AssistantMessage.objects.create(
            organization_id=other_org.id,
            conversation=foreign_conversation,
            role='assistant',
            content='Tenant B private message',
        )
        foreign_prompt = AssistantPromptConfig.objects.create(
            organization_id=other_org.id,
            system_prompt='Tenant B private prompt',
        )
        foreign_feedback = AssistantFeedback.objects.create(
            organization_id=other_org.id,
            conversation=foreign_conversation,
            message=foreign_message,
            user=self.user,
            rating=5,
        )
        foreign_audit = AssistantAuditLog.objects.create(
            organization_id=other_org.id,
            user=self.user,
            conversation=foreign_conversation,
            event_type='private_b_event',
        )

        resources = [
            ('prompt-configs', foreign_prompt),
            ('feedback', foreign_feedback),
            ('audit-logs', foreign_audit),
        ]
        for resource, foreign_object in resources:
            with self.subTest(resource=resource):
                collection_url = f'/api/integration/assistant/{resource}/'
                detail_url = f'{collection_url}{foreign_object.id}/'
                listed = self.client.get(collection_url, **self.auth_headers)
                self.assertEqual(listed.status_code, 200)
                self.assertNotIn(foreign_object.id, [item['id'] for item in listed.data['results']])
                self.assertEqual(self.client.get(detail_url, **self.auth_headers).status_code, 404)
                if resource != 'audit-logs':
                    self.assertEqual(
                        self.client.patch(detail_url, {'rating': 1}, format='json', **self.auth_headers).status_code,
                        404,
                    )
                    self.assertEqual(self.client.delete(detail_url, **self.auth_headers).status_code, 404)

        own_feedback = self.client.post(
            '/api/integration/assistant/feedback/',
            {
                'organization_id': other_org.id,
                'conversation': own_conversation.id,
                'message': own_message.id,
                'rating': 4,
            },
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(own_feedback.status_code, 201)
        self.assertEqual(
            AssistantFeedback.objects.get(id=own_feedback.data['id']).organization_id,
            self.organization.id,
        )

    def test_feedback_cross_tenant_and_missing_references_are_indistinguishable(self):
        other_org = Organization.objects.create(
            name='Reference Tenant B',
            slug='reference-tenant-b',
            email='reference-tenant-b@isosmart.local',
        )
        own_conversation = AssistantConversation.objects.create(
            organization_id=self.organization.id,
            user=self.user,
            title='Own conversation',
        )
        foreign_conversation = AssistantConversation.objects.create(
            organization_id=other_org.id,
            user=self.user,
            title='Foreign conversation',
        )
        foreign_message = AssistantMessage.objects.create(
            organization_id=other_org.id,
            conversation=foreign_conversation,
            role='assistant',
            content='Foreign private content',
        )

        conversation_payload = {'conversation': foreign_conversation.id, 'rating': 3}
        foreign_conversation_response = self.client.post(
            '/api/integration/assistant/feedback/',
            conversation_payload,
            format='json',
            **self.auth_headers,
        )
        missing_conversation_response = self.client.post(
            '/api/integration/assistant/feedback/',
            {'conversation': 99999999, 'rating': 3},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(foreign_conversation_response.status_code, 400)
        self.assertEqual(missing_conversation_response.status_code, 400)
        self.assertEqual(foreign_conversation_response.data, missing_conversation_response.data)

        foreign_message_response = self.client.post(
            '/api/integration/assistant/feedback/',
            {'conversation': own_conversation.id, 'message': foreign_message.id, 'rating': 3},
            format='json',
            **self.auth_headers,
        )
        missing_message_response = self.client.post(
            '/api/integration/assistant/feedback/',
            {'conversation': own_conversation.id, 'message': 99999999, 'rating': 3},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(foreign_message_response.status_code, 400)
        self.assertEqual(missing_message_response.status_code, 400)
        self.assertEqual(foreign_message_response.data, missing_message_response.data)
        self.assertNotIn(other_org.name, str(foreign_message_response.data))

    def test_assistant_audit_log_api_is_read_only_but_internal_emission_remains_available(self):
        conversation = AssistantConversation.objects.create(
            organization_id=self.organization.id,
            user=self.user,
            title='Audited conversation',
        )
        internal_log = AssistantAuditLog.objects.create(
            organization_id=self.organization.id,
            user=self.user,
            conversation=conversation,
            event_type='internal_test_event',
        )
        collection_url = '/api/integration/assistant/audit-logs/'
        detail_url = f'{collection_url}{internal_log.id}/'

        self.assertEqual(self.client.get(collection_url, **self.auth_headers).status_code, 200)
        self.assertEqual(self.client.get(detail_url, **self.auth_headers).status_code, 200)
        self.assertEqual(
            self.client.post(collection_url, {'event_type': 'client_event'}, format='json', **self.auth_headers).status_code,
            405,
        )
        self.assertEqual(
            self.client.put(detail_url, {'event_type': 'changed'}, format='json', **self.auth_headers).status_code,
            405,
        )
        self.assertEqual(
            self.client.patch(detail_url, {'event_type': 'changed'}, format='json', **self.auth_headers).status_code,
            405,
        )
        self.assertEqual(self.client.delete(detail_url, **self.auth_headers).status_code, 405)
        internal_log.refresh_from_db()
        self.assertEqual(internal_log.event_type, 'internal_test_event')
