import uuid

from django.db import models


class TenantProjection(models.Model):
    """Local, non-authoritative projection of an AdminApps tenant."""

    class LifecycleStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        DEPROVISIONING = "deprovisioning", "Deprovisioning"
        DELETED_TOMBSTONE = "deleted_tombstone", "Deleted tombstone"
        DRIFTED = "drifted", "Drifted"
        UNKNOWN = "unknown", "Unknown"

    class ProvisioningStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partial"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    class ReconciliationStatus(models.TextChoices):
        IN_SYNC = "in_sync", "In sync"
        STALE = "stale", "Stale"
        MISSING_LOCAL = "missing_local", "Missing local"
        UNEXPECTED_LOCAL = "unexpected_local", "Unexpected local"
        VERSION_CONFLICT = "version_conflict", "Version conflict"
        AUTHORITY_UNAVAILABLE = "authority_unavailable", "Authority unavailable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    adminapps_tenant_id = models.UUIDField(unique=True, editable=False)
    source_version = models.BigIntegerField()
    source_event_id = models.UUIDField(null=True, unique=True)
    display_name_snapshot = models.CharField(max_length=255)
    lifecycle_status = models.CharField(
        max_length=32, choices=LifecycleStatus.choices, default=LifecycleStatus.PENDING
    )
    provisioning_status = models.CharField(
        max_length=32,
        choices=ProvisioningStatus.choices,
        default=ProvisioningStatus.PENDING,
    )
    reconciliation_status = models.CharField(
        max_length=32,
        choices=ReconciliationStatus.choices,
        default=ReconciliationStatus.IN_SYNC,
    )
    reconciliation_error_code = models.CharField(max_length=64, null=True, blank=True)
    last_synced_at = models.DateTimeField()
    last_reconciled_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    deletion_requested_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'qms"."tenant_projection'
        constraints = [
            models.CheckConstraint(
                check=models.Q(lifecycle_status__in=(
                    "pending", "active", "suspended", "deprovisioning",
                    "deleted_tombstone", "drifted", "unknown",
                )),
                name="foundation_tenant_lifecycle_valid",
            ),
            models.CheckConstraint(
                check=models.Q(provisioning_status__in=("pending", "partial", "complete", "failed")),
                name="foundation_tenant_provisioning_valid",
            ),
            models.CheckConstraint(
                check=models.Q(reconciliation_status__in=(
                    "in_sync", "stale", "missing_local", "unexpected_local",
                    "version_conflict", "authority_unavailable",
                )),
                name="foundation_tenant_reconciliation_valid",
            ),
            models.CheckConstraint(
                check=models.Q(source_version__gte=0),
                name="foundation_tenant_source_version_nonnegative",
            ),
        ]


class Organization(models.Model):
    """Greenfield QMS organization; distinct from the tenant control plane."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        TenantProjection,
        on_delete=models.PROTECT,
        related_name="qms_organizations",
        db_column="tenant_id",
    )
    display_name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'qms"."organization'


class Stakeholder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    stakeholder_type = models.CharField(max_length=80)
    name = models.CharField(max_length=255)
    relevance_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'qms"."stakeholder'


class Process(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    name = models.CharField(max_length=255)
    owner = models.ForeignKey("UserProjection", on_delete=models.PROTECT, db_column="owner_id", null=True, blank=True)
    process_type = models.CharField(max_length=80, null=True, blank=True)
    status = models.CharField(max_length=40, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'qms"."process'


class StakeholderRequirement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    stakeholder = models.ForeignKey(Stakeholder, on_delete=models.PROTECT, db_column="stakeholder_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    requirement_text = models.TextField()
    qms_addressed = models.BooleanField(default=False)
    owner_process = models.ForeignKey(Process, on_delete=models.PROTECT, db_column="owner_process_id", null=True, blank=True)
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."stakeholder_requirement'


class ContextItem(models.Model):
    class IssueType(models.TextChoices):
        INTERNAL = "internal", "Internal"
        EXTERNAL = "external", "External"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    issue_type = models.CharField(max_length=16, choices=IssueType.choices)
    description = models.TextField()
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."context_item'


class QmsScope(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    boundaries = models.TextField()
    applicability = models.TextField()
    products_services = models.TextField()
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."qms_scope'


class QmsScopeProcess(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    scope_revision = models.ForeignKey(QmsScope, on_delete=models.PROTECT, db_column="scope_revision_id")
    process = models.ForeignKey(Process, on_delete=models.PROTECT, db_column="process_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."qms_scope_process'


class Risk(models.Model):
    """Append-only assessment revision for one logical business risk."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    process = models.ForeignKey(Process, on_delete=models.PROTECT, db_column="process_id")
    cause = models.TextField()
    event = models.TextField()
    consequence = models.TextField()
    likelihood = models.TextField()
    impact = models.TextField()
    residual = models.TextField()
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."risk'


class Opportunity(models.Model):
    """Append-only revision for one logical opportunity, separate from Risk."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    process = models.ForeignKey(Process, on_delete=models.PROTECT, db_column="process_id")
    hypothesis = models.TextField()
    benefit = models.TextField()
    feasibility = models.TextField()
    status = models.CharField(max_length=40)
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."opportunity'


class Objective(models.Model):
    """Append-only quality-objective revision with a source-backed metric reference."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    owner = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="owner_id", null=True, blank=True,
    )
    metric = models.ForeignKey(
        "MeasurementDefinition", on_delete=models.PROTECT, db_column="metric_id",
        null=True, blank=True,
    )
    target = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=40)
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."objective'


