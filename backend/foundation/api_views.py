"""DRF adapters for the source-artifact API contracts."""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import OperationalError

from .api_serializers import (
    ApprovalDecisionRequestSerializer,
    DomainEventPublishRequestSerializer,
    EvidenceCreateRequestSerializer,
    FoundationAttemptRequestSerializer,
    OnboardingEvidenceIngestionRequestSerializer,
    OrganizationalProfileRequestSerializer,
)
from .source_artifact_api import (
    SourceArtifactAPIError,
    create_evidence,
    list_recommendations,
    onboarding_status,
    onboarding_organizations,
    save_organizational_profile,
    ingest_onboarding_evidence_references,
    publish_domain_event,
    recommendation_basis,
    record_approval_decision,
    request_trace_id,
    resolve_source_artifact_principal,
    submit_foundation_attempt,
)


class SourceArtifactAPIView(APIView):
    def handle_exception(self, exc):
        if isinstance(exc, SourceArtifactAPIError):
            return Response({"code": exc.code, "detail": str(exc)}, status=exc.status_code)
        if isinstance(exc, OperationalError):
            return Response({
                "code": "FOUNDATION_DATABASE_UNAVAILABLE",
                "detail": "the tenant-scoped PostgreSQL operation is unavailable",
            }, status=503)
        response = super().handle_exception(exc)
        if isinstance(exc, ValidationError) or response.status_code in (400, 401, 403, 404, 409, 422, 503):
            if response.status_code == 401:
                code = "AUTHENTICATION_REQUIRED"
            elif response.status_code == 403:
                code = "FORBIDDEN"
            elif isinstance(exc, ValidationError):
                code = "REQUEST_INVALID"
            else:
                code = "REQUEST_FAILED"
            return Response({"code": code, "detail": str(response.data)}, status=response.status_code)
        return response

    def get_principal(self, request):
        return resolve_source_artifact_principal(request)


class OnboardingStatusView(SourceArtifactAPIView):
    def get(self, request):
        principal = self.get_principal(request)
        return Response(onboarding_status(principal))


class OnboardingOrganizationsView(SourceArtifactAPIView):
    def get(self, request):
        principal = self.get_principal(request)
        return Response(onboarding_organizations(principal))


class OrganizationalProfileCreateView(SourceArtifactAPIView):
    def post(self, request):
        serializer = OrganizationalProfileRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        principal = self.get_principal(request)
        payload = {
            "organization_id": serializer.validated_data["organization_id"],
            "event_id": serializer.validated_data["event_id"],
            "profile": serializer.profile(),
        }
        return Response(
            save_organizational_profile(principal, payload, trace_id=request_trace_id(request)),
            status=201,
        )


class OnboardingEvidenceReferencesCreateView(SourceArtifactAPIView):
    def post(self, request):
        serializer = OnboardingEvidenceIngestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        principal = self.get_principal(request)
        return Response(
            ingest_onboarding_evidence_references(
                principal, serializer.validated_data, trace_id=request_trace_id(request),
            ),
            status=201,
        )


class RecommendationListView(SourceArtifactAPIView):
    def get(self, request):
        principal = self.get_principal(request)
        clause = request.query_params.get("clause")
        if clause is not None and (not clause.strip() or len(clause) > 80):
            raise SourceArtifactAPIError("CLAUSE_INVALID", "clause must be a non-empty code up to 80 characters", 422)
        return Response({"results": list_recommendations(principal, clause=clause)})


class RecommendationBasisView(SourceArtifactAPIView):
    def get(self, request, recommendation_id):
        principal = self.get_principal(request)
        return Response(recommendation_basis(principal, recommendation_id))


class ApprovalDecisionView(SourceArtifactAPIView):
    def post(self, request, decision_id):
        serializer = ApprovalDecisionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        principal = self.get_principal(request)
        trace_id = request_trace_id(request)
        result = record_approval_decision(
            principal,
            decision_id,
            decision=serializer.validated_data["decision"],
            comments=serializer.validated_data.get("comments"),
            trace_id=trace_id,
        )
        return Response({
            "approval_id": str(result.approval_id),
            "decision": result.decision,
            "event_id": str(result.event_id),
            "outbox_id": str(result.outbox_id),
            "audit_id": str(result.audit_id),
        })


class DomainEventPublishView(SourceArtifactAPIView):
    def post(self, request):
        serializer = DomainEventPublishRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        principal = self.get_principal(request)
        result = publish_domain_event(principal, serializer.validated_data)
        return Response(result, status=202)


class EvidenceCreateView(SourceArtifactAPIView):
    def post(self, request):
        serializer = EvidenceCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        principal = self.get_principal(request)
        result = create_evidence(
            principal,
            serializer.validated_data,
            trace_id=request_trace_id(request),
        )
        return Response({
            "evidence_id": str(result.entity_id),
            "lineage_id": str(result.aggregate_id),
            "event_id": str(result.event_id),
            "outbox_id": str(result.outbox_id),
            "audit_id": str(result.audit_id),
            "trace_id": str(result.trace_id),
        }, status=201)


class FoundationAttemptCreateView(SourceArtifactAPIView):
    def post(self, request):
        serializer = FoundationAttemptRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        principal = self.get_principal(request)
        result = submit_foundation_attempt(
            principal,
            serializer.validated_data,
            trace_id=request_trace_id(request),
        )
        return Response({
            "attempt_id": str(result.attempt_id),
            "learning_path_id": str(result.learning_path_id),
            "standard_edition_id": str(result.standard_edition_id),
            "question_bank_version": getattr(result, "question_bank_version", 1),
            "score": str(result.score),
            "passed": result.passed,
            "weak_concepts": list(result.weak_concepts),
            "feedback": list(result.feedback),
            "provenance_hash": result.provenance_hash,
            "event_id": str(result.event_id) if result.event_id else None,
            "outbox_id": str(result.outbox_id) if result.outbox_id else None,
            "audit_id": str(result.audit_id),
            "completed_at": result.completed_at.isoformat(),
        }, status=201)
