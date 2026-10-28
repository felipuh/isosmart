# Phase 31.5 — Production Readiness / Operational Hardening plan

- Status: **PROPOSED — NOT AUTHORIZED FOR EXECUTION OR PROMOTION**
- Discovery conclusion: **SUCCESSOR_NOT_DEFINED**
- Baseline: **Phase 31.4 V2.5 — PROMOTED / Clean Retry 16**
- Nature: operational proof in isolated, disposable environments
- Product-code changes authorized by this plan: **none**

## 1. Successor discovery and numbering decision

No repository artifact defines a successor phase with a complete phase ID,
objective, scope, entry gates, exit gates, outputs and evidence model.

The repository repeatedly names **Phase 32** together with
`RuntimeAdoption`, but only as a future blocked capability. ADR-0014 and the
runtime-adoption governance designs define that capability's architecture;
they do not define or authorize a Phase 32 execution plan. Phase 32 is therefore
treated as semantically reserved and remains unauthorized.

The general migration roadmap already assigns macro **Fase 6** to hardening and
retirement. This proposal operationalizes its production-readiness portions
after Phase 31.4 without renumbering or replacing that macro roadmap.

Accordingly, the non-conflicting successor proposed here is **Phase 31.5**. It
is an operational prerequisite gate. It does not invoke RuntimeAdoption and
does not imply Phase 32 authorization.

## 2. Objective

Prove whether ISO Smart can operate safely, recoverably, observably, securely
and predictably as a deployable system under realistic operational conditions,
without reopening the native-execution correctness proven by Phase 31.4.

## 3. Baseline freeze

`Phase 31.4 V2.5 = PROMOTED BASELINE`.

It is used only as a regression oracle. No Phase 31.4 binding correction, new
retry, contract reinterpretation, V2.4 mutation or historical-evidence rewrite
is in scope. A separately governed, demonstrated future regression is the only
valid trigger to consider reopening it.

## 4. Scope and workstreams

| ID | Workstream | Required proof |
|---|---|---|
| WS-A | Deployment reproducibility | Fresh supported environment from declared runtime, PostgreSQL, roles, migrations, protected configuration and locked dependencies; two clean builds/runs produce equivalent inventories and gates. |
| WS-B | Upgrade path | Upgrade from the latest supported predecessor fixture; schema, data, RLS, event/outbox and rollback/forward-fix boundary reconciled with zero unexplained loss. |
| WS-C | Backup/restore | Backup and restore into a new isolated instance; startup, tenant relationships, critical hashes/counts, event/outbox state, permissions and RLS reverified. |
| WS-D | Disaster recovery | Controlled PostgreSQL, app and worker restarts; interrupted transactions/delivery, stale process and partial service outage; measured recovery. RTO/RPO are recorded as observations until owners approve targets. |
| WS-E | Transaction recovery | Retry, idempotency, duplicate delivery, ambiguous commit, partial failure, rollback and governed reprocessing; explicit at-least-once/exactly-once assumptions. |
| WS-F | Security and RLS negative paths | Cross-tenant, unauthorized/stale actor, wrong role/entitlement, missing/invalid credentials, privilege escalation and `BYPASSRLS` absence. |
| WS-G | Secrets and configuration | Secret scan, externalized keys, environment separation, safe logging and rehearsed service/DB credential rotation in isolation. |
| WS-H | Observability | Structured logs, correlation/trace propagation, audit events, liveness/readiness, DB health, outbox backlog and failed-ingress visibility; dashboard/alert minimums and synthetic signal tests. |
| WS-I | Performance | Reproducible baseline for tenant ingress, Process, Opportunity, Agent chain, ActionPlan, Authorization and controlled revision; latency distribution, throughput, query counts/slow queries and bottlenecks recorded. No production SLO is invented. |
| WS-J | Concurrency | Concurrent Opportunity, AgentRun, ActionPlan, Authorization, controlled revision and idempotency-key tests; zero duplicate IDs, invalid revisions, lineage races or tenant contamination. |
| WS-K | Integration resilience | AdminApps ↔ ISO Smart duplicate, delayed, out-of-order, receiver-failure, sender-retry, consumer-restart and idempotent replay scenarios. |
| WS-L | Operational maintenance | Restart, redeploy simulation, post-restart migrations, DB maintenance, log rotation, cleanup and retry-backlog handling in isolation. |
| WS-M | Rollback/forward-fix | Separate runbooks and decision records for code rollback, schema rollback, forward migration and data repair; unsafe schema rollback is rejected rather than assumed. |
| WS-N | Pilot/production gates | Objective, non-automatic gates for demo, controlled pilot, controlled production and general production. |

