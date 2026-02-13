from django.contrib import admin
from .models import (
    PerformanceIndicator, Measurement, DataAnalysis,
    InternalAudit, AuditFinding, ManagementReview
)

@admin.register(PerformanceIndicator)
class PerformanceIndicatorAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'indicator_type', 'target_value', 'unit_of_measure', 'frequency', 'status']
    list_filter = ['indicator_type', 'frequency', 'status']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['indicator', 'measurement_date', 'actual_value', 'target_value', 'variance_percentage', 'status']
    list_filter = ['status', 'measurement_date']
    search_fields = ['indicator__code', 'indicator__name', 'comments']
    readonly_fields = ['variance', 'variance_percentage', 'created_at', 'updated_at']
    date_hierarchy = 'measurement_date'

@admin.register(DataAnalysis)
class DataAnalysisAdmin(admin.ModelAdmin):
    list_display = ['title', 'analysis_type', 'period_start', 'period_end', 'status']
    list_filter = ['analysis_type', 'status']
    search_fields = ['title', 'objectives', 'findings']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(InternalAudit)
class InternalAuditAdmin(admin.ModelAdmin):
    list_display = ['audit_code', 'title', 'audit_type', 'planned_date', 'status']
    list_filter = ['audit_type', 'status', 'planned_date']
    search_fields = ['audit_code', 'title', 'objectives', 'scope']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'planned_date'

@admin.register(AuditFinding)
class AuditFindingAdmin(admin.ModelAdmin):
    list_display = ['finding_number', 'audit', 'finding_type', 'due_date', 'status']
    list_filter = ['finding_type', 'status']
    search_fields = ['finding_number', 'description', 'clause_reference']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ManagementReview)
class ManagementReviewAdmin(admin.ModelAdmin):
    list_display = ['review_code', 'title', 'scheduled_date', 'actual_date', 'status']
    list_filter = ['status', 'scheduled_date']
    search_fields = ['review_code', 'title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
