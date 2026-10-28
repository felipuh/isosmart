# LAB05-C1-R2 — non-financial authentication schema

Verdict: `LAB05_C1_R2_NONFINANCIAL_SCHEMA_PASS` (local disposable schema only).

Baseline verified clean: ISO Smart `61bf5a27ac49f66cc8b57f083c752e8fe397d108`,
branch `checkpoint/rec-git-03-isosmart-20261020`, tracking its origin counterpart;
AdminApps `5190c9b0`, branch `security/rec-git-sec-01-workspace-20261021`, tracking
`origin/security/rec-git-sec-01-20261021`. AdminApps was inspected, not changed.
No MedSupplier process was started or modified.

## Real graph diagnosis

`MigrationLoader(None)` loads the production graph and resolves its project
state under independent synthetic settings. The forward plan for
`authentication.0011_application_auth_runtime_privileges` contains 81 nodes.
It depends on `core.0019`, whose ancestry includes `core.0012` and financial
`core.0011_billing_models`, and on `foundation.0037`, with its full ancestry.
The machine evidence records every edge, not an AST approximation.

Authentication targets 0001–0010 have no billing ancestor. Core 0001–0010
precede billing. These are non-financial graph candidates, not evidence that a
partial production migration run supplies the current runtime schema. In
particular, authentication.0002 and core.0004 transfer UserProfile state only;
core.0003's physical legacy profile declares a one-to-one user relationship and
`last_login_at`, whereas the live model uses multi-organization FK membership.
Organization.external_id arrives in core.0005. We did not run these partial
chains or claim equivalence to the current models.

The required live authentication FK closure has no foundation model. Foundation
is a migration/grants dependency, not a query or FK dependency of sync_identity,
the selected profile queries, reset tokens, blacklist, or AuditLog. No foundation
schema/table is projected and no foundation behavior is claimed.

## Implementation and acceptance

The opt-in `backend/lab05_c1_r2/` runner creates a private Unix-socket PostgreSQL
18.6 cluster, SCRAM credentials generated in a mode-0700 temporary directory,
and a fresh database. No operational settings/env files are imported. TCP and
Python external connections are disabled. Credentials and database files are
removed with the cluster; only sanitized structural evidence is retained.

Django 4.2.22 schema_editor creates 12 tables from real models: auth_user,
organizations, user_profiles, refresh_token_blacklist, password_reset_tokens,
audit_logs, django_content_type, auth_permission, auth_group and their three
M2M tables. Every local model column matches PostgreSQL; inventory includes all
12 sequences, indexes, PK/unique/check/FK definitions and RLS policies.

`manage.py check --settings=lab05_c1_r2.settings` loads actual authentication
URLs/views and reports no issues. Actual `central_auth.sync_identity` creates
and updates synthetic identities twice, with idempotent subject/profile binding
and unusable local passwords. Real ORM tests cover joins, reverse profiles,
lockout counters, blacklist hashing, reset replacement/use, audit insertion and
persistence after reconnect. No authentication model or ORM call is mocked.
Fixtures passed to sync_identity are schema inputs, not centrally authenticated
proofs; CENTRAL verification and HTTP behavior are not claimed.

Two separately authenticated runtime roles have no admin attributes, inherited
roles, schema CREATE or database CREATE/TEMP. Grants permit only selected
SELECT/INSERT/UPDATE operations and sequence USAGE; auth_user UPDATE is limited
to authentication columns. Catalog/M2M writes, DELETE/TRUNCATE, DDL, role
creation/escalation, superuser updates and sequence setval are rejected. FK,
NOT NULL, PK and composite membership uniqueness are tested, not disabled.
Forced RLS isolates organization/profile/audit data using session_user; reads,
updates, cross-tenant inserts and tenant-GUC spoofing are checked after both
synthetic tenants exist. Global identity visibility is intentional. Reset and
blacklist state is user-scoped, including across memberships of the same user.

There are zero billing tables, zero executed migrations, no django_migrations
relation, and no non-public application schemas. No fake history is created.
Normal settings, migration source and auth/model contracts retain identical
SHA-256 hashes in LAB05_C1_R2_SOURCE_INTEGRITY.json. The full project and business
workflows are not supported by this narrow schema; runtime deletion, permission
catalog administration and foundation operations remain outside scope.

## Publication and reproducibility

The original ancestry has 238 commits and includes backend/.env and frontend/.env;
the tip also tracks a virtual environment. It is not reused for publication.
A parentless snapshot preserves source and normative documents, excludes 13,716
runtime/credential/dependency paths plus vite.pid, and blanks environment template
values. Original refs/history remain untouched. No production migration/settings
or central contract changes accompany the laboratory.

Gitleaks 8.30.1 audits every staged object and every object reachable from the
publication ref. The exact file-digest/line/rule manifest reviews 41 nonsecret
synthetic identifiers or evidence hashes; no blanket rule suppression is used.
New laboratory secrets and databases are never staged. The scanner also rejects
prohibited paths, symlinks/submodules and populated environment templates.

Acceptance passed with an independently installed minimal pinned Python
environment. Repeat the README command from the clean publication checkout to
verify the committed source; output belongs outside Git. SQL/model evidence is
in `docs/security/LAB05-C1-R2/evidence.json`. No historical suites were run.

Remaining work: genuine consumer HTTP integration, central proof/session tests
against this schema, and a separately reviewed runtime tenant-routing contract.
This result is not `LAB05_C1_HTTP_E2E_PASS`.

`PRODUCTION_READY = FALSE` · `PHASE31_5 = EXECUTION_HELD` ·
`S3_DECISION_02A_NOT_CLOSED` · `NO_DEPLOYMENT` · `NO_SHARED_DB_MUTATION`.