class MeasurementDefinition(models.Model):
    """Versioned definition of what, how and when to measure; not a KPI subsystem."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    process = models.ForeignKey(
        Process, on_delete=models.PROTECT, db_column="process_id", null=True, blank=True,
    )
    what_is_measured = models.TextField()
    method = models.TextField()
    measurement_timing = models.TextField()
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."measurement_definition'


class Change(models.Model):
    """Permanent Change business object represented by append-only revisions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    change_type = models.CharField(max_length=80, db_column="type")
    purpose = models.TextField()
    impact = models.TextField()
    status = models.CharField(max_length=40)
    approval_id = models.UUIDField(null=True, blank=True)
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."change'


class ChangeProcess(models.Model):
    """Source-backed affected Process snapshot for one Change revision."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    change_revision = models.ForeignKey(Change, on_delete=models.PROTECT, db_column="change_revision_id")
    process = models.ForeignKey(Process, on_delete=models.PROTECT, db_column="process_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."change_process'


class Standard(models.Model):
    """Global logical identity of a curated normative standard."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=120, unique=True)
    title = models.TextField(null=True, blank=True)
    publisher = models.CharField(max_length=160, default="ISO")

    class Meta:
        managed = False
        db_table = 'normative"."standard'


class StandardEdition(models.Model):
    """Concrete normative edition; published material is immutable."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard = models.ForeignKey(Standard, on_delete=models.PROTECT, db_column="standard_id")
    edition = models.CharField(max_length=120)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    source_hash = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'normative"."standard_edition'


class Clause(models.Model):
    """Edition-safe clause hierarchy node without licensed normative text."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard_edition = models.ForeignKey(
        StandardEdition, on_delete=models.PROTECT, db_column="standard_edition_id",
    )
    code = models.CharField(max_length=80)
    title = models.TextField(null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, db_column="parent_id",
        related_name="children", null=True, blank=True,
    )

    class Meta:
        managed = False
        db_table = 'normative"."clause'


