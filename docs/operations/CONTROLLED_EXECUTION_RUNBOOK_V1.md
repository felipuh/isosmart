# Controlled Execution Operational Runbook v1

**Version:** v1

**Status:** DESIGN APPROVED — NOT PRODUCTION ENABLEMENT

**Scope:** `opportunity.defer_evaluation` and its exact recovery capability

**Date:** 2026-08-24

This runbook defines role categories and fail-closed procedures. AdminApps
resolves the actual authenticated identity, global access/MFA and authority.
This document does not authorize production, staging, a shared DEV/QA database,
deployment, raw-SQL repair, a second action or an external effect.

## 1. Non-negotiable invariants

- Preserve ActionExecution, Receipt, Opportunity revisions, DomainEvent,
  TransactionalOutbox, ImmutableAuditLog and compensation history.
- Never blind-retry after an ambiguous COMMIT.
- Reconcile with the exact Authorization and idempotency identity.
- `COMMITTED` means the execution artifacts committed; it says nothing about
  effectiveness.
- `NOT_COMMITTED` permits at most one normal controlled invocation after every
  gate is revalidated.
- `INCONSISTENT` means no retry and no automatic repair.
- Never use ad-hoc `UPDATE`, `DELETE`, receipt insertion, status forcing, RLS
  disablement or history deletion as repair.

## 2. Operational roles

| Role category | Responsibility | May authorize |
|---|---|---|
| Platform operator | Collect scoped operational evidence, invoke exact reconciliation, disable the exact capability through the governed release mechanism | containment/disable request within assigned environment |
| Security operator | Investigate identity, ACL, RLS, SECURITY DEFINER, search-path or secret/integrity concerns | security containment and security clearance |
| QMS authorized reviewer | Evaluate business provenance and effect on the Opportunity; decide whether a proposed repair/compensation workflow is acceptable | QMS repair decision and later business workflow, never raw DML |
| Release authority | Own forward-only release boundary, change validation and controlled capability state | deployment/change window and enable/disable decision |
| Incident commander | Coordinates evidence custody, owners, severity, communications and closure | incident workflow, not business data mutation |

Separation of duties: re-enable requires Release authority plus Security
operator clearance and QMS authorized reviewer approval. One person may not
self-approve a privileged repair they performed. Personal names are maintained
in the external incident/authority system, not this runbook.

## 3. First response to an ambiguous execution result

1. Stop caller retry and preserve Authorization ID, trace ID and the raw
   idempotency key only in the protected caller context; operational logs use
   only its hash.
2. Bind trusted tenant context from authenticated server identity. Do not accept
   tenant or Organization from a client request.
3. Invoke only the exact forward reconciliation capability using the original
   Authorization and idempotency key. Compensation uses its different exact
   reconciliation capability.
4. Record reconciliation audit ID, outcome, reason and observed artifact counts.
5. Follow exactly one outcome procedure below.

## 4. `COMMITTED` procedure

The reconciliation capability has already proved one exact terminal execution,
Receipt, resulting Opportunity revision, business event/outbox/audit and
execution event/outbox/audit.

1. Retrieve the immutable Receipt returned by reconciliation; do not recreate it.
2. Verify Authorization, ActionPlan ID/hash, action/policy, tenant,
   Organization, target lineage, before/after revision and trace match the
   caller's protected request record.
3. Verify artifact counts remain exactly one for the Receipt, resulting
   revision and both event/outbox/audit groups.
4. Return the existing Receipt with `replayed=true` through the normal sanitized
   response path.
5. Never rerun the action. Do not compensate or claim effectiveness.

Escalate and disable the capability if a fresh exact reconciliation changes to
`INCONSISTENT`, counts/provenance differ, a receipt/hash mismatch appears, RLS
or ACL behavior is unexpected, or audit/event/outbox evidence is unavailable.

## 5. `NOT_COMMITTED` procedure

The reconciliation capability has already proved no durable claim and that the
exact authorized Opportunity leaf remains unchanged.

1. Verify no ActionExecution claim or Receipt exists for the exact tenant/key.
2. Verify the exact target revision is still the unique leaf, status remains
   `under_evaluation`, the fingerprint matches and no successor exists.
