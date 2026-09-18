"""Phase 13 prepared-action, dry-run, and execution-authorization contracts.

This module deliberately contains no action executor, adapter, provider call, or
business-object mutation.  It only records immutable preparation/governance
artifacts.
"""

import json
from dataclasses import dataclass
from uuid import UUID, uuid4

from django.db import connections
from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    ActionPlan, ActionPlanDryRun, AgentDecision, AgentRun, Approval, DomainEvent,
    ExecutionAuthorization, ModelPolicy, TransactionalOutbox, UserProjection,
)
from .tenant_context import TrustedTenantIdentity, trusted_tenant_context


EVENT_CONTRACTS = {
    "action_plan.prepared": 1,
    "action_plan.dry_run_completed": 1,
    "execution_authorization.granted": 1,
    "execution_authorization.denied": 1,
}
PRECONDITION_RESULTS = {"satisfied", "not_satisfied", "unknown"}


class IdempotencyConflict(ValueError):
    status_equivalent = 409


class AuthorizationDenied(PermissionError):
    """Raised only by callers that opt to convert a denied result to an error."""

    status_equivalent = 403


@dataclass(frozen=True)
class ExecutionAuthorizerContext:
    identity: TrustedTenantIdentity
    principal_type: str = "governance_service"
    authority_source: str = "trusted_backend_policy_evaluator"
    actor_id: str = "execution-authorization-evaluator"

    def __post_init__(self):
        if self.principal_type != "governance_service":
            raise ValueError("execution authorization requires the governance-service principal")
        if self.authority_source != "trusted_backend_policy_evaluator":
            raise ValueError("authorization authority must come from the trusted backend")
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("authorization actor identity is required")


@dataclass(frozen=True)
class ActionPlanResult:
    action_plan_id: UUID
    action_plan_hash: str
    replayed: bool
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID


@dataclass(frozen=True)
class DryRunResult:
    dry_run_id: UUID
    action_plan_hash: str
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID


