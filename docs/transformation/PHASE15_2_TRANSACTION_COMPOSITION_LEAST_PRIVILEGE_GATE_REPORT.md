# Phase 15.2 — Transaction Composition + Least-Privilege Design Gate

**Fecha:** 2026-08-24

**Naturaleza:** design + contract gate; docs-only; zero QMS/external effect

**Veredicto:** **PROMOTED**

## 1. Verdict and entry blockers

The sole candidate remains:

```text
action_type = opportunity.defer_evaluation
target_type = Opportunity
transition = under_evaluation -> deferred
compensation = opportunity.resume_evaluation
impact = standard
reversibility = reversible under defined preconditions
Human Approval = required
max_autonomy = A3
policy = controlled-qms-action-policy/v1 (non-normative)
```

Phase 15 and Phase 15.1 remain historically `NOT PROMOTED`. This gate closes
the two residual technical design blockers without implementing either
solution:

| Blocker | Result | Design proof |
|---|---|---|
| A — transaction-aware composition | **CLOSED** | one caller-owned atomic boundary and one shared Opportunity primitive can contain target revision/Event/Outbox/Audit plus execution completion/Receipt/Event/Outbox/Audit |
| B — least privilege | **CLOSED** | executor has no Opportunity DML; an exact `SECURITY DEFINER` defer wrapper delegates to the shared private primitive under a non-login, non-owner, NOBYPASSRLS function role |

The two designs are mutually compatible because a PostgreSQL function executes
inside the caller's existing transaction and cannot independently commit.

## 2. Evidence inspected

`AGENTS.md`, Phase 5/12/13/14/15/15.1 reports, ADR-0007/0008, Product Policy
v1, eventing, immutable audit, PostgreSQL RLS and threat-model designs were read.
The complete Opportunity model/command, tenant context, Event/Outbox/Audit
services, ActionExecution service, migrations 0005/0014 and role/grant harness
patterns were inspected. Initial `git status` showed pre-existing user changes;
they were preserved.