class RequirementControl(models.Model):
    """Atomic evaluable normative unit, distinct from a business requirement."""

    class CertifiabilityClassification(models.TextChoices):
        NORMATIVE_REQUIREMENT = "normative_requirement", "Normative requirement"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard_edition = models.ForeignKey(
        StandardEdition, on_delete=models.PROTECT, db_column="standard_edition_id",
    )
    clause = models.ForeignKey(Clause, on_delete=models.PROTECT, db_column="clause_id")
    paraphrase = models.TextField()
    applicability_rule = models.JSONField(default=dict)
    control_type = models.CharField(max_length=120, null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    @property
    def certifiability_classification(self):
        return self.CertifiabilityClassification.NORMATIVE_REQUIREMENT

    class Meta:
        managed = False
        db_table = 'normative"."requirement_control'


class KnowledgeLayer(models.Model):
    """Global methodological layer identity tied to an exact source edition."""

    class CertifiabilityClassification(models.TextChoices):
        NON_CERTIFIABLE_GUIDANCE = "non_certifiable_guidance", "Non-certifiable guidance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard_edition = models.ForeignKey(
        StandardEdition, on_delete=models.PROTECT, db_column="standard_edition_id",
    )
    layer_type = models.CharField(max_length=120)
    certifiability_classification = models.CharField(
        max_length=40,
        choices=CertifiabilityClassification.choices,
        default=CertifiabilityClassification.NON_CERTIFIABLE_GUIDANCE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'normative"."knowledge_layer'


class KnowledgeLayerRule(models.Model):
    """Exact append-only revision of non-certifiable methodological guidance."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    class CertifiabilityClassification(models.TextChoices):
        NON_CERTIFIABLE_GUIDANCE = "non_certifiable_guidance", "Non-certifiable guidance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge_layer = models.ForeignKey(
        KnowledgeLayer, on_delete=models.PROTECT, db_column="knowledge_layer_id",
    )
    lineage_id = models.UUIDField()
    rule_key = models.CharField(max_length=160)
    version = models.CharField(max_length=80)
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    logic_json = models.JSONField(default=dict)
    evidence_expectation = models.JSONField(default=dict)
    source_reference = models.TextField(null=True, blank=True)
    certifiability_classification = models.CharField(
        max_length=40,
        choices=CertifiabilityClassification.choices,
        default=CertifiabilityClassification.NON_CERTIFIABLE_GUIDANCE,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'normative"."knowledge_layer_rule'


class KnowledgeLayerBinding(models.Model):
    """Guidance-only relation from one exact Rule revision to one exact control."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    class RelationshipType(models.TextChoices):
        INFORMS = "informs", "Informs"

    class SemanticEffect(models.TextChoices):
        GUIDANCE_ONLY = "guidance_only", "Guidance only"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge_layer_rule = models.ForeignKey(
        KnowledgeLayerRule, on_delete=models.PROTECT, db_column="knowledge_layer_rule_id",
    )
    standard_edition = models.ForeignKey(
        StandardEdition, on_delete=models.PROTECT, db_column="standard_edition_id",
    )
    requirement_control = models.ForeignKey(
        RequirementControl, on_delete=models.PROTECT, db_column="requirement_control_id",
    )
    relationship_type = models.CharField(
        max_length=40, choices=RelationshipType.choices,
        default=RelationshipType.INFORMS,
    )
    priority = models.CharField(max_length=40, null=True, blank=True)
    rationale = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    semantic_effect = models.CharField(
        max_length=40,
        choices=SemanticEffect.choices,
        default=SemanticEffect.GUIDANCE_ONLY,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'normative"."knowledge_layer_binding'


class NormativeCurationAudit(models.Model):
    """Append-only global audit record for the isolated curator boundary."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=160)
    entity_type = models.CharField(max_length=120)
    entity_id = models.UUIDField()
    actor_id = models.CharField(max_length=255)
    trace_id = models.UUIDField()
    payload_hash = models.CharField(max_length=64)
    occurred_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'normative"."curation_audit'


class Document(models.Model):
    """Logical identity of controlled documented information."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    document_type = models.CharField(max_length=80, db_column="doc_type")
    owner = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="owner_id", null=True, blank=True,
    )
    current_version = models.ForeignKey(
        "DocumentVersion", on_delete=models.PROTECT, db_column="current_version_id",
        null=True, blank=True, related_name="current_for_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'qms"."document'


class DocumentVersion(models.Model):
    """Immutable material version; bytes live beyond the PostgreSQL boundary."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    document = models.ForeignKey(Document, on_delete=models.PROTECT, db_column="document_id")
    version = models.CharField(max_length=80)
    predecessor = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="predecessor_id",
        related_name="successor", null=True, blank=True,
    )
    content_reference = models.TextField()
    content_hash = models.CharField(max_length=64)
    approved_by = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="approved_by",
        null=True, blank=True, related_name="approved_document_versions",
    )
    effective_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."document_version'


class Evidence(models.Model):
    """Canonical, append-only evidence revision with structured source provenance."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    lineage_id = models.UUIDField()
    revision = models.PositiveIntegerField()
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    source_type = models.CharField(max_length=80)
    source_uri = models.TextField(null=True, blank=True)
    content_hash = models.CharField(max_length=64)
    captured_at = models.DateTimeField()
    trust_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.PROTECT, db_column="document_version_id",
        null=True, blank=True,
    )
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."evidence'


class EvidenceCoverage(models.Model):
    """Append-only assessment against an exact evidence and normative revision."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    evidence = models.ForeignKey(Evidence, on_delete=models.PROTECT, db_column="evidence_id")
    standard_edition = models.ForeignKey(
        StandardEdition, on_delete=models.PROTECT, db_column="standard_edition_id",
    )
    requirement_control = models.ForeignKey(
        RequirementControl, on_delete=models.PROTECT, db_column="requirement_control_id",
    )
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    validation_status = models.CharField(max_length=80, default="proposed")
    validated_by = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="validated_by",
        null=True, blank=True, related_name="validated_evidence_coverages",
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."evidence_coverage'


class Recommendation(models.Model):
    """Immutable governed proposal; persistence never authorizes execution."""

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    title = models.TextField()
    body = models.TextField()
    confidence = models.DecimalField(max_digits=5, decimal_places=4)
    assumptions = models.JSONField(default=list)
    impact = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PROPOSED)
    intended_autonomy = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."recommendation'


class RecommendationBasis(models.Model):
    """Append-only frozen provenance for one exact recommendation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    recommendation = models.ForeignKey(
        Recommendation, on_delete=models.PROTECT, db_column="recommendation_id",
        related_name="basis_rows",
    )
    standard_edition = models.ForeignKey(
        StandardEdition, on_delete=models.PROTECT, db_column="standard_edition_id",
    )
    requirement_control = models.ForeignKey(
        RequirementControl, on_delete=models.PROTECT, db_column="requirement_control_id",
    )
    knowledge_layer_rule = models.ForeignKey(
        KnowledgeLayerRule, on_delete=models.PROTECT, db_column="knowledge_layer_rule_id",
    )
    evidence = models.ForeignKey(Evidence, on_delete=models.PROTECT, db_column="evidence_id")
    rationale = models.TextField()
    model_provider = models.CharField(max_length=120, null=True, blank=True)
    model_identifier = models.CharField(max_length=200)
    model_version = models.CharField(max_length=120)
    prompt_version = models.CharField(max_length=120)
    rule_bundle_version = models.CharField(max_length=120)
    dataset_version_reference = models.TextField(null=True, blank=True)
    embedding_namespace = models.TextField(null=True, blank=True)
    trace_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."recommendation_basis'


class ModelPolicy(models.Model):
    """Versioned global AI-governance policy; published rows are immutable."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lineage_id = models.UUIDField()
    policy_key = models.CharField(max_length=160)
    version = models.CharField(max_length=80)
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    approved_models = models.JSONField(default=list)
    data_classes = models.JSONField(default=list)
    guardrails = models.JSONField(default=dict)
    human_gate_rules = models.JSONField(default=dict)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'governance"."model_policy'


class AgentDefinition(models.Model):
    """Versioned global definition of one logical agent capability."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lineage_id = models.UUIDField()
    agent_key = models.CharField(max_length=160)
    name = models.CharField(max_length=240)
    version = models.CharField(max_length=80)
    previous_revision = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="previous_revision_id",
        related_name="next_revision", null=True, blank=True,
    )
    purpose = models.TextField()
    capability = models.CharField(max_length=160)
    autonomy_max = models.PositiveSmallIntegerField()
    model_policy = models.ForeignKey(
        ModelPolicy, on_delete=models.PROTECT, db_column="model_policy_id",
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'governance"."agent_definition'


class AgentCatalogCurationAudit(models.Model):
    """Append-only global ledger for the isolated agent catalog curator."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=160)
    entity_type = models.CharField(max_length=120)
    entity_id = models.UUIDField()
    actor_id = models.CharField(max_length=255)
    trace_id = models.UUIDField()
    payload_hash = models.CharField(max_length=64)
    occurred_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'governance"."curation_audit'


class AgentRun(models.Model):
    """One concrete governed execution record; never an action authority."""

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    agent_definition = models.ForeignKey(
        AgentDefinition, on_delete=models.PROTECT, db_column="agent_definition_id",
    )
    model_policy = models.ForeignKey(
        ModelPolicy, on_delete=models.PROTECT, db_column="model_policy_id",
    )
    capability = models.CharField(max_length=160)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.RUNNING)
    requested_autonomy = models.PositiveSmallIntegerField()
    effective_autonomy_ceiling = models.PositiveSmallIntegerField()
    model_provider = models.CharField(max_length=120, null=True, blank=True)
    model_identifier = models.CharField(max_length=200)
    model_version = models.CharField(max_length=120)
    prompt_version = models.CharField(max_length=120)
    rule_bundle_version = models.CharField(max_length=120)
    dataset_version_reference = models.TextField(null=True, blank=True)
    embedding_namespace = models.TextField(null=True, blank=True)
    trace_id = models.UUIDField()
    correlation_id = models.UUIDField(null=True, blank=True)
    causation_id = models.UUIDField(null=True, blank=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."agent_run'


class AgentRunInput(models.Model):
    """Frozen typed input bundle: normative/retrieval context plus exact rule."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    agent_run = models.ForeignKey(
        AgentRun, on_delete=models.PROTECT, db_column="agent_run_id", related_name="frozen_inputs",
    )
    standard_edition = models.ForeignKey(
        StandardEdition, on_delete=models.PROTECT, db_column="standard_edition_id",
    )
    requirement_control = models.ForeignKey(
        RequirementControl, on_delete=models.PROTECT, db_column="requirement_control_id",
    )
    knowledge_layer_rule = models.ForeignKey(
        KnowledgeLayerRule, on_delete=models.PROTECT, db_column="knowledge_layer_rule_id",
    )
    evidence = models.ForeignKey(Evidence, on_delete=models.PROTECT, db_column="evidence_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."agent_run_input'


class AgentRunRecommendation(models.Model):
    """Immutable output linkage; Recommendation remains its own aggregate."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    agent_run = models.OneToOneField(
        AgentRun, on_delete=models.PROTECT, db_column="agent_run_id", related_name="recommendation_link",
    )
    recommendation = models.OneToOneField(
        Recommendation, on_delete=models.PROTECT, db_column="recommendation_id",
        related_name="agent_run_link",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."agent_run_recommendation'


class AgentDecision(models.Model):
    """Append-only governed decision/proposal derived from one exact AgentRun."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    agent_run = models.ForeignKey(
        AgentRun, on_delete=models.PROTECT, db_column="agent_run_id", related_name="decisions",
    )
    recommendation = models.ForeignKey(
        Recommendation, on_delete=models.PROTECT, db_column="recommendation_id",
        related_name="agent_decisions", null=True, blank=True,
    )
    decision_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    confidence = models.DecimalField(max_digits=5, decimal_places=4)
    explainability = models.JSONField(default=dict)
    decision_autonomy = models.PositiveSmallIntegerField()
    human_gate_required = models.BooleanField()
    trace_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."agent_decision'


