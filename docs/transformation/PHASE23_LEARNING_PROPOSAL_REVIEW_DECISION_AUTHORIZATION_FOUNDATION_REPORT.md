# Phase 23 — Learning Proposal Review + Decision + Application Authorization Foundation

- Date: 2026-08-25
- Scope: additive, inert governance foundation only
- Phase 22 prerequisite: **PROMOTED**
- PostgreSQL: official isolated 18.6 image
- Final database run: `20260825T181952Z_852f01`
- External business effects/deployment: **ZERO**
- Verdict: **PROMOTED — ZERO P0/P1 BLOCKERS**

## 1. Executive verdict and Phase 22 authorization

Phase 22's `governed-learning-proposal-review-application-boundary/v1` authorizes
only immutable review, exact decision, and inert application-authorization
records. Phase 23 implements exactly that foundation. It does not apply a
proposal, create target vN+1, call a target curator, publish, activate, deploy,
change runtime behavior, increase autonomy, or modify normative content.

The implemented semantic chain remains explicit:

```text
EffectivenessCheck -> LearningSignal -> LearningProposal
-> LearningProposalReview -> LearningProposalDecision
-> LearningApplicationAuthorization
-> FUTURE target-specific application -> FUTURE target vN+1
```

No command auto-advances to the next boundary.

## 2. Migration evolution and retained history

Migration `0019_learning_proposal_review_application_authorization_foundation`
is additive and depends only on frozen migration 0018. Empty Phase 23 history
passed `0018 -> 0019 -> 0018 -> 0019`. After governance rows existed, reverse
was denied with the documented forward-only error and every review, decision,
and authorization row remained present. History was not deleted to simulate
reversibility.

Migrations 0001–0018 remain byte-for-byte identical to their promoted hashes.
No protected target schema or target grant was changed.

## 3. LearningProposalReview

`LearningProposalReview` is append-only governance evidence. It freezes tenant,
Organization, exact proposal ID/revision/predecessor/material hash, exact target
type/ID/lineage/version/hash, deterministic target status (`valid|stale`), bounded
safety findings, reviewed governance domains, trusted reviewer provenance,
global governance scope, policy, trace, correlation, and timestamps.

The only review outcome is `review_recorded`; review does not imply approval or
authorization. Multiple independent reviews may be appended. Review records
contain no raw Evidence, document body, prompt, token, secret, or arbitrary
target mutation payload.

## 4. LearningProposalDecision

`LearningProposalDecision` is immutable and one-effective-record-per-exact-
proposal. Its only outcomes are the Phase 22 values:

- `approved_for_application`;
- `rejected`;
- `changes_requested`.

It freezes the exact proposal and target tuple plus the exact review ID set and
review-set hash. `approved_for_application` means only that a separate inert
authorization may be requested. It does not modify status on LearningProposal,
create an authorization automatically, or affect a target.

## 5. LearningApplicationAuthorization

`LearningApplicationAuthorization` is an immutable `authorized` artifact bound
to one exact approved decision, proposal revision/material hash, target
type/ID/lineage/version/hash, target-specific capability/version, trusted
authorizer provenance, idempotency identity/hash, policy, trace, and timestamps.

It has no field/value/dynamic mutation payload, application claim, executor,
target writer, curator call, successor result, publication, activation, or
deployment semantics. Denied requests create no misleading authorization row.

## 6. Exact proposal and target freeze

All three records compute and freeze the same canonical proposal material hash.
The frozen proposal material includes proposal identity, revision/predecessor,
tenant/Organization, target tuple, proposed-change hash, pending status, and
Phase 21 policy. Every boundary also copies the exact target identity, lineage,
version, and Phase 21 canonical full-row hash. No `latest` or current-pointer
rebinding exists.

## 7. Drift and supersession

- A review may record `target_status_snapshot=stale` as historical evidence.
- Decision creation rejects a superseded proposal or drifted target.
- Authorization creation rejects supersession, target drift, missing/ambiguous
  decision history, and every non-approved outcome.
- Existing authorization history is never mutated. The query classification is
  deterministically `VALID` or `STALE`.
- P1 review/decision/authorization never transfers to P2.
- A curator-drift-versus-authorization race ends either denied or with a
  historical authorization that immediately classifies `STALE`; it never
  rebinds or mutates the target.

