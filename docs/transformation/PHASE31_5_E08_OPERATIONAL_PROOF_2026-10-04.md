# Phase31.5 E-08 Operational Proof — 2026-10-04

## A. Executive Verdict

E-08 remains **FAIL**. Repository-local corrections and the PostgreSQL/backup proofs passed, but deployment startup, PostgreSQL-backed authentication runtime, and complete worker-process lifecycle evidence were not executed. Phase31.5 remains **EXECUTION_HELD**.

## B. Governance Integrity

Evidence 18–21 was preserved; this cycle created evidence 22. No lifecycle, AdminApps, production, staging, customer-data, external API, webhook, or event-delivery operation occurred.

## C. Starting State

SQLite operational escape was already closed. E-07 remained external rotation evidence only. E-08 began failed for executable operational proof.

## D. Pre-flight Validation

`manage.py check --settings=backend.settings_test`, frontend build, frontend lint, shell syntax, and `git diff --check` passed. A host `compileall backend` attempt traversed virtual environments with a Python-version mismatch; this was not source failure. Repository source compilation had already passed before that broad traversal.

## E. Deployment Contract Audit

Corrected the database health check to use PostgreSQL image variables. Added `.dockerignore`, excluding environment files, repository metadata, dependency trees, logs, media, dumps, and build detritus. Base images retain exact version tags; no digest was invented.

## F. Environment Variable Contract

`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` are canonical for the image. Django now accepts them when `DB_NAME`, `DB_USER`, and `DB_PASSWORD` aliases are absent. The example no longer duplicates credentials.

## G. Redis Dependency Adjudication

No declared production component consumes Redis; the ADR’s PostgreSQL transactional outbox remains the delivery mechanism. Redis was removed from the Compose topology.

## H. Disposable PostgreSQL Environment

The rootless Podman gate used an official local PostgreSQL 18.6 image, random local-only credentials/names, loopback networking, and verified teardown.

## I. Migration Result

Migrations and the PostgreSQL security matrix passed. Full regression: **32/32 PASS**. Initial failures were corrected: an RLS-protected test queried without tenant context, and its migration leaf assertion was stale.

## J. JWT / HttpOnly Runtime Proof

Static implementation is cookie-only and frontend build/lint passed. Required PostgreSQL-backed login/cookie/missing-invalid-expired credential runtime proof was not run; prerequisite remains open.

## K. CSRF Runtime Proof

Cookie authentication enforces CSRF on unsafe methods in source. Required runtime missing/invalid/valid-CSRF proof remains open.

## L. Refresh / Logout Proof

Rotation/blacklist/logout source paths were inspected, but no PostgreSQL-backed lifecycle test was executed. Open.

## M. Backup Creation Proof

`scripts/backup_postgres.sh` passed against a local synthetic source database. It produced a custom archive and SHA-256 manifest. Production mode without encryption command was rejected.

## N. Backup Integrity Proof

`pg_restore --list` and `sha256sum --check` passed. A deliberately invalid manifest was rejected. No keys or credentials were retained.

## O. Restore Proof

Restore to a fresh disposable database passed and recovered the synthetic marker. All local container, volume, and temporary backup artifacts were removed.

## P. Worker Functional Proof

The PostgreSQL regression exercises the Foundation consumer discovery, claim, local processing, publish, and duplicate receipt behavior. The worker now only accepts its deployment-configured tenant when explicitly enabled.

## Q. Worker Retry Proof

The existing PostgreSQL test deterministically fails first delivery, verifies `failed` and one attempt, then retries successfully after prerequisite setup. This source-level functional evidence passed in the 32-test suite.

## R. Worker Concurrency Proof

Independent simultaneous command-process proof was not executed. Open.

## S. Worker Shutdown Proof

Independent SIGTERM/SIGINT proof was not executed. Open.

## T. Deployment Build Proof

Not executed: no Compose provider is installed and `python:3.12.7-slim-bookworm` was absent locally. No registry pull was performed.

## U. Deployment Startup / Health Proof

Not executed because the image was not built and Compose was unavailable. Open.

## V. PostgreSQL 32-Test Regression

**PASS — 32/32.** The gate also passed its rollback acceptance checks and confirmed cleanup.

## W. Backend Regression

Django system check passed. The PostgreSQL integration gate is authoritative for PostgreSQL-only behavior.

## X. Frontend Regression

`npm run build` and `npm run lint` passed. Persistent storage references remaining in the frontend are non-auth UI preferences/onboarding flags; no bearer JWT storage or bearer-header construction was found.

## Y. Security Regression

No secret was printed or retained. Cookie/CSRF source protections, RLS checks, loopback-only proof networking, build-context exclusion, and backup manifest validation were preserved.

## Z. Failure / Root-Cause / Correction Log

| Failure | Root cause | Correction | Retest |
|---|---|---|---|
| PostgreSQL regression error | RLS test read lacked trusted tenant context | Wrapped reads in context | 32/32 PASS |
| Migration regression failure | New migrations 0036/0037 made leaf assertion stale | Updated reversal/reapply assertions | 32/32 PASS |
| WP2 acceptance failure | Fixture lacked required precondition outcome | Derived synthetic evaluator outcomes from plan | PASS |
| WP2 acceptance failure | Existing rollback lineage correctly rejects changed idempotency key | Asserted immutable idempotency conflict | PASS |
| Backup proof launch failure | Scripts are checked in non-executable | Test invokes them through Bash | PASS |

## AA. Files Changed

Deployment Compose/example/settings, worker guard, RLS/migration/acceptance tests, Docker ignore rules, backup proof script, and this report/evidence.

## AB. External Effect Audit

All prohibited effect counts are zero.

## AC. Updated Prerequisite Matrix

| Prerequisite | State |
|---|---|
| SQLite operational escape | CLOSED (preserved) |
| Backup/restore | CLOSED |
| Deployment reproducibility | OPEN |
| JWT/localStorage | OPEN |
| Worker/outbox operability | OPEN |

## AD. E-07 Result

**FAIL — AUTHENTIC ROTATION EVIDENCE REQUIRED.** No credential rotation was attempted.

## AE. E-08 Result

**FAIL.** Exact blockers: missing local Compose provider/base image prevented build/startup proof; authentication runtime suite and independent worker concurrency/shutdown command proofs remain unexecuted.
