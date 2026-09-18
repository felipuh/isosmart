# Phase 17 — First Controlled Mutation Post-POC Hardening + Effectiveness Foundation Design Gate

**Date:** 2026-08-24  
**PostgreSQL:** 18.6 official image, ephemeral only  
**Final run:** `20260824T210713Z_e6db86`  
**Verdict:** **PROMOTED**

## 1. Entry, scope and migration evolution

All Phase 16 guarantees entered promoted: migration 0015; one shared Opportunity
primitive; exact ActionPlan/governance/TOCTOU checks; durable idempotency; one
atomic QMS+execution transaction; 13/13 rollback; least-privilege owner;
SECURITY DEFINER/RLS/search-path controls; separate compensation; zero external
effects. Migrations 0001–0015 remained byte-for-byte frozen.

Phase 17 adds only `0016_controlled_execution_recovery_hardening`. It adds no
business action and no EffectivenessCheck schema. The sole forward mutation is
still `opportunity.defer_evaluation`, `under_evaluation -> deferred`; resume is
still a separately governed compensation.

## 2. Ambiguous COMMIT model and actual transport fault

The modeled sequence is client transaction work → client sends COMMIT → socket
fails before libpq can know whether PostgreSQL committed. This is not the Phase
16 application-response-loss simulation.

The harness used a one-shot, local PostgreSQL wire-protocol proxy. It parsed the
frontend simple-query packet, forwarded the literal COMMIT to PostgreSQL, parsed
backend packets, observed `ReadyForQuery` (server transaction completion),
withheld that packet, then closed the client connection. libpq raised an unknown
connection result while a fresh connection proved the transaction committed.
The proxy touched only the ephemeral local test transport and was removed by the
process finalizer.

A separate pre-COMMIT case executed all transactional SQL and closed the client
without sending COMMIT. PostgreSQL rolled back on disconnect. This proves both
sides of the ambiguity, not an exception after a known response.

## 3. Reconciliation algorithm and outcomes

Reconciliation uses an exact SECURITY DEFINER read/audit capability under the
trusted transaction-local tenant. Input is only typed Authorization ID and
idempotency key; forward and compensation have separate public functions. The
key is SHA-256 hashed for audit and never persisted raw outside the existing
claim field.

Algorithm:

1. load exact Authorization and immutable ActionPlan;
2. match tenant, Organization, action, policy, Plan ID/hash, target lineage,
   expected revision/state/fingerprint and intended transition;
3. find `(tenant,idempotency_key)` execution;
4. if absent, prove the exact expected target is still the current leaf;
5. if present, prove exact claim provenance and terminal state;
6. prove exactly one Receipt, resulting revision, domain Event/Outbox/Audit and
   execution Event/Outbox/Audit, including IDs, trace, result hash and revisions;
7. append a separate `execution_reconciliation` audit signal;
8. return one of three closed outcomes.

| Outcome | Durable meaning | Caller behavior |
|---|---|---|
| `COMMITTED` | all eight governed artifact classes exist exactly once with exact provenance | return immutable Receipt, `replayed=true`; never mutate |
| `NOT_COMMITTED` | no claim and exact authorized source leaf remains unchanged | one safe controlled execution may proceed |
| `INCONSISTENT` | any mismatch, missing/duplicate artifact, running claim or unsafe target | fail closed; operational intervention; no retry |

The committed-ack-loss path observed one Opportunity revision, one business
event/outbox/audit, one succeeded ActionExecution, one Receipt and one execution
event/outbox/audit. Recovery returned that execution. The pre-COMMIT path first
returned NOT_COMMITTED, then executed exactly once. A terminal execution without
Receipt returned INCONSISTENT and manufactured no success.

## 4. Durable claim ownership, concurrency and crash

Phase 16's unique `(tenant_id,idempotency_key)` ActionExecution row was durable,
but two first callers could both see no row before uniqueness rejected one
INSERT. 0016 adds a transaction advisory lock on a canonical tenant+key claim
identity before the existing lookup. The ActionExecution row remains the durable
owner and the unique constraint remains the independent database defense; the
advisory lock is only the pre-row serializer.

Two exact concurrent callers produced one creator (`replayed=false`) and one
waiter returning the same execution (`replayed=true`). Two concurrent callers
using the same claim with different Authorization/Plan/target produced exactly
one owner and one provenance conflict. Claims are never reassigned.

The controlled path cannot durably abandon a running claim: claim, mutation and
terminal receipt share one transaction, so crash/disconnect before commit rolls
all of them back. A deliberate running fixture was classified INCONSISTENT. No
lease, timeout or silent stealing was invented; recovery remains an explicit
operational decision until source/product policy defines more.

