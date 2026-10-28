# resources/urls.py
"""
URLs for Resources Module
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ResourceViewSet,
    InfrastructureViewSet,
    WorkEnvironmentViewSet,
    CompetenceViewSet,
    TrainingViewSet,
    AwarenessViewSet,
    CommunicationViewSet,
    support_cockpit_kpis,
    support_ai_competence_plan,
    support_ai_awareness_pulse,
    support_ai_communication_draft,
    support_ai_document_health,
)

router = DefaultRouter()
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'infrastructure', InfrastructureViewSet, basename='infrastructure')
router.register(r'work-environment', WorkEnvironmentViewSet, basename='workenvironment')
router.register(r'competences', CompetenceViewSet, basename='competence')
router.register(r'trainings', TrainingViewSet, basename='training')
router.register(r'awareness', AwarenessViewSet, basename='awareness')
router.register(r'communications', CommunicationViewSet, basename='communication')

app_name = 'resources'

urlpatterns = [
    path('', include(router.urls)),
    path('cockpit/kpis/', support_cockpit_kpis, name='support-cockpit-kpis'),
    path('ai/competence-plan/', support_ai_competence_plan, name='support-ai-competence-plan'),
    path('ai/awareness-pulse/', support_ai_awareness_pulse, name='support-ai-awareness-pulse'),
    path('ai/communication-draft/', support_ai_communication_draft, name='support-ai-communication-draft'),
    path('ai/document-health/', support_ai_document_health, name='support-ai-document-health'),
]