class Approval(models.Model):
    """Append-only human governance outcome; never an execution record."""

    class Decision(models.TextChoices):
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        REQUEST_CHANGES = "request_changes", "Request changes"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    agent_decision = models.ForeignKey(
        AgentDecision, on_delete=models.PROTECT, db_column="agent_decision_id",
        related_name="human_approvals",
    )
    recommendation = models.ForeignKey(
        Recommendation, on_delete=models.PROTECT, db_column="recommendation_id",
        related_name="human_approvals", null=True, blank=True,
    )
    required_role = models.CharField(max_length=160)
    decision = models.CharField(max_length=24, choices=Decision.choices)
    decided_by = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="decided_by_id",
        related_name="human_approvals",
    )
    adminapps_user_id_snapshot = models.UUIDField()
    actor_type = models.CharField(max_length=24, default="human")
    comments = models.TextField(null=True, blank=True)
    decided_at = models.DateTimeField()
    trace_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."approval'


class ActionPlan(models.Model):
    """Exact, immutable description of a proposed action; it has no side effects."""

    class Impact(models.TextChoices):
        STANDARD = "standard", "Standard"
        HIGH = "high", "High"

    class Reversibility(models.TextChoices):
        REVERSIBLE = "reversible", "Reversible"
        IRREVERSIBLE = "irreversible", "Irreversible"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    agent_decision = models.ForeignKey(AgentDecision, on_delete=models.PROTECT, db_column="agent_decision_id")
    recommendation = models.ForeignKey(Recommendation, on_delete=models.PROTECT, db_column="recommendation_id")
    action_type = models.CharField(max_length=160)
    target_type = models.CharField(max_length=160)
    target_id = models.CharField(max_length=255)
    parameters = models.JSONField(default=dict)
    impact = models.CharField(max_length=24, choices=Impact.choices)
    reversibility = models.CharField(max_length=32, choices=Reversibility.choices)
    preconditions = models.JSONField(default=list)
    dry_run_supported = models.BooleanField(default=True)
    required_autonomy = models.PositiveSmallIntegerField()
    action_plan_hash = models.CharField(max_length=64)
    idempotency_key = models.CharField(max_length=200)
    trace_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."action_plan'


