from django.conf import settings
from django.db import models


class AssistantConversation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('archived', 'Archivada'),
    ]

    organization_id = models.IntegerField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assistant_conversations',
    )
    title = models.CharField(max_length=200, default='Nueva conversación')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_route = models.CharField(max_length=255, blank=True)
    current_module = models.CharField(max_length=80, blank=True)
    current_submodule = models.CharField(max_length=120, blank=True)
    last_standard_focus = models.CharField(max_length=80, blank=True)
    last_clause_focus = models.CharField(max_length=40, blank=True)
    context_summary = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assistant_conversations'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['organization_id', 'status']),
            models.Index(fields=['organization_id', 'updated_at']),
            models.Index(fields=['organization_id', 'user']),
        ]

    def __str__(self):
        return f"{self.organization_id} - {self.title}"


class AssistantMessage(models.Model):
    ROLE_CHOICES = [
        ('system', 'Sistema'),
        ('user', 'Usuario'),
        ('assistant', 'Asistente'),
        ('tool', 'Herramienta'),
    ]

    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    organization_id = models.IntegerField(db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    content_type = models.CharField(max_length=30, default='text')
    model_name = models.CharField(max_length=80, blank=True)
    token_usage_prompt = models.IntegerField(null=True, blank=True)
    token_usage_completion = models.IntegerField(null=True, blank=True)
    token_usage_total = models.IntegerField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assistant_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['organization_id', 'conversation']),
            models.Index(fields=['organization_id', 'created_at']),
        ]

    def __str__(self):
        return f"{self.organization_id} - {self.role}"


class AssistantOrgProfile(models.Model):
    organization_id = models.IntegerField(unique=True)
    primary_standards = models.JSONField(default=list, blank=True)
    secondary_standards = models.JSONField(default=list, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    risk_tolerance = models.CharField(max_length=50, blank=True)
    organization_summary = models.TextField(blank=True)
    preferred_response_style = models.CharField(max_length=50, default='pragmatic')
    forbidden_topics = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assistant_org_profiles'
        indexes = [
            models.Index(fields=['organization_id', 'updated_at']),
        ]

    def __str__(self):
        return f"Org {self.organization_id}"


class AssistantMemoryItem(models.Model):
    MEMORY_TYPE_CHOICES = [
        ('decision', 'Decision'),
        ('fact', 'Fact'),
        ('risk', 'Risk'),
        ('evidence', 'Evidence'),
        ('policy', 'Policy'),
        ('summary', 'Summary'),
    ]

    organization_id = models.IntegerField(db_index=True)
    memory_type = models.CharField(max_length=40, choices=MEMORY_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    source_type = models.CharField(max_length=40, blank=True)
    source_id = models.CharField(max_length=80, blank=True)
    module = models.CharField(max_length=60, blank=True)
    standard_code = models.CharField(max_length=40, blank=True)
    clause_reference = models.CharField(max_length=40, blank=True)
    confidence_score = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assistant_memory_items'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['organization_id', 'memory_type']),
            models.Index(fields=['organization_id', 'module']),
            models.Index(fields=['organization_id', 'standard_code']),
            models.Index(fields=['organization_id', 'is_active']),
        ]

    def __str__(self):
        return f"{self.organization_id} - {self.title}"


class AssistantPromptConfig(models.Model):
    organization_id = models.IntegerField(unique=True)
    system_prompt = models.TextField(blank=True)
    normative_policy = models.TextField(blank=True)
    response_policy = models.TextField(blank=True)
    citation_policy = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_prompt_updates',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assistant_prompt_configs'

    def __str__(self):
        return f"PromptConfig Org {self.organization_id}"


class AssistantFeedback(models.Model):
    organization_id = models.IntegerField(db_index=True)
    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.CASCADE,
        related_name='feedback_items',
    )
    message = models.ForeignKey(
        AssistantMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_items',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_feedback_items',
    )
    rating = models.SmallIntegerField()
    feedback_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assistant_feedback'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization_id', 'rating']),
            models.Index(fields=['organization_id', 'created_at']),
        ]


class AssistantAuditLog(models.Model):
    organization_id = models.IntegerField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_audit_logs',
    )
    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    event_type = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assistant_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization_id', 'event_type']),
            models.Index(fields=['organization_id', 'created_at']),
        ]


class AssistantDocumentChunk(models.Model):
    SOURCE_CHOICES = [
        ('document', 'Documento'),
        ('policy', 'Política'),
        ('procedure', 'Procedimiento'),
        ('record', 'Registro'),
        ('manual', 'Manual'),
        ('regulation', 'Normativa externa'),
        ('memory_item', 'Elemento de memoria'),
    ]

    organization_id = models.IntegerField(db_index=True)
    document_id = models.CharField(max_length=120, db_index=True)
    chunk_index = models.PositiveSmallIntegerField(default=0)
    chunk_text = models.TextField()
    source_type = models.CharField(max_length=40, choices=SOURCE_CHOICES, default='document')
    source_title = models.CharField(max_length=255, blank=True)
    module = models.CharField(max_length=60, blank=True)
    standard_code = models.CharField(max_length=40, blank=True)
    clause_reference = models.CharField(max_length=40, blank=True)
    # ID del vector en la colección Chroma/Qdrant
    vector_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    version = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assistant_document_chunks'
        unique_together = [('organization_id', 'document_id', 'chunk_index', 'version')]
        ordering = ['document_id', 'chunk_index']
        indexes = [
            models.Index(fields=['organization_id', 'document_id']),
            models.Index(fields=['organization_id', 'module']),
            models.Index(fields=['organization_id', 'standard_code']),
            models.Index(fields=['organization_id', 'is_active']),
        ]

    def __str__(self):
        return f"Org {self.organization_id} | {self.document_id} #{self.chunk_index}"