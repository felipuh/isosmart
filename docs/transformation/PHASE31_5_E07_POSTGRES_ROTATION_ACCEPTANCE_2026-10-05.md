# Phase31.5 E-07 PostgreSQL Rotation Acceptance

Date: 2026-10-05

Scope: repository-local PostgreSQL acceptance using disposable PostgreSQL and synthetic credentials only. This evidence does not authorize or perform authentic credential rotation.

**Final technical verdict: `POSTGRES_ROTATION_ACCEPTANCE_READY`**

## A. Governance Integrity

- `E-07 = FAIL_AUTHENTIC_ROTATION_EVIDENCE_REQUIRED`.
- `E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`.
- `Phase31.5 = EXECUTION_HELD`.
- Evidence 27 was not modified.
- No authentic credential was accessed, authenticated, created, revoked, or rotated. Production and staging were not accessed. No customer workflow was run.
- The initial administrator password remains a separate `INITIAL_ADMINISTRATOR_PASSWORD` item. API-key acceptance alone cannot close E-07 until that exposure is separately adjudicated.
- The approved ISO Smart secret-injection authority is not established; see sections M and N.

## B. Repository Baseline

| Repository | Branch | Baseline HEAD | Result |
|---|---|---|---|
| AdminApps (`/home/felipe/proyectos/adminapps`) | `hardening/p0-p1-enterprise-readiness` | `8b9c5684997baaa590b34af241a173e1a9c41143` | Required implementation commit present; source unchanged. |
| ISO Smart (`/home/felipe/proyectos/isosmart`) | `hardening/p0-p1-enterprise-readiness` | `f626c6e57f481d915d4ba8f64ab8ef054e7eba91` | Required governance-report baseline present. |

Both worktrees contained unrelated pre-existing changes. They were preserved; only this report is task-owned.

## C. Disposable PostgreSQL Environment

- `POSTGRES_VERSION = 18.6 (Debian 18.6-1.pgdg13+2)`.
- Run ID: `e07-20261005T035813Z-85547`.
- Provider: rootless Podman; PostgreSQL image `docker.io/library/postgres:18.6`.
- Container: `adminapps-e07-20261005T035813Z-85547` (removed).
- Local binding during proof: `127.0.0.1:41549` only.
- Primary database: `adminapps_e0720261005T035813Z85547`.
- Separate legacy-migration proof database: `adminapps_legacyproof_20261005_0358`.
- Database role was synthetic (`adminapps_synthetic`) with a randomly generated temporary password. The password was not recorded in this report or any evidence.
- The image-created anonymous volume was unique to this container and removed with it. There was no named persistent volume.
- Django ran with a temporary settings shim that disabled `dotenv.load_dotenv` before importing project settings and overrode the database configuration with the synthetic connection details. The repository `.env` was not read.

## D. Migration Acceptance

`POSTGRES_MIGRATIONS = PASS`

- The normal Django migration graph was applied to the primary disposable PostgreSQL database.
- `integration.0006_integration_api_key_lifecycle` applied successfully.
- `showmigrations integration` reported migrations `0001` through `0006` applied.
- `manage.py migrate --check` found no unapplied migrations. The separate legacy-proof database was also restored to its complete leaf migration graph.
- No schema was changed outside Django migrations.

## E. Legacy Classification

`LEGACY_CLASSIFICATION = PASS`

The PostgreSQL-specific `IntegrationAPIKeyLegacyMigrationTests` passed. An additional isolated migration proof used in-memory generated synthetic values: it migrated to `0005_demorequest`, inserted active and inactive legacy rows through that historical model state, and applied `0006_integration_api_key_lifecycle`.

After migration:

- The active row remained byte-for-byte identifiable by its original synthetic legacy value and was classified `legacy_plaintext` / `active`.
- The inactive row retained its original synthetic value and was classified `legacy_plaintext` / `revoked`.
- Neither value was placed in `credential_hash`; neither row was rotated or linked to a replacement.
- No rotation audit event was created.
- Captured migration stdout/stderr contained neither synthetic value.

## F. Rotation Lifecycle

`POSTGRES_ROTATION_LIFECYCLE = PASS`

The focused PostgreSQL lifecycle tests passed, and the instrumented disposable-database proof verified:

