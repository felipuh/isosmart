# leadership/views.py
"""
Views for Leadership Module
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from authentication.permissions import OrganizationPermission
from integration.services.auto_indexing import (
    queue_customer_focus_index,
    queue_leadership_commitment_index,
    queue_quality_policy_index,
    remove_indexed_artifact,
)

from .models import (
    QualityPolicy,
    OrganizationalRole,
    RoleAssignment,
    RACIMatrix,
    RACIEntry,
    LeadershipCommitment,
    CustomerFocusEvidence
)
from .serializers import (
    QualityPolicySerializer,
    OrganizationalRoleSerializer,
    RoleAssignmentSerializer,
    RACIMatrixSerializer,
    RACIEntrySerializer,
    LeadershipCommitmentSerializer,
    CustomerFocusEvidenceSerializer
)


class OrganizationQuerysetMixin:
    organization_lookup = 'organization_id'

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request, 'user', None) and self.request.user.is_superuser:
            return queryset

        organization_id = getattr(self.request, 'organization_id', None)
        if organization_id and self.organization_lookup:
            return queryset.filter(**{self.organization_lookup: organization_id})

        return queryset.none()

    def get_organization_context(self):
        organization_id = getattr(self.request, 'organization_id', None)
        organization_name = None
        profile = getattr(self.request, 'user_profile', None)
        if profile and getattr(profile, 'organization', None):
            organization_name = profile.organization.name
        return organization_id, organization_name


class QualityPolicyViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Políticas de Calidad"""
    queryset = QualityPolicy.objects.all()
    serializer_class = QualityPolicySerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'status', 'is_published']
    search_fields = ['title', 'version', 'content']
    ordering_fields = ['version', 'created_at', 'effective_date']
    ordering = ['-version', '-created_at']
    
    def perform_create(self, serializer):
        org_id, org_name = self.get_organization_context()
        if org_id and not self.request.user.is_superuser:
            policy = serializer.save(
                created_by=self.request.user,
                organization_id=org_id,
                organization_name=org_name or serializer.validated_data.get('organization_name', '')
            )
            queue_quality_policy_index(policy)
            return

        policy = serializer.save(created_by=self.request.user)
        queue_quality_policy_index(policy)

    def perform_update(self, serializer):
        policy = serializer.save()
        queue_quality_policy_index(policy)

    def perform_destroy(self, instance):
        org_id = instance.organization_id
        artifact_id = f'leadership_policy_{instance.id}'
        super().perform_destroy(instance)
        remove_indexed_artifact(org_id, artifact_id)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprobar política"""
        policy = self.get_object()
        policy.approve(request.user)
        return Response({'status': 'Política aprobada'})
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publicar política"""
        policy = self.get_object()
        try:
            policy.publish()
            return Response({'status': 'Política publicada'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def make_obsolete(self, request, pk=None):
        """Marcar política como obsoleta"""
        policy = self.get_object()
        policy.make_obsolete()
        return Response({'status': 'Política marcada como obsoleta'})


class OrganizationalRoleViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Roles Organizacionales"""
    queryset = OrganizationalRole.objects.all()
    serializer_class = OrganizationalRoleSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'level', 'is_qms_role', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['level', 'name', 'created_at']
    ordering = ['level', 'name']
    
    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Obtener jerarquía del rol"""
        role = self.get_object()
        return Response({
            'path': role.get_hierarchy_path() if hasattr(role, 'get_hierarchy_path') else role.name,
            'subordinates': OrganizationalRoleSerializer(role.subordinates.all(), many=True).data
        })

    def perform_create(self, serializer):
        org_id, org_name = self.get_organization_context()
        if org_id and not self.request.user.is_superuser:
            serializer.save(
                organization_id=org_id,
                organization_name=org_name or serializer.validated_data.get('organization_name', '')
            )
            return

        serializer.save()


class RoleAssignmentViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Asignaciones de Roles"""
    queryset = RoleAssignment.objects.all()
    serializer_class = RoleAssignmentSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'user', 'role', 'assignment_type', 'is_active']
    search_fields = ['user__username', 'user__email', 'role__name']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']
    
    def perform_create(self, serializer):
        org_id, _ = self.get_organization_context()
        role = serializer.validated_data.get('role')
        if org_id and role and role.organization_id != org_id and not self.request.user.is_superuser:
            raise PermissionDenied('El rol no pertenece a la organizacion activa.')

        if org_id and not self.request.user.is_superuser:
            serializer.save(assigned_by=self.request.user, organization_id=org_id)
            return

        serializer.save(assigned_by=self.request.user)


class RACIMatrixViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Matrices RACI"""
    queryset = RACIMatrix.objects.all()
    serializer_class = RACIMatrixSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        org_id, org_name = self.get_organization_context()
        if org_id and not self.request.user.is_superuser:
            serializer.save(
                created_by=self.request.user,
                organization_id=org_id,
                organization_name=org_name or serializer.validated_data.get('organization_name', '')
            )
            return

        serializer.save(created_by=self.request.user)


class RACIEntryViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    organization_lookup = 'matrix__organization_id'
    """ViewSet para Entradas RACI"""
    queryset = RACIEntry.objects.all()
    serializer_class = RACIEntrySerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['matrix']
    search_fields = ['activity', 'description']
    ordering_fields = ['order', 'activity']
    ordering = ['order']

    def perform_create(self, serializer):
        org_id = getattr(self.request, 'organization_id', None)
        matrix = serializer.validated_data.get('matrix')
        if org_id and matrix and matrix.organization_id != org_id and not self.request.user.is_superuser:
            raise PermissionDenied('La matriz no pertenece a la organizacion activa.')

        serializer.save()


class LeadershipCommitmentViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Compromisos de Liderazgo"""
    queryset = LeadershipCommitment.objects.all()
    serializer_class = LeadershipCommitmentSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'commitment_type', 'status', 'evidence_type']
    search_fields = ['title', 'description']
    ordering_fields = ['commitment_date', 'created_at']
    ordering = ['-commitment_date']

    def perform_create(self, serializer):
        org_id, org_name = self.get_organization_context()
        if org_id and not self.request.user.is_superuser:
            commitment = serializer.save(
                organization_id=org_id,
                organization_name=org_name or serializer.validated_data.get('organization_name', '')
            )
            queue_leadership_commitment_index(commitment)
            return

        commitment = serializer.save()
        queue_leadership_commitment_index(commitment)

    def perform_update(self, serializer):
        commitment = serializer.save()
        queue_leadership_commitment_index(commitment)

    def perform_destroy(self, instance):
        org_id = instance.organization_id
        artifact_id = f'leadership_commitment_{instance.id}'
        super().perform_destroy(instance)
        remove_indexed_artifact(org_id, artifact_id)


class CustomerFocusEvidenceViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Evidencias de Enfoque al Cliente"""
    queryset = CustomerFocusEvidence.objects.all()
    serializer_class = CustomerFocusEvidenceSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'focus_type']
    search_fields = ['title', 'description', 'action_taken']
    ordering_fields = ['action_date', 'created_at']
    ordering = ['-action_date']
    
    def perform_create(self, serializer):
        org_id, org_name = self.get_organization_context()
        if org_id and not self.request.user.is_superuser:
            evidence = serializer.save(
                created_by=self.request.user,
                organization_id=org_id,
                organization_name=org_name or serializer.validated_data.get('organization_name', '')
            )
            queue_customer_focus_index(evidence)
            return

        evidence = serializer.save(created_by=self.request.user)
        queue_customer_focus_index(evidence)

    def perform_update(self, serializer):
        evidence = serializer.save()
        queue_customer_focus_index(evidence)

    def perform_destroy(self, instance):
        org_id = instance.organization_id
        artifact_id = f'customer_focus_{instance.id}'
        super().perform_destroy(instance)
        remove_indexed_artifact(org_id, artifact_id)
