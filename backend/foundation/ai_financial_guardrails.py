"""Fail-closed, product-scoped financial admission for ISO Smart AI calls.

The service intentionally does not contact AdminApps: no authenticated central
reservation/entitlement contract exists yet.  Consequently production callers
are rejected before this service can reserve.  The persistence below is used
only for controlled, synthetic PostgreSQL evidence and is explicitly not a
cross-product cap.
"""

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import AIFinancialGuardrailPolicy, AIFinancialReservation, AIModelPricingVersion


class FinancialAdmissionDenied(Exception):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def _pricing(*, using, provider, model_identifier, at):
    pricing = AIModelPricingVersion.objects.using(using).filter(
        provider=provider, model_identifier=model_identifier,
        verification_status="verified", effective_from__lte=at,
    ).filter(effective_to__isnull=True) | AIModelPricingVersion.objects.using(using).filter(
        provider=provider, model_identifier=model_identifier,
        verification_status="verified", effective_from__lte=at, effective_to__gt=at,
    )
    pricing = pricing.order_by("-effective_from").first()
    if not pricing or not pricing.source_reference or pricing.rate_unit <= 0:
        raise FinancialAdmissionDenied("AI_PRICING_UNVERIFIED", "a verified effective pricing version is required")
    if pricing.input_token_rate is None or pricing.output_token_rate is None:
        raise FinancialAdmissionDenied("AI_PRICING_INCOMPLETE", "pricing cannot bound input and output cost")
    if pricing.input_token_rate < 0 or pricing.output_token_rate < 0:
        raise FinancialAdmissionDenied("AI_PRICING_INVALID", "pricing rates must be non-negative")
    return pricing


def worst_case_cost(*, pricing, input_tokens, output_tokens):
    return ((Decimal(input_tokens) * pricing.input_token_rate)
            + (Decimal(output_tokens) * pricing.output_token_rate)) / Decimal(pricing.rate_unit)