Repository version is Django 4.2.22. Its documented transaction contract says
nested `atomic` blocks are savepoints and only the outermost block commits or
rolls back. The selected design is stricter: the inner primitive creates no
atomic/savepoint at all and relies on the outer owner. See
[Django 4.2 transactions](https://docs.djangoproject.com/en/4.2/topics/db/transactions/).

PostgreSQL documents that `SECURITY DEFINER` uses function-owner privileges and
requires a safe search path and selective EXECUTE grants. The design follows
those requirements and also keeps the owner subject to RLS. See
[PostgreSQL 18 CREATE FUNCTION](https://www.postgresql.org/docs/18/sql-createfunction.html)
and [row security](https://www.postgresql.org/docs/18/ddl-rowsecurity.html).

## 3. Current Opportunity command problem

`change_opportunity_status` delegates to `_revise`, which currently combines:

- trusted tenant context and transaction ownership;
- current-leaf lookup and validation;
- status input normalization;
- copy-forward of Process/hypothesis/benefit/feasibility;
- append-only revision and lineage preservation;
- `opportunity.status_changed` v1;
- TransactionalOutbox;
- immutable audit;
- fault injection and result construction.

`trusted_tenant_context` rejects `connection.in_atomic_block`. Therefore the
command cannot run beneath the ActionExecution transaction required here.
Phase 14 separately commits execution start, invokes the synthetic executor,
then opens another completion transaction. Calling the current command between
those boundaries could leave a QMS revision committed without a coherent
controlled receipt. This is the exact composition defect; the domain semantics
themselves remain promoted.

## 4. Proposed shared Opportunity primitive

The future refactor has two layers.

### Public/governed command boundary

`change_opportunity_status` retains its current signature and remains
responsible for trusted identity, outer transaction, input validation, actor/
trace resolution and result mapping.

### Transaction-aware domain operation

One private, repository-owned primitive, conceptually
`apply_opportunity_status_transition_in_transaction`, will:

1. assert an active atomic block on the requested database alias;
2. accept one exact current revision and one validated desired status;
3. lock the expected revision and prove it is the unique current leaf;
4. preserve tenant, Organization, lineage, Process, hypothesis, benefit and
   feasibility;
5. append revision N+1 with exact predecessor;
6. emit the unchanged `opportunity.status_changed` schema v1 payload;
7. insert one TransactionalOutbox row;
8. append one Opportunity audit entry;
9. return revision/event/outbox/audit/trace identifiers.

It is an Opportunity-domain primitive, not
`change_opportunity_status_for_executor`. The executable core is a private
`SECURITY INVOKER` database function so the normal APP command and the narrow
controlled wrapper call the same mutation/event/audit implementation. EXECUTOR
cannot execute the private generic function.

## 5. Public command compatibility

Future public flow:

```text
change_opportunity_status(existing arguments)
  -> validate status and trace exactly as today
  -> trusted_tenant_context owns atomic + SET LOCAL
  -> shared primitive
  -> MaterialMutationResult with the same meaning
  -> commit
```

Preserved behavior: nonblank status validation, current-leaf rejection,
append-only history, copied substantive fields, lineage/revision rules, event
type/schema/payload, outbox, audit hashes/metadata, actor/trace, rollback fault
semantics and result fields. Contract tests in Phase 16 must compare old/new
golden event and audit shapes before the old implementation is removed.

## 6. Transaction ownership contract

| Question | Contract |
|---|---|
| Active `transaction.atomic` required? | Yes, on the exact alias/connection. |
| Assertion? | Fail before SQL unless `connection.in_atomic_block` and trusted transaction-local tenant context match. |
| Nest under outer atomic? | Yes; that is its intended use. |
| Savepoint? | No. The inner primitive opens no `atomic` block. |
| Commit/rollback/autocommit change? | Never; Django forbids these inside atomic and the function contains no transaction control. |
| Exception behavior? | Propagate; caller must not catch inside the atomic unit. |
| Event/Outbox/Audit transaction? | Same connection and outer transaction as the revision. |

A new internal tenant-context binder may set/verify `SET LOCAL` only after the
outer caller opens atomic. It accepts `TrustedTenantIdentity`, actor and trace,
never request-controlled tenant data. The existing public context manager is
not weakened.

## 7. Event/Outbox/Audit and execution composition

Future controlled flow:

```text
outer atomic on executor alias
  SET LOCAL trusted tenant/actor/trace
  lock or create exact ActionExecution/idempotency identity
  revalidate Authorization + Plan/hash + Approval + policy
  lock and revalidate exact Opportunity leaf/fingerprint
  call narrow defer wrapper -> shared Opportunity primitive
    Opportunity revision
    Opportunity DomainEvent
    Opportunity TransactionalOutbox
    Opportunity Audit
  complete ActionExecution
  create ActionExecutionReceipt
  create execution lifecycle DomainEvent
  create execution TransactionalOutbox
  create execution Audit
commit once
```

There is no dispatcher, async callback or `on_commit` substitute inside this
unit. Outbox dispatch happens only after commit. If Opportunity audit, Receipt,
execution Event/Outbox/Audit or commit fails, the target revision and every
other uncommitted artifact roll back together.

## 8. Lock ordering and deadlock analysis

Fixed order for the controlled path:

1. ActionExecution/idempotency row (or unique-key claim);
2. immutable Authorization/ActionPlan/Approval reads;
3. exact Opportunity current revision/lineage lock;
4. Opportunity event-stream sequencing lock;
5. Opportunity audit-stream lock;
6. execution event-stream sequencing lock;
7. execution audit-stream lock;
8. associated Outbox/Receipt inserts.

The public Opportunity command begins at step 3 and follows the same suffix.
It never takes an execution lock after a target lock, so there is no inverse
ordering with the adapter. The current `Max(aggregate_version)+1` path must be
serialized by the shared primitive using the repository's promoted stream-lock
strategy before allocation. Audit append retains its per-stream serialization.

`SELECT FOR UPDATE` on the expected revision plus the unique predecessor
constraint gives pessimistic and constraint-level no-fork protection. A
deadlock, serialization failure or unique race propagates and rolls back. It is
not replay success; the caller re-reads the durable idempotency identity before
any retry.

## 9. Exact current leaf, TOCTOU and state token

The authorized state token is exactly:

- tenant ID from trusted context;
- Organization ID from frozen ActionPlan and target;
- Opportunity lineage ID (`target_id`);
- current revision ID (`expected_revision_id`);
- integer revision (`expected_revision`);
- status `under_evaluation`;
- `controlled-opportunity-state-v1` canonical SHA-256 of tenant,
  Organization, lineage, revision ID/number, Process ID, hypothesis, benefit,
  feasibility and status.

Under the target lock the wrapper derives plan/target values server-side,
recomputes the state hash and compares every element. It also checks no row has
`previous_revision_id = expected_revision_id`. Any mismatch is
`stale_target`/conflict with no domain command.

Required lifecycle:

```text
dry-run -> human Approval -> ExecutionAuthorization -> execution transaction
-> target lock -> exact revalidation -> mutation
```

Dry-run or authorization success never substitutes for execution-time
revalidation.

## 10. Idempotency and already-desired state

Before mutation, lock/find the durable identity:

`tenant + Organization + Authorization + plan hash + action type + target`
`lineage + expected revision ID + idempotency key`.

- If an exact committed Receipt proves the current leaf is the exact resulting
  revision produced by that execution, return that Receipt and do not invoke
  the primitive.
- If status is `deferred` but the exact execution/Receipt/domain-event/
  resulting-revision provenance is absent or different, return stale/conflict.
- A running row without Receipt is not success; recovery policy remains
  fail-closed and is outside this gate.

Status equality alone never proves idempotency.

## 11. Transaction failure matrix

| # | Failure point | Expected outcome |
|---:|---|---|
| 1 | target lock | exception/timeout; outer transaction rollback; no new artifact |
| 2 | stale-state validation | controlled conflict; rollback; primitive not called |
| 3 | Opportunity revision insert | rollback target/execution unit |
| 4 | Opportunity DomainEvent | revision rolls back |
| 5 | Opportunity Outbox | revision and event roll back |
| 6 | Opportunity Audit | revision/event/outbox roll back |
| 7 | ActionExecution completion | Opportunity unit and execution start/claim roll back |
| 8 | Receipt | Opportunity mutation and completion roll back |
| 9 | execution DomainEvent | Receipt/completion/Opportunity unit roll back |
| 10 | execution Outbox | execution event and all prior writes roll back |
| 11 | execution Audit | every write in the unit rolls back |
| 12 | commit | PostgreSQL commits all or none; connection loss during commit is `outcome_unknown`, resolved only by exact idempotency/Receipt read, never blind re-execution |

Every detected failure before commit leaves no business mutation. A separate
post-rollback security/attempt record may be designed later, but cannot claim a
QMS result and is not part of the atomic success unit.

## 12. Least-privilege alternatives

| Option | Security | Composition | Testability/integration | RLS/search path | Complexity/maintainability | Decision |
|---|---|---|---|---|---|---|
| A. Python service + executor target DML | convention only; bypassable | easy ORM atomic | easy unit tests | RLS limits tenant, not action | low code, unacceptable privilege | Reject |
| B. Standalone exact `SECURITY DEFINER` wrapper | strong literal capability | joins caller transaction | strong raw-SQL tests | must harden owner/path/RLS | medium | Use as outer privilege wrapper |
| C. Dedicated shared domain DB function | eliminates duplicated mutation logic | native same transaction | golden contract + PG tests | invoker by default; wrapper elevates | higher migration cost, one source of truth | Use as inner primitive |
| D. Executor role with INSERT policy/GUC flag | generic insert or forgeable custom GUC | easy | brittle negative tests | policy cannot prove authorized action alone | deceptively simple | Reject |

Selected architecture combines B+C: one private shared `SECURITY INVOKER`
Opportunity primitive and one public-to-EXECUTOR exact `SECURITY DEFINER`
forward-action wrapper.

## 13. Selected privilege architecture and hardening

Function owner:

- dedicated `NOLOGIN`, non-superuser, `NOBYPASSRLS`, `NOINHERIT` role;
- not owner of Opportunity/Event/Outbox/Audit/execution tables;
- not granted to runtime roles;
- only SELECT/INSERT/function rights required by the shared primitive and
  explicit tenant policies;
- no CREATE on `public`, `qms`, `eventing`, `audit` or temporary trusted
  schemas beyond unavoidable default temp behavior addressed by search path.

Narrow wrapper contract accepts only exact execution/authorization identities
(and, if UUID allocation remains caller-generated, typed UUIDs whose linkage is
validated). It accepts no tenant, Organization, action type, target type,
desired status, field name/value, arbitrary JSON mutation or SQL fragment. It:

1. derives tenant from transaction context;
2. loads exact execution/authorization/plan/Approval;
3. requires literal action/target/policy/A3/standard/reversible;
4. derives target and expected state from frozen Plan;
5. locks and revalidates;
6. invokes the private shared primitive with fixed
   `under_evaluation -> deferred`;
7. returns bounded typed result IDs.

Hardening: `SECURITY DEFINER`, `VOLATILE`, not leakproof, fixed
`search_path=pg_catalog,pg_temp`, fully qualified relations/functions/types,
no dynamic SQL/default/variadic overload, explicit casts, `REVOKE FROM PUBLIC`
and selective EXECUTE in one migration transaction. Function owner differs
from EXECUTOR. SQL injection surface is limited to typed values and no string
interpolation.

## 14. Executor privilege matrix

| Executor capability | Phase 15.2 | Future Phase 16 POC |
|---|---:|---:|
| Opportunity SELECT | none currently; exact tenant-scoped read only if wrapper requires it | direct SELECT optional/minimal; wrapper derives target |
| Opportunity INSERT | **No** | **No** |
| Opportunity UPDATE | **No** | **No** |
| Opportunity DELETE | **No** | **No** |
| execute private generic status primitive | **No** | **No** |
| narrow defer capability | No runtime grant | EXECUTE exact wrapper only |
| narrow resume capability | **No** | separate wrapper/grant only in separately authorized compensation POC |
| ActionExecution lifecycle | existing Phase 14 exact functions only | exact evolved start/complete functions |
| Event/Outbox/Audit | existing bounded rights | only rights needed for lifecycle; target writes occur under function owner |

Direct INSERT/UPDATE/DELETE, arbitrary status transition, field mutation and
cross-tenant calls must all return permission denial or controlled rejection.

## 15. RLS behavior

EXECUTOR remains LOGIN, non-superuser, non-owner, `NOBYPASSRLS`, `NOINHERIT`.
The function owner is also non-superuser, non-owner and `NOBYPASSRLS`; therefore
its statements remain subject to ENABLE+FORCE RLS. Policies for its minimal
table rights use only:

```sql
tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
```

The wrapper independently matches Opportunity tenant/Organization to
ActionExecution, Authorization and Plan. Context A sees/changes A only; B sees/
changes B only; missing or empty context yields no row/permission and no
fallback. No function parameter can override the tenant. Immutable tenant/
Organization triggers and composite FKs remain active.

`SECURITY DEFINER` is selected only with these controls. Table ownership or
`BYPASSRLS` for the owner would invalidate Blocker B and force `NOT PROMOTED`.

## 16. Compensation capability separation

Forward EXECUTE grant does not authorize resume. Compensation requires a
separate wrapper with fixed `deferred -> under_evaluation`, a new ActionPlan,
dry-run, human Approval, ExecutionAuthorization, ActionExecution,
idempotency/fingerprint and receipt. Prefer a separate function rather than an
action-literal parameter. Its privilege may be granted only for the isolated
compensation POC and removed during teardown. Failure preserves the original
forward revision/receipt/history.

## 17. Threat matrix

| Threat | Control | Required Phase 16 evidence | Residual POC risk |
|---|---|---|---|
| generic executor DML | no target DML grants | catalog + direct SQL denials | Low |
| function privilege escalation | fixed inputs/literals; private generic function | function ACL/owner/signature tests | Low |
| unsafe search path | pg_catalog, pg_temp; qualification; no CREATE | catalog definition + hostile temp object test | Low |
| cross-tenant target | trusted SET LOCAL + RLS + exact joins | A/B/none matrix | Low |
| wrong Organization | composite equality/FKs | cross-Organization rejection | Low |
| stale/concurrent Opportunity | leaf lock + exact token + unique predecessor | stale and two-writer tests | Low |
| duplicate execution | durable exact receipt identity | concurrent/exact replay tests | Low |
| partial commit | one outer atomic | forced failure at every stage | Low |
| domain event/audit missing | same primitive/transaction | forced event/audit failure | Low |
| receipt missing | same transaction | forced receipt failure | Low |
| execution completed without QMS mutation | domain result required before terminal write | forced domain failure | Low |
| QMS mutation without completion | completion/receipt before one commit | forced completion failure | Low |
| arbitrary field/status | no such wrapper parameter | signature + hostile calls | Low |
| compensation abuse | separate function/grant/auth | forward role cannot resume | Low |
| commit outcome ambiguity | exact idempotency read/reconcile | disconnect-at-commit test if feasible | Medium operational |

There are 0 P0 and 0 P1 design defects blocking an isolated ephemeral POC.
Django 4.2.22 is an existing unsupported dependency and must be upgraded on the
product security roadmap; the Phase 16 POC is local, ephemeral, no-network and
does not expand production exposure, so it is not a blocker for this bounded
proof.

## 18. Full security matrix

`R` is tenant/minimum scoped; `W` is existing governed write; `N` is none;
`F` is exact function only.

| Principal | Opportunity SELECT | INSERT | UPDATE | DELETE | defer capability | resume capability | ActionExecution write | Approval write | Authorization write |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| APP | R | W via command | N | N | N | N | N | N | N |
| WORKER | R | N | N | N | N | N | N | N | N |
| EXECUTOR | minimum/optional R | N | N | N | F | N | F | N | N |
| HUMAN APPROVER | minimum R | N | N | N | N | N | N | F existing | N |
| PROJECTOR | N | N | N | N | N | N | N | N | N |
| AUDIT WRITER | N | N | N | N | N | N | N | N | N |
| NORMATIVE CURATOR | N | N | N | N | N | N | N | N | N |
| AGENT CURATOR | N | N | N | N | N | N | N | N | N |
| MIGRATOR | controlled | controlled | controlled | controlled | install/revoke | install/revoke | controlled | controlled | controlled |
| FUNCTION OWNER | R under RLS | minimal primitive INSERT | N | N | internal call only | N | only if exact wrapper composition requires | N | N |

No right in this matrix is granted by Phase 15.2.

## 19. Phase 16 exact acceptance test plan

1. Authorized exact defer succeeds.
2. Direct EXECUTOR `UPDATE qms.opportunity` denied.
3. Direct EXECUTOR `INSERT qms.opportunity` denied.
4. Direct EXECUTOR `DELETE qms.opportunity` denied.
5. Arbitrary desired status/action/field cannot be passed and is denied.
6. Status other than `under_evaluation` denied.
7. Wrong expected revision ID/number denied.
8. Changed Process/hypothesis/benefit/feasibility or canonical hash denied.
9. Cross-tenant target denied and not disclosed.
10. Cross-Organization target denied.
11. Missing/empty tenant context denied.
12. Change after authorization but before execution denied stale.
13. Concurrent second transition loses/conflicts; one revision/event only.
14. Exact duplicate execution returns prior Receipt without second mutation.
15. Unrelated already-deferred leaf conflicts, never replay success.
16. Opportunity event created exactly once with existing v1 golden payload.
17. Opportunity audit created exactly once with existing hashes/metadata.
18. Execution event, audit and receipt each created exactly once.
19. Forced domain failure rolls back execution completion and all new rows.
20. Forced Receipt failure rolls back Opportunity revision/event/outbox/audit.
21. Forced Opportunity or execution audit failure rolls back everything.
22. Compensation requires separately authorized resume wrapper/capability.
23. Failed/stale compensation leaves original history and receipt intact.
24. Reverse migration restores the exact Phase 15.2 baseline.

Additional mandatory contract tests: old/new public command golden parity;
inner primitive rejects autocommit; no savepoint/commit occurs; executor cannot
execute private primitive; owner is NOLOGIN/non-superuser/NOBYPASSRLS/non-owner;
PUBLIC has no EXECUTE; hostile search-path/temp shadowing fails; A-only/none/B-
only on the same connection after commit and rollback; every failure-matrix
stage has zero partial delta; allowlist contains no second action.

## 20. Anticipated migration 0015 design — not implemented

Only Phase 16 may create 0015. Anticipated contents:

1. bootstrap/configure a dedicated non-login function-owner role in the
   ephemeral harness and assert its attributes/ownership;
2. create private shared Opportunity status-transition function with the exact
   existing revision/Event/Outbox/Audit contract;
3. create exact defer `SECURITY DEFINER` wrapper, safe search path, owner, ACL,
   literal policy/action/transition and frozen-plan revalidation;
4. add minimal RLS policies/grants for the function owner; never target DML for
   EXECUTOR;
5. evolve ActionExecution/Receipt executor/outcome constraints and exact
   start/complete functions only enough for this one POC action;
6. add supporting event-stream uniqueness/serialization only if catalog proof
   shows current constraints insufficient; no unrelated schema;
7. reversible SQL restores Phase 14 definitions/ACLs/policies and drops only
   0015 objects; role teardown is performed and proven by the harness.

No model/API/provider/external-effect schema is justified. The wrapper does not
include resume; if the required compensation POC is in the same ephemeral
phase, its separate function/grant must still be separately authorized and
removed on reverse/teardown.

## 21. Frozen migration hashes

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

**14/14 MATCH. Migration 0015 is absent.**

## 22. Authoritative source hashes

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

**10/10 MATCH.**

## 23. Zero-side-effect evidence and verification

- Only this report and ADR-0009 were created.
- No Python, model, test, setting, API, migration, role, grant, function,
  adapter, executor registry or allowlist changed.
- No database or QMS command was opened or invoked; no Opportunity revision or
  other QMS state can have persisted.
- No production/staging/shared/ephemeral DB, broker, provider, HTTP mutation,
  external system, AdminApps, MedSupplier or deployment was used.
- `SyntheticNoOpExecutor` remains the only executable executor and
  `EXECUTOR_ALLOWLIST` remains exactly `{synthetic_noop}`.
- Migration 0015 is absent; 0001-0014 and all sources remain byte-identical.
- `git diff --check` and final status were run after writing these docs.
- Backend/Django/migration/compile suites were not rerun because no code, test,
  schema or runtime artifact changed; inherited baselines are not represented
  as newly executed.

## 24. Residual blockers and scope of promotion

No design blocker remains for an ephemeral controlled PostgreSQL POC. Phase 16
must still implement and behaviorally prove every item in section 19; a failed
catalog, RLS, parity, rollback or direct-bypass test fails closed and prevents
promotion beyond the POC.

Product Policy v1 remains `PROPOSED — NOT APPROVED FOR CONTROLLED POC` as an
unchanged historical governance artifact. This report is the explicit gate
decision recommending **APPROVE FOR EPHEMERAL CONTROLLED POC**; it does not
silently rewrite the policy. The policy remains non-normative. Candidate impact,
reversibility, mandatory Approval and A3 ceiling are unchanged.

This promotion authorizes only Phase 16 implementation/testing in a dedicated,
ephemeral PostgreSQL 18.6 resource. It authorizes no production/shared DB,
general real execution, external effect or second forward action.

## 25. Promotion verdict

**PHASE 15.2 — TRANSACTION COMPOSITION + LEAST-PRIVILEGE DESIGN GATE: PROMOTED**

| Blocker/component | State | Evidence | Risk/next action |
|---|---|---|---|
| Blocker A — composition | CLOSED | shared caller-owned primitive; one atomic unit; failure matrix | implement parity + rollback tests in Phase 16 |
| Blocker B — least privilege | CLOSED | private invoker primitive + exact hardened definer wrapper; no executor DML | prove catalogs, hostile calls and A/B/none |
| Mutual compatibility | PASS | function and completion writes share caller transaction | no external call inside atomic |
| Opportunity public command | DESIGN PRESERVED | same signature/event/audit/history contract | golden parity before replacing code path |
| TOCTOU/idempotency | DESIGN CLOSED | exact locked leaf/fingerprint + exact prior Receipt | prove concurrency and commit ambiguity |
| Compensation | SEPARATE / NOT GRANTED | distinct fixed resume wrapper and authorization | no implicit forward privilege |
| Product Policy v1 | NON-NORMATIVE / UNCHANGED | explicit successor gate only | version future semantic changes |
| Adapter/real executor/runtime grant | ABSENT | repository/status/allowlist scan | Phase 16 POC only after migration |
| SyntheticNoOpExecutor | ONLY EXECUTABLE IMPLEMENTATION | allowlist code scan | preserve until Phase 16 gate executes |
| Migrations 0001-0014 | FROZEN / 14/14 MATCH | exact SHA-256 | preserve byte-for-byte |
| Migration 0015 | ABSENT | filesystem scan | Phase 16 only if implementing selected design |
| Source artifacts | FROZEN / 10/10 MATCH | exact SHA-256 | preserve byte-for-byte |
| QMS/external effects | ZERO | docs-only; no DB/external invocation | maintain isolated POC boundary |
| P0/P1 blocking ephemeral POC | 0 / 0 | completed design/threat/security gates | implementation failures fail closed |

## NEXT_CODEX_PROMPT

Implement exclusively Phase 16 in `/home/felipe/proyectos/isosmart` as an EPHEMERAL POSTGRESQL 18.6 CONTROLLED MUTATION POC for the single forward action `action_type="opportunity.defer_evaluation"`, `target_type="Opportunity"`, transition `under_evaluation -> deferred`; do not add a second forward action, touch production/staging/shared databases, create external effects, deploy, or modify the ten authoritative source artifacts or migrations `0001-0014`. Read `AGENTS.md`, Product Policy `controlled-qms-action-policy/v1`, ADR-0009 and the Phase 15.2 report first. Implement migration `0015+` only as required by ADR-0009: a caller-owned transaction-aware shared Opportunity domain primitive reused by the unchanged public command and the controlled path; an exact hardened least-privilege executor capability with dedicated NOLOGIN non-superuser NOBYPASSRLS non-table-owner function owner, fixed safe search_path, fully qualified objects, no dynamic SQL, PUBLIC revoked, no generic Opportunity INSERT/UPDATE/DELETE for EXECUTOR, and no arbitrary action/status/field/value parameters. Require exact ActionPlan canonical hash, policy identity, effective human Approval, A3 ceiling, tenant/Organization equality, SELECT FOR UPDATE/current-leaf proof, exact revision/status/substantive fingerprint revalidation after authorization, durable exact idempotency, and one atomic unit containing Opportunity revision + DomainEvent + Outbox + Audit + ActionExecution completion + Receipt + execution Event + Outbox + Audit. Execute the complete 24-test Phase 16 acceptance plan plus public-command golden parity, autocommit rejection, hostile search-path/function ACL/catalog tests, A/none/B RLS and direct bypass tests, every forced-failure rollback point, concurrent execution, commit-outcome reconciliation, full backend regression from 165 PASS, foundation baseline from 67 PASS, Django check, makemigrations check/dry-run, Python compilation, PostgreSQL forward/reverse/forward, 14/14 frozen migration hashes, 10/10 source hashes and mandatory teardown. Implement compensation only as a separately authorized `opportunity.resume_evaluation` POC with a separate fixed capability/grant and its own Plan, Approval, Authorization, idempotency and rollback tests; it must not broaden the forward wrapper or executor authority. Keep all resources ephemeral and emit PROMOTED only if every functional, atomicity, RLS, least-privilege, reverse-migration, zero-external-effect and teardown check passes; otherwise fail closed, report exact residual blockers and remove all ephemeral resources.
