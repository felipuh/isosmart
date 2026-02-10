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
    ChangeControlViewSet
)

router = DefaultRouter()
router.register(r'risks-opportunities', RiskOpportunityViewSet, basename='riskopportunity')
router.register(r'objectives', QualityObjectiveViewSet, basename='objective')
router.register(r'actions', ObjectiveActionViewSet, basename='action')
router.register(r'changes', ChangeControlViewSet, basename='change')

app_name = 'planning'

urlpatterns = [
    path('', include(router.urls)),
]
