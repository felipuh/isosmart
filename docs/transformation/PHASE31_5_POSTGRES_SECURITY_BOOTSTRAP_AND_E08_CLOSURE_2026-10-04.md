# Phase31.5 PostgreSQL Security Bootstrap and E-08 Continuation — 2026-10-04

## A. Executive Verdict

`PHASE31.5 E-08 PARTIALLY CLOSED — SPECIFIC TECHNICAL BLOCKERS REMAIN`.

The repository-local pre-migration PostgreSQL role contract is now single-source, idempotent, and clean-cluster exercised.  Phase31.5 remains `EXECUTION_HELD`.  E-07 remains `FAIL — AUTHENTIC ROTATION EVIDENCE REQUIRED`.

## B. Starting Blocker and Discovery

The historical partial manual bootstrap was incomplete.  A repository-wide scan of all active `foundation` migrations (0001–0037), their `RunSQL` blocks, RLS policies, grants, `SET ROLE` calls, runtime settings, harnesses, and ADR-0020 found exactly the 24 identities below.  No migration creates a cluster role; every listed identity is therefore `BOOTSTRAP_REQUIRED`.  No additional audit-reader/audit role is defined by active source.

| Role key | Source provenance | Purpose | LOGIN | Superuser / Createdb / Createrole / BypassRLS | Membership | Before migration |
|---|---|---|---|---|---|---|
| migrator | ADR-0020; migrations 0001–0037 | database owner and migration identity | yes | no / no / no / no | may SET three owner roles | yes |
| app, worker | migrations 0001–0037 | web runtime; outbox runtime | yes | no / no / no / no | none | yes |
| projector, audit_writer | migrations 0002–0003 | projection ingress; audit append | yes | no / no / no / no | none | yes |
| normative_curator, agent_catalog_curator | migrations 0008, 0011 | curation identities | yes | no / no / no / no | none | yes |
| human_approver, execution_authorizer, executor | migrations 0012–0014, 0036 | governed decision/execution identities | yes | no / no / no / no | none | yes |
| learning_governance, learning_reviewer, learning_approver, learning_authorizer, learning_application_executor | migrations 0018–0021, 0025 | governed learning identities | yes | no / no / no / no | none | yes |
| rule_publisher, rule_activator, rule_adopter, rule_resolver, release_repair, release_controller | migration 0022 | rule/release identities | yes | no / no / no / no | none | yes |
| qms_action_owner, knowledge_rule_application_owner, rule_governance_owner | migrations 0015, 0021–0023 | restricted function owners | no | no / no / no / no | granted only to migrator with SET | yes |

The cluster/bootstrap identity is PostgreSQL `postgres`, used only for role/database creation in the disposable proof.  It is not exposed to application aliases.  `migrator` owns the generated database and schema objects.  LOGIN runtime identities are separate and have `NOINHERIT`; the three ownership principals are `NOLOGIN`.

## C. Bootstrap Implementation and Idempotency

`backend/foundation/postgres_foundation_gate.py` now declares `ROLE_SPECS` as the authoritative contract and derives creation, verification, teardown, and evidence role lists from it.  `bootstrap_idempotent` is invoked for both first and second execution before any Django migration.  It creates a wholly fresh database/roles once, then verifies exact attributes, database ownership, and exactly the three permitted memberships.  Any partial setup, privilege drift, ownership drift, or membership drift fails explicitly; it is never silently accepted.

The bootstrap script hash for this run is `52cc2406b7afe01152111d30ee213ab8dc7d53c7f1800d8f3898ad91dcb201f2`.

## D. Clean-Cluster and Security Result

A new local, loopback-only Podman PostgreSQL 18.6 cluster was used after deleting the interrupted broad-run resources.  The first bootstrap returned PASS; the immediate second bootstrap returned PASS/IDEMPOTENT; the focused harness applied the current migration leaf and removed its own container and volume.  The full-repository suite was intentionally stopped after it entered an unrelated CPU-bound legacy test; that broad suite is not claimed as E-08 evidence.

The focused harness retains the existing Foundation RLS acceptance behavior: runtime roles are non-superuser/non-BYPASSRLS, owner roles are NOLOGIN, tenant context is required, and cross-tenant visibility is denied.  This cycle does not relabel the prior 32/32 result; it preserves it pending a fresh recorded 32-test run.

## E. Failure / Correction Journal

| Attempt | Failure | Root cause | Correction | Retest |
|---|---|---|---|---|
| Historical | migration exposed another role after manual patch | incomplete reactive bootstrap | complete migration/source inventory | replaced |
| 1 | harness started before temporary dependency install finished | local proof environment timing | completed isolated dependency setup | clean rerun |
| 2 | broad legacy suite became CPU-bound after migrations | out-of-scope full suite, not migration/security gate | terminated proof processes and removed exact run resources | focused harness completed |

## F. Remaining E-08 Actions

Still required: a 32/32 PostgreSQL regression run recorded for this cycle; application image rebuild; governed startup/health topology; PostgreSQL-backed login/cookie/CSRF/refresh/logout proof; and independent worker command, retry, concurrency, SIGTERM/SIGINT, and tenant/RLS proofs.  No production/staging/AdminApps/customer/external-delivery operation occurred.
