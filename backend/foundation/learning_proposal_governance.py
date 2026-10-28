"""Phase-23 inert proposal review, decision, and application authorization."""

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from uuid import UUID, uuid4

from django.db import connections, transaction
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash
from .learning_delta import (
    canonical_delta_bytes,
    eligibility_classification,
    exact_binding_tuple,
    validate_canonical_delta_document,
)
from .governed_learning import SHA256_RE, TARGET_TABLES
from .models import (
    DomainEvent,
    LearningApplicationAuthorization,
    LearningProposal,
    LearningProposalCanonicalDelta,
    LearningProposalDecision,
    LearningProposalReview,
    TransactionalOutbox,
)
from .tenant_context import TrustedTenantIdentity, bind_trusted_tenant_context_in_transaction


POLICY_ID = "governed-learning-proposal-review-application-boundary/v1"
REVIEW_PERMISSION = "qms.learning_proposal.review"
DECISION_PERMISSION = "qms.learning_proposal.decide"
AUTHORIZATION_PERMISSION = "qms.learning_application.authorize"
CAPABILITY_BY_TARGET = {
    "ModelPolicy": "revise_model_policy",
    "AgentDefinition": "revise_agent_definition",
    "KnowledgeLayerRule": "revise_knowledge_layer_rule",
}
EVENT_CONTRACTS = {
    "learning_proposal.reviewed": 1,
    "learning_proposal.decision_recorded": 1,
    "learning_application.authorized": 1,
}


class GovernanceFailurePoint(str, Enum):
    AFTER_ARTIFACT = "after_artifact"
    AFTER_EVENT = "after_event"
    AFTER_OUTBOX = "after_outbox"
    AFTER_AUDIT = "after_audit"
    BEFORE_COMMIT = "before_commit"


class GovernanceConflict(RuntimeError):
    """A durable identity was replayed with different material."""


@dataclass(frozen=True)
class TrustedLearningReviewAuthority:
    identity: TrustedTenantIdentity
    organization_id: UUID
    actor_user_projection_id: UUID
    actor_external_id: UUID
    permissions: frozenset[str]
    mfa_verified: bool
    access_active: bool
    global_governance: bool
    authority_context_version: str
    authority_decision_reference: str


@dataclass(frozen=True)
class TrustedLearningDecisionAuthority:
    identity: TrustedTenantIdentity
    organization_id: UUID
    actor_user_projection_id: UUID
    actor_external_id: UUID
    permissions: frozenset[str]
    mfa_verified: bool
    access_active: bool
    global_governance: bool
    authority_context_version: str
    authority_decision_reference: str


@dataclass(frozen=True)
class TrustedLearningApplicationAuthority:
    identity: TrustedTenantIdentity
    organization_id: UUID
    actor_user_projection_id: UUID
    actor_external_id: UUID
    permissions: frozenset[str]
    mfa_verified: bool
    access_active: bool
    global_governance: bool
    authority_context_version: str
    authority_decision_reference: str


@dataclass(frozen=True)
class LearningReviewFindings:
    summary: str
    governance_domains: tuple[str, ...]
    autonomy_change_detected: bool = False
    normative_change_detected: bool = False
    policy_relaxation_detected: bool = False
    cross_tenant_effect_detected: bool = False


@dataclass(frozen=True)
class GovernanceCommandResult:
    artifact_id: UUID
    event_id: UUID | None
    outbox_id: UUID | None
    provenance_hash: str
    replayed: bool = False


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _inject(actual, expected):
    if actual == expected:
        raise RuntimeError(f"deliberate Phase 23 rollback at {expected.value}")


def _proposal_material(proposal):
    material = {
        "learning_proposal_id": str(proposal.id),
        "revision": proposal.revision,
        "predecessor_id": str(proposal.predecessor_id) if proposal.predecessor_id else None,
        "tenant_id": str(proposal.tenant_id),
        "organization_id": str(proposal.organization_id),
        "target_type": proposal.target_type,
        "target_scope": proposal.target_scope,
        "target_id": str(proposal.target_id),
        "target_lineage_id": str(proposal.target_lineage_id),
        "target_version": proposal.target_version,
        "target_hash": proposal.target_hash,
        "proposed_change_hash": proposal.proposed_change_hash,
        "status": proposal.status,
        "policy_id": proposal.policy_id,
    }
    if eligibility_classification(proposal) == "CANONICAL_DELTA_V1_ELIGIBLE":
        material = {**material, **{
            "canonical_delta_id": str(proposal.canonical_delta_id),
            "canonicalization_version": proposal.canonicalization_version,
            "delta_schema_version": proposal.delta_schema_version,
            "operation_id": proposal.operation_id,
            "operation_version": proposal.operation_version,
            "delta_hash": proposal.delta_hash,
        }}
    return material