class ActionPlanDryRun(models.Model):
    """Immutable read-only simulation result bound to one exact plan hash."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    action_plan = models.ForeignKey(ActionPlan, on_delete=models.PROTECT, db_column="action_plan_id")
    action_plan_hash = models.CharField(max_length=64)
    expected_affected_objects = models.JSONField(default=list)
    intended_state_delta = models.JSONField(default=dict)
    validation_status = models.CharField(max_length=24)
    precondition_results = models.JSONField(default=list)
    impact_summary = models.JSONField(default=dict)
    trace_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."action_plan_dry_run'


class ExecutionAuthorization(models.Model):
    """Append-only permission artifact for one exact prepared action."""

    class Outcome(models.TextChoices):
        AUTHORIZED = "authorized", "Authorized"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    action_plan = models.ForeignKey(ActionPlan, on_delete=models.PROTECT, db_column="action_plan_id")
    action_plan_hash = models.CharField(max_length=64)
    dry_run = models.ForeignKey(ActionPlanDryRun, on_delete=models.PROTECT, db_column="dry_run_id")
    agent_decision = models.ForeignKey(AgentDecision, on_delete=models.PROTECT, db_column="agent_decision_id")
    recommendation = models.ForeignKey(Recommendation, on_delete=models.PROTECT, db_column="recommendation_id")
    effective_approval = models.ForeignKey(Approval, on_delete=models.PROTECT, db_column="effective_approval_id")
    agent_run = models.ForeignKey(AgentRun, on_delete=models.PROTECT, db_column="agent_run_id")
    agent_definition = models.ForeignKey(AgentDefinition, on_delete=models.PROTECT, db_column="agent_definition_id")
    model_policy = models.ForeignKey(ModelPolicy, on_delete=models.PROTECT, db_column="model_policy_id")
    effective_autonomy_ceiling = models.PositiveSmallIntegerField()
    impact = models.CharField(max_length=24, choices=ActionPlan.Impact.choices)
    reversibility = models.CharField(max_length=32, choices=ActionPlan.Reversibility.choices)
    outcome = models.CharField(max_length=24, choices=Outcome.choices)
    idempotency_key = models.CharField(max_length=200)
    authorization_request_hash = models.CharField(max_length=64)
    actor_type = models.CharField(max_length=40, default="governance_service")
    actor_id = models.CharField(max_length=255)
    trace_id = models.UUIDField()
    authorized_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'qms"."execution_authorization'


class ActionExecution(models.Model):
    """One immutable attempt to run an exact authorization through an allow-listed executor."""

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    class ExecutorType(models.TextChoices):
        SYNTHETIC_NOOP = "synthetic_noop", "Synthetic no-op"
        CONTROLLED_OPPORTUNITY = "controlled_opportunity", "Controlled Opportunity"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    execution_authorization = models.ForeignKey(
        ExecutionAuthorization, on_delete=models.PROTECT, db_column="execution_authorization_id",
        related_name="action_executions",
    )
    action_plan = models.ForeignKey(ActionPlan, on_delete=models.PROTECT, db_column="action_plan_id")
    action_plan_hash = models.CharField(max_length=64)
    executor_type = models.CharField(max_length=40, choices=ExecutorType.choices)
    status = models.CharField(max_length=24, choices=Status.choices)
    attempt_number = models.PositiveIntegerField(default=1)
    retry_of = models.ForeignKey(
        "self", on_delete=models.PROTECT, db_column="retry_of_execution_id",
        null=True, blank=True, related_name="retry_attempts",
    )
    precondition_results = models.JSONField(default=dict)
    idempotency_key = models.CharField(max_length=200)
    trace_id = models.UUIDField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."action_execution'


class ActionExecutionReceipt(models.Model):
    """Append-only synthetic terminal receipt for exactly one execution attempt."""

    class Outcome(models.TextChoices):
        SYNTHETIC_NOOP_SUCCEEDED = "synthetic_noop_succeeded", "Synthetic no-op succeeded"
        SYNTHETIC_NOOP_FAILED = "synthetic_noop_failed", "Synthetic no-op failed"
        OPPORTUNITY_DEFERRED = "opportunity_deferred", "Opportunity deferred"
        OPPORTUNITY_EVALUATION_RESUMED = (
            "opportunity_evaluation_resumed", "Opportunity evaluation resumed"
        )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    action_execution = models.OneToOneField(
        ActionExecution, on_delete=models.PROTECT, db_column="action_execution_id",
        related_name="receipt",
    )
    executor_type = models.CharField(max_length=40, choices=ActionExecution.ExecutorType.choices)
    outcome = models.CharField(max_length=40, choices=Outcome.choices)
    result = models.JSONField(default=dict)
    result_hash = models.CharField(max_length=64)
    action_plan_hash = models.CharField(max_length=64)
    trace_id = models.UUIDField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."action_execution_receipt'


class EffectivenessCheck(models.Model):
    """Immutable, human-attested assessment of one exact controlled execution."""

    class Outcome(models.TextChoices):
        EFFECTIVE = "effective", "Effective"
        INEFFECTIVE = "ineffective", "Ineffective"
        INCONCLUSIVE = "inconclusive", "Inconclusive"
        UNKNOWN = "unknown", "Unknown"

    class AssessmentMethod(models.TextChoices):
        HUMAN_REVIEW = "human_review", "Human review"
        SYSTEM_ASSISTED = "system_assisted", "System assisted"
        MEASUREMENT_DERIVED = "measurement_derived", "Measurement derived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    action_execution = models.ForeignKey(ActionExecution, on_delete=models.PROTECT, db_column="action_execution_id")
    receipt = models.ForeignKey(ActionExecutionReceipt, on_delete=models.PROTECT, db_column="receipt_id")
    action_plan = models.ForeignKey(ActionPlan, on_delete=models.PROTECT, db_column="action_plan_id")
    execution_authorization = models.ForeignKey(ExecutionAuthorization, on_delete=models.PROTECT, db_column="execution_authorization_id")
    agent_decision = models.ForeignKey(AgentDecision, on_delete=models.PROTECT, db_column="agent_decision_id")
    recommendation = models.ForeignKey(Recommendation, on_delete=models.PROTECT, db_column="recommendation_id")
    opportunity_lineage_id = models.UUIDField()
    before_opportunity_revision = models.ForeignKey(
        Opportunity, on_delete=models.PROTECT, db_column="before_opportunity_revision_id",
        related_name="effectiveness_checks_as_before",
    )
    resulting_opportunity_revision = models.ForeignKey(
        Opportunity, on_delete=models.PROTECT, db_column="resulting_opportunity_revision_id",
        related_name="effectiveness_checks_as_result",
    )
    outcome = models.CharField(max_length=24, choices=Outcome.choices)
    assessment_method = models.CharField(max_length=32, choices=AssessmentMethod.choices)
    criteria_hash = models.CharField(max_length=64)
    planning_context_hash = models.CharField(max_length=64)
    reason_code = models.CharField(max_length=80, null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)
    due_at = models.DateTimeField()
    assessed_at = models.DateTimeField()
    measurement_definition = models.ForeignKey(
        MeasurementDefinition, on_delete=models.PROTECT,
        db_column="measurement_definition_id", null=True, blank=True,
    )
    predecessor = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="predecessor_id",
        related_name="successor", null=True, blank=True,
    )
    revision = models.PositiveIntegerField()
    correction_reason = models.TextField(null=True, blank=True)
    actor_user_projection = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="actor_user_projection_id",
        related_name="effectiveness_attestations",
    )
    actor_external_id_snapshot = models.UUIDField()
    actor_type = models.CharField(max_length=24, default="human")
    authority_context_version = models.CharField(max_length=120)
    authority_decision_reference = models.CharField(max_length=255)
    policy_id = models.CharField(max_length=120, default="effectiveness-check-policy/v1")
    trace_id = models.UUIDField()
    correlation_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."effectiveness_check'


class EffectivenessEvidence(models.Model):
    """Exact immutable Evidence revision used by one EffectivenessCheck."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    effectiveness_check = models.ForeignKey(
        EffectivenessCheck, on_delete=models.PROTECT, db_column="effectiveness_check_id",
        related_name="evidence_links",
    )
    evidence = models.ForeignKey(Evidence, on_delete=models.PROTECT, db_column="evidence_id")
    evidence_lineage_id_snapshot = models.UUIDField()
    evidence_revision_snapshot = models.PositiveIntegerField()
    evidence_content_hash_snapshot = models.CharField(max_length=64)
    criterion_role = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."effectiveness_evidence'
        constraints = [
            models.UniqueConstraint(
                fields=("effectiveness_check", "evidence"),
                name="qms_effectiveness_evidence_check_revision_unique",
            )
        ]


