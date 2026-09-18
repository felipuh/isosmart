# Phase 19 — EffectivenessCheck Foundation Implementation

**Date:** 2026-08-24

**Policy:** `effectiveness-check-policy/v1` — ISO Smart Product Policy, non-normative

**PostgreSQL:** 18.6 official image, isolated ephemeral lifecycle

**Final run:** `20260824T220042Z_01693a`
**Verdict:** **PROMOTED**

## 1. Scope and migration evolution

Phase 19 implements only the approved EffectivenessCheck foundation for the exact
succeeded controlled action `opportunity.defer_evaluation`. It adds migration
`0017_effectiveness_check_foundation`; migrations 0001–0016 remain byte-for-byte
unchanged. It adds no second QMS action, endpoint, deployment, production/staging/
shared-environment enablement, external effect, automatic compensation, automatic
learning or effectiveness-driven executor.

0017 is additive. In an empty/no-Phase-19-history state, `0016 -> 0017 -> 0016 ->
0017` passed. Once an EffectivenessCheck exists, reverse raises and preserves all
history; operational rollback is disable/read/forward-fix, never history deletion.

## 2. Source and policy reconciliation

All ten authoritative artifacts were byte-read directly and their SHA-256 digests
match the promoted manifest. The approved Product Policy and ADR-0011 were not
modified. Source-backed facts remain: EffectivenessCheck is separate from and
downstream of execution, uses method/due/result/Evidence semantics, and evaluates
results/effectiveness. Policy-v1 choices remain explicitly non-normative: closed
outcomes, human authority, trusted timing, Evidence 1..N, conditional measurement,
linear correction, and one recorded event.

No `RequirementControl`, `StandardEdition`, `KnowledgeLayerRule`, normative
coverage or certifiability semantics were created or reinterpreted.

## 3. EffectivenessCheck model and exact provenance

`qms.effectiveness_check` is tenant- and Organization-scoped and append-only. A
complete record freezes:

- exact ActionExecution and its exact terminal ActionExecutionReceipt;
- exact ActionPlan/hash and ExecutionAuthorization;
- exact AgentDecision and Recommendation;
- Opportunity lineage, authorized pre-execution revision and exact resulting
  deferred revision;
- outcome, assessment method, criteria hash and planning-context hash;
- frozen `due_at`, `assessed_at`, policy, trace/correlation;
- exact optional MeasurementDefinition revision;
- human UserProjection link plus AdminApps external actor snapshot and resolved
  authority provenance; and
- predecessor, revision and correction reason.

The insert trigger proves the execution is `succeeded`, executor is
`controlled_opportunity`, receipt belongs to that execution, receipt outcome is
`opportunity_deferred`, every Plan/Authorization/Decision/Recommendation link is
the exact promoted chain, the Opportunity result matches the receipt payload, and
`effectiveness_claimed=false`. No current/latest pointer is used.

## 4. Outcomes and timing

The database enum constraint permits exactly:

| Outcome | Policy-v1 semantics |
|---|---|
| `effective` | every mandatory criterion is supported and none disproved |
| `ineffective` | valid exact Evidence disproves at least one mandatory criterion |
| `inconclusive` | assessment completed but Evidence cannot support a reliable binary conclusion |
| `unknown` | assessment could not be completed because an evidenced blocker made required Evidence unavailable/invalid/inaccessible |

`inconclusive` and `unknown` require a bounded reason code and human explanation.
All v1 records require `assessed_at >= due_at`; there is no 7/30/90-day default.
`due_at` comes only from the typed governed planning context, is bound to execution,
Organization, target and policy, and must be later than the resulting revision.
Execution success never derives an outcome; a failed/non-committed execution is
ineligible rather than automatically ineffective.

## 5. Human authority and AdminApps boundary

