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
    CustomerFocusEvidence
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
