# improvement/admin.py
"""
Admin for Improvement Module
"""

from django.contrib import admin
from .models import Nonconformity, CorrectiveAction, ContinualImprovement


@admin.register(Nonconformity)
class NonconformityAdmin(admin.ModelAdmin):
    list_display = [
        'nc_number', 'title', 'source', 'severity', 'status',
        'detection_date', 'organization_name'
    ]
    list_filter = ['source', 'severity', 'status', 'detection_date']
    search_fields = ['nc_number', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'detection_date'


@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(admin.ModelAdmin):
    list_display = [
        'action_number', 'nonconformity', 'action_type', 'status',
        'completion_percentage', 'planned_completion_date'
    ]
    list_filter = ['action_type', 'status', 'is_effective']
    search_fields = ['action_number', 'action_description', 'root_cause_identified']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContinualImprovement)
class ContinualImprovementAdmin(admin.ModelAdmin):
    list_display = [
        'initiative_number', 'title', 'improvement_type', 'priority',
        'status', 'completion_percentage', 'organization_name'
    ]
    list_filter = ['improvement_type', 'priority', 'status']
    search_fields = ['initiative_number', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'proposed_date'
