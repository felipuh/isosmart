"""Material Phase 5 commands with one business/event/outbox/audit transaction."""

from uuid import UUID, uuid4

from django.db import connections, transaction
from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    DomainEvent,
    Objective,
    Opportunity,
    Organization,
    Process,
    Risk,
    TransactionalOutbox,
)
from .qms_context import MaterialMutationResult
from .tenant_context import trusted_tenant_context


EVENT_CONTRACTS = {
    "risk.created": 1,
    "risk.revised": 1,
    "opportunity.created": 1,
    "opportunity.revised": 1,
    "opportunity.status_changed": 1,
    "objective.created": 1,
    "objective.revised": 1,
    "objective.status_changed": 1,
}

_UNSET = object()


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


class RiskOpportunityObjectiveCommandService:
    def __init__(self, *, using="app"):
        self.using = using

    def _emit(self, *, identity, aggregate_type, aggregate_id, event_type, payload,
              actor_id, trace_id, occurred_at, before=None, after=None):
        normalized_payload = __import__("json").loads(canonical_json(payload))["value"]
        version = (
            DomainEvent.objects.using(self.using)
            .filter(aggregate_type=aggregate_type, aggregate_id=aggregate_id)
            .aggregate(value=Max("aggregate_version"))["value"] or 0
        ) + 1
        event_id = uuid4()
        DomainEvent.objects.using(self.using).create(
            event_id=event_id,
            tenant_id=identity.tenant_id,
            event_type=event_type,
            schema_version=EVENT_CONTRACTS[event_type],
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            aggregate_version=version,
            occurred_at=occurred_at,
            trace_id=trace_id,
            source="iso-smart-qms",
            payload=normalized_payload,
            payload_hash=canonical_hash(normalized_payload),
        )
        outbox = TransactionalOutbox.objects.using(self.using).create(
            tenant_id=identity.tenant_id,
            domain_event_id=event_id,
            status=TransactionalOutbox.Status.PENDING,
            publish_attempts=0,
            available_at=occurred_at,
        )
        audit_id = AuditWriterService(using=self.using).append(AuditAppend(
            tenant_id=identity.tenant_id,
            stream_type=aggregate_type,
            stream_id=aggregate_id,
            actor_type="user",
            actor_id=str(actor_id),
            action=event_type,
            entity_type=aggregate_type,
            entity_id=aggregate_id,
            trace_id=trace_id,
            occurred_at=occurred_at,
            before_hash=canonical_hash(before) if before is not None else None,
            after_hash=canonical_hash(after) if after is not None else None,
            metadata={"event_id": str(event_id), "schema_version": EVENT_CONTRACTS[event_type]},
        ))
        return event_id, outbox.id, audit_id

    @staticmethod
    def _state(row, field_names):
        return {
            "revision": row.revision,
            **{name: getattr(row, name) for name in field_names},
        }

    def _create(self, *, model, aggregate_type, event_type, identity, organization_id,
                actor_id, trace_id, fields, change_reason, fail_before_commit):
        trace_id = UUID(str(trace_id))
        occurred_at = timezone.now()
        entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            if organization_id is None:
                organization_id = Process.objects.using(self.using).get(pk=fields["process_id"]).organization_id
            Organization.objects.using(self.using).get(pk=organization_id)
            row = model.objects.using(self.using).create(
                id=entity_id,
                tenant_id=identity.tenant_id,
                organization_id=organization_id,
                lineage_id=entity_id,
                revision=1,
                change_reason=change_reason,
                **fields,
            )
            state = self._state(row, tuple(fields))
            emitted = self._emit(
                identity=identity, aggregate_type=aggregate_type, aggregate_id=entity_id,
                event_type=event_type,
                payload={"lineage_id": str(entity_id), "revision_id": str(entity_id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, after=state,
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 5 rollback before commit")
            return MaterialMutationResult(entity_id, entity_id, *emitted, trace_id)

    def _revise(self, *, model, aggregate_type, event_type, identity, revision_id,
                actor_id, trace_id, fields, field_names=None, overrides=None,
                change_reason=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id))
        occurred_at = timezone.now()
        entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            prior = model.objects.using(self.using).get(pk=revision_id)
            if model.objects.using(self.using).filter(previous_revision_id=prior.id).exists():
                raise ValueError("only the current revision can be revised")
            if fields is None:
                fields = {name: getattr(prior, name) for name in field_names}
                fields.update(overrides or {})
            else:
                fields = {
                    name: getattr(prior, name) if value is _UNSET else value
                    for name, value in fields.items()
                }
            before = self._state(prior, tuple(fields))
            row = model.objects.using(self.using).create(
                id=entity_id,
                tenant_id=prior.tenant_id,
                organization_id=prior.organization_id,
                lineage_id=prior.lineage_id,
                revision=prior.revision + 1,
                previous_revision_id=prior.id,
                change_reason=change_reason,
                **fields,
            )
            after = self._state(row, tuple(fields))
            emitted = self._emit(
                identity=identity, aggregate_type=aggregate_type, aggregate_id=prior.lineage_id,
                event_type=event_type,
                payload={
                    "lineage_id": str(prior.lineage_id),
                    "previous_revision_id": str(prior.id),
                    "revision_id": str(entity_id),
                    "changes": {name: {"before": before[name], "after": after[name]}
                                for name in fields if before[name] != after[name]},
                    "revision": after["revision"],
                },
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at,
                before=before, after=after,
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 5 rollback before commit")
            return MaterialMutationResult(entity_id, prior.lineage_id, *emitted, trace_id)

    def create_risk(self, *, identity, process_id, cause, event, consequence,
                    likelihood, impact, residual, actor_id, trace_id,
                    change_reason=None, fail_before_commit=False):
        fields = {
            "process_id": process_id,
            "cause": _required(cause, "cause"),
            "event": _required(event, "event"),
            "consequence": _required(consequence, "consequence"),
            "likelihood": _required(likelihood, "likelihood"),
            "impact": _required(impact, "impact"),
            "residual": _required(residual, "residual"),
        }
        return self._create(model=Risk, aggregate_type="risk", event_type="risk.created",
            identity=identity, organization_id=None, actor_id=actor_id, trace_id=trace_id,
            fields=fields, change_reason=change_reason, fail_before_commit=fail_before_commit)

    def revise_risk(self, *, identity, risk_id, process_id, cause, event, consequence,
                    likelihood, impact, residual, actor_id, trace_id,
                    change_reason=None, fail_before_commit=False):
        fields = {
            "process_id": process_id,
            "cause": _required(cause, "cause"), "event": _required(event, "event"),
            "consequence": _required(consequence, "consequence"),
            "likelihood": _required(likelihood, "likelihood"),
            "impact": _required(impact, "impact"), "residual": _required(residual, "residual"),
        }
        return self._revise(model=Risk, aggregate_type="risk", event_type="risk.revised",
            identity=identity, revision_id=risk_id, actor_id=actor_id, trace_id=trace_id,
            fields=fields, change_reason=change_reason, fail_before_commit=fail_before_commit)

    def create_opportunity(self, *, identity, process_id, hypothesis, benefit, feasibility,
                           status, actor_id, trace_id, change_reason=None, fail_before_commit=False):
        fields = {"process_id": process_id, "hypothesis": _required(hypothesis, "hypothesis"),
                  "benefit": _required(benefit, "benefit"), "feasibility": _required(feasibility, "feasibility"),
                  "status": _required(status, "status")}
        return self._create(model=Opportunity, aggregate_type="opportunity", event_type="opportunity.created",
            identity=identity, organization_id=None, actor_id=actor_id, trace_id=trace_id,
            fields=fields, change_reason=change_reason, fail_before_commit=fail_before_commit)

    def revise_opportunity(self, *, identity, opportunity_id, process_id, hypothesis, benefit,
                           feasibility, status, actor_id, trace_id, change_reason=None,
                           fail_before_commit=False):
        fields = {"process_id": process_id, "hypothesis": _required(hypothesis, "hypothesis"),
                  "benefit": _required(benefit, "benefit"), "feasibility": _required(feasibility, "feasibility"),
                  "status": _required(status, "status")}
        return self._revise(model=Opportunity, aggregate_type="opportunity", event_type="opportunity.revised",
            identity=identity, revision_id=opportunity_id, actor_id=actor_id, trace_id=trace_id,
            fields=fields, change_reason=change_reason, fail_before_commit=fail_before_commit)

    def change_opportunity_status(self, *, identity, opportunity_id, status, actor_id, trace_id,
                                  change_reason=None, fail_before_commit=False):
        status = _required(status, "status")
        trace_id = UUID(str(trace_id))
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using
        ):
            return self._apply_opportunity_status_transition_in_transaction(
                identity=identity,
                opportunity_id=opportunity_id,
                status=status,
                actor_id=actor_id,
                trace_id=trace_id,
                change_reason=change_reason,
                fail_before_commit=fail_before_commit,
            )

    def _apply_opportunity_status_transition_in_transaction(
        self, *, identity, opportunity_id, status, actor_id, trace_id,
        change_reason=None, fail_before_commit=False,
    ):
        """Apply one Opportunity status revision in the caller's transaction.

        The method owns no transaction/savepoint and never commits.  PostgreSQL
        delegates revision/event/outbox/audit creation to the migration-managed
        domain primitive used by the controlled action wrappers as well.
        """

        connection = transaction.get_connection(self.using)
        if not connection.in_atomic_block:
            raise RuntimeError("Opportunity transition requires an active transaction")
        status = _required(status, "status")
        trace_id = UUID(str(trace_id))

        phase16_primitive_available = False
        if connection.vendor == "postgresql":
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT to_regprocedure("
                    "'qms.foundation_0015_apply_opportunity_status_transition("
                    "uuid,uuid,text,text,uuid,text,text)')"
                )
                phase16_primitive_available = cursor.fetchone()[0] is not None
        if phase16_primitive_available:
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT revision_id,lineage_id,event_id,outbox_id,audit_id,trace_id "
                    "FROM qms.foundation_0015_apply_opportunity_status_transition("
                    "%s,%s,%s,%s,%s,%s,%s)",
                    [str(opportunity_id), str(uuid4()), status, str(actor_id),
                     str(trace_id), change_reason, "user"],
                )
                row = cursor.fetchone()
            result = MaterialMutationResult(*row)
        else:
            occurred_at = timezone.now()
            entity_id = uuid4()
            prior = Opportunity.objects.using(self.using).get(pk=opportunity_id)
            if Opportunity.objects.using(self.using).filter(
                previous_revision_id=prior.id
            ).exists():
                raise ValueError("only the current revision can be revised")
            fields = {
                name: getattr(prior, name)
                for name in ("process_id", "hypothesis", "benefit", "feasibility", "status")
            }
            before = self._state(prior, tuple(fields))
            fields["status"] = status
            row = Opportunity.objects.using(self.using).create(
                id=entity_id, tenant_id=prior.tenant_id,
                organization_id=prior.organization_id, lineage_id=prior.lineage_id,
                revision=prior.revision + 1, previous_revision_id=prior.id,
                change_reason=change_reason, **fields,
            )
            after = self._state(row, tuple(fields))
            emitted = self._emit(
                identity=identity, aggregate_type="opportunity",
                aggregate_id=prior.lineage_id,
                event_type="opportunity.status_changed",
                payload={
                    "lineage_id": str(prior.lineage_id),
                    "previous_revision_id": str(prior.id),
                    "revision_id": str(entity_id),
                    "changes": {"status": {"before": prior.status, "after": status}},
                    "revision": after["revision"],
                },
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at,
                before=before, after=after,
            )
            result = MaterialMutationResult(
                entity_id, prior.lineage_id, *emitted, trace_id
            )
        if fail_before_commit:
            raise RuntimeError("deliberate Phase 5 rollback before commit")
        return result

    def create_objective(self, *, identity, organization_id, target, status, actor_id, trace_id,
                         owner_id=None, metric_id=None, due_date=None, change_reason=None,
                         fail_before_commit=False):
        fields = {"owner_id": owner_id, "metric_id": metric_id, "target": _required(target, "target"),
                  "due_date": due_date, "status": _required(status, "status")}
        return self._create(model=Objective, aggregate_type="objective", event_type="objective.created",
            identity=identity, organization_id=organization_id, actor_id=actor_id, trace_id=trace_id,
            fields=fields, change_reason=change_reason, fail_before_commit=fail_before_commit)

    def revise_objective(self, *, identity, objective_id, target, status, actor_id, trace_id,
                         owner_id=None, metric_id=_UNSET, due_date=None, change_reason=None,
                         fail_before_commit=False):
        fields = {"owner_id": owner_id, "metric_id": metric_id, "target": _required(target, "target"),
                  "due_date": due_date, "status": _required(status, "status")}
        return self._revise(model=Objective, aggregate_type="objective", event_type="objective.revised",
            identity=identity, revision_id=objective_id, actor_id=actor_id, trace_id=trace_id,
            fields=fields, change_reason=change_reason, fail_before_commit=fail_before_commit)

    def change_objective_status(self, *, identity, objective_id, status, actor_id, trace_id,
                                change_reason=None, fail_before_commit=False):
        return self._revise(model=Objective, aggregate_type="objective", event_type="objective.status_changed",
            identity=identity, revision_id=objective_id, actor_id=actor_id, trace_id=trace_id,
            fields=None, field_names=("owner_id", "metric_id", "target", "due_date", "status"),
            overrides={"status": _required(status, "status")},
            change_reason=change_reason, fail_before_commit=fail_before_commit)
