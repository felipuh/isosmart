"""Source-backed onboarding step catalog and persisted-state projection."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from .models import (
    DomainEvent,
    Evidence,
    LearningPath,
    Organization,
    OnboardingTransition,
    OnboardingWorkflow,
    QuizAttempt,
    TenantProjection,
    UserProjection,
)
from .canonical import canonical_hash
from .document_evidence import DocumentEvidenceCommandService
from .tenant_context import bind_trusted_tenant_context_in_transaction, trusted_tenant_context


@dataclass(frozen=True)
class OnboardingStep:
    number: int
    key: str
    title: str
    prerequisite_keys: tuple[str, ...]


ONBOARDING_STEPS = (
    OnboardingStep(1, "plan_selection", "Plan Selection", ()),
    OnboardingStep(2, "account_registration", "Account Registration", ("plan_selection",)),
    OnboardingStep(3, "billing_contact", "Billing Contact", ("account_registration",)),
    OnboardingStep(4, "payment", "Payment", ("billing_contact",)),
    OnboardingStep(5, "payment_verification", "Payment Verification", ("payment",)),
    OnboardingStep(6, "subscription_activation", "Subscription Activation", ("payment_verification",)),
    OnboardingStep(7, "tenant_provisioning", "Tenant Provisioning", ("subscription_activation",)),
    OnboardingStep(8, "security_setup", "Security Setup", ("tenant_provisioning",)),
    OnboardingStep(9, "foundation_gate", "ISO 9000:2026 Foundation Gate", ("security_setup",)),
    OnboardingStep(10, "organizational_profile", "Organizational Profile", ("foundation_gate",)),
    OnboardingStep(11, "value_discovery", "Value Discovery", ("organizational_profile",)),
    OnboardingStep(12, "document_data_ingestion", "Document/Data Ingestion", ("value_discovery",)),
    OnboardingStep(13, "context_twin_baseline", "Context Twin Baseline", ("document_data_ingestion",)),
    OnboardingStep(14, "quality_baseline", "Quality Baseline", ("context_twin_baseline",)),
    OnboardingStep(15, "human_validation", "Human Validation", ("quality_baseline",)),
    OnboardingStep(16, "agents_activation", "Agents Activation", ("human_validation",)),
    OnboardingStep(17, "first_day_value", "First-Day Value", ("agents_activation",)),
)


def _status(*, complete, available, in_progress=False):
    if complete:
        return "COMPLETE"
    if in_progress:
        return "IN_PROGRESS"
    return "AVAILABLE" if available else "LOCKED"


class OnboardingWorkflowError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class OnboardingWorkflowService:
    """Persist and advance one tenant/user onboarding journey."""

    def __init__(self, *, using="app"):
        self.using = using

    @contextmanager
    def _tenant_boundary(self, *, identity, actor_id, trace_id):
        connection = transaction.get_connection(self.using)
        if connection.in_atomic_block:
            bind_trusted_tenant_context_in_transaction(
                identity, actor_id=actor_id, trace_id=trace_id, using=self.using,
            )
            yield
            return
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using,
        ):
            yield

    def ensure(self, *, identity, user_id, actor_id, trace_id):
        with self._tenant_boundary(identity=identity, actor_id=actor_id, trace_id=trace_id):
            workflow, _ = OnboardingWorkflow.objects.using(self.using).get_or_create(
                tenant_id=identity.tenant_id,
                user_id=user_id,
                defaults={"current_step": ONBOARDING_STEPS[0].key},
            )
            return workflow

    def transition(
        self, *, identity, user_id, step_key, to_status, event_id, event_type,
        source_reference, actor_id, trace_id, state=None,
    ):
        step = next((item for item in ONBOARDING_STEPS if item.key == step_key), None)
        if step is None:
            raise OnboardingWorkflowError("UNKNOWN_STEP", f"unknown onboarding step: {step_key}")
        if to_status not in {"in_progress", "complete", "blocked"}:
            raise OnboardingWorkflowError("INVALID_STATUS", f"invalid onboarding status: {to_status}")
        if state is not None and (not isinstance(state, dict) or "status" in state):
            raise OnboardingWorkflowError("INVALID_STATE", "state must be an object without a status override")
        if not event_type or not source_reference:
            raise OnboardingWorkflowError("MISSING_PROVENANCE", "event type and source reference are required")
        with self._tenant_boundary(identity=identity, actor_id=actor_id, trace_id=trace_id):
            with transaction.atomic(using=self.using):
                workflow, _ = OnboardingWorkflow.objects.using(self.using).get_or_create(
                    tenant_id=identity.tenant_id,
                    user_id=user_id,
                    defaults={"current_step": ONBOARDING_STEPS[0].key},
                )
                workflow = OnboardingWorkflow.objects.using(self.using).select_for_update().get(id=workflow.id)
                existing = OnboardingTransition.objects.using(self.using).filter(event_id=event_id).first()
                if existing:
                    if (existing.tenant_id != identity.tenant_id or existing.workflow_id != workflow.id
                            or existing.step_key != step_key or existing.to_status != to_status
                            or existing.event_type != event_type or existing.source_reference != source_reference
                            or workflow.state.get(step_key) != {"status": to_status, **(state or {})}):
                        raise OnboardingWorkflowError("EVENT_CONFLICT", "event belongs to another onboarding transition")
                    return workflow, existing, True
                state_data = dict(workflow.state or {})
                current = state_data.get(step_key, {}).get("status")
                completed = set(workflow.completed_steps or [])
                if to_status == "complete":
                    missing = [key for key in step.prerequisite_keys if key not in completed]
                    if missing:
                        raise OnboardingWorkflowError("PREREQUISITES_INCOMPLETE", f"missing prerequisites: {missing}")
                if current == "complete" and to_status != "complete":
                    raise OnboardingWorkflowError("INVALID_TRANSITION", "completed step cannot regress")
                if current == "complete" and state_data[step_key] != {"status": to_status, **(state or {})}:
                    raise OnboardingWorkflowError("INVALID_TRANSITION", "completed step provenance cannot be replaced")
                if current == to_status and to_status != "complete":
                    raise OnboardingWorkflowError("DUPLICATE_TRANSITION", "step is already in that state")
                previous = current or "available"
                state_data[step_key] = {"status": to_status, **(state or {})}
                if to_status == "complete":
                    completed.add(step_key)
                next_step = workflow.current_step
                if to_status == "complete" and workflow.current_step == step_key:
                    index = step.number
                    next_step = ONBOARDING_STEPS[index].key if index < len(ONBOARDING_STEPS) else step_key
                workflow.current_step = next_step
                workflow.status = OnboardingWorkflow.Status.COMPLETE if len(completed) == len(ONBOARDING_STEPS) else OnboardingWorkflow.Status.IN_PROGRESS
                workflow.completed_steps = sorted(completed)
                workflow.state = state_data
                workflow.version += 1
                workflow.save(using=self.using, update_fields=("current_step", "status", "completed_steps", "state", "version", "updated_at"))
                transition = OnboardingTransition.objects.using(self.using).create(
                    tenant_id=identity.tenant_id,
                    workflow_id=workflow.id,
                    step_key=step_key,
                    from_status=previous,
                    to_status=to_status,
                    event_id=event_id,
                    event_type=event_type,
                    source_reference=source_reference,
                    provenance_hash=canonical_hash({"event_id": str(event_id), "step_key": step_key, "state": state_data}),
                    actor_id=str(actor_id),
                )
                return workflow, transition, False


class OrganizationProfileCommandService:
    """Persist the source-listed Organizational Profile into canonical onboarding state."""

    REQUIRED_FIELDS = frozenset({
        "role", "expertise_level", "size_range", "sites_count",
        "countries", "sector", "certification_status",
    })
    OPTIONAL_FIELDS = frozenset({"employees_count"})

    def __init__(self, *, using="app"):
        self.using = using

    @classmethod
    def validate_profile(cls, profile):
        if not isinstance(profile, dict):
            raise OnboardingWorkflowError("INVALID_PROFILE", "organizational profile must be an object")
        fields = set(profile)
        missing = cls.REQUIRED_FIELDS - fields
        unknown = fields - cls.REQUIRED_FIELDS - cls.OPTIONAL_FIELDS
        if missing:
            raise OnboardingWorkflowError(
                "MISSING_PROFILE_FIELDS", f"organizational profile is missing: {sorted(missing)}",
            )
        if unknown:
            raise OnboardingWorkflowError(
                "UNKNOWN_PROFILE_FIELDS", f"organizational profile has unsupported fields: {sorted(unknown)}",
            )
        for name in ("role", "expertise_level", "size_range", "sector", "certification_status"):
            value = profile[name]
            if not isinstance(value, str) or not value.strip():
                raise OnboardingWorkflowError("INVALID_PROFILE_FIELD", f"{name} must be a nonblank string")
        for name in ("sites_count", "employees_count"):
            if name in profile:
                value = profile[name]
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise OnboardingWorkflowError("INVALID_PROFILE_FIELD", f"{name} must be a nonnegative integer")
        countries = profile["countries"]
        if (not isinstance(countries, list) or not countries or
                any(not isinstance(country, str) or not country.strip() for country in countries)):
            raise OnboardingWorkflowError("INVALID_PROFILE_FIELD", "countries must be a nonempty string list")
        return {
            key: value.strip() if isinstance(value, str) else
            [country.strip() for country in value] if key == "countries" else value
            for key, value in profile.items()
        }

    def save_profile(
        self, *, identity, organization_id, user_id, profile, event_id, actor_id, trace_id,
    ):
        profile = self.validate_profile(profile)
        organization_id = str(organization_id)
        profile_hash = canonical_hash(profile)
        workflow_service = OnboardingWorkflowService(using=self.using)
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using,
        ):
            Organization.objects.using(self.using).get(
                id=organization_id, tenant_id=identity.tenant_id,
            )
            UserProjection.objects.using(self.using).get(
                id=user_id, tenant_id=identity.tenant_id,
            )
            return workflow_service.transition(
                identity=identity, user_id=user_id,
                step_key="organizational_profile", to_status="complete",
                event_id=event_id, event_type="onboarding.organizational_profile.saved",
                source_reference=f"onboarding-profile-sha256:{profile_hash}",
                actor_id=actor_id, trace_id=trace_id,
                state={
                    "organization_id": organization_id,
                    "profile": profile,
                    "profile_hash": profile_hash,
                },
            )


class OnboardingEvidenceIngestionService:
    """Atomically ingest metadata-only source references and complete onboarding step 12."""

    SOURCE_TYPES = frozenset({
        "strategy", "process", "kpi", "audit", "complaint", "supplier", "document",
    })
    ITEM_FIELDS = frozenset({
        "event_id", "source_type", "source_uri", "content_hash", "captured_at",
        "document_version_id",
    })

    def __init__(self, *, using="app"):
        self.using = using

    @classmethod
    def _validate_items(cls, items):
        if not isinstance(items, (list, tuple)) or not items:
            raise OnboardingWorkflowError("INVALID_INGESTION", "at least one source reference is required")
        validated = []
        event_ids = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict) or set(item) - cls.ITEM_FIELDS:
                raise OnboardingWorkflowError("INVALID_INGESTION", f"invalid source reference at index {index}")
            required = {"event_id", "source_type", "source_uri", "content_hash", "captured_at"}
            if required - set(item):
                raise OnboardingWorkflowError("INVALID_INGESTION", f"incomplete source reference at index {index}")
            if item["source_type"] not in cls.SOURCE_TYPES:
                raise OnboardingWorkflowError("INVALID_INGESTION", f"unsupported source type at index {index}")
            if not isinstance(item["source_uri"], str) or not item["source_uri"].strip():
                raise OnboardingWorkflowError("INVALID_INGESTION", f"source_uri is required at index {index}")
            if not isinstance(item["captured_at"], datetime) or timezone.is_naive(item["captured_at"]):
                raise OnboardingWorkflowError("INVALID_INGESTION", f"captured_at must be timezone-aware at index {index}")
            try:
                event_id = UUID(str(item["event_id"]))
            except (TypeError, ValueError, AttributeError) as exc:
                raise OnboardingWorkflowError("INVALID_INGESTION", f"event_id is invalid at index {index}") from exc
            if event_id in event_ids:
                raise OnboardingWorkflowError("INVALID_INGESTION", "source event IDs must be unique")
            event_ids.add(event_id)
            validated.append({**item, "event_id": event_id})
        return validated

    def ingest_batch(
        self, *, identity, organization_id, user_id, items, transition_event_id,
        actor_id, trace_id,
    ):
        validated = self._validate_items(items)
        transition_event_id = UUID(str(transition_event_id))
        batch_material = [{
            "event_id": str(item["event_id"]), "source_type": item["source_type"],
            "source_uri": item["source_uri"].strip(), "content_hash": item["content_hash"],
            "captured_at": item["captured_at"],
            "document_version_id": str(item["document_version_id"]) if item.get("document_version_id") else None,
        } for item in validated]
        batch_hash = canonical_hash(batch_material)
        evidence_ids = []
        workflow_service = OnboardingWorkflowService(using=self.using)
        evidence_service = DocumentEvidenceCommandService(using=self.using)

        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using,
        ):
            Organization.objects.using(self.using).get(
                id=organization_id, tenant_id=identity.tenant_id,
            )
            UserProjection.objects.using(self.using).get(
                id=user_id, tenant_id=identity.tenant_id,
            )
            workflow = OnboardingWorkflow.objects.using(self.using).filter(
                tenant_id=identity.tenant_id, user_id=user_id,
            ).first()
            completed_ingestion = (workflow.state or {}).get("document_data_ingestion", {}) if workflow else {}
            if completed_ingestion.get("status") == "complete":
                prior_transition = OnboardingTransition.objects.using(self.using).filter(
                    workflow_id=workflow.id, step_key="document_data_ingestion",
                    to_status="complete", event_type="onboarding.document_data_ingestion.completed",
                ).order_by("-created_at").first()
                if prior_transition is None or prior_transition.event_id != transition_event_id:
                    raise OnboardingWorkflowError(
                        "EVENT_CONFLICT", "completed ingestion replay requires the original transition event ID",
                    )
            for item in validated:
                existing_event = DomainEvent.objects.using(self.using).filter(
                    event_id=item["event_id"],
                ).first()
                if existing_event:
                    if (existing_event.tenant_id != identity.tenant_id or
                            existing_event.event_type != "evidence.created" or
                            existing_event.aggregate_type != "evidence"):
                        raise OnboardingWorkflowError("EVENT_CONFLICT", "event ID is bound to another event")
                    evidence_id = existing_event.payload.get("revision_id")
                    row = Evidence.objects.using(self.using).get(
                        id=evidence_id, tenant_id=identity.tenant_id,
                        organization_id=organization_id,
                    )
                    if (row.source_type != item["source_type"] or row.source_uri != item["source_uri"].strip()
                            or row.content_hash != item["content_hash"]
                            or row.captured_at != item["captured_at"]
                            or str(row.document_version_id) != str(item.get("document_version_id"))):
                        raise OnboardingWorkflowError("EVENT_CONFLICT", "replayed evidence payload changed")
                    evidence_ids.append(str(row.id))
                    continue

                result = evidence_service.create_evidence_in_current_transaction(
                    identity=identity, organization_id=organization_id,
                    source_type=item["source_type"], source_uri=item["source_uri"].strip(),
                    content_hash=item["content_hash"], captured_at=item["captured_at"],
                    document_version_id=item.get("document_version_id"),
                    event_id=item["event_id"], actor_id=actor_id, trace_id=trace_id,
                    change_reason="onboarding_document_data_ingestion",
                )
                evidence_ids.append(str(result.entity_id))

            return workflow_service.transition(
                identity=identity, user_id=user_id,
                step_key="document_data_ingestion", to_status="complete",
                event_id=transition_event_id,
                event_type="onboarding.document_data_ingestion.completed",
                source_reference=f"onboarding-evidence-batch-sha256:{batch_hash}",
                actor_id=actor_id, trace_id=trace_id,
                state={
                    "organization_id": str(organization_id),
                    "evidence_ids": evidence_ids,
                    "source_types": sorted({item["source_type"] for item in validated}),
                    "batch_hash": batch_hash,
                    "content_bytes_read": False,
                },
            )


def onboarding_steps(principal, *, using="app"):
    """Project the canonical steps from current domain state, never constants."""
    tenant_id = principal.tenant_id
    user_id = principal.user_projection_id
    paths = LearningPath.objects.using(using).filter(
        active=True,
        standard_edition__status="published",
        standard_edition__standard__code__icontains="9000",
        standard_edition__edition__icontains="2026",
    )
    attempts = QuizAttempt.objects.using(using).filter(
        tenant_id=tenant_id, user_id=user_id, passed=True, learning_path__in=paths,
    )
    foundation_complete = attempts.exists()
    tenant_ready = TenantProjection.objects.using(using).filter(
        id=tenant_id,
        lifecycle_status=TenantProjection.LifecycleStatus.ACTIVE,
        provisioning_status=TenantProjection.ProvisioningStatus.COMPLETE,
        reconciliation_status=TenantProjection.ReconciliationStatus.IN_SYNC,
    ).exists()

    completed = {
        "tenant_provisioning": tenant_ready,
        "foundation_gate": foundation_complete,
        # A domain object is not proof of a completed onboarding workflow.
        # Steps 10-17 require their explicit persisted transition/provenance.
    }
    # Steps owned by the external control plane remain locked until its
    # authoritative projection is available; the first step is actionable.
    completed_keys = {key for key, value in completed.items() if value}
    workflow = OnboardingWorkflow.objects.using(using).filter(
        tenant_id=tenant_id, user_id=user_id,
    ).first()
    persisted_state = (workflow.state or {}) if workflow else {}
    completed_keys.update(workflow.completed_steps or [] if workflow else [])
    rows = []
    for step in ONBOARDING_STEPS:
        prerequisites_met = all(key in completed_keys for key in step.prerequisite_keys)
        rows.append({
            "number": step.number,
            "key": step.key,
            "title": step.title,
            "status": str(persisted_state.get(step.key, {}).get("status", _status(
                complete=step.key in completed_keys,
                available=not step.prerequisite_keys and step.number == 1 or prerequisites_met,
                in_progress=False,
            ))).upper(),
            "prerequisites": list(step.prerequisite_keys),
        })
    return rows
