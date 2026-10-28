# resources/serializers.py
"""
Serializers for Resources Module
"""

from rest_framework import serializers
from .models import (
    Resource,
    Infrastructure,
    WorkEnvironment,
    Competence,
    Training,
    Awareness,
    Communication
)


class ResourceSerializer(serializers.ModelSerializer):
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    
    class Meta:
        model = Resource
        fields = [
            'id', 'organization_id', 'organization_name',
            'resource_type', 'resource_type_display',
            'name', 'code', 'description',
            'quantity', 'unit', 'location',
            'status', 'status_display',
            'responsible', 'responsible_name',
            'acquisition_cost', 'maintenance_cost',
            'acquisition_date', 'next_maintenance_date',
            'documentation', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InfrastructureSerializer(serializers.ModelSerializer):
    infrastructure_type_display = serializers.CharField(source='get_infrastructure_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    
    class Meta:
        model = Infrastructure
        fields = [
            'id', 'organization_id', 'organization_name',
            'infrastructure_type', 'infrastructure_type_display',
            'name', 'code', 'description', 'location',
            'capacity', 'current_usage',
            'maintenance_schedule', 'last_maintenance_date', 'next_maintenance_date',
            'status', 'status_display',
            'responsible', 'responsible_name',
            'specifications', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WorkEnvironmentSerializer(serializers.ModelSerializer):
    overall_condition_display = serializers.CharField(source='get_overall_condition_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    
    class Meta:
        model = WorkEnvironment
        fields = [
            'id', 'organization_id', 'organization_name',
            'area_name', 'location', 'description',
            'temperature_control', 'humidity_control', 'lighting_adequate', 'noise_controlled',
            'ergonomic_conditions', 'safety_measures',
            'overall_condition', 'overall_condition_display',
            'last_evaluation_date', 'next_evaluation_date',
            'responsible', 'responsible_name',
            'improvement_actions', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CompetenceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    required_level_display = serializers.CharField(source='get_required_level_display', read_only=True)
    current_level_display = serializers.CharField(source='get_current_level_display', read_only=True)
    acquisition_method_display = serializers.CharField(source='get_acquisition_method_display', read_only=True)
    evaluator_name = serializers.CharField(source='evaluator.get_full_name', read_only=True)
    has_gap = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Competence
        fields = [
            'id', 'organization_id', 'organization_name',
            'user', 'user_name', 'position',
            'competence_name', 'description',
            'required_level', 'required_level_display',
            'current_level', 'current_level_display',
            'acquisition_method', 'acquisition_method_display',
            'evidence', 'acquired_date', 'expiration_date',
            'last_evaluation_date', 'evaluator', 'evaluator_name', 'evaluation_notes',
            'needs_improvement', 'improvement_plan', 'has_gap',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['has_gap', 'created_at', 'updated_at']


class TrainingSerializer(serializers.ModelSerializer):
    training_type_display = serializers.CharField(source='get_training_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    coordinator_name = serializers.CharField(source='coordinator.get_full_name', read_only=True)
    participants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Training
        fields = [
            'id', 'organization_id', 'organization_name',
            'title', 'code', 'description',
            'training_type', 'training_type_display',
            'instructor', 'provider',
            'start_date', 'end_date', 'duration_hours',
            'participants', 'participants_count', 'max_participants',
            'status', 'status_display',
            'cost', 'evaluation_method', 'passing_score',
            'materials', 'coordinator', 'coordinator_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['participants_count', 'created_at', 'updated_at']
    
    def get_participants_count(self, obj):
        return obj.participants.count()


class AwarenessSerializer(serializers.ModelSerializer):
    awareness_type_display = serializers.CharField(source='get_awareness_type_display', read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    participants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Awareness
        fields = [
            'id', 'organization_id', 'organization_name',
            'activity_name', 'description',
            'awareness_type', 'awareness_type_display',
            'method', 'method_display',
            'date', 'target_audience',
            'participants', 'participants_count',
            'responsible', 'responsible_name',
            'evidence', 'effectiveness_evaluation',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['participants_count', 'created_at', 'updated_at']
    
    def get_participants_count(self, obj):
        return obj.participants.count()


class CommunicationSerializer(serializers.ModelSerializer):
    communication_type_display = serializers.CharField(source='get_communication_type_display', read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    communicator_name = serializers.CharField(source='communicator.get_full_name', read_only=True)
    
    class Meta:
        model = Communication
        fields = [
            'id', 'organization_id', 'organization_name',
            'title', 'description',
            'communication_type', 'communication_type_display',
            'method', 'method_display',
            'frequency', 'frequency_display',
            'content_summary',
            'scheduled_date', 'last_communication_date',
            'target_audience',
            'communicator', 'communicator_name',
            'evidence', 'status', 'status_display',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
