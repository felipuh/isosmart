# operations/urls.py
"""
URLs for Operations Module
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OperationalControlViewSet,
    CustomerRequirementViewSet,
    DesignProjectViewSet,
    ExternalProviderViewSet,
    ProductionControlViewSet,
    ProductReleaseViewSet,
    NonconformityViewSet,
    DispositionViewSet,
    operations_cockpit_kpis,
    operations_ai_requirements,
    operations_ai_providers,
    operations_ai_releases,
    operations_ai_nonconformities,
)

router = DefaultRouter()
router.register(r'controls', OperationalControlViewSet, basename='control')
router.register(r'requirements', CustomerRequirementViewSet, basename='requirement')
router.register(r'design-projects', DesignProjectViewSet, basename='designproject')
router.register(r'providers', ExternalProviderViewSet, basename='provider')
router.register(r'production', ProductionControlViewSet, basename='production')
router.register(r'releases', ProductReleaseViewSet, basename='release')
router.register(r'nonconformities', NonconformityViewSet, basename='nonconformity')
router.register(r'dispositions', DispositionViewSet, basename='disposition')

app_name = 'operations'

urlpatterns = [
    path('', include(router.urls)),
    path('cockpit/kpis/', operations_cockpit_kpis, name='operations-cockpit-kpis'),
    path('ai/requirements/', operations_ai_requirements, name='operations-ai-requirements'),
    path('ai/providers/', operations_ai_providers, name='operations-ai-providers'),
    path('ai/releases/', operations_ai_releases, name='operations-ai-releases'),
    path('ai/nonconformities/', operations_ai_nonconformities, name='operations-ai-nonconformities'),
]
