# leadership/serializers.py
"""
Serializers for Leadership Module
"""

from rest_framework import serializers
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


class QualityPolicySerializer(serializers.ModelSerializer):
    """Serializer para Políticas de Calidad"""
    
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = QualityPolicy
        fields = [
            'id', 'organization_id', 'organization_name',
            'version', 'title', 'content',
            'customer_focus', 'framework_for_objectives',
            'commitment_requirements', 'commitment_improvement',
            'status', 'approved_by', 'approved_by_name',
            'approval_date', 'approval_comments',
            'effective_date', 'review_date',
            'is_published', 'communication_channels', 'published_date',
            'pdf_file', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['approved_by', 'approval_date', 'published_date', 'created_by', 'created_at', 'updated_at']


class OrganizationalRoleSerializer(serializers.ModelSerializer):
    """Serializer para Roles Organizacionales"""
    
    reports_to_name = serializers.CharField(source='reports_to.name', read_only=True)
    subordinates_count = serializers.SerializerMethodField()
    
    class Meta:
        model = OrganizationalRole
        fields = [
            'id', 'organization_id', 'organization_name',
            'name', 'code', 'description',
            'level', 'reports_to', 'reports_to_name',
            'responsibilities', 'authorities', 'required_competencies',
            'is_qms_role', 'is_active',
            'subordinates_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_subordinates_count(self, obj):
        return obj.subordinates.count()


class RoleAssignmentSerializer(serializers.ModelSerializer):
    """Serializer para Asignaciones de Roles"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    
    class Meta:
        model = RoleAssignment
        fields = [
            'id', 'organization_id',
            'role', 'role_name',
            'user', 'user_name', 'user_email',
            'start_date', 'end_date',
            'assignment_type', 'notes', 'is_active',
            'assigned_by', 'assigned_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['assigned_by', 'created_at', 'updated_at']


class RACIEntrySerializer(serializers.ModelSerializer):
    """Serializer para Entradas RACI"""
    
    responsible_roles_data = OrganizationalRoleSerializer(source='responsible_roles', many=True, read_only=True)
    accountable_roles_data = OrganizationalRoleSerializer(source='accountable_roles', many=True, read_only=True)
    consulted_roles_data = OrganizationalRoleSerializer(source='consulted_roles', many=True, read_only=True)
    informed_roles_data = OrganizationalRoleSerializer(source='informed_roles', many=True, read_only=True)
    
    class Meta:
        model = RACIEntry
        fields = [
            'id', 'matrix', 'activity', 'description', 'order',
            'responsible_roles', 'responsible_roles_data',
            'accountable_roles', 'accountable_roles_data',
            'consulted_roles', 'consulted_roles_data',
            'informed_roles', 'informed_roles_data'
        ]


class RACIMatrixSerializer(serializers.ModelSerializer):
    """Serializer para Matrices RACI"""
    
    entries = RACIEntrySerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    entries_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RACIMatrix
        fields = [
            'id', 'organization_id', 'organization_name',
            'name', 'description', 'is_active',
            'entries', 'entries_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_entries_count(self, obj):
        return obj.entries.count()


class LeadershipCommitmentSerializer(serializers.ModelSerializer):
    """Serializer para Compromisos de Liderazgo"""
    
    committed_by_name = serializers.CharField(source='committed_by.get_full_name', read_only=True)
    commitment_type_display = serializers.CharField(source='get_commitment_type_display', read_only=True)
    evidence_type_display = serializers.CharField(source='get_evidence_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = LeadershipCommitment
        fields = [
            'id', 'organization_id', 'organization_name',
            'commitment_type', 'commitment_type_display',
            'title', 'description',
            'evidence_type', 'evidence_type_display',
            'evidence_document', 'evidence_url',
            'commitment_date', 'committed_by', 'committed_by_name',
            'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CustomerFocusEvidenceSerializer(serializers.ModelSerializer):
    """Serializer para Evidencias de Enfoque al Cliente"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    focus_type_display = serializers.CharField(source='get_focus_type_display', read_only=True)
    
    class Meta:
        model = CustomerFocusEvidence
        fields = [
            'id', 'organization_id', 'organization_name',
            'focus_type', 'focus_type_display',
            'title', 'description',
            'action_taken', 'results', 'action_date',
            'evidence_file',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


# ─────────────────────────────────────────────────────────────
# NUEVOS SERIALIZERS — Evidence Graph, ManagementReview,
# ApprovalRecord, QualityCultureSurvey, AIGovernanceLog
# ─────────────────────────────────────────────────────────────

class EvidenceNodeSerializer(serializers.ModelSerializer):
    """Serializer para Nodos del Grafo de Evidencias"""

    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    outgoing_edges_count = serializers.SerializerMethodField()
    incoming_edges_count = serializers.SerializerMethodField()

    class Meta:
        model = EvidenceNode
        fields = [
            'id', 'organization_id', 'node_type', 'node_type_display',
            'title', 'description',
            'reference_id', 'reference_model',
            'data_source', 'expected_impact',
            'responsible', 'responsible_name',
            'approver', 'approver_name', 'approved_at',
            'metadata',
            'outgoing_edges_count', 'incoming_edges_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['approved_at', 'created_at', 'updated_at']

    def get_outgoing_edges_count(self, obj):
        return obj.outgoing_edges.count()

    def get_incoming_edges_count(self, obj):
        return obj.incoming_edges.count()


class EvidenceEdgeSerializer(serializers.ModelSerializer):
    """Serializer para Aristas del Grafo de Evidencias"""

    edge_type_display = serializers.CharField(source='get_edge_type_display', read_only=True)
    source_title = serializers.CharField(source='source.title', read_only=True)
    target_title = serializers.CharField(source='target.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = EvidenceEdge
        fields = [
            'id', 'source', 'source_title',
            'target', 'target_title',
            'edge_type', 'edge_type_display', 'label',
            'created_by', 'created_by_name', 'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']


class EvidenceGraphSerializer(serializers.Serializer):
    """Grafo completo de evidencias (nodos + aristas) para visualización"""
    nodes = EvidenceNodeSerializer(many=True)
    edges = EvidenceEdgeSerializer(many=True)


class ReviewDecisionSerializer(serializers.ModelSerializer):
    """Serializer para Decisiones de Revisión por la Dirección"""

    decision_type_display = serializers.CharField(source='get_decision_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)

    class Meta:
        model = ReviewDecision
        fields = [
            'id', 'review',
            'title', 'description',
            'decision_type', 'decision_type_display',
            'responsible', 'responsible_name',
            'due_date', 'status', 'status_display',
            'ai_suggested', 'rationale',
            'approved_by', 'approved_by_name', 'approved_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['approved_by', 'approved_at', 'created_at', 'updated_at']


class ManagementReviewSerializer(serializers.ModelSerializer):
    """Serializer para Revisiones por la Dirección"""

    review_type_display = serializers.CharField(source='get_review_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    facilitator_name = serializers.CharField(source='facilitator.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    minutes_approved_by_name = serializers.CharField(source='minutes_approved_by.get_full_name', read_only=True)
    ai_brief_approved_by_name = serializers.CharField(source='ai_brief_approved_by.get_full_name', read_only=True)
    decisions = ReviewDecisionSerializer(many=True, read_only=True)
    decisions_count = serializers.SerializerMethodField()

    class Meta:
        model = ManagementReview
        fields = [
            'id', 'organization_id', 'organization_name',
            'title', 'review_type', 'review_type_display',
            'scheduled_date', 'actual_date',
            'status', 'status_display',
            'facilitator', 'facilitator_name',
            'attendee_ids', 'agenda_items',
            'ai_brief', 'ai_brief_generated_at',
            'ai_brief_approved_by', 'ai_brief_approved_by_name', 'ai_brief_approved_at',
            'minutes', 'minutes_approved_by', 'minutes_approved_by_name', 'minutes_approved_at',
            'decisions', 'decisions_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'ai_brief', 'ai_brief_generated_at',
            'ai_brief_approved_by', 'ai_brief_approved_at',
            'minutes_approved_by', 'minutes_approved_at',
            'created_by', 'created_at', 'updated_at',
        ]

    def get_decisions_count(self, obj):
        return obj.decisions.count()


class ApprovalRecordSerializer(serializers.ModelSerializer):
    """Serializer para Registros Inmutables de Aprobación"""

    workflow_type_display = serializers.CharField(source='get_workflow_type_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True)

    class Meta:
        model = ApprovalRecord
        fields = [
            'id', 'organization_id',
            'workflow_type', 'workflow_type_display',
            'reference_id', 'reference_model',
            'title',
            'approved_by', 'approved_by_name', 'approved_by_email',
            'approved_at', 'digital_signature',
            'content_snapshot', 'ip_address', 'notes',
        ]
        # Todos los campos son de solo lectura — el registro es inmutable
        read_only_fields = [
            'approved_at', 'digital_signature', 'content_snapshot',
            'approved_by', 'ip_address',
        ]


class QualityCultureSurveySerializer(serializers.ModelSerializer):
    """Serializer para Encuestas de Cultura de Calidad"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    response_count = serializers.SerializerMethodField()
    has_enough_responses = serializers.SerializerMethodField()

    class Meta:
        model = QualityCultureSurvey
        fields = [
            'id', 'organization_id', 'organization_name',
            'title', 'description',
            'status', 'status_display',
            'start_date', 'end_date',
            'questions', 'min_responses_for_analysis',
            'response_count', 'has_enough_responses',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_response_count(self, obj):
        return obj.responses.count()

    def get_has_enough_responses(self, obj):
        return obj.responses.count() >= obj.min_responses_for_analysis


class SurveyResponseSerializer(serializers.ModelSerializer):
    """
    Serializer para Respuestas de Encuesta.
    Por diseño: NO se expone session_hash en respuestas, no se acepta user/email.
    """

    class Meta:
        model = SurveyResponse
        fields = ['id', 'survey', 'responses', 'submitted_at']
        read_only_fields = ['submitted_at']

    def validate(self, data):
        """Asegurar que no haya campos de identidad en la respuesta."""
        responses = data.get('responses', {})
        forbidden = {'user', 'user_id', 'email', 'nombre', 'name', 'dni', 'cedula'}
        found = forbidden & set(str(k).lower() for k in responses.keys())
        if found:
            raise serializers.ValidationError(
                f"Privacidad por diseño: no se permiten campos de identificación en respuestas: {found}"
            )
        return data


class AIGovernanceLogSerializer(serializers.ModelSerializer):
    """Serializer para Logs de Gobernanza de IA"""

    human_decision_display = serializers.CharField(source='get_human_decision_display', read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.get_full_name', read_only=True)

    class Meta:
        model = AIGovernanceLog
        fields = [
            'id', 'organization_id', 'module', 'operation',
            'model_version', 'prompt_template',
            # prompt_hash: auditable pero no expone el prompt completo
            'prompt_hash',
            'response_summary',
            'ai_recommendation', 'sources_cited',
            'hallucination_flags', 'privacy_check_passed',
            'human_decision', 'human_decision_display',
            'decided_by', 'decided_by_name', 'decided_at',
            'human_notes',
            'created_at',
        ]
        read_only_fields = [
            'prompt_hash', 'model_version', 'prompt_template',
            'response_summary', 'ai_recommendation', 'sources_cited',
            'hallucination_flags', 'privacy_check_passed',
            'created_at',
        ]
