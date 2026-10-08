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
