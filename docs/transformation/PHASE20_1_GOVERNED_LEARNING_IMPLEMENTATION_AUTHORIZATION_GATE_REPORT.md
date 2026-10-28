# Phase 20.1 — Governed Learning Implementation Authorization Gate

**Date:** 2026-08-24

**Nature:** governance approval gate only; documentation-only

**Authorization:** `governed-learning-implementation-authorization/v1`

**Authorization status:** **APPROVED FOR PHASE 21 FOUNDATION IMPLEMENTATION**

**Verdict:** **PROMOTED**

## 1. Original blocker and historical truth

Phase 20 was PROMOTED, but the attempted Phase 21 execution was correctly
blocked and not promoted. `governed-learning-policy/v1` had status **APPROVED
FOR DESIGN/IMPLEMENTATION GATE** and explicitly stated that it authorized no
table, migration, event, optimizer, training job, proposal application or
external effect. Phase 20 additionally required Product Policy approval before
Phase 21 implementation.

This gate does not edit that policy or reinterpret its former status. It closes
the blocker through the separate
`GOVERNED_LEARNING_IMPLEMENTATION_AUTHORIZATION_V1.md` authorization artifact.

## 2. Current Product Policy status and constraints

The exact inspected Product Policy remains:

| Item | Exact current state |
|---|---|
| Policy ID/version | `governed-learning-policy/v1`, v1 |
| Status | **APPROVED FOR DESIGN/IMPLEMENTATION GATE** |
| Allowed scope | design of the EffectivenessCheck revision -> LearningSignal -> LearningProposal -> separate review -> approved new target version boundary |
| Prohibited by the policy itself | table, migration, event, optimizer, training job, proposal application and external effect |
| Preconditions for implementation | later Product Policy approval; separate authority; versioned target changes; tenant/global, security and implementation gates |
| Governance constraints | no self-modification, no direct mutation, no automatic autonomy/normative/cross-tenant learning, no proposal self-application, exact provenance and human/governance separation |

The policy is sufficiently specified and risk-bounded for the inert foundation
only because the new authorization fixes the exact implementation scope and
retains every policy prohibition on proposal application and target mutation.

## 3. Policy invariant review

Phase 20 invariants remain unchanged:

- no automatic self-modification or policy self-edit;
- no direct Effectiveness-to-target mutation;
- no automatic autonomy escalation;
- no normative automatic edit or reinterpretation;
- no cross-tenant learning by default;
- `LearningSignal` is governed evidence, not a score or update;
- `LearningProposal` is explainable, non-executing and governance-pending;
- learning-governance authority is separate from effectiveness-review authority;
- future target changes are versioned and separately approved; and
- no automatic proposal application.

The governed chain remains a separation-of-duties model, not a runtime feedback
loop.

## 4. Implementation authorization analysis

The narrow authorization question is answered **yes**. Phase 20 plus the new
authorization bounds Phase 21 to records, provenance, trusted authority context,
isolation, history, two typed created events, atomic outbox/audit and RLS. It
does not authorize any consumer or command capable of applying a proposal.

The foundation can be tested without inventing local RBAC: Phase 21 may
materialize a typed trusted authority context and synthetic test resolver while
AdminApps remains authoritative. A live permission integration, API and
production enablement remain prohibited. Missing or unverifiable authority must
fail before mutation.

No successor ADR is created. This gate grants Product Policy implementation
authority without changing the architecture or rewriting ADR-0011; the separate
versioned authorization and this report preserve the repository's governance
history.

## 5. Exact authorized scope

Only the following foundation is authorized:

1. immutable tenant/Organization-scoped `LearningSignal`;
2. exact `LearningSignalEffectiveness` links;
3. explainable, non-executing `LearningProposal`;
4. minimized exact provenance;
5. separate trusted learning-governance authority context and decision
   provenance;
6. tenant isolation and no cross-tenant aggregation;
7. correction-aware current-leaf sampling;
8. append-only/versioned proposal history;
9. `learning_signal.created` v1 and `learning_proposal.created` v1 only;
10. `TransactionalOutbox` and `ImmutableAuditLog` atomicity;
11. PostgreSQL constraints, least privilege and `ENABLE` + `FORCE RLS`; and
12. additive migration `0018+` only for these objects and controls.

Target taxonomy, scope and exact current version/hash may be stored only as
proposal provenance. No target write is authorized.