class LearningSignal(models.Model):
    """Immutable categorical signal with a creation-time Effectiveness derivation snapshot."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    selected_effectiveness_check = models.ForeignKey(
        EffectivenessCheck, on_delete=models.PROTECT, db_column="selected_effectiveness_check_id",
        related_name="derived_learning_signals",
    )
    effectiveness_lineage_id = models.UUIDField()
    selected_revision = models.PositiveIntegerField()
    selected_predecessor_id_snapshot = models.UUIDField(null=True, blank=True)
    selected_outcome_snapshot = models.CharField(max_length=24, choices=EffectivenessCheck.Outcome.choices)
    selected_was_current_leaf = models.BooleanField(default=True)
    derivation_timestamp = models.DateTimeField()
    derivation_policy_id = models.CharField(max_length=120)
    derivation_policy_version = models.CharField(max_length=40)
    provenance_hash = models.CharField(max_length=64)
    actor_user_projection = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="actor_user_projection_id",
        related_name="learning_signals_created",
    )
    actor_external_id_snapshot = models.UUIDField()
    authority_context_version = models.CharField(max_length=120)
    authority_decision_reference = models.CharField(max_length=255)
    trace_id = models.UUIDField()
    correlation_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."learning_signal'


class LearningSignalEffectiveness(models.Model):
    """Frozen member of the full Effectiveness lineage selected for a signal."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    learning_signal = models.ForeignKey(
        LearningSignal, on_delete=models.PROTECT, db_column="learning_signal_id",
        related_name="effectiveness_snapshot",
    )
    effectiveness_check = models.ForeignKey(
        EffectivenessCheck, on_delete=models.PROTECT, db_column="effectiveness_check_id",
    )
    lineage_id_snapshot = models.UUIDField()
    revision_snapshot = models.PositiveIntegerField()
    predecessor_id_snapshot = models.UUIDField(null=True, blank=True)
    outcome_snapshot = models.CharField(max_length=24, choices=EffectivenessCheck.Outcome.choices)
    check_created_at_snapshot = models.DateTimeField()
    is_selected_leaf = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."learning_signal_effectiveness'


class LearningProposal(models.Model):
    """Immutable governance-pending proposal; it has no target-application semantics."""

    class Status(models.TextChoices):
        GOVERNANCE_PENDING = "governance_pending", "Governance pending"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    target_type = models.CharField(max_length=80)
    target_scope = models.CharField(max_length=16, default="global")
    target_id = models.UUIDField()
    target_lineage_id = models.UUIDField()
    target_version = models.CharField(max_length=120)
    target_snapshot = models.JSONField()
    target_hash = models.CharField(max_length=64)
    proposed_change_hash = models.CharField(max_length=64)
    canonical_delta = models.OneToOneField(
        "LearningProposalCanonicalDelta", on_delete=models.PROTECT,
        db_column="canonical_delta_id", related_name="bound_proposal",
        null=True, blank=True,
    )
    canonicalization_version = models.CharField(max_length=80, null=True, blank=True)
    delta_schema_version = models.CharField(max_length=120, null=True, blank=True)
    operation_id = models.CharField(max_length=160, null=True, blank=True)
    operation_version = models.CharField(max_length=40, null=True, blank=True)
    delta_hash = models.CharField(max_length=64, null=True, blank=True)
    rationale = models.TextField()
    expected_effect = models.TextField()
    risks = models.JSONField(default=list)
    required_governance_domains = models.JSONField(default=list)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.GOVERNANCE_PENDING)
    predecessor = models.OneToOneField(
        "self", on_delete=models.PROTECT, db_column="predecessor_id",
        related_name="successor", null=True, blank=True,
    )
    revision = models.PositiveIntegerField()
    correction_reason = models.TextField(null=True, blank=True)
    actor_user_projection = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="actor_user_projection_id",
        related_name="learning_proposals_created",
    )
    actor_external_id_snapshot = models.UUIDField()
    authority_context_version = models.CharField(max_length=120)
    authority_decision_reference = models.CharField(max_length=255)
    policy_id = models.CharField(max_length=120)
    trace_id = models.UUIDField()
    correlation_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."learning_proposal'


