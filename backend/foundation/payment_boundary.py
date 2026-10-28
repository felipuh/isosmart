"""Repository-local signed payment webhook boundary; no gateway calls."""

from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
import time
from typing import Any, Mapping, Protocol
from uuid import UUID

from .canonical import canonical_hash
from .eventing import ConsumerReceiptService
from .onboarding import OnboardingWorkflowService


class PaymentBoundaryError(ValueError):
    pass


class SignedPayloadVerifier(Protocol):
    def verify(self, *, payload: bytes, signature: str, timestamp: int) -> None: ...


def _message(payload: bytes, timestamp: int) -> bytes:
    return f"{timestamp}.".encode() + payload


@dataclass(frozen=True)
class HmacPaymentSigner:
    secret: bytes

    def sign(self, *, payload: bytes, timestamp: int) -> str:
        digest = hmac.new(self.secret, _message(payload, timestamp), sha256).hexdigest()
        return f"v1={digest}"


@dataclass(frozen=True)
class HmacPaymentVerifier:
    secret: bytes
    max_age_seconds: int = 300

    def verify(self, *, payload: bytes, signature: str, timestamp: int) -> None:
        if abs(int(time.time()) - int(timestamp)) > self.max_age_seconds:
            raise PaymentBoundaryError("payment signature timestamp expired")
        expected = HmacPaymentSigner(self.secret).sign(payload=payload, timestamp=timestamp)
        if not hmac.compare_digest(expected, str(signature)):
            raise PaymentBoundaryError("payment signature invalid")


class PaymentVerificationService:
    consumer_name = "onboarding.payment_verification"

    def __init__(self, *, using="worker", verifier: SignedPayloadVerifier):
        self.using = using
        self.verifier = verifier

    def verify(
        self, *, identity, user_id, event_id, payload: Mapping[str, Any],
        signature: str, timestamp: int, actor_id, trace_id,
    ):
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        self.verifier.verify(payload=encoded, signature=signature, timestamp=timestamp)
        if payload.get("status") != "confirmed":
            raise PaymentBoundaryError("payment is not confirmed")
        payment_reference = str(payload.get("payment_reference") or "").strip()
        if not payment_reference:
            raise PaymentBoundaryError("payment_reference is required")

        def handle(received):
            OnboardingWorkflowService(using="app").transition(
                identity=identity,
                user_id=user_id,
                step_key="payment_verification",
                to_status="complete",
                event_id=event_id,
                event_type="payment.confirmed",
                source_reference=f"payment:{payment_reference}",
                actor_id=actor_id,
                trace_id=trace_id,
                state={
                    "payment_reference_hash": canonical_hash(payment_reference),
                    "payload_hash": canonical_hash(received),
                },
            )

        return ConsumerReceiptService(using=self.using).receive(
            identity=identity,
            consumer_name=self.consumer_name,
            event_id=UUID(str(event_id)),
            payload=dict(payload),
            trace_id=trace_id,
            handler=handle,
        )