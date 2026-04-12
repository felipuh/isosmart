# leadership/models.py
"""
Leadership Module - ISO 9001:2015 Cláusula 5
Liderazgo y Compromiso de la Dirección
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class QualityPolicy(models.Model):
    """
    Política de Calidad de la Organización
    ISO 9001:2015 - Cláusula 5.2
    """
    organization_id = models.IntegerField(
        help_text="ID de la organización (integración con Admin Apps)"
    )
    organization_name = models.CharField(
        max_length=200,
        help_text="Nombre de la organización (cache)"
    )
    
    version = models.CharField(
        max_length=20,
        help_text="Versión de la política (ej: 1.0, 2.1)"
    )
    title = models.CharField(
        max_length=200,
        default="Política de Calidad"
    )
    
    content = models.TextField(
        verbose_name="Contenido de la Política",
        help_text="Texto completo de la política de calidad"
    )
    
    customer_focus = models.TextField(
        verbose_name="Enfoque al Cliente",
        help_text="Cómo la política demuestra enfoque al cliente",
        blank=True
    )
    framework_for_objectives = models.TextField(
        verbose_name="Marco para Objetivos",
        help_text="Cómo proporciona marco para objetivos de calidad",
        blank=True
    )
    commitment_requirements = models.TextField(
        verbose_name="Compromiso con Requisitos",
        help_text="Compromiso de cumplir requisitos aplicables",
        blank=True
    )
    commitment_improvement = models.TextField(
        verbose_name="Compromiso con Mejora Continua",
        help_text="Compromiso de mejora continua del SGC",
        blank=True
    )
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('review', 'En Revisión'),
        ('approved', 'Aprobada'),
        ('active', 'Activa'),
        ('obsolete', 'Obsoleta'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_policies'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_comments = models.TextField(blank=True)
    
    effective_date = models.DateField(
        verbose_name="Fecha de Vigencia",
        help_text="Fecha desde la cual la política está vigente",
        null=True,
        blank=True
    )
    review_date = models.DateField(
        verbose_name="Fecha de Próxima Revisión",
        help_text="Fecha programada para próxima revisión",
        null=True,
        blank=True
    )
    
    is_published = models.BooleanField(
        default=False,
        help_text="Si está publicada y disponible para toda la organización"
    )
    communication_channels = models.JSONField(
        default=list,
        help_text="Canales donde se ha comunicado",
        blank=True
    )
    published_date = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_policies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    pdf_file = models.FileField(
        upload_to='leadership/policies/pdfs/',
        null=True,
        blank=True,
        help_text="Versión PDF firmada de la política"
    )
    
    class Meta:
        verbose_name = "Política de Calidad"
        verbose_name_plural = "Políticas de Calidad"
        ordering = ['-version', '-created_at']
        unique_together = [['organization_id', 'version']]
        indexes = [
            models.Index(fields=['organization_id', 'status']),
            models.Index(fields=['organization_id', 'is_published']),
        ]
    
    def __str__(self):
        return f"{self.organization_name} - Política v{self.version}"
    
    def approve(self, user):
        self.status = 'approved'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()
    
    def publish(self):
        if self.status != 'approved':
            raise ValueError("Solo se pueden publicar políticas aprobadas")
        self.is_published = True
        self.published_date = timezone.now()
        self.status = 'active'
        self.save()
    
    def make_obsolete(self):
        self.status = 'obsolete'
        self.is_published = False
        self.save()


class OrganizationalRole(models.Model):
    """
    Roles dentro de la organización para el SGC
    ISO 9001:2015 - Cláusula 5.3
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre del Rol"
    )
    code = models.CharField(
        max_length=50,
        verbose_name="Código del Rol"
    )
    description = models.TextField(
        verbose_name="Descripción",
        blank=True
    )
    
    level = models.IntegerField(
        verbose_name="Nivel Jerárquico",
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )
    
    responsibilities = models.JSONField(
        default=list,
        blank=True
    )
    authorities = models.JSONField(
        default=list,
        blank=True
    )
    required_competencies = models.JSONField(
        default=list,
        blank=True
    )
    
    is_qms_role = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rol Organizacional"
        verbose_name_plural = "Roles Organizacionales"
        ordering = ['level', 'name']
        unique_together = [['organization_id', 'code']]
    
    def __str__(self):
        return f"{self.name} ({self.organization_name})"


