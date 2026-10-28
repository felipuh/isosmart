# ISO Smart Controlled QMS Action Product Policy v1

**Version:** v1

**Status:** PROPOSED — NOT APPROVED FOR CONTROLLED POC

**Date:** 2026-08-24

**Owner/system authority:** ISO Smart Product Governance

**Policy identity:** `controlled-qms-action-policy/v1`

> **THIS POLICY DEFINES ISO SMART APPLICATION BEHAVIOR.**
>
> **IT DOES NOT DEFINE, MODIFY, INTERPRET OR ADD A CERTIFIABLE ISO
> REQUIREMENT.**

This artifact is an ISO Smart-owned, non-normative product-governance decision.
It is not an authoritative external source and must not be stored or treated as
one. It never creates or alters `RequirementControl` or `KnowledgeLayerRule`,
never affects certifiable-requirement counts, and never claims that the state
machine below is defined by ISO.

## 1. Scope and policy decision

The authoritative source package establishes `Opportunity` as a QMS business
object associated with a Process and gives it `hypothesis`, `benefit`,
`feasibility`, and `status`. It also requires human approval for material record
changes and places execution after the human gate. The sources do **not** define
status values, legal transitions, impact, or a business inverse.

Product Policy v1 proposes only this bounded application behavior:

```text
action_type = "opportunity.defer_evaluation"
target_type = "Opportunity"
expected current state = "under_evaluation"
desired state = "deferred"
single legal transition = under_evaluation -> deferred
impact = standard
reversibility = reversible
max_autonomy = A3
human_approval = required
```

`under_evaluation` means ISO Smart treats the Opportunity as currently eligible
for internal evaluation. `deferred` means ISO Smart temporarily removes that
Opportunity from active internal evaluation without accepting it, rejecting it,
changing its hypothesis/benefit/feasibility, communicating externally, or
changing another QMS object. These meanings and values are product decisions,
not ISO requirements. This policy does not define any other lifecycle state or
transition.

The exact compensation action is:

```text
action_type = "opportunity.resume_evaluation"
target_type = "Opportunity"
expected current state = "deferred"
desired state = "under_evaluation"
single compensation transition = deferred -> under_evaluation
```

The compensation identifier is governed here for future use, but compensation
is not an automatically executed inverse and is not part of the one forward
action authorized by this policy proposal.

## 2. Preconditions and fail-closed rule

All conditions are mandatory and must be resolved server-side. `unknown` is a
denial with zero mutation.

1. The trusted TenantProjection is active and entitled.
2. The exact Opportunity revision exists under that tenant.
3. Its Organization equals the exact ActionPlan, Decision, Approval,
   Authorization, and ActionExecution Organization.
4. `target_id` is the exact Opportunity lineage ID; `expected_revision_id` is
   the exact current leaf revision ID; `expected_revision` is its integer
   revision; no successor exists.
5. The observed status is exactly `under_evaluation`.
6. Hypothesis, benefit, feasibility, Process, tenant, Organization, and lineage
   match the frozen expected-state fingerprint and are not changed by the plan.
7. The ActionPlan hash recomputes exactly under
   `iso-smart-action-plan-v1`; the ExecutionAuthorization binds that exact hash.
8. The effective human Approval is `approve`, unambiguous, active, and bound to
   the exact Decision/Recommendation/published ModelPolicy chain.
9. `policy_id` is `controlled-qms-action-policy/v1`, required autonomy is A3,
   and no broader authority is inferred from the target type.
10. No terminal execution or receipt conflicts with the exact idempotency
    identity.
11. The execution implementation can atomically compose the promoted domain
    command, domain event/outbox/audit, and execution completion/receipt.
12. The executor reaches the mutation only through a narrow action-specific
    boundary and has no generic Opportunity INSERT/UPDATE/DELETE authority.

Preconditions 11 and 12 are not satisfied by the current Phase 14 runtime;
therefore this v1 policy remains `PROPOSED` and does not authorize a POC.

## 3. Business impact classification

The proposed action is `impact = standard` only when every precondition above
passes. The business effect is one tenant/Organization-scoped Opportunity being
temporarily excluded from active internal evaluation. It does not accept or
reject the Opportunity; alter its substantive assessment fields or Process;
send a message; change financial, identity, access, billing, security, normative,
document, evidence, or audit state; delete or overwrite history; or affect
another aggregate. The promoted command would append one revision and preserve
the prior revision. Any broader effect or integration is outside this policy and
fails closed.

## 4. Business reversibility and compensation

The forward business meaning is “temporarily stop active internal evaluation.”
The compensation business meaning is “restore the same Opportunity to active
internal evaluation.” It uses the promoted
`RiskOpportunityObjectiveCommandService.change_opportunity_status` semantics,
creates a later revision, and emits its own domain event/outbox/audit.

Compensation is eligible only when the exact forward-produced revision is still
the current leaf, its status remains `deferred`, its substantive state
fingerprint matches the forward receipt, the same policy version is applicable,
and a new ActionPlan, dry-run, authorization, human Approval, idempotency key,
and ActionExecution have independently passed. It is invalid after any
successor revision, substantive field change, unrelated status change, policy
withdrawal, tenant/Organization mismatch, or unknown condition. Invalid
compensation does not rewrite history or run raw SQL; it stops and requires
human resolution.

Compensation restores the status meaning only. It cannot undo downstream human
decisions or external effects; this policy prevents those effects from being
part of the forward action.

