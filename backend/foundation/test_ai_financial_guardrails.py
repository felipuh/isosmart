from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from foundation.ai_financial_guardrails import FinancialAdmissionDenied, worst_case_cost
from foundation.ai_usage import (
    AIFinancialGuardrailBlocked, assert_paid_provider_admission,
    run_metered_capability,
)


class FinancialGuardrailUnitTests(TestCase):
    def test_decimal_worst_case_cost_includes_input_and_maximum_output(self):
        pricing = SimpleNamespace(
            input_token_rate=Decimal("0.1500000000"),
            output_token_rate=Decimal("0.6000000000"),
            rate_unit=1_000_000,
        )
        self.assertEqual(
            worst_case_cost(pricing=pricing, input_tokens=1000, output_tokens=2000),
            Decimal("0.0013500000"),
        )

    @patch("foundation.ai_usage.settings")
    def test_real_provider_is_rejected_before_any_provider_invocation(self, settings):
        settings.AI_REAL_INFERENCE_AUTHORIZED = False
        provider = SimpleNamespace(execution_mode="REAL_AI")
        with self.assertRaises(AIFinancialGuardrailBlocked) as raised:
            assert_paid_provider_admission(provider)
        self.assertEqual(raised.exception.code, "AI_REAL_INFERENCE_NOT_AUTHORIZED")

    @patch("foundation.ai_usage.settings")
    def test_common_execution_path_rejects_before_ledger_or_provider(self, settings):
        settings.AI_REAL_INFERENCE_AUTHORIZED = False
        provider = Mock(execution_mode="REAL_AI")
        ledger = Mock()
        with self.assertRaises(AIFinancialGuardrailBlocked):
            run_metered_capability(
                ledger=ledger, capability="test", provider=provider, context={},
                validate=lambda value: value, invocation_id="synthetic-request",
            )
        ledger.reserve.assert_not_called()
        provider.analyze.assert_not_called()

    @patch("foundation.ai_usage.settings")
    def test_authorized_switch_still_fails_closed_without_central_authority_contract(self, settings):
        settings.AI_REAL_INFERENCE_AUTHORIZED = True
        provider = SimpleNamespace(execution_mode="REAL_AI")
        with self.assertRaises(AIFinancialGuardrailBlocked) as raised:
            assert_paid_provider_admission(provider)
        self.assertEqual(raised.exception.code, "AI_FINANCIAL_AUTHORITY_CONTRACT_MISSING")

    def test_invalid_bounds_are_rejected_without_database_access(self):
        from foundation.ai_financial_guardrails import FinancialGuardrailService
        service = FinancialGuardrailService(using="default")
        with self.assertRaises(FinancialAdmissionDenied) as raised:
            service.reserve_controlled_test(
                tenant_id="not-used", invocation_id="request", provider="fixture", model_identifier="fixture",
                input_token_bound=-1, max_output_tokens=10, usage_record=object(),
            )
        self.assertEqual(raised.exception.code, "AI_INPUT_BOUND_INVALID")
