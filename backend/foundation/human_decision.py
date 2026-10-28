"""Phase 12 governed AgentDecision and Human Decision Gate commands."""

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from django.db import connections
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    AgentDecision,
    AgentRun,
    AgentRunRecommendation,
    Approval,
    DomainEvent,
    ModelPolicy,
    TransactionalOutbox,
    UserProjection,
)
from .tenant_context import TrustedTenantIdentity, trusted_tenant_context


EVENT_CONTRACTS = {"agent_decision.recorded": 1, "approval.recorded": 1}


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _json_object(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _confidence(value):
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("confidence must be a normalized decimal in [0,1]") from exc
    if not normalized.is_finite() or normalized < 0 or normalized > 1:
        raise ValueError("confidence must be a normalized decimal in [0,1]")
    return normalized


def _autonomy(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 4:
        raise ValueError("decision_autonomy must be an integer from A0 through A4")
    return value


def _human_gate_required(policy, decision_autonomy):
    rules = _json_object(policy.human_gate_rules, "ModelPolicy.human_gate_rules")
    levels = rules.get("required_autonomy_levels", [])
    if not isinstance(levels, list) or any(level not in {"A0", "A1", "A2", "A3", "A4"} for level in levels):
        raise ValueError("human_gate_rules.required_autonomy_levels must contain only A0-A4")
    always_required = rules.get("always_required", False)
    if not isinstance(always_required, bool):
        raise ValueError("human_gate_rules.always_required must be boolean")
    # A3 is source-defined as requiring explicit human approval. Policy may
    # require a gate at any other level, including A4; no level authorizes action.
    return decision_autonomy == 3 or always_required or f"A{decision_autonomy}" in levels


@dataclass(frozen=True)
class AuthorizedHumanContext:
    """Authority already resolved by the trusted AdminApps/server boundary."""

    identity: TrustedTenantIdentity
    user_projection_id: UUID
    adminapps_user_id: UUID
    authorized_roles: tuple[str, ...]
    principal_type: str = "human"
    authority_source: str = "adminapps_contract"

    def __post_init__(self):
        if self.principal_type != "human":
            raise ValueError("only a resolved human principal may enter the Human Decision Gate")
        if self.authority_source not in {"adminapps_contract", "controlled_test_fixture"}:
            raise ValueError("human approval authority must come from the trusted server boundary")
        if not self.authorized_roles or any(not isinstance(role, str) or not role.strip() for role in self.authorized_roles):
            raise ValueError("resolved human authority requires at least one nonblank role")


@dataclass(frozen=True)
class AgentDecisionResult:
    decision_id: UUID
    recommendation_id: UUID | None
    human_gate_required: bool
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID


@dataclass(frozen=True)
class ApprovalResult:
    approval_id: UUID
    decision: str
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID


def _event_and_outbox(*, using, tenant_id, event_type, aggregate_type, aggregate_id,
                      occurred_at, trace_id, payload, source):
    event_id = uuid4()
    canonical_payload = json.loads(canonical_json(payload))["value"]
    DomainEvent.objects.using(using).create(
        event_id=event_id, tenant_id=tenant_id, event_type=event_type,
        schema_version=EVENT_CONTRACTS[event_type], aggregate_type=aggregate_type,
        aggregate_id=aggregate_id, aggregate_version=1, occurred_at=occurred_at,
        trace_id=trace_id, source=source, payload=canonical_payload,
        payload_hash=canonical_hash(canonical_payload),
    )
    outbox = TransactionalOutbox.objects.using(using).create(
        tenant_id=tenant_id, domain_event_id=event_id,
        status=TransactionalOutbox.Status.PENDING, publish_attempts=0,
        available_at=occurred_at,
    )
    return event_id, outbox.id


class AgentDecisionCommandService:
    """Worker-only append boundary; records governance and performs no action."""

    def __init__(self, *, using="worker"):
        self.using = using

    def record_agent_decision(
        self, *, identity, agent_run_id, decision_type, payload, confidence,
        explainability, decision_autonomy, actor_id, fail_before_commit=False,
    ):
        decision_id = uuid4()
        decision_autonomy = _autonomy(decision_autonomy)
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=uuid4(), using=self.using,
        ):
            run = AgentRun.objects.using(self.using).select_for_update().get(id=agent_run_id)
            policy = ModelPolicy.objects.using(self.using).get(id=run.model_policy_id)
            if decision_autonomy > min(run.requested_autonomy, run.effective_autonomy_ceiling):
                raise ValueError("AgentDecision autonomy exceeds the exact AgentRun/policy ceiling")
            link = AgentRunRecommendation.objects.using(self.using).filter(agent_run_id=run.id).first()
            recommendation_id = link.recommendation_id if link else None
            gate_required = _human_gate_required(policy, decision_autonomy)
            decision = AgentDecision.objects.using(self.using).create(
                id=decision_id, tenant_id=identity.tenant_id,
                organization_id=run.organization_id, agent_run_id=run.id,
                recommendation_id=recommendation_id,
                decision_type=_required(decision_type, "decision_type"),
                payload=_json_object(payload, "payload"), confidence=_confidence(confidence),
                explainability=_json_object(explainability, "explainability"),
                decision_autonomy=decision_autonomy,
                human_gate_required=gate_required, trace_id=run.trace_id,
            )
            occurred_at = decision.created_at
            state = {
                "agent_decision_id": str(decision.id), "agent_run_id": str(run.id),
                "recommendation_id": str(recommendation_id) if recommendation_id else None,
                "organization_id": str(run.organization_id),
                "decision_type": decision.decision_type, "payload": decision.payload,
                "confidence": str(decision.confidence),
                "confidence_semantics": "normalized_indicator_not_statistical_probability",
                "explainability": decision.explainability,
                "decision_autonomy": f"A{decision.decision_autonomy}",
                "effective_autonomy_ceiling": f"A{run.effective_autonomy_ceiling}",
                "human_gate_required": decision.human_gate_required,
                "model_policy_id": str(run.model_policy_id), "trace_id": str(run.trace_id),
                "advisory_only": True, "execution_authorized": False, "no_execution": True,
            }
            event_id, outbox_id = _event_and_outbox(
                using=self.using, tenant_id=identity.tenant_id,
                event_type="agent_decision.recorded", aggregate_type="agent_decision",
                aggregate_id=decision.id, occurred_at=occurred_at, trace_id=run.trace_id,
                payload=state, source="iso-smart-agent-runtime",
            )
            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=identity.tenant_id, stream_type="agent_decision",
                stream_id=decision.id, actor_type="worker", actor_id=str(actor_id),
                action="agent_decision.recorded", entity_type="agent_decision",
                entity_id=decision.id, trace_id=run.trace_id, occurred_at=occurred_at,
                after_hash=canonical_hash(state),
                metadata={"event_id": str(event_id), "schema_version": 1,
                          "agent_run_id": str(run.id),
                          "recommendation_id": str(recommendation_id) if recommendation_id else None,
                          "human_gate_required": gate_required,
                          "execution_authorized": False},
            ))
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 12 AgentDecision rollback after audit")
            return AgentDecisionResult(
                decision.id, recommendation_id, gate_required, event_id, outbox_id, audit_id,
            )


