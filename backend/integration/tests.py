import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from authentication.models import UserProfile
from core.models import Organization
from integration.models import AssistantMemoryItem, AssistantOrgProfile
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

    def test_stream_fallback_when_provider_returns_401(self):
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
        self.assertEqual(done_payload.get('provider'), 'fallback')
        self.assertTrue(done_payload.get('error'))
        self.assertIsInstance(done_payload.get('conversation_id'), int)