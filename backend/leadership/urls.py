# leadership/urls.py
"""
URLs for Leadership Module — ISO 9001:2015 Cláusula 5
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QualityPolicyViewSet,
    OrganizationalRoleViewSet,
    RoleAssignmentViewSet,
    RACIMatrixViewSet,
    RACIEntryViewSet,
    LeadershipCommitmentViewSet,
    CustomerFocusEvidenceViewSet,
    # Nuevos ViewSets
    EvidenceNodeViewSet,
    EvidenceEdgeViewSet,
    ManagementReviewViewSet,
    ReviewDecisionViewSet,
    ApprovalRecordViewSet,
    QualityCultureSurveyViewSet,
    SurveyResponseViewSet,
    AIGovernanceLogViewSet,
    # AI endpoints
    ai_generate_policy_draft,
    ai_analyze_voc,
    ai_detect_raci_gaps,
    ai_detect_policy_incoherences,
    ai_validate_iso_rules,
    ai_generate_auditor_pack,
    leadership_cockpit_kpis,
)

router = DefaultRouter()
# Existentes
router.register(r'policies', QualityPolicyViewSet, basename='policy')
router.register(r'roles', OrganizationalRoleViewSet, basename='role')
router.register(r'role-assignments', RoleAssignmentViewSet, basename='roleassignment')
router.register(r'raci-matrices', RACIMatrixViewSet, basename='racimatrix')
router.register(r'raci-entries', RACIEntryViewSet, basename='racientry')
router.register(r'commitments', LeadershipCommitmentViewSet, basename='commitment')
router.register(r'customer-focus', CustomerFocusEvidenceViewSet, basename='customerfocus')
# Nuevos
router.register(r'evidence-nodes', EvidenceNodeViewSet, basename='evidencenode')
router.register(r'evidence-edges', EvidenceEdgeViewSet, basename='evidenceedge')
router.register(r'management-reviews', ManagementReviewViewSet, basename='managementreview')
router.register(r'review-decisions', ReviewDecisionViewSet, basename='reviewdecision')
router.register(r'approval-records', ApprovalRecordViewSet, basename='approvalrecord')
router.register(r'culture-surveys', QualityCultureSurveyViewSet, basename='culturesurvey')
router.register(r'survey-responses', SurveyResponseViewSet, basename='surveyresponse')
router.register(r'ai-governance-logs', AIGovernanceLogViewSet, basename='aigovernancelog')

app_name = 'leadership'

urlpatterns = [
    path('', include(router.urls)),
    # AI endpoints
    path('ai/policy-draft/', ai_generate_policy_draft, name='ai-policy-draft'),
    path('ai/voc-analysis/', ai_analyze_voc, name='ai-voc-analysis'),
    path('ai/raci-gaps/', ai_detect_raci_gaps, name='ai-raci-gaps'),
    path('ai/policy-incoherences/', ai_detect_policy_incoherences, name='ai-policy-incoherences'),
    path('ai/validate-iso-rules/', ai_validate_iso_rules, name='ai-validate-iso-rules'),
    path('ai/auditor-pack/', ai_generate_auditor_pack, name='ai-auditor-pack'),
    path('cockpit/kpis/', leadership_cockpit_kpis, name='cockpit-kpis'),
]
