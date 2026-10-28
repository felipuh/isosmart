"""
URLs para Stakeholder Intelligence Engine (SIE)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ai_modules.sie import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'stakeholders', views.StakeholderProfileViewSet, basename='stakeholder')
router.register(r'change-logs', views.StakeholderChangeLogViewSet, basename='changelog')
router.register(r'relationships', views.StakeholderRelationshipViewSet, basename='relationship')
router.register(r'engagement-plans', views.StakeholderEngagementPlanViewSet, basename='engagement-plan')

app_name = 'sie'

urlpatterns = [
    path('', include(router.urls)),
]
