"""
Modelos para el Módulo SPM - Smart Process Mapper
ISO 4.4 - Sistema de gestión de calidad y sus procesos
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ProcessMap(models.Model):
    """
    Mapa general de procesos de la organización
    """

    organization_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="ID de Organización"
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name="Título del Mapa",
        default="Mapa de Procesos Organizacional"
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
    
    # Estadísticas del mapa
    total_processes = models.IntegerField(
        verbose_name="Total de Procesos",
        default=0
    )
    
    strategic_count = models.IntegerField(
        verbose_name="Procesos Estratégicos",
        default=0
    )
    
    operational_count = models.IntegerField(
        verbose_name="Procesos Operativos",
        default=0
    )
    
    support_count = models.IntegerField(
        verbose_name="Procesos de Apoyo",
        default=0
    )
    
    # Análisis de interacciones
    interaction_analysis = models.JSONField(
        verbose_name="Análisis de Interacciones",
        help_text="Matriz de interacciones entre procesos",
        default=dict
    )
    
    # Procesos críticos identificados
    critical_processes = models.JSONField(
        verbose_name="Procesos Críticos",
        help_text="Lista de procesos identificados como críticos",
        default=list
    )
    
    # Recomendaciones
    recommendations = models.JSONField(
        verbose_name="Recomendaciones",
        default=list
    )
    
    # Estado
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('under_review', 'En Revisión'),
        ('approved', 'Aprobado'),
        ('active', 'Activo'),
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
    
    # Relación con alcance
    scope_definition = models.ForeignKey(
        'asb.ScopeDefinition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_maps',
        verbose_name="Definición de Alcance"
    )
    
    class Meta:
        verbose_name = "Mapa de Procesos"
        verbose_name_plural = "Mapas de Procesos"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} v{self.version}"
    
    @property
    def is_active(self):
        return self.status == 'active'


class Process(models.Model):
    """
    Proceso individual dentro del SGC
    """
    
    process_map = models.ForeignKey(
        ProcessMap,
        on_delete=models.CASCADE,
        related_name='processes',
        verbose_name="Mapa de Procesos"
    )
    
    # Información básica
    code = models.CharField(
        max_length=20,
        verbose_name="Código del Proceso",
        help_text="Ej: EST-01, OPE-02, APO-03"
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre del Proceso"
    )
    
    description = models.TextField(
        verbose_name="Descripción",
        blank=True
    )
    
    # Clasificación
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
    
    # Objetivo del proceso
    objective = models.TextField(
        verbose_name="Objetivo del Proceso",
        blank=True
    )
    
    # Responsable
    owner = models.CharField(
        max_length=100,
        verbose_name="Dueño del Proceso",
        help_text="Persona o cargo responsable"
    )
    
    # Entradas del proceso
    inputs = models.JSONField(
        verbose_name="Entradas",
        help_text="Recursos, información, documentos que requiere el proceso",
        default=list
    )
    
    # Salidas del proceso
    outputs = models.JSONField(
        verbose_name="Salidas",
        help_text="Productos, servicios, documentos que genera el proceso",
        default=list
    )
    
    # Recursos necesarios
    resources = models.JSONField(
        verbose_name="Recursos",
        help_text="Personal, equipos, infraestructura necesaria",
        default=list
    )
    
    # KPIs del proceso
    kpis = models.JSONField(
        verbose_name="Indicadores de Desempeño (KPIs)",
        default=list
    )
    
    # Riesgos del proceso
    risks = models.JSONField(
        verbose_name="Riesgos Identificados",
        default=list
    )
    
    # Controles
    controls = models.JSONField(
        verbose_name="Controles",
        help_text="Controles para gestionar los riesgos",
        default=list
    )
    
    # Criticidad
    criticality_score = models.FloatField(
        verbose_name="Nivel de Criticidad",
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=0.5,
        help_text="0 = No crítico, 1 = Altamente crítico"
    )
    
    is_critical = models.BooleanField(
        default=False,
        verbose_name="Proceso Crítico"
    )

    # Variables de sostenibilidad y resiliencia (ISO 9001:2026)
    CARBON_INTENSITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('unknown', 'Desconocida'),
    ]

    CLIMATE_EXPOSURE_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]

    SUPPLY_CHAIN_RISK_CHOICES = [
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('unknown', 'Desconocido'),
    ]

    carbon_intensity_category = models.CharField(
        max_length=20,
        choices=CARBON_INTENSITY_CHOICES,
        default='unknown',
        verbose_name="Intensidad de Carbono"
    )

    climate_exposure_level = models.CharField(
        max_length=20,
        choices=CLIMATE_EXPOSURE_CHOICES,
        default='medium',
        verbose_name="Exposición Climática"
    )

    supply_chain_risk = models.CharField(
        max_length=20,
        choices=SUPPLY_CHAIN_RISK_CHOICES,
        default='unknown',
        verbose_name="Riesgo de Cadena de Suministro"
    )

    resilience_score = models.FloatField(
        verbose_name="Score de Resiliencia",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=50.0,
        help_text="Capacidad de respuesta del proceso ante disrupciones (0-100)"
    )
    
    # Documentación
    documented_in = models.CharField(
        max_length=200,
        verbose_name="Documentado en",
        blank=True,
        help_text="Referencia al documento del procedimiento"
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proceso"
        verbose_name_plural = "Procesos"
        ordering = ['process_type', 'code']
        unique_together = ['process_map', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ProcessInteraction(models.Model):
    """
    Interacciones entre procesos
    """
    
    process_map = models.ForeignKey(
        ProcessMap,
        on_delete=models.CASCADE,
        related_name='interactions',
        verbose_name="Mapa de Procesos"
    )
    
    source_process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name='outgoing_interactions',
        verbose_name="Proceso Origen"
    )
    
    target_process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name='incoming_interactions',
        verbose_name="Proceso Destino"
    )
    
    INTERACTION_TYPE_CHOICES = [
        ('input_output', 'Entrada-Salida'),
        ('information', 'Flujo de Información'),
        ('dependency', 'Dependencia'),
        ('resource_sharing', 'Recursos Compartidos'),
    ]
    
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_TYPE_CHOICES,
        verbose_name="Tipo de Interacción"
    )
    
    description = models.TextField(
        verbose_name="Descripción de la Interacción",
        blank=True
    )
    
    # Qué se intercambia
    exchanged_items = models.JSONField(
        verbose_name="Items Intercambiados",
        help_text="Documentos, información, productos intercambiados",
        default=list
    )
    
    # Frecuencia
    FREQUENCY_CHOICES = [
        ('continuous', 'Continuo'),
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('on_demand', 'Bajo Demanda'),
    ]
    
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='on_demand',
        verbose_name="Frecuencia"
    )
    
    # Criticidad de la interacción
    is_critical = models.BooleanField(
        default=False,
        verbose_name="Interacción Crítica"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Interacción entre Procesos"
        verbose_name_plural = "Interacciones entre Procesos"
        ordering = ['source_process', 'target_process']
    
    def __str__(self):
        return f"{self.source_process.code} → {self.target_process.code}"


class ProcessActivity(models.Model):
    """
    Actividades dentro de un proceso
    """
    
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Proceso"
    )
    
    sequence_number = models.IntegerField(
        verbose_name="Número de Secuencia",
        validators=[MinValueValidator(1)]
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Actividad"
    )
    
    description = models.TextField(
        verbose_name="Descripción",
        blank=True
    )
    
    responsible = models.CharField(
        max_length=100,
        verbose_name="Responsable",
        blank=True
    )
    
    estimated_duration = models.CharField(
        max_length=50,
        verbose_name="Duración Estimada",
        blank=True,
        help_text="Ej: 2 horas, 1 día"
    )
    
    tools_required = models.JSONField(
        verbose_name="Herramientas Requeridas",
        default=list
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Actividad del Proceso"
        verbose_name_plural = "Actividades del Proceso"
        ordering = ['process', 'sequence_number']
    
    def __str__(self):
        return f"{self.process.code} - Act {self.sequence_number}: {self.name}"