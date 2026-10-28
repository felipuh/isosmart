"""Explicit PostgreSQL-only settings for repository integration checks."""

import os

from .settings import *  # noqa: F401,F403


if DATABASES["default"].get("ENGINE") != "django.db.backends.postgresql":
    raise RuntimeError(
        "PostgreSQL integration settings refuse a non-PostgreSQL default database"
    )

if os.getenv("ISO_SMART_POSTGRES_INTEGRATION") != "1":
    raise RuntimeError(
        "ISO_SMART_POSTGRES_INTEGRATION=1 is required for PostgreSQL integration settings"
    )
