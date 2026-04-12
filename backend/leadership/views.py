# leadership/views.py
"""
Views for Leadership Module
ISO 9001:2015 – Cláusula 5 | Copiloto de Liderazgo
Separación explícita: IA recomienda → Humano aprueba → Registro inmutable
"""

import hashlib
import json

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from authentication.permissions import OrganizationPermission, IsOrgAdmin, IsOrgManager
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
    CustomerFocusEvidence,
    EvidenceNode,
    EvidenceEdge,
    ManagementReview,
    ReviewDecision,
    ApprovalRecord,
    QualityCultureSurvey,
    SurveyResponse,
    AIGovernanceLog,
)
from .serializers import (
    QualityPolicySerializer,
    OrganizationalRoleSerializer,
    RoleAssignmentSerializer,
    RACIMatrixSerializer,
    RACIEntrySerializer,
    LeadershipCommitmentSerializer,
    CustomerFocusEvidenceSerializer,
    EvidenceNodeSerializer,
    EvidenceEdgeSerializer,
    ManagementReviewSerializer,
    ReviewDecisionSerializer,
    ApprovalRecordSerializer,
    QualityCultureSurveySerializer,
    SurveyResponseSerializer,
    AIGovernanceLogSerializer,
)
from ai_modules.sla.iso_rules_engine import ISOLeadershipRulesEngine
from ai_modules.sla.leadership_engine import LeadershipAIService

import logging
logger = logging.getLogger(__name__)

