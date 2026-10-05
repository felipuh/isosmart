# QMS API implementation contract

QMS_API_AUTHORITY = IMPLEMENTATION_DEFINED_WITHIN_SOURCE_CONSTRAINTS

The source OpenAPI defines no `/v1/qms/*` routes. Entities and fields come from the
source catalog (Audit, Finding, Nonconformity, CorrectiveAction, Evidence); the routes
below are an implementation mechanism and are not source-defined.

## Endpoints
GET: `/v1/qms/{capabilities,owners,organizations,requirements,audits,findings,evidence,nonconformities,corrective-actions}`
POST: audits, findings, `findings/<id>/nonconformity`, `nonconformities/<id>/corrective-actions`.
Tenant and actor are always derived server-side from the principal (never from the body).

## Write authorization (QMS_WRITE_POLICY = SEMANTICS_INSUFFICIENT)
The source defines no QMS roles. Writes fail closed:
- `QMS_WRITE_ROLES` (env list, default empty) -> 403 `QMS_WRITE_POLICY_NOT_ESTABLISHED`.
- role claim not in list -> 403 `QMS_WRITE_ROLE_REQUIRED`.
Reads remain available to any active tenant user.

## Open semantics
- status/severity/type: FIELD_DEFINED_SEMANTICS_OPEN (free text, no enums).
- `CorrectiveAction.cause_id`: CAUSE_REFERENCE_SEMANTICS_INSUFFICIENT (no Cause entity).
  CAPA creation returns 409 `CAPA_CAUSE_REFERENCE_UNDEFINED` unless `QMS_CAPA_CREATE_ENABLED=true`.
- Audit and CAPA creation emit no DomainEvent (none defined); Finding emits
  `audit.finding.created`, Nonconformity `nonconformity.detected`; all write ImmutableAuditLog.

## Known residual
`/v1/evidence` (pre-existing, outside this slice) is not gated by `QMS_WRITE_ROLES`.
