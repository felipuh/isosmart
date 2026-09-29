# Phase 31.4 V2.5 — Clean Retry 17 final report

## Verdict

`EVIDENCE_RUN_FAIL`

## Run ID

`Phase 31.4 V2.5 Clean Retry 17`

## Environment

PASS — dedicated PostgreSQL 18.6 AdminApps and ISO Smart containers, networks, volumes, databases, and ports.

## Migrations

PASS — ISO Smart foundation `24/24`; pending `0`; fake `0`; manual schema patches `0`.

## Stage EXT

PASS. Six identities and provenance:

- `external_adminapps_tenant_id`: `ac312d29-2f3e-4a12-9094-5838b9484780` — ADMINAPPS_EXTERNAL_TENANT
- `external_adminapps_actor_user_id`: `597130f2-9e2a-45af-9a17-a83298de0206` — ADMINAPPS_EXTERNAL_ACTOR
- `iso_smart_tenant_projection_id`: `c6b0937f-05c1-492a-9546-65c469fa4ea4` — TENANT_PROJECTION_READBACK
- `iso_smart_user_projection_id`: `205aa6c9-6b46-45ef-9dc4-c7ea308dcb55` — USER_PROJECTION_READBACK
- `qms_organization_id`: `c6cf6b88-9a2d-4920-ae90-d971ee4585fb` — QMS_NATIVE_ORGANIZATION
- `process_id`: `7018612e-58dc-4a91-b163-9005dc413bba` — QMS_NATIVE_PROCESS

## Phases

Required `33`; executed `1`; PASS `0`; FAIL `1`; stopped before `32` phases.

`PRECREATION_INTEGRITY` returned FAIL because it has no registered operation/assertions/evidence contract.

## Native captures

Expected `565`; resolved `0`; unresolved `565`. No placeholders, fixture substitutions, or historical fallback were used.

## External/upstream captures

AdminApps tenant `1/1`; actor `1/1`; entitlement `1/1`. Local projections and QMS IDs were not counted as upstream-native.

## Live graph

Members `0/118`; fields `0/1664`; unresolved `1664`; hash `null`. Not materialized after the first blocker.

## Exact comparison

NOT RUN; mismatch counts remain `null`, not fabricated zeros.

## Event/outbox/audit

Stage EXT AdminApps outbox delivery and ISO Smart ingress receipt PASS. Material native-chain evidence NOT EXECUTED.

## Authority

AdminApps actor and entitlement were read back from the isolated authority. The `superadmin` membership is classified `SYNTHETIC_TEST_AUTHORITY`; no full real approval-authority proof is claimed.

## Security

FAIL — `0/8` probes executed after fail-closed stop.

## Transactions

FAIL — required material-chain atomicity/rollback/idempotency proofs were not executed.

## SHA manifest

PASS — every retained Retry 17 artifact except the manifest itself is hashed and read back.

## Teardown

`PASS`

## Post-teardown verification

`PASS` — containers, networks, volumes, DB reachability, and allocated ports absent.

## P0/P1

Pre-run: P0 `0`, P1 `0`. Run findings: P0 `1`, P1 `0`.

## Historical artifacts modified

None. Historical provenance remains `NOT_PROVEN`.

## Current baseline modified

None; only run-scoped evidence artifacts were added.

## Phase 31.5

`EXECUTION_HELD`

## Promotion status

`NOT_DECIDED_IN_THIS_TASK`

## Exact next step

Convene one governance remediation review to approve a concrete `PRECREATION_INTEGRITY` executor, operation, assertions, and retained-evidence contract before authorizing another disposable run.
