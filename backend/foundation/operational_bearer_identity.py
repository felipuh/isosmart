"""Short-lived bearer issuance for the existing Phase 31.4 runtime identity.

The credential is intentionally an in-memory object.  Its representation and
evidence never contain the raw token, and teardown overwrites its byte buffer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import hashlib
import os
from typing import Any


class OperationalBearerError(RuntimeError):
    """Fail-closed identity or credential contract violation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:
        return f"{self.code}: {super().__str__()}"


@dataclass
class RuntimeBearerCredential:
    identity_id: str
    token_fingerprint: str
    lifetime_seconds: int
    _token: bytearray = field(repr=False)
    token_type: str = "Bearer"
    token_source: str = "adminapps_simplejwt_programmatic_access_token"
    _destroyed: bool = field(default=False, init=False, repr=False)

    def authorization_value(self) -> str:
        if self._destroyed or not self._token:
            raise OperationalBearerError("CREDENTIAL_DESTROYED", "runtime bearer is unavailable")
        return f"{self.token_type} {self._token.decode('ascii')}"

    def write_to_fd(self, descriptor: int) -> None:
        if self._destroyed or not self._token:
            raise OperationalBearerError("CREDENTIAL_DESTROYED", "runtime bearer is unavailable")
        view = memoryview(self._token)
        written = 0
        while written < len(view):
            written += os.write(descriptor, view[written:])

    def evidence(self) -> dict[str, Any]:
        return {
            "token_present": not self._destroyed and bool(self._token),
            "token_type": self.token_type,
            "identity_id": self.identity_id,
            "token_fingerprint": self.token_fingerprint,
            "token_source": self.token_source,
            "token_lifetime_seconds": self.lifetime_seconds,
            "token_persisted": False,
        }

    def destroy(self) -> None:
        for index in range(len(self._token)):
            self._token[index] = 0
        self._token.clear()
        self._destroyed = True


def _required(value: Any, *, code: str, message: str) -> Any:
    if value is None:
        raise OperationalBearerError(code, message)
    return value


def acquire_runtime_bearer(
    identity: Any,
    membership: Any,
    entitlement: Any,
    *,
    token_class: Any,
    issuer: str,
    audience: tuple[str, ...] = ("iso-smart",),
    client_id: str = "phase31-operational-readiness",
    lifetime_seconds: int = 900,
) -> RuntimeBearerCredential:
    """Issue one access token for an already persisted, eligible identity."""
    identity = _required(
        identity,
        code="IDENTITY_NOT_FOUND",
        message="the existing runtime identity is required",
    )
    identity_id = str(getattr(identity, "pk", None) or getattr(identity, "id", ""))
    if not identity_id:
        raise OperationalBearerError("IDENTITY_NOT_FOUND", "runtime identity has no stable subject")
    if not bool(getattr(identity, "is_active", False)):
        raise OperationalBearerError("IDENTITY_INACTIVE", "runtime identity is inactive")

    membership = _required(
        membership,
        code="MEMBERSHIP_NOT_FOUND",
        message="an active tenant membership is required",
    )
    if not bool(getattr(membership, "is_active", False)):
        raise OperationalBearerError("MEMBERSHIP_INACTIVE", "tenant membership is inactive")
    if str(getattr(membership, "user_id", "")) != identity_id:
        raise OperationalBearerError("IDENTITY_BINDING_MISMATCH", "membership subject does not match")
    organization = _required(
        getattr(membership, "organization", None),
        code="TENANT_NOT_FOUND",
        message="membership has no tenant",
    )
    if str(getattr(organization, "status", "")) != "active":
        raise OperationalBearerError("TENANT_INACTIVE", "tenant is not active")

    entitlement = _required(
        entitlement,
        code="ENTITLEMENT_NOT_FOUND",
        message="ISO Smart entitlement is required",
    )
    if str(getattr(entitlement, "organization_id", "")) != str(getattr(organization, "pk", None) or organization.id):
        raise OperationalBearerError("TENANT_BINDING_MISMATCH", "entitlement tenant does not match")
    if not bool(getattr(entitlement, "access_allowed", False)):
        raise OperationalBearerError("ENTITLEMENT_DENIED", "ISO Smart entitlement is not active")
    if lifetime_seconds <= 0 or lifetime_seconds > 3600:
        raise OperationalBearerError("TOKEN_LIFETIME_INVALID", "diagnostic access lifetime must be 1..3600 seconds")

    token = token_class.for_user(identity)
    token.set_exp(lifetime=timedelta(seconds=lifetime_seconds))
    token["iss"] = issuer
    token["aud"] = list(audience)
    token["client_id"] = client_id
    token["email"] = str(getattr(identity, "email", ""))
    token["full_name"] = str(getattr(identity, "full_name", ""))
    token["organization_id"] = str(getattr(organization, "pk", None) or organization.id)
    token["organization_code"] = str(getattr(organization, "code", ""))
    token["organization_name"] = str(getattr(organization, "name", ""))
    token["role"] = str(getattr(membership, "role", "viewer"))
    token["scope"] = "openid profile email tenant:read"
    token["allowed_products"] = ["ISO_SMART"]

    token_subject = str(token.get("user_id") or token.get("sub") or "")
    if token_subject != identity_id:
        raise OperationalBearerError("TOKEN_SUBJECT_MISMATCH", "issued token subject does not match identity")
    encoded = str(token).encode("ascii")
    return RuntimeBearerCredential(
        identity_id=identity_id,
        token_fingerprint=hashlib.sha256(encoded).hexdigest(),
        lifetime_seconds=lifetime_seconds,
        _token=bytearray(encoded),
    )
