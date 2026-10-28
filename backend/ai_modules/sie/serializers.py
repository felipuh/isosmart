"""
Serializers para Stakeholder Intelligence Engine (SIE)
Django REST Framework
"""

from rest_framework import serializers
from ai_modules.sie.models.stakeholder import (
    StakeholderProfile,
    StakeholderChangeLog,
    StakeholderRelationship,
    StakeholderEngagementPlan
)


class StakeholderProfileSerializer(serializers.ModelSerializer):
    """Serializer para Stakeholder Profile"""
    
    engagement_category = serializers.ReadOnlyField()
    risk_level = serializers.ReadOnlyField()
    
    class Meta:
        model = StakeholderProfile
        fields = [
            'id', 'name', 'stakeholder_type', 'organization', 
            'contact_person', 'email', 'phone',
            'power', 'interest', 'influence_score', 'satisfaction_score',
            'expectations', 'requirements',
            'communication_frequency', 'preferred_channel',
            'notes', 'is_active', 'created_at', 'last_updated', 'last_contact',
            'engagement_category', 'risk_level'
        ]
        read_only_fields = ['created_at', 'last_updated', 'influence_score']


class StakeholderProfileListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    engagement_category = serializers.ReadOnlyField()
    risk_level = serializers.ReadOnlyField()
    
    class Meta:
        model = StakeholderProfile
        fields = [
            'id', 'name', 'stakeholder_type', 'organization',
            'power', 'interest', 'influence_score', 'satisfaction_score',
            'is_active', 'engagement_category', 'risk_level'
        ]


class StakeholderChangeLogSerializer(serializers.ModelSerializer):
    """Serializer para Change Logs"""
    
    stakeholder_name = serializers.CharField(source='stakeholder.name', read_only=True)
    
    class Meta:
        model = StakeholderChangeLog
        fields = [
            'id', 'stakeholder', 'stakeholder_name', 'change_type',
            'previous_state', 'new_state', 'similarity_score',
            'detected_at', 'alert_sent'
        ]
        read_only_fields = ['detected_at']


class StakeholderRelationshipSerializer(serializers.ModelSerializer):
    """Serializer para relaciones entre stakeholders"""
    
    from_stakeholder_name = serializers.CharField(source='from_stakeholder.name', read_only=True)
    to_stakeholder_name = serializers.CharField(source='to_stakeholder.name', read_only=True)
    
    class Meta:
        model = StakeholderRelationship
        fields = [
            'id', 'from_stakeholder', 'from_stakeholder_name',
            'to_stakeholder', 'to_stakeholder_name',
            'relationship_type', 'strength', 'description',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class StakeholderEngagementPlanSerializer(serializers.ModelSerializer):
    """Serializer para planes de engagement"""
    
    stakeholder_name = serializers.CharField(source='stakeholder.name', read_only=True)
    
    class Meta:
        model = StakeholderEngagementPlan
        fields = [
            'id', 'stakeholder', 'stakeholder_name', 'plan_title',
            'objectives', 'actions', 'success_metrics',
            'status', 'start_date', 'end_date',
            'effectiveness_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NetworkVisualizationSerializer(serializers.Serializer):
    """Serializer para datos de visualización de red"""
    
    nodes = serializers.ListField(child=serializers.DictField())
    edges = serializers.ListField(child=serializers.DictField())
    statistics = serializers.DictField()


class StakeholderAnalysisResultSerializer(serializers.Serializer):
    """Serializer para resultados del análisis de IA"""
    
    status = serializers.CharField()
    message = serializers.CharField(required=False, allow_null=True)
    module = serializers.CharField(required=False, allow_null=True)
    iso_clause = serializers.CharField(required=False, allow_null=True)
    execution_time = serializers.FloatField(required=False, allow_null=True)
    stakeholders_analyzed = serializers.IntegerField(required=False, allow_null=True)
    stakeholders_count = serializers.IntegerField(required=False, allow_null=True)
    critical_stakeholders = serializers.ListField(child=serializers.DictField(), required=False, allow_null=True)
    changes_detected = serializers.ListField(child=serializers.DictField(), required=False, allow_null=True)
    network_statistics = serializers.DictField(required=False, allow_null=True)
    influence_metrics = serializers.DictField(required=False, allow_null=True)
    network_visualization = NetworkVisualizationSerializer(required=False, allow_null=True)
    recommendations = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)