## 8. Separation of duties and AdminApps boundary

Three separate trusted context types and three separate real database LOGIN
principals exist: learning reviewer, learning approver, and learning authorizer.
All are non-superuser, `NOINHERIT`, `NOBYPASSRLS`, non-owner, and least privilege.

AdminApps remains authoritative for identity, MFA, access, roles, and governance
permissions. Commands accept typed server-resolved authority only. Client actor,
role, tenant, Organization, permission, approval, scope, body, query, and header
claims cannot grant authority. `UserProjection` is only an exact identity link.

Executed denials prove:

- proposal creator cannot approve or authorize the same proposal;
- review-only authority cannot decide;
- decision approver cannot act as application authorizer on the same proposal;
- worker, projector, audit writer, executor, and Phase 21 learning-governance
  principal have no decision/authorization INSERT privilege;
- effectiveness review authority is not accepted as Phase 23 authority; and
- target curator rights neither imply nor are implied by proposal governance.

The reviewer and approver are separate database authorities. A human may hold
both only through independently resolved trusted contexts; creator self-approval
still fails closed. Application authorizer is required to be distinct from both
creator and exact decision approver.

## 9. Tenant, Organization, and global target boundary

Every Phase 23 table has direct non-null tenant and Organization scope,
composite tenant/Organization foreign keys, and exact proposal linkage. Tenant
visibility for review/decision/authorization passed A/none/B as respectively
`5/0/0`, `3/0/0`, and `2/0/0` in the final synthetic run.

All current target candidates are global. The governance rows remain tenant-
scoped provenance and require trusted global governance. No target receives a
fake tenant ID. No tenant actor gains global target DML, and no cross-tenant
aggregation, influence, or application exists.

## 10. Target-specific capabilities and safety exclusions

The exact Phase 22 existing curator capability names are allow-listed:

| Target | Inert capability identifier |
|---|---|
| `ModelPolicy` | `revise_model_policy` |
| `AgentDefinition` | `revise_agent_definition` |
| `KnowledgeLayerRule` | `revise_knowledge_layer_rule` |

The capability identifier is provenance only. No generic
`apply_learning_proposal`, `update_learning_target`, arbitrary field writer, or
application adapter exists. Prompt/rule bundle and retrieval configuration are
not eligible. Safety findings block approval for autonomy changes, normative
changes, policy relaxation, and cross-tenant effects.

## 11. Idempotency and concurrency

Authorization identity includes tenant, Organization, exact proposal revision
and material hash, decision, target tuple, capability/version, idempotency key,
authorizer, authority context version, and authority decision reference. Exact
replay returns the same artifact. Same key plus different provenance conflicts.

PostgreSQL transaction-scoped advisory serialization plus unique constraints
proved:

- two reviews both append immutable evidence;
- two exact decisions produce one record and one deterministic replay;
- two exact authorizations produce one record and one deterministic replay;
- proposal correction makes P1 decision fail closed;
- target drift versus authorization never creates a rebound authorization; and
- no duplicate effective governance outcome exists.

## 12. Events, outbox, and audit

Only these Phase 23 schema-v1 events were added:

- `learning_proposal.reviewed`;
- `learning_proposal.decision_recorded`;
- `learning_application.authorized`.

The final learning event allow-list is the two Phase 21 created events plus these
three Phase 23 events. No applied/completed/target-updated/autonomy event exists.

Each successful command atomically writes the governance record, DomainEvent,
TransactionalOutbox, and ImmutableAuditLog. Audit reconstructs the exact actor,
proposal, reviews/decision, target tuple, capability, trace, event, policy, and
authority-decision linkage. Hardened audit metadata stores bounded IDs/hashes
and a hash of the authority decision reference; the immutable artifact retains
the exact sanitized authority reference. Raw content and secrets are excluded.

## 13. Atomic commands and rollback matrices

The explicit commands are:

- `record_learning_proposal_review(...)`;
- `record_learning_proposal_decision(...)`;
- `authorize_learning_proposal_application(...)`.

For each command, injected failure after primary insert, after Event, after
Outbox, after Audit, and before commit left zero partial state.

