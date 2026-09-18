# Phase 16 — First Controlled Internal QMS Mutation POC

**Date:** 2026-08-24

**PostgreSQL:** 18.6 official image, ephemeral only

**Final run:** `20260824T204123Z_aaa169`

**Product policy:** `controlled-qms-action-policy/v1`, non-normative
**Verdict:** **PROMOTED**

## 1. Scope and migration evolution

Migration `0015_first_controlled_qms_mutation_poc` is the only schema evolution.
Migrations `0001–0014` remain byte-for-byte frozen. The only forward real action is
`opportunity.defer_evaluation`, fixed to `under_evaluation -> deferred`.
`opportunity.resume_evaluation` exists only as a separately planned, approved,
authorized and invoked compensation POC.

The migration installs versioned canonicalization/fingerprint helpers, one shared
Opportunity-domain transition primitive, one private governed controlled executor,
and two fixed `SECURITY DEFINER` wrappers. It extends the existing execution and
receipt constraints only for `controlled_opportunity` and the two exact outcomes.
No new generic entity/field/value/status API exists.

The tested schema sequence was `0001…0015 -> 0014 -> 0015`. Before Phase 16
history was written, reverse removed both wrappers, every Phase 16 policy/grant and
the shared functions, restored the Phase 14 executor/receipt constraints and
trigger semantics, and left the public Opportunity command operational through its
pre-Phase-16 compatible fallback. The second forward succeeded.

## 2. Shared Opportunity primitive and public compatibility

`RiskOpportunityObjectiveCommandService.change_opportunity_status` retains its
public signature and validation. Its flow is:

```text
validate boundary -> trusted_tenant_context (outer atomic + SET LOCAL)
-> _apply_opportunity_status_transition_in_transaction -> commit
```

The inner method asserts `connection.in_atomic_block`, opens no atomic/savepoint,
never commits and has no external call. On PostgreSQL 0015 it invokes
`qms.foundation_0015_apply_opportunity_status_transition`; the controlled wrappers
invoke the same function. After a reverse to 0014, the public command uses the
equivalent repository implementation so the rollback does not strand the public
API.

The database primitive locks the exact expected revision, proves it is the unique
leaf, copies Process/hypothesis/benefit/feasibility, appends revision N+1, creates
`opportunity.status_changed` schema v1, Outbox and immutable audit, and returns the
new revision/lineage/event/outbox/audit/trace IDs. It is not executable by
EXECUTOR. Autocommit invocation failed before SQL and left zero mutation.

Golden scenarios using equal substantive fields proved equal resulting status,
revision increment, predecessor/lineage rules, copied substantive fields, event
type/schema/status delta/revision, Outbox relationship, and audit before/after
hash inputs. Controlled execution added only execution-specific artifacts.

## 3. Controlled adapter, plan and governance

`ControlledOpportunityActionService.defer_evaluation` has no action/status/field/
value argument. It binds a `TrustedTenantIdentity` inside one caller-owned atomic
block and calls only `qms.defer_opportunity_evaluation(authorization_id,
idempotency_key)`. Resume is a different method and different fixed database
function.

Inside the wrapper the system recomputes `iso-smart-action-plan-v1` and requires:

- the exact Plan, Plan hash, Authorization, dry-run and target;
- literal action/target/policy/impact/reversibility and A3 exactly;
- exact Decision/Recommendation/Run/Definition/published ModelPolicy chain;
- the exact effective, latest, unambiguous human `approve` outcome;
- matching tenant and Organization throughout;
- every required precondition present and satisfied;
- `controlled-opportunity-state-v1` fingerprint equality.

A0/A1/A2 and A4 cannot execute this real mutation: the wrapper requires A3
exactly. Reject, request_changes, missing and ambiguous approvals remain denied by
the Phase 13/14 matrices and are revalidated in the Phase 16 function.

## 4. TOCTOU, current leaf, fingerprint and lock order

The mandatory chain is dry-run -> Approval -> Authorization -> execution
transaction -> idempotency claim -> `SELECT FOR UPDATE` expected Opportunity leaf
-> exact revalidation -> mutation. The fingerprint covers tenant, Organization,
lineage, revision ID/number, Process, hypothesis, benefit, feasibility and status.

Actual lock/write order:

1. existing execution/idempotency row lookup with `FOR UPDATE`, or unique running
   execution claim;
2. immutable Authorization/Plan/DryRun/Decision/Run/Approval reads;
3. exact Opportunity expected leaf `FOR UPDATE` and successor check;
4. Opportunity event-stream advisory transaction lock, Event, Outbox, audit;
5. execution completion and Receipt;
6. execution event-stream advisory transaction lock, Event, Outbox, audit;
7. outer commit.

