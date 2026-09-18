# Phase 31.4 V2.5 — external authority boundary verdict

**Verdict: BLOCKED.** This is a read-only architecture and repository audit, not an upstream smoke test or a live retry. Stage EXT (External Authority Readiness) is **FAIL**. Stage B and promotion are not authorized by this finding. No AdminApps instance, database, webhook, or external service was contacted.

## System of record and entity identity

ADR-0002 and `ISO_SMART_AI_ADMINAPPS_CONTRACT.md` assign global tenant, identity, access, and provisioning authority to AdminApps. They assign the QMS `Organization` aggregate to ISO Smart. `foundation.TenantProjection` is a local projection with its own UUID and a distinct `adminapps_tenant_id`. `foundation.Organization` is a local QMS aggregate with its own UUID and a required FK to that projection. These are different concepts, even though AdminApps also calls its customer/tenant model `Organization`.

In the active AdminApps backend (`backend/config/settings.py` installs `apps.organizations`), `apps.organizations.Organization` is the customer record. It has a UUID primary key and can be created through `POST /api/organizations/`, guarded by `IsSuperAdmin`; the serializer creates the row and settings. This identifies a **candidate** source for the global tenant identity. The repositories do not contain an approved mapping that equates this UUID with the provisional ISO Smart envelope's `adminapps_tenant_id`, nor a tenant aggregate/event producer. The other `backend/organizations` tree is not the active installed app and has a different integer-ID model; it must not be used to infer the contract.

The ISO Smart `qms.Organization` corresponds to option **C: local QMS producer required**. It is neither an AdminApps organization projection nor a derivation performed by `ProjectionWriterService`. The Phase 2 report explicitly says the projector has no business DML on `qms.organization`; its existing `OrganizationEventingService.rename` requires a row already present. No native QMS organization creation command was found. The Phase 2 schema permits multiple QMS organizations per tenant, so automatically copying the AdminApps customer row would impose an unapproved one-to-one rule.

The active AdminApps creation API currently persists a customer `Organization` and its settings; it does not emit the provisional `tenant.provisioned` event. Its integration API exposes an API-key-protected organization read and product access validation, but neither response is the versioned provisioning event required by `ProjectionWriterService`. The AdminApps customer record's UUID is therefore only a candidate canonical tenant identifier. The shared contract must specify whether this UUID is the tenant aggregate ID, how status `trial`/`active` maps to tenant lifecycle, and how the initial source version is assigned. These choices cannot be inferred from similarly named models.

## Event and projection path

ISO Smart defines a **provisional internal**, transport-neutral `tenant.provisioned` schema v1 in `foundation/projection_contract.py`: `event_id`, `event_type`, `schema_version`, `source`, `source_version`, `occurred_at`, `trace_id`, `aggregate_type`, `aggregate_id`, `adminapps_tenant_id`, `payload.display_name`, and optional `correlation_id`. It requires UUID IDs, timezone-aware time, `source=adminapps`, nonnegative source version, matching tenant aggregate/type, and `aggregate_id == adminapps_tenant_id`. `ContractOnlyAdminAppsAdapter.receive` validates the envelope and passes a `ProjectionEvent` to `ProjectionWriterService`; the writer atomically inserts/updates `TenantProjection`, checks source versions and lifecycle, and treats a replay of the current event/version as idempotent.

This is **not an authenticated live ingress**. `projection_contract.py` calls the vocabulary provisional; `adminapps_adapter.py` explicitly has no transport. The validator checks a source *string*, not a signature, issuer, authenticated channel, product entitlement, nonce, or durable inbox receipt. `ProjectionWriterService` verifies the DTO type and database semantics; it does not independently prove external origin. Earlier event IDs can no longer be verified through the current projection row after a later version replaces `source_event_id`. No matching `tenant.provisioned` producer, versioned outbox, signed webhook, or delivery path was found in the active AdminApps app. The AdminApps integration area's event endpoint is for landing analytics, not tenant provisioning.

Therefore an envelope with the right shape would be insufficient evidence of AdminApps authority. It must not be submitted to this adapter as a fabricated live event.

The narrowest viable implementation route is **Option B, an isolated real AdminApps instance**, after the shared tenant mapping and event contract are approved. AdminApps must emit the real event through an authenticated, durable delivery path; ISO Smart must verify that path before invoking the existing contract validator and writer. A separate ISO Smart product command must then create the QMS organization under the projected tenant. The organization command's actor authorization and idempotency policy remain undefined, so implementing it now would invent governance rules. Option A can use the same contract if controlled live access becomes available. Options C and D remain conditional on explicit governance approval and source proof.

## Stage EXT — external precondition contract

| Gate | Required evidence before a full live retry | Current result |
| --- | --- | --- |
| E1 AdminApps source | Approved mapping from AdminApps customer/tenant identity to `adminapps_tenant_id`; authenticated creation command and a real versioned event producer | **BLOCKED**: customer API exists, mapping/event producer absent |
| E2 transport and authority | Authenticated delivery, issuer/signature or equivalent channel verification, schema/version, event ID, replay protection, entitlement/tenant authority, and consumer contract tests | **BLOCKED**: ISO adapter is contract-only |
| E3 TenantProjection | Native writer consumes E1 and records event ID/version; database row points to the canonical external UUID | **NOT EXECUTED** |
| E4 QMS Organization | ISO Smart product command creates its own QMS organization under E3 after an authorized actor/tenant decision; transaction emits event, outbox, audit | **BLOCKED**: native creation producer and its authorization contract absent |
| E5 relation | Persisted `Organization.tenant_id` equals E3's local projection ID, with tenant RLS and immutable FK verified | **NOT EXECUTED** |
| E6 upstream smoke | E1 → projection → local QMS organization → `QmsContextCommandService.create_process` → `RiskOpportunityObjectiveCommandService.create_opportunity`, with persisted IDs and event/outbox/audit evidence | **NOT EXECUTED**; `UPSTREAM_NATIVE_CHAIN = BLOCKED` |

