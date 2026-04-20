"""System health services."""

from __future__ import annotations

from django.db import DatabaseError, connection


class HealthCheckError(Exception):
    """Raised when a health check dependency is unavailable."""


def check_database_connection() -> None:
    """Run a trivial DB statement to verify database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError as exc:
        raise HealthCheckError("database_unavailable") from exc
