from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PerformanceIndicatorViewSet, MeasurementViewSet, DataAnalysisViewSet,
    InternalAuditViewSet, AuditFindingViewSet, ManagementReviewViewSet,
    performance_cockpit_kpis, performance_ai_indicator_drift,
    performance_ai_audit_assistant, performance_ai_executive_brief,
)

router = DefaultRouter()
router.register(r'indicators', PerformanceIndicatorViewSet, basename='performance-indicator')
router.register(r'measurements', MeasurementViewSet, basename='measurement')
router.register(r'analyses', DataAnalysisViewSet, basename='data-analysis')
router.register(r'audits', InternalAuditViewSet, basename='internal-audit')
router.register(r'findings', AuditFindingViewSet, basename='audit-finding')
router.register(r'reviews', ManagementReviewViewSet, basename='management-review')

urlpatterns = [
    path('', include(router.urls)),
    path('cockpit/kpis/', performance_cockpit_kpis, name='performance-cockpit-kpis'),
    path('ai/indicator-drift/', performance_ai_indicator_drift, name='performance-ai-indicator-drift'),
    path('ai/audit-assistant/', performance_ai_audit_assistant, name='performance-ai-audit-assistant'),
    path('ai/executive-brief/', performance_ai_executive_brief, name='performance-ai-executive-brief'),
]