3. Revalidate active tenant/Organization, effective human Approval,
   Authorization outcome and scope, exact ActionPlan canonical hash, policy v1,
   preconditions and capability state.
4. Append/retain the reconciliation audit evidence.
5. Invoke the normal recoverable forward wrapper once using the original
   Authorization and idempotency key.
6. If transport becomes ambiguous again, return to reconciliation; never issue
   a second blind invocation.

Any mismatch changes the operational result to fail-closed escalation, not an
operator-selected `NOT_COMMITTED` override.

## 6. `INCONSISTENT` procedure

1. Do not retry, resume, compensate, manufacture a Receipt or choose which
   artifact is “correct.”
2. Open an incident and assign an Incident commander, Platform operator,
   Security operator and QMS authorized reviewer.
3. Disable the affected exact capability when new execution could compound the
   inconsistency. Preserve public non-controlled Opportunity behavior unless it
   independently violates an invariant.
4. Preserve snapshots/exports and identifiers for ActionExecution, Receipt,
   exact Opportunity lineage/revisions, Authorization, Plan/hash, Approval,
   Decision/Recommendation chain, DomainEvent, Outbox and ImmutableAuditLog.
5. Capture tenant, Organization, trace, execution/receipt IDs, hashed
   idempotency, target before/after revisions, observed counts, capability
   state, database/release version and timestamps. Never copy raw secrets,
   prompts or Evidence content into the incident log.
6. Determine whether the cause is transport ambiguity, privileged intervention,
   code/schema drift, ACL/RLS failure, partial historical import or integrity
   corruption.
7. If no pre-approved governed repair procedure exists, keep the capability
   disabled and escalate to a forward-fix design gate. No automatic repair is
   implied.

## 7. Repair authority and limits

A repair may be authorized only by the QMS authorized reviewer for business
meaning, the Security operator for integrity/security, and the Release authority
for the forward change. The repair implementation must be a versioned,
reviewed, least-privilege, tenant/Organization-scoped procedure with dry-run,
pre/post reconciliation, atomicity, event/audit evidence and rollback by
forward correction or capability disablement.

Permitted repair scope is limited to creating new corrective/projection artifacts
or restoring a missing operational capability when a separately approved
procedure proves the source-of-truth history. What may never be rewritten:

- Opportunity revisions or predecessor lineage;
- ActionExecution terminal history or claim ownership;
- Receipts, DomainEvents, Outbox records or ImmutableAuditLog entries;
- Approval, Authorization, ActionPlan/hash, Decision, Recommendation or source
  Evidence; or
- history to make an old downgrade or artifact-count check pass.

If immutable artifacts disagree and no safe additive repair is proved, retain
them, document the integrity exception and freeze the capability.

## 8. Capability disable governance

Disable `opportunity.defer_evaluation` through the governed capability/grant
mechanism when any of these conditions is confirmed or cannot promptly be
excluded:

- reconciliation returns `INCONSISTENT`;
- an RLS, tenant/Organization, ACL, SECURITY DEFINER or search-path invariant
  fails;
- Receipt, revision, event, outbox or audit counts/provenance mismatch;
- an execution claim requires intervention or claim ownership is ambiguous;
- repeated unexplained idempotency/provenance conflicts indicate systemic drift;
- release code does not understand the retained-history forward-only boundary;
- capability state differs from the approved environment marker.

Disablement revokes only the exact controlled forward capability, is audited,
records reason/authority/release/trace/time, and preserves history. It does not
enable compensation, disable RLS, remove public Opportunity commands or delete
data.

## 9. Capability enable governance

There is no automatic self-enable. Re-enable only when all are true:

1. root cause is known and documented;
2. every affected execution is reconciled or remains explicitly quarantined
   under an approved additive repair plan;
3. the corrective forward change passed complete Phase 16/17, security, RLS,
   ACL, concurrency, ambiguity and retained-history regression in isolated
   PostgreSQL 18.6;
4. backup/restore and forward-only release checks pass where applicable;
5. observability and alert routing are verified;
6. Security operator clears the invariant; QMS authorized reviewer accepts the
   business state; Release authority approves the environment change; and
7. enablement audit records exact approvers, evidence, release and time.

