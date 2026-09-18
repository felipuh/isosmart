"""Phase-21 inert governed-learning artifacts; no target application surface."""

from dataclasses import dataclass
from enum import Enum
import json
import re
from uuid import UUID, uuid4

from django.db import connections, transaction
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash
from .learning_delta import (
    KnowledgeLayerRuleSourceReferenceCorrection,
    build_canonical_delta,
)
from .models import (
    DomainEvent,
    EffectivenessCheck,
    LearningProposal,
    LearningProposalCanonicalDelta,
    LearningProposalSignal,
    LearningSignal,
    LearningSignalEffectiveness,
    TransactionalOutbox,
)
from .tenant_context import TrustedTenantIdentity, bind_trusted_tenant_context_in_transaction


AUTHORIZATION_ID = "governed-learning-implementation-authorization/v1"
DERIVATION_POLICY_ID = "governed-learning-signal-derivation/v1"
DERIVATION_POLICY_VERSION = "v1"
SIGNAL_PERMISSION = "qms.learning_signal.create"
PROPOSAL_PERMISSION = "qms.learning_proposal.create"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TARGET_TABLES = {
    "ModelPolicy": "governance.model_policy",
    "AgentDefinition": "governance.agent_definition",
    "KnowledgeLayerRule": "normative.knowledge_layer_rule",
}


class LearningFailurePoint(str, Enum):
    AFTER_ARTIFACT = "after_artifact"
    AFTER_FIRST_LINK = "after_first_link"
    AFTER_LINKS = "after_links"
    AFTER_EVENT = "after_event"
    AFTER_OUTBOX = "after_outbox"
    AFTER_AUDIT = "after_audit"
    BEFORE_COMMIT = "before_commit"


class ExactProposalFailurePoint(str, Enum):
    AFTER_DELTA = "after_delta"


@dataclass(frozen=True)
class TrustedLearningGovernanceAuthority:
    """Server-resolved human governance authority, separate from QMS review authority."""

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
class ExactLearningTarget:
    target_type: str
    target_id: UUID
    target_lineage_id: UUID
    target_version: str
    target_hash: str


@dataclass(frozen=True)
class LearningCommandResult:
    artifact_id: UUID
    event_id: UUID
    outbox_id: UUID
    provenance_hash: str


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _hash(value, name):
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
    return value


def _inject(actual, expected):
    if actual == expected:
        raise RuntimeError(f"deliberate Phase 21 rollback at {expected.value}")


class _LearningCommand:
    def __init__(self, *, using="learning_governance"):
        self.using = using

    @staticmethod
    def _validate_authority(authority, permission):
        if not isinstance(authority, TrustedLearningGovernanceAuthority):
            raise TypeError("authority must be trusted server-resolved learning governance authority")
        if not isinstance(authority.identity, TrustedTenantIdentity):
            raise TypeError("authority identity must be TrustedTenantIdentity")
        if not authority.mfa_verified or not authority.access_active or permission not in authority.permissions:
            raise PermissionError("active AdminApps learning-governance authority, MFA and exact permission required")
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
                "set_config('app.learning_permissions',%s,true),"
                "set_config('app.mfa_verified','true',true),"
                "set_config('app.access_active','true',true),"
                "set_config('app.authority_context_version',%s,true),"
                "set_config('app.authority_decision_reference',%s,true)",
                [str(authority.organization_id), ",".join(sorted(authority.permissions)),
                 authority.authority_context_version, authority.authority_decision_reference],
            )

    def _event_outbox_audit(
        self, *, authority, event_type, aggregate_type, artifact_id, revision,
        payload, trace_id, correlation_id, occurred_at, failure_point,
    ):
        event_id, outbox_id = uuid4(), uuid4()
        payload_hash = canonical_hash(payload)
        DomainEvent.objects.using(self.using).create(
            event_id=event_id, tenant_id=authority.identity.tenant_id,
            event_type=event_type, schema_version=1, aggregate_type=aggregate_type,
            aggregate_id=artifact_id, aggregate_version=revision, occurred_at=occurred_at,
            trace_id=trace_id, correlation_id=correlation_id,
            source="iso-smart-learning-governance", payload=payload, payload_hash=payload_hash,
        )
        _inject(failure_point, LearningFailurePoint.AFTER_EVENT)
        TransactionalOutbox.objects.using(self.using).create(
            id=outbox_id, tenant_id=authority.identity.tenant_id,
            domain_event_id=event_id, status="pending", publish_attempts=0,
            available_at=occurred_at,
        )
        _inject(failure_point, LearningFailurePoint.AFTER_OUTBOX)
        AuditWriterService(using=self.using).append(AuditAppend(
            tenant_id=authority.identity.tenant_id, stream_type=aggregate_type,
            stream_id=artifact_id, actor_type="human_governance",
            actor_id=str(authority.actor_external_id), action=event_type,
            entity_type=aggregate_type, entity_id=artifact_id, trace_id=trace_id,
            occurred_at=occurred_at, after_hash=payload_hash,
            metadata={"event_id": str(event_id), "schema_version": 1,
                      "authority_decision_reference": authority.authority_decision_reference},
        ))
        _inject(failure_point, LearningFailurePoint.AFTER_AUDIT)
        return event_id, outbox_id


