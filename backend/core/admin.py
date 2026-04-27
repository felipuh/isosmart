from django.contrib import admin
from .models import (
    ContextAnalysis, Document, FeatureFlag, StakeholderProfile, StakeholderChangeLog,
    ScopeElement, ScopeAudit, ProcessMap, RiskMatrix, QualityObjective,
    ChangeLog, AIModelVersion, AIAuditLog, BillingSubscription, BillingPayment,
    NotificationDelivery,
)

@admin.register(ContextAnalysis)
class ContextAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'status', 'total_documents_processed', 'execution_time_seconds']
    list_filter = ['status', 'timestamp']
    search_fields = ['id']
    readonly_fields = ['timestamp', 'execution_time_seconds']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'source', 'is_processed', 'created_at']
    list_filter = ['document_type', 'is_processed', 'created_at']
    search_fields = ['title', 'content', 'source']
    date_hierarchy = 'created_at'

@admin.register(StakeholderProfile)
class StakeholderProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'stakeholder_type', 'influence_score', 'power', 'interest', 'is_active']
    list_filter = ['stakeholder_type', 'power', 'interest', 'is_active']
    search_fields = ['name']
    ordering = ['-influence_score']

@admin.register(StakeholderChangeLog)
class StakeholderChangeLogAdmin(admin.ModelAdmin):
    list_display = ['stakeholder', 'change_type', 'similarity_score', 'detected_at', 'alert_sent']
    list_filter = ['change_type', 'alert_sent', 'detected_at']
    date_hierarchy = 'detected_at'

@admin.register(ScopeElement)
class ScopeElementAdmin(admin.ModelAdmin):
    list_display = ['process_id', 'process_name', 'included', 'process_type', 'version']
    list_filter = ['included', 'process_type']
    search_fields = ['process_id', 'process_name']

@admin.register(ScopeAudit)
class ScopeAuditAdmin(admin.ModelAdmin):
    list_display = ['id', 'audit_date', 'coverage_percentage', 'status']
    list_filter = ['status', 'audit_date']
    date_hierarchy = 'audit_date'

@admin.register(ProcessMap)
class ProcessMapAdmin(admin.ModelAdmin):
    list_display = ['process_id', 'process_name', 'owner', 'health_status', 'version', 'updated_at']
    list_filter = ['health_status', 'updated_at']
    search_fields = ['process_id', 'process_name', 'owner']

@admin.register(RiskMatrix)
class RiskMatrixAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_module', 'risk_level', 'status', 'responsible', 'detection_date']
    list_filter = ['source_module', 'risk_level', 'status', 'risk_category']
    search_fields = ['risk_description', 'responsible']
    date_hierarchy = 'detection_date'
    ordering = ['-detection_date']

@admin.register(QualityObjective)
class QualityObjectiveAdmin(admin.ModelAdmin):
    list_display = ['indicator_name', 'responsible', 'status', 'progress_percentage', 'deadline']
    list_filter = ['status', 'source_module', 'measurement_frequency']
    search_fields = ['indicator_name', 'objective_description', 'responsible']
    date_hierarchy = 'deadline'

@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'change_type', 'status', 'responsible', 'detection_date']
    list_filter = ['change_type', 'status', 'detection_date']
    search_fields = ['change_description', 'responsible']
    date_hierarchy = 'detection_date'

@admin.register(AIModelVersion)
class AIModelVersionAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'framework', 'status', 'training_date']
    list_filter = ['status', 'framework', 'training_date']
    search_fields = ['name', 'version']

@admin.register(AIAuditLog)
class AIAuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'model_name', 'model_version', 'timestamp', 'inference_time_ms', 'confidence_score']
    list_filter = ['model_name', 'timestamp']
    search_fields = ['model_name', 'user_id']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp', 'input_hash', 'output_hash']


@admin.register(BillingSubscription)
class BillingSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'status', 'payment_method', 'next_due_date', 'grace_days', 'auto_suspend_enabled']
    list_filter = ['status', 'payment_method', 'auto_suspend_enabled', 'currency']
    search_fields = ['organization__name', 'payer_name', 'payer_email']
    readonly_fields = ['created_at', 'updated_at', 'suspended_at', 'cancelled_at']


@admin.register(BillingPayment)
class BillingPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'subscription', 'status', 'payment_method', 'amount', 'currency', 'due_date', 'paid_at', 'evidence_file']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['subscription__organization__name', 'reference']
    readonly_fields = ['created_at', 'updated_at', 'evidence_uploaded_at']


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'organization', 'channel', 'status', 'sent_at', 'created_at']
    list_filter = ['event_type', 'channel', 'status', 'created_at']
    search_fields = ['organization__name', 'subject', 'event_key']


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['name', 'scope', 'organization', 'enabled', 'updated_at']
    list_filter = ['scope', 'enabled']
    search_fields = ['name', 'description', 'organization__name']
    list_editable = ['enabled']
    readonly_fields = ['created_at', 'updated_at']