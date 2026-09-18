"""Material Phase 4 commands: business row + event + outbox + audit atomically."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
import json

from .canonical import canonical_hash, canonical_json
from .models import (
    ContextItem,
    DomainEvent,
    Organization,
    Process,
    QmsScope,
    QmsScopeProcess,
    Stakeholder,
    StakeholderRequirement,
    TransactionalOutbox,
)
from .tenant_context import trusted_tenant_context


EVENT_CONTRACTS = {
    "stakeholder.created": 1,
    "stakeholder.updated": 1,
    "stakeholder_requirement.created": 1,
    "stakeholder_requirement.superseded": 1,
    "process.created": 1,
    "process.updated": 1,
    "context_item.created": 1,
    "context_item.superseded": 1,
    "qms_scope.created": 1,
    "qms_scope.revised": 1,
}


@dataclass(frozen=True)
class MaterialMutationResult:
    entity_id: UUID
    aggregate_id: UUID
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID
    trace_id: UUID


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


class QmsContextCommandService:
    def __init__(self, *, using="app"):
        self.using = using

    def _emit(self, *, identity, aggregate_type, aggregate_id, event_type, payload,
              actor_id, trace_id, occurred_at, before=None, after=None):
        payload = json.loads(canonical_json(payload))["value"]
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
            payload=payload,
            payload_hash=canonical_hash(payload),
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

    def _result(self, entity_id, aggregate_id, emitted, trace_id, fail_before_commit):
        if fail_before_commit:
            raise RuntimeError("deliberate Phase 4 rollback before commit")
        return MaterialMutationResult(entity_id, aggregate_id, *emitted, trace_id)

    def create_stakeholder(self, *, identity, organization_id, stakeholder_type, name,
                           relevance_score=None, actor_id, trace_id, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        state = {"stakeholder_type": _required(stakeholder_type, "stakeholder_type"),
                 "name": _required(name, "name"), "relevance_score": relevance_score}
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(pk=organization_id)
            Stakeholder.objects.using(self.using).create(
                id=entity_id, tenant_id=identity.tenant_id, organization_id=organization_id, **state
            )
            payload = {"stakeholder_id": str(entity_id), "organization_id": str(organization_id), "state": state}
            emitted = self._emit(identity=identity, aggregate_type="stakeholder", aggregate_id=entity_id,
                                 event_type="stakeholder.created", payload=payload, actor_id=actor_id,
                                 trace_id=trace_id, occurred_at=occurred_at, after=state)
            return self._result(entity_id, entity_id, emitted, trace_id, fail_before_commit)

    def update_stakeholder(self, *, identity, stakeholder_id, actor_id, trace_id,
                           name=None, stakeholder_type=None, relevance_score=None,
                           fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            row = Stakeholder.objects.using(self.using).select_for_update().get(pk=stakeholder_id)
            before = {"stakeholder_type": row.stakeholder_type, "name": row.name,
                      "relevance_score": row.relevance_score}
            if name is not None: row.name = _required(name, "name")
            if stakeholder_type is not None: row.stakeholder_type = _required(stakeholder_type, "stakeholder_type")
            if relevance_score is not None: row.relevance_score = relevance_score
            row.save(using=self.using, update_fields=("name", "stakeholder_type", "relevance_score", "updated_at"))
            after = {"stakeholder_type": row.stakeholder_type, "name": row.name,
                     "relevance_score": row.relevance_score}
            payload = {"stakeholder_id": str(row.id), "before": before, "after": after}
            emitted = self._emit(identity=identity, aggregate_type="stakeholder", aggregate_id=row.id,
                                 event_type="stakeholder.updated", payload=payload, actor_id=actor_id,
                                 trace_id=trace_id, occurred_at=occurred_at, before=before, after=after)
            return self._result(row.id, row.id, emitted, trace_id, fail_before_commit)

    def create_process(self, *, identity, organization_id, name, actor_id, trace_id,
                       owner_id=None, process_type=None, status="active", fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        state = {"name": _required(name, "name"), "owner_id": str(owner_id) if owner_id else None,
                 "process_type": process_type, "status": _required(status, "status")}
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(pk=organization_id)
            Process.objects.using(self.using).create(
                id=entity_id, tenant_id=identity.tenant_id, organization_id=organization_id,
                name=state["name"], owner_id=owner_id, process_type=process_type, status=state["status"],
            )
            payload = {"process_id": str(entity_id), "organization_id": str(organization_id), "state": state}
            emitted = self._emit(identity=identity, aggregate_type="process", aggregate_id=entity_id,
                                 event_type="process.created", payload=payload, actor_id=actor_id,
                                 trace_id=trace_id, occurred_at=occurred_at, after=state)
            return self._result(entity_id, entity_id, emitted, trace_id, fail_before_commit)

    def update_process(self, *, identity, process_id, actor_id, trace_id, name=None,
                       owner_id=None, process_type=None, status=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            row = Process.objects.using(self.using).select_for_update().get(pk=process_id)
            before = {"name": row.name, "owner_id": str(row.owner_id) if row.owner_id else None,
                      "process_type": row.process_type, "status": row.status}
            if name is not None: row.name = _required(name, "name")
            if owner_id is not None: row.owner_id = owner_id
            if process_type is not None: row.process_type = process_type
            if status is not None: row.status = _required(status, "status")
            row.save(using=self.using, update_fields=("name", "owner_id", "process_type", "status", "updated_at"))
            after = {"name": row.name, "owner_id": str(row.owner_id) if row.owner_id else None,
                     "process_type": row.process_type, "status": row.status}
            emitted = self._emit(identity=identity, aggregate_type="process", aggregate_id=row.id,
                                 event_type="process.updated", payload={"process_id": str(row.id), "before": before, "after": after},
                                 actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, before=before, after=after)
            return self._result(row.id, row.id, emitted, trace_id, fail_before_commit)

    def create_stakeholder_requirement(self, *, identity, stakeholder_id, requirement_text,
                                       actor_id, trace_id, qms_addressed=False, owner_process_id=None,
                                       change_reason=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            stakeholder = Stakeholder.objects.using(self.using).get(pk=stakeholder_id)
            state = {"revision": 1, "requirement_text": _required(requirement_text, "requirement_text"),
                     "qms_addressed": bool(qms_addressed), "owner_process_id": str(owner_process_id) if owner_process_id else None}
            StakeholderRequirement.objects.using(self.using).create(
                id=entity_id, tenant_id=identity.tenant_id, organization_id=stakeholder.organization_id,
                stakeholder_id=stakeholder.id, lineage_id=entity_id, revision=1,
                requirement_text=state["requirement_text"], qms_addressed=state["qms_addressed"],
                owner_process_id=owner_process_id, change_reason=change_reason,
            )
            emitted = self._emit(identity=identity, aggregate_type="stakeholder_requirement", aggregate_id=entity_id,
                                 event_type="stakeholder_requirement.created",
                                 payload={"requirement_id": str(entity_id), "stakeholder_id": str(stakeholder.id), "state": state},
                                 actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, after=state)
            return self._result(entity_id, entity_id, emitted, trace_id, fail_before_commit)

    def supersede_stakeholder_requirement(self, *, identity, requirement_id, requirement_text,
                                          actor_id, trace_id, qms_addressed=None, owner_process_id=None,
                                          change_reason=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            prior = StakeholderRequirement.objects.using(self.using).get(pk=requirement_id)
            if StakeholderRequirement.objects.using(self.using).filter(previous_revision_id=prior.id).exists():
                raise ValueError("only the current requirement revision can be superseded")
            before = {"revision": prior.revision, "requirement_text": prior.requirement_text,
                      "qms_addressed": prior.qms_addressed,
                      "owner_process_id": str(prior.owner_process_id) if prior.owner_process_id else None}
            addressed = prior.qms_addressed if qms_addressed is None else bool(qms_addressed)
            process_id = prior.owner_process_id if owner_process_id is None else owner_process_id
            after = {"revision": prior.revision + 1, "requirement_text": _required(requirement_text, "requirement_text"),
                     "qms_addressed": addressed, "owner_process_id": str(process_id) if process_id else None}
            StakeholderRequirement.objects.using(self.using).create(
                id=entity_id, tenant_id=prior.tenant_id, organization_id=prior.organization_id,
                stakeholder_id=prior.stakeholder_id, lineage_id=prior.lineage_id, revision=prior.revision + 1,
                previous_revision_id=prior.id, requirement_text=after["requirement_text"],
                qms_addressed=addressed, owner_process_id=process_id, change_reason=change_reason,
            )
            payload = {"lineage_id": str(prior.lineage_id), "previous_revision_id": str(prior.id),
                       "new_revision_id": str(entity_id), "before": before, "after": after}
            emitted = self._emit(identity=identity, aggregate_type="stakeholder_requirement", aggregate_id=prior.lineage_id,
                                 event_type="stakeholder_requirement.superseded", payload=payload, actor_id=actor_id,
                                 trace_id=trace_id, occurred_at=occurred_at, before=before, after=after)
            return self._result(entity_id, prior.lineage_id, emitted, trace_id, fail_before_commit)

    def create_context_item(self, *, identity, organization_id, issue_type, description,
                            actor_id, trace_id, change_reason=None, fail_before_commit=False):
        return self._create_revision(ContextItem, "context_item", "context_item.created", identity=identity,
            organization_id=organization_id, actor_id=actor_id, trace_id=trace_id,
            fields={"issue_type": issue_type, "description": _required(description, "description")},
            change_reason=change_reason, fail_before_commit=fail_before_commit)

    def supersede_context_item(self, *, identity, context_item_id, issue_type, description,
                               actor_id, trace_id, change_reason=None, fail_before_commit=False):
        return self._supersede_revision(ContextItem, "context_item", "context_item.superseded", context_item_id,
            identity=identity, actor_id=actor_id, trace_id=trace_id,
            fields={"issue_type": issue_type, "description": _required(description, "description")},
            change_reason=change_reason, fail_before_commit=fail_before_commit)

    def create_scope(self, *, identity, organization_id, boundaries, applicability, products_services,
                     actor_id, trace_id, process_ids=(), change_reason=None, fail_before_commit=False):
        return self._create_revision(QmsScope, "qms_scope", "qms_scope.created", identity=identity,
            organization_id=organization_id, actor_id=actor_id, trace_id=trace_id,
            fields={"boundaries": _required(boundaries, "boundaries"), "applicability": _required(applicability, "applicability"),
                    "products_services": _required(products_services, "products_services")},
            process_ids=process_ids, change_reason=change_reason, fail_before_commit=fail_before_commit)

    def revise_scope(self, *, identity, scope_id, boundaries, applicability, products_services,
                     actor_id, trace_id, process_ids=(), change_reason=None, fail_before_commit=False):
        return self._supersede_revision(QmsScope, "qms_scope", "qms_scope.revised", scope_id,
            identity=identity, actor_id=actor_id, trace_id=trace_id,
            fields={"boundaries": _required(boundaries, "boundaries"), "applicability": _required(applicability, "applicability"),
                    "products_services": _required(products_services, "products_services")},
            process_ids=process_ids, change_reason=change_reason, fail_before_commit=fail_before_commit)

    def _create_revision(self, model, aggregate_type, event_type, *, identity, organization_id,
                         actor_id, trace_id, fields, change_reason, process_ids=(), fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(pk=organization_id)
            model.objects.using(self.using).create(id=entity_id, tenant_id=identity.tenant_id,
                organization_id=organization_id, lineage_id=entity_id, revision=1,
                change_reason=change_reason, **fields)
            self._set_scope_processes(model, entity_id, identity.tenant_id, organization_id, process_ids)
            state = {"revision": 1, **fields, "process_ids": sorted(str(value) for value in process_ids)}
            emitted = self._emit(identity=identity, aggregate_type=aggregate_type, aggregate_id=entity_id,
                                 event_type=event_type, payload={"revision_id": str(entity_id), "state": state},
                                 actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, after=state)
            return self._result(entity_id, entity_id, emitted, trace_id, fail_before_commit)

    def _supersede_revision(self, model, aggregate_type, event_type, prior_id, *, identity,
                            actor_id, trace_id, fields, change_reason, process_ids=(), fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            prior = model.objects.using(self.using).get(pk=prior_id)
            if model.objects.using(self.using).filter(previous_revision_id=prior.id).exists():
                raise ValueError("only the current revision can be superseded")
            field_names = list(fields)
            before = {"revision": prior.revision, **{name: getattr(prior, name) for name in field_names}}
            model.objects.using(self.using).create(id=entity_id, tenant_id=prior.tenant_id,
                organization_id=prior.organization_id, lineage_id=prior.lineage_id,
                revision=prior.revision + 1, previous_revision_id=prior.id,
                change_reason=change_reason, **fields)
            self._set_scope_processes(model, entity_id, prior.tenant_id, prior.organization_id, process_ids)
            after = {"revision": prior.revision + 1, **fields,
                     "process_ids": sorted(str(value) for value in process_ids)}
            emitted = self._emit(identity=identity, aggregate_type=aggregate_type, aggregate_id=prior.lineage_id,
                                 event_type=event_type,
                                 payload={"lineage_id": str(prior.lineage_id), "previous_revision_id": str(prior.id),
                                          "new_revision_id": str(entity_id), "before": before, "after": after},
                                 actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at,
                                 before=before, after=after)
            return self._result(entity_id, prior.lineage_id, emitted, trace_id, fail_before_commit)

    def _set_scope_processes(self, model, scope_revision_id, tenant_id, organization_id, process_ids):
        if model is not QmsScope:
            return
        for process_id in set(process_ids):
            Process.objects.using(self.using).get(pk=process_id, organization_id=organization_id)
            QmsScopeProcess.objects.using(self.using).create(
                id=uuid4(), tenant_id=tenant_id, organization_id=organization_id,
                scope_revision_id=scope_revision_id, process_id=process_id,
            )
