# Governed Learning Foundation Implementation Authorization v1

- Authorization ID: `governed-learning-implementation-authorization/v1`
- Version: v1
- Date: 2026-08-24
- Owner/system authority: ISO Smart Product Governance
- Related Product Policy: `governed-learning-policy/v1`
- Related gate: `PHASE 20 — EFFECTIVENESS OPERATIONAL VALIDATION + GOVERNED LEARNING BOUNDARY DESIGN GATE`
- Decision: **APPROVED FOR PHASE 21 FOUNDATION IMPLEMENTATION**
- Nature: implementation authorization; non-normative; no runtime enablement

> This authorization does not amend, replace or retroactively broaden
> `GOVERNED_LEARNING_POLICY_V1.md`. That policy remains historically accurate:
> it designed the boundary and itself authorized no table, migration or event.

## 1. Authorization decision

ISO Smart Product Governance authorizes only an inert, tenant-isolated governed
learning foundation. Phase 20 sufficiently specifies the provenance, authority,
correction, uncertainty, tenant, global-target, normative and non-application
boundaries needed to implement the records and controls listed below.

This decision authorizes implementation, not use in production, proposal
approval or application, target mutation, automatic learning or an external
effect. Any ambiguity is resolved fail-closed in favor of no write and no target
effect.

## 2. Exact authorized scope

Phase 21 may implement only:

1. `LearningSignal` as an immutable governed input record;
2. exact `LearningSignalEffectiveness` links to authorized current
   `EffectivenessCheck` leaves and their reconstructible correction lineages;
3. `LearningProposal` as an explainable, non-executing, governance-pending
   proposal;
4. exact, minimized provenance for signals and proposals;
5. a trusted learning-governance authority context and attributable authority
   decision provenance, separate from effectiveness-review authority;
6. tenant and Organization isolation, with no cross-tenant aggregation;
7. correction-aware sampling that defaults to one current leaf per
   EffectivenessCheck lineage;
8. append-only proposal records and versioned/superseding proposal history;
9. only `learning_signal.created` schema v1 and
   `learning_proposal.created` schema v1 typed `DomainEvent` contracts;
10. one `TransactionalOutbox` record and one `ImmutableAuditLog` append for
    each successfully committed foundation command;
11. PostgreSQL constraints, composite tenant/Organization relations, least-
    privilege grants, tenant-context protections and `ENABLE` + `FORCE ROW
    LEVEL SECURITY`; and
12. additive migration `0018+` only as required for this exact foundation.

Phase 21 may represent an allow-listed target taxonomy, current target version
identifier/hash and tenant/global scope as proposal provenance. It may not write,
publish, supersede or create a version of any target artifact.

## 3. LearningSignal boundary

A `LearningSignal` is an immutable, governed, tenant- and Organization-scoped
input record derived under an explicitly versioned derivation rule from exact
authorized/redacted evidence. It preserves the selected Effectiveness leaf,
lineage and applicable execution, receipt, plan, authorization, recommendation,
agent, model-policy, evidence, normative-reference, trace and policy provenance
without copying raw Evidence bodies, prompts, secrets or tokens.

It is not an optimizer result, score, penalty, label, model update, policy
update, approval or autonomous feedback instruction. Creation of a signal has no
effect on a target or runtime behavior.

## 4. LearningProposal boundary

A `LearningProposal` is explainable, immutable, non-executing and governance-
pending. It identifies exact supporting signals/samples, target taxonomy and
scope, bound current target version/hash, proposed change representation,
rationale, expected effect, risks, provenance, proposer and required governance
domains.

Persisting, versioning or superseding a proposal must not apply its proposed
change, create a target version, alter a target, increase autonomy or emit an
application/approval event. No Phase 21 service, function, trigger, task or
principal may possess a target-application path.

## 5. Tenant and global-target boundary

- Tenant-derived signals remain under the same tenant and Organization as their
  authoritative Effectiveness provenance.
- Tenant A records cannot be selected, linked, aggregated, read or used by
  Tenant B.
- There is no automatic or implicit promotion to global learning.
- A tenant-scoped proposal may reference an allow-listed global target only as
  non-executing provenance. It cannot create, edit, publish or supersede that
  global target.
- Cross-tenant aggregation, anonymized cross-tenant learning and global
  proposal application require a later Product Policy version, privacy/security
  review and separate implementation authorization.

## 6. Authority and AdminApps requirements

Effectiveness-review authority is not learning-governance authority. Phase 21
must accept only server-resolved trusted authority contexts, preserve the
authority decision reference and context version, and reject body/query/header,
agent, optimizer or `UserProjection` claims as authority.

AdminApps remains the system of record for identity, global roles, MFA, product
access and active tenant access. ISO Smart must not create a competing identity
or local RBAC authority. The foundation may implement a typed trusted-context
boundary and synthetic test resolver; it does not authorize a live AdminApps
integration, API or production fallback. Missing, stale, revoked, mismatched or
unverifiable authority fails closed before database mutation.