The command accepts one `TrustedEffectivenessAuthority`, not tenant, Organization,
actor, role, MFA or permission request fields. It requires active AdminApps access,
MFA and `qms.effectiveness_check.record`; correction independently requires
`qms.effectiveness_check.supersede`. Transaction-local trusted context is verified
again by the insert trigger. UserProjection existence alone grants nothing.

The persisted actor snapshot is limited to UserProjection ID, AdminApps external
ID, actor type `human`, authority context version and decision reference. No MFA
material, token, secret, role database or unnecessary personal data is stored.
System, worker, agent, projector, audit-writer and executor principals cannot attest.
No new database principal was justified: the existing app command principal is the
server-side AdminApps decision boundary; the existing human principal has read-only
access to Phase-19 tables.

## 6. EffectivenessEvidence and validation

`qms.effectiveness_evidence` links a check to one exact immutable Evidence revision
and freezes its lineage ID, revision number, content hash and criterion role. A
deferred constraint trigger requires at least one link. There is no semantic
numeric maximum and the command never truncates. Unique `(check,evidence)` rejects
exact duplicates. Composite foreign keys and validation triggers reject cross-
tenant/cross-Organization links and any ID/lineage/revision/hash mismatch. Later
Evidence revisions cannot change existing links; Evidence content is never copied.

## 7. MeasurementDefinition boundary

The linkage is exactly one-or-none. `measurement_derived` planning requires one
exact same-tenant/same-Organization MeasurementDefinition revision; other v1
assessment methods require it absent. No latest pointer, MeasurementRecord, value,
unit, threshold, measured-at field or generic measurement processor was introduced.

## 8. Immutable history, supersession and correction

UPDATE and DELETE triggers reject material mutation for checks and Evidence links.
A correction inserts a new complete row with revision `predecessor + 1`, a mandatory
correction reason and independently resolved reviewer authority. The predecessor is
unique, so no fork can form. Self-reference, cross-boundary predecessor, revision
gap, predecessor reuse, different execution/receipt/governance chain or different
Opportunity target is rejected. Since rows cannot update and predecessors must
already exist with revision +1, cycles cannot be created.

PostgreSQL proved `v1=inconclusive -> v2=effective`: both rows, Evidence sets,
events, outbox rows and audits remain reconstructible, with v2 as the only leaf.

## 9. Event, outbox and immutable audit

Every initial or correction record emits one `effectiveness_check.recorded`, schema
v1. Payload contains identifiers, hashes, target before/result, outcome, method,
human actor reference, exact Evidence references, optional measurement revision,
timing, lineage, trace and policy; it contains no Evidence body or secret.

The same transaction appends one pending TransactionalOutbox row and one
ImmutableAuditLog row. Audit reconstructs tenant/Organization, reviewer authority,
check/revision/predecessor, execution/receipt/plan/governance chain, exact target,
criteria/planning hashes, outcome/reason, Evidence IDs/hashes, optional measurement,
event/outbox IDs and trace. The existing audit secret filter is preserved; the
exact ExecutionAuthorization is represented by the sanitized
`execution_governance_id` identifier.

## 10. Atomic command and rollback matrix

`EffectivenessCheckCommandService.record_effectiveness_check` is the only explicit
command. One outer transaction creates Check, 1..N Evidence links, DomainEvent,
Outbox and Audit. It has no generic save or external adapter.

| Forced failure point | Result |
|---|---|
| before Check | PASS — zero partial unit |
| after Check | PASS — zero partial unit |
| during first Evidence link | PASS — zero partial unit |
| during later Evidence link | PASS — zero partial unit |
| after Evidence links | PASS — zero partial unit |
| after DomainEvent | PASS — zero partial unit |
| after Outbox | PASS — zero partial unit |
| after Audit | PASS — zero partial unit |
| immediately before commit | PASS — zero partial unit |

Atomic success committed exactly the Check, Evidence links, event, outbox and audit.

## 11. No derived effects or contamination