## 5. Observability and event taxonomy

Stable reconciliation/audit fields are tenant, Organization, hashed idempotency,
claim/execution ID, Plan ID/hash, governance artifact, action, target and revision
provenance, trace, observed artifact counts, reconciliation outcome/reason,
execution outcome, replay/retry class and compensation lineage. Raw keys, tokens,
secrets and prompts are excluded.

`opportunity.status_changed` remains the business event.
`action_execution.succeeded` remains the execution lifecycle event.
Reconciliation is operational-only and is recorded in immutable audit under a
separate stream; no new DomainEvent taxonomy was created. The repo has no metrics
foundation, so metric names are design-only and no Prometheus/OpenTelemetry
dependency was introduced.

## 6. Function-owner ACL inventory and minimization

Catalog proof after 0016:

- NOLOGIN, NOSUPERUSER, NOINHERIT, NOCREATEDB, NOCREATEROLE, NOREPLICATION,
  NOBYPASSRLS;
- member of no role; migrator's separately controlled membership in owner remains
  the DDL path;
- owns no table or sequence and has no sequence USAGE/UPDATE;
- owns only the exact Phase 15/16 SECURITY DEFINER wrappers/primitive required by
  the design; no schema CREATE after migration;
- target privileges remain Opportunity `SELECT/INSERT/UPDATE` (UPDATE only for
  `FOR UPDATE`), ActionExecution `SELECT/INSERT/UPDATE`, Receipt `SELECT/INSERT`,
  Event/Outbox `SELECT/INSERT`, exact provenance reads and audit append;
- 0016 removed unused SELECT on Organization, UserProjection and Recommendation;
- 0016 added tenant-scoped audit SELECT solely to validate exact artifact counts;
- PUBLIC cannot execute controlled or reconciliation functions; EXECUTOR cannot
  execute private generic helpers or perform generic Opportunity DML.

## 7. SECURITY DEFINER/RLS regression

PASS: fixed `search_path=pg_catalog,pg_temp`, qualified trusted objects, no
dynamic SQL, fixed forward/compensation/reconciliation wrappers, no arbitrary
action/status/field/value/tenant/Organization parameter, PUBLIC revoked, distinct
NOLOGIN owner, executor-only EXECUTE, exact Organization/revision/hash checks,
ENABLE+FORCE RLS, A/none/B, hostile search path and direct INSERT/UPDATE/DELETE
denials. Migrations issue owner-only grants by controlled `SET LOCAL ROLE`; no
owner or bypass privilege was broadened.

## 8. Retained-history analysis and rollback policy

Artifacts were classified as:

- historical schema/data: Opportunity revisions, ActionExecution, Receipt;
- capability: wrappers, grants, policies and functions;
- adapter behavior: Python exact invocation/reconciliation;
- immutable history: business/execution events, outbox and audit, including
  compensation.

Decision: **option C**. After the first controlled execution, 0015 is a
forward-only deployment boundary. `0016 -> 0015` passed with retained history.
`0015 -> 0014` was intentionally rejected by old synthetic-only constraints;
the failed migration transaction preserved every controlled row and capability
definition. No data was deleted to fake reversibility.

Schema rollback is not compensation. Business history remains readable and
compensation still requires a new exact governance chain.

## 9. Capability disable and expand/contract

The tested kill switch revoked EXECUTE on the recoverable forward wrapper. A new
controlled defer was denied, while the public Opportunity command still appended
its normal revision/event/outbox/audit. Existing controlled executions and
receipts remained unchanged. EXECUTE was regranted only to continue the isolated
gate.

Production evolution is: expand → revoke/disable capability → preserve/read
history → stop new writes → reconcile/observe → ship a forward fix → contract
only after backup/restore, approval and zero-use evidence. Never downgrade data,
disable RLS or delete history as rollback.

## 10. Effectiveness source reconciliation