_iso_rules = ISOLeadershipRulesEngine()



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


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE GRAPH VIEWSETS
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceNodeViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Nodos del Grafo de Evidencias de Liderazgo"""
    queryset = EvidenceNode.objects.all()
    serializer_class = EvidenceNodeSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'node_type', 'reference_model']
    search_fields = ['title', 'description', 'data_source']
    ordering_fields = ['node_type', 'created_at']
    ordering = ['node_type', '-created_at']

    def perform_create(self, serializer):
        org_id, _ = self.get_organization_context()
        if org_id and not self.request.user.is_superuser:
            serializer.save(organization_id=org_id)
            return
        serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprobar un nodo de evidencia (responsable asignado confirmado)"""
        node = self.get_object()
        if not node.responsible_id:
            return Response(
                {'error': 'ISO 5.3: El nodo debe tener responsable asignado antes de aprobarse.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        node.approve(request.user)
        return Response({'status': 'Nodo aprobado', 'approved_at': node.approved_at})

    @action(detail=False, methods=['get'])
    def graph(self, request):
        """Retorna el grafo completo (nodos + aristas) para visualización"""
        org_id = getattr(request, 'organization_id', None)
        if not org_id and not request.user.is_superuser:
            return Response({'nodes': [], 'edges': []})

        nodes_qs = self.get_queryset()
        edges_qs = EvidenceEdge.objects.filter(
            source__organization_id=org_id
        ).select_related('source', 'target') if org_id else EvidenceEdge.objects.all()

        return Response({
            'nodes': EvidenceNodeSerializer(nodes_qs, many=True).data,
            'edges': EvidenceEdgeSerializer(edges_qs, many=True).data,
        })


class EvidenceEdgeViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Aristas del Grafo de Evidencias"""
    queryset = EvidenceEdge.objects.all()
    serializer_class = EvidenceEdgeSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    organization_lookup = 'source__organization_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['edge_type']
    search_fields = ['label']

    def perform_create(self, serializer):
        org_id, _ = self.get_organization_context()
        source = serializer.validated_data.get('source')
        if org_id and source and source.organization_id != org_id and not self.request.user.is_superuser:
            raise PermissionDenied('El nodo fuente no pertenece a la organización activa.')
        serializer.save(created_by=self.request.user)


# ─────────────────────────────────────────────────────────────────────────────
# MANAGEMENT REVIEW VIEWSETS
# ─────────────────────────────────────────────────────────────────────────────

class ManagementReviewViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Revisiones por la Dirección – ISO 9001:2015 Cláusula 9.3"""
    queryset = ManagementReview.objects.all()
    serializer_class = ManagementReviewSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'status', 'review_type']
    search_fields = ['title']
    ordering_fields = ['scheduled_date', 'created_at']
    ordering = ['-scheduled_date']

    def perform_create(self, serializer):
        org_id, org_name = self.get_organization_context()
        # Validar reglas ISO antes de crear
        data = dict(serializer.validated_data)
        rule_result = _iso_rules.validate_management_review_inputs(data)
        if not rule_result.passed:
            blockers = [v.message for v in rule_result.violations if v.severity == 'blocker']
            raise ValidationError({'iso_violations': blockers})

        if org_id and not self.request.user.is_superuser:
            serializer.save(
                created_by=self.request.user,
                organization_id=org_id,
                organization_name=org_name or serializer.validated_data.get('organization_name', '')
            )
            return
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_brief(self, request, pk=None):
        """
        Genera brief pre-reunión con IA.
        OUTPUT: borrador que requiere aprobación del facilitador.
        Separación IA recomienda / humano aprueba.
        """
        review = self.get_object()
        org_id = review.organization_id

        ai_service = LeadershipAIService()
        result = ai_service.generate_management_review_brief({
            'organization_id': org_id,
            'review_id': review.id,
        })

        if result.get('status') == 'brief_ready':
            review.ai_brief = result['brief']
            review.ai_brief_generated_at = timezone.now()
            review.ai_brief_approved_by = None
            review.ai_brief_approved_at = None
            review.save(update_fields=['ai_brief', 'ai_brief_generated_at',
                                        'ai_brief_approved_by', 'ai_brief_approved_at'])

            # Registrar en gobernanza de IA
            gov_data = result.get('governance_log_data', {})
            if gov_data:
                AIGovernanceLog.objects.create(**{
                    k: v for k, v in gov_data.items()
                    if k in [f.name for f in AIGovernanceLog._meta.get_fields()]
                })

        return Response({
            'status': result.get('status'),
            'message': result.get('message'),
            'ai_requires_human_approval': True,
            'brief_preview': (result.get('brief') or '')[:300],
            'sources_cited': result.get('sources_cited', []),
            'hallucination_flags': result.get('hallucination_flags', []),
        })

    @action(detail=True, methods=['post'])
    def approve_brief(self, request, pk=None):
        """Aprueba el brief generado por IA para su distribución."""
        review = self.get_object()
        if not review.ai_brief:
            return Response(
                {'error': 'No hay brief generado para aprobar.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        review.approve_brief(request.user)
        return Response({'status': 'Brief aprobado',
                         'approved_by': request.user.get_full_name(),
                         'approved_at': review.ai_brief_approved_at})

    @action(detail=True, methods=['post'])
    def approve_minutes(self, request, pk=None):
        """
        Aprueba el acta de la revisión.
        Genera un ApprovalRecord inmutable con firma digital.
        """
        review = self.get_object()
        try:
            review.approve_minutes(request.user)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Crear registro inmutable de aprobación
        snapshot = {
            'review_id': review.id,
            'title': review.title,
            'minutes': review.minutes,
            'scheduled_date': str(review.scheduled_date),
            'status': review.status,
        }
        ts_iso = review.minutes_approved_at.isoformat()
        sig = ApprovalRecord.generate_signature(snapshot, request.user.pk, ts_iso)
        ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or None

        ApprovalRecord.objects.create(
            organization_id=review.organization_id,
            workflow_type='review_minutes',
            reference_id=review.id,
            reference_model='leadership.ManagementReview',
            title=f"Acta: {review.title}",
            approved_by=request.user,
            digital_signature=sig,
            content_snapshot=snapshot,
            ip_address=ip,
            notes=request.data.get('notes', ''),
        )

        return Response({
            'status': 'Acta aprobada y firmada digitalmente',
            'digital_signature': sig,
            'approved_at': review.minutes_approved_at,
        })


class ReviewDecisionViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Decisiones de Revisiones por la Dirección"""
    queryset = ReviewDecision.objects.all()
    serializer_class = ReviewDecisionSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    organization_lookup = 'review__organization_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['review', 'decision_type', 'status', 'ai_suggested']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        # Regla ISO: toda decisión debe tener responsable
        rule_result = _iso_rules.validate_decision_has_responsible(data)
        if not rule_result.passed:
            blockers = [v.message for v in rule_result.violations if v.severity == 'blocker']
            raise ValidationError({'iso_violations': blockers})
        serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprueba una decisión — genera ApprovalRecord inmutable."""
        decision = self.get_object()
        try:
            decision.approve(request.user)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        snapshot = {
            'decision_id': decision.id,
            'title': decision.title,
            'decision_type': decision.decision_type,
            'responsible_id': decision.responsible_id,
            'rationale': decision.rationale,
            'ai_suggested': decision.ai_suggested,
        }
        ts_iso = decision.approved_at.isoformat()
        sig = ApprovalRecord.generate_signature(snapshot, request.user.pk, ts_iso)
        ip = request.META.get('REMOTE_ADDR') or None

        ApprovalRecord.objects.create(
            organization_id=decision.review.organization_id,
            workflow_type='review_decision',
            reference_id=decision.id,
            reference_model='leadership.ReviewDecision',
            title=f"Decisión: {decision.title}",
            approved_by=request.user,
            digital_signature=sig,
            content_snapshot=snapshot,
            ip_address=ip,
            notes=request.data.get('notes', ''),
        )

        return Response({
            'status': 'Decisión aprobada',
            'digital_signature': sig,
            'approved_at': decision.approved_at,
        })


# ─────────────────────────────────────────────────────────────────────────────
# APPROVAL RECORDS (solo lectura — los registros son inmutables)
# ─────────────────────────────────────────────────────────────────────────────

class ApprovalRecordViewSet(OrganizationQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet READ-ONLY para Registros de Aprobación.
    Los registros son inmutables — no se permite edición ni eliminación.
    """
    queryset = ApprovalRecord.objects.all()
    serializer_class = ApprovalRecordSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'workflow_type', 'reference_model']
    search_fields = ['title', 'digital_signature']
    ordering_fields = ['approved_at', 'workflow_type']
    ordering = ['-approved_at']

    @action(detail=True, methods=['get'])
    def verify_signature(self, request, pk=None):
        """Verifica la integridad de la firma digital del registro."""
        record = self.get_object()
        ts_iso = record.approved_at.isoformat()
        expected_sig = ApprovalRecord.generate_signature(
            record.content_snapshot, record.approved_by_id, ts_iso
        )
        is_valid = expected_sig == record.digital_signature
        return Response({
            'valid': is_valid,
            'stored_signature': record.digital_signature,
            'computed_signature': expected_sig,
            'message': 'Firma válida — integridad confirmada' if is_valid else
                       '⚠️ Firma no coincide — posible manipulación del registro',
        })


# ─────────────────────────────────────────────────────────────────────────────
# QUALITY CULTURE SURVEYS (ISO 9001:2026 — Cultura y Ética)
# ─────────────────────────────────────────────────────────────────────────────

class QualityCultureSurveyViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet para Encuestas Anónimas de Cultura de Calidad"""
    queryset = QualityCultureSurvey.objects.all()
    serializer_class = QualityCultureSurveySerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'created_at']
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

    @action(detail=True, methods=['get'])
    def aggregate_results(self, request, pk=None):
        """
        Devuelve resultados AGREGADOS de la encuesta.
        Solo disponible si hay >= min_responses (privacidad por diseño).
        """
        survey = self.get_object()
        ai_service = LeadershipAIService()
        result = ai_service.aggregate_culture_survey({
            'organization_id': survey.organization_id,
            'survey_id': survey.id,
        })
        return Response(result)


class SurveyResponseViewSet(viewsets.GenericViewSet):
    """
    Endpoint anónimo para responder encuestas de cultura.
    NO requiere autenticación — respuestas puramente anónimas.
    NO expone listado ni detalle de respuestas individuales.
    """
    serializer_class = SurveyResponseSerializer
    permission_classes = []   # Público — sin autenticación requerida

    @action(detail=False, methods=['post'], url_path='submit')
    def submit(self, request):
        """
        Enviar respuesta anónima.
        Regla de privacidad: no se acepta user/user_id/email.
        """
        # Validar regla de privacidad primero
        rule_result = _iso_rules.validate_no_individual_survey_data(request.data)
        if not rule_result.passed:
            blockers = [v.message for v in rule_result.violations]
            return Response({'error': blockers}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Generar session_hash sin vincularlo al usuario
        session_seed = f"{request.META.get('HTTP_USER_AGENT', '')}{timezone.now().isoformat()}"
        session_hash = hashlib.sha256(session_seed.encode()).hexdigest()

        survey = serializer.validated_data['survey']
        if SurveyResponse.objects.filter(survey=survey, session_hash=session_hash).exists():
            return Response(
                {'error': 'Esta sesión ya respondió la encuesta.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        SurveyResponse.objects.create(
            survey=survey,
            responses=serializer.validated_data['responses'],
            session_hash=session_hash,
        )
        return Response({'status': 'Respuesta registrada de forma anónima. Gracias.'}, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# AI GOVERNANCE LOG VIEWSET
# ─────────────────────────────────────────────────────────────────────────────

class AIGovernanceLogViewSet(OrganizationQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Logs de Gobernanza de IA.
    READ-ONLY para lista/detalle. Solo los propietarios pueden registrar decisión humana.
    """
    queryset = AIGovernanceLog.objects.all()
    serializer_class = AIGovernanceLogSerializer
    permission_classes = [IsAuthenticated, OrganizationPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'operation', 'human_decision', 'module']
    search_fields = ['operation', 'response_summary']
    ordering_fields = ['created_at', 'operation']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def decide(self, request, pk=None):
        """
        Registra la decisión humana sobre una recomendación IA.
        Opciones: accepted / rejected / modified
        """
        log = self.get_object()
        decision = request.data.get('decision', '')
        notes = request.data.get('notes', '')
        try:
            log.record_human_decision(request.user, decision, notes)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'status': 'Decisión registrada',
            'human_decision': log.human_decision,
            'decided_by': request.user.get_full_name(),
            'decided_at': log.decided_at,
        })

    @action(detail=False, methods=['get'])
    def pending_decisions(self, request):
        """Lista logs con decisión humana pendiente para la organización."""
        org_id = getattr(request, 'organization_id', None)
        qs = self.get_queryset().filter(human_decision='pending')
        if org_id:
            qs = qs.filter(organization_id=org_id)
        serializer = self.get_serializer(qs[:20], many=True)
        return Response({'count': qs.count(), 'results': serializer.data})


# ─────────────────────────────────────────────────────────────────────────────
# AI ENDPOINTS — Motor IA Híbrido (RAG + Reglas ISO)
# Principio: NADA se publica automáticamente. Todo es borrador para aprobación.
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_generate_policy_draft(request):
    """
    Genera borrador de política de calidad con IA.
    Primero valida reglas ISO; luego invoca RAG + LLM.
    Output: borrador que requiere aprobación explícita.
    """
    org_id = getattr(request, 'organization_id', None)
    if not org_id:
        return Response({'error': 'organization_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

    context_data = request.data.get('context', {})
    ai_service = LeadershipAIService()
    result = ai_service.generate_policy_draft({'organization_id': org_id, **context_data})

    # Persistir log de gobernanza
    gov_data = result.pop('governance_log_data', {})
    if gov_data:
        allowed_fields = {f.name for f in AIGovernanceLog._meta.get_fields()}
        AIGovernanceLog.objects.create(**{k: v for k, v in gov_data.items() if k in allowed_fields})

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_analyze_voc(request):
    """
    Análisis NLP de Voz del Cliente.
    Detecta patrones, riesgos de satisfacción y propone acciones preventivas.
    """
    org_id = getattr(request, 'organization_id', None)
    if not org_id:
        return Response({'error': 'organization_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

    ai_service = LeadershipAIService()
    result = ai_service.analyze_voc_patterns({'organization_id': org_id})

    gov_data = result.pop('governance_log_data', {})
    if gov_data:
        allowed_fields = {f.name for f in AIGovernanceLog._meta.get_fields()}
        AIGovernanceLog.objects.create(**{k: v for k, v in gov_data.items() if k in allowed_fields})

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_detect_raci_gaps(request):
    """Detecta brechas en matrices RACI activas (sin R, sin A, sobrecargas, duplicidades)."""
    org_id = getattr(request, 'organization_id', None)
    if not org_id:
        return Response({'error': 'organization_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

    ai_service = LeadershipAIService()
    result = ai_service.detect_raci_gaps({'organization_id': org_id})
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_detect_policy_incoherences(request):
    """Detecta incoherencias entre la política de calidad y los resultados/objetivos actuales."""
    org_id = getattr(request, 'organization_id', None)
    if not org_id:
        return Response({'error': 'organization_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

    ai_service = LeadershipAIService()
    result = ai_service.detect_policy_incoherences({'organization_id': org_id})
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_validate_iso_rules(request):
    """
    Valida datos contra reglas ISO duras antes de guardar.
    Endpoint de pre-validación para feedback inmediato en el frontend.
    """
    entity_type = request.data.get('entity_type', '')
    data = request.data.get('data', {})

    rule_result = _iso_rules.validate_all(entity_type, data)
    return Response({
        'passed': rule_result.passed,
        'violations': [
            {
                'rule_id': v.rule_id,
                'severity': v.severity,
                'message': v.message,
                'field': v.field,
                'suggestion': v.suggestion,
            }
            for v in rule_result.violations
        ],
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_generate_auditor_pack(request):
    """
    Genera el Auditor Pack: datos estructurados para exportación PDF/ZIP.
    Incluye: políticas, actas, decisiones, registros de aprobación,
    grafo de evidencias, roles y RACI.
    """
    org_id = getattr(request, 'organization_id', None)
    if not org_id:
        return Response({'error': 'organization_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

    ai_service = LeadershipAIService()
    pack_data = ai_service.build_auditor_pack_data(org_id, request.user)
    return Response(pack_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leadership_cockpit_kpis(request):
    """
    Dashboard ejecutivo: 8-12 KPIs clave del módulo de Liderazgo.
    Para el Cockpit de Liderazgo en el frontend.
    """
    org_id = getattr(request, 'organization_id', None)
    if not org_id and not request.user.is_superuser:
        return Response({'error': 'organization_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

    from django.db.models import Count, Q

    stats = {}

    # 1. Política activa
    active_policy = QualityPolicy.objects.filter(
        organization_id=org_id, status='active'
    ).order_by('-version').first()
    stats['active_policy'] = {
        'version': active_policy.version if active_policy else None,
        'effective_date': str(active_policy.effective_date) if active_policy else None,
        'review_due': str(active_policy.review_date) if active_policy else None,
    }

    # 2. Revisiones por la dirección
    review_stats = ManagementReview.objects.filter(organization_id=org_id).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        planned=Count('id', filter=Q(status='planned')),
        with_signed_minutes=Count('id', filter=Q(minutes_approved_at__isnull=False)),
    )
    stats['management_reviews'] = review_stats

    # 3. Decisiones pendientes
    pending_decisions = ReviewDecision.objects.filter(
        review__organization_id=org_id,
        status__in=['proposed', 'approved', 'in_progress']
    ).count()
    overdue_decisions = ReviewDecision.objects.filter(
        review__organization_id=org_id,
        status__in=['proposed', 'approved', 'in_progress'],
        due_date__lt=timezone.now().date()
    ).count()
    stats['decisions'] = {'pending': pending_decisions, 'overdue': overdue_decisions}

    # 4. Roles y cobertura
    total_roles = OrganizationalRole.objects.filter(organization_id=org_id, is_active=True).count()
    assigned_roles = RoleAssignment.objects.filter(organization_id=org_id, is_active=True).count()
    stats['roles'] = {'total': total_roles, 'assigned': assigned_roles}

    # 5. RACI gaps (análisis rápido)
    raci_matrices_count = RACIMatrix.objects.filter(organization_id=org_id, is_active=True).count()
    stats['raci'] = {'active_matrices': raci_matrices_count}

    # 6. Gobernanza IA — decisiones pendientes
    ai_pending = AIGovernanceLog.objects.filter(
        organization_id=org_id, human_decision='pending'
    ).count()
    stats['ai_governance'] = {'pending_decisions': ai_pending}

    # 7. Aprobaciones inmutables registradas
    approval_records_count = ApprovalRecord.objects.filter(organization_id=org_id).count()
    stats['approval_records'] = {'total': approval_records_count}

    # 8. Encuestas de cultura activas
    active_surveys = QualityCultureSurvey.objects.filter(
        organization_id=org_id, status='active'
    ).count()
    stats['culture_surveys'] = {'active': active_surveys}

    # 9. Evidence graph nodes
    evidence_nodes_count = EvidenceNode.objects.filter(organization_id=org_id).count()
    approved_nodes = EvidenceNode.objects.filter(
        organization_id=org_id, approved_at__isnull=False
    ).count()
    stats['evidence_graph'] = {
        'total_nodes': evidence_nodes_count,
        'approved_nodes': approved_nodes,
    }

    # Alertas tempranas
    alerts = []
    if overdue_decisions > 0:
        alerts.append({
            'type': 'warning',
            'category': 'decisions',
            'message': f'{overdue_decisions} decisión(es) de revisión vencidas.',
        })
    if ai_pending > 3:
        alerts.append({
            'type': 'info',
            'category': 'ai_governance',
            'message': f'{ai_pending} recomendaciones de IA pendientes de decisión humana.',
        })
    if not active_policy:
        alerts.append({
            'type': 'critical',
            'category': 'policy',
            'message': 'No hay política de calidad activa. ISO 5.2 requiere una política vigente.',
        })
    if total_roles > 0 and assigned_roles == 0:
        alerts.append({
            'type': 'warning',
            'category': 'roles',
            'message': 'Roles definidos pero ninguno asignado a usuarios.',
        })

    return Response({
        'organization_id': org_id,
        'kpis': stats,
        'alerts': alerts,
        'generated_at': timezone.now().isoformat(),
    })