class HumanDecisionGateService:
    """Dedicated human principal path; identity/role/tenant are never command fields."""

    def __init__(self, *, using="human_approver"):
        self.using = using

    def record_human_approval(self, *, authority, agent_decision_id, comments, trace_id,
                              fail_before_commit=False):
        return self._record(authority=authority, agent_decision_id=agent_decision_id,
                            decision=Approval.Decision.APPROVE, comments=comments,
                            trace_id=trace_id, fail_before_commit=fail_before_commit)

    def record_human_rejection(self, *, authority, agent_decision_id, comments, trace_id,
                               fail_before_commit=False):
        return self._record(authority=authority, agent_decision_id=agent_decision_id,
                            decision=Approval.Decision.REJECT, comments=comments,
                            trace_id=trace_id, fail_before_commit=fail_before_commit)

    def request_human_changes(self, *, authority, agent_decision_id, comments, trace_id,
                              fail_before_commit=False):
        return self._record(authority=authority, agent_decision_id=agent_decision_id,
                            decision=Approval.Decision.REQUEST_CHANGES, comments=comments,
                            trace_id=trace_id, fail_before_commit=fail_before_commit)

    def _record(self, *, authority, agent_decision_id, decision, comments, trace_id,
                fail_before_commit):
        if not isinstance(authority, AuthorizedHumanContext):
            raise TypeError("authority must be a server-resolved AuthorizedHumanContext")
        trace_id = UUID(str(trace_id))
        actor_id = str(authority.adminapps_user_id)
        with trusted_tenant_context(
            authority.identity, actor_id=actor_id, trace_id=trace_id, using=self.using,
        ):
            governed_decision = AgentDecision.objects.using(self.using).get(id=agent_decision_id)
            if not governed_decision.human_gate_required:
                raise ValueError("AgentDecision does not require a Human Decision Gate")
            run = AgentRun.objects.using(self.using).get(id=governed_decision.agent_run_id)
            policy = ModelPolicy.objects.using(self.using).get(id=run.model_policy_id)
            required_role = _required(policy.human_gate_rules.get("required_role"),
                                      "ModelPolicy.human_gate_rules.required_role")
            if required_role not in authority.authorized_roles:
                raise PermissionError("resolved human principal lacks the policy-required approval role")
            user = UserProjection.objects.using(self.using).get(
                id=authority.user_projection_id,
                adminapps_user_id=authority.adminapps_user_id,
                lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
            )
            approval_id = uuid4()
            decided_at = timezone.now()
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT qms.foundation_0012_record_human_approval(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    [str(approval_id), str(authority.identity.tenant_id),
                     str(governed_decision.organization_id), str(governed_decision.id),
                     str(governed_decision.recommendation_id) if governed_decision.recommendation_id else None,
                     required_role, decision, str(user.id), str(authority.adminapps_user_id),
                     comments, decided_at, str(trace_id)],
                )
                cursor.fetchone()
            state = {
                "approval_id": str(approval_id),
                "agent_decision_id": str(governed_decision.id),
                "agent_run_id": str(run.id),
                "recommendation_id": str(governed_decision.recommendation_id)
                    if governed_decision.recommendation_id else None,
                "organization_id": str(governed_decision.organization_id),
                "required_role": required_role, "decision": decision,
                "decided_by_user_projection_id": str(user.id),
                "adminapps_user_id_snapshot": str(authority.adminapps_user_id),
                "actor_type": "human", "decided_at": decided_at.isoformat(),
                "comments_hash": canonical_hash(comments) if comments is not None else None,
                "authority_source": authority.authority_source,
                "trace_id": str(trace_id), "execution_authorized": False,
                "no_execution": True,
            }
            event_id, outbox_id = _event_and_outbox(
                using=self.using, tenant_id=authority.identity.tenant_id,
                event_type="approval.recorded", aggregate_type="approval",
                aggregate_id=approval_id, occurred_at=decided_at, trace_id=trace_id,
                payload=state, source="iso-smart-human-decision-gate",
            )
            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=authority.identity.tenant_id, stream_type="approval",
                stream_id=approval_id, actor_type="human", actor_id=actor_id,
                action="approval.recorded", entity_type="approval", entity_id=approval_id,
                trace_id=trace_id, occurred_at=decided_at, after_hash=canonical_hash(state),
                metadata={"event_id": str(event_id), "schema_version": 1,
                          "organization_id": str(governed_decision.organization_id),
                          "agent_decision_id": str(governed_decision.id),
                          "agent_run_id": str(run.id),
                          "recommendation_id": str(governed_decision.recommendation_id)
                              if governed_decision.recommendation_id else None,
                          "decision": decision, "required_role": required_role,
                          "comments_hash": state["comments_hash"],
                          "authority_source": authority.authority_source,
                          "execution_authorized": False},
            ))
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 12 Approval rollback after audit")
            return ApprovalResult(approval_id, decision, event_id, outbox_id, audit_id)