The public command starts at step 3 and uses the same suffix. No controlled path
acquires an execution lock after the target. Two concurrent authorizations against
one expected leaf produced exactly one success and one stale/conflict, one new
revision and one business event.

## 5. Idempotency and commit reconciliation

The durable identity is tenant + Organization + Authorization + Plan hash + action
+ target lineage + expected revision + idempotency key. The first execution creates
one effect. Exact replay reads the committed ActionExecution and Receipt and
returns it with `replayed=true`; it never invokes the primitive again. The same key
with a different authorization/plan failed conflict. A target made `deferred` by
the public command failed stale and was not mistaken for replay.

The lost-response test discarded the first returned value after commit and retried
the same request. The committed execution/receipt was reconstructed; Opportunity,
business event, execution event, Outbox and audit counts did not duplicate.
Ambiguous commit outcome uses the same algorithm: reconnect, bind trusted tenant,
look up the exact idempotency identity, verify terminal execution + immutable
Receipt + resulting revision/event provenance, return it if exact, otherwise
conflict/unknown; never blindly rerun.

## 6. Atomic unit and rollback matrix

One PostgreSQL transaction contains the execution claim, Opportunity lock and
revision, Opportunity Event/Outbox/Audit, execution terminal transition, Receipt,
execution Event/Outbox/Audit and commit. There is no dispatcher or external call
inside it. Execution cannot become succeeded without the returned business
revision, and the business revision cannot commit without execution completion.

| Failure point | Result |
|---|---|
| after target lock | PASS — zero partial delta |
| before revision insert | PASS — zero partial delta |
| after revision insert | PASS — zero partial delta |
| after Opportunity DomainEvent | PASS — zero partial delta |
| after Opportunity Outbox | PASS — zero partial delta |
| after Opportunity Audit | PASS — zero partial delta |
| before execution completion | PASS — zero partial delta |
| after execution completion mutation | PASS — zero partial delta |
| after Receipt | PASS — zero partial delta |
| after execution DomainEvent | PASS — zero partial delta |
| after execution Outbox | PASS — zero partial delta |
| after execution Audit | PASS — zero partial delta |
| immediately before commit | PASS — zero partial delta |

## 7. SECURITY DEFINER, owner, ACL and RLS

The fixed wrappers are `SECURITY DEFINER`, `VOLATILE`, use
`search_path=pg_catalog,pg_temp`, fully qualify trusted objects, contain no dynamic
SQL and accept only typed Authorization ID plus idempotency key. Tenant comes only
from transaction-local `app.tenant_id`; Organization/target/action/status are
server-derived. `PUBLIC` execute is revoked.

The owner is a run-scoped `foundation_qms_action_owner_*` role: NOLOGIN,
NOSUPERUSER, NOBYPASSRLS, NOINHERIT, not a table owner and not a runtime role. It
has no CREATE on qms after the migration's ownership transfer. It receives only
the table/function privileges required for locks, append operations and exact
completion. Opportunity UPDATE is required by PostgreSQL for `SELECT FOR UPDATE`;
append-only triggers reject actual row UPDATE. No runtime principal is a member.

EXECUTOR is LOGIN, non-superuser, NOBYPASSRLS, NOINHERIT and non-owner. It has no
Opportunity INSERT/UPDATE/DELETE and cannot execute the private shared primitive.
Only EXECUTOR has forward/resume wrapper EXECUTE; APP, WORKER, PROJECTOR, AUDIT
WRITER, NORMATIVE CURATOR, AGENT CURATOR, HUMAN APPROVER, AUTHORIZER and PUBLIC do
not. Direct INSERT, UPDATE, DELETE and arbitrary status attempts were denied.

Both owner and executor remain under ENABLE + FORCE RLS. Tenant A executed A;
tenant B against A was denied; missing context was denied. Organization and target
must equal the frozen Plan/Authorization/Execution chain. Catalog assertions proved
owner and executor are neither owner nor BYPASSRLS. A hostile temporary
`opportunity` object and caller search path did not shadow any trusted reference.

## 8. Receipt and effectiveness boundary

The successful result/Receipt includes execution ID, Plan hash, action literal,
policy v1, Opportunity lineage, before revision ID/number/status, after revision
ID/number/status, domain event ID, trace, compensation eligibility and timestamps.
It records `business_state_changed=true` and `effectiveness_claimed=false`.
Success means only that the exact authorized transition committed. No
`EffectivenessCheck` or beneficial-outcome claim exists.

## 9. Compensation

Resume uses `qms.resume_opportunity_evaluation`, not a desired-status parameter.
The test created a new Plan, human Approval chain, Authorization, idempotency key,
ActionExecution and Receipt. History remained:

```text
under_evaluation r1 -> deferred r2 -> under_evaluation r3
```