| Source | Concept | Field/relation | Semantics | Implementable now? | Rationale |
|---|---|---|---|---:|---|
| Integrated DOCX | runtime stage | Execute → “MEDIR EFICACIA” | effectiveness follows execution | Boundary only | exact object lifecycle/outcomes absent |
| DOCX clauses 6.1/9.1/10.2 | evaluation | measure/review efficacy; evidence and method matter | benefit must be evaluated, not inferred | Partial design | no exact timing/actor/outcome contract |
| XLSX architecture map | `EffectivenessCheck` | `check_id; subject_type; subject_id; method; due_at; result; evidence_id` | separate check with evidence | Partial design | polymorphic subject and one evidence field are insufficient for exact execution provenance |
| Master JSON | `EffectivenessCheck` | same fields; CAPA has `effectiveness_check_id` | named historical relation and corrective-action use | Partial design | no ActionExecution FK, versioning or outcome enum |
| Source DDL | `effectiveness_check` | tenant, subject, method, due, result, evidence, completed | minimal persistence sketch | No migration | DDL is partial; lacks Organization/RLS/exact governed chain |
| Mermaid | lifecycle | Execute → Measure effectiveness → Institutional memory | execution success is not effectiveness | Boundary only | learning step exists conceptually but is not authority to automate learning |
| Draw.io | lifecycle node | `Effectiveness` after Execute | separate stage | Boundary only | no fields/actor/timing |
| Nodes/Edges CSV | monitoring/evidence graph | 9.1.1 measurement/evaluation, 10.2.2 corrective evidence | measurement and evidence are relevant | Partial design | no EffectivenessCheck entity contract in graph edges |
| OpenAPI | Evidence endpoint only | Evidence hash/metadata | supporting evidence is governed | No API | no EffectivenessCheck operation or contract |
| LEEME | single business object/evidence graph | no check fields | avoid duplicate objects; preserve provenance | Principle only | not a lifecycle specification |

The sources sufficiently prove separation and evidence dependence, but not enough
to implement a safe EffectivenessCheck schema/command in Phase 17.

## 11. EffectivenessCheck candidate model and blockers

The future record is separate, append-only/versioned and tenant/Organization
scoped. It references exact ActionExecution and Receipt provenance, ActionPlan
ID/hash, AgentDecision, Recommendation, target Opportunity lineage, authorized
before revision and resulting revision. It links one or more exact Evidence
revisions through a typed junction; MeasurementDefinition is optional only for a
source-backed measurement-derived method. It stores method, observation/result,
assessed/completed time, actor provenance and trace.

It never changes ActionExecution status, Receipt, Approval, Authorization, Plan,
Decision or Recommendation. Recommendation confidence is not effectiveness.
Compensation neutralizes a mutation; effectiveness evaluates intended benefit.
`ineffective` must never automatically compensate; another governed decision is
required. No learning optimizer, retraining, prompt tuning, policy mutation,
cross-tenant learning or automatic recommendation adjustment was implemented.

Blocking Product Policy decisions before implementation:

1. closed outcomes (the conceptual effective/ineffective/inconclusive set is not
   yet frozen; unknown must remain distinct from success);
2. who may assess: human, system or measurement-derived, and exact AdminApps
   authority for a human;
3. how `due_at`/earliest assessment is derived; no arbitrary seven-day window;
4. minimum/maximum Evidence cardinality and acceptable evidence state;
5. when a MeasurementDefinition is required and how its observation is frozen;
6. append/version lineage, corrections and event semantics;
7. whether `effectiveness_check.recorded` is a business event (not implemented).

## 12. Tests and verification

New hardening matrix:

| Test | Result |
|---|---|
| disconnect before COMMIT reaches server | PASS — NOT_COMMITTED then one retry |
| COMMIT reaches server / acknowledgement lost | PASS — COMMITTED exact replay |
| terminal execution missing Receipt | PASS — INCONSISTENT |
| concurrent same claim | PASS — one creator, one deterministic waiter |
| same key/different provenance | PASS — one owner, one conflict |
| running/abandoned fixture | PASS — no stealing, INCONSISTENT |
| owner exact ACL/role/ownership/sequence/membership | PASS |
| 0016 retained-history reverse | PASS |
| 0015 retained-history reverse | intentionally blocked, history preserved |
| capability disable | PASS — controlled denied/history retained |
| public command during disable | PASS |
| compensation history | Phase 16 regression PASS |
| Effectiveness does not alter execution semantics | PASS — schema absent; receipt flag false |

Complete Phase 16 regression passed inside the final PostgreSQL lifecycle:
controlled forward, compensation, Phase 15.2 24/24 matrix, golden parity,
autocommit rejection, hostile search path, ACL/catalog, RLS, direct bypass,
concurrency, stale state, idempotency/lost response and 13/13 rollback.

## 13. Regression, integrity, hashes and teardown

- PostgreSQL 18.6 official image: PASS; lifecycle and fault proxy PASS.
- Backend: **165 PASS / 0 FAIL / 0 SKIP**.
- Foundation: **67 PASS / 0 FAIL / 0 SKIP**.
- `manage.py check`: PASS, zero issues.
- `makemigrations --check --dry-run`: PASS, no changes.
- Python compilation: PASS.
- Migrations 0001–0015: **15/15 exact promoted SHA-256 MATCH**.
- Migration 0016 SHA-256:
  `e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5`.
- Authoritative source artifacts: **10/10 exact SHA-256 MATCH**.
- Phase 17 scoped `git diff --check`: PASS.
- Finalizer: database, eleven roles, container, volume, proxy sockets and temp
  directory absent/closed: PASS.

