# improvement/models.py
"""
Improvement Module - ISO 9001:2015 Clause 10
Mejora continua, no conformidades y acciones correctivas
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Nonconformity(models.Model):
    """
    No conformidades - ISO 9001:2015 Clause 10.2
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)

    SOURCE_CHOICES = [
        ('internal_audit', 'Auditoria interna'),
        ('customer_complaint', 'Queja de cliente'),
        ('process_monitoring', 'Monitoreo de procesos'),
        ('product_inspection', 'Inspeccion de producto'),
        ('management_review', 'Revision por la direccion'),
        ('supplier_issue', 'Problema de proveedor'),
        ('other', 'Otro'),
    ]

    SEVERITY_CHOICES = [
        ('critical', 'Critica'),
        ('major', 'Mayor'),
        ('minor', 'Menor'),
    ]

    STATUS_CHOICES = [
        ('open', 'Abierta'),
        ('analysis', 'En analisis'),
        ('action_plan', 'Plan de accion definido'),
        ('implementing', 'Implementando acciones'),
        ('verification', 'Verificacion'),
        ('closed', 'Cerrada'),
        ('rejected', 'Rechazada'),
    ]

    # Identificacion
    nc_number = models.CharField(
        max_length=50,
        verbose_name="Numero de NC"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    detection_date = models.DateField()
    detected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='improvement_nonconformities_detected'
    )

    # Clasificacion
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    affected_process = models.CharField(max_length=200, blank=True)
    iso_clause_reference = models.CharField(max_length=100, blank=True)

    # Impacto
    impact_description = models.TextField(blank=True)
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Acciones inmediatas
    immediate_action_taken = models.TextField(blank=True)
    containment_measures = models.TextField(blank=True)

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='improvement_nonconformities_responsible'
    )

    # Evidencia
    evidence_files = models.JSONField(default=list, blank=True)

    # Fechas
    target_closure_date = models.DateField(null=True, blank=True)
    actual_closure_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'No Conformidad (Mejora)'
        verbose_name_plural = 'No Conformidades (Mejora)'
        ordering = ['-detection_date', '-created_at']
        unique_together = [['organization_id', 'nc_number']]
        indexes = [
            models.Index(fields=['organization_id', 'status']),
            models.Index(fields=['organization_id', 'severity']),
        ]

    def __str__(self):
        return f"{self.nc_number} - {self.title}"


class CorrectiveAction(models.Model):
    """
    Acciones correctivas - ISO 9001:2015 Clause 10.2
    """
    organization_id = models.IntegerField()
    nonconformity = models.ForeignKey(
        Nonconformity,
        on_delete=models.CASCADE,
        related_name='corrective_actions'
    )

    ACTION_TYPE_CHOICES = [
        ('corrective', 'Correctiva'),
        ('preventive', 'Preventiva'),
        ('improvement', 'Mejora'),
    ]

    STATUS_CHOICES = [
        ('planned', 'Planificada'),
        ('in_progress', 'En progreso'),
        ('implemented', 'Implementada'),
        ('verified', 'Verificada'),
        ('effective', 'Efectiva'),
        ('not_effective', 'No efectiva'),
        ('cancelled', 'Cancelada'),
    ]

    # Identificacion
    action_number = models.CharField(max_length=50)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)

    # Analisis de causa raiz
    root_cause_analysis = models.TextField(help_text="5 Whys, Ishikawa, etc.")
    root_cause_identified = models.TextField()
    analysis_method = models.CharField(max_length=100, blank=True)

    # Plan de accion
    action_description = models.TextField()
    implementation_steps = models.TextField()
    resources_required = models.TextField(blank=True)

    # Responsabilidad y tiempos
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrective_actions_responsible'
    )
    planned_start_date = models.DateField()
    planned_completion_date = models.DateField()
    actual_start_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)

    # Verificacion
    verification_method = models.TextField(blank=True)
    verification_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrective_actions_verified'
    )
    verification_result = models.TextField(blank=True)

    # Efectividad
    effectiveness_criteria = models.TextField(blank=True)
    effectiveness_review_date = models.DateField(null=True, blank=True)
    effectiveness_result = models.TextField(blank=True)
    is_effective = models.BooleanField(null=True, blank=True)

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    completion_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Comentarios
    comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Accion Correctiva'
        verbose_name_plural = 'Acciones Correctivas'
        ordering = ['-created_at']
        unique_together = [['organization_id', 'action_number']]
        indexes = [
            models.Index(fields=['organization_id', 'status']),
            models.Index(fields=['organization_id', 'action_type']),
        ]

    def __str__(self):
        return f"{self.action_number} - {self.nonconformity.nc_number}"


class ContinualImprovement(models.Model):
    """
    Iniciativas de mejora continua - ISO 9001:2015 Clause 10.3
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)

    IMPROVEMENT_TYPE_CHOICES = [
        ('process', 'Mejora de proceso'),
        ('product', 'Mejora de producto'),
        ('service', 'Mejora de servicio'),
        ('system', 'Mejora del SGC'),
        ('technology', 'Mejora tecnologica'),
        ('methodology', 'Mejora metodologica'),
    ]

    STATUS_CHOICES = [
        ('proposed', 'Propuesta'),
        ('under_evaluation', 'En evaluacion'),
        ('approved', 'Aprobada'),
        ('in_progress', 'En progreso'),
        ('implemented', 'Implementada'),
        ('measuring_results', 'Midiendo resultados'),
        ('successful', 'Exitosa'),
        ('unsuccessful', 'No exitosa'),
        ('cancelled', 'Cancelada'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Critica'),
    ]

    # Identificacion
    initiative_number = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField()
    improvement_type = models.CharField(max_length=50, choices=IMPROVEMENT_TYPE_CHOICES)

    # Justificacion
    current_situation = models.TextField()
    proposed_improvement = models.TextField()
    expected_benefits = models.TextField()
    alignment_with_objectives = models.TextField(blank=True)

    # Caso de negocio
    estimated_investment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    estimated_savings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    expected_roi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    payback_period_months = models.IntegerField(null=True, blank=True)

    # Metricas de exito
    success_criteria = models.TextField()
    kpis_to_measure = models.JSONField(default=list, blank=True)
    baseline_measurements = models.TextField(blank=True)
    target_measurements = models.TextField(blank=True)

    # Planificacion
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    champion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='improvement_initiatives_champion'
    )
    team_members = models.JSONField(default=list, blank=True)

    # Cronograma
    proposed_date = models.DateField()
    approval_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)

    # Implementacion
    implementation_plan = models.TextField(blank=True)
    milestones = models.JSONField(default=list, blank=True)
    risks_and_mitigation = models.TextField(blank=True)

    # Resultados
    actual_results = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Estado
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='proposed')
    completion_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mejora Continua'
        verbose_name_plural = 'Mejoras Continuas'
        ordering = ['-priority', '-created_at']
        unique_together = [['organization_id', 'initiative_number']]
        indexes = [
            models.Index(fields=['organization_id', 'status']),
            models.Index(fields=['organization_id', 'priority']),
        ]

    def __str__(self):
        return f"{self.initiative_number} - {self.title}"