| Command | Rollback result |
|---|---:|
| Review | 5/5 PASS |
| Decision | 5/5 PASS |
| Authorization | 5/5 PASS |
| Phase 21 inherited signal/proposal | 14/14 PASS |
| EffectivenessCheck inherited | 9/9 PASS |

## 14. RLS, raw SQL, and catalog security

All three tables have `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL
SECURITY`. No-tenant visibility is zero and Tenant B cannot read Tenant A.
Composite relations reject cross-tenant/cross-Organization proposal links.

Direct UPDATE and DELETE were denied on review, decision, and authorization.
Database triggers reject proposal/target re-pointing, outcome/status mutation,
decision re-pointing, capability mutation, stale target decisions, stale target
authorizations, creator self-approval, combined approver/authorizer duty, and
untrusted context. Protected target INSERT/UPDATE/DELETE is false for every
Phase 23 principal. Runtime principals own no Phase 23 table.

## 15. Protected-target invariance and no-effect tests

Count plus ordered complete-row JSON digests were identical before and after all
review, decision, authorization, replay, concurrency, rollback, and supersession
operations for ModelPolicy, AgentDefinition, KnowledgeLayerRule, normative
catalog, Recommendation, execution, Effectiveness, Opportunity, and agent-run
history. The deliberate drift fixture used the already-promoted target curator
path only after this invariance assertion and proved stale handling; no Phase 23
command performed that mutation.

An approved decision caused zero target changes. One authorization, concurrent
authorization replays, and multiple authorizations across synthetic proposals
caused zero target changes, no successor, no publish/activation, and no runtime
behavior change.

Repository contract scans found no application executor, target writer, generic
mutation function, target DML grant, or forbidden application/target/autonomy
event in the Phase 23 module or migration.

## 16. Inherited regressions

The final PostgreSQL lifecycle reran the applicable Phase 13, 14, 16, 17, 19,
and complete Phase 21 matrices. Phase 20/20.1 are governance/design boundaries;
their frozen artifacts and their implementation authorization remained
unchanged. Results include Phase 16 13/13 rollback, Phase 19 9/9 rollback,
Phase 21 14/14 rollback, Effectiveness correction concurrency, controlled
execution recovery, RLS, role catalog, protected-history, and no-auto-learning
guarantees: all PASS.

## 17. Backend, foundation, and Django integrity

| Suite/check | PASS | FAIL | SKIP | Duration | Delta |
|---|---:|---:|---:|---:|---|
| Full backend | 185 | 0 | 0 | 111.515 s | Phase 23 adds 5 contract tests; exact whole-repo entry run was not recorded |
| Foundation | 87 | 0 | 0 | 0.057 s final | +5 from promoted Phase 21 count 82 |
| `manage.py check` | 1 | 0 | 0 | completed | zero issues |
| `makemigrations --check --dry-run` | 1 | 0 | 0 | completed | no drift |
| Python compilation | 1 | 0 | 0 | completed | new module/migration/harness compile |

The legacy full suite attempted pre-existing Chroma/PostHog DNS telemetry; the
sandbox blocked resolution and no request succeeded. Phase 23 code contains no
HTTP/provider/tool/notification integration and made zero external business
effects.

## 18. Migration hashes

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
| 0018 | `703a85885a67df953f38ef35302205caeddea249104683f4f751ab20ece0696b` | MATCH |
| 0019 | `c188b638124404bba10cae4c94a678053d49d7a1d07c6e455a48e46524064b50` | NEW |

## 19. Source and governance hashes

All ten sources were directly byte-read. Every member of the DOCX and XLSX ZIP
packages was read; XML/text content was extracted for semantic reconciliation.
Hashes are 10/10 MATCH with `SOURCE_ARTIFACT_MANIFEST.md`:

`8308bde9…`, `e0a59c91…`, `11c2b461…`, `952d8ac9…`, `ecaecd25…`,
`30e3c052…`, `de1b4899…`, `29ac5c2d…`, `c41e847e…`, `eb42315c…`.

Frozen governance/artifact hashes remained unchanged:

