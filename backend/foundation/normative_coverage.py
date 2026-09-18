"""Phase 8 commands for curated normative history and evidence coverage."""

import json
import re
from decimal import Decimal
from uuid import UUID, uuid4

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    Clause,
    DomainEvent,
    Evidence,
    EvidenceCoverage,
    NormativeCurationAudit,
    Organization,
    RequirementControl,
    Standard,
    StandardEdition,
    TransactionalOutbox,
)
from .qms_context import MaterialMutationResult
from .tenant_context import trusted_tenant_context


EVENT_CONTRACTS = {"evidence_coverage.recorded": 1}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _optional_hash(value):
    if value is None:
        return None
    normalized = _required(value, "source_hash").lower()
    if not SHA256_RE.fullmatch(normalized):
        raise ValueError("source_hash must be a lowercase SHA-256 hex digest")
    return normalized


class NormativeCatalogCommandService:
    """Narrow boundary intended only for the isolated normative curator LOGIN."""

    def __init__(self, *, using="normative_curator"):
        self.using = using

    def _audit(self, *, action, entity_type, entity_id, actor_id, trace_id, payload):
        NormativeCurationAudit.objects.using(self.using).create(
            id=uuid4(), action=action, entity_type=entity_type, entity_id=entity_id,
            actor_id=_required(str(actor_id), "actor_id"), trace_id=trace_id,
            payload_hash=canonical_hash(payload), occurred_at=timezone.now(),
        )

    def create_standard(self, *, code, actor_id, trace_id, title=None, publisher="ISO"):
        trace_id = UUID(str(trace_id)); entity_id = uuid4()
        state = {"code": _required(code, "code"), "title": title,
                 "publisher": _required(publisher, "publisher")}
        with transaction.atomic(using=self.using):
            Standard.objects.using(self.using).create(id=entity_id, **state)
            self._audit(action="standard.created", entity_type="standard", entity_id=entity_id,
                        actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def create_standard_edition(self, *, standard_id, edition, actor_id, trace_id,
                                effective_from=None, effective_to=None, source_hash=None):
        trace_id = UUID(str(trace_id)); entity_id = uuid4()
        state = {
            "standard_id": str(standard_id), "edition": _required(edition, "edition"),
            "status": StandardEdition.Status.DRAFT,
            "effective_from": effective_from.isoformat() if effective_from else None,
            "effective_to": effective_to.isoformat() if effective_to else None,
            "source_hash": _optional_hash(source_hash),
        }
        with transaction.atomic(using=self.using):
            StandardEdition.objects.using(self.using).create(
                id=entity_id, standard_id=standard_id, edition=state["edition"],
                status=state["status"], effective_from=effective_from,
                effective_to=effective_to, source_hash=state["source_hash"],
            )
            self._audit(action="standard_edition.created", entity_type="standard_edition",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def add_clause(self, *, standard_edition_id, code, actor_id, trace_id,
                   title=None, parent_id=None):
        trace_id = UUID(str(trace_id)); entity_id = uuid4()
        state = {"standard_edition_id": str(standard_edition_id),
                 "code": _required(code, "code"), "title": title,
                 "parent_id": str(parent_id) if parent_id else None}
        with transaction.atomic(using=self.using):
            Clause.objects.using(self.using).create(
                id=entity_id, standard_edition_id=standard_edition_id,
                code=state["code"], title=title, parent_id=parent_id,
            )
            self._audit(action="clause.created", entity_type="clause", entity_id=entity_id,
                        actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def add_requirement_control(self, *, standard_edition_id, clause_id, paraphrase,
                                actor_id, trace_id, applicability_rule=None,
                                control_type=None, valid_from=None, valid_to=None):
        trace_id = UUID(str(trace_id)); entity_id = uuid4()
        state = {
            "standard_edition_id": str(standard_edition_id), "clause_id": str(clause_id),
            "paraphrase": _required(paraphrase, "paraphrase"),
            "applicability_rule": applicability_rule or {}, "control_type": control_type,
            "valid_from": valid_from.isoformat() if valid_from else None,
            "valid_to": valid_to.isoformat() if valid_to else None,
        }
        with transaction.atomic(using=self.using):
            RequirementControl.objects.using(self.using).create(
                id=entity_id, standard_edition_id=standard_edition_id, clause_id=clause_id,
                paraphrase=state["paraphrase"], applicability_rule=state["applicability_rule"],
                control_type=control_type, valid_from=valid_from, valid_to=valid_to,
            )
            self._audit(action="requirement_control.created", entity_type="requirement_control",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def publish_standard_edition(self, *, standard_edition_id, actor_id, trace_id,
                                 fail_before_commit=False):
        trace_id = UUID(str(trace_id))
        with transaction.atomic(using=self.using):
            edition = StandardEdition.objects.using(self.using).select_for_update().get(
                id=standard_edition_id,
            )
            if edition.status != StandardEdition.Status.DRAFT:
                raise ValueError("only a draft edition can be published")
            if not Clause.objects.using(self.using).filter(standard_edition_id=edition.id).exists():
                raise ValueError("edition requires at least one clause")
            if not RequirementControl.objects.using(self.using).filter(
                standard_edition_id=edition.id,
            ).exists():
                raise ValueError("edition requires at least one requirement control")
            edition.status = StandardEdition.Status.PUBLISHED
            edition.save(using=self.using, update_fields=("status",))
            self._audit(
                action="standard_edition.published", entity_type="standard_edition",
                entity_id=edition.id, actor_id=actor_id, trace_id=trace_id,
                payload={"standard_id": str(edition.standard_id),
                         "edition": edition.edition, "status": edition.status},
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 8 publication rollback before commit")
        return edition.id


class EvidenceCoverageCommandService:
    def __init__(self, *, using="app"):
        self.using = using

    def record_evidence_coverage(self, *, identity, organization_id, evidence_id,
                                 standard_edition_id, requirement_control_id,
                                 actor_id, trace_id, confidence=None,
                                 validation_status="proposed", validated_by=None,
                                 validated_at=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); coverage_id = uuid4()
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using,
        ):
            Organization.objects.using(self.using).get(id=organization_id)
            evidence = Evidence.objects.using(self.using).get(id=evidence_id)
            requirement = RequirementControl.objects.using(self.using).get(
                id=requirement_control_id, standard_edition_id=standard_edition_id,
            )
            status = _required(validation_status, "validation_status")
            row = EvidenceCoverage.objects.using(self.using).create(
                id=coverage_id, tenant_id=identity.tenant_id,
                organization_id=organization_id, evidence_id=evidence.id,
                standard_edition_id=standard_edition_id,
                requirement_control_id=requirement.id,
                confidence=Decimal(str(confidence)) if confidence is not None else None,
                validation_status=status, validated_by_id=validated_by,
                validated_at=validated_at,
            )
            state = {
                "coverage_id": str(row.id), "evidence_id": str(row.evidence_id),
                "evidence_lineage_id": str(evidence.lineage_id),
                "evidence_revision": evidence.revision,
                "standard_edition_id": str(row.standard_edition_id),
                "requirement_control_id": str(row.requirement_control_id),
                "confidence": str(row.confidence) if row.confidence is not None else None,
                "validation_status": row.validation_status,
                "validated_by": str(row.validated_by_id) if row.validated_by_id else None,
                "validated_at": row.validated_at.isoformat() if row.validated_at else None,
            }
            normalized = json.loads(canonical_json(state))["value"]
            event_id = uuid4()
            aggregate_version = (
                DomainEvent.objects.using(self.using)
                .filter(aggregate_type="evidence_coverage", aggregate_id=row.id)
                .aggregate(value=Max("aggregate_version"))["value"] or 0
            ) + 1
            DomainEvent.objects.using(self.using).create(
                event_id=event_id, tenant_id=identity.tenant_id,
                event_type="evidence_coverage.recorded", schema_version=1,
                aggregate_type="evidence_coverage", aggregate_id=row.id,
                aggregate_version=aggregate_version, occurred_at=occurred_at,
                trace_id=trace_id, source="iso-smart-qms", payload=normalized,
                payload_hash=canonical_hash(normalized),
            )
            outbox = TransactionalOutbox.objects.using(self.using).create(
                tenant_id=identity.tenant_id, domain_event_id=event_id,
                status=TransactionalOutbox.Status.PENDING, publish_attempts=0,
                available_at=occurred_at,
            )
            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=identity.tenant_id, stream_type="evidence_coverage",
                stream_id=row.id, actor_type="user", actor_id=str(actor_id),
                action="evidence_coverage.recorded", entity_type="evidence_coverage",
                entity_id=row.id, trace_id=trace_id, occurred_at=occurred_at,
                after_hash=canonical_hash(state),
                metadata={"event_id": str(event_id), "schema_version": 1},
            ))
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 8 coverage rollback before commit")
            return MaterialMutationResult(
                row.id, row.id, event_id, outbox.id, audit_id, trace_id,
            )