def proposal_material_hash(proposal):
    return canonical_hash(_proposal_material(proposal))


class _GovernanceCommand:
    authority_type = object
    permission = ""
    permission_setting = ""

    def __init__(self, *, using):
        self.using = using

    def _validate_authority(self, authority):
        if not isinstance(authority, self.authority_type):
            raise TypeError("authority must be the exact trusted server-resolved governance authority")
        if not isinstance(authority.identity, TrustedTenantIdentity):
            raise TypeError("authority identity must be TrustedTenantIdentity")
        if (not authority.mfa_verified or not authority.access_active or
                not authority.global_governance or self.permission not in authority.permissions):
            raise PermissionError("active global AdminApps governance authority, MFA, and exact permission required")
        _required(authority.authority_context_version, "authority_context_version")
        _required(authority.authority_decision_reference, "authority_decision_reference")

    def _bind(self, authority, trace_id):
        bind_trusted_tenant_context_in_transaction(
            authority.identity, actor_id=authority.actor_external_id,
            trace_id=trace_id, using=self.using,
        )
        with connections[self.using].cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.organization_id',%s,true),"
                f"set_config('{self.permission_setting}',%s,true),"
                "set_config('app.mfa_verified','true',true),"
                "set_config('app.access_active','true',true),"
                "set_config('app.governance_scope','global',true),"
                "set_config('app.governance_actor_type','human',true),"
                "set_config('app.authority_context_version',%s,true),"
                "set_config('app.authority_decision_reference',%s,true)",
                [str(authority.organization_id), self.permission,
                 authority.authority_context_version, authority.authority_decision_reference],
            )

    def _proposal(self, authority, proposal_id, *, lock=True):
        proposal_id = UUID(str(proposal_id))
        if lock:
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,23))",
                    [str(proposal_id)],
                )
        query = LearningProposal.objects.using(self.using)
        proposal = query.get(pk=proposal_id, organization_id=authority.organization_id)
        if proposal.tenant_id != authority.identity.tenant_id:
            raise PermissionError("proposal is outside the trusted tenant")
        return proposal

    def _target_is_current(self, proposal):
        table = TARGET_TABLES.get(proposal.target_type)
        if table is None:
            return False
        with connections[self.using].cursor() as cursor:
            cursor.execute(
                f"SELECT to_jsonb(t) FROM {table} t WHERE id=%s AND lineage_id=%s "
                "AND version=%s AND NOT EXISTS "
                f"(SELECT 1 FROM {table} n WHERE n.previous_revision_id=t.id)",
                [str(proposal.target_id), str(proposal.target_lineage_id), proposal.target_version],
            )
            row = cursor.fetchone()
        if row is None:
            return False
        snapshot = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        if snapshot != proposal.target_snapshot or canonical_hash(snapshot) != proposal.target_hash:
            return False
        if snapshot.get("status") == "published":
            return True
        if proposal.target_type != "KnowledgeLayerRule" or snapshot.get("status") != "draft":
            return False
        with connections[self.using].cursor() as cursor:
            cursor.execute("SELECT to_regclass('qms.learning_target_application_receipt')")
            if cursor.fetchone()[0] is None:
                return False
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM qms.learning_target_application_receipt "
                "WHERE after_rule_id=%s AND forward_receipt_id IS NULL "
                "AND result_status='draft' AND result_published=false "
                "AND runtime_effect_changed=false)",
                [str(proposal.target_id)],
            )
            return cursor.fetchone()[0]

    @staticmethod
    def _proposal_is_current(proposal, using):
        return not LearningProposal.objects.using(using).filter(predecessor_id=proposal.id).exists()

    def _verified_delta_binding(self, proposal):
        if eligibility_classification(proposal) != "CANONICAL_DELTA_V1_ELIGIBLE":
            return {}
        delta = LearningProposalCanonicalDelta.objects.using(self.using).get(
            pk=proposal.canonical_delta_id, learning_proposal_id=proposal.id,
        )
        encoded = bytes(delta.canonical_bytes)
        if (canonical_delta_bytes(delta.delta_document) != encoded or
                hashlib.sha256(encoded).hexdigest() != delta.delta_hash or
                proposal.proposed_change_hash != delta.delta_hash):
            raise GovernanceConflict("proposal-owned canonical delta material is not exact")
        edition_snapshot = None
        if proposal.target_type == "KnowledgeLayerRule":
            edition_id = delta.delta_document["payload"]["standard_edition_id"]
            with connections[self.using].cursor() as cursor:
                cursor.execute("SELECT to_jsonb(e) FROM normative.standard_edition e WHERE id=%s", [edition_id])
                row = cursor.fetchone()
            if row:
                edition_snapshot = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        validate_canonical_delta_document(
            delta.delta_document, proposal.target_snapshot, edition_snapshot=edition_snapshot,
        )
        expected = (delta.id, delta.canonicalization_version, delta.delta_schema_version,
                    delta.operation_id, delta.operation_version, delta.delta_hash)
        if exact_binding_tuple(proposal) != expected:
            raise GovernanceConflict("proposal direct delta binding differs from its owned artifact")
        return {
            "canonical_delta_id": delta.id,
            "canonicalization_version": delta.canonicalization_version,
            "delta_schema_version": delta.delta_schema_version,
            "operation_id": delta.operation_id,
            "operation_version": delta.operation_version,
            "delta_hash": delta.delta_hash,
        }

    @staticmethod
    def _payload_binding(binding):
        return {key: str(value) if key == "canonical_delta_id" else value
                for key, value in binding.items()}

    def _event_outbox_audit(
        self, *, authority, event_type, aggregate_type, artifact_id, aggregate_version,
        payload, trace_id, correlation_id, occurred_at, failure_point,
    ):
        event_id, outbox_id = uuid4(), uuid4()
        payload_hash = canonical_hash(payload)
        DomainEvent.objects.using(self.using).create(
            event_id=event_id, tenant_id=authority.identity.tenant_id,
            event_type=event_type, schema_version=EVENT_CONTRACTS[event_type],
            aggregate_type=aggregate_type, aggregate_id=artifact_id,
            aggregate_version=aggregate_version, occurred_at=occurred_at,
            trace_id=trace_id, correlation_id=correlation_id,
            source="iso-smart-learning-governance", payload=payload, payload_hash=payload_hash,
        )
        _inject(failure_point, GovernanceFailurePoint.AFTER_EVENT)
        TransactionalOutbox.objects.using(self.using).create(
            id=outbox_id, tenant_id=authority.identity.tenant_id,
            domain_event_id=event_id, status="pending", publish_attempts=0,
            available_at=occurred_at,
        )
        _inject(failure_point, GovernanceFailurePoint.AFTER_OUTBOX)
        audit_metadata = {
            "event_id": str(event_id), "schema_version": EVENT_CONTRACTS[event_type],
            "governance_record_id": str(artifact_id),
            "proposal_id": payload.get("learning_proposal_id"),
            "proposal_revision": payload.get("proposal_revision"),
            "proposal_material_hash": payload.get("proposal_material_hash"),
            "review_ids": payload.get("review_ids"),
            "decision_id": payload.get("decision_id") or payload.get("learning_proposal_decision_id"),
            "target_type": payload.get("target_type"), "target_id": payload.get("target_id"),
            "target_lineage_id": payload.get("target_lineage_id"),
            "target_version": payload.get("target_version"), "target_hash": payload.get("target_hash"),
            "capability_id": payload.get("capability_id"),
            "capability_version": payload.get("capability_version"),
            "governance_outcome": payload.get("outcome") or payload.get("review_outcome") or payload.get("authorization_status"),
            "idempotency_hash": payload.get("idempotency_hash"),
            "governance_decision_reference_hash": canonical_hash(
                authority.authority_decision_reference
            ),
            "policy_id": payload.get("policy_id"),
        }
        audit_metadata = {key: value for key, value in audit_metadata.items() if value is not None}
        AuditWriterService(using=self.using).append(AuditAppend(
            tenant_id=authority.identity.tenant_id, stream_type=aggregate_type,
            stream_id=artifact_id, actor_type="human_governance",
            actor_id=str(authority.actor_external_id), action=event_type,
            entity_type=aggregate_type, entity_id=artifact_id, trace_id=trace_id,
            occurred_at=occurred_at, after_hash=payload_hash,
            metadata=audit_metadata,
        ))
        _inject(failure_point, GovernanceFailurePoint.AFTER_AUDIT)
        return event_id, outbox_id, payload_hash