## 5. Out of scope

- reopening Phase 31.4 or assigning Retry 17;
- changing V2.4, its SHA, contracts or historical evidence;
- redesigning native identity semantics or the AdminApps authority model;
- implementing or invoking Phase 32/RuntimeAdoption;
- unrelated product features, UI/UX optimization or MedSupplier changes;
- destructive migration, restore over an existing database, shared-environment
  failure injection/load testing, staging/production action or deployment;
- declaring certification, production SLOs, RTO or RPO without owner approval.

## 6. Entry gates

| Gate | Machine-verifiable condition | Current disposition |
|---|---|---|
| E-01 | Phase 31.4 promotion closure says `verdict=PROMOTED` | `PASS` |
| E-02 | Retry 16 exact comparison says `result=PASS`, `total_mismatches=0` | `PASS` |
| E-03 | Retry 16 SHA manifest and current-source hashes verify | `PASS` read-only on 2026-09-22 |
| E-04 | V2.4 contract hash equals `a102d...9387` and historical preservation passes | `PASS` |
| E-05 | Full regression evidence passes with no unexplained skip in the declared suite | `PASS` in promoted source-integrity evidence; must be rerun for Phase 31.5 entry |
| E-06 | `pending_migrations=0`, `fake_migrations=0`, `manual_schema_patches=0` in an isolated target | `PASS` in Retry 16; must be rerun for Phase 31.5 entry |
| E-07 | Active current P0 count is `0` | Required before execution |
| E-08 | Active current V2.5 P1 count is `0` | Required before execution |
| E-09 | Dedicated disposable environment and teardown plan are approved; no shared target resolves | Outstanding |
| E-10 | Test-data classification, destructive-test boundaries and evidence redaction rules are approved | Outstanding |

Execution starts only when E-01 through E-10 are serialized in one entry-gate
artifact with no `FAIL` or `UNKNOWN`. Baseline facts are not enough to infer the
two outstanding environment-safety approvals.

## 7. Exit gates

Promotion requires one final closure artifact to prove all of the following:

1. Fresh deployment reproducibility: `PASS`.
2. Supported-predecessor upgrade and reconciliation: `PASS`.
3. Backup/restore into a fresh target and post-restore integrity/RLS: `PASS`.
4. Declared disaster-recovery scenarios: `PASS`; observed recovery metrics
   recorded, with approved RTO/RPO targets either met or explicitly
   `NOT_DEFINED` (which blocks production but need not block baseline capture).
5. Transaction recovery/idempotency matrix: `PASS`.
6. Security and RLS negative matrix: `PASS`, cross-tenant successes `0`, runtime
   superuser/owner/`BYPASSRLS` principals `0`.
7. Secret/configuration review and isolated rotation drill: `PASS`, committed
   secrets `0`, secret values in evidence/logs `0`.
8. Observability signal tests: `PASS` for every declared critical failure mode;
   liveness/readiness are distinct and backlog/failed-ingress signals exist.
9. Performance baseline: recorded with workload, dataset, environment,
   warmup/run counts and latency distribution; correctness errors `0`. Any SLO
   remains `NOT_DEFINED` unless separately approved.
10. Concurrency matrix: `PASS`, duplicate governed IDs `0`, invalid revision
    forks `0`, cross-tenant contamination `0`.
