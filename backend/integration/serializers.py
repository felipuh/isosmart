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
        read_only_fields = ('organization_id', 'user', 'created_at', 'updated_at')


class AssistantMessageSerializer(serializers.ModelSerializer):
    conversation = serializers.PrimaryKeyRelatedField(
        queryset=AssistantConversation.objects.none(),
        error_messages={
            'does_not_exist': 'Referencia de conversación inválida.',
            'incorrect_type': 'Referencia de conversación inválida.',
        },
    )

    class Meta:
        model = AssistantMessage
        fields = [
            'id', 'conversation', 'organization_id', 'role', 'content',
            'content_type', 'model_name', 'token_usage_prompt',
            'token_usage_completion', 'token_usage_total', 'latency_ms',
            'created_at',
        ]
        read_only_fields = ('organization_id', 'created_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        organization_id = getattr(request, 'organization_id', None)
        if organization_id:
            self.fields['conversation'].queryset = AssistantConversation.objects.filter(
                organization_id=organization_id,
            )

    def validate(self, attrs):
        conversation = attrs.get('conversation') or getattr(self.instance, 'conversation', None)
        request = self.context.get('request')
        organization_id = getattr(request, 'organization_id', None)
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
        read_only_fields = ('organization_id', 'created_at', 'updated_at')


class AssistantMemoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMemoryItem
        fields = [
            'id', 'organization_id', 'memory_type', 'title', 'content',
            'source_type', 'source_id', 'module', 'standard_code',
            'clause_reference', 'confidence_score', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ('organization_id', 'created_at', 'updated_at')


class AssistantPromptConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantPromptConfig
        fields = [
            'id', 'organization_id', 'system_prompt', 'normative_policy',
            'response_policy', 'citation_policy', 'enabled', 'updated_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = ('organization_id', 'updated_by', 'created_at', 'updated_at')


class AssistantFeedbackSerializer(serializers.ModelSerializer):
    conversation = serializers.PrimaryKeyRelatedField(
        queryset=AssistantConversation.objects.none(),
        error_messages={
            'does_not_exist': 'Referencia de conversación inválida.',
            'incorrect_type': 'Referencia de conversación inválida.',
        },
    )
    message = serializers.PrimaryKeyRelatedField(
        queryset=AssistantMessage.objects.none(),
        allow_null=True,
        required=False,
        error_messages={
            'does_not_exist': 'Referencia de mensaje inválida.',
            'incorrect_type': 'Referencia de mensaje inválida.',
        },
    )

    class Meta:
        model = AssistantFeedback
        fields = [
            'id', 'organization_id', 'conversation', 'message', 'user',
            'rating', 'feedback_text', 'created_at',
        ]
        read_only_fields = ('organization_id', 'user', 'created_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        organization_id = getattr(request, 'organization_id', None)
        if organization_id:
            self.fields['conversation'].queryset = AssistantConversation.objects.filter(
                organization_id=organization_id,
            )
            self.fields['message'].queryset = AssistantMessage.objects.filter(
                organization_id=organization_id,
                conversation__organization_id=organization_id,
            )

    def validate(self, attrs):
        conversation = attrs.get('conversation') or getattr(self.instance, 'conversation', None)
        message = attrs.get('message') if 'message' in attrs else getattr(self.instance, 'message', None)
        request = self.context.get('request')
        organization_id = getattr(request, 'organization_id', None)

        if not organization_id:
            raise serializers.ValidationError('No fue posible validar la organización activa.')
        if conversation.organization_id != organization_id:
            raise serializers.ValidationError({'conversation': 'Referencia de conversación inválida.'})
        if message and (
            message.organization_id != organization_id
            or message.conversation_id != conversation.id
        ):
            raise serializers.ValidationError({'message': 'Referencia de mensaje inválida.'})
        return attrs

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
        read_only_fields = fields
