from django.urls import path

from . import qms_api_views as qms
from .api_views import (
    ApprovalDecisionView,
    DomainEventPublishView,
    EvidenceCreateView,
    FoundationAttemptCreateView,
    OnboardingEvidenceReferencesCreateView,
    OnboardingOrganizationsView,
    OnboardingStatusView,
    OrganizationalProfileCreateView,
    ValueDiscoveryExecuteView,
    ValueDiscoveryResultView,
    RecommendationBasisView,
    RecommendationListView,
)


urlpatterns = [
    path("v1/onboarding/status", OnboardingStatusView.as_view(), name="source-onboarding-status"),
    path("v1/onboarding/organizations", OnboardingOrganizationsView.as_view(), name="onboarding-organizations"),
    path("v1/onboarding/organizational-profile", OrganizationalProfileCreateView.as_view(), name="onboarding-organizational-profile"),
    path("v1/onboarding/document-references", OnboardingEvidenceReferencesCreateView.as_view(), name="onboarding-document-references"),
    path("v1/onboarding/value-discovery", ValueDiscoveryExecuteView.as_view(), name="onboarding-value-discovery"),
    path("v1/onboarding/value-discovery/<uuid:execution_id>", ValueDiscoveryResultView.as_view(), name="onboarding-value-discovery-result"),
    path("v1/recommendations", RecommendationListView.as_view(), name="source-recommendations"),
    path("v1/recommendations/<uuid:recommendation_id>/basis", RecommendationBasisView.as_view(), name="source-recommendation-basis"),
    path("v1/approvals/<uuid:decision_id>/decision", ApprovalDecisionView.as_view(), name="source-approval-decision"),
    path("v1/events", DomainEventPublishView.as_view(), name="source-domain-events"),
    path("v1/evidence", EvidenceCreateView.as_view(), name="source-evidence"),
    path("v1/learning/iso9000/attempts", FoundationAttemptCreateView.as_view(), name="source-foundation-attempt"),
]

urlpatterns += [
    path("v1/qms/capabilities", qms.QmsCapabilitiesView.as_view()),
    path("v1/qms/owners", qms.QmsOwnersView.as_view()),
    path("v1/qms/organizations", qms.QmsOrganizationsView.as_view(), name="qms-organizations"),
    path("v1/qms/requirements", qms.QmsRequirementsView.as_view(), name="qms-requirements"),
    path("v1/qms/evidence", qms.QmsEvidenceView.as_view(), name="qms-evidence-list"),
    path("v1/qms/audits", qms.AuditsView.as_view(), name="qms-audits"),
    path("v1/qms/findings", qms.FindingsView.as_view(), name="qms-findings"),
    path("v1/qms/findings/<uuid:finding_id>/nonconformity", qms.FindingNonconformityView.as_view(), name="qms-finding-nonconformity"),
    path("v1/qms/nonconformities", qms.NonconformitiesView.as_view(), name="qms-nonconformities"),
    path("v1/qms/nonconformities/<uuid:nc_id>/corrective-actions", qms.NonconformityCorrectiveActionView.as_view(), name="qms-nc-corrective-actions"),
    path("v1/qms/corrective-actions", qms.CorrectiveActionsView.as_view(), name="qms-corrective-actions"),
]
