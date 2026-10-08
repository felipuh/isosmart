"""Provider-neutral, tenant-scoped AI usage metering and outbox production."""

from dataclasses import dataclass
from decimal import Decimal
import logging
from time import monotonic
from uuid import NAMESPACE_URL, uuid5

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .canonical import canonical_hash
from .models import AIModelPricingVersion, AIUsageRecord, DomainEvent, TenantProjection, TransactionalOutbox
from .tenant_context import trusted_tenant_context


logger = logging.getLogger(__name__)

AI_USAGE_EVENT_TYPE = "ai_usage.recorded"
AI_USAGE_EVENT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProviderInferenceResult:
    data: dict
    usage: dict | None = None
    provider_request_id: str | None = None
    response_status: str | None = "success"


def normalize_usage(usage):
    """Use only provider metadata; never infer tokens from prompts or text."""
    if not isinstance(usage, dict):
        return None
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    cached = details.get("cached_tokens", details.get("cached_input_tokens")) if isinstance(details, dict) else None
    values = (input_tokens, output_tokens, total_tokens, cached)
    if any(value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0) for value in values):
        return None
    if input_tokens is None or output_tokens is None:
        return None
    if total_tokens is None:
        total_tokens = input_tokens + output_tokens
    if total_tokens != input_tokens + output_tokens:
        return None
    return {"input_tokens": input_tokens, "output_tokens": output_tokens,
            "total_tokens": total_tokens, "cached_input_tokens": cached}


class AIUsageReplay(Exception):
    pass


class AIUsageLedger:
    PRODUCT = "iso-smart"
    AGENT = "value-discovery"

    def __init__(self, *, using, identity, execution_id, correlation_id, actor_id):
        self.using, self.identity = using, identity
        self.execution_id, self.correlation_id = execution_id, correlation_id
        self.actor_id = actor_id

    def reserve(self, *, invocation_id, capability, provider):
        """Commit before provider I/O so a failed domain transaction cannot erase usage."""
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=self.correlation_id, using=self.using):
            authoritative_id = TenantProjection.objects.using(self.using).only("adminapps_tenant_id").get(
                id=self.identity.tenant_id
            ).adminapps_tenant_id
            try:
                return AIUsageRecord.objects.using(self.using).create(
                    tenant_id=self.identity.tenant_id, adminapps_tenant_id=authoritative_id,
                    product_identifier=self.PRODUCT, agent_name=self.AGENT, capability_name=capability,
                    execution_id=self.execution_id, correlation_id=self.correlation_id, invocation_id=invocation_id,
                    provider=provider.provider_name, model_identifier=provider.model_identifier,
                    api_operation="chat.completions", usage_status="started", cost_status="pending", attempt_status="started",
                )
            except IntegrityError as exc:
                raise AIUsageReplay("a prior provider attempt already exists for this invocation") from exc

    def finalize(self, record, *, result=None, outcome, error_category=None, duration_ms=None):
        normalized = normalize_usage(result.usage if result else None)
        values = {"attempt_status": outcome, "provider_outcome": result.response_status if result else "unknown",
                  "provider_response_status": result.response_status if result else None,
                  "provider_request_id": result.provider_request_id if result else None, "duration_ms": duration_ms,
                  "error_category": error_category, "finalized_at": timezone.now()}
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=self.correlation_id, using=self.using):
            if normalized is None:
                values.update(usage_status="unknown", cost_status="unpriced", currency=None, estimated_provider_cost=None,
                              pricing_version=None, input_token_rate=None, output_token_rate=None, cached_input_token_rate=None)
            else:
                values.update(usage_status="reported", **normalized)
                values.update(self._price(record, normalized))
            AIUsageRecord.objects.using(self.using).filter(pk=record.pk).update(**values)
            finalized = AIUsageRecord.objects.using(self.using).get(pk=record.pk)
            # The ledger update has already committed.  A transient eventing problem
            # must therefore never erase provider-reported consumption.  The delivery
            # worker can reconcile a missing event for this immutable record later.
            try:
                _ensure_adminapps_usage_event(record=finalized, using=self.using)
            except Exception:
                logger.exception("ai_usage_outbox_enqueue_failed usage_record=%s", finalized.id)
            return finalized

    def _price(self, record, usage):
        at = timezone.now()
        tariff = AIModelPricingVersion.objects.using(self.using).filter(
            provider=record.provider, model_identifier=record.model_identifier, verification_status="verified",
            effective_from__lte=at).filter(Q(effective_to__isnull=True) | Q(effective_to__gt=at)).order_by("-effective_from").first()
        if not tariff or tariff.input_token_rate is None or tariff.output_token_rate is None:
            return {"cost_status": "unpriced", "currency": None, "estimated_provider_cost": None, "pricing_version": None,
                    "input_token_rate": None, "output_token_rate": None, "cached_input_token_rate": None}
        cost = Decimal(usage["input_tokens"]) * tariff.input_token_rate + Decimal(usage["output_tokens"]) * tariff.output_token_rate
        if usage.get("cached_input_tokens") and tariff.cached_input_token_rate is not None:
            cost += Decimal(usage["cached_input_tokens"]) * (tariff.cached_input_token_rate - tariff.input_token_rate)
        return {"cost_status": "estimated", "currency": tariff.currency, "estimated_provider_cost": cost / Decimal(tariff.rate_unit),
                "pricing_version": tariff, "input_token_rate": tariff.input_token_rate, "output_token_rate": tariff.output_token_rate,
                "cached_input_token_rate": tariff.cached_input_token_rate}