class LearningProposalReviewCommandService(_GovernanceCommand):
    authority_type = TrustedLearningReviewAuthority
    permission = REVIEW_PERMISSION
    permission_setting = "app.learning_review_permissions"

    def __init__(self, *, using="learning_reviewer"):
        super().__init__(using=using)

    def record_learning_proposal_review(
        self, *, authority, proposal_id, findings, trace_id,
        correlation_id=None, failure_point=None,
    ):
        self._validate_authority(authority)
        if not isinstance(findings, LearningReviewFindings):
            raise TypeError("findings must be bounded LearningReviewFindings")
        summary = _required(findings.summary, "findings.summary")
        domains = tuple(sorted({_required(item, "governance_domain") for item in findings.governance_domains}))
        if not domains:
            raise ValueError("at least one reviewed governance domain is required")
        trace_id = UUID(str(trace_id))
        correlation_id = UUID(str(correlation_id)) if correlation_id else None
        review_id, occurred_at = uuid4(), timezone.now()

        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, trace_id)
            proposal = self._proposal(authority, proposal_id, lock=False)
            delta_binding = self._verified_delta_binding(proposal)
            material_hash = proposal_material_hash(proposal)
            target_status = "valid" if self._target_is_current(proposal) else "stale"
            finding_payload = {
                **asdict(findings), "summary": summary,
                "governance_domains": list(domains),
            }
            LearningProposalReview.objects.using(self.using).create(
                id=review_id, tenant_id=proposal.tenant_id,
                organization_id=proposal.organization_id,
                learning_proposal_id=proposal.id,
                proposal_revision_snapshot=proposal.revision,
                proposal_predecessor_id_snapshot=proposal.predecessor_id,
                proposal_material_hash=material_hash,
                target_type=proposal.target_type, target_id=proposal.target_id,
                target_lineage_id=proposal.target_lineage_id,
                target_version=proposal.target_version, target_hash=proposal.target_hash,
                target_status_snapshot=target_status, review_outcome="review_recorded",
                findings=finding_payload, reviewed_governance_domains=list(domains),
                reviewer_user_projection_id=authority.actor_user_projection_id,
                reviewer_external_id_snapshot=authority.actor_external_id,
                authority_context_version=authority.authority_context_version,
                authority_decision_reference=authority.authority_decision_reference,
                governance_scope="global", policy_id=POLICY_ID,
                trace_id=trace_id, correlation_id=correlation_id,
                **delta_binding,
            )
            _inject(failure_point, GovernanceFailurePoint.AFTER_ARTIFACT)
            payload = {
                "learning_proposal_review_id": str(review_id),
                "learning_proposal_id": str(proposal.id),
                "proposal_revision": proposal.revision,
                "proposal_material_hash": material_hash,
                "target_type": proposal.target_type, "target_id": str(proposal.target_id),
                "target_lineage_id": str(proposal.target_lineage_id),
                "target_version": proposal.target_version, "target_hash": proposal.target_hash,
                "target_status": target_status, "review_outcome": "review_recorded",
                "findings": finding_payload, "governance_scope": "global",
                "authority_decision_reference": authority.authority_decision_reference,
                "policy_id": POLICY_ID,
            }
            payload = {**payload, **self._payload_binding(delta_binding)}
            event_id, outbox_id, payload_hash = self._event_outbox_audit(
                authority=authority, event_type="learning_proposal.reviewed",
                aggregate_type="learning_proposal_review", artifact_id=review_id,
                aggregate_version=1, payload=payload, trace_id=trace_id,
                correlation_id=correlation_id, occurred_at=occurred_at,
                failure_point=failure_point,
            )
            _inject(failure_point, GovernanceFailurePoint.BEFORE_COMMIT)
        return GovernanceCommandResult(review_id, event_id, outbox_id, payload_hash)


