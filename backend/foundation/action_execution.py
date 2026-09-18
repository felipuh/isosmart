"""Phase 14 governed synthetic action execution.

The only executor in this module is an internal deterministic no-op.  The
start and terminal-result transactions are deliberately separate so a future
adapter is never forced into an open database transaction.
"""

import json
from dataclasses import dataclass
from uuid import UUID, uuid4

from django.db import connections
from django.db.models import Max
from django.utils import timezone

from .action_authorization import (
    IdempotencyConflict,
    PRECONDITION_RESULTS,
    _required,
    action_plan_canonical_state,
    resolve_effective_approval,
)
from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    ActionExecution,
    ActionExecutionReceipt,
    ActionPlan,
    AgentDecision,
    AgentRun,
    ExecutionAuthorization,
    DomainEvent,
    ModelPolicy,
    TransactionalOutbox,
    UserProjection,
)
from .tenant_context import TrustedTenantIdentity, trusted_tenant_context


EVENT_CONTRACTS = {
    "action_execution.started": 1,
    "action_execution.succeeded": 1,
    "action_execution.failed": 1,
}
EXECUTOR_ALLOWLIST = frozenset({ActionExecution.ExecutorType.SYNTHETIC_NOOP})


class ExecutionRejected(PermissionError):
    status_equivalent = 403

    def __init__(self, reason_code):
        super().__init__(reason_code)
        self.reason_code = reason_code


class SyntheticExecutionFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class SyntheticPreconditionEvaluator:
    """Trusted, side-effect-free Phase 14 evaluator fixture/boundary."""

    outcomes: dict
    authority_source: str = "trusted_server_side_synthetic_evaluator"

    def __post_init__(self):
        if self.authority_source != "trusted_server_side_synthetic_evaluator":
            raise ValueError("precondition evaluator must be trusted and server-side")
        if not isinstance(self.outcomes, dict):
            raise ValueError("precondition outcomes must be an object")
        if any(value not in PRECONDITION_RESULTS for value in self.outcomes.values()):
            raise ValueError("invalid precondition outcome")

    def evaluate(self, action_plan):
        expected = {item["identity"] for item in action_plan.preconditions}
        if set(self.outcomes) != expected:
            raise ExecutionRejected("precondition_evaluation_incomplete")
        return dict(self.outcomes)


@dataclass(frozen=True)
class ExecutionPrincipalContext:
    identity: TrustedTenantIdentity
    precondition_evaluator: SyntheticPreconditionEvaluator
    principal_type: str = "execution_service"
    authority_source: str = "trusted_backend_execution_service"
    actor_id: str = "synthetic-action-executor"
    executor_type: str = ActionExecution.ExecutorType.SYNTHETIC_NOOP

    def __post_init__(self):
        if self.principal_type != "execution_service":
            raise ValueError("execution requires the execution-service principal")
        if self.authority_source != "trusted_backend_execution_service":
            raise ValueError("execution authority must be server-resolved")
        if self.executor_type not in EXECUTOR_ALLOWLIST:
            raise ValueError("executor is not allow-listed")
        _required(self.actor_id, "actor_id")
        if not isinstance(self.precondition_evaluator, SyntheticPreconditionEvaluator):
            raise TypeError("a trusted synthetic precondition evaluator is required")


@dataclass(frozen=True)
class ExecutorInvocation:
    execution_id: UUID
    action_plan_id: UUID
    action_plan_hash: str
    action_type: str
    target_type: str
    target_id: str


@dataclass(frozen=True)
class ExecutorResult:
    outcome: str
    result: dict


class SyntheticNoOpExecutor:
    executor_type = ActionExecution.ExecutorType.SYNTHETIC_NOOP

    def __init__(self, *, force_failure=False):
        self.force_failure = bool(force_failure)

    def execute(self, invocation):
        if not isinstance(invocation, ExecutorInvocation):
            raise TypeError("executor invocation contract is required")
        if not invocation.action_plan_hash or len(invocation.action_plan_hash) != 64:
            raise ValueError("exact ActionPlan hash is required")
        if self.force_failure:
            raise SyntheticExecutionFailure("forced_synthetic_failure")
        result = {
            "classification": "NON-PRODUCTION",
            "mode": "SYNTHETIC",
            "effect": "NO-OP",
            "business_state_changed": False,
            "execution_id": str(invocation.execution_id),
            "action_plan_id": str(invocation.action_plan_id),
            "action_plan_hash": invocation.action_plan_hash,
            "executor": self.executor_type,
            "message": "Authorized synthetic no-op executor completed; no QMS action occurred.",
        }
        return ExecutorResult(ActionExecutionReceipt.Outcome.SYNTHETIC_NOOP_SUCCEEDED, result)


