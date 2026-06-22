"""
URLs for Admin Apps integration
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .assistant_memory_views import (
    AssistantAuditLogViewSet,
    AssistantConversationViewSet,
    AssistantFeedbackViewSet,
    AssistantMemoryItemViewSet,
    AssistantMessageViewSet,
    AssistantOrgProfileViewSet,
    AssistantPromptConfigViewSet,
)

app_name = 'integration'

router = DefaultRouter()
router.register(r'assistant/conversations', AssistantConversationViewSet, basename='assistant-conversations')
router.register(r'assistant/messages', AssistantMessageViewSet, basename='assistant-messages')
router.register(r'assistant/org-profiles', AssistantOrgProfileViewSet, basename='assistant-org-profiles')
router.register(r'assistant/memory-items', AssistantMemoryItemViewSet, basename='assistant-memory-items')
router.register(r'assistant/prompt-configs', AssistantPromptConfigViewSet, basename='assistant-prompt-configs')
router.register(r'assistant/feedback', AssistantFeedbackViewSet, basename='assistant-feedback')
router.register(r'assistant/audit-logs', AssistantAuditLogViewSet, basename='assistant-audit-logs')

urlpatterns = [
    path('health/', views.admin_apps_health, name='adminapps-health'),
    path('assistant/stream/', views.assistant_stream, name='assistant-stream'),
    path('assistant/state/', views.assistant_state, name='assistant-state'),
    path('assistant/index-document/', views.index_document, name='assistant-index-document'),
    path('aims/overview/', views.aims_overview, name='aims-overview'),
    path('aims/model-lifecycle-check/', views.aims_model_lifecycle_check, name='aims-model-lifecycle-check'),
    path('aims/risk-register/', views.aims_risk_register, name='aims-risk-register'),
    path('aims/audit-digest/', views.aims_audit_digest, name='aims-audit-digest'),
    path('organizations/', views.organizations, name='adminapps-organizations'),
    path('organizations/<str:org_id>/', views.organization_detail, name='adminapps-organization-detail'),
    path('organizations/<str:org_id>/users/', views.organization_users, name='adminapps-organization-users'),
    path('organizations/<str:org_id>/modules/', views.organization_modules, name='adminapps-organization-modules'),
]

urlpatterns += router.urls
