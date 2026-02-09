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
    CommunicationViewSet
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
]
