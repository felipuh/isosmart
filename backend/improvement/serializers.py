# improvement/serializers.py
"""
Serializers for Improvement Module
"""

from rest_framework import serializers
from .models import Nonconformity, CorrectiveAction, ContinualImprovement


class CorrectiveActionSerializer(serializers.ModelSerializer):
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    nonconformity_number = serializers.CharField(source='nonconformity.nc_number', read_only=True)

    class Meta:
        model = CorrectiveAction
        fields = [
            'id', 'organization_id', 'nonconformity', 'nonconformity_number',
            'action_number', 'action_type', 'action_type_display',
            'root_cause_analysis', 'root_cause_identified', 'analysis_method',
            'action_description', 'implementation_steps', 'resources_required',
            'responsible', 'responsible_name',
            'planned_start_date', 'planned_completion_date',
            'actual_start_date', 'actual_completion_date',
            'verification_method', 'verification_date', 'verified_by', 'verified_by_name',
            'verification_result',
            'effectiveness_criteria', 'effectiveness_review_date',
            'effectiveness_result', 'is_effective',
            'status', 'status_display', 'completion_percentage',
            'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, attrs):
        nonconformity = attrs.get('nonconformity') or getattr(self.instance, 'nonconformity', None)
        organization_id = attrs.get('organization_id') or getattr(self.instance, 'organization_id', None)

        if nonconformity and organization_id and nonconformity.organization_id != organization_id:
            raise serializers.ValidationError({
                'organization_id': 'Debe coincidir con la organizacion de la no conformidad.'
            })

        return attrs


class NonconformitySerializer(serializers.ModelSerializer):
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    detected_by_name = serializers.CharField(source='detected_by.get_full_name', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    corrective_actions = CorrectiveActionSerializer(many=True, read_only=True)
    corrective_actions_count = serializers.SerializerMethodField()

    class Meta:
        model = Nonconformity
        fields = [
            'id', 'organization_id', 'organization_name',
            'nc_number', 'title', 'description',
            'source', 'source_display',
            'detection_date', 'detected_by', 'detected_by_name',
            'severity', 'severity_display',
            'affected_process', 'iso_clause_reference',
            'impact_description', 'estimated_cost',
            'immediate_action_taken', 'containment_measures',
            'status', 'status_display',
            'responsible', 'responsible_name',
            'evidence_files',
            'target_closure_date', 'actual_closure_date',
            'corrective_actions', 'corrective_actions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_corrective_actions_count(self, obj):
        return obj.corrective_actions.count()


class ContinualImprovementSerializer(serializers.ModelSerializer):
    improvement_type_display = serializers.CharField(source='get_improvement_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    champion_name = serializers.CharField(source='champion.get_full_name', read_only=True)

    class Meta:
        model = ContinualImprovement
        fields = [
            'id', 'organization_id', 'organization_name',
            'initiative_number', 'title', 'description',
            'improvement_type', 'improvement_type_display',
            'current_situation', 'proposed_improvement', 'expected_benefits',
            'alignment_with_objectives',
            'estimated_investment', 'estimated_savings', 'expected_roi',
            'payback_period_months',
            'success_criteria', 'kpis_to_measure', 'baseline_measurements', 'target_measurements',
            'priority', 'priority_display',
            'champion', 'champion_name', 'team_members',
            'proposed_date', 'approval_date', 'start_date', 'completion_date', 'review_date',
            'implementation_plan', 'milestones', 'risks_and_mitigation',
            'actual_results', 'lessons_learned', 'recommendations',
            'status', 'status_display', 'completion_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
