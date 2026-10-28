"""Small source-backed Audit → Finding → Nonconformity → CorrectiveAction commands.

The source catalog provides fields and lineage, not audit/CAPA workflow states;
these commands therefore create immutable records only and never infer transitions.
"""

from dataclasses import dataclass
from uuid import UUID, uuid4

from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash
from .models import (
    DomainEvent, Evidence, Finding, Organization, QmsAudit, QmsCorrectiveAction,
    QmsNonconformity, RequirementControl, TransactionalOutbox,
)
from .tenant_context import trusted_tenant_context


@dataclass(frozen=True)
class QmsAuditMutationResult:
    entity_id: UUID
    event_id: UUID | None
    outbox_id: UUID | None
    audit_id: UUID
    trace_id: UUID


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


class QmsAuditCommandService:
    def __init__(self, *, using="app"):
        self.using = using

    def _event_and_audit(self, *, identity, entity, entity_id, event_type, payload,
                         actor_id, trace_id, occurred_at):
        event_id = outbox_id = None
        if event_type:
            version = (DomainEvent.objects.using(self.using).filter(
                aggregate_type=entity, aggregate_id=entity_id,
            ).aggregate(value=Max("aggregate_version"))["value"] or 0) + 1
            event_id = uuid4()
            DomainEvent.objects.using(self.using).create(
                event_id=event_id, tenant_id=identity.tenant_id, event_type=event_type,
                schema_version=1, aggregate_type=entity, aggregate_id=entity_id,
                aggregate_version=version, occurred_at=occurred_at, trace_id=trace_id,
                source="iso-smart-qms", payload=payload, payload_hash=canonical_hash(payload),
            )
            outbox_id = TransactionalOutbox.objects.using(self.using).create(
                tenant_id=identity.tenant_id, domain_event_id=event_id,
                status=TransactionalOutbox.Status.PENDING, publish_attempts=0,
                available_at=occurred_at,
            ).id
        audit_id = AuditWriterService(using=self.using).append(AuditAppend(
            tenant_id=identity.tenant_id, stream_type=entity, stream_id=entity_id,
            actor_type="user", actor_id=str(actor_id), action=event_type or f"{entity}.created",
            entity_type=entity, entity_id=entity_id, trace_id=trace_id, occurred_at=occurred_at,
            after_hash=canonical_hash(payload), metadata={"event_id": str(event_id) if event_id else None},
        ))
        return QmsAuditMutationResult(entity_id, event_id, outbox_id, audit_id, trace_id)

    def create_audit(self, *, identity, organization_id, scope, criteria, status, lead_auditor,
                     actor_id, trace_id):
        trace_id = UUID(str(trace_id)); row_id = uuid4(); now = timezone.now()
        state = {"scope": _required(scope, "scope"), "criteria": _required(criteria, "criteria"),
                 "status": _required(status, "status"), "lead_auditor": _required(lead_auditor, "lead_auditor")}
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(pk=organization_id)
            QmsAudit.objects.using(self.using).create(id=row_id, tenant_id=identity.tenant_id,
                organization_id=organization_id, **state)
            return self._event_and_audit(identity=identity, entity="audit", entity_id=row_id,
                event_type=None, payload={"audit_id": str(row_id), "organization_id": str(organization_id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=now)

    def create_finding(self, *, identity, audit_id, requirement_id, finding_type, statement,
                       evidence_id, actor_id, trace_id):
        trace_id = UUID(str(trace_id)); row_id = uuid4(); now = timezone.now()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            audit = QmsAudit.objects.using(self.using).get(pk=audit_id)
            RequirementControl.objects.using(self.using).get(pk=requirement_id)
            evidence = Evidence.objects.using(self.using).get(pk=evidence_id)
            if evidence.organization_id != audit.organization_id:
                raise ValueError("evidence organization does not match audit organization")
            state = {"type": _required(finding_type, "finding_type"), "statement": _required(statement, "statement")}
            Finding.objects.using(self.using).create(id=row_id, tenant_id=identity.tenant_id,
                organization_id=audit.organization_id, audit_id=audit.id, requirement_id=requirement_id,
                evidence_id=evidence.id, finding_type=state["type"], statement=state["statement"])
            payload = {"finding_id": str(row_id), "audit_id": str(audit.id), "requirement_id": str(requirement_id),
                       "evidence_id": str(evidence.id), "state": state}
            return self._event_and_audit(identity=identity, entity="finding", entity_id=row_id,
                event_type="audit.finding.created", payload=payload, actor_id=actor_id, trace_id=trace_id, occurred_at=now)

    def create_nonconformity_from_finding(self, *, identity, finding_id, description, severity,
                                          status, actor_id, trace_id):
        trace_id = UUID(str(trace_id)); row_id = uuid4(); now = timezone.now()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            finding = Finding.objects.using(self.using).get(pk=finding_id)
            state = {"source_type": "finding", "source_id": str(finding.id),
                     "description": _required(description, "description"), "severity": _required(severity, "severity"),
                     "status": _required(status, "status")}
            QmsNonconformity.objects.using(self.using).create(id=row_id, tenant_id=identity.tenant_id,
                organization_id=finding.organization_id, source_type="finding", source_id=finding.id,
                description=state["description"], severity=state["severity"], status=state["status"])
            return self._event_and_audit(identity=identity, entity="nonconformity", entity_id=row_id,
                event_type="nonconformity.detected", payload={"nc_id": str(row_id), "organization_id": str(finding.organization_id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=now)

    def create_corrective_action(self, *, identity, nonconformity_id, cause_id, action, owner_id,
                                 due_date, effectiveness_check_id=None, actor_id=None, trace_id=None):
        trace_id = UUID(str(trace_id)); row_id = uuid4(); now = timezone.now()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            nc = QmsNonconformity.objects.using(self.using).get(pk=nonconformity_id)
            state = {"nc_id": str(nc.id), "cause_id": str(cause_id), "action": _required(action, "action"),
                     "owner_id": str(owner_id), "due_date": due_date.isoformat(), "effectiveness_check_id": str(effectiveness_check_id) if effectiveness_check_id else None}
            QmsCorrectiveAction.objects.using(self.using).create(id=row_id, tenant_id=identity.tenant_id,
                organization_id=nc.organization_id, nonconformity_id=nc.id, cause_id=cause_id, action=state["action"],
                owner_id=owner_id, due_date=due_date, effectiveness_check_id=effectiveness_check_id)
            return self._event_and_audit(identity=identity, entity="corrective_action", entity_id=row_id,
                event_type=None, payload={"capa_id": str(row_id), "organization_id": str(nc.organization_id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=now)