## 10. Forward-only release gate and environment markers

Migration 0015 is forward-only after the first controlled history exists.
Before enabling any future environment, the Release authority must run
read-only catalog/data queries and classify:

| Marker | Determination |
|---|---|
| `NO_CONTROLLED_HISTORY` | no `controlled_opportunity` ActionExecution exists |
| `CONTROLLED_HISTORY_EXISTS` | at least one such execution exists; downgrade below 0015 is forbidden |
| `CAPABILITY_DISABLED` | exact recoverable forward wrapper is not executable by EXECUTOR or release configuration denies it |
| `CAPABILITY_ENABLED` | exact wrapper grant/configuration is present and matches approved release state |

The release manifest records migration set/hash, marker results, query time,
environment identity and authority. A mismatch stops release. An automatic
downgrade that removes wrappers or data is not a rollback plan. Use disable,
observe/reconcile, forward fix and later evidence-based contract cleanup.

## 11. Observability contract

Every structured operational signal uses stable names and sanitized values:

```text
tenant_id, organization_id, trace_id, action_execution_id,
action_plan_id, plan_hash, authorization_id, hashed_idempotency_key,
action_type, policy_id, target_lineage_id, before_revision_id,
after_revision_id, reconciliation_outcome, reconciliation_reason,
receipt_id, observed_artifact_counts, capability_state,
release/migration identity, timestamp
```

Never log raw idempotency keys, tokens, credentials, prompts, Recommendation
body, Evidence/document content or unnecessary personal data. Operational
telemetry is not a second system of record; immutable audit remains the durable
governance signal.

## 12. Conceptual alert conditions

No monitoring product is installed by this design. Future telemetry must alert
on:

- any `INCONSISTENT` reconciliation;
- running/terminal execution requiring intervention;
- Receipt/revision/event/outbox/audit mismatch;
- RLS, tenant, Organization, ACL or search-path invariant failure;
- repeated idempotency or provenance conflicts outside expected client error;
- capability unexpectedly enabled or unavailable relative to release marker;
- retained-history downgrade attempt; and
- audit append/reconciliation failure.

Alert deduplication must preserve the first and latest trace/audit IDs. Severity
and routing are set by the incident policy; this runbook invents no SLA/SLO
numbers. Production SLO/SLA, paging targets and response times remain a future
release blocker.

## 13. Closure evidence

An incident closes only after preserved evidence, exact reconciliation results,
root cause, authority decisions, corrective validation, final capability state
and residual risk are recorded. Closing an incident never means deleting the
inconsistent artifacts or relabeling execution as effective.

## 14. Effectiveness review operations (Phase 20 addendum)

The internal attention query consumes only server-authorized tenant/Organization
context plus trusted governed effectiveness plans. Queue membership is never
reviewer authority; every record/correction still resolves current AdminApps
access, MFA and exact permissions independently.

- `due`: `as_of == due_at` and no check exists; present for human review only.
- `overdue`: `as_of > due_at` and no check exists; do not mutate execution, create
  a check, invent an SLA or trigger another workflow automatically.
- `unknown`: current leaf records an evidenced assessment blocker; it is neither
  execution failure nor ineffectiveness.
- `inconclusive`: current leaf records a completed but non-binary assessment; it
  is not scored as negative.
- superseded revisions remain history; attention uses the sole current leaf and
  reports revision/correction count.

For a correction conflict, reload the current leaf and complete lineage. The
losing reviewer must not retry against a stale predecessor; a new correction
requires refreshed Evidence, independently current authority and a reason. Never
repair a fork or stale write with raw SQL.

Authority revocation does not rewrite an assessment made while the actor was
authorized. A revoked actor cannot create a new assessment/correction. A later
Evidence or MeasurementDefinition revision never rewrites an earlier check;
where policy permits, use a governed correction with exact new references.

Sanitized visibility may include category, due time, current check/revision,
correction count, actor reference, execution/trace IDs and reason code. Never
expose Evidence bodies, prompts, tokens or secrets. Conceptual alerts may cover
overdue review, repeated inconclusive outcomes, missing Evidence, authority
failure and lineage conflict; this runbook installs no external monitoring.
