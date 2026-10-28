"""Policy-v1 governed EffectivenessCheck command; database-only and append-only."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from uuid import UUID, uuid4

from django.db import connections, transaction
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash
from .models import (
    ActionExecution,
    DomainEvent,
    EffectivenessCheck,
    EffectivenessEvidence,
    TransactionalOutbox,
)
from .tenant_context import TrustedTenantIdentity, bind_trusted_tenant_context_in_transaction


POLICY_ID = "effectiveness-check-policy/v1"
RECORD_PERMISSION = "qms.effectiveness_check.record"
SUPERSEDE_PERMISSION = "qms.effectiveness_check.supersede"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EffectivenessFailurePoint(str, Enum):
    BEFORE_CHECK = "before_check"
    AFTER_CHECK = "after_check"
    DURING_FIRST_EVIDENCE = "during_first_evidence"
    DURING_LATER_EVIDENCE = "during_later_evidence"
    AFTER_EVIDENCE = "after_evidence"
    AFTER_EVENT = "after_event"
    AFTER_OUTBOX = "after_outbox"
    AFTER_AUDIT = "after_audit"
    BEFORE_COMMIT = "before_commit"


@dataclass(frozen=True)
class TrustedEffectivenessAuthority:
    """Resolved server-side AdminApps authority; request fields are not accepted."""

    identity: TrustedTenantIdentity
    organization_id: UUID
    actor_user_projection_id: UUID
    actor_external_id: UUID
    permissions: frozenset[str]
    mfa_verified: bool
    access_active: bool
    authority_context_version: str
    authority_decision_reference: str


@dataclass(frozen=True)
class GovernedEffectivenessPlan:
    """Frozen governed planning context bound to an exact execution and target."""

    action_execution_id: UUID
    organization_id: UUID
    opportunity_lineage_id: UUID
    due_at: datetime
    criteria_hash: str
    planning_context_hash: str
    assessment_method: str
    measurement_definition_id: UUID | None = None
    policy_id: str = POLICY_ID


@dataclass(frozen=True)
class ExactEvidenceReference:
    evidence_id: UUID
    lineage_id: UUID
    revision: int
    content_hash: str
    criterion_role: str


@dataclass(frozen=True)
class EffectivenessRecordResult:
    effectiveness_check_id: UUID
    revision: int
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID
    trace_id: UUID


class EffectivenessReviewCategory(str, Enum):
    DUE = "due"
    OVERDUE = "overdue"
    UNKNOWN = "unknown"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class EffectivenessReviewItem:
    """Sanitized attention item; it is never an authorization decision."""

    category: str
    action_execution_id: UUID
    organization_id: UUID
    due_at: datetime
    current_check_id: UUID | None
    current_revision: int | None
    correction_count: int
    actor_external_id: UUID | None
    trace_id: UUID | None


class EffectivenessReviewQueueService:
    """Tenant-safe read model over trusted plans and immutable current leaves."""

    def __init__(self, *, using="app"):
        self.using = using

    def requiring_attention(self, *, identity, organization_id, plans, as_of):
        if not isinstance(identity, TrustedTenantIdentity):
            raise TypeError("identity must be server-authorized")
        if timezone.is_naive(as_of):
            raise ValueError("as_of must be timezone-aware")
        plans = tuple(plans)
        for plan in plans:
            self._validate_queue_plan(plan, organization_id)
        execution_ids = [plan.action_execution_id for plan in plans]
        with transaction.atomic(using=self.using):
            bind_trusted_tenant_context_in_transaction(
                identity, actor_id="effectiveness-review-queue", trace_id=uuid4(),
                using=self.using,
            )
            leaves = {
                row.action_execution_id: row
                for row in EffectivenessCheck.objects.using(self.using)
                .filter(organization_id=organization_id, action_execution_id__in=execution_ids,
                        successor__isnull=True)
            }
            items = []
            for plan in plans:
                leaf = leaves.get(plan.action_execution_id)
                category = None
                if leaf is None and as_of >= plan.due_at:
                    category = (EffectivenessReviewCategory.OVERDUE.value
                                if as_of > plan.due_at else EffectivenessReviewCategory.DUE.value)
                elif leaf is not None and leaf.outcome in {
                    EffectivenessCheck.Outcome.UNKNOWN,
                    EffectivenessCheck.Outcome.INCONCLUSIVE,
                }:
                    category = leaf.outcome
                if category:
                    items.append(EffectivenessReviewItem(
                        category=category, action_execution_id=plan.action_execution_id,
                        organization_id=organization_id, due_at=plan.due_at,
                        current_check_id=leaf.id if leaf else None,
                        current_revision=leaf.revision if leaf else None,
                        correction_count=(leaf.revision - 1) if leaf else 0,
                        actor_external_id=leaf.actor_external_id_snapshot if leaf else None,
                        trace_id=leaf.trace_id if leaf else None,
                    ))
            return tuple(sorted(items, key=lambda item: (item.due_at, str(item.action_execution_id))))

    @staticmethod
    def _validate_queue_plan(plan, organization_id):
        EffectivenessCheckCommandService._validate_plan(plan)
        if plan.organization_id != organization_id:
            raise PermissionError("governed plan and server-authorized Organization mismatch")


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _hash(value, name):
    value = _required(value, name).lower()
    if not SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
    return value


class EffectivenessCheckCommandService:
    """Records an initial check or correction as one atomic governed unit."""

    def __init__(self, *, using="app"):
        self.using = using

    @staticmethod
    def _validate_authority(authority, *, correction):
        if not isinstance(authority, TrustedEffectivenessAuthority):
            raise TypeError("authority must be trusted server-resolved Effectiveness authority")
        if not isinstance(authority.identity, TrustedTenantIdentity):
            raise TypeError("authority identity must be a TrustedTenantIdentity")
        required = {RECORD_PERMISSION}
        if correction:
            required.add(SUPERSEDE_PERMISSION)
        if not authority.mfa_verified or not authority.access_active or not required.issubset(authority.permissions):
            raise PermissionError("active AdminApps reviewer authority, MFA and exact permissions are required")
        _required(authority.authority_context_version, "authority_context_version")
        _required(authority.authority_decision_reference, "authority_decision_reference")

    @staticmethod
    def _validate_plan(plan):
        if not isinstance(plan, GovernedEffectivenessPlan):
            raise TypeError("plan must be a trusted GovernedEffectivenessPlan")
        if plan.policy_id != POLICY_ID:
            raise ValueError("only effectiveness-check-policy/v1 is supported")
        if timezone.is_naive(plan.due_at):
            raise ValueError("due_at must be timezone-aware")
        _hash(plan.criteria_hash, "criteria_hash")
        _hash(plan.planning_context_hash, "planning_context_hash")
        if plan.assessment_method not in EffectivenessCheck.AssessmentMethod.values:
            raise ValueError("invalid assessment_method")
        needs_measurement = plan.assessment_method == EffectivenessCheck.AssessmentMethod.MEASUREMENT_DERIVED
        if needs_measurement != (plan.measurement_definition_id is not None):
            raise ValueError("MeasurementDefinition linkage must match frozen assessment semantics")

    @staticmethod
    def _validate_evidence(references):
        references = tuple(references)
        if not references:
            raise ValueError("at least one exact Evidence revision is required")
        seen = set()
        for reference in references:
            if not isinstance(reference, ExactEvidenceReference):
                raise TypeError("evidence references must be ExactEvidenceReference values")
            if reference.evidence_id in seen:
                raise ValueError("duplicate exact Evidence revision")
            seen.add(reference.evidence_id)
            if reference.revision < 1:
                raise ValueError("Evidence revision must be positive")
            _hash(reference.content_hash, "evidence content hash")
            _required(reference.criterion_role, "criterion_role")
        return references

    @staticmethod
    def _inject(failure_point, expected):
        if failure_point == expected:
            raise RuntimeError(f"deliberate Phase 19 rollback at {expected.value}")

    def record_effectiveness_check(
        self, *, authority, plan, outcome, evidence, trace_id,
        predecessor_id=None, correction_reason=None, reason_code=None,
        explanation=None, correlation_id=None, assessed_at=None,
        failure_point=None,
    ):
        predecessor_id = UUID(str(predecessor_id)) if predecessor_id else None
        self._validate_authority(authority, correction=predecessor_id is not None)
        self._validate_plan(plan)
        references = self._validate_evidence(evidence)
        if authority.organization_id != plan.organization_id:
            raise PermissionError("authority and governed plan Organization mismatch")
        if outcome not in EffectivenessCheck.Outcome.values:
            raise ValueError("invalid EffectivenessCheck outcome")
        assessed_at = assessed_at or timezone.now()
        if timezone.is_naive(assessed_at):
            raise ValueError("assessed_at must be timezone-aware")
        if assessed_at < plan.due_at:
            raise ValueError("a v1 EffectivenessCheck cannot be recorded before due_at")
        uncertain = outcome in (EffectivenessCheck.Outcome.INCONCLUSIVE, EffectivenessCheck.Outcome.UNKNOWN)
        if uncertain and (not _required(reason_code, "reason_code") or not _required(explanation, "explanation")):
            raise ValueError("uncertain outcome reason and explanation are required")
        if not uncertain and (reason_code or explanation):
            raise ValueError("reason_code/explanation are reserved for inconclusive or unknown")
        if predecessor_id and not _required(correction_reason, "correction_reason"):
            raise ValueError("correction_reason is required for supersession")
        if not predecessor_id and correction_reason:
            raise ValueError("correction_reason requires a predecessor")

        trace_id = UUID(str(trace_id))
        correlation_id = UUID(str(correlation_id)) if correlation_id else None
        check_id, event_id, outbox_id = uuid4(), uuid4(), uuid4()
        occurred_at = assessed_at

        with transaction.atomic(using=self.using, savepoint=False):
            bind_trusted_tenant_context_in_transaction(
                authority.identity, actor_id=authority.actor_external_id,
                trace_id=trace_id, using=self.using,
            )
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('app.organization_id',%s,true),"
                    "set_config('app.effectiveness_permissions',%s,true),"
                    "set_config('app.mfa_verified','true',true),"
                    "set_config('app.access_active','true',true),"
                    "set_config('app.authority_context_version',%s,true),"
                    "set_config('app.authority_decision_reference',%s,true)",
                    [str(authority.organization_id), ",".join(sorted(authority.permissions)),
                     authority.authority_context_version, authority.authority_decision_reference],
                )
            self._inject(failure_point, EffectivenessFailurePoint.BEFORE_CHECK)
            execution = (
                ActionExecution.objects.using(self.using)
                .select_related("action_plan", "execution_authorization")
                .get(pk=plan.action_execution_id)
            )
            predecessor = None
            if predecessor_id:
                predecessor = EffectivenessCheck.objects.using(self.using).get(pk=predecessor_id)
            revision = predecessor.revision + 1 if predecessor else 1
            receipt = execution.receipt
            authorization = execution.execution_authorization
            action_plan = execution.action_plan
            row = EffectivenessCheck.objects.using(self.using).create(
                id=check_id, tenant_id=authority.identity.tenant_id,
                organization_id=authority.organization_id,
                action_execution_id=execution.id, receipt_id=receipt.id,
                action_plan_id=action_plan.id, execution_authorization_id=authorization.id,
                agent_decision_id=authorization.agent_decision_id,
                recommendation_id=authorization.recommendation_id,
                opportunity_lineage_id=plan.opportunity_lineage_id,
                before_opportunity_revision_id=receipt.result["before_revision_id"],
                resulting_opportunity_revision_id=receipt.result["after_revision_id"],
                outcome=outcome, assessment_method=plan.assessment_method,
                criteria_hash=_hash(plan.criteria_hash, "criteria_hash"),
                planning_context_hash=_hash(plan.planning_context_hash, "planning_context_hash"),
                reason_code=reason_code, explanation=explanation,
                due_at=plan.due_at, assessed_at=assessed_at,
                measurement_definition_id=plan.measurement_definition_id,
                predecessor_id=predecessor_id, revision=revision,
                correction_reason=correction_reason,
                actor_user_projection_id=authority.actor_user_projection_id,
                actor_external_id_snapshot=authority.actor_external_id,
                actor_type="human",
                authority_context_version=authority.authority_context_version,
                authority_decision_reference=authority.authority_decision_reference,
                policy_id=POLICY_ID, trace_id=trace_id, correlation_id=correlation_id,
            )
            self._inject(failure_point, EffectivenessFailurePoint.AFTER_CHECK)
            evidence_payload = []
            for index, reference in enumerate(references):
                if index == 0:
                    self._inject(failure_point, EffectivenessFailurePoint.DURING_FIRST_EVIDENCE)
                elif index > 0:
                    self._inject(failure_point, EffectivenessFailurePoint.DURING_LATER_EVIDENCE)
                EffectivenessEvidence.objects.using(self.using).create(
                    id=uuid4(), tenant_id=authority.identity.tenant_id,
                    organization_id=authority.organization_id,
                    effectiveness_check_id=check_id, evidence_id=reference.evidence_id,
                    evidence_lineage_id_snapshot=reference.lineage_id,
                    evidence_revision_snapshot=reference.revision,
                    evidence_content_hash_snapshot=reference.content_hash,
                    criterion_role=reference.criterion_role,
                )
                evidence_payload.append({
                    "evidence_revision_id": str(reference.evidence_id),
                    "lineage_id": str(reference.lineage_id), "revision": reference.revision,
                    "content_hash": reference.content_hash, "criterion_role": reference.criterion_role,
                })
            self._inject(failure_point, EffectivenessFailurePoint.AFTER_EVIDENCE)
            payload = {
                "effectiveness_check_id": str(check_id), "revision": revision,
                "supersedes_check_id": str(predecessor_id) if predecessor_id else None,
                "action_execution_id": str(execution.id), "receipt_id": str(receipt.id),
                "action_plan_id": str(action_plan.id), "plan_hash": action_plan.action_plan_hash,
                "execution_authorization_id": str(authorization.id),
                "agent_decision_id": str(authorization.agent_decision_id),
                "recommendation_id": str(authorization.recommendation_id),
                "target_type": "Opportunity", "target_lineage_id": str(plan.opportunity_lineage_id),
                "before_revision_id": receipt.result["before_revision_id"],
                "after_revision_id": receipt.result["after_revision_id"],
                "outcome": outcome, "assessment_method": plan.assessment_method,
                "actor_type": "human", "actor_external_id": str(authority.actor_external_id),
                "measurement_definition_revision_id": str(plan.measurement_definition_id) if plan.measurement_definition_id else None,
                "evidence_revisions": evidence_payload,
                "due_at": plan.due_at.astimezone(__import__("datetime").timezone.utc).isoformat(),
                "assessed_at": assessed_at.astimezone(__import__("datetime").timezone.utc).isoformat(),
                "trace_id": str(trace_id), "policy_id": POLICY_ID,
            }
            DomainEvent.objects.using(self.using).create(
                event_id=event_id, tenant_id=authority.identity.tenant_id,
                event_type="effectiveness_check.recorded", schema_version=1,
                aggregate_type="effectiveness_check", aggregate_id=check_id,
                aggregate_version=revision, occurred_at=occurred_at, trace_id=trace_id,
                correlation_id=correlation_id, source="iso-smart-effectiveness-governance",
                payload=payload, payload_hash=canonical_hash(payload),
            )
            self._inject(failure_point, EffectivenessFailurePoint.AFTER_EVENT)
            TransactionalOutbox.objects.using(self.using).create(
                id=outbox_id, tenant_id=authority.identity.tenant_id,
                domain_event_id=event_id, status=TransactionalOutbox.Status.PENDING,
                publish_attempts=0, available_at=occurred_at,
            )
            self._inject(failure_point, EffectivenessFailurePoint.AFTER_OUTBOX)
            audit_metadata = dict(payload)
            audit_metadata["execution_governance_id"] = audit_metadata.pop(
                "execution_authorization_id"
            )
            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=authority.identity.tenant_id,
                stream_type="effectiveness_check", stream_id=execution.id,
                actor_type="human", actor_id=str(authority.actor_external_id),
                action="effectiveness_check.recorded", entity_type="effectiveness_check",
                entity_id=check_id, trace_id=trace_id, occurred_at=occurred_at,
                after_hash=canonical_hash(payload), metadata={
                    **audit_metadata, "event_id": str(event_id), "outbox_id": str(outbox_id),
                    "criteria_hash": row.criteria_hash,
                    "planning_context_hash": row.planning_context_hash,
                    "reason_code": reason_code, "explanation": explanation,
                    "correction_reason": correction_reason,
                    "authority_context_version": authority.authority_context_version,
                    "authority_decision_reference": authority.authority_decision_reference,
                },
            ))
            self._inject(failure_point, EffectivenessFailurePoint.AFTER_AUDIT)
            self._inject(failure_point, EffectivenessFailurePoint.BEFORE_COMMIT)
        return EffectivenessRecordResult(check_id, revision, event_id, outbox_id, audit_id, trace_id)