class FinancialGuardrailService:
    """Serializes reservations by policy row; PostgreSQL locks prevent overspend."""

    PRODUCT = "iso-smart"

    def __init__(self, *, using):
        self.using = using

    def reserve_controlled_test(self, *, tenant_id, invocation_id, provider, model_identifier,
                                input_token_bound, max_output_tokens, usage_record):
        """Reserve an explicitly labelled synthetic-test policy only.

        This private test seam is not reached by real provider execution.  It
        validates the same atomic accounting mechanics without asserting that
        an ISO-local policy represents AdminApps financial authority.
        """
        if not isinstance(input_token_bound, int) or input_token_bound < 0:
            raise FinancialAdmissionDenied("AI_INPUT_BOUND_INVALID", "input token bound must be an exact non-negative integer")
        if not isinstance(max_output_tokens, int) or max_output_tokens <= 0:
            raise FinancialAdmissionDenied("AI_OUTPUT_BOUND_INVALID", "maximum output tokens must be an enforceable positive integer")
        now = timezone.now()
        with transaction.atomic(using=self.using):
            policy = AIFinancialGuardrailPolicy.objects.using(self.using).select_for_update().filter(
                tenant_id=tenant_id, product_identifier=self.PRODUCT, provider=provider,
                model_identifier=model_identifier, status="enabled", policy_scope="controlled_test",
                period_start__lte=now, period_end__gt=now,
            ).order_by("-period_start").first()
            if policy is None:
                raise FinancialAdmissionDenied("AI_GUARDRAIL_POLICY_MISSING", "no applicable controlled-test policy exists")
            if input_token_bound > policy.max_input_tokens:
                raise FinancialAdmissionDenied("AI_INPUT_LIMIT_EXCEEDED", "input token bound exceeds policy")
            if max_output_tokens > policy.max_output_tokens:
                raise FinancialAdmissionDenied("AI_OUTPUT_LIMIT_EXCEEDED", "output token limit exceeds policy")
            existing = AIFinancialReservation.objects.using(self.using).filter(
                tenant_id=tenant_id, invocation_id=invocation_id,
            ).first()
            if existing:
                if (existing.policy_id != policy.id or existing.reserved_input_tokens != input_token_bound
                        or existing.reserved_output_tokens != max_output_tokens):
                    raise FinancialAdmissionDenied("AI_RESERVATION_IDENTITY_CONFLICT", "request identity conflicts with its reservation")
                return existing, True
            requests = AIFinancialReservation.objects.using(self.using).filter(policy=policy).count()
            if requests >= policy.max_request_count:
                raise FinancialAdmissionDenied("AI_REQUEST_QUOTA_EXHAUSTED", "request quota is exhausted")
            pricing = _pricing(using=self.using, provider=provider, model_identifier=model_identifier, at=now)
            if pricing.currency != policy.currency:
                raise FinancialAdmissionDenied("AI_CURRENCY_MISMATCH", "policy and verified pricing currencies differ")
            reserved_cost = worst_case_cost(pricing=pricing, input_tokens=input_token_bound, output_tokens=max_output_tokens)
            # A settled row always has settled_cost; unresolved/reserved rows hold
            # their full worst-case amount.  Calculate in Python to avoid silently
            # converting NULL/unknown exposure to zero.
            held = Decimal("0")
            for reservation in AIFinancialReservation.objects.using(self.using).filter(policy=policy).exclude(status="released"):
                held += reservation.settled_cost if reservation.settled_cost is not None else reservation.reserved_cost
            if held + reserved_cost > policy.max_reserved_cost:
                raise FinancialAdmissionDenied("AI_BUDGET_EXCEEDED", "worst-case reservation exceeds the product-scoped cap")
            try:
                reservation = AIFinancialReservation.objects.using(self.using).create(
                    policy=policy, tenant_id=tenant_id, invocation_id=invocation_id, usage_record=usage_record,
                    reserved_input_tokens=input_token_bound, reserved_output_tokens=max_output_tokens,
                    reserved_cost=reserved_cost, currency=policy.currency, status="reserved",
                )
            except IntegrityError as exc:
                raise FinancialAdmissionDenied("AI_RESERVATION_IDENTITY_CONFLICT", "request identity was reserved concurrently") from exc
            return reservation, False

    def settle(self, *, reservation_id, actual_cost, usage_complete):
        """Settle known usage; retain full exposure for unknown/unpriced outcomes."""
        with transaction.atomic(using=self.using):
            reservation = AIFinancialReservation.objects.using(self.using).select_for_update().get(id=reservation_id)
            if reservation.status in {"settled", "released", "unresolved"}:
                return reservation
            if not usage_complete or actual_cost is None:
                reservation.status = "unresolved"
                reservation.resolution_reason = "UNKNOWN_OR_UNPRICED_USAGE"
            elif actual_cost < 0 or actual_cost > reservation.reserved_cost:
                reservation.status = "unresolved"
                reservation.resolution_reason = "USAGE_OUTSIDE_RESERVED_BOUND"
            else:
                reservation.status = "settled"
                reservation.settled_cost = actual_cost
                reservation.resolution_reason = None
            reservation.settled_at = timezone.now()
            reservation.save(update_fields=["status", "settled_cost", "resolution_reason", "settled_at", "updated_at"])
            return reservation

    def release_before_dispatch(self, *, reservation_id):
        """Only an explicit, proven pre-dispatch failure may release exposure."""
        with transaction.atomic(using=self.using):
            reservation = AIFinancialReservation.objects.using(self.using).select_for_update().get(id=reservation_id)
            if reservation.status == "reserved":
                reservation.status = "released"
                reservation.resolution_reason = "PROVEN_NOT_DISPATCHED"
                reservation.settled_at = timezone.now()
                reservation.save(update_fields=["status", "resolution_reason", "settled_at", "updated_at"])
            return reservation
