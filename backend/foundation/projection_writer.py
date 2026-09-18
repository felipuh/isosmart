"""The only application service authorized to mutate AdminApps projections."""

import uuid
from dataclasses import dataclass
from enum import Enum

from django.db import connections, transaction

from .projection_contract import (
    AggregateType,
    ProjectionEvent,
    ProjectionEventType,
)


class ProjectionResultKind(str, Enum):
    APPLIED = "applied"
    IDEMPOTENT_REPLAY = "idempotent_replay"


@dataclass(frozen=True)
class ProjectionResult:
    kind: ProjectionResultKind
    projection_id: uuid.UUID
    source_version: int
    event_id: uuid.UUID


class ProjectionFailure(RuntimeError):
    status_equivalent = 409
    failure_code = "projection_conflict"


class ProjectionVersionConflict(ProjectionFailure):
    failure_code = "source_version_conflict"


class ProjectionVersionRegression(ProjectionFailure):
    failure_code = "source_version_regression"


class ImmutableProjectionConflict(ProjectionFailure):
    failure_code = "immutable_projection_reassignment"


class InvalidLifecycleTransition(ProjectionFailure):
    failure_code = "invalid_lifecycle_transition"


class ProjectionAuthorityUnavailable(ProjectionFailure):
    status_equivalent = 503
    failure_code = "adminapps_authority_unavailable"


_TENANT_TRANSITIONS = {
    "pending": {"pending", "active", "suspended", "deprovisioning", "drifted", "unknown"},
    "active": {"active", "suspended", "deprovisioning", "drifted", "unknown"},
    "suspended": {"suspended", "active", "deprovisioning", "drifted", "unknown"},
    "deprovisioning": {"deprovisioning", "deleted_tombstone", "drifted"},
    "deleted_tombstone": {"deleted_tombstone"},
    "drifted": {"drifted", "pending", "active", "suspended", "deprovisioning"},
    "unknown": {"unknown", "pending", "active", "suspended", "deprovisioning", "drifted"},
}
_USER_TRANSITIONS = {
    "active": {"active", "suspended", "revoked", "deleted_tombstone"},
    "suspended": {"suspended", "active", "revoked", "deleted_tombstone"},
    "revoked": {"revoked", "deleted_tombstone"},
    "deleted_tombstone": {"deleted_tombstone"},
}