class LearningProposalDecisionCommandService(_GovernanceCommand):
    authority_type = TrustedLearningDecisionAuthority
    permission = DECISION_PERMISSION
    permission_setting = "app.learning_decision_permissions"

    def __init__(self, *, using="learning_approver"):
        super().__init__(using=using)

    def record_learning_proposal_decision(
        self, *, authority, proposal_id, review_ids, outcome, rationale,
        trace_id, correlation_id=None, failure_point=None,
    ):
        self._validate_authority(authority)
        if outcome not in LearningProposalDecision.Outcome.values:
            raise ValueError("decision outcome is not Phase-22 approved")
        rationale = _required(rationale, "rationale")
        review_ids = tuple(sorted({UUID(str(item)) for item in review_ids}, key=str))
        if not review_ids:
            raise ValueError("one or more exact proposal reviews are required")
        trace_id = UUID(str(trace_id))
        correlation_id = UUID(str(correlation_id)) if correlation_id else None
        occurred_at = timezone.now()

        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, trace_id)
            proposal = self._proposal(authority, proposal_id)
            if proposal.actor_external_id_snapshot == authority.actor_external_id:
                raise PermissionError("proposal creator cannot approve own proposal")
            if not self._proposal_is_current(proposal, self.using):
                raise GovernanceConflict("superseded proposal revision cannot receive a decision")
            if not self._target_is_current(proposal):
                raise GovernanceConflict("target drift requires revalidation and a new proposal")
            reviews = list(LearningProposalReview.objects.using(self.using).filter(
                id__in=review_ids, learning_proposal_id=proposal.id,
                proposal_revision_snapshot=proposal.revision,
            ))
            if len(reviews) != len(review_ids):
                raise PermissionError("reviews are missing or do not bind the exact proposal revision")
            if any(row.target_status_snapshot != "valid" for row in reviews):
                raise GovernanceConflict("stale review evidence cannot support a decision")
            delta_binding = self._verified_delta_binding(proposal)
            expected_binding = exact_binding_tuple(proposal)
            if any(exact_binding_tuple(row) != expected_binding for row in reviews):
                raise GovernanceConflict("reviews do not bind the identical exact delta tuple")
            if outcome == LearningProposalDecision.Outcome.APPROVED_FOR_APPLICATION:
                unsafe = (
                    "autonomy_change_detected", "normative_change_detected",
                    "policy_relaxation_detected", "cross_tenant_effect_detected",
                )
                if any(any(bool(row.findings.get(flag)) for flag in unsafe) for row in reviews):
                    raise PermissionError("prohibited safety finding prevents approval")
            material_hash = proposal_material_hash(proposal)
            review_snapshot = [str(item) for item in review_ids]
            review_set_hash = canonical_hash(review_snapshot)
            identity = {
                "proposal_id": str(proposal.id), "proposal_material_hash": material_hash,
                "review_set_hash": review_set_hash, "outcome": outcome,
                "rationale": rationale,
                "approver": str(authority.actor_external_id), "policy_id": POLICY_ID,
            }
            identity_hash = canonical_hash(identity)
            existing = LearningProposalDecision.objects.using(self.using).filter(
                learning_proposal_id=proposal.id).first()
            if existing:
                if existing.decision_identity_hash != identity_hash:
                    raise GovernanceConflict("proposal already has a different immutable decision")
                return GovernanceCommandResult(
                    existing.id, None, None, existing.decision_identity_hash, replayed=True,
                )
            decision_id = uuid4()
            LearningProposalDecision.objects.using(self.using).create(
                id=decision_id, tenant_id=proposal.tenant_id,
                organization_id=proposal.organization_id,
                learning_proposal_id=proposal.id,
                proposal_revision_snapshot=proposal.revision,
                proposal_predecessor_id_snapshot=proposal.predecessor_id,
                proposal_material_hash=material_hash,
                review_ids_snapshot=review_snapshot, review_set_hash=review_set_hash,
                target_type=proposal.target_type, target_id=proposal.target_id,
                target_lineage_id=proposal.target_lineage_id,
                target_version=proposal.target_version, target_hash=proposal.target_hash,
                outcome=outcome, rationale=rationale,
                decision_identity_hash=identity_hash,
                approver_user_projection_id=authority.actor_user_projection_id,
                approver_external_id_snapshot=authority.actor_external_id,
                authority_context_version=authority.authority_context_version,
                authority_decision_reference=authority.authority_decision_reference,
                governance_scope="global", policy_id=POLICY_ID,
                trace_id=trace_id, correlation_id=correlation_id,
                **delta_binding,
            )
            _inject(failure_point, GovernanceFailurePoint.AFTER_ARTIFACT)
            payload = {
                "learning_proposal_decision_id": str(decision_id),
                "learning_proposal_id": str(proposal.id),
                "proposal_revision": proposal.revision,
                "proposal_material_hash": material_hash,
                "review_ids": review_snapshot, "review_set_hash": review_set_hash,
                "target_type": proposal.target_type, "target_id": str(proposal.target_id),
                "target_lineage_id": str(proposal.target_lineage_id),
                "target_version": proposal.target_version, "target_hash": proposal.target_hash,
                "outcome": outcome, "governance_scope": "global",
                "authority_decision_reference": authority.authority_decision_reference,
                "policy_id": POLICY_ID,
            }
            payload = {**payload, **self._payload_binding(delta_binding)}
            event_id, outbox_id, payload_hash = self._event_outbox_audit(
                authority=authority, event_type="learning_proposal.decision_recorded",
                aggregate_type="learning_proposal_decision", artifact_id=decision_id,
                aggregate_version=1, payload=payload, trace_id=trace_id,
                correlation_id=correlation_id, occurred_at=occurred_at,
                failure_point=failure_point,
            )
            _inject(failure_point, GovernanceFailurePoint.BEFORE_COMMIT)
        return GovernanceCommandResult(decision_id, event_id, outbox_id, payload_hash)


