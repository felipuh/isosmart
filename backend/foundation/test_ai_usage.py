from types import SimpleNamespace
from contextlib import nullcontext
from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from django.utils import timezone

from foundation.ai_usage import normalize_usage, serialize_for_adminapps, usage_event_id_for
from foundation.ai_usage_delivery import (
    AIUsageDelivery,
    PERMANENT_REJECTION,
    RETRY_EXHAUSTED,
    delivery_failure_kind,
    retry_cycle_exhausted,
)


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

    def test_usage_event_identity_is_stable_and_delivery_classifies_errors_safely(self):
        record_id = uuid4()
        self.assertEqual(usage_event_id_for(record_id), usage_event_id_for(record_id))
        self.assertNotEqual(usage_event_id_for(record_id), usage_event_id_for(uuid4()))
        self.assertEqual(delivery_failure_kind(401), 'permanent')
        self.assertEqual(delivery_failure_kind(422), 'permanent')
        self.assertEqual(delivery_failure_kind(503), 'retryable')
        self.assertEqual(delivery_failure_kind(None), 'retryable')
        self.assertNotEqual(RETRY_EXHAUSTED, PERMANENT_REJECTION)

    def test_retry_exhaustion_is_bounded_per_authorized_cycle_without_erasing_history(self):
        self.assertTrue(retry_cycle_exhausted(publish_attempts=2, max_attempts=2))
        self.assertFalse(retry_cycle_exhausted(publish_attempts=3, max_attempts=2))
        self.assertTrue(retry_cycle_exhausted(publish_attempts=4, max_attempts=2))

    @patch('foundation.ai_usage_delivery.trusted_tenant_context', return_value=nullcontext())
    @patch('foundation.ai_usage_delivery.TransactionalOutbox.objects')
    def test_exhausted_503_is_recorded_for_recovery_not_as_a_permanent_rejection(self, objects, _context):
        objects.using.return_value.get.return_value = SimpleNamespace(publish_attempts=2)
        delivery = Mock()
        dispatcher = AIUsageDelivery(enabled=True, endpoint='http://loopback.test', api_key='synthetic', max_attempts=2)
        result = dispatcher._retryable(delivery, object(), uuid4(), 'worker', uuid4(), 503)
        self.assertEqual(result.state, 'RETRY_EXHAUSTED')
        self.assertEqual(result.status_code, 503)
        self.assertEqual(delivery.mark_failed.call_args.kwargs['error_code'], RETRY_EXHAUSTED)
        self.assertNotEqual(delivery.mark_failed.call_args.kwargs['error_code'], PERMANENT_REJECTION)