Before/after row counts and aggregate byte-state digests matched for ActionExecution,
Receipt, ActionPlan, ExecutionAuthorization, AgentDecision, Recommendation,
RecommendationBasis, Opportunity, ModelPolicy, AgentDefinition,
KnowledgeLayerRule, RequirementControl, StandardEdition and EvidenceCoverage.
Therefore recording `inconclusive` and `effective` changed none of execution,
compensation, recommendation confidence, learning/model/prompt/rule or normative
history. The Effectiveness module imports no HTTP, shell, subprocess, provider,
tool, notification or controlled-action service. `ineffective` uses the same inert
recording path and cannot invoke `opportunity.resume_evaluation`.

## 12. RLS, principals and raw SQL

Both Phase-19 tables have `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL
SECURITY`. Real app-principal visibility passed A/none/B = `2/0/0`; transaction-
local context cleanup passed through the inherited Phase 16/17 pool and rollback
matrices. Composite constraints enforce Organization isolation and DB-level tenant/
Organization immutability through the material mutation guards.

Direct UPDATE and DELETE of checks, tenant reassignment of Evidence links, exact
duplicate and cross-Organization Evidence links, and a second successor fork were
denied. PostgreSQL also exercised frozen Evidence constraints, exact execution-chain
validation, deferred non-empty Evidence, linear predecessor locking and RLS boundary
checks through successful/negative command paths. WORKER, AGENT-curator, PROJECTOR, AUDIT WRITER, EXECUTOR and human
read principal receive no Phase-19 insert capability.

## 13. Regression and integrity evidence

| Gate | Result | Legitimate delta |
|---|---|---|
| Complete Phase 16 matrix | PASS | none |
| Complete Phase 17 matrix | PASS | none |
| Phase 19 PostgreSQL matrix | PASS | new 0017 foundation |
| Backend regression | **172 PASS / 0 FAIL / 0 SKIP** | +7 Phase-19 contract tests from 165 |
| Foundation-only | **74 PASS / 0 FAIL / 0 SKIP** | +7 from 67 |
| `manage.py check` | PASS, zero issues | none |
| `makemigrations --check --dry-run` | PASS, no changes | 0017 is complete |
| Python compilation | PASS | new module/migration/harness compile |
| scoped `git diff --check` | PASS | unrelated Sidebar whitespace untouched |

The legacy backend suite again attempted pre-existing Chroma/PostHog DNS telemetry;
it failed closed. The Phase-19 module and PostgreSQL gate made zero network/business
calls.

## 14. Hash integrity

Migrations 0001–0016 match their promoted SHA-256 values exactly:

`0d72f262…`, `1f538ca4…`, `dadfad2c…`, `04504327…`, `96ab33a1…`,
`033242bd…`, `c7f6a203…`, `285aecb3…`, `412c6459…`, `c4f37a9a…`,
`cdb23edc…`, `7f280e24…`, `06177fde…`, `ee0e42a7…`, `5e297591…`,
`e922ff20…`.

New migration 0017 SHA-256:
`580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38`.

The ten authoritative source hashes are 10/10 MATCH:

`8308bde9…`, `e0a59c91…`, `11c2b461…`, `952d8ac9…`, `ecaecd25…`,
`30e3c052…`, `de1b4899…`, `29ac5c2d…`, `c41e847e…`, `eb42315c…`.

Policy v1 SHA-256 remains
`3e2f2b5b3f335bcb425c4b3d8043c2b541de56b0a7b14fbc63b8f48e4392758f`.

## 15. Zero external effect and teardown

No deployment, production, staging, shared DEV/QA, AdminApps/MedSupplier mutation,
HTTP business action, shell/subprocess adapter, provider/tool invocation, broker,
notification or external QMS effect occurred. PostgreSQL was ephemeral only.
Finalizer evidence: database absent, all eleven run-scoped roles absent, container
absent, volume absent and temporary directory absent. Teardown also passed after
each failed development run.