class ExecutorRegistry:
    """Closed Phase 14 registry; no dynamic loading, providers, tools, or adapters."""

    def __init__(self, executors):
        self._executors = dict(executors)
        if set(self._executors) != set(EXECUTOR_ALLOWLIST):
            raise ValueError("Phase 14 registry must contain synthetic_noop only")
        if any(not isinstance(value, SyntheticNoOpExecutor) for value in self._executors.values()):
            raise TypeError("Phase 14 accepts SyntheticNoOpExecutor only")

    @classmethod
    def synthetic_only(cls, *, force_failure=False):
        executor = SyntheticNoOpExecutor(force_failure=force_failure)
        return cls({executor.executor_type: executor})

    def resolve(self, executor_type):
        try:
            return self._executors[executor_type]
        except KeyError as exc:
            raise ExecutionRejected("executor_not_allowlisted") from exc


@dataclass(frozen=True)
class ActionExecutionResult:
    execution_id: UUID
    receipt_id: UUID | None
    status: str
    replayed: bool
    action_plan_hash: str


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


def _plan_hash(plan):
    return canonical_hash(action_plan_canonical_state(
        organization_id=plan.organization_id,
        agent_decision_id=plan.agent_decision_id,
        recommendation_id=plan.recommendation_id,
        action_type=plan.action_type,
        target_type=plan.target_type,
        target_id=plan.target_id,
        parameters=plan.parameters,
        impact=plan.impact,
        reversibility=plan.reversibility,
        preconditions=plan.preconditions,
        dry_run_supported=plan.dry_run_supported,
        required_autonomy=plan.required_autonomy,
    ))


def _reject_unless(condition, reason_code):
    if not condition:
        raise ExecutionRejected(reason_code)