class LearningProposalCanonicalDelta(models.Model):
    """Immutable proposal-owned canonical bytes; inert contract material only."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    learning_proposal = models.OneToOneField(
        LearningProposal, on_delete=models.PROTECT, db_column="learning_proposal_id",
        related_name="owned_canonical_delta",
    )
    canonicalization_version = models.CharField(max_length=80)
    delta_schema_version = models.CharField(max_length=120)
    operation_id = models.CharField(max_length=160)
    operation_version = models.CharField(max_length=40)
    target_type = models.CharField(max_length=80)
    target_id = models.UUIDField()
    target_lineage_id = models.UUIDField()
    target_version = models.CharField(max_length=120)
    target_hash = models.CharField(max_length=64)
    delta_document = models.JSONField()
    canonical_bytes = models.BinaryField()
    delta_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."learning_proposal_canonical_delta'


class LearningProposalSignal(models.Model):
    """Exact immutable supporting signal and final-sample identity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    learning_proposal = models.ForeignKey(
        LearningProposal, on_delete=models.PROTECT, db_column="learning_proposal_id",
        related_name="signal_links",
    )
    learning_signal = models.ForeignKey(
        LearningSignal, on_delete=models.PROTECT, db_column="learning_signal_id",
    )
    effectiveness_lineage_id_snapshot = models.UUIDField()
    signal_provenance_hash_snapshot = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."learning_proposal_signal'


class LearningProposalReview(models.Model):
    """Immutable governance evidence for one exact LearningProposal revision."""

    class TargetStatus(models.TextChoices):
        VALID = "valid", "Valid"
        STALE = "stale", "Stale"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    learning_proposal = models.ForeignKey(
        LearningProposal, on_delete=models.PROTECT, db_column="learning_proposal_id",
        related_name="governance_reviews",
    )
    proposal_revision_snapshot = models.PositiveIntegerField()
    proposal_predecessor_id_snapshot = models.UUIDField(null=True, blank=True)
    proposal_material_hash = models.CharField(max_length=64)
    canonical_delta_id = models.UUIDField(null=True, blank=True)
    canonicalization_version = models.CharField(max_length=80, null=True, blank=True)
    delta_schema_version = models.CharField(max_length=120, null=True, blank=True)
    operation_id = models.CharField(max_length=160, null=True, blank=True)
    operation_version = models.CharField(max_length=40, null=True, blank=True)
    delta_hash = models.CharField(max_length=64, null=True, blank=True)
    target_type = models.CharField(max_length=80)
    target_id = models.UUIDField()
    target_lineage_id = models.UUIDField()
    target_version = models.CharField(max_length=120)
    target_hash = models.CharField(max_length=64)
    target_status_snapshot = models.CharField(max_length=16, choices=TargetStatus.choices)
    review_outcome = models.CharField(max_length=32, default="review_recorded")
    findings = models.JSONField()
    reviewed_governance_domains = models.JSONField(default=list)
    reviewer_user_projection = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="reviewer_user_projection_id",
        related_name="learning_proposal_reviews",
    )
    reviewer_external_id_snapshot = models.UUIDField()
    authority_context_version = models.CharField(max_length=120)
    authority_decision_reference = models.CharField(max_length=255)
    governance_scope = models.CharField(max_length=16, default="global")
    policy_id = models.CharField(max_length=160)
    trace_id = models.UUIDField()
    correlation_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."learning_proposal_review'


class LearningProposalDecision(models.Model):
    """One immutable governed outcome for one exact proposal revision."""

    class Outcome(models.TextChoices):
        APPROVED_FOR_APPLICATION = "approved_for_application", "Approved for application"
        REJECTED = "rejected", "Rejected"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    learning_proposal = models.OneToOneField(
        LearningProposal, on_delete=models.PROTECT, db_column="learning_proposal_id",
        related_name="governance_decision",
    )
    proposal_revision_snapshot = models.PositiveIntegerField()
    proposal_predecessor_id_snapshot = models.UUIDField(null=True, blank=True)
    proposal_material_hash = models.CharField(max_length=64)
    canonical_delta_id = models.UUIDField(null=True, blank=True)
    canonicalization_version = models.CharField(max_length=80, null=True, blank=True)
    delta_schema_version = models.CharField(max_length=120, null=True, blank=True)
    operation_id = models.CharField(max_length=160, null=True, blank=True)
    operation_version = models.CharField(max_length=40, null=True, blank=True)
    delta_hash = models.CharField(max_length=64, null=True, blank=True)
    review_ids_snapshot = models.JSONField(default=list)
    review_set_hash = models.CharField(max_length=64)
    target_type = models.CharField(max_length=80)
    target_id = models.UUIDField()
    target_lineage_id = models.UUIDField()
    target_version = models.CharField(max_length=120)
    target_hash = models.CharField(max_length=64)
    outcome = models.CharField(max_length=32, choices=Outcome.choices)
    rationale = models.TextField()
    decision_identity_hash = models.CharField(max_length=64, unique=True)
    approver_user_projection = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="approver_user_projection_id",
        related_name="learning_proposal_decisions",
    )
    approver_external_id_snapshot = models.UUIDField()
    authority_context_version = models.CharField(max_length=120)
    authority_decision_reference = models.CharField(max_length=255)
    governance_scope = models.CharField(max_length=16, default="global")
    policy_id = models.CharField(max_length=160)
    trace_id = models.UUIDField()
    correlation_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."learning_proposal_decision'


