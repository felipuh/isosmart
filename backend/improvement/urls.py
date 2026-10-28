# improvement/urls.py
"""
URLs for Improvement Module
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NonconformityViewSet, CorrectiveActionViewSet, ContinualImprovementViewSet,
    improvement_cockpit_kpis, improvement_ai_root_cause,
    improvement_ai_corrective_tracker, improvement_ai_continual_optimizer,
)

router = DefaultRouter()
router.register(r'nonconformities', NonconformityViewSet, basename='improvement-nonconformity')
router.register(r'corrective-actions', CorrectiveActionViewSet, basename='improvement-corrective-action')
router.register(r'continual-improvements', ContinualImprovementViewSet, basename='improvement-continual-improvement')

app_name = 'improvement'

urlpatterns = [
    path('', include(router.urls)),
    path('cockpit/kpis/', improvement_cockpit_kpis, name='improvement-cockpit-kpis'),
    path('ai/root-cause/', improvement_ai_root_cause, name='improvement-ai-root-cause'),
    path('ai/corrective-tracker/', improvement_ai_corrective_tracker, name='improvement-ai-corrective-tracker'),
    path('ai/continual-optimizer/', improvement_ai_continual_optimizer, name='improvement-ai-continual-optimizer'),
]
