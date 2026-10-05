# Phase31.5 E-08 Authentication and Worker Final Closure — 2026-10-05

## Disposition

**E-08: CLOSED for the repository-local technical acceptance evidence exercised in this cycle.**
**E-07: FAIL — AUTHENTIC ROTATION EVIDENCE REQUIRED.**
**Phase31.5 remains `EXECUTION_HELD`.**

This record does not authorize Phase31.5 execution, staging, production access,
AdminApps authority use, or customer-data processing. The authentication and
worker proofs used only a loopback-bound, disposable PostgreSQL 18.6 instance,
synthetic identities, and mocked external application API methods.

## Deployment Health Contract

`/health` remains authenticated readiness and is not weakened to satisfy an
unauthenticated container probe. A minimal public `/livez` endpoint now supplies
the liveness contract, is the exact HTTPS-redirect exception, and is the target
of the production Compose healthcheck.

The rebuilt image `localhost/isosmart-e08:phase315-final` has image ID
`31e5e1da3636063fad3f1a0f7e677ad386e96ae45e9c23cbfe6467acff18e95d` and runs
as the non-root `isosmart` user. A loopback-only HTTP probe with the configured
reverse-proxy host and forwarded-HTTPS headers returned:

| Request | Result |
|---|---:|
| `GET /livez` | 204 |
| unauthenticated `GET /health` | 401 |
| unauthenticated `GET /api/auth/me/` | 401 |
| `GET /api/auth/csrf/` | 200 |
| refresh-cookie POST without CSRF | 403 |
| refresh-cookie POST with mismatched CSRF | 403 |
| refresh-cookie POST with matching CSRF and a synthetic invalid JWT | 401 |

The last result confirms the configured canonical HTTPS origin passed CSRF
validation and the request reached refresh-token validation. No valid token
value was emitted or recorded.

The production Compose graph and healthcheck target were source-reviewed, but
no Compose provider was available for a Compose invocation. The image itself
was built and exercised directly under rootless Podman. The probe container
and its temporary files were removed; the built image was intentionally kept
locally.

## PostgreSQL Authentication Lifecycle

The clean PostgreSQL 18.6 proof completed with run ID
`20261005T013341Z_f4733c`, **28 assertions passed**, and container, volume,
database, roles, and temporary harness directory teardown verified.

The full application migration graph was applied to the disposable database.
Authentication requests then used the source-provisioned application role,
which was verified as neither superuser nor `BYPASSRLS`. Synthetic fixtures
proved the application role can create and resolve its user, organization,
and profile; authenticate the configured owner tenant; and persist refresh
revocation state.

The proof covered invalid and valid login, denial of a different tenant,
production cookie attributes, token omission from the response body,
authenticated `/me`, unauthenticated/malformed/expired access-cookie
rejection, and foreign-profile invisibility. It also covered missing/invalid
CSRF rejection, successful refresh rotation, old-token replay rejection,
logout cookie clearing, and refresh revocation without storing raw refresh
tokens. External AdminApps credential, product-access, user, and organization
client methods were stubbed; no external API request was made.

This run exposed a real least-privilege deployment defect: the application
role had no access to the legacy `auth_user` table. Migration
`authentication.0011_application_auth_runtime_privileges` now grants DML only
on the authentication tables needed by runtime flows and usage/select only on
their corresponding ID sequences. It consumes the existing
`foundation.app_role` setting and does not create roles or broaden schema-wide
privileges.

The tenant probe also found that `OrganizationMiddleware` loaded a profile by
profile ID without binding it to the signed token's user and organization
claims. The lookup now binds those claims before exposing `request.user_profile`;
the PostgreSQL proof verified a mismatched foreign profile claim resolves to
no profile.

## Worker and Foundation PostgreSQL Regression

The fresh Foundation run completed with run ID `20261005T013421Z_2ed261`:

- selected PostgreSQL suite: **32/32 passed**;
- rollback acceptance: **18 passed**;
- worker process coverage included empty queue, configured-tenant mismatch,
  process-level failure and retry, overlapping two-process claims using
  `SKIP LOCKED`, restricted worker role flags, and both SIGTERM and SIGINT
  shutdown;
- disposable container, volume, and temporary directory teardown: **PASS**.

The existing suite count remains 32; worker-process assertions are included in
the existing integration case rather than being reported as extra test cases.

## Backup and Other Regressions

`scripts/test_backup_restore_postgres.sh` returned `BACKUP_RESTORE_PROOF=PASS`.
It verified the production-mode encryption guard, a synthetic PostgreSQL dump,
manifest checksum, restore into a separate disposable database, restored
marker equality, and rejection of a modified manifest.

Additional results:

- Django system check using test settings: passed.
- Python compilation of changed Python sources: passed.
- Pylance syntax checks of the changed middleware, migration, and harnesses:
  no syntax errors.
- Frontend production build: passed.
- Frontend lint: passed.
- Frontend source scan: no persistent authentication-token storage or
  persistent Bearer authorization header patterns. The `localStorage` use
  named `refreshStorageKey` is only the Context dashboard's auto-refresh
  interval preference; it does not store an authentication token.
- Production application image rebuild: passed.

## E-08 Matrix and Governance State

| Prerequisite | State |
|---|---|
| Deployment health contract | CLOSED — public liveness separated from authenticated readiness |
| PostgreSQL application authentication | CLOSED — restricted role, cookie, CSRF, refresh, logout, and tenant proofs passed |
| Worker/outbox runtime | CLOSED — process, retry, concurrency, tenant, role, and shutdown proofs passed |
| Backup/restore | CLOSED — disposable PostgreSQL regression passed |
| Frontend auth-token persistence | CLOSED — no persistent auth-token/Bearer pattern found |

**E-08 is closed for this local technical evidence cycle. E-07 remains
`FAIL — AUTHENTIC ROTATION EVIDENCE REQUIRED`; therefore Phase31.5 remains
`EXECUTION_HELD`.** No held phase state was changed.

## Evidence and Publication

Machine-readable evidence is recorded in
`docs/governance/evidence/phase31_5/26_auth_worker_closure_2026-10-05.json`.
The evidence package is based on starting commit `15f250fadc567b158d7dcfa3f9c9cabb40e7ce1a`
on `hardening/p0-p1-enterprise-readiness`. Publication uses a normal, non-force
commit and push, with unrelated pre-existing worktree changes excluded.
