# planning/admin.py
"""
Admin configuration for Planning Module
"""

from django.contrib import admin
from .models import (
    RiskOpportunity,
    QualityObjective,
    ObjectiveAction,
    ChangeControl
)


class ObjectiveActionInline(admin.TabularInline):
    model = ObjectiveAction
    extra = 1
    fields = ['action_number', 'description', 'responsible', 'due_date', 'status', 'progress_percentage']
    readonly_fields = []


@admin.register(RiskOpportunity)
class RiskOpportunityAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'item_type', 'category', 'risk_level', 'opportunity_score', 'status', 'owner']
    list_filter = ['item_type', 'category', 'status', 'context', 'organization_name']
    search_fields = ['code', 'title', 'description']
    readonly_fields = ['risk_level', 'opportunity_score', 'created_at', 'updated_at']
    filter_horizontal = []
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Identificación', {
            'fields': ('item_type', 'code', 'title', 'description', 'context', 'category')
        }),
        ('Evaluación de Riesgo', {
            'fields': ('probability', 'impact', 'risk_level'),
            'classes': ('collapse',)
        }),
        ('Evaluación de Oportunidad', {
            'fields': ('feasibility', 'benefit', 'opportunity_score'),
            'classes': ('collapse',)
        }),
        ('Tratamiento', {
            'fields': ('treatment', 'treatment_description', 'owner')
        }),
        ('Estado y Seguimiento', {
            'fields': ('status', 'review_date', 'last_review_date', 'review_notes')
        }),
        ('Integración', {
            'fields': ('related_processes',)
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """Mostrar campos según el tipo"""
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.item_type == 'risk':
            # Ocultar campos de oportunidad
            return [fs for fs in fieldsets if 'Oportunidad' not in fs[0]]
        elif obj and obj.item_type == 'opportunity':
            # Ocultar campos de riesgo
            return [fs for fs in fieldsets if 'Riesgo' not in fs[0]]
        return fieldsets


@admin.register(QualityObjective)
class QualityObjectiveAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'status', 'progress_percentage', 'target_date', 'owner', 'is_smart']
    list_filter = ['status', 'alignment', 'organization_name', 'is_specific', 'is_measurable']
    search_fields = ['code', 'title', 'description']
    readonly_fields = ['is_smart', 'achievement_percentage', 'created_at', 'updated_at']
    filter_horizontal = ['addresses_risks', 'leverages_opportunities']
    date_hierarchy = 'target_date'
    inlines = [ObjectiveActionInline]
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Identificación', {
            'fields': ('code', 'title', 'description', 'alignment')
        }),
        ('Criterios SMART', {
            'fields': (
                ('is_specific', 'is_measurable', 'is_achievable', 'is_relevant', 'is_time_bound'),
                'is_smart'
            )
        }),
        ('Medición', {
            'fields': ('metric', 'baseline', 'target', 'current_value', 'unit', 'achievement_percentage')
        }),
        ('Responsable y Plazos', {
            'fields': ('owner', 'start_date', 'target_date', 'completion_date')
        }),
        ('Estado y Progreso', {
            'fields': ('status', 'progress_percentage')
        }),
        ('Vinculación con Riesgos y Oportunidades', {
            'fields': ('addresses_risks', 'leverages_opportunities'),
            'classes': ('collapse',)
        }),
        ('Recursos', {
            'fields': ('required_resources', 'budget'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ObjectiveAction)
class ObjectiveActionAdmin(admin.ModelAdmin):
    list_display = ['objective', 'action_number', 'description', 'responsible', 'due_date', 'status', 'progress_percentage']
    list_filter = ['status', 'organization_id']
    search_fields = ['description', 'what_will_be_done', 'objective__title']
    readonly_fields = ['is_overdue', 'created_at', 'updated_at']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Objetivo', {
            'fields': ('organization_id', 'objective', 'action_number')
        }),
        ('Descripción', {
            'fields': ('description', 'what_will_be_done', 'how_will_be_done')
        }),
        ('Responsabilidad y Plazos', {
            'fields': ('responsible', 'due_date', 'completion_date', 'is_overdue')
        }),
        ('Recursos', {
            'fields': ('resources_needed', 'estimated_cost')
        }),
        ('Estado y Progreso', {
            'fields': ('status', 'progress_percentage')
        }),
        ('Evaluación', {
            'fields': ('effectiveness', 'effectiveness_notes', 'evidence')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChangeControl)
class ChangeControlAdmin(admin.ModelAdmin):
    list_display = ['change_number', 'title', 'change_type', 'status', 'urgency', 'planned_date', 'requested_by']
    list_filter = ['status', 'change_type', 'urgency', 'reason', 'organization_name']
    search_fields = ['change_number', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'planned_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Identificación', {
            'fields': ('change_number', 'title', 'description', 'change_type')
        }),
        ('Justificación', {
            'fields': ('reason', 'justification', 'urgency')
        }),
        ('Planificación', {
            'fields': ('planned_date', 'actual_implementation_date')
        }),
        ('Impacto', {
            'fields': ('affected_areas', 'impact_assessment')
        }),
        ('Riesgos', {
            'fields': ('potential_risks', 'mitigation_plan'),
            'classes': ('collapse',)
        }),
        ('Responsables', {
            'fields': ('requested_by', 'approved_by', 'implemented_by')
        }),
        ('Estado', {
            'fields': ('status', 'approval_date', 'approval_comments')
        }),
        ('Verificación', {
            'fields': ('verification_date', 'verification_notes', 'is_effective')
        }),
        ('Documentación', {
            'fields': ('related_documents',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_changes', 'reject_changes']
    
    def approve_changes(self, request, queryset):
        for change in queryset.filter(status='submitted'):
            change.approve(request.user)
        self.message_user(request, f"{queryset.count()} cambios aprobados.")
    approve_changes.short_description = "Aprobar cambios seleccionados"
    
    def reject_changes(self, request, queryset):
        for change in queryset.filter(status='submitted'):
            change.reject(request.user, "Rechazado desde admin")
        self.message_user(request, f"{queryset.count()} cambios rechazados.")
    reject_changes.short_description = "Rechazar cambios seleccionados"