class LearningSignalCommandService(_LearningCommand):
    """Freezes a current Effectiveness leaf and its complete historical lineage."""

    def create_signal(
        self, *, authority, effectiveness_check_id, trace_id,
        correlation_id=None, derived_at=None, failure_point=None,
    ):
        self._validate_authority(authority, SIGNAL_PERMISSION)
        check_id = UUID(str(effectiveness_check_id))
        trace_id = UUID(str(trace_id))
        correlation_id = UUID(str(correlation_id)) if correlation_id else None
        derived_at = derived_at or timezone.now()
        if timezone.is_naive(derived_at):
            raise ValueError("derived_at must be timezone-aware")
        signal_id = uuid4()

        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, trace_id)
            selected = EffectivenessCheck.objects.using(self.using).get(
                pk=check_id, organization_id=authority.organization_id
            )
            if selected.created_at > derived_at:
                raise ValueError("derivation timestamp predates selected Effectiveness revision")
            if EffectivenessCheck.objects.using(self.using).filter(predecessor_id=selected.id).exists():
                raise ValueError("selected EffectivenessCheck is not the authorized current leaf")
            lineage = list(
                EffectivenessCheck.objects.using(self.using)
                .filter(action_execution_id=selected.action_execution_id, revision__lte=selected.revision)
                .order_by("revision")
            )
            if len(lineage) != selected.revision or lineage[-1].id != selected.id:
                raise ValueError("Effectiveness lineage is incomplete or selected revision is not its leaf")
            for index, row in enumerate(lineage):
                expected = None if index == 0 else lineage[index - 1].id
                if row.revision != index + 1 or row.predecessor_id != expected:
                    raise ValueError("Effectiveness lineage is not exact and linear")
            snapshot = [{
                "effectiveness_check_id": str(row.id), "revision": row.revision,
                "predecessor_id": str(row.predecessor_id) if row.predecessor_id else None,
                "outcome": row.outcome, "created_at": row.created_at,
            } for row in lineage]
            provenance = {
                "selected_effectiveness_check_id": str(selected.id),
                "effectiveness_lineage_id": str(selected.action_execution_id),
                "selected_revision": selected.revision,
                "selected_predecessor_id": str(selected.predecessor_id) if selected.predecessor_id else None,
                "selected_was_current_leaf": True, "derivation_timestamp": derived_at,
                "derivation_policy_id": DERIVATION_POLICY_ID,
                "derivation_policy_version": DERIVATION_POLICY_VERSION,
                "lineage": snapshot,
            }
            provenance_hash = canonical_hash(provenance)
            LearningSignal.objects.using(self.using).create(
                id=signal_id, tenant_id=authority.identity.tenant_id,
                organization_id=authority.organization_id,
                selected_effectiveness_check_id=selected.id,
                effectiveness_lineage_id=selected.action_execution_id,
                selected_revision=selected.revision,
                selected_predecessor_id_snapshot=selected.predecessor_id,
                selected_outcome_snapshot=selected.outcome,
                selected_was_current_leaf=True, derivation_timestamp=derived_at,
                derivation_policy_id=DERIVATION_POLICY_ID,
                derivation_policy_version=DERIVATION_POLICY_VERSION,
                provenance_hash=provenance_hash,
                actor_user_projection_id=authority.actor_user_projection_id,
                actor_external_id_snapshot=authority.actor_external_id,
                authority_context_version=authority.authority_context_version,
                authority_decision_reference=authority.authority_decision_reference,
                trace_id=trace_id, correlation_id=correlation_id,
            )
            _inject(failure_point, LearningFailurePoint.AFTER_ARTIFACT)
            for index, row in enumerate(lineage):
                LearningSignalEffectiveness.objects.using(self.using).create(
                    id=uuid4(), tenant_id=authority.identity.tenant_id,
                    organization_id=authority.organization_id, learning_signal_id=signal_id,
                    effectiveness_check_id=row.id,
                    lineage_id_snapshot=selected.action_execution_id,
                    revision_snapshot=row.revision,
                    predecessor_id_snapshot=row.predecessor_id,
                    outcome_snapshot=row.outcome,
                    check_created_at_snapshot=row.created_at,
                    is_selected_leaf=row.id == selected.id,
                )
                if index == 0:
                    _inject(failure_point, LearningFailurePoint.AFTER_FIRST_LINK)
            _inject(failure_point, LearningFailurePoint.AFTER_LINKS)
            payload = {
                "learning_signal_id": str(signal_id),
                "selected_effectiveness_check_id": str(selected.id),
                "effectiveness_lineage_id": str(selected.action_execution_id),
                "selected_revision": selected.revision,
                "selected_predecessor_id": str(selected.predecessor_id) if selected.predecessor_id else None,
                "selected_outcome": selected.outcome, "selected_was_current_leaf": True,
                "derivation_timestamp": derived_at.astimezone(
                    __import__("datetime").timezone.utc
                ).isoformat(),
                "derivation_policy_id": DERIVATION_POLICY_ID,
                "derivation_policy_version": DERIVATION_POLICY_VERSION,
                "provenance_hash": provenance_hash,
                "authority_decision_reference": authority.authority_decision_reference,
            }
            event_id, outbox_id = self._event_outbox_audit(
                authority=authority, event_type="learning_signal.created",
                aggregate_type="learning_signal", artifact_id=signal_id, revision=1,
                payload=payload, trace_id=trace_id, correlation_id=correlation_id,
                occurred_at=derived_at, failure_point=failure_point,
            )
            _inject(failure_point, LearningFailurePoint.BEFORE_COMMIT)
        return LearningCommandResult(signal_id, event_id, outbox_id, provenance_hash)


