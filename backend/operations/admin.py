# operations/admin.py
"""
Admin configuration for Operations Module
"""

from django.contrib import admin
from .models import (
    OperationalControl,
    CustomerRequirement,
    DesignProject,
    ExternalProvider,
    ProductionControl,
    ProductRelease,
    Nonconformity,
    Disposition
)


@admin.register(OperationalControl)
class OperationalControlAdmin(admin.ModelAdmin):
    list_display = ['control_code', 'control_name', 'control_type', 'frequency', 'responsible', 'is_active']
    list_filter = ['control_type', 'frequency', 'is_active', 'organization_name']
    search_fields = ['control_code', 'control_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Identificación', {
            'fields': ('control_code', 'control_name', 'description', 'control_type')
        }),
        ('Proceso y Criterios', {
            'fields': ('related_process', 'acceptance_criteria')
        }),
        ('Recursos y Responsable', {
            'fields': ('required_resources', 'responsible')
        }),
        ('Frecuencia', {
            'fields': ('frequency',)
        }),
        ('Documentación', {
            'fields': ('procedure_reference',)
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerRequirement)
class CustomerRequirementAdmin(admin.ModelAdmin):
    list_display = ['requirement_code', 'customer_name', 'requirement_title', 'requirement_type', 'status', 'is_confirmed']
    list_filter = ['requirement_type', 'status', 'is_confirmed', 'can_meet_requirement', 'organization_name']
    search_fields = ['requirement_code', 'customer_name', 'requirement_title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'communication_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Cliente', {
            'fields': ('customer_name', 'customer_code', 'contact_person')
        }),
        ('Requisito', {
            'fields': ('requirement_code', 'requirement_title', 'description', 'requirement_type')
        }),
        ('Comunicación', {
            'fields': ('communication_date', 'communication_method')
        }),
        ('Revisión', {
            'fields': ('is_reviewed', 'review_date', 'reviewed_by', 'review_notes')
        }),
        ('Confirmación', {
            'fields': ('is_confirmed', 'confirmation_date', 'confirmation_evidence')
        }),
        ('Capacidad', {
            'fields': ('can_meet_requirement', 'capacity_notes')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DesignProject)
class DesignProjectAdmin(admin.ModelAdmin):
    list_display = ['project_code', 'project_name', 'project_type', 'current_stage', 'status', 'project_leader', 'target_completion_date']
    list_filter = ['project_type', 'current_stage', 'status', 'is_verified', 'is_validated', 'organization_name']
    search_fields = ['project_code', 'project_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['team_members']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Identificación', {
            'fields': ('project_code', 'project_name', 'description', 'project_type')
        }),
        ('Etapa Actual', {
            'fields': ('current_stage', 'status')
        }),
        ('Diseño - Entradas y Salidas', {
            'fields': ('design_inputs', 'design_outputs', 'design_controls')
        }),
        ('Verificación', {
            'fields': ('verification_method', 'is_verified', 'verification_date', 'verification_notes')
        }),
        ('Validación', {
            'fields': ('validation_method', 'is_validated', 'validation_date', 'validation_notes')
        }),
        ('Equipo', {
            'fields': ('project_leader', 'team_members')
        }),
        ('Fechas', {
            'fields': ('start_date', 'target_completion_date', 'actual_completion_date')
        }),
        ('Documentación', {
            'fields': ('documentation',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExternalProvider)
class ExternalProviderAdmin(admin.ModelAdmin):
    list_display = ['provider_code', 'provider_name', 'provision_type', 'classification', 'performance_rating', 'last_evaluation_date', 'is_active']
    list_filter = ['provision_type', 'classification', 'performance_rating', 'is_active', 'organization_name']
    search_fields = ['provider_code', 'provider_name', 'contact_person', 'products_services']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'last_evaluation_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Información del Proveedor', {
            'fields': ('provider_code', 'provider_name', 'contact_person', 'email', 'phone', 'address')
        }),
        ('Provisión', {
            'fields': ('provision_type', 'products_services')
        }),
        ('Evaluación', {
            'fields': ('evaluation_criteria', 'last_evaluation_date', 'evaluation_score', 'evaluation_notes')
        }),
        ('Clasificación y Desempeño', {
            'fields': ('classification', 'performance_rating')
        }),
        ('Controles', {
            'fields': ('controls_applied',)
        }),
        ('Responsable', {
            'fields': ('responsible',)
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductionControl)
class ProductionControlAdmin(admin.ModelAdmin):
    list_display = ['control_code', 'product_service_name', 'control_type', 'requires_traceability', 'responsible', 'is_active']
    list_filter = ['control_type', 'requires_traceability', 'handles_customer_property', 'is_active', 'organization_name']
    search_fields = ['control_code', 'product_service_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Identificación', {
            'fields': ('control_code', 'product_service_name', 'description', 'control_type')
        }),
        ('Control', {
            'fields': ('control_method',)
        }),
        ('Trazabilidad', {
            'fields': ('requires_traceability', 'traceability_method')
        }),
        ('Propiedad del Cliente', {
            'fields': ('handles_customer_property', 'customer_property_controls')
        }),
        ('Preservación', {
            'fields': ('preservation_requirements',)
        }),
        ('Post-Entrega', {
            'fields': ('post_delivery_activities',)
        }),
        ('Control de Cambios', {
            'fields': ('change_control_process',)
        }),
        ('Responsable', {
            'fields': ('responsible',)
        }),
        ('Metadatos', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductRelease)
class ProductReleaseAdmin(admin.ModelAdmin):
    list_display = ['release_code', 'product_service_name', 'release_date', 'status', 'quantity_released', 'authorized_by']
    list_filter = ['status', 'verification_performed', 'acceptance_criteria_met', 'organization_name']
    search_fields = ['release_code', 'product_service_name', 'batch_lot_number', 'customer_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'release_date'
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Identificación', {
            'fields': ('release_code', 'product_service_name', 'batch_lot_number')
        }),
        ('Fecha', {
            'fields': ('release_date',)
        }),
        ('Verificación', {
            'fields': ('verification_performed', 'verification_results')
        }),
        ('Criterios de Aceptación', {
            'fields': ('acceptance_criteria_met', 'criteria_details')
        }),
        ('Autorización', {
            'fields': ('authorized_by', 'authorization_date')
        }),
        ('Trazabilidad', {
            'fields': ('traceability_info',)
        }),
        ('Cliente', {
            'fields': ('customer_name', 'delivery_date')
        }),
        ('Cantidad', {
            'fields': ('quantity_released', 'unit')
        }),
        ('Estado', {
            'fields': ('status', 'notes')
        }),
        ('Evidencia', {
            'fields': ('evidence',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class DispositionInline(admin.StackedInline):
    model = Disposition
    extra = 0
    fields = ['disposition_action', 'action_description', 'authorized_by', 'authorization_date', 'is_verified', 'is_effective']


@admin.register(Nonconformity)
class NonconformityAdmin(admin.ModelAdmin):
    list_display = ['nc_number', 'title', 'detection_date', 'nc_type', 'severity', 'status', 'affects_customer', 'responsible']
    list_filter = ['nc_type', 'severity', 'status', 'detection_stage', 'affects_customer', 'organization_name']
    search_fields = ['nc_number', 'title', 'description', 'affected_product_service']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'detection_date'
    inlines = [DispositionInline]
    
    fieldsets = (
        ('Organización', {
            'fields': ('organization_id', 'organization_name')
        }),
        ('Identificación', {
            'fields': ('nc_number', 'title', 'description')
        }),
        ('Detección', {
            'fields': ('detection_date', 'detected_by', 'detection_stage')
        }),
        ('Clasificación', {
            'fields': ('nc_type', 'severity')
        }),
        ('Producto/Servicio Afectado', {
            'fields': ('affected_product_service', 'batch_lot_number', 'quantity_affected')
        }),
        ('Cliente', {
            'fields': ('affects_customer', 'customer_name', 'customer_notified', 'notification_date')
        }),
        ('Estado', {
            'fields': ('status', 'responsible')
        }),
        ('Evidencia', {
            'fields': ('evidence',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Disposition)
class DispositionAdmin(admin.ModelAdmin):
    list_display = ['nonconformity', 'disposition_action', 'authorized_by', 'is_verified', 'is_effective']
    list_filter = ['disposition_action', 'requires_authorization', 'is_verified', 'is_effective']
    search_fields = ['nonconformity__nc_number', 'action_description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('No Conformidad', {
            'fields': ('nonconformity',)
        }),
        ('Decisión', {
            'fields': ('disposition_action', 'action_description')
        }),
        ('Autorización', {
            'fields': ('requires_authorization', 'authorized_by', 'authorization_date', 'authorization_notes')
        }),
        ('Implementación', {
            'fields': ('implemented_by', 'implementation_date', 'implementation_notes')
        }),
        ('Verificación', {
            'fields': ('is_verified', 'verification_date', 'verified_by', 'verification_notes')
        }),
        ('Efectividad', {
            'fields': ('is_effective', 'effectiveness_notes')
        }),
        ('Costos', {
            'fields': ('estimated_cost', 'actual_cost'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
