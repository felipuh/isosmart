# planning/models.py
"""
Planning Module - ISO 9001:2015 Cláusula 6
Planificación del Sistema de Gestión de Calidad
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class RiskOpportunity(models.Model):
    """
    Riesgos y Oportunidades
    ISO 9001:2015 - Cláusula 6.1
    Integra con el módulo de Risks existente
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    TYPE_CHOICES = [
        ('risk', 'Riesgo'),
        ('opportunity', 'Oportunidad'),
    ]
    item_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Tipo"
    )
    
    # Identificación
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Contexto
    CONTEXT_CHOICES = [
        ('internal', 'Interno'),
        ('external', 'Externo'),
        ('both', 'Interno y Externo'),
    ]
    context = models.CharField(max_length=20, choices=CONTEXT_CHOICES)
    
    # Categoría
    CATEGORY_CHOICES = [
        ('strategic', 'Estratégico'),
        ('operational', 'Operacional'),
        ('financial', 'Financiero'),
        ('climatic', 'Climático'),
        ('cyber', 'Ciber'),
        ('compliance', 'Cumplimiento'),
        ('reputation', 'Reputacional'),
        ('technology', 'Tecnológico'),
        ('market', 'Mercado'),
        ('other', 'Otro'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Evaluación (para riesgos)
    probability = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Muy baja, 5=Muy alta"
    )
    impact = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Insignificante, 5=Catastrófico"
    )
    risk_level = models.IntegerField(
        null=True,
        blank=True,
        help_text="Calculado automáticamente: probability x impact"
    )
    
    # Evaluación (para oportunidades)
    feasibility = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Muy difícil, 5=Muy fácil"
    )
    benefit = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Mínimo, 5=Muy alto"
    )
    opportunity_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Calculado: feasibility x benefit"
    )
    
    # Tratamiento
    TREATMENT_CHOICES = [
        ('avoid', 'Evitar'),
        ('mitigate', 'Mitigar'),
        ('transfer', 'Transferir'),
        ('accept', 'Aceptar'),
        ('exploit', 'Explotar (Oportunidad)'),
        ('enhance', 'Mejorar (Oportunidad)'),
    ]
    treatment = models.CharField(
        max_length=20,
        choices=TREATMENT_CHOICES,
        blank=True
    )
    treatment_description = models.TextField(
        blank=True,
        verbose_name="Descripción del Tratamiento"
    )
    
    # Responsable
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='risks_opportunities_owned',
        verbose_name="Responsable"
    )
    
    # Estado
    STATUS_CHOICES = [
        ('identified', 'Identificado'),
        ('in_treatment', 'En Tratamiento'),
        ('monitored', 'Monitoreado'),
        ('closed', 'Cerrado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='identified'
    )
    
    # Seguimiento
    review_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Revisión"
    )
    last_review_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Última Revisión"
    )
    review_notes = models.TextField(blank=True)
    
    # Integración con procesos
    related_processes = models.JSONField(
        default=list,
        blank=True,
        help_text="IDs de procesos relacionados"
    )
    ai_sources = models.JSONField(
        default=list,
        blank=True,
        help_text="Fuentes de datos y evidencias usadas para justificar el riesgo/oportunidad"
    )
    proposed_actions = models.JSONField(
        default=list,
        blank=True,
        help_text="Acciones propuestas por reglas/IA"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planning_risks_approved',
        verbose_name="Aprobado por"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Riesgo/Oportunidad"
        verbose_name_plural = "Riesgos y Oportunidades"
        ordering = ['-risk_level', '-opportunity_score', 'title']
        indexes = [
            models.Index(fields=['organization_id', 'item_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Calcular automáticamente los scores
        if self.item_type == 'risk':
            if self.probability and self.impact:
                self.risk_level = self.probability * self.impact
            else:
                self.risk_level = None
            self.opportunity_score = None
        elif self.item_type == 'opportunity':
            if self.feasibility and self.benefit:
                self.opportunity_score = self.feasibility * self.benefit
            else:
                self.opportunity_score = None
            self.risk_level = None
        super().save(*args, **kwargs)

    @property
    def normalized_probability(self):
        if self.probability is None:
            return None
        return round(float(self.probability) / 5, 2)

    @property
    def normalized_impact(self):
        if self.impact is None:
            return None
        return round(float(self.impact) / 5, 2)

    @property
    def level_band(self):
        score = self.risk_level or self.opportunity_score or 0
        if score >= 15:
            return 'high'
        if score >= 8:
            return 'medium'
        return 'low'

    def approve(self, user, notes=''):
        self.approved_by = user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save(update_fields=['approved_by', 'approved_at', 'approval_notes'])


class QualityObjective(models.Model):
    """
    Objetivos de Calidad
    ISO 9001:2015 - Cláusula 6.2
    Mejora e integra con el módulo de Objectives existente
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Identificación
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # SMART
    is_specific = models.BooleanField(default=False, verbose_name="Específico")
    is_measurable = models.BooleanField(default=False, verbose_name="Medible")
    is_achievable = models.BooleanField(default=False, verbose_name="Alcanzable")
    is_relevant = models.BooleanField(default=False, verbose_name="Relevante")
    is_time_bound = models.BooleanField(default=False, verbose_name="Con plazo")
    
    # Alineación
    ALIGNMENT_CHOICES = [
        ('policy', 'Política de Calidad'),
        ('strategic', 'Estrategia Organizacional'),
        ('customer', 'Requisitos del Cliente'),
        ('compliance', 'Cumplimiento Legal'),
        ('improvement', 'Mejora Continua'),
    ]
    alignment = models.CharField(
        max_length=50,
        choices=ALIGNMENT_CHOICES,
        verbose_name="Alineado con"
    )
    
    # Medición
    metric = models.CharField(
        max_length=200,
        verbose_name="Métrica",
        help_text="Cómo se mide el objetivo"
    )
    baseline = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Línea Base"
    )
    target = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Meta"
    )
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Actual"
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ej: %, días, unidades"
    )
    
    # Responsable
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='objectives_owned',
        verbose_name="Responsable"
    )
    
    # Plazos
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    target_date = models.DateField(verbose_name="Fecha Meta")
    completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Cumplimiento"
    )
    
    # Estado
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('in_progress', 'En Progreso'),
        ('achieved', 'Logrado'),
        ('partially_achieved', 'Parcialmente Logrado'),
        ('not_achieved', 'No Logrado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Progreso
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="% de avance"
    )
    
    # Vinculación con riesgos/oportunidades
    addresses_risks = models.ManyToManyField(
        RiskOpportunity,
        related_name='objectives',
        blank=True,
        limit_choices_to={'item_type': 'risk'},
        verbose_name="Aborda Riesgos"
    )
    leverages_opportunities = models.ManyToManyField(
        RiskOpportunity,
        related_name='opportunity_objectives',
        blank=True,
        limit_choices_to={'item_type': 'opportunity'},
        verbose_name="Aprovecha Oportunidades"
    )
    
    # Recursos
    required_resources = models.TextField(
        blank=True,
        verbose_name="Recursos Requeridos"
    )
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Presupuesto"
    )
    ai_recommendations = models.JSONField(
        default=dict,
        blank=True,
        help_text="Sugerencias IA para formular, medir o corregir el objetivo"
    )
    forecast_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Predicción simple de cumplimiento o atraso"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planning_objectives_approved',
        verbose_name="Aprobado por"
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Objetivo de Calidad"
        verbose_name_plural = "Objetivos de Calidad"
        ordering = ['-start_date', 'title']
        unique_together = [['organization_id', 'code']]
        indexes = [
            models.Index(fields=['organization_id', 'status']),
            models.Index(fields=['target_date']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    @property
    def is_smart(self):
        """Verificar si cumple criterios SMART"""
        return all([
            self.is_specific,
            self.is_measurable,
            self.is_achievable,
            self.is_relevant,
            self.is_time_bound
        ])
    
    @property
    def achievement_percentage(self):
        """Calcular % de logro vs meta"""
        if self.current_value is not None and self.target:
            return min(100, (float(self.current_value) / float(self.target)) * 100)
        return 0

    def approve(self, user):
        self.status = 'approved'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approval_date'])


class ObjectiveAction(models.Model):
    """
    Acciones para lograr objetivos
    ISO 9001:2015 - Cláusula 6.2.2
    """
    organization_id = models.IntegerField()
    
    objective = models.ForeignKey(
        QualityObjective,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    
    # Identificación
    action_number = models.IntegerField(
        verbose_name="Número de Acción"
    )
    description = models.TextField(verbose_name="Descripción de la Acción")
    
    # Qué y Cómo
    what_will_be_done = models.TextField(
        verbose_name="Qué se hará"
    )
    how_will_be_done = models.TextField(
        blank=True,
        verbose_name="Cómo se hará"
    )
    
    # Quién y Cuándo
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions_responsible',
        verbose_name="Responsable"
    )
    due_date = models.DateField(verbose_name="Fecha Límite")
    completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Finalización"
    )
    
    # Recursos
    resources_needed = models.TextField(
        blank=True,
        verbose_name="Recursos Necesarios"
    )
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Costo Estimado"
    )
    
    # Estado
    STATUS_CHOICES = [
        ('planned', 'Planificada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('delayed', 'Retrasada'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )
    
    # Progreso
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Evaluación
    effectiveness = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=No efectiva, 5=Muy efectiva"
    )
    effectiveness_notes = models.TextField(
        blank=True,
        verbose_name="Notas de Efectividad"
    )
    
    # Evidencias
    evidence = models.FileField(
        upload_to='planning/actions/',
        null=True,
        blank=True,
        verbose_name="Evidencia"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Acción para Objetivo"
        verbose_name_plural = "Acciones para Objetivos"
        ordering = ['objective', 'action_number']
        unique_together = [['objective', 'action_number']]
    
    def __str__(self):
        return f"{self.objective.code} - Acción {self.action_number}"
    
    @property
    def is_overdue(self):
        """Verificar si está retrasada"""
        from datetime import date
        if self.status not in ['completed', 'cancelled']:
            return date.today() > self.due_date
        return False


class ChangeControl(models.Model):
    """
    Control de Cambios al SGC
    ISO 9001:2015 - Cláusula 6.3
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Identificación
    change_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(verbose_name="Descripción del Cambio")
    
    # Tipo de cambio
    CHANGE_TYPE_CHOICES = [
        ('process', 'Proceso'),
        ('procedure', 'Procedimiento'),
        ('resource', 'Recurso'),
        ('technology', 'Tecnología'),
        ('structure', 'Estructura Organizacional'),
        ('scope', 'Alcance del SGC'),
        ('policy', 'Política'),
        ('other', 'Otro'),
    ]
    change_type = models.CharField(
        max_length=50,
        choices=CHANGE_TYPE_CHOICES
    )
    
    # Justificación
    REASON_CHOICES = [
        ('improvement', 'Mejora'),
        ('correction', 'Corrección'),
        ('compliance', 'Cumplimiento'),
        ('risk_mitigation', 'Mitigación de Riesgo'),
        ('opportunity', 'Oportunidad'),
        ('external_requirement', 'Requisito Externo'),
    ]
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        verbose_name="Razón del Cambio"
    )
    justification = models.TextField(verbose_name="Justificación Detallada")
    
    # Planificación
    URGENCY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES)
    
    planned_date = models.DateField(
        verbose_name="Fecha Planificada de Implementación"
    )
    actual_implementation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Real de Implementación"
    )
    
    # Impacto
    affected_areas = models.TextField(
        verbose_name="Áreas Afectadas"
    )
    impact_assessment = models.TextField(
        verbose_name="Evaluación de Impacto",
        help_text="Consecuencias del cambio"
    )
    
    # Riesgos del cambio
    potential_risks = models.TextField(
        blank=True,
        verbose_name="Riesgos Potenciales"
    )
    mitigation_plan = models.TextField(
        blank=True,
        verbose_name="Plan de Mitigación"
    )
    
    # Responsables
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='changes_requested',
        verbose_name="Solicitado por"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='changes_approved',
        verbose_name="Aprobado por"
    )
    implemented_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='changes_implemented',
        verbose_name="Implementado por"
    )
    
    # Estado
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('submitted', 'Enviado'),
        ('under_review', 'En Revisión'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('in_implementation', 'En Implementación'),
        ('implemented', 'Implementado'),
        ('verified', 'Verificado'),
        ('closed', 'Cerrado'),
    ]
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_comments = models.TextField(blank=True)
    
    # Verificación
    verification_date = models.DateField(null=True, blank=True)
    verification_notes = models.TextField(
        blank=True,
        verbose_name="Notas de Verificación"
    )
    is_effective = models.BooleanField(
        default=False,
        verbose_name="Cambio Efectivo"
    )
    
    # Documentación
    related_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="IDs de documentos relacionados"
    )
    impact_estimated = models.JSONField(
        default=dict,
        blank=True,
        help_text="Impacto estimado estructurado antes de implementar el cambio"
    )
    implementation_plan = models.JSONField(
        default=list,
        blank=True,
        help_text="Cronograma o plan generado manualmente o por IA"
    )
    affected_versions = models.JSONField(
        default=list,
        blank=True,
        help_text="Versiones, documentos o procesos afectados por el cambio"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Control de Cambio"
        verbose_name_plural = "Controles de Cambios"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization_id', 'status']),
            models.Index(fields=['planned_date']),
        ]
    
    def __str__(self):
        return f"{self.change_number} - {self.title}"
    
    def approve(self, user):
        """Aprobar el cambio"""
        if not self.impact_assessment and not self.impact_estimated:
            raise ValueError('Todo cambio debe tener analisis de impacto antes de aprobarse.')
        self.status = 'approved'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()
    
    def reject(self, user, comments):
        """Rechazar el cambio"""
        self.status = 'rejected'
        self.approved_by = user
        self.approval_comments = comments
        self.save()