class LearningApplicationAuthorizationCommandService(_GovernanceCommand):
    authority_type = TrustedLearningApplicationAuthority
    permission = AUTHORIZATION_PERMISSION
    permission_setting = "app.learning_authorization_permissions"

    def __init__(self, *, using="learning_authorizer"):
        super().__init__(using=using)

    def authorize_learning_proposal_application(
        self, *, authority, proposal_id, decision_id, capability_id,
        idempotency_key, trace_id, correlation_id=None, failure_point=None,
    ):
        self._validate_authority(authority)
        capability_id = _required(capability_id, "capability_id")
        idempotency_key = _required(idempotency_key, "idempotency_key")
        if len(idempotency_key) > 255:
            raise ValueError("idempotency_key is too long")
        trace_id = UUID(str(trace_id))
        correlation_id = UUID(str(correlation_id)) if correlation_id else None
        occurred_at = timezone.now()

        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, trace_id)
            proposal = self._proposal(authority, proposal_id)
            if proposal.actor_external_id_snapshot == authority.actor_external_id:
                raise PermissionError("proposal creator cannot authorize own proposal")
            if not self._proposal_is_current(proposal, self.using):
                raise GovernanceConflict("superseded proposal revision cannot be authorized")
            if not self._target_is_current(proposal):
                raise GovernanceConflict("target drift makes application authorization stale")
            decision = LearningProposalDecision.objects.using(self.using).get(
                pk=UUID(str(decision_id)), learning_proposal_id=proposal.id,
            )
            if decision.outcome != LearningProposalDecision.Outcome.APPROVED_FOR_APPLICATION:
                raise PermissionError("only approved_for_application may be separately authorized")
            if decision.approver_external_id_snapshot == authority.actor_external_id:
                raise PermissionError("decision approver and application authorizer must be independent")
            delta_binding = self._verified_delta_binding(proposal)
            expected_tuple = exact_binding_tuple(proposal)
            if exact_binding_tuple(decision) != expected_tuple:
                raise GovernanceConflict("decision does not bind the proposal's exact delta tuple")
            expected_capability = (
                proposal.operation_id if delta_binding else CAPABILITY_BY_TARGET.get(proposal.target_type)
            )
            if capability_id != expected_capability:
                raise PermissionError("capability is not the exact immutable target-operation contract")
            material_hash = proposal_material_hash(proposal)
            material = {
                "tenant_id": str(proposal.tenant_id), "organization_id": str(proposal.organization_id),
                "proposal_id": str(proposal.id), "proposal_revision": proposal.revision,
                "proposal_material_hash": material_hash, "decision_id": str(decision.id),
                "target_type": proposal.target_type, "target_id": str(proposal.target_id),
                "target_lineage_id": str(proposal.target_lineage_id),
                "target_version": proposal.target_version, "target_hash": proposal.target_hash,
                "capability_id": capability_id, "capability_version": "v1",
                "idempotency_key": idempotency_key,
                "authorizer": str(authority.actor_external_id),
                "authority_context_version": authority.authority_context_version,
                "authority_decision_reference": authority.authority_decision_reference,
            }
            material = {**material, **self._payload_binding(delta_binding)}
            idempotency_hash = canonical_hash(material)
            existing = LearningApplicationAuthorization.objects.using(self.using).filter(
                tenant_id=proposal.tenant_id, idempotency_key=idempotency_key,
            ).first()
            if existing:
                if existing.idempotency_hash != idempotency_hash:
                    raise GovernanceConflict("idempotency key already binds different authorization material")
                return GovernanceCommandResult(
                    existing.id, None, None, existing.idempotency_hash, replayed=True,
                )
            authorization_id = uuid4()
            LearningApplicationAuthorization.objects.using(self.using).create(
                id=authorization_id, tenant_id=proposal.tenant_id,
                organization_id=proposal.organization_id,
                learning_proposal_id=proposal.id,
                learning_proposal_decision_id=decision.id,
                proposal_revision_snapshot=proposal.revision,
                proposal_material_hash=material_hash,
                target_type=proposal.target_type, target_id=proposal.target_id,
                target_lineage_id=proposal.target_lineage_id,
                target_version=proposal.target_version, target_hash=proposal.target_hash,
                capability_id=capability_id, capability_version="v1",
                authorization_status="authorized", idempotency_key=idempotency_key,
                idempotency_hash=idempotency_hash,
                authorizer_user_projection_id=authority.actor_user_projection_id,
                authorizer_external_id_snapshot=authority.actor_external_id,
                authority_context_version=authority.authority_context_version,
                authority_decision_reference=authority.authority_decision_reference,
                governance_scope="global", policy_id=POLICY_ID,
                trace_id=trace_id, correlation_id=correlation_id,
                **delta_binding,
            )
            _inject(failure_point, GovernanceFailurePoint.AFTER_ARTIFACT)
            payload = {
                "learning_application_authorization_id": str(authorization_id),
                **{key: value for key, value in material.items() if key != "idempotency_key"},
                "authorization_status": "authorized", "idempotency_hash": idempotency_hash,
                "governance_scope": "global",
                "authority_decision_reference": authority.authority_decision_reference,
                "policy_id": POLICY_ID,
            }
            event_id, outbox_id, payload_hash = self._event_outbox_audit(
                authority=authority, event_type="learning_application.authorized",
                aggregate_type="learning_application_authorization",
                artifact_id=authorization_id, aggregate_version=1,
                payload=payload, trace_id=trace_id, correlation_id=correlation_id,
                occurred_at=occurred_at, failure_point=failure_point,
            )
            _inject(failure_point, GovernanceFailurePoint.BEFORE_COMMIT)
        return GovernanceCommandResult(authorization_id, event_id, outbox_id, payload_hash)

    def classify_authorization(self, *, authority, authorization_id):
        """Return deterministic VALID/STALE without mutating authorization history."""
        self._validate_authority(authority)
        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, uuid4())
            authorization = LearningApplicationAuthorization.objects.using(self.using).get(
                pk=UUID(str(authorization_id)), organization_id=authority.organization_id,
            )
            proposal = self._proposal(authority, authorization.learning_proposal_id, lock=False)
            if (eligibility_classification(proposal) != "CANONICAL_DELTA_V1_ELIGIBLE" or
                    eligibility_classification(authorization) != "CANONICAL_DELTA_V1_ELIGIBLE"):
                return "LEGACY_INERT"
            if (not self._proposal_is_current(proposal, self.using) or
                    not self._target_is_current(proposal) or
                    authorization.proposal_material_hash != proposal_material_hash(proposal) or
                    exact_binding_tuple(authorization) != exact_binding_tuple(proposal)):
                return "STALE"
            return "VALID"