def run_metered_capability(*, ledger, capability, provider, context, validate, invocation_id):
    record = ledger.reserve(invocation_id=invocation_id, capability=capability, provider=provider)
    started = monotonic()
    response = None
    try:
        metadata_method = getattr(type(provider), "analyze_with_metadata", None)
        response = (provider.analyze_with_metadata(capability=capability, context=context)
                    if callable(metadata_method) else ProviderInferenceResult(data=provider.analyze(capability=capability, context=context)))
        value = validate(response.data)
    except Exception as exc:
        ledger.finalize(record, result=response, outcome="rejected" if response else "failed",
                        error_category=getattr(exc, "code", exc.__class__.__name__),
                        duration_ms=int((monotonic() - started) * 1000))
        raise
    ledger.finalize(record, result=response, outcome="completed", duration_ms=int((monotonic() - started) * 1000))
    return value


def serialize_for_adminapps(record, *, usage_event_id):
    """Secret-free v1 payload for the authenticated AdminApps ingestion contract.

    Delivery is intentionally separate: this cycle does not configure an endpoint
    or publish external events.
    """
    return {
        "schema_version": 1, "usage_event_id": str(usage_event_id), "usage_record_id": str(record.id),
        "adminapps_tenant_id": str(record.adminapps_tenant_id), "execution_id": str(record.execution_id),
        "correlation_id": str(record.correlation_id), "product_identifier": record.product_identifier,
        "agent_name": record.agent_name, "capability_name": record.capability_name, "provider": record.provider,
        "model_identifier": record.model_identifier, "attempted_at": record.created_at.isoformat(),
        "attempt_status": record.attempt_status, "usage_status": record.usage_status,
        "input_tokens": record.input_tokens, "output_tokens": record.output_tokens, "total_tokens": record.total_tokens,
        "cost_status": record.cost_status,
        "estimated_provider_cost": str(record.estimated_provider_cost) if record.estimated_provider_cost is not None else None,
        "currency": record.currency,
        "pricing_version_id": str(getattr(record, "pricing_version_id", None)) if getattr(record, "pricing_version_id", None) else None,
    }


def usage_event_id_for(record_id):
    """Stable event identity makes outbox recovery safe after a process crash."""
    return uuid5(NAMESPACE_URL, f"smart3ai:iso-smart:ai-usage:{record_id}")


def ensure_adminapps_usage_event(*, record, using, identity):
    """Persist exactly one secret-free AdminApps delivery event for a final ledger row.

    This only creates a local outbox record.  It never performs network I/O and
    therefore cannot make provider inference depend on AdminApps availability.
    """
    with trusted_tenant_context(identity, actor_id="ai-usage-outbox", trace_id=record.correlation_id, using=using):
        return _ensure_adminapps_usage_event(record=record, using=using)


def _ensure_adminapps_usage_event(*, record, using):
    """Persist an event while the caller already owns the tenant context."""
    if record.usage_status == "started" or not record.finalized_at:
        return None
    if not record.adminapps_tenant_id:
        raise ValueError("finalized AI usage requires an authoritative AdminApps tenant")
    event_id = usage_event_id_for(record.id)
    payload = serialize_for_adminapps(record, usage_event_id=event_id)
    with transaction.atomic(using=using):
        event, created = DomainEvent.objects.using(using).get_or_create(
            event_id=event_id,
            defaults={
                "tenant_id": record.tenant_id,
                "event_type": AI_USAGE_EVENT_TYPE,
                "schema_version": AI_USAGE_EVENT_SCHEMA_VERSION,
                "aggregate_type": "ai_usage_record",
                "aggregate_id": record.id,
                "aggregate_version": 1,
                "occurred_at": record.finalized_at,
                "trace_id": record.correlation_id,
                "correlation_id": record.correlation_id,
                "source": "iso-smart-ai-usage",
                "payload": payload,
                "payload_hash": canonical_hash(payload),
            },
        )
        if not created and event.payload_hash != canonical_hash(payload):
            raise AIUsageReplay("AI usage event identity conflicts with persisted payload")
        outbox, _ = TransactionalOutbox.objects.using(using).get_or_create(
            domain_event_id=event_id,
            defaults={
                "tenant_id": record.tenant_id,
                "status": TransactionalOutbox.Status.PENDING,
                "publish_attempts": 0,
                "available_at": timezone.now(),
            },
        )
        return outbox
