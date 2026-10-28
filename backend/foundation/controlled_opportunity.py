"""Phase 16 fixed controlled Opportunity capabilities.

This module exposes no generic action/status/field/value mutation surface.  The
database functions own the exact governed forward and compensation semantics;
the Python boundary only binds trusted transaction-local identity and maps the
durable receipt result.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import UUID

from django.db import connections, transaction

from .action_authorization import _required
from .canonical import canonical_hash
from .tenant_context import (
    TrustedTenantIdentity,
    bind_trusted_tenant_context_in_transaction,
)


FORWARD_ACTION = "opportunity.defer_evaluation"
COMPENSATION_ACTION = "opportunity.resume_evaluation"
PRODUCT_POLICY_ID = "controlled-qms-action-policy/v1"


def opportunity_substantive_state(row):
    """Frozen Phase 16 stale-state contract (`controlled-opportunity-state-v1`)."""

    return {
        "canonicalization": "controlled-opportunity-state-v1",
        "tenant_id": str(row.tenant_id),
        "organization_id": str(row.organization_id),
        "lineage_id": str(row.lineage_id),
        "revision_id": str(row.id),
        "revision": row.revision,
        "process_id": str(row.process_id),
        "hypothesis": row.hypothesis,
        "benefit": row.benefit,
        "feasibility": row.feasibility,
        "status": row.status,
    }


def opportunity_substantive_fingerprint(row):
    return canonical_hash(opportunity_substantive_state(row))


@dataclass(frozen=True)
class ControlledOpportunityResult:
    execution_id: UUID
    action_plan_hash: str
    action_type: str
    opportunity_lineage_id: UUID
    before_revision_id: UUID
    after_revision_id: UUID
    domain_event_id: UUID
    replayed: bool
    receipt: dict


class ReconciliationOutcome(str, Enum):
    COMMITTED = "COMMITTED"
    NOT_COMMITTED = "NOT_COMMITTED"
    INCONSISTENT = "INCONSISTENT"


@dataclass(frozen=True)
class ControlledExecutionReconciliation:
    outcome: ReconciliationOutcome
    reason: str
    authorization_id: UUID
    action_plan_id: UUID
    action_plan_hash: str
    action_type: str
    idempotency_hash: str
    tenant_id: UUID
    organization_id: UUID
    trace_id: UUID
    execution_id: Optional[UUID]
    observed: dict
    reconciliation_audit_id: UUID
    receipt: Optional[dict]


class ControlledExecutionInconsistent(RuntimeError):
    """Durable evidence cannot safely prove commit or rollback."""


class ControlledOpportunityActionService:
    """One forward capability plus its separately authorized compensation path."""

    def __init__(self, *, using="executor"):
        self.using = using

    def _execution_function(self, action):
        recoverable = f"{action}_recoverable"
        with connections[self.using].cursor() as cursor:
            cursor.execute("SELECT to_regprocedure(%s)", [f"qms.{recoverable}(uuid,text)"])
            if cursor.fetchone()[0] is not None:
                return recoverable
        return action

    @staticmethod
    def _result(receipt):
        if isinstance(receipt, str):
            receipt = json.loads(receipt)
        return ControlledOpportunityResult(
            execution_id=UUID(receipt["execution_id"]),
            action_plan_hash=receipt["action_plan_hash"],
            action_type=receipt["action_type"],
            opportunity_lineage_id=UUID(receipt["opportunity_lineage_id"]),
            before_revision_id=UUID(receipt["before_revision_id"]),
            after_revision_id=UUID(receipt["after_revision_id"]),
            domain_event_id=UUID(receipt["domain_event_id"]),
            replayed=bool(receipt["replayed"]),
            receipt=receipt,
        )

    def _invoke(self, *, identity, authorization_id, idempotency_key, function_name):
        if not isinstance(identity, TrustedTenantIdentity):
            raise TypeError("identity must be a TrustedTenantIdentity")
        authorization_id = UUID(str(authorization_id))
        idempotency_key = _required(idempotency_key, "idempotency_key")
        with transaction.atomic(using=self.using, savepoint=False):
            bind_trusted_tenant_context_in_transaction(
                identity,
                actor_id="controlled-opportunity-executor",
                trace_id=authorization_id,
                using=self.using,
            )
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    f"SELECT qms.{function_name}(%s,%s)",
                    [str(authorization_id), idempotency_key],
                )
                receipt = cursor.fetchone()[0]
        return self._result(receipt)

    @staticmethod
    def _reconciliation(payload):
        if isinstance(payload, str):
            payload = json.loads(payload)
        return ControlledExecutionReconciliation(
            outcome=ReconciliationOutcome(payload["outcome"]),
            reason=payload["reason"],
            authorization_id=UUID(payload["authorization_id"]),
            action_plan_id=UUID(payload["action_plan_id"]),
            action_plan_hash=payload["action_plan_hash"],
            action_type=payload["action_type"],
            idempotency_hash=payload["idempotency_hash"],
            tenant_id=UUID(payload["tenant_id"]),
            organization_id=UUID(payload["organization_id"]),
            trace_id=UUID(payload["trace_id"]),
            execution_id=UUID(payload["execution_id"]) if payload["execution_id"] else None,
            observed=payload["observed"],
            reconciliation_audit_id=UUID(payload["reconciliation_audit_id"]),
            receipt=payload["receipt"],
        )

    def _reconcile(self, *, identity, authorization_id, idempotency_key, function_name):
        if not isinstance(identity, TrustedTenantIdentity):
            raise TypeError("identity must be a TrustedTenantIdentity")
        authorization_id = UUID(str(authorization_id))
        idempotency_key = _required(idempotency_key, "idempotency_key")
        with transaction.atomic(using=self.using, savepoint=False):
            bind_trusted_tenant_context_in_transaction(
                identity,
                actor_id="controlled-execution-reconciler",
                trace_id=authorization_id,
                using=self.using,
            )
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    f"SELECT qms.{function_name}(%s,%s)",
                    [str(authorization_id), idempotency_key],
                )
                payload = cursor.fetchone()[0]
        return self._reconciliation(payload)

    def reconcile_defer_evaluation(self, *, identity, authorization_id, idempotency_key):
        return self._reconcile(
            identity=identity,
            authorization_id=authorization_id,
            idempotency_key=idempotency_key,
            function_name="reconcile_defer_opportunity_evaluation",
        )

    def reconcile_resume_evaluation(self, *, identity, authorization_id, idempotency_key):
        return self._reconcile(
            identity=identity,
            authorization_id=authorization_id,
            idempotency_key=idempotency_key,
            function_name="reconcile_resume_opportunity_evaluation",
        )

    def recover_defer_after_ambiguous_commit(
        self, *, identity, authorization_id, idempotency_key
    ):
        """Reconcile first; execute once only when durable state proves rollback."""

        reconciliation = self.reconcile_defer_evaluation(
            identity=identity,
            authorization_id=authorization_id,
            idempotency_key=idempotency_key,
        )
        if reconciliation.outcome is ReconciliationOutcome.COMMITTED:
            return self._result(reconciliation.receipt)
        if reconciliation.outcome is ReconciliationOutcome.NOT_COMMITTED:
            return self.defer_evaluation(
                identity=identity,
                authorization_id=authorization_id,
                idempotency_key=idempotency_key,
            )
        raise ControlledExecutionInconsistent(
            f"controlled execution reconciliation failed closed: {reconciliation.reason}"
        )

    def defer_evaluation(self, *, identity, authorization_id, idempotency_key):
        return self._invoke(
            identity=identity,
            authorization_id=authorization_id,
            idempotency_key=idempotency_key,
            function_name=self._execution_function("defer_opportunity_evaluation"),
        )

    def resume_evaluation(self, *, identity, authorization_id, idempotency_key):
        return self._invoke(
            identity=identity,
            authorization_id=authorization_id,
            idempotency_key=idempotency_key,
            function_name=self._execution_function("resume_opportunity_evaluation"),
        )
