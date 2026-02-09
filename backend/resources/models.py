# resources/models.py
"""
Resources Module - ISO 9001:2015 Cláusula 7
Apoyo - Recursos, Competencia, Conciencia, Comunicación
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Resource(models.Model):
    """
    Recursos organizacionales
    ISO 9001:2015 - Cláusula 7.1
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    RESOURCE_TYPE_CHOICES = [
        ('human', 'Recurso Humano'),
        ('infrastructure', 'Infraestructura'),
        ('technology', 'Tecnología'),
        ('information', 'Información'),
        ('financial', 'Financiero'),
        ('material', 'Material'),
        ('other', 'Otro'),
    ]
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPE_CHOICES)
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Detalles
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0)]
    )
    unit = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Estado
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('in_use', 'En Uso'),
        ('maintenance', 'En Mantenimiento'),
        ('retired', 'Retirado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Responsable
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resources_managed'
    )
    
    # Costos
    acquisition_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    maintenance_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Fechas
    acquisition_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    # Documentación
    documentation = models.FileField(
        upload_to='resources/documentation/',
        null=True,
        blank=True
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"
        ordering = ['resource_type', 'name']
        indexes = [
            models.Index(fields=['organization_id', 'resource_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_resource_type_display()})"


class Infrastructure(models.Model):
    """
    Infraestructura organizacional
    ISO 9001:2015 - Cláusula 7.1.3
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    INFRASTRUCTURE_TYPE_CHOICES = [
        ('building', 'Edificio/Instalación'),
        ('equipment', 'Equipo'),
        ('software', 'Software'),
        ('transport', 'Transporte'),
        ('utilities', 'Servicios'),
    ]
    infrastructure_type = models.CharField(max_length=50, choices=INFRASTRUCTURE_TYPE_CHOICES)
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    description = models.TextField()
    location = models.CharField(max_length=200)
    
    # Capacidad
    capacity = models.CharField(max_length=100, blank=True)
    current_usage = models.CharField(max_length=100, blank=True)
    
    # Mantenimiento
    maintenance_schedule = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: Mensual, Trimestral, Anual"
    )
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    # Estado
    STATUS_CHOICES = [
        ('operational', 'Operativo'),
        ('maintenance', 'En Mantenimiento'),
        ('repair', 'En Reparación'),
        ('out_of_service', 'Fuera de Servicio'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational')
    
    # Responsable
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='infrastructure_managed'
    )
    
    # Documentos
    specifications = models.FileField(
        upload_to='resources/infrastructure/specs/',
        null=True,
        blank=True
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Infraestructura"
        verbose_name_plural = "Infraestructura"
        ordering = ['infrastructure_type', 'name']
        unique_together = [['organization_id', 'code']]
    
    def __str__(self):
        return f"{self.name} - {self.location}"


class WorkEnvironment(models.Model):
    """
    Ambiente de trabajo
    ISO 9001:2015 - Cláusula 7.1.4
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    area_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField()
    
    # Factores físicos
    temperature_control = models.BooleanField(default=False)
    humidity_control = models.BooleanField(default=False)
    lighting_adequate = models.BooleanField(default=True)
    noise_controlled = models.BooleanField(default=True)
    
    # Factores sociales
    ergonomic_conditions = models.TextField(blank=True)
    safety_measures = models.TextField(blank=True)
    
    # Evaluación
    CONDITION_CHOICES = [
        ('excellent', 'Excelente'),
        ('good', 'Bueno'),
        ('fair', 'Regular'),
        ('poor', 'Deficiente'),
    ]
    overall_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    
    # Fechas de evaluación
    last_evaluation_date = models.DateField(null=True, blank=True)
    next_evaluation_date = models.DateField(null=True, blank=True)
    
    # Responsable
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='environments_managed'
    )
    
    # Mejoras
    improvement_actions = models.TextField(
        blank=True,
        help_text="Acciones de mejora planificadas o implementadas"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ambiente de Trabajo"
        verbose_name_plural = "Ambientes de Trabajo"
        ordering = ['area_name']
    
    def __str__(self):
        return f"{self.area_name} - {self.location}"


class Competence(models.Model):
    """
    Competencias del personal
    ISO 9001:2015 - Cláusula 7.2
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Persona
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='competences'
    )
    
    # Puesto/Rol
    position = models.CharField(max_length=200)
    
    # Competencia
    competence_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Nivel requerido vs actual
    LEVEL_CHOICES = [
        ('basic', 'Básico'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
        ('expert', 'Experto'),
    ]
    required_level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    current_level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    
    # Cómo se adquirió
    ACQUISITION_METHOD_CHOICES = [
        ('education', 'Educación Formal'),
        ('training', 'Capacitación'),
        ('experience', 'Experiencia Laboral'),
        ('certification', 'Certificación'),
    ]
    acquisition_method = models.CharField(max_length=50, choices=ACQUISITION_METHOD_CHOICES)
    
    # Evidencias
    evidence = models.FileField(
        upload_to='resources/competences/',
        null=True,
        blank=True,
        help_text="Certificados, diplomas, etc."
    )
    
    # Fechas
    acquired_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Para certificaciones que expiran"
    )
    
    # Evaluación
    last_evaluation_date = models.DateField(null=True, blank=True)
    evaluator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='competences_evaluated'
    )
    evaluation_notes = models.TextField(blank=True)
    
    # Gap
    needs_improvement = models.BooleanField(default=False)
    improvement_plan = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Competencia"
        verbose_name_plural = "Competencias"
        ordering = ['user', 'competence_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.competence_name}"
    
    @property
    def has_gap(self):
        """Verificar si hay brecha entre nivel requerido y actual"""
        levels = ['basic', 'intermediate', 'advanced', 'expert']
        if self.required_level and self.current_level:
            return levels.index(self.required_level) > levels.index(self.current_level)
        return False


class Training(models.Model):
    """
    Capacitaciones y entrenamientos
    ISO 9001:2015 - Cláusula 7.2
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Información del curso
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    description = models.TextField()
    
    # Tipo
    TRAINING_TYPE_CHOICES = [
        ('internal', 'Interno'),
        ('external', 'Externo'),
        ('online', 'En Línea'),
        ('on_the_job', 'En el Puesto'),
    ]
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPE_CHOICES)
    
    # Instructor/Proveedor
    instructor = models.CharField(max_length=200, blank=True)
    provider = models.CharField(max_length=200, blank=True)
    
    # Fechas
    start_date = models.DateField()
    end_date = models.DateField()
    duration_hours = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Participantes
    participants = models.ManyToManyField(
        User,
        related_name='trainings_attended',
        blank=True
    )
    max_participants = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )
    
    # Estado
    STATUS_CHOICES = [
        ('planned', 'Planificado'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Costos
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Evaluación
    evaluation_method = models.CharField(max_length=200, blank=True)
    passing_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Materiales
    materials = models.FileField(
        upload_to='resources/trainings/materials/',
        null=True,
        blank=True
    )
    
    # Responsable
    coordinator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='trainings_coordinated'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Capacitación"
        verbose_name_plural = "Capacitaciones"
        ordering = ['-start_date']
        unique_together = [['organization_id', 'code']]
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"


class Awareness(models.Model):
    """
    Toma de conciencia
    ISO 9001:2015 - Cláusula 7.3
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Actividad
    activity_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Tipo
    AWARENESS_TYPE_CHOICES = [
        ('policy', 'Política de Calidad'),
        ('objectives', 'Objetivos de Calidad'),
        ('contribution', 'Contribución a la Eficacia'),
        ('improvement', 'Beneficios de Mejora'),
        ('nonconformity', 'Implicaciones de No Conformidad'),
    ]
    awareness_type = models.CharField(max_length=50, choices=AWARENESS_TYPE_CHOICES)
    
    # Método
    METHOD_CHOICES = [
        ('meeting', 'Reunión'),
        ('training', 'Capacitación'),
        ('email', 'Correo Electrónico'),
        ('poster', 'Cartel/Póster'),
        ('intranet', 'Intranet'),
        ('video', 'Video'),
        ('other', 'Otro'),
    ]
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    
    # Fecha
    date = models.DateField()
    
    # Participantes
    participants = models.ManyToManyField(
        User,
        related_name='awareness_activities',
        blank=True
    )
    target_audience = models.CharField(max_length=200)
    
    # Responsable
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='awareness_activities_managed'
    )
    
    # Evidencias
    evidence = models.FileField(
        upload_to='resources/awareness/',
        null=True,
        blank=True
    )
    
    # Evaluación
    effectiveness_evaluation = models.TextField(
        blank=True,
        help_text="Cómo se evaluó la efectividad de la actividad"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Actividad de Conciencia"
        verbose_name_plural = "Actividades de Conciencia"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.activity_name} - {self.date}"


class Communication(models.Model):
    """
    Comunicación interna y externa
    ISO 9001:2015 - Cláusula 7.4
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Información básica
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Tipo
    COMMUNICATION_TYPE_CHOICES = [
        ('internal', 'Interna'),
        ('external', 'Externa'),
    ]
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE_CHOICES)
    
    # Método
    METHOD_CHOICES = [
        ('email', 'Correo Electrónico'),
        ('meeting', 'Reunión'),
        ('memo', 'Memorándum'),
        ('report', 'Informe'),
        ('presentation', 'Presentación'),
        ('intranet', 'Intranet'),
        ('notice_board', 'Tablón de Anuncios'),
        ('other', 'Otro'),
    ]
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    
    # Frecuencia (para comunicaciones recurrentes)
    FREQUENCY_CHOICES = [
        ('one_time', 'Una Vez'),
        ('daily', 'Diaria'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('annual', 'Anual'),
    ]
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='one_time')
    
    # Qué se comunica
    content_summary = models.TextField()
    
    # Cuándo
    scheduled_date = models.DateField(null=True, blank=True)
    last_communication_date = models.DateField(null=True, blank=True)
    
    # A quién
    target_audience = models.CharField(max_length=200)
    
    # Quién comunica
    communicator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='communications_sent'
    )
    
    # Evidencia
    evidence = models.FileField(
        upload_to='resources/communications/',
        null=True,
        blank=True
    )
    
    # Estado
    STATUS_CHOICES = [
        ('planned', 'Planificada'),
        ('sent', 'Enviada'),
        ('received', 'Recibida'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Comunicación"
        verbose_name_plural = "Comunicaciones"
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_communication_type_display()})"
