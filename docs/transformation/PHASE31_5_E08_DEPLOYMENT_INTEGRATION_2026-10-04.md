# Phase31.5 E-08 deployment bootstrap integration — 2026-10-04

## A. Executive Verdict

`P1-31_5-ENTRY-DEPLOYMENT-REPRODUCIBILITY = CLOSED` for the governed clean-start sequence. E-08 remains `FAIL` because the PostgreSQL authentication and independent worker runtime suites have not yet been completed.

## B. Governance Integrity

Phase31.5 remains `EXECUTION_HELD`. No Phase31.5 lifecycle, WS-A, AdminApps authority proof, staging, production, customer data, or external event delivery was invoked.

## C. Starting Git State

Branch: `hardening/p0-p1-enterprise-readiness`; starting published checkpoint: `2a898bf3`. Pre-existing unrelated working-tree changes were preserved.

## D. Compose Defect Verification

The prior graph was `database (healthy) -> migrate -> web/outbox-worker`; it contained no Foundation bootstrap service. A clean migration therefore lacked the governed role contract.

## E. Bootstrap Deployment Integration

`foundation-bootstrap` now calls `postgres_foundation_gate.py --deployment-bootstrap`, a non-destructive interface over the authoritative `ROLE_SPECS`. `migrate` waits for it to complete successfully and uses `migrate_with_foundation_roles.py`, which derives all PostgreSQL session role settings from that same contract before Django starts.

## F. Credential Separation

Compose now maps five separate, untracked production environment files: database initialization, bootstrap, migrator, web, and worker. The bootstrap credential is absent from web and worker templates. No real credentials were added.

## G. Clean Cluster Proof

Using a new disposable PostgreSQL 16.4 container and network, with no application roles, Foundation database, or schema, the database became ready before bootstrap.

## H. Bootstrap First Run

PASS: 24 roles, consisting of 21 LOGIN and 3 NOLOGIN roles; database owner and membership contracts were verified.

## I. Bootstrap Idempotency

PASS: a second bootstrap invocation after the clean migration returned the same verified 24/21/3 contract without reconciliation or teardown.

## J. Migration Result

PASS: all Django applications migrated from zero through `foundation.0037_qms_audit_capa_foundation`. The first attempt correctly failed closed because migration session role settings were absent; the root cause was corrected by the source-owned migration launcher and the clean run was repeated successfully.

## K. Deployment Startup

PASS for database -> bootstrap -> migrate -> web. The rebuilt image started Gunicorn under `isosmart`, not root. Compose syntax/dependency assertions passed. Compose execution itself was unavailable because the local Podman installation has no Compose provider; native Podman reproduced the declared order.

## L. Health Proof

The web process ran and accepted loopback traffic. `/health` returned 301 without the configured HTTPS proxy header and 401 with it, which matches the repository's authenticated-readiness contract. A successful authenticated health response was not claimed because the disposable database has no approved synthetic runtime identity seed. The current Docker healthcheck also lacks this credential and is therefore not a successful authenticated readiness proof.

## M. Deployment Prerequisite Result

`CLOSED` for role bootstrap, idempotency, zero-state migration, and non-root web startup. The healthcheck authentication limitation is recorded for the next auth/runtime suite and does not alter the verified migration topology.

## N. Auth PostgreSQL Environment

Not run to completion in this cycle.

## O. Login

Not run.

## P. Cookie Security

Not run.

## Q. CSRF

Not run.

## R. Refresh / Revocation

Not run.

## S. Logout

Not run.

## T. Auth Tenant / RLS

Not run.

## U. Frontend Auth Regression

Not rerun in this source-state delta.

## V. Worker Command

Not run.

## W. Worker Retry

Not run.

## X. Worker Concurrency

Not run.

## Y. SIGTERM / SIGINT

Not run.

## Z. Worker Tenant / RLS

Not run.

## AA. Fresh 32-Test Regression

Not rerun in this source-state delta.

## AB. Backup Regression

Not rerun; preserved as previously closed.

## AC. Backend Regression

Python compilation of changed deployment modules and static Compose graph assertions passed. Image build passed.

## AD. Frontend Regression

Not rerun because this change is backend/deployment-only.

## AE. Failure / Root-Cause / Correction Journal

1. Clean migration failed at Foundation 0001 with missing runtime role settings.
2. The missing session settings were the cause; no role was manually created.
3. Added a migration-only launcher that derives all settings from `ROLE_SPECS`.
4. Rebuilt and reran a clean database: migrations completed through Foundation 0037.

## AF. Cleanup

The named disposable container and network are removed at the end of this cycle. The rebuilt local image may remain.

## AG. Files Changed

- `deploy/compose.production.yml`
- `backend/foundation/postgres_foundation_gate.py`
- `backend/foundation/migrate_with_foundation_roles.py`
- production environment templates

## AH. Final E-08 Matrix

| Prerequisite | State |
|---|---|
| SQLite operational escape | CLOSED (preserved) |
| Backup/restore | CLOSED (preserved) |
| Deployment reproducibility | CLOSED |
| JWT/localStorage | OPEN |
| Worker/outbox operability | OPEN |

`E-08 = FAIL` — remaining technical work is the PostgreSQL auth lifecycle suite and independent worker runtime suite. `E-07 = FAIL — AUTHENTIC ROTATION EVIDENCE REQUIRED`. `Phase31.5 = EXECUTION_HELD`.