| Artifact | SHA-256 |
|---|---|
| Governed Learning Policy v1 | `7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec` |
| Phase 21 implementation authorization | `04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c` |
| Phase 22 governance boundary | `2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514` |
| Phase 22 ADR-0012 | `4fd6b330081ad4cd24bb55792bf10e9529033156c43d70eba0868be25a403fd0` |
| Phase 22 report | `a94ba44e4b968aa2d117d99ebe03f4e094c4e1e684fb380ddc40c220efe3a1b2` |
| Effectiveness Policy v1 | `3e2f2b5b3f335bcb425c4b3d8043c2b541de56b0a7b14fbc63b8f48e4392758f` |
| Controlled QMS Action Policy v1 | `29829c38745db67985fb1523837c79276508bdc9d2136b64442ea238ed13566f` |

## 20. Zero external effects, teardown, and git hygiene

No production, staging, shared database, AdminApps write, MedSupplier write,
provider/tool call, notification, deployment, target application, or business
effect occurred. PostgreSQL used only run-scoped database, roles, container,
volume, and temporary directory. Finalizer verification: database/roles removed,
container absent, volume absent, temporary directory absent.

All Phase 23 files pass trailing-whitespace and Python checks. Repository-wide
`git diff --check` retains only the known unrelated pre-existing Sidebar
whitespace note; Phase 23 did not edit that file. Unrelated dirty worktree files
were preserved.

## 21. Residual risks

1. This is a foundation, not an API or operational queue; production enablement
   remains prohibited.
2. Live AdminApps authority resolution is outside this gate; only typed trusted
   contexts and synthetic tests exist.
3. Authorization expiry, revocation, and one-time application claim remain for a
   future target-specific application gate; no application exists to consume one.
4. Prompt/retrieval targets, cross-tenant learning, activation/deployment, and
   autonomy/policy relaxation remain not ready or separately prohibited.
5. The full legacy test suite still attempts blocked telemetry DNS and should be
   made hermetic in a separate change.

There are **0 P0** and **0 P1** blockers to the next source/policy and security
design gate. None of these residual risks authorizes target application.

## 22. Promotion verdict

**PHASE 23 — LEARNING PROPOSAL REVIEW + DECISION + APPLICATION AUTHORIZATION
FOUNDATION: PROMOTED**

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| Phase 22 prerequisite | PASS | promoted boundary/ADR/report hashes unchanged | keep scope inert |
| Migration 0019 | PASS | additive; empty-history F/R/F; retained reverse denied | forward-fix after history |
| Review | PASS | exact immutable proposal/target evidence; concurrent append | no approval implication |
| Decision | PASS | exact three outcomes; one record/replay; stale/self approval denied | no automatic authorization |
| ApplicationAuthorization | PASS | exact inert capability; replay/conflict; VALID/STALE | no application/executor |
| Authorities/AdminApps | PASS | three principals; trusted contexts; spoof/combined-duty denied | live resolver later only |
| Tenant/global/RLS | PASS | ENABLE+FORCE 3/3; A/none/B; no target DML | no cross-tenant/global mutation |
| Event/outbox/audit | PASS | three allow-listed v1 events; 15/15 rollback | preserve bounded metadata |
| Concurrency/drift | PASS | review, decision, authorization, correction and curator race | future gate must repeat TOCTOU at mutation |
| Protected/no-effect | PASS | governance operations leave all protected rows identical | deliberate curator drift isolated |
| Regressions | PASS | Phase 13/14/16/17/19/21 + 185 backend + 87 foundation | remove legacy telemetry separately |
| Hashes/teardown | PASS | 18/18 frozen migrations; 10/10 sources; governance unchanged; resources absent | freeze 0019 after promotion |

## NEXT_CODEX_PROMPT

Execute PHASE 24 — FIRST LEARNING TARGET APPLICATION CANDIDATE SOURCE/POLICY + SECURITY DESIGN GATE in `/home/felipe/proyectos/isosmart`. Do not implement generic proposal application and do not mutate any target. Compare eligible target types and select exactly one narrow versioned target operation only if it can require the exact proposal, exact decision, exact application authorization, exact immutable target vN/hash, future vN+1-only creation, a target-specific capability and curator, idempotency, TOCTOU/concurrency controls, rollback by version compensation, separate publication/activation, no normative content, no autonomy escalation, and no cross-tenant/global escalation. If no target satisfies every criterion, emit NOT PROMOTED.
