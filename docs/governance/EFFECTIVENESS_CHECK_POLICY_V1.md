# ISO Smart Effectiveness Check Product Policy v1

**Version:** v1

**Status:** APPROVED FOR IMPLEMENTATION GATE

**Date:** 2026-08-24

**Owner/system authority:** ISO Smart Product Governance

**Policy identity:** `effectiveness-check-policy/v1`

> **THIS POLICY DEFINES ISO SMART APPLICATION GOVERNANCE.**
>
> **IT IS NOT AN ISO REQUIREMENT AND DOES NOT DEFINE, MODIFY, INTERPRET OR
> ADD A CERTIFIABLE ISO REQUIREMENT.**

This artifact is an ISO Smart-owned, non-normative Product Policy. Source facts
are identified as such; every closed choice not fixed by the authoritative
source package is a Product Policy decision. This policy never creates or
alters `RequirementControl`, `StandardEdition`, `KnowledgeLayerRule`, normative
coverage, certifiability counts or a compliance conclusion.

## 1. Scope and invariant

Version 1 governs only the future effectiveness assessment of the currently
controlled forward action:

```text
opportunity.defer_evaluation
Opportunity
under_evaluation -> deferred
```

It does not govern another QMS action, broaden the forward action or broaden
the separately governed compensation `opportunity.resume_evaluation`.

Source fact: the source package names `EffectivenessCheck`, places
effectiveness after execution, associates it with `method`, `due_at`, `result`
and Evidence, and requires results/effectiveness to be evaluated. Product
Policy fixes the safe application contract below because the sources do not.

```text
ActionExecution = record that an authorized action was executed.
EffectivenessCheck = separate governed assessment of whether that executed
action achieved its approved business objective over the planned observation
context.
```

Execution success is not effectiveness. Execution failure is not
ineffectiveness. Compensation is not ineffectiveness. Reconciliation
`COMMITTED` is not effectiveness. A check never updates or reinterprets
`ActionExecution`, `ActionExecutionReceipt`, `ExecutionAuthorization`,
`ActionPlan`, `Approval`, `AgentDecision`, `Recommendation`,
`RecommendationBasis`, `AgentRun` or `AgentRunInput`.

## 2. Effectiveness intent and criteria

`controlled-qms-action-policy/v1` defines `deferred` as temporarily removing an
Opportunity from active internal evaluation without accepting or rejecting it,
changing hypothesis/benefit/feasibility, communicating externally or changing
another QMS object. Product Policy therefore defines the assessable business
objective as:

> During the approved observation interval, the exact Opportunity lineage was
> kept out of active internal evaluation for the approved governance purpose,
> and no evaluation decision or unauthorized downstream action defeated that
> purpose.

The observation interval starts at the exact resulting deferred revision's
creation/commit time and ends at `due_at`. A v1 assessment plan must freeze:

1. the governance purpose for the deferral;
2. the interval and exact `due_at`;
3. objective criteria that can establish whether active evaluation advanced,
   an evaluation decision occurred, or an unauthorized downstream action
   defeated the purpose;
4. the evidence classes expected for every criterion;
5. whether a MeasurementDefinition is used and its exact revision; and
6. the authorized human reviewer role category.

The status change itself is execution evidence, not a sufficient effectiveness
criterion. Recommendation confidence has no direct or threshold mapping to an
effectiveness outcome. Vague criteria such as “worked as intended” are invalid.

## 3. Closed outcome taxonomy

Exactly one outcome is required on every recorded check:

| Outcome | Exact meaning |
|---|---|
| `effective` | The assessment was performed after the observation interval and every mandatory criterion is supported by valid exact Evidence; no mandatory criterion is disproved. |
| `ineffective` | The assessment was performed after the observation interval and valid exact Evidence disproves at least one mandatory business-objective criterion. |
| `inconclusive` | The assessment was performed, but valid Evidence is insufficient, conflicting or too ambiguous to support a reliable positive or negative conclusion. |
| `unknown` | A reliable assessment could not be performed because required Evidence was unavailable, inaccessible or invalid, or another recorded blocking condition prevented evaluation. |

`unknown` means evaluation could not be completed. `inconclusive` means an
evaluation was completed but did not yield a reliable binary conclusion. Each
`unknown` or `inconclusive` check requires a bounded reason code plus human
explanation. Neither is treated as effective or ineffective.

