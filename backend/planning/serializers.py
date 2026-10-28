# planning/serializers.py
"""
Serializers for Planning Module
"""

from rest_framework import serializers
from .models import (
    RiskOpportunity,
    QualityObjective,
    ObjectiveAction,
    ChangeControl,
    PlanningVersionRecord,
    PlanningApprovalRecord,
    PlanningAIGovernanceLog,
)


class RiskOpportunitySerializer(serializers.ModelSerializer):
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    context_display = serializers.CharField(source='get_context_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    treatment_display = serializers.CharField(source='get_treatment_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    normalized_probability = serializers.FloatField(read_only=True)
    normalized_impact = serializers.FloatField(read_only=True)
    level_band = serializers.CharField(read_only=True)
    
    class Meta:
        model = RiskOpportunity
        fields = [
            'id', 'organization_id', 'organization_name',
            'item_type', 'item_type_display',
            'code', 'title', 'description',
            'context', 'context_display',
            'category', 'category_display',
            'probability', 'impact', 'risk_level',
            'normalized_probability', 'normalized_impact', 'level_band',
            'feasibility', 'benefit', 'opportunity_score',
            'treatment', 'treatment_display', 'treatment_description',
            'owner', 'owner_name',
            'ai_sources', 'proposed_actions',
            'status', 'status_display',
            'approved_by', 'approved_by_name', 'approved_at', 'approval_notes',
            'review_date', 'last_review_date', 'review_notes',
            'related_processes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['risk_level', 'opportunity_score', 'created_at', 'updated_at']


class ObjectiveActionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ObjectiveAction
        fields = [
            'id', 'organization_id', 'objective',
            'action_number', 'description',
            'what_will_be_done', 'how_will_be_done',
            'responsible', 'responsible_name',
            'due_date', 'completion_date',
            'resources_needed', 'estimated_cost',
            'status', 'status_display',
            'progress_percentage',
            'effectiveness', 'effectiveness_notes',
            'evidence', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['is_overdue', 'created_at', 'updated_at']

    def validate(self, attrs):
        objective = attrs.get('objective') or getattr(self.instance, 'objective', None)
        organization_id = attrs.get('organization_id') or getattr(self.instance, 'organization_id', None)

        if objective and organization_id and objective.organization_id != organization_id:
            raise serializers.ValidationError({
                'organization_id': 'Debe coincidir con la organizacion del objetivo.'
            })

        return attrs


class QualityObjectiveSerializer(serializers.ModelSerializer):
    alignment_display = serializers.CharField(source='get_alignment_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    is_smart = serializers.BooleanField(read_only=True)
    achievement_percentage = serializers.FloatField(read_only=True)
    actions = ObjectiveActionSerializer(many=True, read_only=True)
    actions_count = serializers.SerializerMethodField()
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = QualityObjective
        fields = [
            'id', 'organization_id', 'organization_name',
            'code', 'title', 'description',
            'is_specific', 'is_measurable', 'is_achievable', 'is_relevant', 'is_time_bound',
            'is_smart',
            'alignment', 'alignment_display',
            'metric', 'baseline', 'target', 'current_value', 'unit',
            'achievement_percentage',
            'owner', 'owner_name',
            'start_date', 'target_date', 'completion_date',
            'status', 'status_display',
            'progress_percentage',
            'addresses_risks', 'leverages_opportunities',
            'required_resources', 'budget',
            'ai_recommendations', 'forecast_summary',
            'approved_by', 'approved_by_name', 'approval_date',
            'actions', 'actions_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_smart', 'achievement_percentage', 'actions_count', 'created_at', 'updated_at']

    def validate(self, attrs):
        organization_id = attrs.get('organization_id') or getattr(self.instance, 'organization_id', None)
        addresses_risks = attrs.get('addresses_risks')
        leverages_opportunities = attrs.get('leverages_opportunities')

        if organization_id and addresses_risks is not None:
            invalid = [item.id for item in addresses_risks if item.organization_id != organization_id]
            if invalid:
                raise serializers.ValidationError({
                    'addresses_risks': 'Todos los riesgos deben pertenecer a la misma organizacion.'
                })

        if organization_id and leverages_opportunities is not None:
            invalid = [item.id for item in leverages_opportunities if item.organization_id != organization_id]
            if invalid:
                raise serializers.ValidationError({
                    'leverages_opportunities': 'Todas las oportunidades deben pertenecer a la misma organizacion.'
                })

        return attrs
    
    def get_actions_count(self, obj):
        return obj.actions.count()


class ChangeControlSerializer(serializers.ModelSerializer):
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    implemented_by_name = serializers.CharField(source='implemented_by.get_full_name', read_only=True)
    
    class Meta:
        model = ChangeControl
        fields = [
            'id', 'organization_id', 'organization_name',
            'change_number', 'title', 'description',
            'change_type', 'change_type_display',
            'reason', 'reason_display',
            'justification',
            'urgency', 'urgency_display',
            'planned_date', 'actual_implementation_date',
            'affected_areas', 'impact_assessment',
            'potential_risks', 'mitigation_plan',
            'requested_by', 'requested_by_name',
            'approved_by', 'approved_by_name',
            'implemented_by', 'implemented_by_name',
            'status', 'status_display',
            'approval_date', 'approval_comments',
            'verification_date', 'verification_notes', 'is_effective',
            'related_documents', 'impact_estimated', 'implementation_plan', 'affected_versions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PlanningVersionRecordSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)

    class Meta:
        model = PlanningVersionRecord
        fields = [
            'id', 'organization_id', 'entity_type', 'entity_type_display', 'entity_id',
            'version_number', 'snapshot', 'changed_by', 'changed_by_name',
            'change_reason', 'created_at'
        ]
        read_only_fields = fields


class PlanningApprovalRecordSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    workflow_type_display = serializers.CharField(source='get_workflow_type_display', read_only=True)

    class Meta:
        model = PlanningApprovalRecord
        fields = [
            'id', 'organization_id', 'workflow_type', 'workflow_type_display',
            'reference_model', 'reference_id', 'title', 'approved_by', 'approved_by_name',
            'approved_at', 'digital_signature', 'content_snapshot', 'notes'
        ]
        read_only_fields = fields


class PlanningAIGovernanceLogSerializer(serializers.ModelSerializer):
    decided_by_name = serializers.CharField(source='decided_by.get_full_name', read_only=True)
    human_decision_display = serializers.CharField(source='get_human_decision_display', read_only=True)

    class Meta:
        model = PlanningAIGovernanceLog
        fields = [
            'id', 'organization_id', 'operation', 'model_version', 'prompt_template', 'prompt_hash',
            'response_summary', 'ai_recommendation', 'data_sources', 'privacy_check_passed',
            'human_decision', 'human_decision_display', 'decided_by', 'decided_by_name',
            'decided_at', 'human_notes', 'created_at'
        ]
        read_only_fields = [
            'model_version', 'prompt_template', 'prompt_hash', 'response_summary',
            'ai_recommendation', 'data_sources', 'privacy_check_passed', 'created_at'
        ]
