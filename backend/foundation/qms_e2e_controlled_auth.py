"""Controlled-principal authentication for the local QMS browser E2E ONLY.

Wired exclusively by ``backend.settings_qms_e2e_controlled``; it is never part of
the default authentication classes. It is NOT an AdminApps integration.
"""

import json
from types import SimpleNamespace
from uuid import UUID

from rest_framework import authentication, exceptions

HEADER = "HTTP_X_CONTROLLED_PRINCIPAL"


class ControlledPrincipalAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        raw = request.META.get(HEADER)
        if not raw:
            return None
        try:
            claims = json.loads(raw)
            UUID(str(claims["user_id"]))
            UUID(str(claims["organization_id"]))
        except (ValueError, KeyError, TypeError) as exc:
            raise exceptions.AuthenticationFailed("invalid controlled principal") from exc
        claims.setdefault("client_id", "qms-controlled-e2e")
        return SimpleNamespace(is_authenticated=True, pk=claims["user_id"]), claims
