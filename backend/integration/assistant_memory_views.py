from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.organization_scoping import OrganizationScopedViewSetMixin
from .services.auto_indexing import queue_memory_item_index, remove_indexed_artifact

from .models import (
    AssistantAuditLog,
    AssistantConversation,
    AssistantFeedback,
    AssistantMemoryItem,
    AssistantMessage,
    AssistantOrgProfile,
    AssistantPromptConfig,
)
from .serializers import (
    AssistantAuditLogSerializer,
    AssistantConversationSerializer,
    AssistantFeedbackSerializer,
    AssistantMemoryItemSerializer,
    AssistantMessageSerializer,
    AssistantOrgProfileSerializer,
    AssistantPromptConfigSerializer,
)


class AssistantTenantScopedViewSetMixin(OrganizationScopedViewSetMixin):
    """Tenant scope derived only from the authenticated request context."""

    def get_organization_id(self):
        organization_id = self._parse_org_id(getattr(self.request, 'organization_id', None))
        if not organization_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No fue posible validar la organización activa.')
        return organization_id


class AssistantConversationViewSet(AssistantTenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AssistantConversation.objects.all()
    serializer_class = AssistantConversationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization_id', 'status', 'current_module', 'current_submodule', 'user']
    search_fields = ['title', 'context_summary']
    ordering_fields = ['updated_at', 'created_at']

    def perform_create(self, serializer):
        serializer.save(
            organization_id=self.get_organization_id(),
            user=self.request.user,
        )


class AssistantMessageViewSet(AssistantTenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AssistantMessage.objects.select_related('conversation').all()
    serializer_class = AssistantMessageSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization_id', 'conversation', 'role', 'model_name']
    search_fields = ['content']
    ordering_fields = ['created_at']


class AssistantOrgProfileViewSet(AssistantTenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AssistantOrgProfile.objects.all()
    serializer_class = AssistantOrgProfileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization_id']
    organization_lookup_field = 'organization_id'
    organization_write_field = 'organization_id'


class AssistantMemoryItemViewSet(AssistantTenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AssistantMemoryItem.objects.all()
    serializer_class = AssistantMemoryItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization_id', 'memory_type', 'module', 'standard_code', 'is_active']
    search_fields = ['title', 'content', 'clause_reference']
    ordering_fields = ['updated_at', 'created_at', 'confidence_score']

    def perform_create(self, serializer):
        item = serializer.save(organization_id=self.get_organization_id())
        queue_memory_item_index(item)

    def perform_update(self, serializer):
        item = serializer.save()
        if item.is_active:
            queue_memory_item_index(item)
        else:
            remove_indexed_artifact(item.organization_id, f'memory_item_{item.id}')

    def perform_destroy(self, instance):
        org_id = instance.organization_id
        artifact_id = f'memory_item_{instance.id}'
        super().perform_destroy(instance)
        remove_indexed_artifact(org_id, artifact_id)


class AssistantPromptConfigViewSet(AssistantTenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AssistantPromptConfig.objects.all()
    serializer_class = AssistantPromptConfigSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization_id', 'enabled']
    organization_lookup_field = 'organization_id'
    organization_write_field = 'organization_id'

    def perform_create(self, serializer):
        serializer.save(
            organization_id=self.get_organization_id(),
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class AssistantFeedbackViewSet(AssistantTenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AssistantFeedback.objects.select_related('conversation', 'message').all()
    serializer_class = AssistantFeedbackSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization_id', 'conversation', 'message', 'rating']
    ordering_fields = ['created_at', 'rating']

    def perform_create(self, serializer):
        serializer.save(
            organization_id=self.get_organization_id(),
            user=self.request.user,
        )


class AssistantAuditLogViewSet(AssistantTenantScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AssistantAuditLog.objects.select_related('conversation').all()
    serializer_class = AssistantAuditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization_id', 'event_type', 'conversation']
    ordering_fields = ['created_at']
