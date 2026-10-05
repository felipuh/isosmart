from django.urls import path

from .api_views import (
    ApprovalDecisionView,
    DomainEventPublishView,
    EvidenceCreateView,
    FoundationAttemptCreateView,
    OnboardingEvidenceReferencesCreateView,
    OnboardingOrganizationsView,
    OnboardingStatusView,
    OrganizationalProfileCreateView,
    RecommendationBasisView,
    RecommendationListView,
)


urlpatterns = [
    path("v1/onboarding/status", OnboardingStatusView.as_view(), name="source-onboarding-status"),
    path("v1/onboarding/organizations", OnboardingOrganizationsView.as_view(), name="onboarding-organizations"),
    path("v1/onboarding/organizational-profile", OrganizationalProfileCreateView.as_view(), name="onboarding-organizational-profile"),
    path("v1/onboarding/document-references", OnboardingEvidenceReferencesCreateView.as_view(), name="onboarding-document-references"),
    path("v1/recommendations", RecommendationListView.as_view(), name="source-recommendations"),
    path("v1/recommendations/<uuid:recommendation_id>/basis", RecommendationBasisView.as_view(), name="source-recommendation-basis"),
    path("v1/approvals/<uuid:decision_id>/decision", ApprovalDecisionView.as_view(), name="source-approval-decision"),
    path("v1/events", DomainEventPublishView.as_view(), name="source-domain-events"),
    path("v1/evidence", EvidenceCreateView.as_view(), name="source-evidence"),
    path("v1/learning/iso9000/attempts", FoundationAttemptCreateView.as_view(), name="source-foundation-attempt"),
]
