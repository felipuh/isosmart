# operations/models.py
"""
Operations Module - ISO 9001:2015 Cláusula 8
Operación - Procesos operacionales del SGC
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class OperationalControl(models.Model):
    """
    Controles Operacionales
    ISO 9001:2015 - Cláusula 8.1
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Identificación
    control_code = models.CharField(max_length=50, unique=True)
    control_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Tipo de control
    CONTROL_TYPE_CHOICES = [
        ('process', 'Control de Proceso'),
        ('equipment', 'Control de Equipo'),
        ('environment', 'Control de Ambiente'),
        ('monitoring', 'Monitoreo y Medición'),
        ('documentation', 'Control Documental'),
        ('other', 'Otro'),
    ]
    control_type = models.CharField(max_length=50, choices=CONTROL_TYPE_CHOICES)
    
    # Proceso relacionado
    related_process = models.CharField(
        max_length=200,
        blank=True,
        help_text="Proceso al que aplica este control"
    )
    
    # Criterios
    acceptance_criteria = models.TextField(
        verbose_name="Criterios de Aceptación",
        help_text="Criterios para aceptación de productos/servicios"
    )
    
    # Recursos
    required_resources = models.TextField(
        blank=True,
        verbose_name="Recursos Requeridos"
    )
    
    # Responsable
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='operational_controls',
        verbose_name="Responsable"
    )
    
    # Frecuencia
    FREQUENCY_CHOICES = [
        ('continuous', 'Continuo'),
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('annual', 'Anual'),
        ('as_needed', 'Según Necesidad'),
    ]
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='daily'
    )
    
    # Documentación
    procedure_reference = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Referencia a Procedimiento"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Control Operacional"
        verbose_name_plural = "Controles Operacionales"
        ordering = ['control_code']
    
    def __str__(self):
        return f"{self.control_code} - {self.control_name}"