class PlanningVersionRecord(models.Model):
    """Snapshot inmutable de riesgos, objetivos y cambios para trazabilidad de auditoría."""

    ENTITY_CHOICES = [
        ('risk_opportunity', 'Riesgo/Oportunidad'),
        ('quality_objective', 'Objetivo de Calidad'),
        ('change_control', 'Control de Cambio'),
    ]

    organization_id = models.IntegerField(db_index=True)
    entity_type = models.CharField(max_length=30, choices=ENTITY_CHOICES)
    entity_id = models.IntegerField()
    version_number = models.IntegerField()
    snapshot = models.JSONField()
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planning_version_records'
    )
    change_reason = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Version de Planificacion'
        verbose_name_plural = 'Versiones de Planificacion'
        ordering = ['-created_at']
        unique_together = [['entity_type', 'entity_id', 'version_number']]
        indexes = [
            models.Index(fields=['organization_id', 'entity_type']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f"{self.entity_type}:{self.entity_id} v{self.version_number}"


class PlanningApprovalRecord(models.Model):
    """Registro inmutable de aprobaciones críticas de planificación."""

    WORKFLOW_CHOICES = [
        ('risk_approval', 'Aprobación de Riesgo'),
        ('objective_approval', 'Aprobación de Objetivo'),
        ('change_approval', 'Aprobación de Cambio'),
        ('change_rejection', 'Rechazo de Cambio'),
    ]

    organization_id = models.IntegerField(db_index=True)
    workflow_type = models.CharField(max_length=30, choices=WORKFLOW_CHOICES)
    reference_model = models.CharField(max_length=100)
    reference_id = models.IntegerField()
    title = models.CharField(max_length=300)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='planning_approval_records'
    )
    approved_at = models.DateTimeField(auto_now_add=True)
    digital_signature = models.CharField(max_length=64)
    content_snapshot = models.JSONField()
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Registro de Aprobacion de Planificacion'
        verbose_name_plural = 'Registros de Aprobacion de Planificacion'
        ordering = ['-approved_at']
        indexes = [
            models.Index(fields=['organization_id', 'workflow_type']),
            models.Index(fields=['reference_model', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.workflow_type} | {self.title}"

    @classmethod
    def generate_signature(cls, content_snapshot, user_id, timestamp_iso):
        import hashlib
        import json

        payload = json.dumps(
            {'content': content_snapshot, 'user_id': user_id, 'ts': timestamp_iso},
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()


class PlanningAIGovernanceLog(models.Model):
    """Log de prompts, respuesta y decisión humana para IA de planificación."""

    DECISION_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
        ('modified', 'Modificado'),
    ]

    organization_id = models.IntegerField(db_index=True)
    operation = models.CharField(max_length=100)
    model_version = models.CharField(max_length=100, default='unknown')
    prompt_template = models.CharField(max_length=200)
    prompt_hash = models.CharField(max_length=64)
    response_summary = models.TextField()
    ai_recommendation = models.JSONField(default=dict, blank=True)
    data_sources = models.JSONField(default=list, blank=True)
    privacy_check_passed = models.BooleanField(default=True)
    human_decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending')
    decided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planning_ai_decisions'
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    human_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Gobernanza IA de Planificacion'
        verbose_name_plural = 'Logs de Gobernanza IA de Planificacion'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization_id', 'operation']),
            models.Index(fields=['human_decision']),
        ]

    def __str__(self):
        return f"{self.operation} | {self.human_decision}"

    def record_human_decision(self, user, decision, notes=''):
        self.human_decision = decision
        self.decided_by = user
        self.decided_at = timezone.now()
        self.human_notes = notes
        self.save(update_fields=['human_decision', 'decided_by', 'decided_at', 'human_notes'])
