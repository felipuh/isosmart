from unittest import TestCase

from foundation.value_discovery import (
    ControlledValueDiscoveryProvider,
    ValueDiscoveryError,
    _validate_impact_result,
    _validate_profile_result,
    _validate_purpose_result,
)


class ValueDiscoverySchemaTests(TestCase):
    def setUp(self):
        self.context = {
            "profile": {"role": "quality_manager", "sector": "services"},
            "profile_hash": "a" * 64,
            "declared_purpose": "Provide dependable services.",
        }
        self.provider = ControlledValueDiscoveryProvider()

    def test_controlled_provider_returns_all_three_validated_capabilities(self):
        profile = _validate_profile_result(
            self.provider.analyze(capability="organizational_profile", context=self.context), "a" * 64,
        )
        impact = _validate_impact_result(
            self.provider.analyze(capability="impact_savings", context=self.context),
        )
        purpose = _validate_purpose_result(
            self.provider.analyze(capability="purpose_alignment", context=self.context),
            self.context["declared_purpose"],
        )
        self.assertEqual(profile["execution_status"], "COMPLETED")
        self.assertEqual(impact["preliminary_improvement_opportunities"], [])
        self.assertEqual(impact["financial_assessment"]["status"], "NOT_ASSESSED")
        self.assertEqual(purpose["purpose_reference"], "organization_declared_purpose")

    def test_financial_amount_is_rejected_without_authorized_baseline(self):
        output = self.provider.analyze(capability="impact_savings", context=self.context)
        output["financial_assessment"]["amount"] = "money"
        with self.assertRaisesRegex(ValueDiscoveryError, "financial assessment"):
            _validate_impact_result(output)

    def test_quantified_opportunity_is_rejected(self):
        output = self.provider.analyze(capability="impact_savings", context=self.context)
        output["preliminary_improvement_opportunities"] = [{
            "opportunity_id": "opportunity", "title": "Review work", "description": "Save 20 hours",
            "source_basis": ["profile.sector"], "assumptions": [], "potential_value_dimensions": ["time"],
            "required_validation": ["Measure current effort"], "assessment_status": "REQUIRES_VALIDATION",
        }]
        with self.assertRaisesRegex(ValueDiscoveryError, "numeric"):
            _validate_impact_result(output)


class RealValueDiscoveryProviderTests(TestCase):
    def setUp(self):
        from foundation.value_discovery import ChatCompletionsValueDiscoveryProvider
        from django.test import override_settings
        self.settings = override_settings(AI_ASSISTANT_API_URL="https://api.openai.com/v1/chat/completions",
            AI_ASSISTANT_API_KEY="test-only-not-a-real-key", AI_ASSISTANT_MODEL="gpt-4o-mini")
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        self.provider = ChatCompletionsValueDiscoveryProvider()
        self.context = {"profile": {"role": "quality_manager", "sector": "services"},
            "profile_hash": "a" * 64, "declared_purpose": "Provide dependable services."}

    def response(self, content, finish_reason="stop", refusal=None):
        from unittest.mock import Mock
        return Mock(status_code=200, json=lambda: {"choices": [{"finish_reason": finish_reason,
            "message": {"content": content, "refusal": refusal}}]})

    def test_real_provider_requests_strict_schemas_and_validates_each_capability(self):
        import json
        from unittest.mock import patch
        fixture = ControlledValueDiscoveryProvider()
        for capability in ("organizational_profile", "impact_savings", "purpose_alignment"):
            with self.subTest(capability=capability):
                output = fixture.analyze(capability=capability, context=self.context)
                with patch("foundation.value_discovery.httpx.post", return_value=self.response(json.dumps(output))) as post:
                    actual = self.provider.analyze(capability=capability, context=self.context)
                payload = post.call_args.kwargs["json"]
                self.assertEqual(payload["response_format"]["type"], "json_schema")
                schema_config = payload["response_format"]["json_schema"]
                self.assertTrue(schema_config["strict"])
                self.assertFalse(schema_config["schema"]["additionalProperties"])
                self.assertEqual(set(schema_config["schema"]["required"]), set(output))
                self.assertEqual(payload["max_tokens"], 2000)
                self.assertEqual(post.call_count, 1)
                if capability == "organizational_profile":
                    _validate_profile_result(actual, self.context["profile_hash"])
                elif capability == "impact_savings":
                    _validate_impact_result(actual)
                else:
                    _validate_purpose_result(actual, self.context["declared_purpose"])

    def test_refusal_truncation_and_malformed_output_fail_closed_without_retry(self):
        from unittest.mock import patch
        cases = [(self.response("{}", refusal="declined"), "AI_PROVIDER_REFUSED"),
            (self.response("{}", finish_reason="length"), "AI_PROVIDER_INCOMPLETE_RESPONSE"),
            (self.response("invalid-json"), "AI_PROVIDER_MALFORMED_RESPONSE"),
            (self.response("[]"), "AI_PROVIDER_MALFORMED_RESPONSE")]
        for response, code in cases:
            with self.subTest(code=code):
                with patch("foundation.value_discovery.httpx.post", return_value=response) as post:
                    with self.assertRaises(ValueDiscoveryError) as caught:
                        self.provider.analyze(capability="organizational_profile", context=self.context)
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(post.call_count, 1)

    def test_unknown_capability_does_not_call_provider(self):
        from unittest.mock import patch
        with patch("foundation.value_discovery.httpx.post") as post:
            with self.assertRaises(ValueDiscoveryError):
                self.provider.analyze(capability="unsupported", context=self.context)
        post.assert_not_called()
