from django.db import models
from django.conf import settings  # Cambiado de: from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from decimal import Decimal
from typing import Optional
import json

# =====================================================
# Modelos para Análisis de Contexto (ISO 4.1)
# =====================================================

class ContextAnalysis(models.Model):
    """Resultados de análisis de contexto organizacional"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('error', 'Error'),
    ]
    
    id = models.AutoField(primary_key=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='context_analyses')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    internal_insights = models.JSONField(default=dict, blank=True)
    external_insights = models.JSONField(default=dict, blank=True)
    climate_context = models.JSONField(default=dict, blank=True)
    environmental_scope = models.JSONField(default=list, blank=True)
    total_documents_processed = models.IntegerField(default=0)
    execution_time_seconds = models.FloatField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'context_analysis'
        ordering = ['-timestamp']
        verbose_name = 'Análisis de Contexto'
        verbose_name_plural = 'Análisis de Contexto'
    
    def __str__(self):
        return f"Context Analysis {self.id} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Document(models.Model):
    """Documentos procesados por el sistema"""
    
    TYPE_CHOICES = [
        ('acta', 'Acta'),
        ('reporte', 'Reporte'),
        ('politica', 'Política'),
        ('procedimiento', 'Procedimiento'),
        ('otro', 'Otro'),
    ]
    
    id = models.AutoField(primary_key=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    content = models.TextField()
    source = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='documents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_type', 'created_at']),
            models.Index(fields=['is_processed']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.document_type})"


# =====================================================
# Modelos para Partes Interesadas (ISO 4.2)
# =====================================================

class StakeholderProfile(models.Model):
    """Perfiles de partes interesadas"""
    
    TYPE_CHOICES = [
        ('cliente', 'Cliente'),
        ('proveedor', 'Proveedor'),
        ('empleado', 'Empleado'),
        ('regulador', 'Regulador'),
        ('accionista', 'Accionista'),
        ('comunidad', 'Comunidad'),
        ('otro', 'Otro'),
    ]
    
    POWER_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
    ]
    
    id = models.AutoField(primary_key=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='stakeholders')
    name = models.CharField(max_length=255)
    stakeholder_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    influence_score = models.FloatField(default=0.0)
    power = models.CharField(max_length=10, choices=POWER_CHOICES, default='medio')
    interest = models.CharField(max_length=10, choices=POWER_CHOICES, default='medio')
    expectations = models.JSONField(default=list)
    communication_frequency = models.CharField(max_length=50, default='mensual')
    satisfaction_score = models.FloatField(default=0.0, null=True, blank=True)
    contact_info = models.JSONField(default=dict, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'stakeholder_profiles'
        ordering = ['-influence_score', 'name']
        indexes = [
            models.Index(fields=['stakeholder_type', 'is_active']),
            models.Index(fields=['influence_score']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.stakeholder_type})"


class StakeholderChangeLog(models.Model):
    """Log de cambios en expectativas de stakeholders"""
    
    stakeholder = models.ForeignKey(StakeholderProfile, on_delete=models.CASCADE, related_name='change_logs')
    change_type = models.CharField(max_length=100)
    previous_state = models.JSONField()
    new_state = models.JSONField()
    similarity_score = models.FloatField()
    detected_at = models.DateTimeField(auto_now_add=True)
    alert_sent = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'stakeholder_change_logs'
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"Change for {self.stakeholder.name} - {self.detected_at.strftime('%Y-%m-%d')}"


# =====================================================
# Modelos para Alcance del SGC (ISO 4.3)
# =====================================================

class ScopeElement(models.Model):
    """Elementos del alcance del SGC"""
    
    TYPE_CHOICES = [
        ('core', 'Proceso Core'),
        ('soporte', 'Proceso de Soporte'),
        ('estrategico', 'Proceso Estratégico'),
    ]
    
    id = models.AutoField(primary_key=True)
    process_id = models.CharField(max_length=50, unique=True)
    process_name = models.CharField(max_length=255)
    included = models.BooleanField(default=True)
    process_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    iso_clauses_covered = models.JSONField(default=list)
    exclusion_justification = models.TextField(blank=True, null=True)
    products_services = models.JSONField(default=list)
    locations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'scope_elements'
        ordering = ['process_type', 'process_name']
    
    def __str__(self):
        return f"{self.process_id} - {self.process_name}"


class ScopeAudit(models.Model):
    """Auditorías automáticas del alcance"""
    
    id = models.AutoField(primary_key=True)
    audit_date = models.DateTimeField(auto_now_add=True)
    coverage_percentage = models.FloatField()
    gaps = models.JSONField(default=list)
    status = models.CharField(max_length=20, default='compliant')
    recommendations = models.JSONField(default=list)
    
    class Meta:
        db_table = 'scope_audits'
        ordering = ['-audit_date']
    
    def __str__(self):
        return f"Scope Audit {self.audit_date.strftime('%Y-%m-%d')} - {self.coverage_percentage}%"


# =====================================================
# Modelos para Procesos (ISO 4.4)
# =====================================================

class ProcessMap(models.Model):
    """Mapas de procesos del SGC"""
    
    HEALTH_CHOICES = [
        ('healthy', 'Saludable'),
        ('warning', 'Atención'),
        ('critical', 'Crítico'),
    ]
    
    id = models.AutoField(primary_key=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='process_maps')
    process_id = models.CharField(max_length=50, unique=True)
    process_name = models.CharField(max_length=200)
    process_data = models.JSONField(default=dict)
    diagram_url = models.CharField(max_length=500, blank=True)
    predicted_risks = models.JSONField(default=list)
    generated_kpis = models.JSONField(default=list)
    owner = models.CharField(max_length=255)
    health_status = models.CharField(max_length=20, choices=HEALTH_CHOICES, default='healthy')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'process_maps'
        ordering = ['process_name']
    
    def __str__(self):
        return f"{self.process_id} - {self.process_name}"


# =====================================================
# Modelos para Matriz de Riesgos (ISO 6.1)
# =====================================================

class RiskMatrix(models.Model):
    """Matriz consolidada de riesgos"""
    
    SOURCE_CHOICES = [
        ('SCA', 'Context Analyzer'),
        ('SIE', 'Stakeholder Intelligence'),
        ('SPM', 'Process Mapper'),
        ('MANUAL', 'Entrada Manual'),
    ]
    
    PROBABILITY_CHOICES = [
        ('muy_baja', 'Muy Baja'),
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('muy_alta', 'Muy Alta'),
    ]
    
    IMPACT_CHOICES = [
        ('muy_bajo', 'Muy Bajo'),
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('muy_alto', 'Muy Alto'),
    ]
    
    LEVEL_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('critico', 'Crítico'),
    ]
    
    STATUS_CHOICES = [
        ('identified', 'Identificado'),
        ('under_analysis', 'En Análisis'),
        ('mitigated', 'Mitigado'),
        ('accepted', 'Aceptado'),
        ('closed', 'Cerrado'),
    ]
    
    id = models.AutoField(primary_key=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='risk_matrices')
    source_module = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    source_id = models.IntegerField(null=True, blank=True)
    risk_description = models.TextField()
    risk_category = models.CharField(max_length=50)
    probability = models.CharField(max_length=20, choices=PROBABILITY_CHOICES)
    impact = models.CharField(max_length=20, choices=IMPACT_CHOICES)
    risk_level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    mitigation_actions = models.TextField()
    responsible = models.CharField(max_length=255)
    iso_clause = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='identified')
    detection_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    process_id = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        db_table = 'risk_matrix'
        ordering = ['-detection_date']
        indexes = [
            models.Index(fields=['risk_level', 'status']),
            models.Index(fields=['source_module', 'detection_date']),
        ]
    
    def __str__(self):
        return f"Risk {self.id} - {self.risk_level} ({self.source_module})"


# =====================================================
# Modelos para Objetivos de Calidad (ISO 6.2)
# =====================================================

class QualityObjective(models.Model):
    """Objetivos de calidad del SGC"""
    
    SOURCE_CHOICES = [
        ('SPM', 'Process Mapper'),
        ('SCA', 'Context Analyzer'),
        ('MANUAL', 'Entrada Manual'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('in_progress', 'En Progreso'),
        ('achieved', 'Logrado'),
        ('delayed', 'Retrasado'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.AutoField(primary_key=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='quality_objectives')
    source_module = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='MANUAL')
    objective_description = models.TextField()
    indicator_name = models.CharField(max_length=255)
    measurement_unit = models.CharField(max_length=50)
    baseline_value = models.FloatField()
    target_value = models.FloatField()
    current_value = models.FloatField(null=True, blank=True)
    measurement_frequency = models.CharField(max_length=50)
    responsible = models.CharField(max_length=255)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    iso_clause = models.CharField(max_length=10, default='6.2')
    process_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quality_objectives'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.indicator_name} - {self.status}"
    
    @property
    def progress_percentage(self):
        """Calcula el progreso hacia el objetivo"""
        if self.current_value is None:
            return 0
        
        if self.target_value == self.baseline_value:
            return 100
        
        progress = ((self.current_value - self.baseline_value) / 
                   (self.target_value - self.baseline_value)) * 100
        
        return max(0, min(100, progress))


# =====================================================
# Modelos para Gestión de Cambios (ISO 6.3)
# =====================================================

class ChangeLog(models.Model):
    """Registro de cambios planificados"""
    
    TYPE_CHOICES = [
        ('scope_modification', 'Modificación de Alcance'),
        ('process_change', 'Cambio de Proceso'),
        ('stakeholder_requirements', 'Requisitos de Stakeholder'),
        ('regulatory', 'Cambio Regulatorio'),
        ('improvement', 'Mejora Continua'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('pending_approval', 'Pendiente de Aprobación'),
        ('approved', 'Aprobado'),
        ('in_implementation', 'En Implementación'),
        ('completed', 'Completado'),
        ('rejected', 'Rechazado'),
    ]
    
    id = models.AutoField(primary_key=True)
    change_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    change_description = models.TextField()
    justification = models.TextField()
    impact_analysis = models.TextField()
    responsible = models.CharField(max_length=255)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_approval')
    iso_clause = models.CharField(max_length=10, default='6.3')
    detection_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    implementation_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'change_logs'
        ordering = ['-detection_date']
    
    def __str__(self):
        return f"Change {self.id} - {self.change_type} ({self.status})"


# =====================================================
# Modelos para Auditoría de IA (ISO 42001)
# =====================================================

class AIModelVersion(models.Model):
    """Registro de versiones de modelos de IA"""
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('deprecated', 'Obsoleto'),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    framework = models.CharField(max_length=100)
    training_date = models.DateTimeField()
    metrics = models.JSONField(default=dict)
    hyperparameters = models.JSONField(default=dict)
    artifacts_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_model_versions'
        ordering = ['-training_date']
        unique_together = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.status})"


class AIAuditLog(models.Model):
    """Logs de auditoría para cumplimiento ISO 42001"""
    
    id = models.AutoField(primary_key=True)
    model_name = models.CharField(max_length=255)
    model_version = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    input_hash = models.CharField(max_length=64)
    output_hash = models.CharField(max_length=64)
    inference_time_ms = models.FloatField()
    confidence_score = models.FloatField(null=True, blank=True)
    user_id = models.CharField(max_length=100)
    compliance_flags = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'ai_audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'timestamp']),
            models.Index(fields=['user_id', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Audit {self.id} - {self.model_name} ({self.timestamp})"


# =====================================================
# Modelos para Sistema Multicliente y Configuración
# =====================================================

class Organization(models.Model):
    """Organización/Cliente del sistema multicliente"""
    
    id = models.AutoField(primary_key=True)
    external_id = models.CharField(max_length=36, unique=True, null=True, blank=True, help_text='UUID desde Admin Apps')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True)
    
    # Datos de contacto
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    
    # Datos fiscales/legales
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='NIT/RUC/RFC')
    legal_name = models.CharField(max_length=255, blank=True)
    
    # Estado
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configuración de suscripción (para Admin Apps futuro)
    plan_type = models.CharField(max_length=50, default='basic', choices=[
        ('basic', 'Básico'),
        ('professional', 'Profesional'),
        ('enterprise', 'Empresarial'),
    ])
    max_users = models.IntegerField(default=5)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# =====================================================
# NOTA IMPORTANTE:
# El modelo UserProfile se ha MOVIDO a authentication/models.py
# para evitar conflictos con el nuevo sistema de autenticación.
# El modelo en authentication soporta múltiples organizaciones por usuario.
# =====================================================


class OrganizationSettings(models.Model):
    """Configuración general de la organización"""
    
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='settings')
    
    # Configuración de módulos de IA
    ai_sca_enabled = models.BooleanField(default=True, verbose_name='Context Analyzer')
    ai_sie_enabled = models.BooleanField(default=True, verbose_name='Stakeholder Intelligence')
    ai_asb_enabled = models.BooleanField(default=True, verbose_name='Scope Builder')
    ai_spm_enabled = models.BooleanField(default=True, verbose_name='Process Mapper')
    
    # Parámetros de IA
    ai_auto_analysis = models.BooleanField(default=False, verbose_name='Análisis automático')
    ai_analysis_frequency = models.CharField(max_length=20, default='weekly', choices=[
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('manual', 'Manual'),
    ])
    
    # Configuración de notificaciones
    notify_risk_critical = models.BooleanField(default=True)
    notify_risk_high = models.BooleanField(default=True)
    notify_objective_deadline = models.BooleanField(default=True)
    notify_document_upload = models.BooleanField(default=False)
    notify_stakeholder_change = models.BooleanField(default=True)
    notification_email = models.EmailField(blank=True)
    
    # Configuración ISO
    iso_standard = models.CharField(max_length=50, default='ISO 9001:2015')
    enabled_standards = models.JSONField(default=list, blank=True)
    preferred_language = models.CharField(max_length=20, default='es-LATAM', choices=[
        ('es-LATAM', 'Español (LATAM)'),
        ('en', 'English'),
        ('pt', 'Português'),
    ])
    preferred_response_tone = models.CharField(max_length=20, default='manager', choices=[
        ('manager', 'Lenguaje gerente'),
        ('technical', 'Lenguaje técnico'),
    ])
    onboarding_profile = models.JSONField(default=dict, blank=True)
    fiscal_year_start = models.IntegerField(default=1, choices=[(i, f'Mes {i}') for i in range(1, 13)])

    # Onboarding
    onboarding_completed = models.BooleanField(default=False)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    onboarding_completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_onboardings'
    )
    
    # Backup
    auto_backup_enabled = models.BooleanField(default=False)
    backup_frequency = models.CharField(max_length=20, default='weekly', choices=[
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ])
    last_backup_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organization_settings'
    
    def __str__(self):
        return f"Settings - {self.organization.name}"


class ISOClauseConfig(models.Model):
    """Configuración de cláusulas ISO por organización"""
    
    STANDARD_CHOICES = [
        ('ISO9001_2015', 'ISO 9001:2015'),
        ('ISO42001_2023', 'ISO/IEC 42001:2023'),
        ('ISO27001_2022', 'ISO/IEC 27001:2022'),
        ('ISO14001_2015', 'ISO 14001:2015'),
        ('ISO45001_2018', 'ISO 45001:2018'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='iso_clauses')
    standard_code = models.CharField(max_length=20, choices=STANDARD_CHOICES, default='ISO9001_2015')
    clause_number = models.CharField(max_length=10)
    clause_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_applicable = models.BooleanField(default=True)
    exclusion_justification = models.TextField(blank=True)
    responsible = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'iso_clause_configs'
        unique_together = ['organization', 'standard_code', 'clause_number']
        ordering = ['standard_code', 'clause_number']
    
    def __str__(self):
        return f"{self.standard_code} {self.clause_number} - {self.clause_name}"


class AuditLog(models.Model):
    """Log de auditoría para cambios en configuración"""
    
    ACTION_CHOICES = [
        ('create', 'Creación'),
        ('update', 'Actualización'),
        ('delete', 'Eliminación'),
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('export', 'Exportación'),
        ('backup', 'Respaldo'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.module} - {self.created_at}"


class NotificationDelivery(models.Model):
    """Registro de entregas de notificaciones para trazabilidad operativa."""

    CHANNEL_CHOICES = [
        ('email', 'Email'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('failed', 'Fallida'),
        ('skipped', 'Omitida'),
    ]

    EVENT_TYPE_CHOICES = [
        ('billing_payment_registered', 'Pago registrado'),
        ('billing_payment_confirmed', 'Pago confirmado'),
        ('billing_payment_rejected', 'Pago rechazado'),
        ('billing_status_changed', 'Cambio de estado de facturacion'),
        ('billing_due_reminder', 'Recordatorio de cobro'),
        ('risk_critical', 'Riesgo critico'),
        ('risk_high', 'Riesgo alto'),
        ('objective_deadline', 'Vencimiento de objetivo o accion'),
        ('stakeholder_change', 'Cambio de stakeholder'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notification_deliveries')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='email')
    event_key = models.CharField(max_length=255, unique=True)
    recipients = models.JSONField(default=list, blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_deliveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'event_type']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.organization.name} - {self.status}"


class ExternalContextSignal(models.Model):
    """Señales externas relevantes para contexto ISO 4.1 (clima/ESG/digital/regulatorio)."""

    SOURCE_TYPE_CHOICES = [
        ('ipcc', 'IPCC'),
        ('un', 'ONU'),
        ('iso', 'ISO'),
        ('regulator', 'Regulador'),
        ('industry', 'Industria'),
    ]

    IMPACT_CHOICES = [
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Critico'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='external_context_signals')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    source_name = models.CharField(max_length=120)
    source_url = models.URLField(max_length=500, blank=True)
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    signal_hash = models.CharField(max_length=64)
    published_at = models.DateTimeField(null=True, blank=True)
    impact_level = models.CharField(max_length=20, choices=IMPACT_CHOICES, default='medium')
    tags = models.JSONField(default=list, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'external_context_signals'
        ordering = ['-fetched_at']
        unique_together = ['organization', 'source_name', 'signal_hash']
        indexes = [
            models.Index(fields=['organization', 'source_type']),
            models.Index(fields=['impact_level', '-fetched_at']),
        ]

    def __str__(self):
        return f"{self.source_name}: {self.title}"


class EnvironmentalRiskAlert(models.Model):
    """Alertas trazables de riesgos climáticos/ESG conectadas a la matriz 6.1."""

    ALERT_TYPE_CHOICES = [
        ('regulatory_change', 'Cambio regulatorio'),
        ('climate_event', 'Evento climatico'),
        ('supply_chain_risk', 'Riesgo de cadena de suministro'),
        ('process_exposure', 'Exposicion de proceso'),
        ('stakeholder_pressure', 'Presion de stakeholder'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Critico'),
    ]

    STATUS_CHOICES = [
        ('open', 'Abierta'),
        ('in_progress', 'En progreso'),
        ('acknowledged', 'Reconocida'),
        ('closed', 'Cerrada'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='environmental_alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    source_module = models.CharField(max_length=20, default='SCA')
    source_id = models.IntegerField(null=True, blank=True)
    external_signal = models.ForeignKey(
        ExternalContextSignal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )
    linked_risk = models.ForeignKey(
        'RiskMatrix',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='environmental_alerts'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    recommendation = models.TextField(blank=True)
    ai_audit_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'environmental_risk_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'severity']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.alert_type} - {self.severity} - {self.organization.name}"


class OnboardingInsightSnapshot(models.Model):
    """Snapshot versionado de resultados del onboarding disruptivo"""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='onboarding_snapshots')
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    input_profile = models.JSONField(default=dict, blank=True)
    organizational_profile_output = models.JSONField(default=dict, blank=True)
    impact_savings_output = models.JSONField(default=dict, blank=True)
    purpose_alignment_output = models.JSONField(default=dict, blank=True)
    summary_output = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'onboarding_insight_snapshots'
        ordering = ['-created_at']
        unique_together = ['organization', 'version']

    def __str__(self):
        return f"OnboardingSnapshot org={self.organization_id} v{self.version}"


class BillingSubscription(models.Model):
    """Suscripción interna de facturación por organización"""

    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('past_due', 'Pendiente de pago'),
        ('suspended', 'Suspendida'),
        ('cancelled', 'Cancelada'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Transferencia bancaria'),
        ('credit_card', 'Tarjeta de crédito'),
        ('debit_card', 'Tarjeta de débito'),
        ('other', 'Otro'),
    ]

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='billing_subscription')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')

    payer_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    payer_name = models.CharField(max_length=255, blank=True)
    payer_email = models.EmailField(blank=True)
    payer_phone = models.CharField(max_length=50, blank=True)

    monthly_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='USD')
    grace_days = models.PositiveIntegerField(default=8)
    auto_suspend_enabled = models.BooleanField(default=True)

    current_period_start = models.DateField(null=True, blank=True)
    current_period_end = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    last_payment_date = models.DateField(null=True, blank=True)
    past_due_since = models.DateField(null=True, blank=True)

    suspended_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_subscriptions'

    def __str__(self):
        return f"Subscription org={self.organization_id} status={self.status}"

    def evaluate_status(self, today: Optional[date] = None):
        today = today or timezone.now().date()

        if self.status == 'cancelled':
            return self.status

        if not self.next_due_date:
            return self.status

        overdue_days = (today - self.next_due_date).days

        if overdue_days <= 0:
            if self.status in ['past_due', 'suspended']:
                self.status = 'active'
                self.past_due_since = None
                self.suspended_at = None
            return self.status

        if overdue_days <= self.grace_days:
            self.status = 'past_due'
            if self.past_due_since is None:
                self.past_due_since = self.next_due_date
            return self.status

        if self.auto_suspend_enabled:
            self.status = 'suspended'
            if self.suspended_at is None:
                self.suspended_at = timezone.now()
        else:
            self.status = 'past_due'
            if self.past_due_since is None:
                self.past_due_since = self.next_due_date

        return self.status


class BillingPayment(models.Model):
    """Registro de pagos de suscripción"""

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('rejected', 'Rechazado'),
    ]

    subscription = models.ForeignKey(BillingSubscription, on_delete=models.CASCADE, related_name='payments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=BillingSubscription.PAYMENT_METHOD_CHOICES, default='bank_transfer')

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='USD')
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    reference = models.CharField(max_length=255, blank=True)
    evidence_file = models.FileField(upload_to='billing/evidence/%Y/%m/', null=True, blank=True)
    evidence_uploaded_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_billing_payments')
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_billing_payments')
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} org={self.subscription.organization_id} status={self.status}"


# =====================================================
# Feature Flags
# =====================================================

class FeatureFlagQuerySet(models.QuerySet):
    def for_organization(self, organization):
        return self.filter(
            models.Q(scope='global', organization__isnull=True) |
            models.Q(scope='organization', organization=organization)
        )


class FeatureFlagManager(models.Manager):
    def get_queryset(self):
        return FeatureFlagQuerySet(self.model, using=self._db)

    def is_enabled(self, name: str, organization=None) -> bool:
        """Resolve a flag: org-specific overrides global; default False if absent."""
        flags = {
            f.scope: f.enabled
            for f in self.get_queryset()
                         .filter(name=name)
                         .filter(
                             models.Q(scope='global', organization__isnull=True) |
                             models.Q(scope='organization', organization=organization)
                         )
        }
        if organization and 'organization' in flags:
            return flags['organization']
        return flags.get('global', False)

    def resolve_all(self, organization=None) -> dict:
        """Return a dict {flag_name: bool} for all known flags in org context."""
        result: dict = {}
        qs = self.get_queryset().filter(
            models.Q(scope='global', organization__isnull=True) |
            models.Q(scope='organization', organization=organization)
        ).order_by('name', 'scope')

        for flag in qs:
            if flag.scope == 'global' and flag.name not in result:
                result[flag.name] = flag.enabled
            elif flag.scope == 'organization':
                result[flag.name] = flag.enabled
        return result


class FeatureFlag(models.Model):
    SCOPE_GLOBAL = 'global'
    SCOPE_ORGANIZATION = 'organization'
    SCOPE_CHOICES = [
        ('global', 'Global'),
        ('organization', 'Por Organización'),
    ]

    name = models.CharField(max_length=100, db_index=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_GLOBAL)
    organization = models.ForeignKey(
        Organization,
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='feature_flags',
    )
    enabled = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FeatureFlagManager()

    class Meta:
        db_table = 'feature_flags'
        unique_together = [('name', 'organization')]
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'

    def __str__(self):
        org = self.organization.name if self.organization else 'global'
        return f"{self.name} [{org}] → {'ON' if self.enabled else 'OFF'}"
