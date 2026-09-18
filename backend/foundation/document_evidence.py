"""Material Phase 7 commands for logical documents, immutable versions and evidence."""

import hashlib
import json
import re
from decimal import Decimal
from uuid import UUID, uuid4

from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    Document,
    DocumentVersion,
    DomainEvent,
    Evidence,
    Organization,
    TransactionalOutbox,
)
from .qms_context import MaterialMutationResult
from .tenant_context import trusted_tenant_context


EVENT_CONTRACTS = {
    "document.created": 1,
    "document.metadata_revised": 1,
    "document.version_created": 1,
    "evidence.created": 1,
    "evidence.superseded": 1,
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_exact_bytes(content):
    """Return SHA-256 over the exact supplied binary octets, without canonicalization."""
    if not isinstance(content, bytes):
        raise TypeError("content must be exact bytes")
    return hashlib.sha256(content).hexdigest()


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _sha256(value):
    value = _required(value, "content_hash").lower()
    if not SHA256_RE.fullmatch(value):
        raise ValueError("content_hash must be a lowercase SHA-256 hex digest")
    return value


class DocumentEvidenceCommandService:
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
            event_id=event_id, tenant_id=identity.tenant_id, event_type=event_type,
            schema_version=EVENT_CONTRACTS[event_type], aggregate_type=aggregate_type,
            aggregate_id=aggregate_id, aggregate_version=aggregate_version,
            occurred_at=occurred_at, trace_id=trace_id, source="iso-smart-qms",
            payload=normalized_payload, payload_hash=canonical_hash(normalized_payload),
        )
        outbox = TransactionalOutbox.objects.using(self.using).create(
            tenant_id=identity.tenant_id, domain_event_id=event_id,
            status=TransactionalOutbox.Status.PENDING, publish_attempts=0,
            available_at=occurred_at,
        )
        audit_id = AuditWriterService(using=self.using).append(AuditAppend(
            tenant_id=identity.tenant_id, stream_type=aggregate_type, stream_id=aggregate_id,
            actor_type="user", actor_id=str(actor_id), action=event_type,
            entity_type=aggregate_type, entity_id=aggregate_id, trace_id=trace_id,
            occurred_at=occurred_at,
            before_hash=canonical_hash(before) if before is not None else None,
            after_hash=canonical_hash(after) if after is not None else None,
            metadata={"event_id": str(event_id), "schema_version": EVENT_CONTRACTS[event_type]},
        ))
        return event_id, outbox.id, audit_id

    @staticmethod
    def _document_state(row):
        return {
            "document_type": row.document_type,
            "owner_id": str(row.owner_id) if row.owner_id else None,
            "current_version_id": str(row.current_version_id) if row.current_version_id else None,
        }

    @staticmethod
    def _version_state(row):
        return {
            "document_id": str(row.document_id), "version": row.version,
            "predecessor_id": str(row.predecessor_id) if row.predecessor_id else None,
            "content_reference": row.content_reference, "content_hash": row.content_hash,
            "approved_by": str(row.approved_by_id) if row.approved_by_id else None,
            "effective_at": row.effective_at.isoformat() if row.effective_at else None,
        }

    @staticmethod
    def _evidence_state(row):
        return {
            "revision": row.revision, "source_type": row.source_type,
            "source_uri": row.source_uri, "content_hash": row.content_hash,
            "captured_at": row.captured_at.isoformat(),
            "trust_score": str(row.trust_score) if row.trust_score is not None else None,
            "document_version_id": str(row.document_version_id) if row.document_version_id else None,
        }

    def create_document(self, *, identity, organization_id, document_type, actor_id,
                        trace_id, owner_id=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(pk=organization_id)
            row = Document.objects.using(self.using).create(
                id=entity_id, tenant_id=identity.tenant_id, organization_id=organization_id,
                document_type=_required(document_type, "document_type"), owner_id=owner_id,
            )
            state = self._document_state(row)
            emitted = self._emit(
                identity=identity, aggregate_type="document", aggregate_id=entity_id,
                event_type="document.created", payload={"document_id": str(entity_id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, after=state,
            )
            if fail_before_commit: raise RuntimeError("deliberate Phase 7 rollback before commit")
            return MaterialMutationResult(entity_id, entity_id, *emitted, trace_id)

    def revise_document_metadata(self, *, identity, document_id, document_type, actor_id,
                                 trace_id, owner_id=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            row = Document.objects.using(self.using).select_for_update().get(pk=document_id)
            before = self._document_state(row)
            row.document_type = _required(document_type, "document_type")
            row.owner_id = owner_id
            row.save(using=self.using, update_fields=("document_type", "owner", "updated_at"))
            after = self._document_state(row)
            emitted = self._emit(
                identity=identity, aggregate_type="document", aggregate_id=row.id,
                event_type="document.metadata_revised",
                payload={"document_id": str(row.id), "changes": {
                    key: {"before": before[key], "after": after[key]}
                    for key in ("document_type", "owner_id") if before[key] != after[key]
                }}, actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at,
                before=before, after=after,
            )
            if fail_before_commit: raise RuntimeError("deliberate Phase 7 rollback before commit")
            return MaterialMutationResult(row.id, row.id, *emitted, trace_id)

    def create_document_version(self, *, identity, document_id, version, content_reference,
                                content_bytes, actor_id, trace_id, approved_by=None,
                                effective_at=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        content_hash = sha256_exact_bytes(content_bytes)
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            document = Document.objects.using(self.using).select_for_update().get(pk=document_id)
            row = DocumentVersion.objects.using(self.using).create(
                id=entity_id, tenant_id=document.tenant_id, organization_id=document.organization_id,
                document_id=document.id, version=_required(version, "version"),
                predecessor_id=document.current_version_id,
                content_reference=_required(content_reference, "content_reference"),
                content_hash=content_hash, approved_by_id=approved_by, effective_at=effective_at,
            )
            document.current_version_id = row.id
            document.save(using=self.using, update_fields=("current_version", "updated_at"))
            state = self._version_state(row)
            emitted = self._emit(
                identity=identity, aggregate_type="document", aggregate_id=document.id,
                event_type="document.version_created",
                payload={"document_id": str(document.id), "document_version_id": str(row.id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, after=state,
            )
            if fail_before_commit: raise RuntimeError("deliberate Phase 7 rollback before commit")
            return MaterialMutationResult(entity_id, document.id, *emitted, trace_id)

    def _source(self, *, document_version_id, source_type, source_uri, content_hash):
        if document_version_id is None:
            return _required(source_type, "source_type"), source_uri, _sha256(content_hash)
        version = DocumentVersion.objects.using(self.using).get(pk=document_version_id)
        return (
            _required(source_type or "document_version", "source_type"),
            source_uri if source_uri is not None else version.content_reference,
            version.content_hash,
        )

    def create_evidence(self, *, identity, organization_id, source_type, captured_at,
                        actor_id, trace_id, source_uri=None, content_hash=None,
                        trust_score=None, document_version_id=None,
                        change_reason=None, fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(pk=organization_id)
            source_type, source_uri, content_hash = self._source(
                document_version_id=document_version_id, source_type=source_type,
                source_uri=source_uri, content_hash=content_hash,
            )
            row = Evidence.objects.using(self.using).create(
                id=entity_id, tenant_id=identity.tenant_id, organization_id=organization_id,
                lineage_id=entity_id, revision=1, source_type=source_type,
                source_uri=source_uri, content_hash=content_hash, captured_at=captured_at,
                trust_score=Decimal(str(trust_score)) if trust_score is not None else None,
                document_version_id=document_version_id, change_reason=change_reason,
            )
            state = self._evidence_state(row)
            emitted = self._emit(
                identity=identity, aggregate_type="evidence", aggregate_id=entity_id,
                event_type="evidence.created",
                payload={"lineage_id": str(entity_id), "revision_id": str(entity_id), "state": state},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at, after=state,
            )
            if fail_before_commit: raise RuntimeError("deliberate Phase 7 rollback before commit")
            return MaterialMutationResult(entity_id, entity_id, *emitted, trace_id)

    def supersede_evidence(self, *, identity, evidence_id, source_type, captured_at,
                           actor_id, trace_id, source_uri=None, content_hash=None,
                           trust_score=None, document_version_id=None, change_reason=None,
                           fail_before_commit=False):
        trace_id = UUID(str(trace_id)); occurred_at = timezone.now(); entity_id = uuid4()
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            prior = Evidence.objects.using(self.using).get(pk=evidence_id)
            if Evidence.objects.using(self.using).filter(previous_revision_id=prior.id).exists():
                raise ValueError("only the current evidence revision can be superseded")
            source_type, source_uri, content_hash = self._source(
                document_version_id=document_version_id, source_type=source_type,
                source_uri=source_uri, content_hash=content_hash,
            )
            before = self._evidence_state(prior)
            row = Evidence.objects.using(self.using).create(
                id=entity_id, tenant_id=prior.tenant_id, organization_id=prior.organization_id,
                lineage_id=prior.lineage_id, revision=prior.revision + 1,
                previous_revision_id=prior.id, source_type=source_type, source_uri=source_uri,
                content_hash=content_hash, captured_at=captured_at,
                trust_score=Decimal(str(trust_score)) if trust_score is not None else None,
                document_version_id=document_version_id, change_reason=change_reason,
            )
            after = self._evidence_state(row)
            emitted = self._emit(
                identity=identity, aggregate_type="evidence", aggregate_id=prior.lineage_id,
                event_type="evidence.superseded",
                payload={"lineage_id": str(prior.lineage_id), "previous_revision_id": str(prior.id),
                         "revision_id": str(row.id), "revision": row.revision,
                         "changes": {key: {"before": before[key], "after": after[key]}
                                     for key in before if key != "revision" and before[key] != after[key]}},
                actor_id=actor_id, trace_id=trace_id, occurred_at=occurred_at,
                before=before, after=after,
            )
            if fail_before_commit: raise RuntimeError("deliberate Phase 7 rollback before commit")
            return MaterialMutationResult(entity_id, prior.lineage_id, *emitted, trace_id)
