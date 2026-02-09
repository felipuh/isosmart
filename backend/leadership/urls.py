# leadership/urls.py
"""
URLs for Leadership Module
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QualityPolicyViewSet,
    OrganizationalRoleViewSet,
    RoleAssignmentViewSet,
    RACIMatrixViewSet,
    RACIEntryViewSet,
    LeadershipCommitmentViewSet,
    CustomerFocusEvidenceViewSet
)

router = DefaultRouter()
router.register(r'policies', QualityPolicyViewSet, basename='policy')
router.register(r'roles', OrganizationalRoleViewSet, basename='role')
router.register(r'role-assignments', RoleAssignmentViewSet, basename='roleassignment')
router.register(r'raci-matrices', RACIMatrixViewSet, basename='racimatrix')
router.register(r'raci-entries', RACIEntryViewSet, basename='racientry')
router.register(r'commitments', LeadershipCommitmentViewSet, basename='commitment')
router.register(r'customer-focus', CustomerFocusEvidenceViewSet, basename='customerfocus')

app_name = 'leadership'

urlpatterns = [
    path('', include(router.urls)),
]