- A replacement was generated through the lifecycle service and returned only to the calling in-memory application boundary.
- The database stored no raw replacement in `key`; its password verifier differed from the raw replacement, and a safe fingerprint was present.
- The source transitioned to `rotated`, became inactive, had revocation/rotation timestamps, and linked to the replacement.
- The old key was rejected and the replacement was accepted.
- One rotation audit event linked the source and replacement, actor, service name, fingerprints, and safe lifecycle metadata. It contained no raw key or verifier.
- The service/application ownership label (`name`) was preserved on the successor.

`IntegrationAPIKey` has no tenant foreign key: ownership in this implementation is service/application-name scoped, not tenant-scoped. No tenant relationship was invented or claimed.

## G. Atomicity

`POSTGRES_ROTATION_ATOMICITY = PASS`

The focused test `test_failed_audit_write_rolls_back_replacement_and_revocation` forced an audit-write exception after rotation had begun. On PostgreSQL, the transaction rolled back: the source remained active and unchanged, no replacement persisted, and no audit event persisted.

## H. Concurrency

`POSTGRES_ROTATION_CONCURRENCY = PASS`

Both the repository PostgreSQL concurrency test and a controlled two-thread proof passed. Each thread used its own database connection and targeted the same synthetic source record. The first transaction was held open at its in-transaction audit write while the second attempted rotation. PostgreSQL `pg_stat_activity` reported a `wait_event_type = 'Lock'` before the first transaction was released, proving actual transaction overlap and lock contention.

The committed result was deterministic: one rotation succeeded, the competing attempt was rejected, the original was rotated once, exactly one active successor existed, and exactly one rotation audit event corresponded to the committed transition. No competing raw key was emitted or recorded in evidence.

## I. Revocation Permanence

`POSTGRES_REVOCATION_PERMANENCE = PASS`

The PostgreSQL lifecycle test verified that saving a revoked credential with `is_active=True` does not reactivate it. The credential remained revoked/inactive and was rejected by the health probe. The valid replacement remained accepted.

## J. Safe Health Probe Contract

`SAFE_ROTATION_PROBE_CONTRACT = PASS`

Using Django's local test client against the disposable PostgreSQL-backed application and synthetic credentials only:

| Phase | Method | Path | Expected / observed result |
|---|---|---|---|
| Before rotation | `GET` | `/api/integration/health/` | Source synthetic key: `200` |
| After rotation | `GET` | `/api/integration/health/` | Old synthetic key: `401` |
| After rotation | `GET` | `/api/integration/health/` | Replacement synthetic key: `200` |

This route exercises API-key authentication and returns generic service health; no customer workflow was called.

## K. Secret Leakage Review

`RAW_CREDENTIAL_LEAK_REGRESSION = PASS`

- No authentic credential or `.env` value was accessed.
- Synthetic raw keys were not printed in migration or acceptance output, included in the report, or persisted as evidence.
- The captured migration output was scanned for secure-key-shaped strings and the synthetic legacy fixture values; no matches were found.
- Changed-file review and staged-content scanning are required before publication. No password is part of the report.
- Raw credential evidence leaks: `0`.
- `.env` inspected: `NO`.

## L. Resource Teardown

`DISPOSABLE_RESOURCE_TEARDOWN = PASS`

The PostgreSQL container and its unique anonymous volume were removed. Both disposable databases were inside that container and were removed with its storage. The temporary database-password file, temporary settings shim, and captured migration log were removed. Follow-up checks found no matching container or volume.

## M. Authentic Rotation Operator Runbook

**Status: not executed.** This section is a future, non-executed procedure. Authentic rotation remains unauthorized.

1. An authorized operator first confirms the intended AdminApps validation path (persisted row versus any configured hash fallback) and identifies the exact service/application record. In a read-only authorized AdminApps context, list only safe fields for active legacy rows, for example:

   ```python
   IntegrationAPIKey.objects.filter(
       credential_format='legacy_plaintext',
       status='active',
   ).values(
       'id', 'name', 'credential_format', 'status', 'is_active',
       'created_at', 'last_used_at', 'last_used_service',
   )
   ```

   Match the intended service and other approved non-secret identifiers. Do not select, display, copy, or log `key` or `credential_hash`.

