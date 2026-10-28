# Stage EXT remediation report — 2026-09-17

## Verdict

**STAGE_EXT_PASS** for the isolated upstream native chain. **Full Phase 31.4 retry is not authorized** because the historical Retry 8 teardown remains `PENDING` and its database could not be positively identified for safe removal. No Phase 31.4 live retry was run. V2.4 and V2.5 were not changed.

## Tenant identity mapping

`AdminApps apps.organizations.Organization.id` is the canonical, immutable global tenant UUID. The AdminApps PostgreSQL migration protects it with an update trigger. ISO Smart stores the same UUID in `TenantProjection.adminapps_tenant_id`; the projection and each QMS organization have their own UUIDs. The isolated smoke observed AdminApps tenant `e7400a3b-a1c2-4b7c-b6c5-4474fb46f505` and local projection `1792f5b0-3a5d-4b31-89d8-a44572293011`.

## AdminApps producer and event contract

The active AdminApps organization create/update/status APIs commit `tenant_integration_outbox` in the same transaction. Initial `source_version=1`; activation emitted version 2 and suspension emitted version 3 for the second tenant. Envelope schema version 1 contains the canonical UUID, event ID/type, source version, occurred time, trace/correlation IDs, aggregate identity, actor ID when available, display-name snapshot, AdminApps status, and mapped lifecycle. The creation response now exposes the canonical UUID. A dispatcher preserves event IDs and order per tenant, retries failures, and records delivery state.

## Authentication and provenance

The dispatcher requires HTTPS except for explicitly enabled loopback HTTP in this isolated smoke. ISO Smart compares the incoming service key to a configured SHA-256 hash before parsing or projecting. A wrong key returned HTTP 401. Valid delivery returned HTTP 201 for both initial events; a controlled replay returned HTTP 200 with `idempotent_replay`. `eventing.adminapps_ingress_receipt` retained both event IDs, issuer, authentication result, schema/source versions, processing status, projection ID, timestamps and replay count after the projection advanced to version 2.

## TenantProjection and QMS Organization

The authenticated ingress used `ContractOnlyAdminAppsAdapter → validate_projection_event → ProjectionWriterService`; it did not replace the writer. The QMS command used a server-resolved trusted tenant identity, active local lifecycle, fresh AdminApps product validation without fallback, and live AdminApps actor membership with an allowed role. It created two QMS organizations under one projection. A repeated request key returned the original IDs; a conflicting payload was rejected. Unknown tenant, unauthorized actor, cross-tenant actor, and inactive tenant were denied. A deliberate transaction failure left no extra organization, event, outbox or audit row.

`organization.created` schema v1, transactional outbox and immutable audit were committed with each organization. Actor, tenant, organization ID, trace ID, request key and optional correlation ID were recorded. Native Process and Opportunity commands then created `74942c31-58e7-47c2-bfba-d673055ed056` and `64ffaa1d-3ec1-49c3-8aee-a149573b8f67`. The Opportunity's `process_id` matched the Process; its lineage UUID equalled its native ID and revision was 1. Their event/outbox/audit rows were verified.

## Isolated smoke environment and tests

The smoke used an isolated PostgreSQL 18.4 cluster under `/tmp`, separate AdminApps and ISO Smart databases, real AdminApps API/database, the real ISO Smart foundation service/API/PostgreSQL, and authenticated loopback delivery. It did not contact production, staging or shared development. ISO Smart foundation migrations 0001–0005 were applied and the new Stage EXT tables were applied with the migration SQL; the entire ISO Smart migration chain was not replayed in this smoke environment. AdminApps migrations, including the new outbox migration, ran normally. No TenantProjection or QMS Organization row was directly inserted by the smoke.

Executed checks:

- AdminApps: `manage.py test apps.organizations.tests_tenant_events` — **5 passed**.
- AdminApps: `manage.py makemigrations organizations --check --dry-run` — **no changes**.
- ISO Smart: `manage.py test foundation.test_stage_ext_contract foundation.tests.ProjectionContractTests` with isolated SQLite test settings — **12 passed**.
- PostgreSQL smoke: native tenant creation, event production/delivery/replay, projection, two QMS organization creations, Process, Opportunity, event/outbox/audit, rollback and authorization negatives — **passed**.
- The isolated wrong-key POST returned **401**.

## Blockers and Retry 8

`P1-EXTERNAL-ADMINAPPS-AUTHORITY-BOUNDARY` and `P1-ORGANIZATION-NATIVE-PRODUCER-MISSING` are **closed for Stage EXT** by the native, authenticated, provenance-preserving smoke. Stage EXT P0=0, P1=0. Historical Phase 31.4 findings are unchanged.

Retry 8's recorded `teardown=PENDING` remains unresolved. A fresh default Podman inventory was empty; the workspace Podman inventory contained only an older, exited `smart3ai-postgres18` container. The accessible local PostgreSQL server was queried read-only: it is version 18.4 and has no `phase31_4_retry8` database. The Retry 8 audit names PostgreSQL 18.6 (Debian), so absence on the 18.4 server does not prove historical teardown. The 18.6 resource was not positively identified; nothing historical was deleted or marked resolved. The next full retry ID was not allocated or executed.

A repository-wide search found no executed Retry 9 artifact; its only mention was the earlier boundary verdict's candidate note. Retry 9 remains a candidate, subject to a fresh check after teardown is resolved.

## Changed product files

AdminApps:

- `backend/apps/organizations/models.py`
- `backend/apps/organizations/serializers.py`
- `backend/apps/organizations/views.py`
- `backend/apps/organizations/tenant_events.py`
- `backend/apps/organizations/migrations/0004_tenantintegrationoutbox.py`
- `backend/apps/organizations/management/commands/deliver_tenant_events.py`
- `backend/apps/organizations/tests_tenant_events.py`
- `docs/PRODUCT_NEUTRAL_ADMINAPPS_CONTRACT.md`

ISO Smart:

- `backend/backend/settings.py`
- `backend/backend/urls.py`
- `backend/foundation/projection_contract.py`
- `backend/foundation/adminapps_ingress.py`
- `backend/foundation/qms_organization.py`
- `backend/foundation/migrations/0024_adminapps_ingress_receipt.py`
- `backend/foundation/test_stage_ext_contract.py`
- `docs/adr/0002-adminapps-control-plane-boundary.md`
- `docs/transformation/ISO_SMART_AI_ADMINAPPS_CONTRACT.md`
- `docs/transformation/STAGE_EXT_REMEDIATION_REPORT_20260917.md`
- `docs/governance/evidence/stage_ext_20260917/` (twelve separate evidence artifacts and a SHA-256 manifest)

The evidence manifest lists the SHA-256 of each separate artifact. It is separate from all full Phase 31.4 retry evidence.