class LearningApplicationAuthorization(models.Model):
    """Inert authorization record; it exposes no target application operation."""

    class Status(models.TextChoices):
        AUTHORIZED = "authorized", "Authorized"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(TenantProjection, on_delete=models.PROTECT, db_column="tenant_id")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, db_column="organization_id")
    learning_proposal = models.ForeignKey(
        LearningProposal, on_delete=models.PROTECT, db_column="learning_proposal_id",
        related_name="application_authorizations",
    )
    learning_proposal_decision = models.OneToOneField(
        LearningProposalDecision, on_delete=models.PROTECT,
        db_column="learning_proposal_decision_id", related_name="application_authorization",
    )
    proposal_revision_snapshot = models.PositiveIntegerField()
    proposal_material_hash = models.CharField(max_length=64)
    canonical_delta_id = models.UUIDField(null=True, blank=True)
    canonicalization_version = models.CharField(max_length=80, null=True, blank=True)
    delta_schema_version = models.CharField(max_length=120, null=True, blank=True)
    operation_id = models.CharField(max_length=160, null=True, blank=True)
    operation_version = models.CharField(max_length=40, null=True, blank=True)
    delta_hash = models.CharField(max_length=64, null=True, blank=True)
    target_type = models.CharField(max_length=80)
    target_id = models.UUIDField()
    target_lineage_id = models.UUIDField()
    target_version = models.CharField(max_length=120)
    target_hash = models.CharField(max_length=64)
    capability_id = models.CharField(max_length=160)
    capability_version = models.CharField(max_length=40, default="v1")
    authorization_status = models.CharField(max_length=24, choices=Status.choices, default=Status.AUTHORIZED)
    idempotency_key = models.CharField(max_length=255)
    idempotency_hash = models.CharField(max_length=64)
    authorizer_user_projection = models.ForeignKey(
        "UserProjection", on_delete=models.PROTECT, db_column="authorizer_user_projection_id",
        related_name="learning_application_authorizations",
    )
    authorizer_external_id_snapshot = models.UUIDField()
    authority_context_version = models.CharField(max_length=120)
    authority_decision_reference = models.CharField(max_length=255)
    governance_scope = models.CharField(max_length=16, default="global")
    policy_id = models.CharField(max_length=160)
    trace_id = models.UUIDField()
    correlation_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'qms"."learning_application_authorization'


class UserProjection(models.Model):
    """Tenant-scoped identity mapping from AdminApps, never an auth authority."""

    class LifecycleStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        REVOKED = "revoked", "Revoked"
        DELETED_TOMBSTONE = "deleted_tombstone", "Deleted tombstone"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    adminapps_user_id = models.UUIDField(unique=True, editable=False)
    tenant = models.ForeignKey(
        TenantProjection,
        on_delete=models.PROTECT,
        related_name="user_projections",
        db_column="tenant_id",
    )
    source_version = models.BigIntegerField()
    source_event_id = models.UUIDField(unique=True)
    lifecycle_status = models.CharField(
        max_length=32,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.ACTIVE,
    )
    last_synced_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'qms"."user_projection'


class DomainEvent(models.Model):
    """Tenant-scoped, append-only fact recorded by an internal command."""

    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        TenantProjection, on_delete=models.PROTECT, db_column="tenant_id"
    )
    event_type = models.CharField(max_length=160)
    schema_version = models.PositiveIntegerField()
    aggregate_type = models.CharField(max_length=120)
    aggregate_id = models.UUIDField()
    aggregate_version = models.PositiveBigIntegerField()
    occurred_at = models.DateTimeField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    trace_id = models.UUIDField()
    correlation_id = models.UUIDField(null=True, blank=True)
    causation_id = models.UUIDField(null=True, blank=True)
    source = models.CharField(max_length=120)
    payload = models.JSONField()
    payload_hash = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'eventing"."domain_event'


class TransactionalOutbox(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        TenantProjection, on_delete=models.PROTECT, db_column="tenant_id"
    )
    domain_event = models.OneToOneField(
        DomainEvent, on_delete=models.PROTECT, db_column="domain_event_id"
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    publish_attempts = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField()
    lease_owner = models.CharField(max_length=160, null=True, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'eventing"."transactional_outbox'


class ConsumerReceipt(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        TenantProjection, on_delete=models.PROTECT, db_column="tenant_id"
    )
    consumer_name = models.CharField(max_length=160)
    event_id = models.UUIDField()
    payload_hash = models.CharField(max_length=64)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices)
    attempts = models.PositiveIntegerField(default=0)
    last_error_code = models.CharField(max_length=64, null=True, blank=True)
    trace_id = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'eventing"."consumer_receipt'
        constraints = [
            models.UniqueConstraint(
                fields=("consumer_name", "event_id"),
                name="foundation_consumer_receipt_consumer_event_unique",
            )
        ]


class ImmutableAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        TenantProjection, on_delete=models.PROTECT, db_column="tenant_id"
    )
    stream_type = models.CharField(max_length=120)
    stream_id = models.UUIDField()
    sequence_number = models.PositiveBigIntegerField()
    actor_type = models.CharField(max_length=80)
    actor_id = models.CharField(max_length=255, null=True, blank=True)
    action = models.CharField(max_length=160)
    entity_type = models.CharField(max_length=120)
    entity_id = models.UUIDField()
    trace_id = models.UUIDField()
    occurred_at = models.DateTimeField()
    before_hash = models.CharField(max_length=64, null=True, blank=True)
    after_hash = models.CharField(max_length=64, null=True, blank=True)
    payload_hash = models.CharField(max_length=64, null=True, blank=True)
    previous_entry_hash = models.CharField(max_length=64, null=True, blank=True)
    entry_hash = models.CharField(max_length=64)
    metadata_canonical = models.TextField(default="{}")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'audit"."immutable_audit_log'
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "stream_type", "stream_id", "sequence_number"),
                name="foundation_audit_stream_sequence_unique",
            )
        ]