## 6. Exact prohibited scope

Phase 21 must not implement prompt/rule, `ModelPolicy`, `AgentDefinition`,
`KnowledgeLayerRule`, Recommendation logic, retrieval or autonomy changes;
normative content changes; cross-tenant learning; proposal approval/application;
automatic learning/scoring/optimization; automatic target version creation;
direct Effectiveness mutation; a second QMS action or compensation; API,
deployment, production/staging/shared DB, live external integration or any
external effect.

It must not emit `learning_proposal.applied`, `learning_proposal.approved`,
`model.updated`, `policy.updated`, `autonomy.changed` or an equivalent event.

## 7. Signal, proposal, tenant and global boundaries

`LearningSignal` is authorized only as an immutable governed input record. It
is not an optimizer result, score, label, model/policy update, approval or
autonomous instruction. It freezes the authorized/redacted provenance of the
selected current Effectiveness leaf without copying raw Evidence, prompt bodies,
secrets or tokens.

`LearningProposal` is authorized only as an explainable, non-executing,
governance-pending record. Persisting or superseding it cannot apply the change,
create a target version or alter runtime behavior.

Tenant-derived signals and proposals remain tenant/Organization-scoped. Tenant
A cannot influence Tenant B. A tenant proposal that references a global target
remains an inert reference and cannot mutate, publish or supersede that target.
Cross-tenant aggregation and global application require later policy and gates.

## 8. Authority and AdminApps boundary

Effectiveness-review authority does not imply signal derivation, proposal
creation, proposal approval or target-application authority. Phase 21 requires a
server-resolved trusted learning-governance context and attributable decision
reference; client fields, agents, optimizers and `UserProjection` existence
grant nothing.

AdminApps remains authoritative for identity, global roles, MFA, product access
and active tenant access. ISO Smart does not create competing local RBAC. The
Phase 21 foundation may test a typed trusted context synthetically, but it may
not expose an API, connect a live AdminApps write path or enable a production
fallback. Proposal approval/application authority is not implemented.

## 9. Correction-aware and uncertainty semantics

Default final learning input uses one current `EffectivenessCheck` leaf per
lineage at derivation time. The exact leaf and full correction lineage are
frozen. Superseded revisions remain reconstructible, but are included only for
explicit correction-history analysis and cannot be silently double-counted as
independent final outcomes.

`unknown` remains an evidenced inability to assess; `inconclusive` remains a
completed assessment without a reliable binary conclusion. Neither becomes a
negative sample, failure label, penalty, zero or numeric weight by default.
Numeric aggregation is outside Phase 21.

## 10. Normative safety

No learning command may create, edit, supersede or reinterpret `Standard`,
`StandardEdition`, `Clause`, `RequirementControl` or certifiable normative
content, or change certifiability/coverage. `KnowledgeLayerRule` remains
separately governed global curation and is read-only to this foundation.

## 11. Event, migration and atomicity authorization

The only authorized events are `learning_signal.created` schema v1 and
`learning_proposal.created` schema v1. They carry bounded identifiers, hashes,
scope, authority and provenance; no raw Evidence, prompt, secret or token.

Migration `0018+` is authorized only for the approved inert foundation. It does
not authorize target mutation, target version creation, an application workflow
or runtime enablement. Migrations `0001`–`0017` are frozen.

Authorized atomic commands are exactly:

```text
LearningSignal + exact Effectiveness links + DomainEvent + Outbox + Audit
LearningProposal + exact signal/provenance links + DomainEvent + Outbox + Audit
```

There is no target-application transaction. Any failure rolls back the entire
foundation command.

## 12. Threat review