class RoleAssignment(models.Model):
    """Asignación de roles a usuarios"""
    organization_id = models.IntegerField()
    
    role = models.ForeignKey(
        OrganizationalRole,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_assignments'
    )
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    ASSIGNMENT_TYPE_CHOICES = [
        ('permanent', 'Permanente'),
        ('temporary', 'Temporal'),
        ('acting', 'Interino'),
    ]
    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPE_CHOICES,
        default='permanent'
    )
    
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_roles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Asignación de Rol"
        verbose_name_plural = "Asignaciones de Roles"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.name}"


class RACIMatrix(models.Model):
    """Matriz RACI para procesos"""
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_raci_matrices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Matriz RACI"
        verbose_name_plural = "Matrices RACI"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"RACI: {self.name}"


class RACIEntry(models.Model):
    """Entrada individual en matriz RACI"""
    matrix = models.ForeignKey(
        RACIMatrix,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    
    activity = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    responsible_roles = models.ManyToManyField(
        OrganizationalRole,
        related_name='raci_responsible',
        blank=True
    )
    accountable_roles = models.ManyToManyField(
        OrganizationalRole,
        related_name='raci_accountable',
        blank=True
    )
    consulted_roles = models.ManyToManyField(
        OrganizationalRole,
        related_name='raci_consulted',
        blank=True
    )
    informed_roles = models.ManyToManyField(
        OrganizationalRole,
        related_name='raci_informed',
        blank=True
    )
    
    class Meta:
        verbose_name = "Entrada RACI"
        verbose_name_plural = "Entradas RACI"
        ordering = ['matrix', 'order']
    
    def __str__(self):
        return f"{self.matrix.name} - {self.activity}"


class LeadershipCommitment(models.Model):
    """Evidencias de compromiso de la dirección"""
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    COMMITMENT_TYPE_CHOICES = [
        ('responsibility', 'Responsabilidad por SGC'),
        ('policy', 'Política y Objetivos'),
        ('integration', 'Integración en Procesos'),
        ('resources', 'Disponibilidad de Recursos'),
        ('importance', 'Comunicación de Importancia'),
        ('results', 'Logro de Resultados'),
        ('engagement', 'Participación de Personal'),
        ('improvement', 'Promoción de Mejora'),
        ('management', 'Apoyo a Gestión'),
    ]
    commitment_type = models.CharField(max_length=50, choices=COMMITMENT_TYPE_CHOICES)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    EVIDENCE_TYPE_CHOICES = [
        ('meeting', 'Acta de Reunión'),
        ('communication', 'Comunicación'),
        ('decision', 'Decisión Documentada'),
        ('resource_allocation', 'Asignación de Recursos'),
        ('review', 'Revisión por la Dirección'),
        ('policy_update', 'Actualización de Política'),
        ('other', 'Otro'),
    ]
    evidence_type = models.CharField(max_length=50, choices=EVIDENCE_TYPE_CHOICES)
    
    evidence_document = models.FileField(
        upload_to='leadership/commitments/',
        null=True,
        blank=True
    )
    evidence_url = models.URLField(blank=True)
    
    commitment_date = models.DateField()
    committed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='commitments_made'
    )
    
    STATUS_CHOICES = [
        ('planned', 'Planificado'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('verified', 'Verificado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compromiso de Liderazgo"
        verbose_name_plural = "Compromisos de Liderazgo"
        ordering = ['-commitment_date']
    
    def __str__(self):
        return f"{self.title} - {self.commitment_date}"


class CustomerFocusEvidence(models.Model):
    """Evidencias de enfoque al cliente"""
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    FOCUS_TYPE_CHOICES = [
        ('requirements', 'Determinación de Requisitos'),
        ('risks', 'Determinación de Riesgos'),
        ('satisfaction', 'Enfoque en Satisfacción'),
        ('compliance', 'Cumplimiento Legal/Reglamentario'),
    ]
    focus_type = models.CharField(max_length=50, choices=FOCUS_TYPE_CHOICES)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    action_taken = models.TextField()
    results = models.TextField(blank=True)
    action_date = models.DateField()
    
    evidence_file = models.FileField(
        upload_to='leadership/customer_focus/',
        null=True,
        blank=True
    )
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Evidencia de Enfoque al Cliente"
        verbose_name_plural = "Evidencias de Enfoque al Cliente"
        ordering = ['-action_date']
    
    def __str__(self):
        return f"{self.title} - {self.action_date}"


# ─────────────────────────────────────────────────────────────
# LEADERSHIP EVIDENCE GRAPH  (requerimiento crítico)
# Columna vertebral auditable: Decisión → Política → Objetivo
# → Proceso → KPI → Riesgo → Acción → Resultado
# ─────────────────────────────────────────────────────────────

class EvidenceNode(models.Model):
    """Nodo en el grafo de evidencias de liderazgo."""

    NODE_TYPE_CHOICES = [
        ('directive_decision', 'Decisión Directiva'),
        ('quality_policy', 'Política de Calidad'),
        ('objective', 'Objetivo de Calidad'),
        ('process', 'Proceso'),
        ('kpi', 'KPI / Indicador'),
        ('risk', 'Riesgo'),
        ('action', 'Acción'),
        ('result', 'Resultado'),
    ]

    organization_id = models.IntegerField(
        db_index=True,
        help_text="ID de la organización"
    )
    node_type = models.CharField(max_length=30, choices=NODE_TYPE_CHOICES)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    # Referencia opcional al objeto origen en el sistema
    reference_id = models.IntegerField(
        null=True, blank=True,
        help_text="PK del objeto referenciado en el sistema (ej. QualityPolicy.id)"
    )
    reference_model = models.CharField(
        max_length=100, blank=True,
        help_text="Modelo Django referenciado (ej. 'leadership.QualityPolicy')"
    )

    # Atributos auditables obligatorios
    data_source = models.CharField(max_length=200, blank=True)
    expected_impact = models.TextField(blank=True)
    responsible = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='responsible_evidence_nodes'
    )
    approver = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_evidence_nodes'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nodo de Evidencia"
        verbose_name_plural = "Nodos de Evidencia"
        ordering = ['node_type', '-created_at']
        indexes = [
            models.Index(fields=['organization_id', 'node_type']),
            models.Index(fields=['reference_model', 'reference_id']),
        ]

    def __str__(self):
        return f"[{self.get_node_type_display()}] {self.title}"

    def approve(self, user):
        self.approver = user
        self.approved_at = timezone.now()
        self.save(update_fields=['approver', 'approved_at'])


class EvidenceEdge(models.Model):
    """Arista dirigida en el grafo de evidencias."""

    EDGE_TYPE_CHOICES = [
        ('derives_from', 'Deriva de'),
        ('supports', 'Soporta'),
        ('measures', 'Mide'),
        ('mitigates', 'Mitiga'),
        ('generates', 'Genera'),
        ('implements', 'Implementa'),
    ]

    source = models.ForeignKey(
        EvidenceNode, on_delete=models.CASCADE, related_name='outgoing_edges'
    )
    target = models.ForeignKey(
        EvidenceNode, on_delete=models.CASCADE, related_name='incoming_edges'
    )
    edge_type = models.CharField(max_length=30, choices=EDGE_TYPE_CHOICES)
    label = models.CharField(max_length=200, blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_evidence_edges'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Arista de Evidencia"
        verbose_name_plural = "Aristas de Evidencia"
        unique_together = [['source', 'target', 'edge_type']]

    def __str__(self):
        return f"{self.source.title} --[{self.edge_type}]--> {self.target.title}"


# ─────────────────────────────────────────────────────────────
# REVISIÓN POR LA DIRECCIÓN  (ISO 9001:2015 – 5.1)
# ─────────────────────────────────────────────────────────────

class ManagementReview(models.Model):
    """Sesión de Revisión por la Dirección."""

    REVIEW_TYPE_CHOICES = [
        ('scheduled', 'Programada'),
        ('extraordinary', 'Extraordinaria'),
        ('follow_up', 'Seguimiento'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planificada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]

    organization_id = models.IntegerField(db_index=True)
    organization_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    review_type = models.CharField(
        max_length=30, choices=REVIEW_TYPE_CHOICES, default='scheduled'
    )
    scheduled_date = models.DateTimeField()
    actual_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='planned'
    )

    facilitator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='facilitated_reviews'
    )
    attendee_ids = models.JSONField(
        default=list, blank=True,
        help_text="Lista de IDs de usuarios asistentes"
    )

    agenda_items = models.JSONField(
        default=list, blank=True,
        help_text="Puntos de la agenda: [{title, owner, notes}]"
    )

    # Brief generado por IA — requiere aprobación humana antes de distribuir
    ai_brief = models.TextField(
        blank=True,
        help_text="Brief pre-reunión generado por IA (borrador, requiere aprobación)"
    )
    ai_brief_generated_at = models.DateTimeField(null=True, blank=True)
    ai_brief_approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='approved_briefs'
    )
    ai_brief_approved_at = models.DateTimeField(null=True, blank=True)

    # Acta — requiere aprobación con firma
    minutes = models.TextField(blank=True)
    minutes_approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='approved_review_minutes'
    )
    minutes_approved_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name='created_reviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Revisión por la Dirección"
        verbose_name_plural = "Revisiones por la Dirección"
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['organization_id', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.scheduled_date.date()})"

    def approve_brief(self, user):
        self.ai_brief_approved_by = user
        self.ai_brief_approved_at = timezone.now()
        self.save(update_fields=['ai_brief_approved_by', 'ai_brief_approved_at'])

    def approve_minutes(self, user):
        if not self.minutes:
            raise ValueError("No hay acta registrada para aprobar")
        self.minutes_approved_by = user
        self.minutes_approved_at = timezone.now()
        self.status = 'completed'
        self.save(update_fields=['minutes_approved_by', 'minutes_approved_at', 'status'])