No outcome automatically compensates, resumes the Opportunity, changes an
ActionPlan or ModelPolicy, creates a Recommendation, retrains/tunes a model,
changes Knowledge Layers or executes any action. Any response requires a new,
separately planned, approved, authorized, evented and audited workflow.

## 4. Actor and authority

Only an authenticated human in the role category **QMS authorized reviewer**
may attest and create a v1 EffectivenessCheck. The exact server-side authority
decision must include AdminApps-resolved permission
`qms.effectiveness_check.record` for the active tenant and exact Organization;
a correction additionally requires `qms.effectiveness_check.supersede`.
Authority also requires the applicable AdminApps MFA/access context and active
tenant access at record time. `UserProjection` existence, client claims, body
fields, arbitrary headers or an agent assertion never grant authority.

ISO Smart records actor external identity provenance, actor type `human`,
authority context/version, assessment source and trace. AdminApps remains the
system of record for identity, global roles, MFA and access authority; ISO Smart
does not create competing RBAC authority.

System and measurement-derived processes may prepare evidence and a proposed
assessment source, but may not independently attest or create a v1 check:

- `system_assisted`: objective rule output may be attached as Evidence; the
  human reviewer evaluates and attests it.
- `measurement_derived`: an exact MeasurementDefinition and resulting Evidence
  may support criteria; the human reviewer evaluates and attests them.
- execution success, receipt existence or `COMMITTED` reconciliation is never a
  system effectiveness assessor.

Independent system assessment requires a future policy version and a separate
authority/security gate.

## 5. Timing and `due_at`

For v1, `due_at` is the exact UTC instant at which the planned observation
interval ends and the assessment becomes due because Evidence is expected to
be mature. It is not a retention time, execution deadline or arbitrary global
window.

`due_at` must be explicitly supplied through trusted governed effectiveness
planning context and approved by the QMS authorized reviewer before recording
the check. The server must bind it to the exact ActionExecution, tenant,
Organization, target lineage and policy version. It must be strictly later than
the resulting deferred revision's commit time. A client-supplied timestamp that
is not identical to that trusted frozen context is rejected.

`effective`, `ineffective` and `inconclusive` may not be recorded before
`due_at`. An early inability to evaluate is not a completed check; the plan
remains pending. A later `unknown` may record that the due assessment could not
be performed and why. There is no 7/30/90-day default. A changed date requires
a newly governed planning decision; it does not silently edit history.

## 6. Evidence cardinality and validation

Every check references a finite non-empty set of exact immutable Evidence
revisions: minimum **1**, no semantic numeric maximum. Implementations may
impose a documented transport/page safety limit, but must support adding the
remaining exact references atomically or reject the whole command; they may not
silently truncate evidence.

Rules:

1. Every reference identifies the exact Evidence revision ID, logical lineage,
   revision number and committed content/provenance hash. `latest`, `current`
   and mutable pointers are forbidden.
2. The same exact revision may occur only once in a check.
3. Multiple revisions of the same Evidence lineage are allowed only when the
   approved criteria require a chronological comparison; each remains a unique
   exact revision and its criterion/observation role is explicit.
4. Evidence must belong to the same tenant and Organization as the check and
   ActionExecution. Cross-tenant and cross-Organization references are rejected.
5. Each revision must exist, be readable under RLS, be immutable/retained, have
   a recomputable matching canonical provenance/content hash, and be applicable
   to at least one frozen assessment criterion.
6. Draft/current aliases, missing content references, hash mismatch, invalid
   provenance or inaccessible evidence fail closed. They can justify `unknown`
   only through a separately recorded due assessment; they are never ignored.
7. Raw Evidence content is not copied into the check, event or audit record.

For `unknown`, the minimum valid reference documents the attempted assessment
and exact blocking/unavailability condition; it does not pretend the missing or
invalid business evidence was available. Thus uncertainty remains evidenced
without relaxing the 1..N rule.

## 7. MeasurementDefinition linkage

The linkage is **conditionally required**:

- required when any criterion uses a defined measurement's `what`, `method` or
  `measurement_timing`, or when the planning context derives `due_at` from that
  timing;
- absent when the approved assessment is solely an evidence-based governance
  review and no criterion claims to be measurement-defined.

