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
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class AssistantMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMessage
        fields = '__all__'
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
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class AssistantMemoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMemoryItem
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class AssistantPromptConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantPromptConfig
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class AssistantFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantFeedback
        fields = '__all__'
        read_only_fields = ('created_at',)

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('rating debe estar entre 1 y 5.')
        return value


class AssistantAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantAuditLog
        fields = '__all__'
        read_only_fields = ('created_at',)