class ReviewDecision(models.Model):
    """Decisión tomada o registrada en una Revisión por la Dirección."""

    DECISION_TYPE_CHOICES = [
        ('policy_change', 'Cambio de Política'),
        ('objective_change', 'Cambio de Objetivo'),
        ('resource_allocation', 'Asignación de Recursos'),
        ('process_change', 'Cambio de Proceso'),
        ('corrective_action', 'Acción Correctiva'),
        ('improvement_opportunity', 'Oportunidad de Mejora'),
        ('strategic_decision', 'Decisión Estratégica'),
    ]
    STATUS_CHOICES = [
        ('proposed', 'Propuesta'),
        ('approved', 'Aprobada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('rejected', 'Rechazada'),
    ]

    review = models.ForeignKey(
        ManagementReview, on_delete=models.CASCADE, related_name='decisions'
    )
    title = models.CharField(max_length=300)
    description = models.TextField()
    decision_type = models.CharField(max_length=30, choices=DECISION_TYPE_CHOICES)
    responsible = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='responsible_decisions',
        help_text="Regla ISO: toda decisión debe tener responsable asignado"
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='proposed'
    )

    # Trazabilidad IA → Humano
    ai_suggested = models.BooleanField(
        default=False,
        help_text="Sugerida por IA — requiere aprobación humana explícita"
    )
    rationale = models.TextField(
        blank=True, help_text="Por qué se tomó esta decisión (registro del 'por qué')"
    )

    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='approved_decisions'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Decisión de Revisión"
        verbose_name_plural = "Decisiones de Revisión"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.review.title}]"

    def approve(self, user):
        if not self.responsible_id:
            raise ValueError(
                "Regla ISO: toda decisión debe tener responsable asignado antes de aprobarse"
            )
        self.approved_by = user
        self.approved_at = timezone.now()
        self.status = 'approved'
        self.save(update_fields=['approved_by', 'approved_at', 'status'])