@dataclass(frozen=True)
class AuthorizationResult:
    outcome: str
    authorization_id: UUID | None
    reason_code: str | None
    replayed: bool
    event_id: UUID | None
    outbox_id: UUID | None
    audit_id: UUID


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _json_object(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _preconditions(value):
    if not isinstance(value, (list, tuple)):
        raise ValueError("preconditions must be a list")
    normalized = []
    identities = set()
    for index, item in enumerate(value):
        item = _json_object(item, f"preconditions[{index}]")
        identity = _required(item.get("identity"), f"preconditions[{index}].identity")
        if identity in identities:
            raise ValueError("precondition identities must be unique")
        identities.add(identity)
        required = item.get("required", True)
        if not isinstance(required, bool):
            raise ValueError(f"preconditions[{index}].required must be boolean")
        if "expected" not in item:
            raise ValueError(f"preconditions[{index}].expected is required")
        normalized.append({
            "identity": identity,
            "type": _required(item.get("type"), f"preconditions[{index}].type"),
            "expected": item["expected"],
            "required": required,
            "source_reference": item.get("source_reference"),
        })
    return normalized


def _autonomy(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 4:
        raise ValueError("required_autonomy must be an integer from A0 through A4")
    return value


def action_plan_canonical_state(*, organization_id, agent_decision_id, recommendation_id,
                                action_type, target_type, target_id, parameters, impact,
                                reversibility, preconditions, dry_run_supported,
                                required_autonomy):
    """Stable v1 material representation; timestamps and idempotency are excluded."""
    return {
        "canonicalization": "iso-smart-action-plan-v1",
        "organization_id": str(organization_id),
        "agent_decision_id": str(agent_decision_id),
        "recommendation_id": str(recommendation_id),
        "action_type": action_type,
        "target": {"type": target_type, "id": target_id},
        "parameters": parameters,
        "impact": impact,
        "reversibility": reversibility,
        "preconditions": preconditions,
        "dry_run_supported": dry_run_supported,
        "required_autonomy": f"A{required_autonomy}",
    }


def resolve_effective_approval(*, using, agent_decision_id):
    """Return the sole latest outcome, failing closed on a conflicting time tie."""
    history = list(
        Approval.objects.using(using).filter(agent_decision_id=agent_decision_id)
        .order_by("decided_at", "created_at", "id")
    )
    if not history:
        return None, "approval_missing"
    latest_time = history[-1].decided_at
    tied = [row for row in history if row.decided_at == latest_time]
    if len({row.decision for row in tied}) != 1:
        return None, "approval_history_ambiguous"
    effective = tied[-1]
    if effective.decision != Approval.Decision.APPROVE:
        return effective, f"effective_approval_{effective.decision}"
    return effective, None


def _event_and_outbox(*, using, tenant_id, event_type, aggregate_type, aggregate_id,
                      occurred_at, trace_id, payload, source):
    payload = json.loads(canonical_json(payload))["value"]
    version = (DomainEvent.objects.using(using).filter(
        aggregate_type=aggregate_type, aggregate_id=aggregate_id,
    ).aggregate(value=Max("aggregate_version"))["value"] or 0) + 1
    event_id = uuid4()
    DomainEvent.objects.using(using).create(
        event_id=event_id, tenant_id=tenant_id, event_type=event_type,
        schema_version=EVENT_CONTRACTS[event_type], aggregate_type=aggregate_type,
        aggregate_id=aggregate_id, aggregate_version=version, occurred_at=occurred_at,
        trace_id=trace_id, source=source, payload=payload,
        payload_hash=canonical_hash(payload),
    )
    outbox = TransactionalOutbox.objects.using(using).create(
        tenant_id=tenant_id, domain_event_id=event_id,
        status=TransactionalOutbox.Status.PENDING, publish_attempts=0,
        available_at=occurred_at,
    )
    return event_id, outbox.id


class ActionPreparationService:
    def __init__(self, *, using="worker"):
        self.using = using

    def prepare_action_plan(self, *, identity, agent_decision_id, action_type,
                            target_type, target_id, parameters, impact, reversibility,
                            preconditions, dry_run_supported, required_autonomy,
                            idempotency_key, actor_id, trace_id, fail_before_commit=False):
        trace_id = UUID(str(trace_id))
        if impact not in ActionPlan.Impact.values:
            raise ValueError("impact must be standard or high")
        if reversibility not in ActionPlan.Reversibility.values:
            raise ValueError("reversibility must be reversible or irreversible")
        if not isinstance(dry_run_supported, bool):
            raise ValueError("dry_run_supported must be boolean")
        parameters = _json_object(parameters, "parameters")
        preconditions = _preconditions(preconditions)
        required_autonomy = _autonomy(required_autonomy)
        idempotency_key = _required(idempotency_key, "idempotency_key")
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            decision = AgentDecision.objects.using(self.using).get(id=agent_decision_id)
            if decision.recommendation_id is None:
                raise ValueError("ActionPlan requires the exact governed Recommendation")
            state = action_plan_canonical_state(
                organization_id=decision.organization_id, agent_decision_id=decision.id,
                recommendation_id=decision.recommendation_id,
                action_type=_required(action_type, "action_type"),
                target_type=_required(target_type, "target_type"),
                target_id=_required(target_id, "target_id"), parameters=parameters,
                impact=impact, reversibility=reversibility, preconditions=preconditions,
                dry_run_supported=dry_run_supported, required_autonomy=required_autonomy,
            )
            plan_hash = canonical_hash(state)
            existing = ActionPlan.objects.using(self.using).filter(idempotency_key=idempotency_key).first()
            if existing:
                if existing.action_plan_hash != plan_hash:
                    raise IdempotencyConflict("idempotency key is already bound to another ActionPlan hash")
                return ActionPlanResult(existing.id, plan_hash, True, UUID(int=0), UUID(int=0), UUID(int=0))
            occurred_at = timezone.now()
            plan = ActionPlan.objects.using(self.using).create(
                id=uuid4(), tenant_id=identity.tenant_id,
                organization_id=decision.organization_id, agent_decision_id=decision.id,
                recommendation_id=decision.recommendation_id, action_type=state["action_type"],
                target_type=state["target"]["type"], target_id=state["target"]["id"],
                parameters=parameters, impact=impact, reversibility=reversibility,
                preconditions=preconditions, dry_run_supported=dry_run_supported,
                required_autonomy=required_autonomy, action_plan_hash=plan_hash,
                idempotency_key=idempotency_key, trace_id=trace_id,
            )
            payload = dict(state, action_plan_id=str(plan.id), action_plan_hash=plan_hash,
                           no_execution=True)
            event_id, outbox_id = _event_and_outbox(
                using=self.using, tenant_id=identity.tenant_id,
                event_type="action_plan.prepared", aggregate_type="action_plan",
                aggregate_id=plan.id, occurred_at=occurred_at, trace_id=trace_id,
                payload=payload, source="iso-smart-action-preparation",
            )
            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=identity.tenant_id, stream_type="action_plan", stream_id=plan.id,
                actor_type="worker", actor_id=str(actor_id), action="action_plan.prepared",
                entity_type="action_plan", entity_id=plan.id, trace_id=trace_id,
                occurred_at=occurred_at, after_hash=plan_hash,
                metadata={"event_id": str(event_id), "action_plan_hash": plan_hash,
                          "idempotency_key_hash": canonical_hash(idempotency_key),
                          "no_execution": True},
            ))
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 13 ActionPlan rollback after audit")
            return ActionPlanResult(plan.id, plan_hash, False, event_id, outbox_id, audit_id)

    def run_action_plan_dry_run(self, *, identity, action_plan_id,
                                expected_affected_objects, intended_state_delta,
                                validation_status, precondition_results, impact_summary,
                                actor_id, trace_id, fail_before_commit=False):
        trace_id = UUID(str(trace_id))
        if validation_status not in {"passed", "failed"}:
            raise ValueError("validation_status must be passed or failed")
        if not isinstance(expected_affected_objects, list):
            raise ValueError("expected_affected_objects must be a list")
        intended_state_delta = _json_object(intended_state_delta, "intended_state_delta")
        impact_summary = _json_object(impact_summary, "impact_summary")
        if not isinstance(precondition_results, list):
            raise ValueError("precondition_results must be a list")
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            plan = ActionPlan.objects.using(self.using).get(id=action_plan_id)
            expected = {item["identity"] for item in plan.preconditions}
            observed = set()
            for index, result in enumerate(precondition_results):
                result = _json_object(result, f"precondition_results[{index}]")
                identity_key = _required(result.get("identity"), f"precondition_results[{index}].identity")
                if result.get("status") not in PRECONDITION_RESULTS:
                    raise ValueError("precondition result must be satisfied, not_satisfied, or unknown")
                observed.add(identity_key)
            if observed != expected:
                raise ValueError("dry-run must report every exact ActionPlan precondition once")
            occurred_at = timezone.now()
            dry_run = ActionPlanDryRun.objects.using(self.using).create(
                id=uuid4(), tenant_id=identity.tenant_id, organization_id=plan.organization_id,
                action_plan_id=plan.id, action_plan_hash=plan.action_plan_hash,
                expected_affected_objects=expected_affected_objects,
                intended_state_delta=intended_state_delta, validation_status=validation_status,
                precondition_results=precondition_results, impact_summary=impact_summary,
                trace_id=trace_id,
            )
            state = {"dry_run_id": str(dry_run.id), "action_plan_id": str(plan.id),
                     "action_plan_hash": plan.action_plan_hash,
                     "expected_affected_objects": expected_affected_objects,
                     "intended_state_delta": intended_state_delta,
                     "validation_status": validation_status,
                     "precondition_results": precondition_results,
                     "impact_summary": impact_summary, "simulation_only": True,
                     "no_business_state_write": True}
            event_id, outbox_id = _event_and_outbox(
                using=self.using, tenant_id=identity.tenant_id,
                event_type="action_plan.dry_run_completed", aggregate_type="action_plan_dry_run",
                aggregate_id=dry_run.id, occurred_at=occurred_at, trace_id=trace_id,
                payload=state, source="iso-smart-action-simulation",
            )
            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=identity.tenant_id, stream_type="action_plan_dry_run",
                stream_id=dry_run.id, actor_type="worker", actor_id=str(actor_id),
                action="action_plan.dry_run_completed", entity_type="action_plan_dry_run",
                entity_id=dry_run.id, trace_id=trace_id, occurred_at=occurred_at,
                after_hash=canonical_hash(state),
                metadata={"event_id": str(event_id), "action_plan_hash": plan.action_plan_hash,
                          "simulation_only": True, "no_business_state_write": True},
            ))
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 13 dry-run rollback after audit")
            return DryRunResult(dry_run.id, plan.action_plan_hash, event_id, outbox_id, audit_id)


