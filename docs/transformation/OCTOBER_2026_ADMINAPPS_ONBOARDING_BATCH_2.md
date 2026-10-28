# October 2026 — AdminApps baseline reconciliation and onboarding batch 2

Date: 2026-10-05 (America/Costa_Rica)
Scope: repository-local product implementation. This record does not amend the
frozen WP2 matrix or Phase31.5 evidence.

## Boundary and recovered baseline

`E-07 = BLOCKED_BY_EXTERNAL_AUTHORITY / OPERATIONAL_READINESS` concerns an
authentic committed credential rotation, not the existence of the AdminApps
product contract. `E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE` and
`Phase31.5 = EXECUTION_HELD` remain unchanged. Product implementation is
allowed in parallel.

The controlled historical baseline is bound by repository evidence:

- `backend/integration/test_adminapps_endpoint_remediation.py` asserts the
  `ISO_SMART` entitlement URL, permitted and denied entitlement results,
  `source=adminapps`, `fallback=false`, and fail-closed malformed/unreachable
  behavior.
- `docs/governance/evidence/PHASE31_4_V2_5_ADMINAPPS_ENDPOINT_REMEDIATION_V1.json`
  records eight passing focused contract tests and the dynamic endpoint
  correction.
- `docs/governance/evidence/stage_ext_20260917/04-authenticated-transport.json`
  records controlled loopback `X-API-Key` authentication enforcement, invalid
  key `401`, and successful authenticated event delivery.

This is historical controlled-integration evidence only. It does not assert a
currently available authentic runtime or an authentic credential rotation.

## Selected requirements and traceability

| Requirement | Source and authority | Missing behavior | Implementation and test | Current disposition |
|---|---|---|---|---|
| `REQ-ONBOARDING-10` | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, onboarding step 10; `SOURCE_DEFINED` fields and `IMPLEMENTATION_DEFINED_WITHIN_SOURCE_CONSTRAINTS` transport | The existing canonical, PostgreSQL-tested profile command had no HTTP consumer. | `GET /v1/onboarding/organizations` exposes only tenant-scoped canonical QMS organizations. `POST /v1/onboarding/organizational-profile` validates source-listed fields, carries an event idempotency key, and calls the existing command. Route/view tests cover the transport. | `PARTIAL`: no unproven mapping to legacy/AdminApps organization identifiers is created. |
| `REQ-ONBOARDING-12` | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, onboarding step 12; `SOURCE_DEFINED` categories and `IMPLEMENTATION_DEFINED_WITHIN_SOURCE_CONSTRAINTS` metadata transport | The existing atomic metadata/hash ingestion command had no HTTP consumer. | `POST /v1/onboarding/document-references` accepts only an allowed source category, URI, SHA-256 and capture time; it calls the existing evidence/outbox/audit path. The response explicitly reports `content_bytes_read=false`. | `PARTIAL`: this neither uploads bytes nor claims storage/parser/licensing or DocumentVersion semantics. |
| `REQ-API-ONBOARDING-STEP-CONSUMERS` | Derived from the two source-defined journey steps; `IMPLEMENTATION_DEFINED_WITHIN_SOURCE_CONSTRAINTS` | Browser/API consumers needed documented, authenticated contracts. | OpenAPI and the frontend service define the three tenant-bound consumers. The API rejects unknown fields and resolves only the signed principal's tenant. | `COMPLETE` for this transport slice. |

## Security and scope safeguards

- A signed AdminApps bearer remains required by the existing principal resolver.
- The caller selects a canonical ISO Smart organization from the tenant-scoped
  projection; the endpoints do not duplicate or infer AdminApps authority.
- The existing services retain tenant/RLS enforcement, transition provenance,
  immutable audit and outbox behavior. No migration was required.
- Step 12 is intentionally metadata-only. It cannot be used to fabricate
  document content, licensed ISO material, or a Context Twin baseline.

## Verification

- Django focused API and AdminApps contract tests: 28 passing.
- Frontend lint and production build: passing.
- Full backend regression: 658 passing, 0 failures, 0 errors, 0 skipped, on
  the disposable PostgreSQL 18.6 harness. The test-owned container, database,
  roles and volume were removed after the run. No SQLite result is treated as
  authoritative for this slice.