| Risk | Required implementation control | Residual risk after control | Mandatory Phase 21 test |
|---|---|---|---|
| Cross-tenant learning | direct tenant/Organization scope, composite FKs, server-derived context, default-deny ENABLE+FORCE RLS, no aggregation path | Low; privileged DB administration remains governed separately | A/B/none SELECT and write matrix, forged tenant, cross-Organization links, raw SQL, pool reuse |
| Poisoned Effectiveness evidence | exact leaf/evidence hashes and trust metadata, allow-listed derivation rule/version, immutable provenance, no raw copied content | Medium; legitimate-but-misleading evidence still needs human governance review | hash/trust mismatch, inaccessible evidence, stale leaf and tampered provenance rollback |
| Proposal spoofing | trusted human/governance context, proposer and authority-decision provenance, target-version binding, no client authority | Low/Medium; upstream authority compromise remains | forged actor/role/tenant/decision, revoked/stale authority, mismatched target version |
| Authority confusion | separate typed contexts; Effectiveness permission and UserProjection never grant learning governance; no local RBAC | Low | Effectiveness reviewer-only, agent, worker and bare UserProjection all denied before mutation |
| Target privilege escalation | no target DML/grants/service import/application function; allow-listed taxonomy is provenance only | Low | protected target byte-state/count/grant checks across successful signal/proposal commands |
| Automatic self-modification | inert create commands only; no optimizer/application consumer or self-approval event | Low | dependency/import scan, event allow-list and protected target state invariant |
| Autonomy escalation | autonomy is read-only provenance; no A3/A4 update event/path/grant | Low | autonomy/model-policy state unchanged and prohibited event names absent |
| Normative contamination | normative objects read-only/referenced only; no derived certifiability semantics | Low | Standard/Edition/Clause/RequirementControl/KnowledgeLayerRule state and grants unchanged |
| Global-target mutation | tenant proposal may only bind global target ID/version/hash; zero global target write privilege | Low/Medium; future curator compromise is outside this command | tenant proposal referencing global target commits while global target bytes/counts remain identical |
| Duplicate/superseded sample counting | current-leaf resolver, frozen lineage, uniqueness/idempotency and explicit history-analysis mode | Low | v1->vN correction chain, stale leaf rejection, duplicate link rejection, concurrent derivation |

No listed residual risk authorizes target application. Any failed threat control
is a Phase 21 promotion blocker.

## 13. Phase 21 acceptance gates

- [ ] `LearningSignal` immutable and inert.
- [ ] Exact Effectiveness provenance.
- [ ] Correction-aware current-leaf semantics.
- [ ] `LearningProposal` non-executing.
- [ ] Separate trusted governance authority.
- [ ] AdminApps authority preserved.
- [ ] Tenant and Organization isolation.
- [ ] No cross-tenant learning.
- [ ] No automatic/direct target mutation.
- [ ] No prompt/model/policy/Recommendation/retrieval changes.
- [ ] No autonomy change.
- [ ] No normative change.
- [ ] Append-only/versioned history.
- [ ] Only the two authorized typed events.
- [ ] Event/Outbox/Audit atomicity and forced-failure rollback.
- [ ] `ENABLE` + `FORCE RLS`, no owner/superuser/`BYPASSRLS` runtime.
- [ ] Unknown/inconclusive distinction preserved and unscored.
- [ ] No external effect, API, deployment or shared database.
- [ ] No second QMS action or compensation.
- [ ] Frozen migration/source/governance hashes and inherited regressions pass.
- [ ] Isolated PostgreSQL 18.6 resources are completely torn down.

## 14. Governance artifact

Created:
`docs/governance/GOVERNED_LEARNING_IMPLEMENTATION_AUTHORIZATION_V1.md`.

It records the authorization ID/version/date, related Product Policy and Phase
20 gate, approval decision, exact authorized and prohibited scopes, signal and
proposal meanings, tenant/global and authority boundaries, AdminApps ownership,
event/migration/atomicity/RLS authorization, acceptance conditions and
successor-only change control. The original Product Policy was not edited.
Its final SHA-256 is
`04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c`.

## 15. Migration and source integrity

Current SHA-256 verification matches the promoted values for all 17 foundation
migrations:

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
| 0015 | `5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3` | MATCH |
| 0016 | `e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5` | MATCH |
| 0017 | `580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38` | MATCH |

Migration `0018` is absent.

The authoritative source package is **10/10 MATCH** against
`SOURCE_ARTIFACT_MANIFEST.md`:

| Source | SHA-256 | Result |
|---|---|---|
| Integrated specification DOCX | `8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c` | MATCH |
| Lucidchart Draw.io | `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa` | MATCH |
| Mermaid architecture | `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3` | MATCH |
| Architecture workbook | `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5` | MATCH |
| Network nodes CSV | `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3` | MATCH |
| Network edges CSV | `30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6` | MATCH |
| PostgreSQL DDL | `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e` | MATCH |
| OpenAPI | `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8` | MATCH |
| Master data JSON | `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb` | MATCH |
| Import README | `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db` | MATCH |

