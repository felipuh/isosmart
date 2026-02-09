# resources/admin.py
"""
Admin configuration for Resources Module
"""

from django.contrib import admin
from .models import (
    Resource,
    Infrastructure,
    WorkEnvironment,
    Competence,
    Training,
    Awareness,
    Communication
)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'resource_type', 'status', 'quantity', 'location', 'responsible']
    list_filter = ['resource_type', 'status', 'organization_name']
    search_fields = ['name', 'code', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('resource_type', 'name', 'code', 'description')
        }),
        ('Detalles', {
            'fields': ('quantity', 'unit', 'location', 'status')
        }),
        ('Responsable', {
            'fields': ('responsible',)
        }),
        ('Costos', {
            'fields': ('acquisition_cost', 'maintenance_cost'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('acquisition_date', 'next_maintenance_date')
        }),
        ('Documentación', {
            'fields': ('documentation',)
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Infrastructure)
class InfrastructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'infrastructure_type', 'location', 'status', 'next_maintenance_date']
    list_filter = ['infrastructure_type', 'status', 'organization_name']
    search_fields = ['name', 'code', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'next_maintenance_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('infrastructure_type', 'name', 'code', 'description', 'location')
        }),
        ('Capacidad', {
            'fields': ('capacity', 'current_usage')
        }),
        ('Mantenimiento', {
            'fields': ('maintenance_schedule', 'last_maintenance_date', 'next_maintenance_date')
        }),
        ('Estado', {
            'fields': ('status', 'responsible')
        }),
        ('Documentación', {
            'fields': ('specifications',)
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkEnvironment)
class WorkEnvironmentAdmin(admin.ModelAdmin):
    list_display = ['area_name', 'location', 'overall_condition', 'last_evaluation_date', 'responsible']
    list_filter = ['overall_condition', 'organization_name']
    search_fields = ['area_name', 'location', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('area_name', 'location', 'description')
        }),
        ('Factores Físicos', {
            'fields': ('temperature_control', 'humidity_control', 'lighting_adequate', 'noise_controlled')
        }),
        ('Factores Sociales', {
            'fields': ('ergonomic_conditions', 'safety_measures')
        }),
        ('Evaluación', {
            'fields': ('overall_condition', 'last_evaluation_date', 'next_evaluation_date')
        }),
        ('Responsable y Mejoras', {
            'fields': ('responsible', 'improvement_actions')
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'competence_name', 'position', 'required_level', 'current_level', 'needs_improvement']
    list_filter = ['required_level', 'current_level', 'acquisition_method', 'needs_improvement', 'organization_name']
    search_fields = ['user__username', 'user__email', 'competence_name', 'position']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Persona', {
            'fields': ('user', 'position')
        }),
        ('Competencia', {
            'fields': ('competence_name', 'description')
        }),
        ('Niveles', {
            'fields': ('required_level', 'current_level')
        }),
        ('Adquisición', {
            'fields': ('acquisition_method', 'acquired_date', 'expiration_date', 'evidence')
        }),
        ('Evaluación', {
            'fields': ('last_evaluation_date', 'evaluator', 'evaluation_notes')
        }),
        ('Gap Analysis', {
            'fields': ('needs_improvement', 'improvement_plan')
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'training_type', 'start_date', 'duration_hours', 'status', 'coordinator']
    list_filter = ['training_type', 'status', 'organization_name']
    search_fields = ['title', 'code', 'description', 'instructor']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    filter_horizontal = ['participants']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('title', 'code', 'description', 'training_type')
        }),
        ('Instructor/Proveedor', {
            'fields': ('instructor', 'provider')
        }),
        ('Fechas y Duración', {
            'fields': ('start_date', 'end_date', 'duration_hours')
        }),
        ('Participantes', {
            'fields': ('participants', 'max_participants')
        }),
        ('Estado', {
            'fields': ('status', 'coordinator')
        }),
        ('Costo', {
            'fields': ('cost',)
        }),
        ('Evaluación', {
            'fields': ('evaluation_method', 'passing_score')
        }),
        ('Materiales', {
            'fields': ('materials',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Awareness)
class AwarenessAdmin(admin.ModelAdmin):
    list_display = ['activity_name', 'awareness_type', 'method', 'date', 'target_audience', 'responsible']
    list_filter = ['awareness_type', 'method', 'organization_name']
    search_fields = ['activity_name', 'description', 'target_audience']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    filter_horizontal = ['participants']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('activity_name', 'description', 'awareness_type')
        }),
        ('Método y Fecha', {
            'fields': ('method', 'date')
        }),
        ('Audiencia', {
            'fields': ('target_audience', 'participants')
        }),
        ('Responsable', {
            'fields': ('responsible',)
        }),
        ('Evidencia', {
            'fields': ('evidence', 'effectiveness_evaluation')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ['title', 'communication_type', 'method', 'frequency', 'status', 'scheduled_date', 'communicator']
    list_filter = ['communication_type', 'method', 'frequency', 'status', 'organization_name']
    search_fields = ['title', 'description', 'content_summary', 'target_audience']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información Básica', {
            'fields': ('title', 'description', 'communication_type')
        }),
        ('Método y Frecuencia', {
            'fields': ('method', 'frequency')
        }),
        ('Contenido', {
            'fields': ('content_summary',)
        }),
        ('Fechas', {
            'fields': ('scheduled_date', 'last_communication_date')
        }),
        ('Audiencia', {
            'fields': ('target_audience', 'communicator')
        }),
        ('Evidencia', {
            'fields': ('evidence', 'status')
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
