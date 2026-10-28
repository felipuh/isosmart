"""Deterministic inference edge used exclusively by the local browser E2E."""

from .value_discovery import ControlledValueDiscoveryProvider


class ValueDiscoveryE2EProvider(ControlledValueDiscoveryProvider):
    provider_name = "controlled-browser-e2e-fixture"
    model_identifier = "value-discovery-browser-e2e-v1"

    def analyze(self, *, capability, context):
        payload = super().analyze(capability=capability, context=context)
        if capability == "impact_savings":
            payload["non_monetary_savings"]["potential_dimensions"] = ["process clarity"]
            payload["preliminary_improvement_opportunities"] = [{
                "opportunity_id": "clarify-process-ownership",
                "title": "Clarify process ownership",
                "description": "Validate accountable ownership before planning improvements.",
                "source_basis": ["profile.role", "profile.sector"],
                "assumptions": ["The saved profile remains current."],
                "potential_value_dimensions": ["process clarity"],
                "required_validation": ["Confirm the applicable operational process."],
                "assessment_status": "PRELIMINARY",
            }]
        # This bounded fixture proves that rejected model material cannot mark
        # Step 11 complete.  It is unreachable outside the dedicated settings.
        if (context["declared_purpose"] == "E2E_FORCE_INVALID_MODEL_OUTPUT"
                and capability == "impact_savings"):
            payload["financial_assessment"]["amount"] = "100"
        return payload