Frozen governance hashes recorded before and verified after this gate include
`GOVERNED_LEARNING_POLICY_V1.md`
`7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec`,
`EFFECTIVENESS_CHECK_POLICY_V1.md`
`3e2f2b5b3f335bcb425c4b3d8043c2b541de56b0a7b14fbc63b8f48e4392758f`,
and the Phase 20 report
`f0e1465fa790b5d4be70f1798120bae9fb7644cdbdf344006c64ff2563cd0d79`.

## 16. No-runtime-change evidence

This gate created only two Markdown documents: the authorization and this
report. It did not modify models, services, migrations, tests, runtime grants,
events, APIs or settings. No database was opened or created; no migration was
run; no production/staging/shared resource, AdminApps, MedSupplier, provider,
notification, deployment or external system was touched.

The initial worktree contained unrelated local modifications and untracked
foundation/documentation work. They were preserved and not normalized. Final
verification is limited to the authorized document paths plus direct hashes of
the frozen artifacts, rather than claiming the unrelated worktree is clean.
Repository-wide `git diff --check` continues to report only the pre-existing
trailing whitespace at `frontend/src/components/Layout/Sidebar.jsx:28`; this
gate did not edit that file. Separate diff checks of both new documents report
no whitespace errors.

## 17. Residual blockers

There are zero governance blockers for implementing the Phase 21 inert
foundation under this authorization and zero P0/P1 defects identified by this
gate.

The following remain explicit blockers for any broader or live capability:

1. proposal approval/application and target version creation require a later
   Product Policy and implementation gate;
2. cross-tenant/global learning requires separate privacy/security and global
   governance approval;
3. exact live AdminApps permission integration and production authorization are
   not approved here;
4. API, deployment and production/staging/shared database use remain prohibited;
5. numeric scoring/aggregation, optimizer behavior and new events remain
   unapproved.

These are out-of-scope boundaries, not blockers to the authorized foundation.

## 18. Promotion verdict

**PHASE 20.1 — GOVERNED LEARNING IMPLEMENTATION AUTHORIZATION GATE: PROMOTED**

## NEXT_CODEX_PROMPT

Execute **PHASE 21 — GOVERNED LEARNING SIGNAL + LEARNING PROPOSAL FOUNDATION
IMPLEMENTATION** exclusively in `/home/felipe/proyectos/isosmart`, with
`governed-learning-implementation-authorization/v1` as a mandatory blocking
prerequisite. Read `AGENTS.md`, the authorization, the unchanged
`governed-learning-policy/v1`, Phase 20 and Phase 20.1 reports, Phase 19,
`effectiveness-check-policy/v1`, applicable ADRs, data architecture, threat
model, RLS, eventing and immutable audit before changes; run `git status` and
preserve all unrelated local work.

Implement only an inert, tenant/Organization-isolated foundation: immutable
`LearningSignal`; exact `LearningSignalEffectiveness` links to the authorized
current `EffectivenessCheck` leaf with reconstructible full correction lineage;
explainable, non-executing, governance-pending `LearningProposal`; minimized
exact provenance; a typed trusted learning-governance authority context separate
from Effectiveness reviewer authority; correction-aware sampling; append-only/
versioned proposal history; `learning_signal.created` schema v1 and
`learning_proposal.created` schema v1 only; and atomic `DomainEvent` +
`TransactionalOutbox` + `ImmutableAuditLog`. Use additive migration `0018+` only
for this foundation, direct tenant scope, composite tenant/Organization
constraints, immutable scope fields, least-privilege principals, default-deny
PostgreSQL RLS, and catalog-proven `ENABLE ROW LEVEL SECURITY` plus `FORCE ROW
LEVEL SECURITY`.

`LearningSignal` must remain an immutable governed input record, never a score,
penalty, optimizer result, label, model/policy update, approval or autonomous
instruction. `LearningProposal` must remain immutable/versioned, explainable,
non-executing and governance-pending; persisting or superseding it must never
apply the proposed change or create a target version. Target taxonomy, scope and
current version/hash may be stored only as inert provenance. A tenant proposal
may reference a global target but cannot write, publish or supersede it.

Preserve AdminApps as authority for identity, global roles, MFA, product access
and tenant access. Do not invent local RBAC. Accept only server-resolved trusted
authority contexts and preserve decision provenance; client fields, agents,
optimizers and UserProjection existence grant no authority. Synthetic trusted
contexts may be used only in tests. Missing/stale/revoked/mismatched authority
must fail before mutation. Proposal approval and application authority must not
be implemented.

