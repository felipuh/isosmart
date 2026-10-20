from types import SimpleNamespace
from unittest import TestCase
from uuid import uuid4

from django.utils import timezone

from foundation.ai_usage import normalize_usage, serialize_for_adminapps


class AIUsageNormalizationTests(TestCase):
    def test_only_complete_provider_usage_is_authoritative(self):
        self.assertEqual(normalize_usage({'prompt_tokens': 10, 'completion_tokens': 4, 'total_tokens': 14}), {
            'input_tokens': 10, 'output_tokens': 4, 'total_tokens': 14, 'cached_input_tokens': None,
        })
        self.assertIsNone(normalize_usage({'prompt_tokens': 10}))
        self.assertIsNone(normalize_usage({'prompt_tokens': 10, 'completion_tokens': 4, 'total_tokens': 9}))

    def test_adminapps_contract_excludes_prompt_response_and_credentials(self):
        record = SimpleNamespace(id=uuid4(), adminapps_tenant_id=uuid4(), execution_id=uuid4(), correlation_id=uuid4(),
            product_identifier='iso-smart', agent_name='value-discovery', capability_name='purpose_alignment',
            provider='openai-compatible-chat-completions', model_identifier='gpt-4o-mini', created_at=timezone.now(),
            attempt_status='completed', usage_status='reported', input_tokens=10, output_tokens=4, total_tokens=14,
            cost_status='unpriced', estimated_provider_cost=None, currency=None)
        payload = serialize_for_adminapps(record, usage_event_id=uuid4())
        self.assertNotIn('prompt', payload)
        self.assertNotIn('response', payload)
        self.assertNotIn('api_key', payload)
        self.assertEqual(payload['total_tokens'], 14)
