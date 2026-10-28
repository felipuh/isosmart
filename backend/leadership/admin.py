# leadership/admin.py
"""
Admin configuration for Leadership Module
"""

from django.contrib import admin
from .models import (
    QualityPolicy,
    OrganizationalRole,
    RoleAssignment,
    RACIMatrix,
    RACIEntry,
    LeadershipCommitment,
    CustomerFocusEvidence
)


@admin.register(QualityPolicy)
class QualityPolicyAdmin(admin.ModelAdmin):
    list_display = ['title', 'version', 'organization_name', 'status', 'is_published', 'effective_date']
    list_filter = ['status', 'is_published', 'organization_name']
    search_fields = ['title', 'version', 'content', 'organization_name']
    readonly_fields = ['created_at', 'updated_at', 'approval_date', 'published_date']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('version', 'title', 'content')
        }),
        ('Requisitos ISO 9001', {
            'fields': ('customer_focus', 'framework_for_objectives', 
                      'commitment_requirements', 'commitment_improvement')
        }),
        ('Estado y Aprobación', {
            'fields': ('status', 'approved_by', 'approval_date', 'approval_comments')
        }),
        ('Vigencia', {
            'fields': ('effective_date', 'review_date')
        }),
        ('Publicación', {
            'fields': ('is_published', 'published_date', 'communication_channels')
        }),
        ('Archivos', {
            'fields': ('pdf_file',)
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OrganizationalRole)
class OrganizationalRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization_name', 'level', 'reports_to', 'is_qms_role', 'is_active']
    list_filter = ['level', 'is_qms_role', 'is_active', 'organization_name']
    search_fields = ['name', 'code', 'description', 'organization_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('name', 'code', 'description')
        }),
        ('Jerarquía', {
            'fields': ('level', 'reports_to')
        }),
        ('Responsabilidades y Autoridades', {
            'fields': ('responsibilities', 'authorities', 'required_competencies')
        }),
        ('Configuración', {
            'fields': ('is_qms_role', 'is_active')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assignment_type', 'start_date', 'end_date', 'is_active']
    list_filter = ['assignment_type', 'is_active']
    search_fields = ['user__username', 'user__email', 'role__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


class RACIEntryInline(admin.TabularInline):
    model = RACIEntry
    extra = 1
    fields = ['activity', 'description', 'order']
    ordering = ['order']


@admin.register(RACIMatrix)
class RACIMatrixAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization_name']
    search_fields = ['name', 'description', 'organization_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RACIEntryInline]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RACIEntry)
class RACIEntryAdmin(admin.ModelAdmin):
    list_display = ['activity', 'matrix', 'order']
    list_filter = ['matrix']
    search_fields = ['activity', 'description']
    filter_horizontal = ['responsible_roles', 'accountable_roles', 'consulted_roles', 'informed_roles']
    ordering = ['matrix', 'order']


@admin.register(LeadershipCommitment)
class LeadershipCommitmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'commitment_type', 'organization_name', 'status', 'commitment_date', 'committed_by']
    list_filter = ['commitment_type', 'status', 'evidence_type', 'organization_name']
    search_fields = ['title', 'description', 'organization_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'commitment_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('commitment_type', 'title', 'description')
        }),
        ('Evidencia', {
            'fields': ('evidence_type', 'evidence_document', 'evidence_url')
        }),
        ('Fecha y Responsable', {
            'fields': ('commitment_date', 'committed_by')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerFocusEvidence)
class CustomerFocusEvidenceAdmin(admin.ModelAdmin):
    list_display = ['title', 'focus_type', 'organization_name', 'action_date', 'created_by']
    list_filter = ['focus_type', 'organization_name']
    search_fields = ['title', 'description', 'action_taken', 'organization_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'action_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('focus_type', 'title', 'description')
        }),
        ('Acción y Resultados', {
            'fields': ('action_taken', 'results', 'action_date')
        }),
        ('Evidencia', {
            'fields': ('evidence_file',)
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