The signal derivation command must be an allow-listed server-side governance
capability, never an agent or optimizer self-assertion. Proposal creation
requires an attributable human/governance proposer context distinct from the
QMS Effectiveness reviewer context. Proposal approval and application authority
are outside Phase 21 and must not be modeled as an executable capability.

## 7. Correction-aware and uncertainty semantics

The default final sample is the current `EffectivenessCheck` leaf at signal
derivation time. Its exact leaf ID and full correction lineage are frozen.
Superseded records remain reconstructible for explicit correction-history
analysis but may not be silently counted as independent final samples. Database
and service controls must reject duplicate final-sample use within the same
governed derivation/proposal context.

`unknown` and `inconclusive` remain distinct categorical outcomes. Neither is a
negative example, penalty, failure label, score or numeric zero by default.
Phase 21 implements no numeric aggregation or outcome-to-weight mapping.

## 8. Normative and target safety

No learning command may create, edit, supersede, reinterpret or derive
certifiability for `Standard`, `StandardEdition`, `Clause`,
`RequirementControl` or any certifiable normative content.
`KnowledgeLayerRule` remains separately governed global curation and is not a
learning write target. The same no-write boundary applies to prompt/rule
artifacts, `ModelPolicy`, `AgentDefinition`, Recommendation logic, retrieval
strategy and autonomy configuration.

## 9. Event, migration, database and atomicity authorization

Only these new event contracts are authorized in Phase 21:

- `learning_signal.created`, schema version 1;
- `learning_proposal.created`, schema version 1.

The event payloads contain bounded identifiers, hashes, scope, authority and
provenance, not raw Evidence, prompt bodies, secrets or tokens. Phase 21 must not
implement `learning_proposal.applied`, `learning_proposal.approved`,
`model.updated`, `policy.updated`, `autonomy.changed` or an equivalent event.

Migration `0018+` is authorized only for the exact foundation in section 2. It
does not authorize any learning target mutation, target version creation,
runtime enablement or application workflow. Migrations `0001`–`0017` remain
byte-for-byte frozen.

Each command is one PostgreSQL transaction:

```text
LearningSignal + exact Effectiveness links + DomainEvent + Outbox + Audit

LearningProposal + exact signal/provenance links + DomainEvent + Outbox + Audit
```

Any failure rolls back the complete unit. There is no target-application
transaction. Tenant tables require direct tenant scope, composite relational
defenses, immutable tenant/Organization fields, least-privilege principals,
append-only/history protections, default-deny RLS, and catalog proof of both
`ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`.

## 10. Strict prohibited scope

This authorization does not permit:

- prompt, rule artifact, `ModelPolicy`, `AgentDefinition`,
  `KnowledgeLayerRule`, Recommendation logic or retrieval modification;
- autonomy changes or escalation;
- normative content or certifiability changes;
- cross-tenant learning, aggregation or influence;
- proposal approval or application;
- automatic learning, scoring, optimization or target version creation;
- direct or automatic Effectiveness-to-target mutation;
- a second QMS action, compensation or automatic downstream workflow;
- API, deployment, production/staging/shared database, live AdminApps write,
  provider/tool invocation, notification or other external effect.

## 11. Phase 21 acceptance conditions

All conditions are mandatory:

- [ ] `LearningSignal` is immutable and inert.
- [ ] Exact Effectiveness provenance and full lineage are reconstructible.
- [ ] Current-leaf selection and duplicate/superseded-sample defenses pass.
- [ ] `LearningProposal` is explainable, append-only/versioned and non-executing.
- [ ] Learning-governance authority is separate and trusted.
- [ ] AdminApps authority and fail-closed access/MFA boundary are preserved.
- [ ] Tenant and Organization isolation pass at service, constraint and RLS layers.
- [ ] No cross-tenant learning or automatic global promotion exists.
- [ ] No automatic or direct target mutation exists.
- [ ] No prompt, model, policy, Recommendation or retrieval change exists.
- [ ] No autonomy or normative change exists.
- [ ] Only the two authorized schema-v1 created events exist.
- [ ] Signal/proposal, links, event, outbox and audit commit atomically.
- [ ] Protected tables prove `ENABLE` + `FORCE RLS`, default deny, no owner/
      superuser/`BYPASSRLS` runtime and least privilege with real principals.
- [ ] Unknown and inconclusive remain distinct and unscored.
- [ ] Migrations `0001`–`0017` and all frozen governance/source artifacts match.
- [ ] No API, external effect, deployment, persistent/shared database or second
      QMS action is introduced.
- [ ] PostgreSQL 18.6 isolated tests, rollback/retention/concurrency/security
      matrices, inherited regressions and mandatory teardown pass with zero
      P0/P1 blockers.

## 12. Revocation and change control

This authorization is immutable once referenced. Withdrawal or correction uses
a successor authorization and preserves this decision. Any proposal approval or
application, new event, scoring, optimizer, new target type, target mutation,
cross-tenant/global learning, authority expansion, assessor automation, API,
deployment or external effect requires a later Product Policy version and a
separate governance, privacy/security and implementation gate.

Failure of any acceptance condition revokes promotion eligibility and requires
Phase 21 to stop fail-closed without applying a proposal or changing a target.
