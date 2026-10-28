"""Stable internal classification for the future authenticated ingress."""

from enum import IntEnum


class BoundaryStatus(IntEnum):
    AUTHENTICATION_INVALID = 401
    AUTHORIZATION_DENIED = 403
    PROJECTION_CONFLICT = 409
    CONTRACT_INVALID = 422
    AUTHORITY_UNAVAILABLE = 503