The full legacy suite emitted its pre-existing Chroma/PostHog DNS attempts; they
failed closed and are not imported or called by the controlled execution or
Phase 17 paths. No production, staging, persistent/shared developer database,
AdminApps/MedSupplier mutation, deployment, broker, provider, HTTP, notification,
shell/subprocess adapter or external business effect occurred.

## 14. Residual risks

1. An INCONSISTENT outcome needs an operational runbook and human authority for
   repair; Phase 17 deliberately provides no auto-repair or claim stealing.
2. The advisory key serializer depends on every executor using the recoverable
   wrapper. 0016 revokes the old wrapper from EXECUTOR and tests exact ACLs;
   privileged DBA remains a governed trust boundary.
3. Owner needs Opportunity UPDATE only for `SELECT FOR UPDATE`; append-only
   triggers and NOLOGIN/non-membership remain required compensating controls.
4. 0015 is forward-only after first controlled history; release tooling must
   block downgrade and use capability revocation/forward fix.
5. Effectiveness outcomes, actor authority, timing, evidence cardinality,
   MeasurementDefinition relation and correction/version semantics remain
   source/product-policy blockers. No implementation is authorized yet.

There are **0 P0** and **0 P1** defects blocking promotion of this hardening and
design gate. The Effectiveness blockers constrain the next phase's scope rather
than weakening execution recovery.

## 15. Promotion verdict

**PHASE 17 — FIRST CONTROLLED MUTATION POST-POC HARDENING + EFFECTIVENESS FOUNDATION DESIGN GATE: PROMOTED**

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| Ambiguous COMMIT | PASS | protocol proxy + pre-COMMIT disconnect | operational runbook next |
| Reconciliation | PASS | COMMITTED/NOT_COMMITTED/INCONSISTENT exact audit | no blind retry |
| Claim ownership | PASS | durable row+unique; advisory pre-row serialization | retain wrapper ACL |
| Retained history | PASS / FORWARD-ONLY | 0016 reverse safe; 0015 reverse blocked without data loss | enforce release boundary |
| Capability disable | PASS | EXECUTE revoke; public command/history preserved | govern enable/disable |
| Least privilege/RLS | PASS | catalog, ACL, A/none/B, hostile path, direct DML | preserve regression |
| EffectivenessCheck | DESIGN ONLY / BLOCKED FOR IMPLEMENTATION | ten-source matrix; candidate provenance model | close policy decisions only |
| Phase 16 regression | PASS | full promoted matrix + 13/13 rollback | no second action |
| Backend/foundation | 165/165; 67/67 PASS | executed locally | maintain baseline |
| PostgreSQL/teardown | PASS | official 18.6 run `e6db86`; all resources absent | none |
| Frozen migrations/sources | 15/15; 10/10 MATCH | SHA-256 | preserve byte-for-byte |
| External effects | ZERO | isolated local DB/test transport only | no deployment |

## NEXT_CODEX_PROMPT

Execute PHASE 18 — EFFECTIVENESSCHECK SOURCE/POLICY BLOCKER CLOSURE + CONTROLLED EXECUTION OPERATIONAL READINESS DESIGN GATE in `/home/felipe/proyectos/isosmart` without adding a second QMS action, deploying, enabling production/staging/shared databases, creating external effects, or implementing EffectivenessCheck schema before its contract is approved. Preserve migrations `0001–0016`, the ten authoritative source artifacts, Product Policy `controlled-qms-action-policy/v1`, ADR-0007–ADR-0010, and the exact `opportunity.defer_evaluation` / separately governed compensation semantics. Close only the seven Phase 17 Effectiveness blockers with an explicit versioned non-normative Product Policy: exact outcomes including unknown/inconclusive, human/system/measurement-derived actor authority and AdminApps boundary, source-backed timing/due semantics, mandatory Evidence revision cardinality/validation, MeasurementDefinition linkage, append-only correction/version lineage, and event/audit semantics; do not implement automatic compensation or learning. In parallel, design the operational runbook for COMMITTED/NOT_COMMITTED/INCONSISTENT reconciliation, capability disable/enable governance, incident ownership, retained-history forward-only deployment checks and observability fields/alerts without adding external telemetry dependencies. Use PostgreSQL 18.6 ephemeral only for any behavioral proof, rerun the complete Phase 17 and Phase 16 matrices, backend/foundation regressions, Django integrity, hashes, git hygiene and teardown, and emit PROMOTED only if the Effectiveness contract is sufficiently exact to authorize a later implementation gate with zero P0/P1; otherwise fail closed and name only the unresolved policy blockers.