Default sampling must use exactly one current Effectiveness leaf per lineage at
derivation time, freeze that leaf and its full correction lineage, reject stale
or duplicate final-sample use, and keep superseded revisions only for explicit
correction-history analysis. Preserve `unknown` and `inconclusive` as distinct
categorical outcomes; neither may become a negative sample, penalty, zero or
numeric weight. Implement no numeric aggregation.

Strictly do not modify prompts/rules, `ModelPolicy`, `AgentDefinition`,
`KnowledgeLayerRule`, Recommendation logic, retrieval, autonomy, `Standard`,
`StandardEdition`, `Clause`, `RequirementControl`, certifiable normative content
or any target artifact. Do not implement proposal approval/application,
automatic learning, optimization, automatic target version creation,
cross-tenant aggregation/influence, global promotion, a second QMS action,
compensation, API, deployment, live AdminApps writes, providers, notifications,
production/staging/shared databases or any external effect. Do not implement
`learning_proposal.applied`, `learning_proposal.approved`, `model.updated`,
`policy.updated`, `autonomy.changed` or an equivalent event.

Prove two atomic commands and complete rollback at every failure point:
`LearningSignal + exact Effectiveness links + created event + outbox + audit`,
and `LearningProposal + exact signal/provenance links + created event + outbox +
audit`. There is no target-application transaction. Test immutability,
append-only supersession/version history, idempotency, concurrency, stale-leaf
selection, correction chains, duplicate/superseded sample rejection, authority
confusion/spoofing/revocation, target-version mismatch, redaction/minimization,
protected target byte-state invariance, event allow-listing, forced-failure
rollback, raw SQL, grants, tenant/Organization A/B/none isolation, forged tenant,
pool/rollback context cleanup and real-principal catalog properties.

Validate on an official isolated ephemeral PostgreSQL 18.6 lifecycle with safe
predeclared teardown. Re-run the complete applicable Phase 16, 17, 19 and 20
PostgreSQL/security/regression matrices, full backend and foundation tests,
Django checks, migration drift, compilation, `git diff --check`, all 17 frozen
migration hashes, all ten source hashes and frozen policy/ADR/report hashes.
Migration `0018` must be the only justified new migration and must explicitly
state that it grants no target mutation. Record zero external business effects
and prove database, roles, container, volume and temporary resources absent at
teardown, including on failure.

Create the Phase 21 implementation report with exact schema/contracts,
authority and tenant/global boundaries, threat-control test results, atomicity
matrix, RLS/least-privilege catalog evidence, migration/source/governance hashes,
protected-target invariance, regression counts, no-external-effect evidence,
teardown and residual risks. Emit PROMOTED only if every authorization acceptance
condition passes with zero P0/P1 blockers; otherwise stop fail-closed, preserve
all history and emit NOT PROMOTED without applying a proposal or changing a
target.

| Governance item | State | Evidence | Risk/next action |
|---|---|---|---|
| Original policy history | PRESERVED | unchanged policy status and hash | keep immutable |
| Implementation authorization | APPROVED | separate authorization v1 | Phase 21 prerequisite |
| Signal/proposal boundary | APPROVED, INERT ONLY | exact sections 3–4 authorization | no application path |
| Tenant/global safety | APPROVED, DEFAULT-DENY | no cross-tenant; global reference only | later policy for broader scope |
| Authority/AdminApps | APPROVED, SEPARATED | trusted context; AdminApps remains authority | live integration still prohibited |
| Event/migration | NARROWLY APPROVED | two created events; 0018+ foundation only | no applied/updated events |
| Atomicity/RLS/audit | REQUIRED | acceptance gates and threat matrix | prove on PostgreSQL 18.6 in Phase 21 |
| Migrations 0001–0017 | 17/17 MATCH | exact SHA-256 table | remain frozen |
| Authoritative sources | 10/10 MATCH | manifest SHA-256 table | remain frozen |
| Runtime/external effects | ZERO | documentation-only gate | no deployment |
| Residual Phase 21 governance blockers | ZERO | all narrow conditions specified | implementation must pass every gate |
| Phase 20.1 | PROMOTED | authorization + report | proceed only to authorized Phase 21 foundation |
