# operations/serializers.py
"""
Serializers for Operations Module
"""

from rest_framework import serializers
from .models import (
    OperationalControl,
    CustomerRequirement,
    DesignProject,
    ExternalProvider,
    ProductionControl,
    ProductRelease,
    Nonconformity,
    Disposition
)


class OperationalControlSerializer(serializers.ModelSerializer):
    control_type_display = serializers.CharField(source='get_control_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    
    class Meta:
        model = OperationalControl
        fields = [
            'id', 'organization_id', 'organization_name',
            'control_code', 'control_name', 'description',
            'control_type', 'control_type_display',
            'related_process', 'acceptance_criteria',
            'required_resources',
            'responsible', 'responsible_name',
            'frequency', 'frequency_display',
            'procedure_reference',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CustomerRequirementSerializer(serializers.ModelSerializer):
    requirement_type_display = serializers.CharField(source='get_requirement_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    
    class Meta:
        model = CustomerRequirement
        fields = [
            'id', 'organization_id', 'organization_name',
            'customer_name', 'customer_code', 'contact_person',
            'requirement_code', 'requirement_title', 'description',
            'requirement_type', 'requirement_type_display',
            'communication_date', 'communication_method',
            'is_reviewed', 'review_date', 'reviewed_by', 'reviewed_by_name', 'review_notes',
            'is_confirmed', 'confirmation_date', 'confirmation_evidence',
            'can_meet_requirement', 'capacity_notes',
            'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DesignProjectSerializer(serializers.ModelSerializer):
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    current_stage_display = serializers.CharField(source='get_current_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_leader_name = serializers.CharField(source='project_leader.get_full_name', read_only=True)
    team_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DesignProject
        fields = [
            'id', 'organization_id', 'organization_name',
            'project_code', 'project_name', 'description',
            'project_type', 'project_type_display',
            'current_stage', 'current_stage_display',
            'design_inputs', 'design_outputs', 'design_controls',
            'verification_method', 'is_verified', 'verification_date', 'verification_notes',
            'validation_method', 'is_validated', 'validation_date', 'validation_notes',
            'project_leader', 'project_leader_name',
            'team_members', 'team_count',
            'start_date', 'target_completion_date', 'actual_completion_date',
            'status', 'status_display',
            'documentation',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['team_count', 'created_at', 'updated_at']
    
    def get_team_count(self, obj):
        return obj.team_members.count()


class ExternalProviderSerializer(serializers.ModelSerializer):
    provision_type_display = serializers.CharField(source='get_provision_type_display', read_only=True)
    classification_display = serializers.CharField(source='get_classification_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    
    class Meta:
        model = ExternalProvider
        fields = [
            'id', 'organization_id', 'organization_name',
            'provider_code', 'provider_name',
            'contact_person', 'email', 'phone', 'address',
            'provision_type', 'provision_type_display',
            'products_services',
            'evaluation_criteria', 'last_evaluation_date',
            'evaluation_score', 'evaluation_notes',
            'classification', 'classification_display',
            'performance_rating',
            'controls_applied',
            'responsible', 'responsible_name',
            'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductionControlSerializer(serializers.ModelSerializer):
    control_type_display = serializers.CharField(source='get_control_type_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    
    class Meta:
        model = ProductionControl
        fields = [
            'id', 'organization_id', 'organization_name',
            'control_code', 'product_service_name', 'description',
            'control_type', 'control_type_display',
            'control_method',
            'requires_traceability', 'traceability_method',
            'handles_customer_property', 'customer_property_controls',
            'preservation_requirements',
            'post_delivery_activities',
            'change_control_process',
            'responsible', 'responsible_name',
            'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductReleaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    authorized_by_name = serializers.CharField(source='authorized_by.get_full_name', read_only=True)
    
    class Meta:
        model = ProductRelease
        fields = [
            'id', 'organization_id', 'organization_name',
            'release_code', 'product_service_name', 'batch_lot_number',
            'release_date',
            'verification_performed', 'verification_results',
            'acceptance_criteria_met', 'criteria_details',
            'authorized_by', 'authorized_by_name', 'authorization_date',
            'traceability_info',
            'customer_name', 'delivery_date',
            'quantity_released', 'unit',
            'status', 'status_display',
            'notes', 'evidence',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DispositionSerializer(serializers.ModelSerializer):
    disposition_action_display = serializers.CharField(source='get_disposition_action_display', read_only=True)
    authorized_by_name = serializers.CharField(source='authorized_by.get_full_name', read_only=True)
    implemented_by_name = serializers.CharField(source='implemented_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    
    class Meta:
        model = Disposition
        fields = [
            'id', 'nonconformity',
            'disposition_action', 'disposition_action_display',
            'action_description',
            'requires_authorization',
            'authorized_by', 'authorized_by_name', 'authorization_date', 'authorization_notes',
            'implemented_by', 'implemented_by_name', 'implementation_date', 'implementation_notes',
            'is_verified', 'verification_date', 'verified_by', 'verified_by_name', 'verification_notes',
            'is_effective', 'effectiveness_notes',
            'estimated_cost', 'actual_cost',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NonconformitySerializer(serializers.ModelSerializer):
    nc_type_display = serializers.CharField(source='get_nc_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    detection_stage_display = serializers.CharField(source='get_detection_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    detected_by_name = serializers.CharField(source='detected_by.get_full_name', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    disposition = DispositionSerializer(read_only=True)
    has_disposition = serializers.SerializerMethodField()
    
    class Meta:
        model = Nonconformity
        fields = [
            'id', 'organization_id', 'organization_name',
            'nc_number', 'title', 'description',
            'detection_date', 'detected_by', 'detected_by_name',
            'detection_stage', 'detection_stage_display',
            'nc_type', 'nc_type_display',
            'severity', 'severity_display',
            'affected_product_service', 'batch_lot_number', 'quantity_affected',
            'affects_customer', 'customer_name', 'customer_notified', 'notification_date',
            'status', 'status_display',
            'responsible', 'responsible_name',
            'evidence',
            'disposition', 'has_disposition',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['has_disposition', 'created_at', 'updated_at']
    
    def get_has_disposition(self, obj):
        return hasattr(obj, 'disposition')
