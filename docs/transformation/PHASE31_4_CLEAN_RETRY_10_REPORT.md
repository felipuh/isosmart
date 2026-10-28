# Phase 31.4 V2.5 Clean Retry 10

## Verdict

**NOT_PROMOTED.** PostgreSQL role bootstrap and complete clean migrations passed. The fresh AdminApps to ISO Smart chain passed. The V2.5 runtime stopped at `INITIAL_OPPORTUNITY` because the contract Process reference does not resolve to the Process produced in this retry.

## Runtime role bootstrap and PostgreSQL

The approved foundation gate created 21 `LOGIN NOINHERIT` roles and three `NOLOGIN NOINHERIT` function owner roles on a fresh PostgreSQL 18.6 cluster. All foundation roles are `NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS`. The migrator owns the ISO Smart database and protected tables; app, worker, projector and other runtime roles own none of the 50 protected tables. The migration chain defines 250 RLS policies and grants. The exact role attributes, schema access, table privileges, owner relationships and policies are in `PHASE31_4_POSTGRES_RUNTIME_ROLE_BOOTSTRAP_V1.json`. The bootstrap repeat check passed; the frozen `foundation.0001` guard failed before roles existed and passed after bootstrap.

Both disposable databases used the frozen PostgreSQL 18.6 image. The cluster resource manifest records image digest, IDs, names, network, volume, ports, timestamps, and database reset. The isolated host authentication was loopback-only `trust`, inherited from Retry 9's resource policy; the run does not prove password enforcement at the PostgreSQL network boundary.

## Migrations

AdminApps applied 61 migrations from zero and has zero pending. ISO Smart applied 92 migrations from zero in PostgreSQL, including `foundation.0001` and all 24 foundation migrations, and has zero pending. No fake migration or manual schema patch was used. An initial ISO Smart command mistakenly selected the local SQLite database; that result was rejected. This touched `backend/test_default.sqlite3`, which was already locally modified before Retry 10; its prior contents could not be reconstructed safely, so the file was left in place. The first real PostgreSQL attempt then stopped at `foundation.0016` because Django connection `OPTIONS` did not include the supplied role identifiers. The disposable ISO Smart database was recreated empty, `DB_SESSION_OPTIONS` was wired to Django, and the complete chain passed from zero without changing the migration. The failed attempt and its remediation remain in evidence.

## Fresh Stage EXT chain

AdminApps' native API created the tenant, then its native activation API produced source version 2. Authenticated outbox delivery reached ISO Smart ingress; the receipt and TenantProjection retained the canonical external UUID. Live AdminApps entitlement and actor membership authorized the native QMS Organization command. Native Process and Opportunity commands ran, followed by a controlled Opportunity revision. The successor kept the lineage ID, incremented revision 1 to 2, and pointed to the predecessor. Four domain events, four outbox rows, and four audit entries were observed. The disposable AdminApps product was configured in its supported non-billing mode, with an active entitlement.

## Native V2.5 runtime and blocker

The production `build_v25_runtime` factory ran with the app role. It returned PASS for 13 registry phases before `INITIAL_OPPORTUNITY`; these first phases are composition assertions and do not establish the required live captures. At the next phase, `RiskOpportunityObjectiveCommandService.create_opportunity` raised `Process.DoesNotExist`. The frozen contract refers to Process `506d920c-fe62-53c0-aac8-9c1ca8ca78ed`; the fresh native Process is `35ae9e96-478d-40d9-8cdd-be52a0c7048d`. This is `P1-RETRY10-V25-INITIAL-OPPORTUNITY-PROCESS-BINDING-MISMATCH`. No V2.5 contract or migration was altered to force a pass.

The native phase result is 13/33 returned PASS, with failure before the 14th result was recorded. Capture resolution is 0/509. Authority/A3, ActionPlan, full controlled revision within V2.5, references, invariants, transaction rollback, resolved graph 118/118, field count 1664/1664, and exact comparison were not completed by the V2.5 runtime. The Stage EXT revision and event/outbox/audit facts above are separate live checks. Runtime graph mismatch count is not computed.

## Preservation and promotion

V2.4 SHA-256 is `a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387` and passed. Retry 8 closure and Retry 9 historical evidence were not modified. The Retry 9 role-bootstrap blocker is closed by this live proof. Current P0=0 and P1=1. Promotion remains **NOT_PROMOTED**. Both Retry 10 containers, databases, volumes and dedicated networks were removed; the scoped Podman inventory verified their absence (`teardown=PASS`). The SHA-256 evidence manifest is recorded separately.