11. AdminApps integration resilience matrix: `PASS` with idempotent replay and
    fail-closed authorization behavior.
12. Maintenance and rollback/forward-fix drills: `PASS`; immutable evidence is
    unchanged and destructive schema rollback is never assumed.
13. Full regression against the Phase 31.4 baseline: `PASS`, exact-comparison
    mismatch `0` where the baseline oracle applies.
14. Current release findings: `P0=0`, `P1=0`; teardown `PASS`; SHA manifest
    verifies `PASS`.
15. Demo, pilot, controlled-production and general-production decisions remain
    separate explicit decisions; no tier is promoted automatically.

## 8. Severity and release blocking

Reuse the existing P0/P1 model:

- **P0**: boundary break, cross-tenant access, data loss/corruption, authority
  fail-open, committed secret, unrecoverable critical state or misleading
  material AI/provenance. Blocks continued unsafe execution, pilot and all
  production decisions.
- **P1**: required control/reproducibility/recovery/observability/security gate
  absent or failing without a demonstrated boundary breach. Blocks Phase 31.5
  promotion and Enterprise pilot/production.
- Existing P2/P3 remain tracked. A P2 may block scale or production when its
  owning gate says so; it is not silently relabeled.

Any finding that makes the isolated target unsafe stops the affected
workstream. Other independent read-only work may continue; no finding grants
authority to test a shared environment.

## 9. Evidence model

Future execution should create append-only artifacts under
`docs/governance/evidence/phase31_5/`:

```text
00_entry_gate.json
01_environment.json
02_deployment_reproducibility.json
03_upgrade.json
04_backup_restore.json
05_disaster_recovery.json
06_transaction_recovery.json
07_security_rls_negative.json
08_secrets_configuration.json
09_observability.json
10_performance_baseline.json
11_concurrency.json
12_integration_resilience.json
13_operational_maintenance.json
14_rollback_forward_fix.json
15_pilot_production_gates.json
16_regression.json
17_final_closure.json
18_sha256.json
```

Every artifact records schema/version, run ID, isolated target identity,
sanitized configuration, commands/scenarios, expected/actual result, counts,
finding IDs, timestamps and referenced hashes. The final SHA manifest excludes
itself and historical Phase 31.4 evidence remains referenced, never copied or
rewritten.

## 10. Dependencies and known risks

Dependencies include a declared supported predecessor, reproducible dependency
lock/runtime, isolated PostgreSQL 18.6 topology, isolated AdminApps contract
test source, sanitized fixtures, backup storage, worker/outbox execution,
secret injection/rotation mechanism and owners for RTO/RPO and release tiers.

Known risks carried into the phase include the repository risk register's
release-pipeline reproducibility, SQLite-only test history, multi-database
configuration, absent DR/restore evidence, production PostgreSQL inventory and
the frontend `localStorage` token risk that blocks formal production. Phase
31.4 promotion does not close these operational risks.

## 11. First executable ToDo

**Phase 31.5 Entry Gate + Environment Reproducibility Audit**.

This is a read-only/isolated planning-and-proof task. It must:

1. serialize E-01 through E-10 without changing Phase 31.4 evidence;
2. inventory the exact supported runtime, PostgreSQL 18.6 image/digest, roles,
   dependency locks, configuration keys, migrations and service topology;
3. identify a disposable target and prove a target guard prevents shared or
   persistent database selection;
4. define sanitized fixtures, teardown and evidence-redaction rules; and
5. emit `00_entry_gate.json` and `01_environment.json` plus their hashes.

It must not yet provision a database, apply migrations, inject failures, run a
restore/load test, contact live AdminApps, deploy or modify product code.

## 12. Recommendation

Approve only the first executable ToDo above. After its entry artifact passes,
authorize WS-A deployment reproducibility in a fresh isolated environment as a
separate execution step. Do not authorize Phase 32/RuntimeAdoption or any
production/pilot promotion from this plan.
