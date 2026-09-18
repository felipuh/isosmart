"""Atomic event/outbox commands, at-least-once delivery and durable inbox semantics."""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from uuid import UUID, uuid4

from django.db import IntegrityError, transaction
from django.db.models import Max, Q
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash
from .models import ConsumerReceipt, DomainEvent, Organization, TransactionalOutbox
from .tenant_context import trusted_tenant_context


class PayloadIntegrityConflict(RuntimeError):
    status_equivalent = 409


class ReceiptResultKind(Enum):
    PROCESSED = "processed"
    IDEMPOTENT_DUPLICATE = "idempotent_duplicate"


@dataclass(frozen=True)
class ReceiptResult:
    kind: ReceiptResultKind
    receipt_id: UUID


@dataclass(frozen=True)
class OrganizationMutationResult:
    organization_id: UUID
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID
    trace_id: UUID


class OrganizationEventingService:
    """The only Phase 3 Organization command: domain + event + outbox + audit."""

    def __init__(self, *, using="app"):
        self.using = using

    def rename(
        self, *, identity, organization_id, display_name, actor_id,
        trace_id, correlation_id=None, causation_id=None, fail_before_commit=False,
    ):
        trace_id = UUID(str(trace_id))
        occurred_at = timezone.now()
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using
        ):
            organization = (
                Organization.objects.using(self.using).select_for_update().get(pk=organization_id)
            )
            before = {"display_name": organization.display_name, "legal_name": organization.legal_name}
            organization.display_name = display_name
            organization.save(using=self.using, update_fields=("display_name", "updated_at"))
            after = {"display_name": organization.display_name, "legal_name": organization.legal_name}

            aggregate_version = (
                DomainEvent.objects.using(self.using)
                .filter(aggregate_type="organization", aggregate_id=organization.id)
                .aggregate(value=Max("aggregate_version"))["value"] or 0
            ) + 1
            event_id = uuid4()
            payload = {
                "organization_id": str(organization.id),
                "before": before,
                "after": after,
            }
            DomainEvent.objects.using(self.using).create(
                event_id=event_id,
                tenant_id=identity.tenant_id,
                event_type="organization.renamed",
                schema_version=1,
                aggregate_type="organization",
                aggregate_id=organization.id,
                aggregate_version=aggregate_version,
                occurred_at=occurred_at,
                trace_id=trace_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
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
            audit_id = AuditWriterService(using=self.using).append(
                AuditAppend(
                    tenant_id=identity.tenant_id,
                    stream_type="organization",
                    stream_id=organization.id,
                    actor_type="user",
                    actor_id=str(actor_id),
                    action="organization.renamed",
                    entity_type="organization",
                    entity_id=organization.id,
                    trace_id=trace_id,
                    occurred_at=occurred_at,
                    before_hash=canonical_hash(before),
                    after_hash=canonical_hash(after),
                    metadata={"event_id": str(event_id), "schema_version": 1},
                )
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 3 rollback before commit")
            return OrganizationMutationResult(
                organization.id, event_id, outbox.id, audit_id, trace_id
            )


class OutboxDeliveryService:
    """Tenant-scoped SKIP LOCKED claiming for an at-least-once dispatcher."""

    def __init__(self, *, using="worker", lease_duration=None):
        self.using = using
        self.lease_duration = lease_duration or timedelta(minutes=5)

    def claim_next(self, *, identity, worker_id, trace_id):
        with trusted_tenant_context(
            identity, actor_id=worker_id, trace_id=trace_id, using=self.using
        ):
            row = (
                TransactionalOutbox.objects.using(self.using)
                .select_for_update(skip_locked=True)
                .filter(
                    available_at__lte=timezone.now(),
                )
                .filter(
                    Q(status__in=(TransactionalOutbox.Status.PENDING, TransactionalOutbox.Status.FAILED))
                    | Q(status=TransactionalOutbox.Status.PROCESSING, lease_expires_at__lte=timezone.now())
                )
                .order_by("available_at", "created_at")
                .first()
            )
            if row is None:
                return None
            row.status = TransactionalOutbox.Status.PROCESSING
            row.publish_attempts += 1
            row.lease_owner = str(worker_id)
            row.lease_expires_at = timezone.now() + self.lease_duration
            row.last_error_code = None
            row.save(
                using=self.using,
                update_fields=(
                    "status", "publish_attempts", "lease_owner", "lease_expires_at",
                    "last_error_code", "updated_at",
                ),
            )
            return row.id

    def mark_published(self, *, identity, outbox_id, worker_id, trace_id):
        with trusted_tenant_context(
            identity, actor_id=worker_id, trace_id=trace_id, using=self.using
        ):
            row = TransactionalOutbox.objects.using(self.using).select_for_update().get(pk=outbox_id)
            row.status = TransactionalOutbox.Status.PUBLISHED
            row.published_at = timezone.now()
            row.lease_owner = None
            row.lease_expires_at = None
            row.last_error_code = None
            row.save(
                using=self.using,
                update_fields=(
                    "status", "published_at", "lease_owner", "lease_expires_at",
                    "last_error_code", "updated_at",
                ),
            )

    def mark_failed(self, *, identity, outbox_id, worker_id, trace_id, error_code):
        with trusted_tenant_context(
            identity, actor_id=worker_id, trace_id=trace_id, using=self.using
        ):
            row = TransactionalOutbox.objects.using(self.using).select_for_update().get(pk=outbox_id)
            row.status = TransactionalOutbox.Status.FAILED
            row.lease_owner = None
            row.lease_expires_at = None
            row.last_error_code = error_code
            row.save(
                using=self.using,
                update_fields=(
                    "status", "lease_owner", "lease_expires_at", "last_error_code", "updated_at",
                ),
            )


class ConsumerReceiptService:
    def __init__(self, *, using="worker"):
        self.using = using

    def receive(self, *, identity, consumer_name, event_id, payload, trace_id, handler):
        payload_hash = canonical_hash(payload)
        with trusted_tenant_context(
            identity, actor_id=consumer_name, trace_id=trace_id, using=self.using
        ):
            receipt = (
                ConsumerReceipt.objects.using(self.using)
                .select_for_update()
                .filter(consumer_name=consumer_name, event_id=event_id)
                .first()
            )
            if receipt is not None:
                if receipt.payload_hash != payload_hash:
                    raise PayloadIntegrityConflict("event identity was replayed with a different payload hash")
                if receipt.status == ConsumerReceipt.Status.PROCESSED:
                    return ReceiptResult(ReceiptResultKind.IDEMPOTENT_DUPLICATE, receipt.id)
            else:
                try:
                    with transaction.atomic(using=self.using):
                        receipt = ConsumerReceipt.objects.using(self.using).create(
                            tenant_id=identity.tenant_id,
                            consumer_name=consumer_name,
                            event_id=event_id,
                            payload_hash=payload_hash,
                            status=ConsumerReceipt.Status.RECEIVED,
                            attempts=0,
                            trace_id=trace_id,
                        )
                except IntegrityError as exc:
                    raise PayloadIntegrityConflict("event identity already belongs to another durable receipt") from exc

            receipt.status = ConsumerReceipt.Status.PROCESSING
            receipt.attempts += 1
            receipt.last_error_code = None
            receipt.save(
                using=self.using,
                update_fields=("status", "attempts", "last_error_code"),
            )
            handler(payload)
            receipt.status = ConsumerReceipt.Status.PROCESSED
            receipt.processed_at = timezone.now()
            receipt.save(
                using=self.using,
                update_fields=("status", "processed_at"),
            )
            return ReceiptResult(ReceiptResultKind.PROCESSED, receipt.id)


class ReplayService:
    """Records an explicit replay request; it never deletes or rewrites receipts."""

    def __init__(self, *, using="app"):
        self.using = using

    def request(self, *, identity, event_id, consumer_name, actor_id, trace_id, reason):
        if not reason or not reason.strip():
            raise ValueError("replay reason is required")
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using
        ):
            return AuditWriterService(using=self.using).append(
                AuditAppend(
                    tenant_id=identity.tenant_id,
                    stream_type="event-replay",
                    stream_id=UUID(str(event_id)),
                    actor_type="user",
                    actor_id=str(actor_id),
                    action="event.replay.requested",
                    entity_type="domain_event",
                    entity_id=UUID(str(event_id)),
                    trace_id=UUID(str(trace_id)),
                    occurred_at=timezone.now(),
                    metadata={
                        "consumer_name": consumer_name,
                        "event_id": str(event_id),
                        "reason": reason.strip(),
                    },
                )
            )