class ExecutionAuthorizationService:
    def __init__(self, *, using="execution_authorizer"):
        self.using = using

    def evaluate_execution_authorization(self, *, authority, action_plan_id, dry_run_id,
                                         idempotency_key, trace_id,
                                         fail_before_commit=False):
        if not isinstance(authority, ExecutionAuthorizerContext):
            raise TypeError("authority must be a server-resolved ExecutionAuthorizerContext")
        trace_id = UUID(str(trace_id))
        idempotency_key = _required(idempotency_key, "idempotency_key")
        with trusted_tenant_context(authority.identity, actor_id=authority.actor_id,
                                    trace_id=trace_id, using=self.using):
            plan = ActionPlan.objects.using(self.using).get(id=action_plan_id)
            dry_run = ActionPlanDryRun.objects.using(self.using).get(id=dry_run_id)
            request_state = {"operation": "evaluate_execution_authorization",
                             "action_plan_id": str(plan.id),
                             "action_plan_hash": plan.action_plan_hash,
                             "dry_run_id": str(dry_run.id),
                             "dry_run_plan_hash": dry_run.action_plan_hash}
            request_hash = canonical_hash(request_state)
            existing = ExecutionAuthorization.objects.using(self.using).filter(
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                if existing.authorization_request_hash != request_hash:
                    raise IdempotencyConflict("authorization idempotency key is bound to another request")
                return AuthorizationResult("authorized", existing.id, None, True,
                                           None, None, UUID(int=0))
            decision = AgentDecision.objects.using(self.using).get(id=plan.agent_decision_id)
            run = AgentRun.objects.using(self.using).get(id=decision.agent_run_id)
            policy = ModelPolicy.objects.using(self.using).get(id=run.model_policy_id)
            approval, denial = resolve_effective_approval(
                using=self.using, agent_decision_id=decision.id,
            )
            if dry_run.action_plan_id != plan.id or dry_run.action_plan_hash != plan.action_plan_hash:
                denial = "dry_run_plan_hash_mismatch"
            elif decision.recommendation_id != plan.recommendation_id:
                denial = "recommendation_decision_mismatch"
            elif plan.required_autonomy > run.effective_autonomy_ceiling or plan.required_autonomy > decision.decision_autonomy:
                denial = "policy_ceiling_exceeded"
            elif dry_run.validation_status != "passed":
                denial = "dry_run_validation_failed"
            else:
                results = {item["identity"]: item["status"] for item in dry_run.precondition_results}
                if any(item.get("required", True) and results.get(item["identity"]) != "satisfied"
                       for item in plan.preconditions):
                    denial = "required_precondition_not_satisfied"
            if approval is not None:
                actor = UserProjection.objects.using(self.using).filter(
                    id=approval.decided_by_id,
                    adminapps_user_id=approval.adminapps_user_id_snapshot,
                    lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
                ).first()
                required_role = policy.human_gate_rules.get("required_role")
                if actor is None or approval.required_role != required_role:
                    denial = "approval_authority_unverifiable"
            if (plan.impact == ActionPlan.Impact.HIGH or
                    plan.reversibility == ActionPlan.Reversibility.IRREVERSIBLE) and approval is None:
                denial = denial or "human_gate_cannot_be_bypassed"
            occurred_at = timezone.now()
            if denial:
                audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                    tenant_id=authority.identity.tenant_id,
                    stream_type="execution_authorization_evaluation", stream_id=uuid4(),
                    actor_type=authority.principal_type, actor_id=authority.actor_id,
                    action="execution_authorization.denied", entity_type="action_plan",
                    entity_id=plan.id, trace_id=trace_id, occurred_at=occurred_at,
                    after_hash=request_hash,
                    metadata={"action_plan_id": str(plan.id),
                              "action_plan_hash": plan.action_plan_hash,
                              "dry_run_id": str(dry_run.id), "reason_code": denial,
                              "idempotency_key_hash": canonical_hash(idempotency_key),
                              "no_execution": True},
                ))
                return AuthorizationResult("denied", None, denial, False, None, None, audit_id)
            authorization_id = uuid4()
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT qms.foundation_0013_grant_execution_authorization(" +
                    ",".join(["%s"] * 12 + ["%s::smallint"] + ["%s"] * 8) + ")",
                    [str(authorization_id), str(authority.identity.tenant_id),
                     str(plan.organization_id), str(plan.id), plan.action_plan_hash,
                     str(dry_run.id), str(decision.id), str(plan.recommendation_id),
                     str(approval.id), str(run.id), str(run.agent_definition_id),
                     str(run.model_policy_id), run.effective_autonomy_ceiling, plan.impact,
                     plan.reversibility, "authorized", idempotency_key, request_hash,
                     authority.principal_type, authority.actor_id, str(trace_id)],
                )
                cursor.fetchone()
            state = dict(request_state, authorization_id=str(authorization_id),
                         effective_approval_id=str(approval.id), agent_run_id=str(run.id),
                         agent_definition_id=str(run.agent_definition_id),
                         model_policy_id=str(run.model_policy_id), impact=plan.impact,
                         reversibility=plan.reversibility, outcome="authorized",
                         effective_autonomy_ceiling=f"A{run.effective_autonomy_ceiling}",
                         authorized_at=occurred_at.isoformat(), no_execution=True)
            event_id, outbox_id = _event_and_outbox(
                using=self.using, tenant_id=authority.identity.tenant_id,
                event_type="execution_authorization.granted",
                aggregate_type="execution_authorization", aggregate_id=authorization_id,
                occurred_at=occurred_at, trace_id=trace_id, payload=state,
                source="iso-smart-execution-authorization",
            )
            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=authority.identity.tenant_id, stream_type="execution_authorization",
                stream_id=authorization_id, actor_type=authority.principal_type,
                actor_id=authority.actor_id, action="execution_authorization.granted",
                entity_type="execution_authorization", entity_id=authorization_id,
                trace_id=trace_id, occurred_at=occurred_at, after_hash=canonical_hash(state),
                metadata={"event_id": str(event_id), "action_plan_hash": plan.action_plan_hash,
                          "effective_approval_id": str(approval.id),
                          "model_policy_id": str(run.model_policy_id),
                          "request_hash": request_hash,
                          "idempotency_key_hash": canonical_hash(idempotency_key),
                          "no_execution": True},
            ))
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 13 authorization rollback after audit")
            return AuthorizationResult("authorized", authorization_id, None, False,
                                       event_id, outbox_id, audit_id)
