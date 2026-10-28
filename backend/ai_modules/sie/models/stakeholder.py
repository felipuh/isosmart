"""
Modelos de datos para Stakeholder Intelligence Engine (SIE)
ISO 4.2: Comprensión de las necesidades y expectativas de las partes interesadas
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class StakeholderProfile(models.Model):
    """
    Perfil completo de un stakeholder
    Almacena información para análisis de influencia y engagement
    """
    
    STAKEHOLDER_TYPES = [
        ('cliente', 'Cliente'),
        ('proveedor', 'Proveedor'),
        ('empleado', 'Empleado'),
        ('accionista', 'Accionista'),
        ('regulador', 'Entidad Reguladora'),
        ('regulatory_environmental', 'Regulador Ambiental'),
        ('comunidad', 'Comunidad Local'),
        ('community_climate_affected', 'Comunidad Afectada por Clima'),
        ('esg_investor', 'Inversor ESG'),
        ('socio', 'Socio Estratégico'),
        ('competidor', 'Competidor'),
        ('otro', 'Otro'),
    ]
    
    POWER_LEVELS = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
    ]
    
    INTEREST_LEVELS = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
    ]
    
    COMMUNICATION_FREQUENCY = [
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    ]
    
    # Tenant
    organization_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="ID de Organización"
    )

    # Información básica
    name = models.CharField(max_length=200, verbose_name="Nombre")
    stakeholder_type = models.CharField(
        max_length=40,
        choices=STAKEHOLDER_TYPES,
        verbose_name="Tipo de Stakeholder"
    )
    organization = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Organización"
    )
    contact_person = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Persona de Contacto"
    )
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    
    # Análisis de poder e interés (Matriz de Stakeholders)
    power = models.CharField(
        max_length=10, 
        choices=POWER_LEVELS,
        default='medio',
        verbose_name="Nivel de Poder"
    )
    interest = models.CharField(
        max_length=10, 
        choices=INTEREST_LEVELS,
        default='medio',
        verbose_name="Nivel de Interés"
    )
    
    # Métricas calculadas por IA
    influence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Score de Influencia (calculado por IA)",
        help_text="Score compuesto de 0.0 a 1.0"
    )
    satisfaction_score = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name="Score de Satisfacción",
        help_text="De 0 a 10"
    )
    
    # Expectativas y requisitos
    expectations = models.JSONField(
        default=list,
        verbose_name="Expectativas",
        help_text="Lista de expectativas del stakeholder"
    )
    requirements = models.JSONField(
        default=list,
        verbose_name="Requisitos",
        help_text="Requisitos específicos del stakeholder"
    )
    
    # Estrategia de comunicación
    communication_frequency = models.CharField(
        max_length=20,
        choices=COMMUNICATION_FREQUENCY,
        default='mensual',
        verbose_name="Frecuencia de Comunicación"
    )
    preferred_channel = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Canal de Comunicación Preferido"
    )
    
    # Información adicional
    notes = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Notas"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_critical = models.BooleanField(
        default=False,
        verbose_name="Stakeholder Crítico",
        help_text="Marcado automáticamente por IA si influencia > 0.7"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_contact = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Último Contacto"
    )
    
    class Meta:
        verbose_name = "Stakeholder"
        verbose_name_plural = "Stakeholders"
        ordering = ['-influence_score', 'name']
        indexes = [
            models.Index(fields=['stakeholder_type', 'is_active']),
            models.Index(fields=['-influence_score']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_stakeholder_type_display()})"
    
    @property
    def engagement_category(self):
        """Determina la categoría de engagement según matriz poder/interés"""
        if self.power == 'alto' and self.interest == 'alto':
            return 'Gestionar de Cerca'
        elif self.power == 'alto':
            return 'Mantener Satisfecho'
        elif self.interest == 'alto':
            return 'Mantener Informado'
        else:
            return 'Monitorear'
    
    @property
    def risk_level(self):
        """Evalúa el nivel de riesgo del stakeholder"""
        if self.power == 'alto' and self.satisfaction_score < 3.0:
            return 'CRÍTICO'
        elif self.influence_score > 0.7 and self.satisfaction_score < 3.5:
            return 'ALTO'
        elif self.influence_score > 0.5 or self.power == 'alto':
            return 'MEDIO'
        else:
            return 'BAJO'


class StakeholderChangeLog(models.Model):
    """
    Registro de cambios en stakeholders
    Utilizado por el motor de IA para detectar tendencias
    """
    
    stakeholder = models.ForeignKey(
        StakeholderProfile,
        on_delete=models.CASCADE,
        related_name='change_logs'
    )
    
    change_type = models.CharField(
        max_length=100,
        verbose_name="Tipo de Cambio",
        help_text="Ej: expectation_change, contact_change, etc."
    )
    
    previous_state = models.JSONField(
        verbose_name="Estado Anterior",
        help_text="Snapshot del estado previo"
    )
    
    new_state = models.JSONField(
        verbose_name="Nuevo Estado",
        help_text="Snapshot del nuevo estado"
    )
    
    similarity_score = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Score de Similitud",
        help_text="Qué tan similares son los estados (0=completamente diferente, 1=idéntico)"
    )
    
    detected_at = models.DateTimeField(default=timezone.now)
    alert_sent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Log de Cambios"
        verbose_name_plural = "Logs de Cambios"
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['stakeholder', '-detected_at']),
        ]
    
    def __str__(self):
        return f"{self.stakeholder.name} - {self.change_type} ({self.detected_at.strftime('%Y-%m-%d')})"


class StakeholderRelationship(models.Model):
    """
    Relaciones entre stakeholders
    Usado para construir el grafo de red
    """
    
    RELATIONSHIP_TYPES = [
        ('colaboracion', 'Colaboración'),
        ('cliente-proveedor', 'Cliente-Proveedor'),
        ('competencia', 'Competencia'),
        ('regulatoria', 'Regulatoria'),
        ('contractual', 'Contractual'),
        ('general', 'General'),
    ]
    
    from_stakeholder = models.ForeignKey(
        StakeholderProfile,
        on_delete=models.CASCADE,
        related_name='relationships_from'
    )
    
    to_stakeholder = models.ForeignKey(
        StakeholderProfile,
        on_delete=models.CASCADE,
        related_name='relationships_to'
    )
    
    relationship_type = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_TYPES,
        default='general'
    )
    
    strength = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Fuerza de la Relación",
        help_text="0.0 = débil, 1.0 = muy fuerte"
    )
    
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Relación entre Stakeholders"
        verbose_name_plural = "Relaciones entre Stakeholders"
        unique_together = [['from_stakeholder', 'to_stakeholder']]
    
    def __str__(self):
        return f"{self.from_stakeholder.name} → {self.to_stakeholder.name} ({self.relationship_type})"


class StakeholderEngagementPlan(models.Model):
    """
    Plan de engagement para stakeholders críticos
    Generado automáticamente por el módulo SIE
    """
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    stakeholder = models.ForeignKey(
        StakeholderProfile,
        on_delete=models.CASCADE,
        related_name='engagement_plans'
    )
    
    plan_title = models.CharField(max_length=200)
    
    objectives = models.JSONField(
        default=list,
        verbose_name="Objetivos del Plan",
        help_text="Lista de objetivos específicos"
    )
    
    actions = models.JSONField(
        default=list,
        verbose_name="Acciones Planificadas",
        help_text="Lista de acciones con responsables y fechas"
    )
    
    success_metrics = models.JSONField(
        default=list,
        verbose_name="Métricas de Éxito",
        help_text="KPIs para medir efectividad"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Resultado del plan
    effectiveness_score = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name="Score de Efectividad",
        help_text="Evaluación post-ejecución de 0 a 10"
    )
    
    class Meta:
        verbose_name = "Plan de Engagement"
        verbose_name_plural = "Planes de Engagement"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.plan_title} - {self.stakeholder.name}"