The forward wrapper rejected a resume Plan and the resume wrapper rejected a
forward Plan. An intervening public revision after forward defer made the planned
compensation stale; resume was denied and no later revision/history rewrite was
created. Compensation uses the same atomic rollback design as forward execution.

## 10. Phase 15.2 24-test acceptance matrix

| # | Acceptance test | State | Evidence |
|---:|---|---|---|
| 1 | authorized exact defer | PASS | final Phase 16 PG run |
| 2 | executor UPDATE denied | PASS | direct DML matrix |
| 3 | executor INSERT denied | PASS | direct DML matrix |
| 4 | executor DELETE denied | PASS | direct DML matrix |
| 5 | arbitrary action/status/field unavailable | PASS | fixed signatures + hostile calls |
| 6 | source status mismatch denied | PASS | stale/unrelated-deferred tests |
| 7 | wrong revision ID/number denied | PASS | exact locked token checks |
| 8 | substantive field/hash change denied | PASS | fingerprint revalidation |
| 9 | cross-tenant denied | PASS | tenant B -> A denial |
| 10 | cross-Organization denied | PASS | exact composite Plan/target checks |
| 11 | missing tenant denied | PASS | raw no-context call |
| 12 | post-authorization change denied | PASS | stale compensation/unrelated defer |
| 13 | concurrent second transition loses | PASS | two real concurrent connections |
| 14 | exact duplicate returns Receipt | PASS | lost-response replay |
| 15 | unrelated deferred conflicts | PASS | public-provenance stale test |
| 16 | Opportunity event exactly once/golden v1 | PASS | parity + replay count |
| 17 | Opportunity audit exactly once/hashes | PASS | parity + rollback matrix |
| 18 | execution event/audit/receipt exactly once | PASS | durable receipt/replay checks |
| 19 | domain failure rolls all back | PASS | failure points 1–6 |
| 20 | Receipt failure rolls all back | PASS | after-Receipt injection |
| 21 | Opportunity/execution audit failure rolls back | PASS | both audit injections |
| 22 | compensation separately authorized | PASS | distinct Plan/Approval/Auth/execution |
| 23 | stale compensation preserves history | PASS | intervening revision denial |
| 24 | reverse restores Phase 15.2 capability state | PASS | forward/reverse/forward catalog test |

## 11. Additional Phase 16 security and contract tests

| Test | State | Evidence |
|---|---|---|
| public command golden parity | PASS | equal substantive/event/audit semantics |
| primitive autocommit rejection | PASS | failure before SQL, zero mutation |
| hostile search path | PASS | pg_temp shadow object test |
| function ACL catalog | PASS | exact principal matrix |
| owner NOLOGIN/non-super/non-bypass/non-owner | PASS | pg_roles/pg_class assertions |
| SECURITY DEFINER + RLS A/none/B | PASS | real roles and contexts |
| lost response / ambiguous commit | PASS | exact durable reconstruction |
| complete 13-point rollback | PASS | 13/13 zero partial deltas |
| forward/compensation separation | PASS | wrong-wrapper denials |
| public command after 0015 reverse | PASS | compatibility execution at 0014 |

## 12. Regression, integrity and resource evidence

- Full backend: **165 PASS / 0 FAIL / 0 SKIP**; legitimate test-count delta from
  the frozen baseline is zero because Phase 16 behavioral proof lives in the
  PostgreSQL promotion harness.
- Foundation: **67 PASS / 0 FAIL / 0 SKIP**.
- `manage.py check`: PASS, zero issues.
- `makemigrations --check --dry-run`: PASS, no changes.
- Python compilation: PASS.
- PostgreSQL server: **18.6**, official image, real isolated roles/connections.
- Migration 0015 SHA-256:
  `5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3`.
- Frozen migrations `0001–0014`: **14/14 exact promoted SHA-256 MATCH**.
- Authoritative source artifacts: **10/10 exact SHA-256 MATCH**.
- Scoped `git diff --check`: PASS; the known unrelated Sidebar whitespace was not
  modified.
- Teardown: database, eleven roles, container, volume and temp directory absent.

### Frozen migration hashes

| Migration | SHA-256 | Result |
|---|---|---|
| 0001 | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` | MATCH |
| 0002 | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` | MATCH |
| 0003 | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` | MATCH |
| 0004 | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` | MATCH |
| 0005 | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` | MATCH |
| 0006 | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` | MATCH |
| 0007 | `c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec` | MATCH |
| 0008 | `285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032` | MATCH |
| 0009 | `412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc` | MATCH |
| 0010 | `c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79` | MATCH |
| 0011 | `cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2` | MATCH |
| 0012 | `7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc` | MATCH |
| 0013 | `06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b` | MATCH |
| 0014 | `ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33` | MATCH |
| 0015 | `5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3` | NEW |