## 16. Residual risks

1. This is a database/application foundation, not an API or operational review
   queue; production enablement remains prohibited.
2. AdminApps permission/MFA resolution is represented by a trusted server-side
   context contract; live AdminApps integration is intentionally outside this gate.
3. Policy v1 supports one MeasurementDefinition. Multi-definition assessment and
   independent system attestation require a later policy version.
4. The existing legacy test telemetry still attempts DNS outside Phase 19 and
   should be disabled separately for fully hermetic legacy regression.

There are **0 P0** and **0 P1** defects blocking the next approved gate.

## 17. Promotion verdict

**PHASE 19 — EFFECTIVENESSCHECK FOUNDATION IMPLEMENTATION: PROMOTED**

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| Migration 0017 | PASS | additive; empty-history forward/reverse/forward; SHA `580f16d1…` | forward-only after history |
| EffectivenessCheck | PASS | exact immutable execution/governance/target provenance | no API/production enablement |
| EffectivenessEvidence | PASS | finite 1..N exact revisions; hash/scope/duplicate controls | no silent truncation |
| Outcomes/timing | PASS | exact four values; uncertain reasons; due gate | preserve policy v1 |
| Human/AdminApps authority | PASS | trusted MFA/access/permissions; human only | integrate live authority only in later gate |
| MeasurementDefinition | PASS | conditional exact one-or-none | no MeasurementRecord |
| Supersession | PASS | v1 inconclusive -> v2 effective; one leaf | corrections remain append-only |
| Event/Outbox/Audit | PASS | one atomic set per revision | no raw Evidence/secrets |
| Atomicity | PASS | success + 9/9 rollback | retain failure injection |
| Protected history | PASS | execution/learning/normative digests unchanged | no auto-compensation/learning |
| RLS/raw SQL | PASS | ENABLE+FORCE; A/none/B; mutation denied | retain real-principal regression |
| Phase 16/17 | PASS | complete inherited PostgreSQL matrices | no second action |
| Backend/foundation | PASS | 172/172; 74/74 | +7 legitimate Phase-19 tests |
| Hashes | PASS | 16/16 migrations; 10/10 sources; policy unchanged | freeze 0017 after promotion |
| External effects/teardown | PASS | zero Phase-19 effects; all ephemeral resources absent | no deployment |

## NEXT_CODEX_PROMPT

Execute PHASE 20 — EFFECTIVENESS OPERATIONAL VALIDATION + GOVERNED LEARNING BOUNDARY DESIGN GATE in `/home/felipe/proyectos/isosmart` without deployment, production/staging/shared databases, external effects, a second controlled QMS action, automatic compensation, or automatic learning. Preserve migrations `0001–0017`, all ten authoritative source artifacts, `CONTROLLED_QMS_ACTION_POLICY_V1`, `EFFECTIVENESS_CHECK_POLICY_V1`, `CONTROLLED_EXECUTION_RUNBOOK_V1`, ADR-0007 through ADR-0011, and the exact `opportunity.defer_evaluation` / separately authorized compensation boundaries. Prove EffectivenessCheck safety under concurrent initial recording and corrections, duplicate/fork races, pool reuse, rollback and retained-history release handling; define overdue, `unknown` and `inconclusive` operational handling and tenant-safe reviewer queues without external workflow dependency; design how exact authorized/redacted Effectiveness provenance may become input to a future separately governed Learning Optimizer while explicitly forbidding automatic ModelPolicy, AgentDefinition, prompt, rule bundle, confidence, Knowledge Layer, training-data or execution changes. Re-run complete Phase 16, Phase 17 and Phase 19 PostgreSQL 18.6 matrices, full backend/foundation regressions, Django integrity, frozen hashes, zero-external-effect proof and mandatory teardown; fail closed on any provenance, authority, RLS, concurrency, immutability, compensation or learning-boundary regression.
