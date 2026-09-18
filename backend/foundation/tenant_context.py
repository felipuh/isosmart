from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID

from django.db import transaction


@dataclass(frozen=True)
class TrustedTenantIdentity:
    """Server-resolved identity accepted at the database trust boundary.

    Authentication/authorization adapters create this value only after resolving
    an authorized local/AdminApps projection. Request tenant inputs are not part
    of this API.
    """

    subject: str
    tenant_id: UUID


def _set_transaction_context(connection, identity, actor_id, trace_id):
    """Private low-level setter; never call with request-controlled tenant data."""

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, true), "
            "set_config('app.actor_id', %s, true), "
            "set_config('app.trace_id', %s, true)",
            [str(identity.tenant_id), str(actor_id), str(trace_id)],
        )
        cursor.execute("SELECT current_setting('app.tenant_id', true)")
        if cursor.fetchone()[0] != str(identity.tenant_id):
            raise RuntimeError("tenant context verification failed")


def bind_trusted_tenant_context_in_transaction(
    identity, *, actor_id, trace_id, using="default"
):
    """Bind trusted tenant context inside a caller-owned transaction.

    This is the composition seam for internal, database-only commands.  It is
    deliberately not a context manager and never opens, commits, rolls back, or
    creates a savepoint.
    """

    if not isinstance(identity, TrustedTenantIdentity):
        raise TypeError("identity must be a TrustedTenantIdentity")
    connection = transaction.get_connection(using)
    if not connection.in_atomic_block:
        raise RuntimeError("an active caller-owned transaction is required")
    _set_transaction_context(connection, identity, actor_id, trace_id)


@contextmanager
def trusted_tenant_context(identity, *, actor_id, trace_id, using="default"):
    """Set and verify transaction-local context from a trusted identity object."""

    connection = transaction.get_connection(using)
    if connection.in_atomic_block:
        raise RuntimeError(
            "trusted tenant context must own the outermost transaction boundary"
        )

    with transaction.atomic(using=using):
        _set_transaction_context(connection, identity, actor_id, trace_id)
        yield