# ─────────────────────────────────────────────────────────────
# REGISTRO INMUTABLE DE APROBACIONES  (firma digital SHA-256)
# ─────────────────────────────────────────────────────────────

class ApprovalRecord(models.Model):
    """
    Registro inmutable de aprobaciones con firma digital.
    Una vez creado, no se modifica — es la cadena de custodia auditora.
    """

    WORKFLOW_TYPE_CHOICES = [
        ('quality_policy', 'Política de Calidad'),
        ('review_minutes', 'Acta de Revisión'),
        ('review_decision', 'Decisión de Revisión'),
        ('raci_matrix', 'Matriz RACI'),
        ('strategic_decision', 'Decisión Estratégica'),
        ('resource_allocation', 'Asignación de Recursos'),
        ('objective', 'Objetivo de Calidad'),
        ('evidence_node', 'Nodo de Evidencia'),
    ]

    organization_id = models.IntegerField(db_index=True)
    workflow_type = models.CharField(max_length=30, choices=WORKFLOW_TYPE_CHOICES)
    reference_id = models.IntegerField()
    reference_model = models.CharField(max_length=100)
    title = models.CharField(max_length=300)

    # Firmante — PROTECT para no eliminar registros si el usuario se borra
    approved_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='approval_records'
    )
    # auto_now_add → inmutable
    approved_at = models.DateTimeField(auto_now_add=True)

    # SHA-256(json(content_snapshot) + user_id + approved_at ISO)
    digital_signature = models.CharField(
        max_length=64,
        help_text="SHA-256 del snapshot de contenido + ID usuario + timestamp"
    )
    content_snapshot = models.JSONField(
        help_text="Snapshot inmutable del contenido aprobado en el momento de firma"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Registro de Aprobación"
        verbose_name_plural = "Registros de Aprobación"
        ordering = ['-approved_at']
        indexes = [
            models.Index(fields=['organization_id', 'workflow_type']),
            models.Index(fields=['reference_model', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.get_workflow_type_display()} | {self.title} | {self.approved_at}"

    @classmethod
    def generate_signature(cls, content_snapshot: dict, user_id: int, timestamp_iso: str) -> str:
        import hashlib, json
        payload = json.dumps(
            {'content': content_snapshot, 'user_id': user_id, 'ts': timestamp_iso},
            sort_keys=True, ensure_ascii=False
        )
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()


# ─────────────────────────────────────────────────────────────
# CULTURA DE CALIDAD Y ÉTICA  (ISO 9001:2026 – nuevo)
# Regla estricta: sin vigilancia individual, solo tendencias
# ─────────────────────────────────────────────────────────────

class QualityCultureSurvey(models.Model):
    """Micro-encuesta anónima de cultura de calidad."""

    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('active', 'Activa'),
        ('closed', 'Cerrada'),
        ('archived', 'Archivada'),
    ]

    organization_id = models.IntegerField(db_index=True)
    organization_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    questions = models.JSONField(
        default=list,
        help_text="[{id, text, type: 'scale'|'choice'|'text', options}]"
    )
    min_responses_for_analysis = models.IntegerField(
        default=5,
        help_text="Mínimo de respuestas para mostrar resultados (protección privacidad)"
    )
    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name='created_surveys'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Encuesta de Cultura"
        verbose_name_plural = "Encuestas de Cultura"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization_id', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.organization_name})"


class SurveyResponse(models.Model):
    """
    Respuesta anónima a encuesta de cultura.
    POR DISEÑO: sin FK a usuario — privacidad garantizada por arquitectura.
    Los resultados solo se muestran agregados si hay >= min_responses.
    """

    survey = models.ForeignKey(
        QualityCultureSurvey, on_delete=models.CASCADE, related_name='responses'
    )
    responses = models.JSONField(help_text="{question_id: answer_value}")
    submitted_at = models.DateTimeField(auto_now_add=True)
    # Hash de sesión de participación — no permite rastrear al individuo
    session_hash = models.CharField(
        max_length=64,
        help_text="Hash de sesión (no vinculado a identidad — privacidad por diseño)"
    )

    class Meta:
        verbose_name = "Respuesta de Encuesta"
        verbose_name_plural = "Respuestas de Encuesta"
        ordering = ['-submitted_at']
        # Un hash de sesión no puede responder dos veces la misma encuesta
        unique_together = [['survey', 'session_hash']]


# ─────────────────────────────────────────────────────────────
# GOBERNANZA DE IA  (NIST AI RMF / ISO 42001 / EU AI Act)
# Separación explícita: IA recomienda → Humano decide
# ─────────────────────────────────────────────────────────────

class AIGovernanceLog(models.Model):
    """
    Log de gobernanza de IA para el módulo de Liderazgo.
    Registra cada operación de IA: prompt (hashed), respuesta, fuentes, 
    decisión humana y verificaciones de privacidad.
    """

    HUMAN_DECISION_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
        ('modified', 'Modificado con cambios'),
    ]

    organization_id = models.IntegerField(db_index=True)
    module = models.CharField(
        max_length=50, default='leadership',
        help_text="Módulo que originó la operación"
    )
    operation = models.CharField(
        max_length=100,
        help_text="Operación: 'policy_draft', 'voc_analysis', 'raci_gaps', etc."
    )
    model_version = models.CharField(max_length=100, default='unknown')
    prompt_template = models.CharField(
        max_length=200,
        help_text="Nombre de la plantilla de prompt (no el prompt completo)"
    )
    prompt_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 del prompt completo (sin almacenar PII directamente)"
    )
    response_summary = models.TextField(
        help_text="Resumen de la respuesta de IA (sin PII)"
    )
    ai_recommendation = models.JSONField(
        default=dict,
        help_text="Resultado estructurado de la recomendación IA"
    )
    sources_cited = models.JSONField(
        default=list,
        help_text="Fuentes RAG citadas por la IA"
    )
    hallucination_flags = models.JSONField(
        default=list,
        help_text="Alertas detectadas de posibles alucinaciones"
    )
    privacy_check_passed = models.BooleanField(
        default=True,
        help_text="Si el output pasó el control de privacidad por diseño"
    )

    # Decisión humana explícita — eje central de gobernanza
    human_decision = models.CharField(
        max_length=20, choices=HUMAN_DECISION_CHOICES, default='pending'
    )
    decided_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='ai_governance_decisions'
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    human_notes = models.TextField(
        blank=True,
        help_text="Comentarios del humano al aceptar, rechazar o modificar"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Gobernanza IA"
        verbose_name_plural = "Logs de Gobernanza IA"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization_id', 'operation']),
            models.Index(fields=['human_decision']),
            models.Index(fields=['organization_id', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.operation}] org={self.organization_id} | {self.human_decision}"

    def record_human_decision(self, user, decision: str, notes: str = ''):
        if decision not in dict(self.HUMAN_DECISION_CHOICES):
            raise ValueError(f"Decisión inválida: {decision}")
        self.human_decision = decision
        self.decided_by = user
        self.decided_at = timezone.now()
        self.human_notes = notes
        self.save(update_fields=['human_decision', 'decided_by', 'decided_at', 'human_notes'])
