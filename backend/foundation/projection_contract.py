"""AdminApps tenant v1 envelope; transport authentication is enforced at ingress."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID


CONTRACT_SCHEMA_VERSION = 1
ADMINAPPS_SOURCE = "adminapps"
ADMINAPPS_TENANT_STATUS = {
    "trial": "active", "active": "active",
    "inactive": "suspended", "suspended": "suspended",
}


class ProjectionEventType(str, Enum):
    TENANT_PROVISIONED = "tenant.provisioned"
    TENANT_UPDATED = "tenant.updated"
    TENANT_SUSPENDED = "tenant.suspended"
    USER_UPDATED = "user.updated"
    USER_REVOKED = "user.revoked"


class AggregateType(str, Enum):
    TENANT = "tenant"
    USER = "user"


class ContractValidationError(ValueError):
    """Malformed/unsupported event; equivalent to an internal 422 result."""

    failure_code = "contract_validation_failed"
    status_equivalent = 422


@dataclass(frozen=True)
class ProjectionEvent:
    event_id: UUID
    event_type: ProjectionEventType
    schema_version: int
    source: str
    source_version: int
    occurred_at: datetime
    trace_id: UUID
    correlation_id: UUID | None
    aggregate_type: AggregateType
    aggregate_id: UUID
    adminapps_tenant_id: UUID
    payload: Mapping[str, Any]


_EVENT_AGGREGATES = {
    ProjectionEventType.TENANT_PROVISIONED: AggregateType.TENANT,
    ProjectionEventType.TENANT_UPDATED: AggregateType.TENANT,
    ProjectionEventType.TENANT_SUSPENDED: AggregateType.TENANT,
    ProjectionEventType.USER_UPDATED: AggregateType.USER,
    ProjectionEventType.USER_REVOKED: AggregateType.USER,
}


def _required(raw: Mapping[str, Any], field: str) -> Any:
    value = raw.get(field)
    if value is None or value == "":
        raise ContractValidationError(f"{field} is required")
    return value


def _uuid(raw: Mapping[str, Any], field: str) -> UUID:
    try:
        return UUID(str(_required(raw, field)))
    except (TypeError, ValueError) as exc:
        raise ContractValidationError(f"{field} must be a UUID") from exc


def _timestamp(raw: Mapping[str, Any], field: str) -> datetime:
    value = _required(raw, field)
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ContractValidationError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractValidationError(f"{field} must include a timezone")
    return parsed


def validate_projection_event(raw: Mapping[str, Any]) -> ProjectionEvent:
    if not isinstance(raw, Mapping):
        raise ContractValidationError("event envelope must be an object")
    schema_version = _required(raw, "schema_version")
    source_version = _required(raw, "source_version")
    if type(schema_version) is not int or type(source_version) is not int:
        raise ContractValidationError("schema_version and source_version must be integers")
    if schema_version != CONTRACT_SCHEMA_VERSION:
        raise ContractValidationError(f"unsupported schema_version: {schema_version}")
    if source_version < 0:
        raise ContractValidationError("source_version cannot be negative")
    source = str(_required(raw, "source"))
    if source != ADMINAPPS_SOURCE:
        raise ContractValidationError(f"unsupported source: {source}")
    try:
        event_type = ProjectionEventType(str(_required(raw, "event_type")))
    except ValueError as exc:
        raise ContractValidationError(f"unknown event_type: {raw.get('event_type')}") from exc
    try:
        aggregate_type = AggregateType(str(_required(raw, "aggregate_type")))
    except ValueError as exc:
        raise ContractValidationError(f"unknown aggregate_type: {raw.get('aggregate_type')}") from exc
    if _EVENT_AGGREGATES[event_type] is not aggregate_type:
        raise ContractValidationError("event_type does not match aggregate_type")
    payload = _required(raw, "payload")
    if not isinstance(payload, Mapping):
        raise ContractValidationError("payload must be an object")
    if event_type in {
        ProjectionEventType.TENANT_PROVISIONED,
        ProjectionEventType.TENANT_UPDATED,
    } and not str(payload.get("display_name") or "").strip():
        raise ContractValidationError("tenant payload requires display_name")
    if aggregate_type is AggregateType.TENANT:
        lifecycle = payload.get('lifecycle_status')
        if lifecycle is not None and lifecycle not in {'active', 'suspended'}:
            raise ContractValidationError('unsupported tenant lifecycle_status')
        adminapps_status = payload.get('adminapps_status')
        if adminapps_status is not None and (
            adminapps_status not in ADMINAPPS_TENANT_STATUS or
            lifecycle != ADMINAPPS_TENANT_STATUS[adminapps_status]
        ):
            raise ContractValidationError('AdminApps status does not match tenant lifecycle')
    if event_type is ProjectionEventType.USER_UPDATED and not str(payload.get("lifecycle_status") or "").strip():
        raise ContractValidationError("user payload requires lifecycle_status")
    correlation = raw.get("correlation_id")
    try:
        correlation_id = UUID(str(correlation)) if correlation not in (None, "") else None
    except (TypeError, ValueError) as exc:
        raise ContractValidationError("correlation_id must be a UUID when supplied") from exc
    aggregate_id = _uuid(raw, "aggregate_id")
    if aggregate_type is AggregateType.TENANT and aggregate_id != _uuid(raw, "adminapps_tenant_id"):
        raise ContractValidationError("tenant aggregate_id must equal adminapps_tenant_id")
    return ProjectionEvent(
        event_id=_uuid(raw, "event_id"),
        event_type=event_type,
        schema_version=schema_version,
        source=source,
        source_version=source_version,
        occurred_at=_timestamp(raw, "occurred_at"),
        trace_id=_uuid(raw, "trace_id"),
        correlation_id=correlation_id,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        adminapps_tenant_id=_uuid(raw, "adminapps_tenant_id"),
        payload=MappingProxyType(dict(payload)),
    )