class ProjectionWriterService:
    """Apply a validated event atomically through the projector DB alias."""

    def __init__(self, *, using="projector"):
        self.using = using

    def apply(self, event: ProjectionEvent) -> ProjectionResult:
        if not isinstance(event, ProjectionEvent):
            raise TypeError("ProjectionWriterService accepts only validated ProjectionEvent values")
        with transaction.atomic(using=self.using):
            connection = connections[self.using]
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('app.projection_source', %s, true), "
                    "set_config('app.trace_id', %s, true)",
                    [event.source, str(event.trace_id)],
                )
                # Serialize both event identity and aggregate identity.  This
                # avoids reducing concurrent replay/conflict semantics to an
                # opaque unique-constraint IntegrityError.
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0)), "
                    "pg_advisory_xact_lock(hashtextextended(%s,0))",
                    [f"event:{event.event_id}", f"aggregate:{event.aggregate_type.value}:{event.aggregate_id}"],
                )
                if event.aggregate_type is AggregateType.TENANT:
                    return self._apply_tenant(cursor, event)
                return self._apply_user(cursor, event)

    @staticmethod
    def _version_result(row, event):
        projection_id, current_version, current_event_id = row
        current_event_id = uuid.UUID(str(current_event_id)) if current_event_id else None
        if event.source_version < current_version:
            raise ProjectionVersionRegression(
                f"source version {event.source_version} is lower than {current_version}"
            )
        if event.source_version == current_version:
            if event.event_id == current_event_id:
                return ProjectionResult(
                    ProjectionResultKind.IDEMPOTENT_REPLAY,
                    uuid.UUID(str(projection_id)),
                    current_version,
                    event.event_id,
                )
            raise ProjectionVersionConflict(
                f"source version {current_version} already belongs to event {current_event_id}"
            )
        if event.event_id == current_event_id:
            raise ProjectionVersionConflict("event identity cannot be reused at a different version")
        return None

    def _apply_tenant(self, cursor, event):
        cursor.execute(
            "SELECT id,adminapps_tenant_id,source_version FROM qms.tenant_projection WHERE source_event_id=%s",
            [str(event.event_id)],
        )
        prior_event = cursor.fetchone()
        if prior_event:
            if str(prior_event[1]) == str(event.adminapps_tenant_id) and prior_event[2] == event.source_version:
                return ProjectionResult(
                    ProjectionResultKind.IDEMPOTENT_REPLAY,
                    uuid.UUID(str(prior_event[0])), event.source_version, event.event_id,
                )
            raise ProjectionVersionConflict("event identity is already materialized by another tenant/version")
        cursor.execute(
            "SELECT id,source_version,source_event_id,lifecycle_status "
            "FROM qms.tenant_projection WHERE adminapps_tenant_id=%s FOR UPDATE",
            [str(event.adminapps_tenant_id)],
        )
        row = cursor.fetchone()
        requested_status = (
            "suspended"
            if event.event_type is ProjectionEventType.TENANT_SUSPENDED
            else str(event.payload.get("lifecycle_status") or "active")
        )
        if row:
            outcome = self._version_result(row[:3], event)
            if outcome:
                return outcome
            if requested_status not in _TENANT_TRANSITIONS.get(row[3], set()):
                raise InvalidLifecycleTransition(f"tenant lifecycle {row[3]} -> {requested_status} is not allowed")
            display_name = str(event.payload.get("display_name") or "").strip()
            if not display_name:
                cursor.execute(
                    "SELECT display_name_snapshot FROM qms.tenant_projection WHERE id=%s",
                    [str(row[0])],
                )
                display_name = cursor.fetchone()[0]
            cursor.execute(
                "UPDATE qms.tenant_projection SET source_version=%s,source_event_id=%s,"
                "display_name_snapshot=%s,lifecycle_status=%s,last_synced_at=%s,updated_at=statement_timestamp() "
                "WHERE id=%s",
                [event.source_version, str(event.event_id), display_name, requested_status, event.occurred_at, str(row[0])],
            )
            projection_id = uuid.UUID(str(row[0]))
        else:
            if event.event_type is not ProjectionEventType.TENANT_PROVISIONED:
                raise ProjectionAuthorityUnavailable("tenant projection does not exist for non-provisioning event")
            projection_id = uuid.uuid4()
            cursor.execute(
                "INSERT INTO qms.tenant_projection "
                "(id,adminapps_tenant_id,source_version,source_event_id,display_name_snapshot,"
                "lifecycle_status,provisioning_status,reconciliation_status,last_synced_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,'pending','in_sync',%s)",
                [str(projection_id), str(event.adminapps_tenant_id), event.source_version,
                 str(event.event_id), str(event.payload["display_name"]).strip(), requested_status,
                 event.occurred_at],
            )
        return ProjectionResult(ProjectionResultKind.APPLIED, projection_id, event.source_version, event.event_id)

    def _apply_user(self, cursor, event):
        cursor.execute(
            "SELECT id FROM qms.tenant_projection WHERE adminapps_tenant_id=%s",
            [str(event.adminapps_tenant_id)],
        )
        tenant = cursor.fetchone()
        if tenant is None:
            raise ProjectionAuthorityUnavailable("user event references an unknown tenant projection")
        tenant_id = tenant[0]
        cursor.execute(
            "SELECT id,adminapps_user_id,source_version FROM qms.user_projection WHERE source_event_id=%s",
            [str(event.event_id)],
        )
        prior_event = cursor.fetchone()
        if prior_event:
            if str(prior_event[1]) == str(event.aggregate_id) and prior_event[2] == event.source_version:
                return ProjectionResult(
                    ProjectionResultKind.IDEMPOTENT_REPLAY,
                    uuid.UUID(str(prior_event[0])), event.source_version, event.event_id,
                )
            raise ProjectionVersionConflict("event identity is already materialized by another user/version")
        cursor.execute(
            "SELECT id,source_version,source_event_id,lifecycle_status,tenant_id "
            "FROM qms.user_projection WHERE adminapps_user_id=%s FOR UPDATE",
            [str(event.aggregate_id)],
        )
        row = cursor.fetchone()
        requested_status = (
            "revoked" if event.event_type is ProjectionEventType.USER_REVOKED
            else str(event.payload.get("lifecycle_status") or "")
        )
        if requested_status not in _USER_TRANSITIONS:
            raise InvalidLifecycleTransition(f"unsupported user lifecycle status: {requested_status}")
        if row:
            if str(row[4]) != str(tenant_id):
                raise ImmutableProjectionConflict("user tenant association is immutable in the current contract")
            outcome = self._version_result(row[:3], event)
            if outcome:
                return outcome
            if requested_status not in _USER_TRANSITIONS.get(row[3], set()):
                raise InvalidLifecycleTransition(f"user lifecycle {row[3]} -> {requested_status} is not allowed")
            cursor.execute(
                "UPDATE qms.user_projection SET source_version=%s,source_event_id=%s,"
                "lifecycle_status=%s,last_synced_at=%s,updated_at=statement_timestamp() WHERE id=%s",
                [event.source_version, str(event.event_id), requested_status, event.occurred_at, str(row[0])],
            )
            projection_id = uuid.UUID(str(row[0]))
        else:
            if event.event_type is ProjectionEventType.USER_REVOKED:
                raise ProjectionAuthorityUnavailable("cannot revoke an unknown user projection")
            projection_id = uuid.uuid4()
            cursor.execute(
                "INSERT INTO qms.user_projection "
                "(id,adminapps_user_id,tenant_id,source_version,source_event_id,lifecycle_status,last_synced_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                [str(projection_id), str(event.aggregate_id), str(tenant_id), event.source_version,
                 str(event.event_id), requested_status, event.occurred_at],
            )
        return ProjectionResult(ProjectionResultKind.APPLIED, projection_id, event.source_version, event.event_id)
