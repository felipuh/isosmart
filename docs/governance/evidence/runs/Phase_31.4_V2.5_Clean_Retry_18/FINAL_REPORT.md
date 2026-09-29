# Phase 31.4 V2.5 Clean Retry 18 — Final Report

## Verdict

`EVIDENCE_RUN_FAIL`

## Run ID

`Phase 31.4 V2.5 Clean Retry 18`

## Pre-flight

PASS — authorization and V3 SHA-256 matched; V3 integrity passed; protected sources `22/22`; no source drift; initial P0=`0`, P1=`0`; evidence root had no collision.

## Environment

PASS — two isolated PostgreSQL 18.6 containers, networks, volumes, databases, and unique ports (`41491`, `37319`); no Retry 17 reuse and no shared resources.

## Migrations

PASS — AdminApps and ISO Smart migrations completed; runtime roles and DB session configuration passed; pending=`0`, fake=`0`, manual patches=`0`.

## PRECREATION_INTEGRITY

PASS — executor `PrecreationIntegrityExecutor`, operation `verify_precreation_integrity`, assertions `9/9`, retained evidence readback and hash PASS.

## Stage EXT

FAIL — 4/6 identities resolved. AdminApps tenant, AdminApps actor, TenantProjection, and UserProjection were retained with matching readbacks. QMS Organization and Process were not created.

## Phases

Required=`33`; executed=`1`; PASS=`1`; FAIL=`0`; NOT_RUN=`32`. Stage EXT is a prerequisite outside the 33-phase topology and failed after PRECREATION_INTEGRITY, so later phases were not executed.

## First blocker

P1 configuration blocker at `STAGE_EXT` / `QmsOrganizationCommandService.create_organization`: entitlement validation used `http://127.0.0.1:8000` rather than the allocated isolated AdminApps HTTP endpoint. The connection failed and authorization failed closed with `AdminApps product entitlement denied`.

## Native captures

Expected=`565`; resolved=`0`; unresolved=`565`. The capture phase was NOT_RUN; no fixture, historical, or `captured:*` completion was accepted.

## Upstream/external identities

Authority is explicitly `SYNTHETIC_TEST_AUTHORITY`. Upstream external: 2 resolved. Local traceable projections: 2 resolved. ISO Smart native QMS: 0 resolved, 2 unresolved.

## Live graph

NOT_RUN — members=`0`, fields=`0`, unresolved=`1664`, hash=`null`.

## Exact comparison

NOT_RUN — no live graph; no Retry 16 hash or offline output reused.

## Event/outbox/audit

NOT_RUN — corresponding phase not reached.

## Authority

PARTIAL — `SYNTHETIC_TEST_AUTHORITY`; no production authority claimed; human approval and execution authorization NOT_RUN.

## Security

NOT_RUN — 0 probes executed.

## Transactions

NOT_RUN — rollback and idempotency assertions not reached.

## SHA manifest

PASS — every retained Retry 18 artifact is hashed; only the manifest itself is excluded.

## Teardown

PASS — only Retry 18 resources removed; no global prune.

## Post-teardown verification

PASS — containers, networks, and volumes absent; databases unreachable; allocated ports closed.

## P0/P1

P0=`0`; P1=`1`.

## Historical artifacts modified

None. V2.4, V1, V2, V3, Retry 16, Retry 17, provenance discontinuity, and historical promotion closure were preserved. Phase 31.5 remains `EXECUTION_HELD`.
