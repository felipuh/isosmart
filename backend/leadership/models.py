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