class CustomerRequirement(models.Model):
    """
    Requisitos del Cliente
    ISO 9001:2015 - Cláusula 8.2
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Cliente
    customer_name = models.CharField(max_length=200)
    customer_code = models.CharField(max_length=50, blank=True)
    contact_person = models.CharField(max_length=200, blank=True)
    
    # Requisito
    requirement_code = models.CharField(max_length=50)
    requirement_title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Tipo
    REQUIREMENT_TYPE_CHOICES = [
        ('product', 'Producto'),
        ('service', 'Servicio'),
        ('delivery', 'Entrega'),
        ('quality', 'Calidad'),
        ('regulatory', 'Regulatorio'),
        ('other', 'Otro'),
    ]
    requirement_type = models.CharField(max_length=50, choices=REQUIREMENT_TYPE_CHOICES)
    
    # Comunicación
    communication_date = models.DateField(
        verbose_name="Fecha de Comunicación"
    )
    communication_method = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ej: Email, Reunión, Contrato"
    )
    
    # Revisión
    is_reviewed = models.BooleanField(
        default=False,
        verbose_name="Revisado"
    )
    review_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Revisión"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements_reviewed'
    )
    review_notes = models.TextField(blank=True)
    
    # Confirmación
    is_confirmed = models.BooleanField(
        default=False,
        verbose_name="Confirmado con Cliente"
    )
    confirmation_date = models.DateField(null=True, blank=True)
    confirmation_evidence = models.FileField(
        upload_to='operations/requirements/',
        null=True,
        blank=True
    )
    
    # Capacidad
    can_meet_requirement = models.BooleanField(
        default=True,
        verbose_name="¿Podemos Cumplir?"
    )
    capacity_notes = models.TextField(
        blank=True,
        help_text="Notas sobre capacidad de cumplimiento"
    )
    
    # Estado
    STATUS_CHOICES = [
        ('identified', 'Identificado'),
        ('under_review', 'En Revisión'),
        ('confirmed', 'Confirmado'),
        ('in_progress', 'En Progreso'),
        ('fulfilled', 'Cumplido'),
        ('not_feasible', 'No Factible'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='identified'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Requisito del Cliente"
        verbose_name_plural = "Requisitos de los Clientes"
        ordering = ['-communication_date']
        unique_together = [['organization_id', 'requirement_code']]
    
    def __str__(self):
        return f"{self.customer_name} - {self.requirement_title}"


class DesignProject(models.Model):
    """
    Proyectos de Diseño y Desarrollo
    ISO 9001:2015 - Cláusula 8.3
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Identificación
    project_code = models.CharField(max_length=50)
    project_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Tipo
    PROJECT_TYPE_CHOICES = [
        ('product', 'Producto'),
        ('service', 'Servicio'),
        ('process', 'Proceso'),
        ('system', 'Sistema'),
    ]
    project_type = models.CharField(max_length=50, choices=PROJECT_TYPE_CHOICES)
    
    # Etapas de diseño
    STAGE_CHOICES = [
        ('planning', 'Planificación'),
        ('inputs', 'Elementos de Entrada'),
        ('controls', 'Controles'),
        ('outputs', 'Resultados'),
        ('verification', 'Verificación'),
        ('validation', 'Validación'),
        ('changes', 'Control de Cambios'),
        ('completed', 'Completado'),
    ]
    current_stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default='planning'
    )
    
    # Elementos de entrada
    design_inputs = models.TextField(
        blank=True,
        verbose_name="Elementos de Entrada del Diseño"
    )
    
    # Resultados
    design_outputs = models.TextField(
        blank=True,
        verbose_name="Resultados del Diseño"
    )
    
    # Controles
    design_controls = models.TextField(
        blank=True,
        verbose_name="Controles de Diseño y Desarrollo"
    )
    
    # Verificación
    verification_method = models.TextField(
        blank=True,
        verbose_name="Método de Verificación"
    )
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Validación
    validation_method = models.TextField(
        blank=True,
        verbose_name="Método de Validación"
    )
    is_validated = models.BooleanField(default=False)
    validation_date = models.DateField(null=True, blank=True)
    validation_notes = models.TextField(blank=True)
    
    # Responsables
    project_leader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='design_projects_led',
        verbose_name="Líder del Proyecto"
    )
    team_members = models.ManyToManyField(
        User,
        related_name='design_projects',
        blank=True,
        verbose_name="Equipo"
    )
    
    # Fechas
    start_date = models.DateField()
    target_completion_date = models.DateField()
    actual_completion_date = models.DateField(null=True, blank=True)
    
    # Estado
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('on_hold', 'En Espera'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Documentación
    documentation = models.FileField(
        upload_to='operations/design/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proyecto de Diseño y Desarrollo"
        verbose_name_plural = "Proyectos de Diseño y Desarrollo"
        ordering = ['-start_date']
        unique_together = [['organization_id', 'project_code']]
    
    def __str__(self):
        return f"{self.project_code} - {self.project_name}"


class ExternalProvider(models.Model):
    """
    Proveedores Externos
    ISO 9001:2015 - Cláusula 8.4
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Información del proveedor
    provider_code = models.CharField(max_length=50)
    provider_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    # Tipo de provisión
    PROVISION_TYPE_CHOICES = [
        ('product', 'Producto'),
        ('service', 'Servicio'),
        ('process', 'Proceso Subcontratado'),
    ]
    provision_type = models.CharField(max_length=50, choices=PROVISION_TYPE_CHOICES)
    
    # Descripción
    products_services = models.TextField(
        verbose_name="Productos/Servicios Suministrados"
    )
    
    # Evaluación
    evaluation_criteria = models.TextField(
        verbose_name="Criterios de Evaluación"
    )
    last_evaluation_date = models.DateField(null=True, blank=True)
    evaluation_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Puntuación 0-100"
    )
    evaluation_notes = models.TextField(blank=True)
    
    # Clasificación
    CLASSIFICATION_CHOICES = [
        ('approved', 'Aprobado'),
        ('conditional', 'Condicional'),
        ('not_approved', 'No Aprobado'),
    ]
    classification = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_CHOICES,
        default='conditional'
    )
    
    # Desempeño
    performance_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Deficiente, 5=Excelente"
    )
    
    # Controles
    controls_applied = models.TextField(
        blank=True,
        verbose_name="Controles Aplicados al Proveedor"
    )
    
    # Responsable
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='providers_managed'
    )
    
    # Estado
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proveedor Externo"
        verbose_name_plural = "Proveedores Externos"
        ordering = ['provider_name']
        unique_together = [['organization_id', 'provider_code']]
    
    def __str__(self):
        return f"{self.provider_code} - {self.provider_name}"


class ProductionControl(models.Model):
    """
    Control de Producción y Prestación del Servicio
    ISO 9001:2015 - Cláusula 8.5
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Identificación
    control_code = models.CharField(max_length=50)
    product_service_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Tipo
    TYPE_CHOICES = [
        ('production', 'Producción'),
        ('service_delivery', 'Prestación de Servicio'),
    ]
    control_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    
    # Control
    control_method = models.TextField(
        verbose_name="Método de Control"
    )
    
    # Trazabilidad
    requires_traceability = models.BooleanField(
        default=False,
        verbose_name="Requiere Trazabilidad"
    )
    traceability_method = models.TextField(
        blank=True,
        verbose_name="Método de Trazabilidad"
    )
    
    # Propiedad del cliente
    handles_customer_property = models.BooleanField(
        default=False,
        verbose_name="Maneja Propiedad del Cliente"
    )
    customer_property_controls = models.TextField(
        blank=True,
        verbose_name="Controles para Propiedad del Cliente"
    )
    
    # Preservación
    preservation_requirements = models.TextField(
        blank=True,
        verbose_name="Requisitos de Preservación"
    )
    
    # Post-entrega
    post_delivery_activities = models.TextField(
        blank=True,
        verbose_name="Actividades Post-Entrega"
    )
    
    # Cambios
    change_control_process = models.TextField(
        blank=True,
        verbose_name="Proceso de Control de Cambios"
    )
    
    # Responsable
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='production_controls'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Control de Producción"
        verbose_name_plural = "Controles de Producción"
        ordering = ['control_code']
        unique_together = [['organization_id', 'control_code']]
    
    def __str__(self):
        return f"{self.control_code} - {self.product_service_name}"


class ProductRelease(models.Model):
    """
    Liberación de Productos y Servicios
    ISO 9001:2015 - Cláusula 8.6
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Identificación
    release_code = models.CharField(max_length=50)
    product_service_name = models.CharField(max_length=200)
    batch_lot_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Número de Lote/Batch"
    )
    
    # Fecha
    release_date = models.DateField()
    
    # Verificación
    verification_performed = models.BooleanField(
        default=False,
        verbose_name="Verificación Realizada"
    )
    verification_results = models.TextField(
        blank=True,
        verbose_name="Resultados de Verificación"
    )
    
    # Criterios de aceptación
    acceptance_criteria_met = models.BooleanField(
        default=False,
        verbose_name="Criterios de Aceptación Cumplidos"
    )
    criteria_details = models.TextField(
        blank=True,
        verbose_name="Detalles de Criterios"
    )
    
    # Autorización
    authorized_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='releases_authorized',
        verbose_name="Autorizado por"
    )
    authorization_date = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Trazabilidad
    traceability_info = models.TextField(
        blank=True,
        verbose_name="Información de Trazabilidad"
    )
    
    # Cliente
    customer_name = models.CharField(max_length=200, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    
    # Cantidad
    quantity_released = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    unit = models.CharField(max_length=50, blank=True)
    
    # Estado
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('released', 'Liberado'),
        ('rejected', 'Rechazado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Notas
    notes = models.TextField(blank=True)
    
    # Evidencia
    evidence = models.FileField(
        upload_to='operations/releases/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Liberación de Producto/Servicio"
        verbose_name_plural = "Liberaciones de Productos/Servicios"
        ordering = ['-release_date']
        unique_together = [['organization_id', 'release_code']]
    
    def __str__(self):
        return f"{self.release_code} - {self.product_service_name}"


class Nonconformity(models.Model):
    """
    No Conformidades (Salidas No Conformes)
    ISO 9001:2015 - Cláusula 8.7
    """
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    
    # Identificación
    nc_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número de NC"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(verbose_name="Descripción de la No Conformidad")
    
    # Detección
    detection_date = models.DateField(verbose_name="Fecha de Detección")
    detected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='nonconformities_detected',
        verbose_name="Detectado por"
    )
    
    # Etapa
    DETECTION_STAGE_CHOICES = [
        ('production', 'Durante Producción'),
        ('pre_delivery', 'Antes de Entrega'),
        ('post_delivery', 'Después de Entrega'),
        ('in_use', 'Durante Uso'),
    ]
    detection_stage = models.CharField(
        max_length=50,
        choices=DETECTION_STAGE_CHOICES
    )
    
    # Tipo
    NC_TYPE_CHOICES = [
        ('product', 'Producto'),
        ('service', 'Servicio'),
        ('process', 'Proceso'),
        ('documentation', 'Documentación'),
    ]
    nc_type = models.CharField(
        max_length=50,
        choices=NC_TYPE_CHOICES,
        verbose_name="Tipo de NC"
    )
    
    # Severidad
    SEVERITY_CHOICES = [
        ('minor', 'Menor'),
        ('major', 'Mayor'),
        ('critical', 'Crítica'),
    ]
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='minor'
    )
    
    # Producto/Servicio afectado
    affected_product_service = models.CharField(max_length=200)
    batch_lot_number = models.CharField(max_length=100, blank=True)
    quantity_affected = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Cliente
    affects_customer = models.BooleanField(
        default=False,
        verbose_name="Afecta al Cliente"
    )
    customer_name = models.CharField(max_length=200, blank=True)
    customer_notified = models.BooleanField(default=False)
    notification_date = models.DateField(null=True, blank=True)
    
    # Estado
    STATUS_CHOICES = [
        ('identified', 'Identificada'),
        ('under_review', 'En Revisión'),
        ('disposition_pending', 'Disposición Pendiente'),
        ('treated', 'Tratada'),
        ('closed', 'Cerrada'),
    ]
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='identified'
    )
    
    # Responsable
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='nonconformities_responsible',
        verbose_name="Responsable del Tratamiento"
    )
    
    # Evidencia
    evidence = models.FileField(
        upload_to='operations/nonconformities/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "No Conformidad"
        verbose_name_plural = "No Conformidades"
        ordering = ['-detection_date']
    
    def __str__(self):
        return f"{self.nc_number} - {self.title}"


class Disposition(models.Model):
    """
    Disposición de No Conformidades
    ISO 9001:2015 - Cláusula 8.7
    """
    nonconformity = models.OneToOneField(
        Nonconformity,
        on_delete=models.CASCADE,
        related_name='disposition'
    )
    
    # Decisión
    DISPOSITION_CHOICES = [
        ('correction', 'Corrección (Reparar/Retrabajar)'),
        ('segregation', 'Segregación/Contención'),
        ('scrap', 'Desecho/Destrucción'),
        ('regrading', 'Reclasificación'),
        ('concession', 'Concesión (Usar como está)'),
        ('return', 'Devolución al Proveedor'),
    ]
    disposition_action = models.CharField(
        max_length=50,
        choices=DISPOSITION_CHOICES,
        verbose_name="Acción de Disposición"
    )
    
    # Detalles
    action_description = models.TextField(
        verbose_name="Descripción de la Acción"
    )
    
    # Autorización
    requires_authorization = models.BooleanField(
        default=False,
        verbose_name="Requiere Autorización"
    )
    authorized_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispositions_authorized'
    )
    authorization_date = models.DateTimeField(null=True, blank=True)
    authorization_notes = models.TextField(blank=True)
    
    # Implementación
    implemented_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispositions_implemented'
    )
    implementation_date = models.DateField(null=True, blank=True)
    implementation_notes = models.TextField(blank=True)
    
    # Verificación
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Verificada"
    )
    verification_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispositions_verified'
    )
    verification_notes = models.TextField(blank=True)
    
    # Efectividad
    is_effective = models.BooleanField(
        default=False,
        verbose_name="Acción Efectiva"
    )
    effectiveness_notes = models.TextField(blank=True)
    
    # Costos
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Disposición"
        verbose_name_plural = "Disposiciones"
    
    def __str__(self):
        return f"Disposición: {self.nonconformity.nc_number}"