class ActionExecutionService:
    def __init__(self, *, using="executor", registry=None):
        self.using = using
        self.registry = registry or ExecutorRegistry.synthetic_only()

    def _revalidate(self, *, principal, authorization_id):
        authorization = ExecutionAuthorization.objects.using(self.using).get(id=authorization_id)
        plan = ActionPlan.objects.using(self.using).get(id=authorization.action_plan_id)
        decision = AgentDecision.objects.using(self.using).get(id=plan.agent_decision_id)
        run = AgentRun.objects.using(self.using).get(id=decision.agent_run_id)
        policy = ModelPolicy.objects.using(self.using).get(id=run.model_policy_id)
        dry_run = authorization.dry_run

        recomputed_hash = _plan_hash(plan)
        _reject_unless(authorization.outcome == ExecutionAuthorization.Outcome.AUTHORIZED,
                       "authorization_outcome_invalid")
        _reject_unless(authorization.tenant_id == principal.identity.tenant_id,
                       "authorization_tenant_mismatch")
        _reject_unless(authorization.organization_id == plan.organization_id == decision.organization_id,
                       "organization_mismatch")
        _reject_unless(authorization.action_plan_id == plan.id,
                       "authorization_plan_mismatch")
        _reject_unless(recomputed_hash == plan.action_plan_hash == authorization.action_plan_hash,
                       "action_plan_hash_mismatch")
        _reject_unless(authorization.agent_decision_id == decision.id and
                       authorization.recommendation_id == plan.recommendation_id == decision.recommendation_id,
                       "decision_recommendation_mismatch")
        _reject_unless(authorization.agent_run_id == run.id and
                       authorization.agent_definition_id == run.agent_definition_id and
                       authorization.model_policy_id == run.model_policy_id,
                       "frozen_policy_provenance_mismatch")
        _reject_unless(policy.status == ModelPolicy.Status.PUBLISHED and
                       run.model_policy_id == run.agent_definition.model_policy_id,
                       "model_policy_invalid")
        _reject_unless(plan.required_autonomy >= 3 and
                       plan.required_autonomy <= authorization.effective_autonomy_ceiling and
                       plan.required_autonomy <= run.effective_autonomy_ceiling and
                       plan.required_autonomy <= decision.decision_autonomy,
                       "autonomy_ceiling_denied")
        if plan.required_autonomy == 4:
            _reject_unless(plan.reversibility == ActionPlan.Reversibility.REVERSIBLE and
                           plan.impact != ActionPlan.Impact.HIGH,
                           "a4_guardrail_denied")
        _reject_unless(authorization.impact == plan.impact and
                       authorization.reversibility == plan.reversibility,
                       "authorization_classification_mismatch")

        approval, approval_error = resolve_effective_approval(
            using=self.using, agent_decision_id=decision.id,
        )
        _reject_unless(approval_error is None and approval is not None and
                       approval.id == authorization.effective_approval_id,
                       approval_error or "effective_approval_mismatch")
        actor = UserProjection.objects.using(self.using).filter(
            id=approval.decided_by_id,
            adminapps_user_id=approval.adminapps_user_id_snapshot,
            lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
        ).first()
        _reject_unless(actor is not None and
                       approval.required_role == policy.human_gate_rules.get("required_role"),
                       "approval_authority_unverifiable")

        _reject_unless(dry_run.action_plan_id == plan.id and
                       dry_run.action_plan_hash == recomputed_hash and
                       dry_run.validation_status == "passed",
                       "dry_run_consistency_failed")
        outcomes = principal.precondition_evaluator.evaluate(plan)
        _reject_unless(all(not item.get("required", True) or
                           outcomes.get(item["identity"]) == "satisfied"
                           for item in plan.preconditions),
                       "required_precondition_not_satisfied")
        return authorization, plan, outcomes

    def execute_authorized_action(self, *, principal, authorization_id,
                                  idempotency_key, trace_id,
                                  retry_of_execution_id=None,
                                  fail_start_before_commit=False,
                                  fail_completion_before_commit=False):
        if not isinstance(principal, ExecutionPrincipalContext):
            raise TypeError("principal must be a server-resolved ExecutionPrincipalContext")
        trace_id = UUID(str(trace_id))
        idempotency_key = _required(idempotency_key, "idempotency_key")

        with trusted_tenant_context(principal.identity, actor_id=principal.actor_id,
                                    trace_id=trace_id, using=self.using):
            authorization, plan, precondition_outcomes = self._revalidate(
                principal=principal, authorization_id=authorization_id,
            )
            existing = ActionExecution.objects.using(self.using).filter(
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                if (existing.execution_authorization_id != authorization.id or
                        existing.action_plan_hash != plan.action_plan_hash):
                    raise IdempotencyConflict(
                        "execution idempotency key is bound to another authorization or plan hash"
                    )
                receipt = ActionExecutionReceipt.objects.using(self.using).filter(
                    action_execution_id=existing.id,
                ).first()
                return ActionExecutionResult(existing.id, receipt.id if receipt else None,
                                             existing.status, True,
                                             existing.action_plan_hash)

            retry_of = None
            attempt_number = 1
            if retry_of_execution_id is not None:
                retry_of = ActionExecution.objects.using(self.using).get(id=retry_of_execution_id)
                _reject_unless(retry_of.status == ActionExecution.Status.FAILED,
                               "retry_requires_failed_execution")
                _reject_unless(retry_of.execution_authorization_id == authorization.id and
                               retry_of.action_plan_hash == plan.action_plan_hash,
                               "retry_provenance_mismatch")
                attempt_number = retry_of.attempt_number + 1

            started_at = timezone.now()
            execution_id = uuid4()
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT qms.foundation_0014_start_action_execution(" +
                    ",".join(["%s"] * 9 + ["%s::integer", "%s::jsonb"] + ["%s"] * 4) + ")",
                    [str(execution_id), str(principal.identity.tenant_id),
                     str(plan.organization_id), str(authorization.id), str(plan.id),
                     plan.action_plan_hash, principal.executor_type, "running",
                     str(retry_of.id) if retry_of else None, attempt_number,
                     json.dumps(precondition_outcomes), idempotency_key, str(trace_id),
                     started_at, principal.actor_id],
                )
                cursor.fetchone()
            start_state = {
                "execution_id": str(execution_id),
                "authorization_id": str(authorization.id),
                "action_plan_id": str(plan.id),
                "action_plan_hash": plan.action_plan_hash,
                "executor": principal.executor_type,
                "status": "running",
                "attempt": attempt_number,
                "retry_of_execution_id": str(retry_of.id) if retry_of else None,
                "precondition_results": precondition_outcomes,
                "synthetic_only": True,
                "no_business_side_effect": True,
            }
            event_id, _ = _event_and_outbox(
                using=self.using, tenant_id=principal.identity.tenant_id,
                event_type="action_execution.started", aggregate_type="action_execution",
                aggregate_id=execution_id, occurred_at=started_at, trace_id=trace_id,
                payload=start_state, source="iso-smart-synthetic-execution",
            )
            AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=principal.identity.tenant_id, stream_type="action_execution",
                stream_id=execution_id, actor_type=principal.principal_type,
                actor_id=principal.actor_id, action="action_execution.started",
                entity_type="action_execution", entity_id=execution_id,
                trace_id=trace_id, occurred_at=started_at,
                after_hash=canonical_hash(start_state),
                metadata={
                    "event_id": str(event_id), "execution_id": str(execution_id),
                    "governance_artifact_id": str(authorization.id),
                    "action_plan_id": str(plan.id), "action_plan_hash": plan.action_plan_hash,
                    "executor": principal.executor_type, "status": "running",
                    "attempt": attempt_number, "precondition_results": precondition_outcomes,
                    "synthetic_only": True, "no_business_side_effect": True,
                    "idempotency_key_hash": canonical_hash(idempotency_key),
                },
            ))
            if fail_start_before_commit:
                raise RuntimeError("deliberate Phase 14 start rollback")

        invocation = ExecutorInvocation(
            execution_id=execution_id, action_plan_id=plan.id,
            action_plan_hash=plan.action_plan_hash, action_type=plan.action_type,
            target_type=plan.target_type, target_id=plan.target_id,
        )
        executor = self.registry.resolve(principal.executor_type)
        try:
            executor_result = executor.execute(invocation)
            terminal_status = ActionExecution.Status.SUCCEEDED
            receipt_outcome = executor_result.outcome
            result = executor_result.result
        except Exception as exc:
            terminal_status = ActionExecution.Status.FAILED
            receipt_outcome = ActionExecutionReceipt.Outcome.SYNTHETIC_NOOP_FAILED
            result = {
                "classification": "NON-PRODUCTION",
                "mode": "SYNTHETIC",
                "effect": "NO-OP",
                "business_state_changed": False,
                "execution_id": str(execution_id),
                "action_plan_id": str(plan.id),
                "action_plan_hash": plan.action_plan_hash,
                "executor": principal.executor_type,
                "error_code": "forced_synthetic_failure" if isinstance(exc, SyntheticExecutionFailure)
                else "synthetic_executor_failure",
            }

        completed_at = timezone.now()
        receipt_id = uuid4()
        result = json.loads(canonical_json(result))["value"]
        result_hash = canonical_hash(result)
        with trusted_tenant_context(principal.identity, actor_id=principal.actor_id,
                                    trace_id=trace_id, using=self.using):
            # Every retry/completion revalidates the same frozen chain again.
            self._revalidate(principal=principal, authorization_id=authorization_id)
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT qms.foundation_0014_complete_action_execution(" +
                    ",".join(["%s"] * 9 + ["%s::jsonb"] + ["%s"] * 5) + ")",
                    [str(execution_id), str(receipt_id),
                     str(principal.identity.tenant_id), str(plan.organization_id),
                     terminal_status, receipt_outcome, principal.executor_type,
                     plan.action_plan_hash, result_hash, json.dumps(result),
                     str(trace_id), started_at, completed_at, principal.actor_id,
                     "phase14"],
                )
                cursor.fetchone()
            event_type = f"action_execution.{terminal_status}"
            terminal_state = {
                "execution_id": str(execution_id), "receipt_id": str(receipt_id),
                "authorization_id": str(authorization.id), "action_plan_id": str(plan.id),
                "action_plan_hash": plan.action_plan_hash,
                "executor": principal.executor_type, "status": terminal_status,
                "attempt": attempt_number, "result_hash": result_hash,
                "synthetic_only": True, "no_business_side_effect": True,
                "effectiveness_claimed": False,
            }
            event_id, _ = _event_and_outbox(
                using=self.using, tenant_id=principal.identity.tenant_id,
                event_type=event_type, aggregate_type="action_execution",
                aggregate_id=execution_id, occurred_at=completed_at, trace_id=trace_id,
                payload=terminal_state, source="iso-smart-synthetic-execution",
            )
            AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=principal.identity.tenant_id, stream_type="action_execution",
                stream_id=execution_id, actor_type=principal.principal_type,
                actor_id=principal.actor_id, action=event_type,
                entity_type="action_execution", entity_id=execution_id,
                trace_id=trace_id, occurred_at=completed_at,
                after_hash=canonical_hash(terminal_state),
                metadata={
                    "event_id": str(event_id), "execution_id": str(execution_id),
                    "receipt_id": str(receipt_id),
                    "governance_artifact_id": str(authorization.id),
                    "action_plan_id": str(plan.id), "action_plan_hash": plan.action_plan_hash,
                    "executor": principal.executor_type, "status": terminal_status,
                    "attempt": attempt_number, "result_hash": result_hash,
                    "synthetic_only": True, "no_business_side_effect": True,
                    "effectiveness_claimed": False,
                },
            ))
            if fail_completion_before_commit:
                raise RuntimeError("deliberate Phase 14 completion rollback")

        return ActionExecutionResult(execution_id, receipt_id, terminal_status,
                                     False, plan.action_plan_hash)
