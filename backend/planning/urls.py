# planning/urls.py
"""
URLs for Planning Module
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RiskOpportunityViewSet,
    QualityObjectiveViewSet,
    ObjectiveActionViewSet,
    ChangeControlViewSet,
    PlanningVersionRecordViewSet,
    PlanningApprovalRecordViewSet,
    PlanningAIGovernanceLogViewSet,
    planning_cockpit_kpis,
)

router = DefaultRouter()
router.register(r'risks-opportunities', RiskOpportunityViewSet, basename='riskopportunity')
router.register(r'objectives', QualityObjectiveViewSet, basename='objective')
router.register(r'actions', ObjectiveActionViewSet, basename='action')
router.register(r'changes', ChangeControlViewSet, basename='change')
router.register(r'version-records', PlanningVersionRecordViewSet, basename='planning-version-record')
router.register(r'approval-records', PlanningApprovalRecordViewSet, basename='planning-approval-record')
router.register(r'ai-governance-logs', PlanningAIGovernanceLogViewSet, basename='planning-ai-governance-log')

app_name = 'planning'

urlpatterns = [
    path('', include(router.urls)),
    path('cockpit/kpis/', planning_cockpit_kpis, name='planning-cockpit-kpis'),
]
