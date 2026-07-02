from rest_framework import serializers

from .models import (
    AssistantAuditLog,
    AssistantConversation,
    AssistantFeedback,
    AssistantMemoryItem,
    AssistantMessage,
    AssistantOrgProfile,
    AssistantPromptConfig,
)


class AssistantConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantConversation
        fields = [
            'id', 'organization_id', 'user', 'title', 'status',
            'current_route', 'current_module', 'current_submodule',
            'last_standard_focus', 'last_clause_focus', 'context_summary',
            'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')


class AssistantMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMessage
        fields = [
            'id', 'conversation', 'organization_id', 'role', 'content',
            'content_type', 'model_name', 'token_usage_prompt',
            'token_usage_completion', 'token_usage_total', 'latency_ms',
            'created_at',
        ]
        read_only_fields = ('created_at',)

    def validate(self, attrs):
        conversation = attrs.get('conversation') or getattr(self.instance, 'conversation', None)
        organization_id = attrs.get('organization_id') or getattr(self.instance, 'organization_id', None)
        if conversation and organization_id and conversation.organization_id != organization_id:
            raise serializers.ValidationError({'organization_id': 'Debe coincidir con la organización de la conversación.'})
        return attrs


class AssistantOrgProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantOrgProfile
        fields = [
            'id', 'organization_id', 'primary_standards',
            'secondary_standards', 'industry', 'risk_tolerance',
            'organization_summary', 'preferred_response_style',
            'forbidden_topics', 'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')


class AssistantMemoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMemoryItem
        fields = [
            'id', 'organization_id', 'memory_type', 'title', 'content',
            'source_type', 'source_id', 'module', 'standard_code',
            'clause_reference', 'confidence_score', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')


class AssistantPromptConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantPromptConfig
        fields = [
            'id', 'organization_id', 'system_prompt', 'normative_policy',
            'response_policy', 'citation_policy', 'enabled', 'updated_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')


class AssistantFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantFeedback
        fields = [
            'id', 'organization_id', 'conversation', 'message', 'user',
            'rating', 'feedback_text', 'created_at',
        ]
        read_only_fields = ('created_at',)

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('rating debe estar entre 1 y 5.')
        return value


class AssistantAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantAuditLog
        fields = [
            'id', 'organization_id', 'user', 'conversation', 'event_type',
            'metadata', 'created_at',
        ]
        read_only_fields = ('created_at',)
