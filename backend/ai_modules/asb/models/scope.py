"""
Modelos para el Módulo ASB - AI Scope Builder
ISO 4.3 - Determinación del alcance del SGC
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ScopeDefinition(models.Model):
    """
    Definición del Alcance del SGC
    """

    organization_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="ID de Organización"
    )
    
    # Información básica
    title = models.CharField(
        max_length=255,
        verbose_name="Título del Alcance",
        default="Alcance del Sistema de Gestión de Calidad"
    )
    
    version = models.CharField(
        max_length=20,
        verbose_name="Versión",
        default="1.0"
    )
    
    effective_date = models.DateField(
        verbose_name="Fecha de Vigencia",
        default=timezone.now
    )
    
    # Límites organizacionales
    organizational_boundaries = models.JSONField(
        verbose_name="Límites Organizacionales",
        help_text="Estructura, ubicaciones, departamentos incluidos",
        default=dict
    )
    
    # Productos y servicios
    products_services = models.JSONField(
        verbose_name="Productos y Servicios",
        help_text="Lista de productos/servicios incluidos en el alcance",
        default=list
    )
    
    # Requisitos aplicables
    applicable_requirements = models.JSONField(
        verbose_name="Requisitos Aplicables",
        help_text="Requisitos ISO 9001 aplicables y justificaciones",
        default=dict
    )

    # Criterios ambientales y de resiliencia (ISO 9001:2026 + enmienda 2024)
    environmental_criteria = models.JSONField(
        verbose_name="Criterios Ambientales",
        help_text="Criterios de materialidad ambiental y climática para el alcance",
        default=dict
    )

    climate_readiness_score = models.FloatField(
        verbose_name="Score de Madurez Climática",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0,
        help_text="Puntaje de preparación climática del alcance (0-100)"
    )

    digital_readiness_score = models.FloatField(
        verbose_name="Score de Madurez Digital",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0,
        help_text="Puntaje de preparación digital del alcance (0-100)"
    )
    
    # Exclusiones
    exclusions = models.JSONField(
        verbose_name="Exclusiones",
        help_text="Requisitos excluidos con justificación",
        default=list
    )
    
    # Texto descriptivo del alcance
    scope_statement = models.TextField(
        verbose_name="Declaración de Alcance",
        help_text="Texto generado automáticamente del alcance",
        blank=True
    )
    
    # Análisis de cobertura
    coverage_analysis = models.JSONField(
        verbose_name="Análisis de Cobertura",
        help_text="Análisis de qué tan completo es el alcance",
        default=dict
    )
    
    # Estado
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('under_review', 'En Revisión'),
        ('approved', 'Aprobado'),
        ('active', 'Activo'),
        ('superseded', 'Reemplazado'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Estado"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, default="Sistema IA")
    
    # Relación con análisis de contexto
    context_analysis = models.ForeignKey(
        'core.ContextAnalysis',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scope_definitions',
        verbose_name="Análisis de Contexto Relacionado"
    )
    
    class Meta:
        verbose_name = "Definición de Alcance"
        verbose_name_plural = "Definiciones de Alcance"
        ordering = ['-effective_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} v{self.version} - {self.status}"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def total_products(self):
        return len(self.products_services)
    
    @property
    def total_exclusions(self):
        return len(self.exclusions)
    
    @property
    def coverage_score(self):
        """Porcentaje de cobertura del alcance"""
        return self.coverage_analysis.get('coverage_percentage', 0)


class ProcessScope(models.Model):
    """
    Procesos incluidos en el alcance del SGC
    """
    
    scope_definition = models.ForeignKey(
        ScopeDefinition,
        on_delete=models.CASCADE,
        related_name='processes',
        verbose_name="Definición de Alcance"
    )
    
    process_name = models.CharField(
        max_length=200,
        verbose_name="Nombre del Proceso"
    )
    
    process_code = models.CharField(
        max_length=50,
        verbose_name="Código del Proceso",
        blank=True
    )
    
    PROCESS_TYPE_CHOICES = [
        ('strategic', 'Estratégico'),
        ('operational', 'Operativo'),
        ('support', 'Apoyo'),
    ]
    
    process_type = models.CharField(
        max_length=20,
        choices=PROCESS_TYPE_CHOICES,
        verbose_name="Tipo de Proceso"
    )
    
    description = models.TextField(
        verbose_name="Descripción",
        blank=True
    )
    
    owner = models.CharField(
        max_length=100,
        verbose_name="Responsable",
        blank=True
    )
    
    # Entradas y salidas
    inputs = models.JSONField(
        verbose_name="Entradas del Proceso",
        default=list
    )
    
    outputs = models.JSONField(
        verbose_name="Salidas del Proceso",
        default=list
    )
    
    # KPIs
    kpis = models.JSONField(
        verbose_name="Indicadores (KPIs)",
        default=list
    )
    
    # Inclusión
    is_included = models.BooleanField(
        default=True,
        verbose_name="Incluido en Alcance"
    )
    
    exclusion_reason = models.TextField(
        verbose_name="Razón de Exclusión",
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proceso en Alcance"
        verbose_name_plural = "Procesos en Alcance"
        ordering = ['process_type', 'process_name']
    
    def __str__(self):
        return f"{self.process_name} ({self.get_process_type_display()})"


class LocationScope(models.Model):
    """
    Ubicaciones incluidas en el alcance
    """
    
    scope_definition = models.ForeignKey(
        ScopeDefinition,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name="Definición de Alcance"
    )
    
    location_name = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Ubicación"
    )
    
    address = models.TextField(
        verbose_name="Dirección",
        blank=True
    )
    
    LOCATION_TYPE_CHOICES = [
        ('headquarters', 'Sede Principal'),
        ('branch', 'Sucursal'),
        ('warehouse', 'Almacén/Bodega'),
        ('plant', 'Planta de Producción'),
        ('office', 'Oficina'),
        ('remote', 'Trabajo Remoto'),
    ]
    
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPE_CHOICES,
        verbose_name="Tipo de Ubicación"
    )
    
    country = models.CharField(
        max_length=100,
        verbose_name="País"
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name="Ciudad"
    )
    
    # Actividades en esta ubicación
    activities = models.JSONField(
        verbose_name="Actividades Realizadas",
        default=list
    )
    
    employee_count = models.IntegerField(
        verbose_name="Número de Empleados",
        validators=[MinValueValidator(0)],
        default=0
    )
    
    is_included = models.BooleanField(
        default=True,
        verbose_name="Incluida en Alcance"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ubicación en Alcance"
        verbose_name_plural = "Ubicaciones en Alcance"
        ordering = ['country', 'city', 'location_name']
    
    def __str__(self):
        return f"{self.location_name} - {self.city}, {self.country}"