### Authoritative source hashes

| Artifact | SHA-256 | Result |
|---|---|---|
| DOCX | `8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c` | MATCH |
| Draw.io | `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa` | MATCH |
| Mermaid | `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3` | MATCH |
| XLSX | `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5` | MATCH |
| Nodes CSV | `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3` | MATCH |
| Edges CSV | `30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6` | MATCH |
| DDL | `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e` | MATCH |
| OpenAPI | `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8` | MATCH |
| JSON | `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb` | MATCH |
| LEEME | `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db` | MATCH |

No production, staging, shared DB, AdminApps DB, MedSupplier DB, deployment,
HTTP action, provider, shell/subprocess adapter, broker, notification or external
filesystem business effect occurred. Podman and local files were used only by the
isolated test harness and mandatory teardown. The full legacy regression emitted
its pre-existing Chroma/PostHog telemetry DNS attempts; they failed closed and are
not imported or invoked by the controlled adapter.

## 13. Residual risks

1. The POC owner requires table UPDATE privilege solely because PostgreSQL requires
   it for `SELECT FOR UPDATE`; append-only triggers and NOLOGIN/non-membership are
   essential compensating controls and must remain regression-tested.
2. Reversing 0015 after committed controlled history is not a supported product
   rollback: narrowing Phase 14 checks would conflict with retained Phase 16
   execution rows. The proven schema reverse is pre-effect; an operational
   production rollout would require expand/contract retention design. This POC
   authorizes no deployment.
3. Commit ambiguity was simulated as a lost caller response after commit, not a
   forced network disconnect during PostgreSQL COMMIT. Durable reconciliation is
   behaviorally proven, but transport-specific fault injection belongs in Phase 17.
4. The policy remains non-normative and the POC remains ephemeral. No second
   forward action or EffectivenessCheck is authorized.

There are 0 P0 and 0 P1 defects blocking the next hardening/design gate within
this ephemeral POC scope.

## 14. Promotion verdict

**PHASE 16 — FIRST CONTROLLED INTERNAL QMS MUTATION POC: PROMOTED**

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| Migration 0015 | PASS | PG 18.6 forward/reverse/forward; SHA `5e297591…` | freeze after promotion |
| Shared primitive/public command | PASS | golden parity; autocommit rejection; reverse compatibility | retain one source of semantics |
| Controlled forward action | PASS | exact A3/Approval/Plan/Auth/leaf/fingerprint | no second forward action |
| Atomicity | PASS | one transaction; 13/13 rollback | repeat under Phase 17 fault tooling |
| Idempotency/concurrency | PASS | replay/conflict/unrelated provenance/two writers | add transport disconnect test |
| SECURITY DEFINER/owner/ACL | PASS | hardened path, role/catalog/direct DML tests | preserve least privilege |
| RLS/search path | PASS | A/none/B; hostile pg_temp | keep catalog regression |
| Receipt/effectiveness | PASS / SEPARATE | exact receipt; false effectiveness claim | design effectiveness foundation only |
| Compensation | PASS / SEPARATE | new governance chain; stale denial; history retained | no general resume authority |
| Phase 15.2 matrix | 24/24 PASS | section 10 | none |
| Additional Phase 16 tests | PASS | section 11 | transport commit ambiguity in Phase 17 |
| Full backend/foundation | 165/165; 67/67 PASS | executed locally | maintain baselines |
| Frozen migrations/sources | 14/14; 10/10 MATCH | exact SHA-256 | preserve byte-for-byte |
| External effects | ZERO | internal ephemeral PostgreSQL only | no deployment |
| Teardown | PASS | DB/roles/container/volume/temp absent | none |

## NEXT_CODEX_PROMPT

Execute PHASE 17 — FIRST CONTROLLED MUTATION POST-POC HARDENING + EFFECTIVENESS FOUNDATION DESIGN GATE in `/home/felipe/proyectos/isosmart` without adding another QMS action, deploying, using production/staging/shared databases, or creating external effects. Preserve migrations `0001–0015`, the ten authoritative sources, Product Policy `controlled-qms-action-policy/v1`, and the exact `opportunity.defer_evaluation` / separately authorized compensation boundaries. Focus on transport-level ambiguous-COMMIT fault injection and reconciliation, production-grade expand/contract rollback with retained Phase 16 history, stronger idempotency claim serialization/observability, function-owner privilege minimization review, and design-only `EffectivenessCheck` semantics/evidence linkage that never changes the meaning of execution success. Re-run the complete Phase 16 PostgreSQL 18.6 security/atomicity/concurrency matrix, full backend/foundation regressions, hashes and teardown; fail closed if any Phase 16 guarantee regresses.