## 5. Idempotency

- **Case 1 — expected source state:** exact current revision is
  `under_evaluation`; the action is eligible after every gate passes.
- **Case 2 — desired state from the same authorized action:** the current leaf
  is the exact `resulting_revision_id` recorded in the immutable receipt for the
  same Authorization, plan hash, execution/idempotency identity, and domain
  event. Return that prior receipt; do not call the domain command again.
- **Case 3 — desired state from another action:** status is `deferred`, but the
  provenance linkage above is absent or different. Return conflict/stale target;
  never report replay success and never mutate.

The durable identity is tenant + Organization + Authorization ID + plan hash +
action type + target lineage ID + expected revision ID + idempotency key. The
same key with any material difference is conflict.

## 6. TOCTOU and concurrency

Dry-run reads the exact current leaf and records every observed precondition.
Authorization repeats source/revision/state/policy/hash and Approval checks.
Execution repeats them inside the mutation transaction immediately before the
command. Any intervening change causes `stale_target` and zero mutation.

The required strategy is pessimistic locking plus append constraints:

1. lock the ActionExecution/idempotency identity;
2. read immutable Authorization/ActionPlan/Approval provenance;
3. `SELECT ... FOR UPDATE` the exact expected Opportunity revision;
4. prove it is the unique leaf and exact expected state/fingerprint;
5. invoke the governed status command once;
6. write domain event/outbox/audit and execution receipt/lifecycle records;
7. commit once.

Lock order is always execution identity, target revision, domain event stream,
audit stream, then outbox/receipt writes. Serialization/deadlock failure rolls
back the whole unit and never implies success.

## 7. ActionPlan and dry-run contracts

The v1 canonical hash already covers the material contract because all
action-specific fields fit in `parameters`, while action/target/Organization,
impact, reversibility, preconditions, dry-run support, autonomy, Decision, and
Recommendation are top-level canonical fields.

```json
{
  "action_type": "opportunity.defer_evaluation",
  "target_type": "Opportunity",
  "target_id": "<opportunity-lineage-uuid>",
  "parameters": {
    "expected_revision_id": "<current-revision-uuid>",
    "expected_revision": 3,
    "expected_current_state": "under_evaluation",
    "desired_state": "deferred",
    "expected_state_hash": "<sha256>",
    "policy_id": "controlled-qms-action-policy/v1",
    "compensation_action_type": "opportunity.resume_evaluation"
  },
  "impact": "standard",
  "reversibility": "reversible",
  "dry_run_supported": true,
  "required_autonomy": 3
}
```

Tenant is derived from trusted execution identity. Organization is derived from
the target and must equal the canonical plan Organization. No arbitrary
field/value map or runtime replacement payload is allowed.

Dry-run returns target lineage/revision IDs, expected revision, observed and
desired state, state hash, each precondition result, transition legality,
impact, reversibility, compensation availability, policy identity, and plan
hash, with `business_state_changed=false`. It performs no write.

## 8. Domain command, transaction, events, audit, and receipt

The proposed command is
`RiskOpportunityObjectiveCommandService.change_opportunity_status`. It accepts
trusted identity, exact current revision ID, desired status, actor, trace,
optional reason, and rollback-test flag. It requires a current leaf, copies
Process/hypothesis/benefit/feasibility unchanged, appends revision N+1, and emits
`opportunity.status_changed` schema v1 plus TransactionalOutbox and immutable
audit in the command-owned transaction. Database constraints reject forks and
historical UPDATE/DELETE.

Current composition is **not safe for controlled execution**:
`trusted_tenant_context` requires ownership of the outermost transaction and
raises when one already exists, while Phase 14 starts and completes an
ActionExecution in separate transactions around executor invocation. Calling
the command as-is cannot atomically bind business mutation to completion and
receipt. A future command-only design gate must prove an action-specific,
transaction-aware composition seam and a narrow privilege boundary without
changing business/event/audit semantics. Until then, no adapter may register.

Execution lifecycle events (`action_execution.*`) describe the attempt and
outcome. `opportunity.status_changed` alone describes the QMS semantic change.
Neither duplicates the other. Audit streams link by tenant, Organization,
trace, execution ID, target lineage, revision IDs, and domain event ID.

A future receipt must include Execution ID, Authorization ID, plan hash, policy
identity, action/target, before lineage/revision/state/hash, after
lineage/revision/state/hash, domain event/outbox/audit IDs, execution outcome,
idempotency identity, compensation eligibility, timestamps, and
`effectiveness_claimed=false`.

## 9. Approval, autonomy, and effectiveness boundary

Human Approval is always required. `max_autonomy = A3`: an agent may prepare;
a human must approve; the system may execute only the exact approved plan after
all execution gates. A3 is never blanket authority over Opportunity.

Successful execution would prove only that the governed status transition and
its records committed. It does not prove the deferral was effective or useful.
A future `EffectivenessCheck` would need the exact ActionExecution/receipt,
intended evaluation-queue outcome, observation method/time, resulting revision,
and Evidence references. It is not implemented by this policy.

## 10. Change control

The v1 meaning is immutable once a controlled execution is permitted. Any new
state, transition, impact rule, compensation condition, field effect, autonomy
rule, or hash interpretation requires v2+ and must preserve historical policy
identity. Withdrawal is a new governance decision; historical plans and
receipts retain v1. This proposal cannot be silently relabeled approved: a
successor gate must record evidence that preconditions 11 and 12 pass.
