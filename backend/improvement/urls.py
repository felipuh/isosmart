# improvement/urls.py
"""
URLs for Improvement Module
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NonconformityViewSet, CorrectiveActionViewSet, ContinualImprovementViewSet

router = DefaultRouter()
router.register(r'nonconformities', NonconformityViewSet, basename='improvement-nonconformity')
router.register(r'corrective-actions', CorrectiveActionViewSet, basename='improvement-corrective-action')
router.register(r'continual-improvements', ContinualImprovementViewSet, basename='improvement-continual-improvement')

app_name = 'improvement'

urlpatterns = [
    path('', include(router.urls)),
]