2. Before any rotation, require the authorized production change approval and verify `integration.0006_integration_api_key_lifecycle` is applied in the actual AdminApps environment. Do not infer that this disposable-database proof establishes production migration state.

3. Capture safe pre-rotation metadata only: record ID, service name, format/status/active state, available fingerprint, creation and last-use timestamps/service, and current replacement link. Do not capture the raw value or verifier.

4. The source-defined management command syntax is:

   ```text
   python manage.py rotate_integration_key --id <IntegrationAPIKey.id> --actor-id <active-staff-user.id>
   ```

   The command prints the replacement once to stdout. Its arguments contain only record/operator IDs, but the output itself is secret. Do not execute this command until step 5 is resolved and the operator has a preapproved non-recording delivery path.

5. **`SECRET_INJECTION_AUTHORITY_UNRESOLVED`**. ISO Smart source reads `ADMIN_APPS_API_KEY` from its process environment and constructs an `AdminAppsClient` singleton at import time. No approved secret-injection mechanism, receiving command/API, or output-redaction contract was established by this repository-local work. Do not invent one, paste the value into a shell command, pipe it through an unapproved tool, or place it in a transcript, shell history, log, ticket, or artifact. Until the responsible authority specifies and approves direct one-time delivery into the actual runtime secret-injection mechanism, stop before running the rotation command.

6. After an approved injection mechanism is documented and used, restart/redeploy all relevant ISO Smart worker processes so the singleton is reconstructed with the injected `ADMIN_APPS_API_KEY`. No environment-specific restart command is asserted here because the deployment mechanism was not established.

7. Using the authorized AdminApps base URL and the approved secret receiver, perform only the safe probe:

   ```text
   GET <AdminApps base URL>/api/integration/health/
   X-API-Key: <old credential supplied without logging>
   ```

   Require `401` (or policy-approved `403`). Then issue the same `GET` to `/api/integration/health/` using the replacement from the approved receiver and require `200`. Do not call customer workflows. Resolve any configured fallback acceptance path before treating old-key rejection as established.

8. Capture only post-rotation safe metadata: old/new record IDs, service name, lifecycle states, fingerprints, revocation/rotation times, replacement link, and whether each health probe returned its expected status. Capture the `rotated` audit event ID/UUID, actor, timestamp, old/new IDs and fingerprints, and safe metadata. Never copy raw values or verifier strings into evidence.

9. If replacement installation fails, do not reactivate the rotated source, attempt to recover its raw value, or retry by copying the one-time output. Keep affected ISO Smart consumers stopped or otherwise safely held, preserve the audit trail, and escalate to the authorized secret-injection owner. Once the delivery path is approved, use the currently active record and a newly approved rotation/delivery operation as directed by the incident authority; then repeat the two health probes. Do not claim rollback by restoring the revoked credential.

## N. Remaining Blockers

- `SECRET_INJECTION_AUTHORITY_UNRESOLVED`: approved receiver, one-time transfer method, output/logging protections, and environment-specific restart authority still need an owner and documented approval. Authentic rotation is not operationally executable until resolved.
- `INITIAL_ADMINISTRATOR_PASSWORD` remains a separate E-07 item. Its exposure/rotation adjudication is outside this API-key acceptance and must be completed before E-07 can close.
- An authorized operator must still identify the authentic credential's actual acceptance path, verify the production migration precondition, and produce authentic old-key rejection/replacement acceptance evidence.
- No blocker invalidates the local PostgreSQL technical proofs in sections D through L.

## O. Final Verdict

All required repository-local PostgreSQL gates passed:

```text
POSTGRES_MIGRATIONS = PASS
LEGACY_CLASSIFICATION = PASS
POSTGRES_ROTATION_LIFECYCLE = PASS
POSTGRES_ROTATION_ATOMICITY = PASS
POSTGRES_ROTATION_CONCURRENCY = PASS
POSTGRES_REVOCATION_PERMANENCE = PASS
SAFE_ROTATION_PROBE_CONTRACT = PASS
RAW_CREDENTIAL_LEAK_REGRESSION = PASS
DISPOSABLE_RESOURCE_TEARDOWN = PASS
```

`POSTGRES_ROTATION_ACCEPTANCE_READY`

This verdict is limited to the local synthetic-credential acceptance. It does not close E-07, authorize authentic rotation, or release the Phase31.5 execution hold.