E1–E5 are external or upstream preconditions to Stage B, not outputs to be attributed to the V2.5 phase graph. A Stage EXT PASS requires all six, including the smoke chain, on an isolated real integration instance or an explicitly approved provenance-preserving alternative. An authoritative captured event replay must be labelled `AUTHORITATIVE_EXTERNAL_EVENT_REPLAY`, include verifiable original provenance, and prove idempotency; it cannot be described as a newly produced live event. No such artifact was identified in this audit.

## Evidence ownership and required smoke assertions

1. **AdminApps external evidence:** customer/tenant creation request and authorization outcome, canonical UUID, emitted event ID/type/schema/version/time, authority proof, and delivery receipt. Do not assume the AdminApps customer UUID is the ISO tenant UUID until the shared contract approves that mapping.
2. **ISO Smart projection evidence:** authenticated ingress result, `ProjectionWriterService` result, `TenantProjection` local ID, `adminapps_tenant_id`, source event ID/version, validation result, and controlled replay result.
3. **ISO Smart QMS evidence:** authorized local organization creation command and actor, QMS organization ID and tenant FK, `organization.created` event/outbox/audit; then native Process ID/event/outbox/audit and native Opportunity ID/lineage/event/outbox/audit. The opportunity's `process_id` must equal the newly persisted Process ID.

## Blockers and route to the next retry

| Priority | ID | Owner / closure condition |
| --- | --- | --- |
| P1 | `P1-EXTERNAL-ADMINAPPS-AUTHORITY-BOUNDARY` | AdminApps and ISO Smart integration owners agree on canonical tenant mapping, real event producer/schema, authenticated delivery, consumer validation, and provenance evidence. |
| P1 | `P1-ORGANIZATION-NATIVE-PRODUCER-MISSING` | ISO Smart product owners add an authorized QMS organization creation command outside the Phase 31.4 harness, with validation, event/outbox/audit, tenant and actor checks, idempotency policy, and integration tests. This is a product capability gap, not an AdminApps Organization consumer gap. |

P0: **0 identified in this boundary audit**. P1: **2 open**. These do not reclassify the V2.5 runtime, composition, registry, migration, or UUID behavior as defective. Existing retry findings remain historical evidence, not overwritten or declared closed here.

The local organization gap is a **product architecture defect**, not an external AdminApps organization-consumer defect: AdminApps owns the customer/tenant authority, while ISO Smart owns the QMS aggregate. Until the product command and its authorization contract exist, `P1-ORGANIZATION-NATIVE-PRODUCER-MISSING` remains open. If product owners reject local QMS ownership, ADR-0002 and the shared contract must be revised before an external organization producer can be implemented; no adapter should silently change this ownership.

Use an isolated AdminApps test instance (Option B) once its real producer and shared contract exist, or an approved live AdminApps source (Option A). Options C/D require explicit governance authorization and verifiable external provenance. After E1–E6 pass, choose the next unused retry number (Retry 9 appears next after the recorded Retry 8, subject to a repository-wide check at execution time), verify Retry 8's separately recorded `teardown=PENDING` has been resolved, start Stage B only with captured canonical IDs, and execute the full V2.5 graph. Do not label the upstream smoke as the full live retry. No row insertion, synthetic event, fixture authority, direct ORM organization seed, or validation bypass can close this gate.

## Audit scope

Read-only inspection covered the active AdminApps organization model/view/serializer/URL and integration area; ISO Smart ADR-0002, AdminApps contract, tenant model, Phase 2 report, `TenantProjection`/`Organization` models and migration, projection contract/adapter/writer, organization eventing service, QMS Process and Opportunity commands, V2.5 runtime, and the Retry 8 blocker. No database integration test or AdminApps live source was available, so no upstream smoke assertion is marked PASS. The audit changed only this report.

Source anchors: ISO Smart `docs/adr/0002-adminapps-control-plane-boundary.md`, `docs/transformation/ISO_SMART_AI_ADMINAPPS_CONTRACT.md`, `backend/foundation/projection_contract.py`, `backend/foundation/adminapps_adapter.py`, `backend/foundation/projection_writer.py`, `backend/foundation/migrations/0002_projection_organization_user_foundation.py`, `backend/foundation/eventing.py`, `backend/foundation/qms_context.py`, and `backend/foundation/risk_objective.py`; AdminApps `backend/config/settings.py`, `backend/config/urls.py`, `backend/apps/organizations/{models,serializers,views}.py`, `backend/apps/integration/{urls,views}.py`, and `docs/PRODUCT_NEUTRAL_ADMINAPPS_CONTRACT.md`. The repository search also covered producer/event names, services, migrations, adapters, fixtures, and existing Phase 31.4 evidence. Existing local edits in both repositories were preserved.