When required, the check references exactly one immutable
MeasurementDefinition revision under the same tenant and Organization. If more
than one definition would be needed, v1 fails closed pending a later policy.
The definition supplies what/method/when semantics only. Observations must be
preserved as exact Evidence revisions. This policy does not create or imply a
MeasurementRecord and does not invent `measurement_value`, `measured_at`, unit,
formula, threshold or threshold result fields.

## 8. Exact provenance

A check binds to exactly one succeeded controlled ActionExecution and its exact
Receipt. It preserves or transitively proves the immutable ActionPlan ID/hash,
ExecutionAuthorization, AgentDecision, Recommendation and policy identity. For
the target it binds:

- Opportunity logical lineage;
- exact authorized pre-execution revision;
- exact resulting deferred revision;
- tenant and Organization; and
- trace/correlation identifiers.

No `latest` target or governance pointer is allowed. The check does not claim
that a failed or non-committed execution had a business effect to assess.

## 9. Append-only correction and supersession

Every recorded assessment is immutable. A correction creates a new complete
EffectivenessCheck that supersedes the current leaf; material UPDATE/DELETE is
forbidden. The model is **immutable assessment records with linear
supersession**, not mutable logical rows.

The superseding record must have revision `predecessor.revision + 1`, point to
the exact predecessor and retain the same tenant, Organization,
ActionExecution, Receipt and target provenance. It carries its own outcome,
Evidence set, optional MeasurementDefinition, actor, authority context,
assessment time, trace and mandatory correction reason.

There is one current leaf. Forks, predecessor reuse, self-reference, cycles,
cross-tenant/cross-Organization lineage and a different ActionExecution are
rejected. The original record and all predecessors remain readable. Correction
never edits execution, evidence or audit history.

## 10. Event and audit contracts

One business event type is sufficient: `effectiveness_check.recorded`, schema
version 1. Every original or superseding record emits exactly one event and one
TransactionalOutbox row in the same transaction as the future check and its
Evidence links. No separate `effectiveness_check.superseded` DomainEvent is
needed; `supersedes_check_id` and `revision` express the lineage without
duplicating taxonomy.

The event contains identifiers/provenance, not raw blobs:

```text
event_id, schema_version, tenant_id, organization_id,
effectiveness_check_id, revision, supersedes_check_id,
action_execution_id, receipt_id, action_plan_id, plan_hash,
target_type, target_lineage_id, before_revision_id, after_revision_id,
outcome, assessment_method, actor_type, actor_external_id,
measurement_definition_revision_id (nullable), evidence_revision_ids,
due_at, assessed_at, trace_id, policy_id
```

The ImmutableAuditLog append occurs in the same transaction and reconstructs
tenant, Organization, actor and authority context, exact execution/receipt/
plan/authorization provenance, target revisions, outcome and reason,
assessment criteria hash, exact Evidence IDs and hashes,
MeasurementDefinition if used, timing semantics, trace, event/outbox IDs and
supersession lineage. Audit stores hashes and identifiers, not raw Evidence,
prompts, tokens, secrets or sensitive document content.

Any failure to create the check, Evidence links, event, outbox or audit rolls
back the entire future command.

## 11. Compensation, learning and normative boundaries

`ineffective`, `inconclusive` and `unknown` never invoke
`opportunity.resume_evaluation`. Compensation remains a different controlled
action requiring its own Recommendation, Decision, Approval, Plan,
Authorization, idempotency identity, Execution and Receipt.

No effectiveness result automatically updates Recommendation confidence,
ModelPolicy, agent configuration, prompt, Knowledge Layer, training data or
institutional memory. A future learning workflow must be independently governed
and may consume only authorized/redacted provenance.

Effectiveness is operational/QMS governance state. It does not create a
RequirementControl, change StandardEdition or KnowledgeLayerRule, alter
certifiability counts, or reinterpret normative compliance.

## 12. Change control and implementation gate

Policy v1 is immutable once referenced. Any new outcome, assessor type,
cross-Organization rule, evidence cardinality rule, timing derivation,
MeasurementDefinition multiplicity, event meaning, automatic response or
assessment method requires v2+ and preserves v1 history.

`APPROVED FOR IMPLEMENTATION GATE` authorizes only a later Phase 19 foundation
proposal. It does not itself authorize schema, migration, API, deployment,
production/staging/shared-environment enablement, a second QMS action,
automatic compensation, automatic learning or external effects.
