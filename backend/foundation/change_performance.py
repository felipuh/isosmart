"""Material Phase 6 commands for Change and minimal measurement definitions."""

import json
from uuid import UUID, uuid4

from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    Change,
    ChangeProcess,
    DomainEvent,
    MeasurementDefinition,
    Organization,
    Process,
    TransactionalOutbox,
)
from .qms_context import MaterialMutationResult
from .tenant_context import trusted_tenant_context


EVENT_CONTRACTS = {
    "change.created": 1,
    "change.revised": 1,
    "change.status_changed": 1,
    "measurement_definition.created": 1,
    "measurement_definition.revised": 1,
}


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


class ChangePerformanceCommandService:
    def __init__(self, *, using="app"):
        self.using = using

    def _emit(self, *, identity, aggregate_type, aggregate_id, event_type, payload,
              actor_id, trace_id, occurred_at, before=None, after=None):
        normalized_payload = json.loads(canonical_json(payload))["value"]
        aggregate_version = (
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
            aggregate_version=aggregate_version,
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

    def _processes(self, process_ids, organization_id):
        normalized = tuple(dict.fromkeys(UUID(str(item)) for item in (process_ids or ())))
        if not normalized:
            return normalized
        found = set(Process.objects.using(self.using).filter(
            id__in=normalized, organization_id=organization_id,
        ).values_list("id", flat=True))
        if found != set(normalized):
            raise ValueError("every affected process must belong to the trusted tenant and Organization")
        return normalized

    @staticmethod
    def _change_state(row, process_ids):
        return {
            "revision": row.revision,
            "type": row.change_type,
            "purpose": row.purpose,
            "impact": row.impact,
            "status": row.status,
            "approval_id": str(row.approval_id) if row.approval_id else None,
            "process_ids": sorted(str(item) for item in process_ids),
        }

    def create_change(self, *, identity, organization_id, change_type, purpose, impact,
                      status, actor_id, trace_id, approval_id=None, process_ids=(),
                      change_reason=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id))
        occurred_at = timezone.now()
        entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(pk=organization_id)
            process_ids = self._processes(process_ids, organization_id)
            row = Change.objects.using(self.using).create(
                id=entity_id, tenant_id=identity.tenant_id, organization_id=organization_id,
                lineage_id=entity_id, revision=1,
                change_type=_required(change_type, "type"),
                purpose=_required(purpose, "purpose"), impact=_required(impact, "impact"),
                status=_required(status, "status"), approval_id=approval_id,
                change_reason=change_reason,
            )
            for process_id in process_ids:
                ChangeProcess.objects.using(self.using).create(
                    tenant_id=identity.tenant_id, organization_id=organization_id,
                    change_revision_id=row.id, process_id=process_id,
                )
            state = self._change_state(row, process_ids)
            emitted = self._emit(
                identity=identity, aggregate_type="change", aggregate_id=entity_id,
                event_type="change.created",
                payload={"lineage_id": str(entity_id), "revision_id": str(entity_id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, after=state,
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 6 rollback before commit")
            return MaterialMutationResult(entity_id, entity_id, *emitted, trace_id)

    def _revise_change(self, *, identity, change_id, actor_id, trace_id, event_type,
                       overrides, process_ids=None, change_reason=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id))
        occurred_at = timezone.now()
        entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            prior = Change.objects.using(self.using).get(pk=change_id)
            if Change.objects.using(self.using).filter(previous_revision_id=prior.id).exists():
                raise ValueError("only the current revision can be revised")
            prior_processes = tuple(ChangeProcess.objects.using(self.using).filter(
                change_revision_id=prior.id).values_list("process_id", flat=True))
            process_ids = self._processes(
                prior_processes if process_ids is None else process_ids, prior.organization_id,
            )
            fields = {
                "change_type": prior.change_type, "purpose": prior.purpose,
                "impact": prior.impact, "status": prior.status,
                "approval_id": prior.approval_id,
            }
            fields.update(overrides)
            for name in ("change_type", "purpose", "impact", "status"):
                fields[name] = _required(fields[name], "type" if name == "change_type" else name)
            before = self._change_state(prior, prior_processes)
            row = Change.objects.using(self.using).create(
                id=entity_id, tenant_id=prior.tenant_id, organization_id=prior.organization_id,
                lineage_id=prior.lineage_id, revision=prior.revision + 1,
                previous_revision_id=prior.id, change_reason=change_reason, **fields,
            )
            for process_id in process_ids:
                ChangeProcess.objects.using(self.using).create(
                    tenant_id=prior.tenant_id, organization_id=prior.organization_id,
                    change_revision_id=row.id, process_id=process_id,
                )
            after = self._change_state(row, process_ids)
            changes = {key: {"before": before[key], "after": after[key]}
                       for key in before if key != "revision" and before[key] != after[key]}
            emitted = self._emit(
                identity=identity, aggregate_type="change", aggregate_id=prior.lineage_id,
                event_type=event_type,
                payload={"lineage_id": str(prior.lineage_id),
                         "previous_revision_id": str(prior.id), "revision_id": str(row.id),
                         "revision": row.revision, "changes": changes},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at,
                before=before, after=after,
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 6 rollback before commit")
            return MaterialMutationResult(entity_id, prior.lineage_id, *emitted, trace_id)

    def revise_change(self, *, identity, change_id, change_type, purpose, impact, status,
                      actor_id, trace_id, approval_id=None, process_ids=None,
                      change_reason=None, fail_before_commit=False):
        return self._revise_change(
            identity=identity, change_id=change_id, actor_id=actor_id, trace_id=trace_id,
            event_type="change.revised",
            overrides={"change_type": change_type, "purpose": purpose, "impact": impact,
                       "status": status, "approval_id": approval_id},
            process_ids=process_ids, change_reason=change_reason,
            fail_before_commit=fail_before_commit,
        )

    def change_change_status(self, *, identity, change_id, status, actor_id, trace_id,
                             change_reason=None, fail_before_commit=False):
        return self._revise_change(
            identity=identity, change_id=change_id, actor_id=actor_id, trace_id=trace_id,
            event_type="change.status_changed", overrides={"status": status},
            change_reason=change_reason, fail_before_commit=fail_before_commit,
        )

    @staticmethod
    def _measurement_state(row):
        return {
            "revision": row.revision,
            "process_id": str(row.process_id) if row.process_id else None,
            "what_is_measured": row.what_is_measured,
            "method": row.method,
            "measurement_timing": row.measurement_timing,
        }

    def define_measurement(self, *, identity, organization_id, what_is_measured, method,
                           measurement_timing, actor_id, trace_id, process_id=None,
                           change_reason=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id))
        occurred_at = timezone.now()
        entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(pk=organization_id)
            if process_id is not None:
                self._processes((process_id,), organization_id)
            row = MeasurementDefinition.objects.using(self.using).create(
                id=entity_id, tenant_id=identity.tenant_id, organization_id=organization_id,
                lineage_id=entity_id, revision=1, process_id=process_id,
                what_is_measured=_required(what_is_measured, "what_is_measured"),
                method=_required(method, "method"),
                measurement_timing=_required(measurement_timing, "measurement_timing"),
                change_reason=change_reason,
            )
            state = self._measurement_state(row)
            emitted = self._emit(
                identity=identity, aggregate_type="measurement_definition", aggregate_id=entity_id,
                event_type="measurement_definition.created",
                payload={"lineage_id": str(entity_id), "revision_id": str(entity_id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, after=state,
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 6 rollback before commit")
            return MaterialMutationResult(entity_id, entity_id, *emitted, trace_id)

    def revise_measurement_definition(self, *, identity, measurement_definition_id,
                                      what_is_measured, method, measurement_timing,
                                      actor_id, trace_id, process_id=None,
                                      change_reason=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id))
        occurred_at = timezone.now()
        entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            prior = MeasurementDefinition.objects.using(self.using).get(pk=measurement_definition_id)
            if MeasurementDefinition.objects.using(self.using).filter(previous_revision_id=prior.id).exists():
                raise ValueError("only the current measurement definition can be revised")
            if process_id is not None:
                self._processes((process_id,), prior.organization_id)
            before = self._measurement_state(prior)
            row = MeasurementDefinition.objects.using(self.using).create(
                id=entity_id, tenant_id=prior.tenant_id, organization_id=prior.organization_id,
                lineage_id=prior.lineage_id, revision=prior.revision + 1,
                previous_revision_id=prior.id, process_id=process_id,
                what_is_measured=_required(what_is_measured, "what_is_measured"),
                method=_required(method, "method"),
                measurement_timing=_required(measurement_timing, "measurement_timing"),
                change_reason=change_reason,
            )
            after = self._measurement_state(row)
            emitted = self._emit(
                identity=identity, aggregate_type="measurement_definition",
                aggregate_id=prior.lineage_id, event_type="measurement_definition.revised",
                payload={"lineage_id": str(prior.lineage_id),
                         "previous_revision_id": str(prior.id), "revision_id": str(row.id),
                         "revision": row.revision,
                         "changes": {key: {"before": before[key], "after": after[key]}
                                     for key in before if key != "revision" and before[key] != after[key]}},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at,
                before=before, after=after,
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 6 rollback before commit")
            return MaterialMutationResult(entity_id, prior.lineage_id, *emitted, trace_id)
