from rest_framework import serializers
from .models import RiskMatrix, QualityObjective, Document


class RiskMatrixSerializer(serializers.ModelSerializer):
    source_module_display = serializers.CharField(source='get_source_module_display', read_only=True)
    probability_display = serializers.CharField(source='get_probability_display', read_only=True)
    impact_display = serializers.CharField(source='get_impact_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = RiskMatrix
        fields = [
            'id',
            'source_module',
            'source_module_display',
            'source_id',
            'risk_description',
            'risk_category',
            'probability',
            'probability_display',
            'impact',
            'impact_display',
            'risk_level',
            'risk_level_display',
            'mitigation_actions',
            'responsible',
            'iso_clause',
            'status',
            'status_display',
            'detection_date',
            'deadline',
            'process_id',
        ]
        read_only_fields = ['id', 'detection_date']


class QualityObjectiveSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = QualityObjective
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.ChoiceField(choices=Document.TYPE_CHOICES)
    file = serializers.FileField()
    source = serializers.CharField(max_length=255, required=False, default='Sistema')


# =====================================================
# Serializers para Configuración y Multicliente
# =====================================================

from .models import Organization, UserProfile, OrganizationSettings, ISOClauseConfig, AuditLog
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'organization', 'role', 'role_display', 'job_title',
            'department', 'phone', 'avatar', 'theme', 'language',
            'notifications_enabled', 'email_notifications', 'is_active',
            'full_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='user')
    job_title = serializers.CharField(max_length=100, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya existe")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        return value


class OrganizationSerializer(serializers.ModelSerializer):
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'logo', 'email', 'phone', 'address',
            'website', 'tax_id', 'legal_name', 'is_active', 'plan_type',
            'max_users', 'users_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_users_count(self, obj):
        return obj.users.count()


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSettings
        fields = [
            'id', 'organization',
            'ai_sca_enabled', 'ai_sie_enabled', 'ai_asb_enabled', 'ai_spm_enabled',
            'ai_auto_analysis', 'ai_analysis_frequency',
            'notify_risk_critical', 'notify_risk_high', 'notify_objective_deadline',
            'notify_document_upload', 'notify_stakeholder_change', 'notification_email',
            'iso_standard', 'fiscal_year_start',
            'auto_backup_enabled', 'backup_frequency', 'last_backup_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'last_backup_at', 'created_at', 'updated_at']


class ISOClauseConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOClauseConfig
        fields = [
            'id', 'organization', 'clause_number', 'clause_name',
            'description', 'is_applicable', 'exclusion_justification', 'responsible'
        ]
        read_only_fields = ['id', 'organization']


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'organization', 'user', 'user_name', 'action', 'action_display',
            'module', 'description', 'ip_address', 'created_at'
        ]
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "Sistema"