class LearningProposalCommandService(_LearningCommand):
    """Creates only a frozen governance-pending proposal and exact signal links."""

    def _load_target_snapshot(self, target, *, compensation_for_receipt_id=None):
        if not isinstance(target, ExactLearningTarget):
            raise TypeError("target must be ExactLearningTarget")
        table = TARGET_TABLES.get(target.target_type)
        if table is None:
            raise ValueError("target type is not authorized by the Phase 21 implementation")
        _required(target.target_version, "target_version")
        _hash(target.target_hash, "target_hash")
        with connections[self.using].cursor() as cursor:
            cursor.execute(
                f"SELECT to_jsonb(t) FROM {table} t WHERE id=%s AND lineage_id=%s "
                f"AND version=%s AND NOT EXISTS "
                f"(SELECT 1 FROM {table} n WHERE n.previous_revision_id=t.id)",
                [str(target.target_id), str(target.target_lineage_id), target.target_version],
            )
            row = cursor.fetchone()
        if row is None:
            raise ValueError("target reference is stale or not the current leaf")
        snapshot = row[0]
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)
        if snapshot.get("status") != "published":
            receipt_id = UUID(str(compensation_for_receipt_id)) if compensation_for_receipt_id else None
            if target.target_type != "KnowledgeLayerRule" or snapshot.get("status") != "draft" or not receipt_id:
                raise ValueError("only the exact governed compensation target may be an inert draft head")
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM qms.learning_target_application_receipt "
                    "WHERE id=%s AND after_rule_id=%s AND forward_receipt_id IS NULL "
                    "AND result_status='draft' AND result_published=false "
                    "AND runtime_effect_changed=false)",
                    [str(receipt_id), str(target.target_id)],
                )
                if not cursor.fetchone()[0]:
                    raise ValueError("draft compensation target is not the exact forward Receipt result")
        actual_hash = canonical_hash(snapshot)
        if actual_hash != target.target_hash:
            raise ValueError("target hash drift detected; revalidation or a new proposal is required")
        return snapshot

    def target_has_drifted(self, *, authority, target):
        self._validate_authority(authority, PROPOSAL_PERMISSION)
        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, uuid4())
            try:
                self._load_target_snapshot(target)
            except ValueError:
                return True
            return False

    def create_proposal(
        self, *, authority, signal_ids, target, proposed_change_hash=None, delta_command=None,
        rationale, expected_effect, risks, required_governance_domains,
        trace_id, correlation_id=None, predecessor_id=None,
        correction_reason=None, compensation_for_receipt_id=None, failure_point=None,
    ):
        self._validate_authority(authority, PROPOSAL_PERMISSION)
        signal_ids = tuple(UUID(str(item)) for item in signal_ids)
        if not signal_ids or len(set(signal_ids)) != len(signal_ids):
            raise ValueError("one or more distinct supporting LearningSignals are required")
        if (proposed_change_hash is None) == (delta_command is None):
            raise ValueError("provide exactly one of legacy proposed_change_hash or typed delta_command")
        if proposed_change_hash is not None:
            _hash(proposed_change_hash, "proposed_change_hash")
        rationale = _required(rationale, "rationale")
        expected_effect = _required(expected_effect, "expected_effect")
        risks = tuple(_required(item, "risk") for item in risks)
        domains = tuple(_required(item, "required_governance_domain") for item in required_governance_domains)
        if not domains:
            raise ValueError("at least one separate governance domain is required")
        trace_id = UUID(str(trace_id))
        correlation_id = UUID(str(correlation_id)) if correlation_id else None
        predecessor_id = UUID(str(predecessor_id)) if predecessor_id else None
        if bool(predecessor_id) != bool(correction_reason and correction_reason.strip()):
            raise ValueError("proposal correction requires both predecessor and correction_reason")
        proposal_id, delta_id, occurred_at = uuid4(), uuid4(), timezone.now()

        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, trace_id)
            target_snapshot = self._load_target_snapshot(
                target, compensation_for_receipt_id=compensation_for_receipt_id,
            )
            delta = None
            if delta_command is not None:
                edition_snapshot = None
                if isinstance(delta_command, KnowledgeLayerRuleSourceReferenceCorrection):
                    with connections[self.using].cursor() as cursor:
                        cursor.execute(
                            "SELECT to_jsonb(e) FROM normative.standard_edition e WHERE e.id=%s",
                            [str(delta_command.standard_edition_id)],
                        )
                        edition_row = cursor.fetchone()
                    if edition_row:
                        edition_snapshot = edition_row[0]
                        if isinstance(edition_snapshot, str):
                            edition_snapshot = json.loads(edition_snapshot)
                delta = build_canonical_delta(
                    command=delta_command, target_type=target.target_type,
                    target_id=target.target_id, target_lineage_id=target.target_lineage_id,
                    target_version=target.target_version, target_hash=target.target_hash,
                    target_snapshot=target_snapshot, edition_snapshot=edition_snapshot,
                )
                proposed_change_hash = delta.delta_hash
            signals = list(
                LearningSignal.objects.using(self.using)
                .filter(id__in=signal_ids, organization_id=authority.organization_id)
            )
            if len(signals) != len(signal_ids):
                raise PermissionError("supporting signals are missing or outside the trusted tenant/Organization")
            if len({row.effectiveness_lineage_id for row in signals}) != len(signals):
                raise ValueError("duplicate final sample from one Effectiveness lineage")
            predecessor = None
            if predecessor_id:
                predecessor = LearningProposal.objects.using(self.using).get(
                    pk=predecessor_id, organization_id=authority.organization_id,
                )
            revision = predecessor.revision + 1 if predecessor else 1
            delta_binding = {}
            if delta is not None:
                LearningProposalCanonicalDelta.objects.using(self.using).create(
                    id=delta_id, tenant_id=authority.identity.tenant_id,
                    organization_id=authority.organization_id,
                    learning_proposal_id=proposal_id,
                    canonicalization_version=delta.document["canonicalization_version"],
                    delta_schema_version=delta.delta_schema_version,
                    operation_id=delta.operation_id, operation_version=delta.operation_version,
                    target_type=target.target_type, target_id=target.target_id,
                    target_lineage_id=target.target_lineage_id,
                    target_version=target.target_version, target_hash=target.target_hash,
                    delta_document=delta.document, canonical_bytes=delta.canonical_bytes,
                    delta_hash=delta.delta_hash,
                )
                delta_binding = {
                    "canonical_delta_id": delta_id,
                    "canonicalization_version": delta.document["canonicalization_version"],
                    "delta_schema_version": delta.delta_schema_version,
                    "operation_id": delta.operation_id,
                    "operation_version": delta.operation_version,
                    "delta_hash": delta.delta_hash,
                }
            _inject(failure_point, ExactProposalFailurePoint.AFTER_DELTA)
            LearningProposal.objects.using(self.using).create(
                id=proposal_id, tenant_id=authority.identity.tenant_id,
                organization_id=authority.organization_id,
                target_type=target.target_type, target_scope="global",
                target_id=target.target_id, target_lineage_id=target.target_lineage_id,
                target_version=target.target_version, target_snapshot=target_snapshot,
                target_hash=target.target_hash, proposed_change_hash=proposed_change_hash,
                rationale=rationale, expected_effect=expected_effect, risks=list(risks),
                required_governance_domains=list(domains), status="governance_pending",
                predecessor_id=predecessor_id, revision=revision,
                correction_reason=correction_reason.strip() if correction_reason else None,
                actor_user_projection_id=authority.actor_user_projection_id,
                actor_external_id_snapshot=authority.actor_external_id,
                authority_context_version=authority.authority_context_version,
                authority_decision_reference=authority.authority_decision_reference,
                policy_id=AUTHORIZATION_ID, trace_id=trace_id,
                correlation_id=correlation_id,
                **delta_binding,
            )
            _inject(failure_point, LearningFailurePoint.AFTER_ARTIFACT)
            for index, signal in enumerate(signals):
                LearningProposalSignal.objects.using(self.using).create(
                    id=uuid4(), tenant_id=authority.identity.tenant_id,
                    organization_id=authority.organization_id,
                    learning_proposal_id=proposal_id, learning_signal_id=signal.id,
                    effectiveness_lineage_id_snapshot=signal.effectiveness_lineage_id,
                    signal_provenance_hash_snapshot=signal.provenance_hash,
                )
                if index == 0:
                    _inject(failure_point, LearningFailurePoint.AFTER_FIRST_LINK)
            _inject(failure_point, LearningFailurePoint.AFTER_LINKS)
            proposal_provenance = {
                "learning_proposal_id": str(proposal_id), "revision": revision,
                "predecessor_id": str(predecessor_id) if predecessor_id else None,
                "status": "governance_pending", "signal_ids": sorted(str(item) for item in signal_ids),
                "target_type": target.target_type, "target_scope": "global",
                "target_id": str(target.target_id), "target_lineage_id": str(target.target_lineage_id),
                "target_version": target.target_version, "target_hash": target.target_hash,
                "proposed_change_hash": proposed_change_hash,
                "policy_id": AUTHORIZATION_ID,
            }
            if delta is not None:
                proposal_provenance = {**proposal_provenance, **{
                    "canonical_delta_id": str(delta_id),
                    "canonicalization_version": delta.document["canonicalization_version"],
                    "delta_schema_version": delta.delta_schema_version,
                    "operation_id": delta.operation_id,
                    "operation_version": delta.operation_version,
                    "delta_hash": delta.delta_hash,
                }}
            provenance_hash = canonical_hash(proposal_provenance)
            payload = {**proposal_provenance,
                       "authority_decision_reference": authority.authority_decision_reference,
                       "provenance_hash": provenance_hash}
            event_id, outbox_id = self._event_outbox_audit(
                authority=authority, event_type="learning_proposal.created",
                aggregate_type="learning_proposal", artifact_id=proposal_id,
                revision=revision, payload=payload, trace_id=trace_id,
                correlation_id=correlation_id, occurred_at=occurred_at,
                failure_point=failure_point,
            )
            _inject(failure_point, LearningFailurePoint.BEFORE_COMMIT)
        return LearningCommandResult(proposal_id, event_id, outbox_id, provenance_hash)
