"""Explicit, bounded delivery of AI-usage outbox events to AdminApps.

No endpoint or credential has a default.  Operational delivery remains disabled
unless the deployment explicitly enables it; tests inject a local transport.
"""

from dataclasses import dataclass
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from .ai_usage import AI_USAGE_EVENT_TYPE
from .eventing import OutboxDeliveryService
from .models import DomainEvent, TransactionalOutbox
from .tenant_context import trusted_tenant_context


PERMANENT_REJECTION = "AI_USAGE_PERMANENT_REJECTION"
RETRYABLE_FAILURE = "AI_USAGE_RETRYABLE_FAILURE"


@dataclass(frozen=True)
class DeliveryResult:
    state: str
    outbox_id: object | None = None
    status_code: int | None = None


def delivery_failure_kind(status_code):
    """Only client validation/authentication failures are permanently rejected."""
    if status_code is not None and 400 <= status_code < 500:
        return "permanent"
    return "retryable"


class AIUsageDelivery:
    """At-least-once dispatcher with stable event IDs and bounded retries."""

    def __init__(self, *, using="worker", post=None, endpoint=None, api_key=None,
                 enabled=None, timeout_seconds=None, max_attempts=None):
        self.using = using
        self.post = post or requests.post
        self.endpoint = endpoint if endpoint is not None else getattr(settings, "AI_USAGE_ADMINAPPS_ENDPOINT", "")
        self.api_key = api_key if api_key is not None else getattr(settings, "AI_USAGE_ADMINAPPS_API_KEY", "")
        self.enabled = enabled if enabled is not None else getattr(settings, "AI_USAGE_ADMINAPPS_DELIVERY_ENABLED", False)
        self.timeout_seconds = timeout_seconds or getattr(settings, "AI_USAGE_ADMINAPPS_TIMEOUT_SECONDS", 5)
        self.max_attempts = max_attempts or getattr(settings, "AI_USAGE_ADMINAPPS_MAX_ATTEMPTS", 3)

    def _assert_configured(self):
        if not self.enabled:
            raise RuntimeError("AI usage delivery is disabled by deployment configuration")
        if not self.endpoint or not self.api_key:
            raise RuntimeError("AI usage delivery requires an endpoint and authenticated service credential")

    def deliver_next(self, *, identity, worker_id, trace_id):
        self._assert_configured()
        delivery = OutboxDeliveryService(using=self.using)
        outbox_id = delivery.claim_next(
            identity=identity,
            worker_id=worker_id,
            trace_id=trace_id,
            event_type=AI_USAGE_EVENT_TYPE,
            excluded_error_codes=(PERMANENT_REJECTION,),
        )
        if outbox_id is None:
            return None
        with trusted_tenant_context(identity, actor_id=worker_id, trace_id=trace_id, using=self.using):
            row = TransactionalOutbox.objects.using(self.using).select_related("domain_event").get(pk=outbox_id)
            event = row.domain_event
        try:
            response = self.post(
                self.endpoint,
                json=event.payload,
                headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
            status_code = response.status_code
        except requests.RequestException:
            return self._retryable(delivery, identity, outbox_id, worker_id, trace_id)

        if 200 <= status_code < 300:
            delivery.mark_published(identity=identity, outbox_id=outbox_id, worker_id=worker_id, trace_id=trace_id)
            return DeliveryResult("DELIVERED", outbox_id, status_code)
        if delivery_failure_kind(status_code) == "permanent":
            delivery.mark_failed(
                identity=identity, outbox_id=outbox_id, worker_id=worker_id, trace_id=trace_id,
                error_code=PERMANENT_REJECTION,
            )
            return DeliveryResult("PERMANENT_REJECTION", outbox_id, status_code)
        return self._retryable(delivery, identity, outbox_id, worker_id, trace_id, status_code)

    def _retryable(self, delivery, identity, outbox_id, worker_id, trace_id, status_code=None):
        with trusted_tenant_context(identity, actor_id=worker_id, trace_id=trace_id, using=self.using):
            row = TransactionalOutbox.objects.using(self.using).get(pk=outbox_id)
            exhausted = row.publish_attempts >= self.max_attempts
        if exhausted:
            delivery.mark_failed(
                identity=identity, outbox_id=outbox_id, worker_id=worker_id, trace_id=trace_id,
                error_code=PERMANENT_REJECTION,
            )
            return DeliveryResult("PERMANENT_REJECTION", outbox_id, status_code)
        # A bounded backoff avoids a tight retry loop while leaving the source
        # ledger and exact event intact for a later authorized replay.
        delay = min(60, 2 ** max(0, row.publish_attempts - 1))
        delivery.mark_failed(
            identity=identity, outbox_id=outbox_id, worker_id=worker_id, trace_id=trace_id,
            error_code=RETRYABLE_FAILURE,
            available_at=timezone.now() + timedelta(seconds=delay),
        )
        return DeliveryResult("RETRYABLE_FAILURE", outbox_id, status_code)
