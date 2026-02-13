from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PerformanceIndicatorViewSet, MeasurementViewSet, DataAnalysisViewSet,
    InternalAuditViewSet, AuditFindingViewSet, ManagementReviewViewSet
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
]
