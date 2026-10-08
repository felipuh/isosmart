"""Controlled-principal authentication for explicitly opted-in local browser E2E.

This authentication class is wired only by dedicated E2E settings modules.  It
is never included in the default application authentication configuration.
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
        claims.setdefault("client_id", "controlled-browser-e2e")
        return SimpleNamespace(is_authenticated=True, pk=claims["user_id"]), claims
