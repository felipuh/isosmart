"""HTTP schemas for the source-artifact API surface."""

import re
from decimal import Decimal

from rest_framework import serializers


class FoundationAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_option_ids = serializers.ListField(
        child=serializers.CharField(max_length=160), allow_empty=False, max_length=20,
    )


class FoundationAttemptRequestSerializer(serializers.Serializer):
    learning_path_id = serializers.UUIDField()
    answers = FoundationAnswerSerializer(many=True, allow_empty=False, max_length=200)


class OrganizationalProfileRequestSerializer(serializers.Serializer):
    """Transport schema for the source-listed onboarding profile fields."""

    organization_id = serializers.UUIDField()
    event_id = serializers.UUIDField()
    role = serializers.CharField(max_length=120)
    expertise_level = serializers.CharField(max_length=120)
    size_range = serializers.CharField(max_length=120)
    sites_count = serializers.IntegerField(min_value=0)
    countries = serializers.ListField(
        child=serializers.CharField(max_length=120), allow_empty=False, max_length=100,
    )
    sector = serializers.CharField(max_length=255)
    certification_status = serializers.CharField(max_length=120)
    employees_count = serializers.IntegerField(min_value=0, required=False)

    def profile(self):
        return {
            key: value for key, value in self.validated_data.items()
            if key not in {"organization_id", "event_id"}
        }


class OnboardingEvidenceReferenceSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    source_type = serializers.ChoiceField(
        choices=("strategy", "process", "kpi", "audit", "complaint", "supplier", "document"),
    )
    source_uri = serializers.CharField(max_length=2000)
    content_hash = serializers.RegexField(regex=r"^[0-9a-f]{64}$", max_length=64)
    captured_at = serializers.DateTimeField()
    document_version_id = serializers.UUIDField(required=False, allow_null=True)


class OnboardingEvidenceIngestionRequestSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    event_id = serializers.UUIDField(
        help_text="Idempotency key for the onboarding transition, not an uploaded file identifier.",
    )
    items = OnboardingEvidenceReferenceSerializer(many=True, allow_empty=False, max_length=100)


class ValueDiscoveryRequestSerializer(serializers.Serializer):
    """IMPLEMENTATION_DEFINED_WITHIN_OWNER_APPROVED_CONTRACT."""

    organization_id = serializers.UUIDField()
    event_id = serializers.UUIDField(help_text="Idempotency key for Step 11 completion.")
    organization_declared_purpose = serializers.CharField(max_length=2000, trim_whitespace=True)


class ApprovalDecisionRequestSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=("approve", "reject", "request_changes"))
    comments = serializers.CharField(required=False, allow_blank=True, max_length=4000)


class EvidenceCreateRequestSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    source_type = serializers.CharField(max_length=80)
    source_uri = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content_hash = serializers.CharField(required=False, allow_blank=False, max_length=64)
    captured_at = serializers.DateTimeField()
    trust_score = serializers.DecimalField(
        required=False, allow_null=True, max_digits=5, decimal_places=4,
        min_value=Decimal("0"), max_value=Decimal("1"),
    )
    document_version_id = serializers.UUIDField(required=False, allow_null=True)
    change_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_content_hash(self, value):
        if not re.fullmatch(r"[0-9a-f]{64}", value):
            raise serializers.ValidationError("content_hash must be a lowercase SHA-256 digest")
        return value

    def validate(self, attrs):
        if not attrs.get("document_version_id") and not attrs.get("content_hash"):
            raise serializers.ValidationError({
                "content_hash": "content_hash is required unless document_version_id is supplied",
            })
        return attrs


PUBLISHABLE_EVENT_TYPES = (
    "context.signal.detected",
    "stakeholder.requirement.changed",
    "kpi.threshold.breached",
    "supplier.performance.degraded",
    "customer.complaint.received",
    "change.requested",
    "document.updated",
    "measurement.out_of_tolerance",
    "audit.finding.created",
    "nonconformity.detected",
)


class DomainEventPublishRequestSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    event_type = serializers.ChoiceField(choices=PUBLISHABLE_EVENT_TYPES)
    aggregate_type = serializers.CharField(max_length=120)
    aggregate_id = serializers.UUIDField()
    aggregate_version = serializers.IntegerField(min_value=1)
    occurred_at = serializers.DateTimeField()
    trace_id = serializers.UUIDField()
    correlation_id = serializers.UUIDField(required=False, allow_null=True)
    causation_id = serializers.UUIDField(required=False, allow_null=True)
    payload = serializers.JSONField()

    def validate_payload(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("payload must be a JSON object")
        return value


class ErrorResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()
