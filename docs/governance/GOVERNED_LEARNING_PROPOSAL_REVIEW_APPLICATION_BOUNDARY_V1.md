# Governed Learning Proposal Review and Application Boundary v1

- Boundary ID: `governed-learning-proposal-review-application-boundary/v1`
- Version: v1
- Date: 2026-08-24
- Owner/system authority: ISO Smart Product Governance
- Status: **APPROVED FOR REVIEW/DECISION/APPLICATION-AUTHORIZATION FOUNDATION IMPLEMENTATION GATE**
- Nature: ISO Smart Product Policy and security boundary; non-normative
- Application status: **PROHIBITED — NO TARGET APPLICATION OR SUCCESSOR CREATION AUTHORIZED**

> This boundary is not an ISO requirement. It does not create, modify,
> supersede or interpret certifiable normative content. It does not amend the
> Phase 21 foundation into an execution capability.

## 1. Purpose and governing invariant

This boundary determines that a future foundation may record review, decision
and application authorization for an exact `LearningProposal` revision without
creating a generic self-modification capability. It authorizes a later
implementation gate for those inert governance artifacts only.

The governed sequence is:

```text
LearningProposal exact revision
  -> independent review
  -> exact decision
  -> separately issued application authorization
  -> future target-specific application gate (not authorized here)
  -> future draft successor vN+1 (not authorized here)
  -> separate publication/activation/release (not authorized here)
```

Review, approval and authorization each cause zero target mutation. A proposal
status is never application authority. No actor, agent, event consumer or
database principal may infer application authority from the existence, count,
outcome or age of LearningSignals or proposals.

## 2. Source facts, Product Policy and design inference

### Source facts

The ten authoritative artifacts describe a universal agent runtime ending in
Effectiveness and governed learning, human approval for material changes,
version/model/prompt/rule provenance, A0–A4 boundaries, versioned Knowledge
Layers and a non-destructive normative history. They identify
`AgentDefinition`, `ModelPolicy`, `KnowledgeLayerRule` and Effectiveness-related
concepts. They do not define LearningProposal review records, decision
authority, application authorization, a generic target writer, proposal
application, cross-tenant aggregation or automatic self-modification.

### Product Policy decisions

ISO Smart therefore requires exact immutable proposal and target binding,
independent human governance, separate decision and authorization artifacts,
tenant-to-global escalation through global governance, target-specific future
capabilities, fail-closed drift, additive successor versions and separate
publication/activation. Automatic application, cross-tenant influence,
normative mutation and autonomy escalation are prohibited.

### Design inferences

Because approval must be attributable and frozen to one exact proposal
revision, a future immutable review/decision artifact is required. Because
approval must not execute, a separate immutable application-authorization
artifact is required. Because target invariants and curators differ, a generic
mutation primitive cannot be made least-privilege; one narrow capability per
target and operation is required.

## 3. Authorized future foundation

A later gate may propose only additive, inert records and controls for:

1. immutable `LearningProposalReview` or equivalent review evidence;
2. immutable `LearningProposalDecision` or equivalent exact decision;
3. immutable `LearningApplicationAuthorization` or equivalent authorization;
4. exact links to one proposal revision, target vN/hash and authority decision;
5. trusted AdminApps-backed authority resolution and separation of duties;
6. expiration, revocation, one-time claim and deterministic idempotency state;
7. tenant/Organization isolation with a distinct global-governance boundary;
8. event/outbox/audit records for the foundation contracts authorized by that
   later gate; and
9. PostgreSQL constraints, RLS and least-privilege grants for those artifacts.

That future foundation must remain non-executing. It may not import or call a
target curator command and may not possess protected-target DML.

## 4. Explicitly prohibited scope

This boundary does not authorize:

- application of a LearningProposal;
- creation, publication, activation or deployment of a target successor;
- any generic `target/field/operation/value` writer;
- target DML for a learning, review, approval or authorization principal;
- a new runtime executor, optimizer, consumer or automatic feedback loop;
- prompt/rule bundle or retrieval configuration application;
- cross-tenant aggregation, anonymized global learning or tenant-to-tenant
  behavioral influence;
- an autonomy increase or removal of a human gate;
- mutation or reinterpretation of normative/catalog content; or
- production, staging, shared database, deployment or external effect.

## 5. Target taxonomy and readiness

| Target | Scope/current versioning | Existing successor authority/capability | Required frozen vN material | Future learning-request readiness | Required approval and invariant |
|---|---|---|---|---|---|
| `ModelPolicy` | Global; lineage/version; published rows immutable | Isolated agent catalog curator; `revise_model_policy` creates a draft from current published leaf | full row/hash, lineage/key/version, approved models, data classes, guardrails, human gates, status | **CONDITIONALLY READY for review/authorization design only** | independent AI governance + security/platform; no self-approval, guardrail relaxation, allowlist expansion or human-gate removal; application automatic = prohibited |
| `AgentDefinition` | Global; lineage/version; published rows immutable | Isolated agent catalog curator; `revise_agent_definition` creates a draft from current published leaf | full row/hash, lineage/key/name/version, purpose, capability, autonomy ceiling, exact ModelPolicy, status | **CONDITIONALLY READY for review/authorization design only** | AI governance + platform target curator; exact published ModelPolicy compatibility; no autonomy increase through learning; application automatic = prohibited |
| `KnowledgeLayerRule` | Global; lineage/version; published rows immutable | Isolated normative curator; `revise_knowledge_layer_rule` creates a draft from current published leaf | full row/hash, layer/edition, lineage/key/version, logic, evidence expectation, source reference, classification, status | **CONDITIONALLY READY for review/authorization design only** | global normative curation + AI governance; published edition/source provenance; classification fixed to `non_certifiable_guidance`; application automatic = prohibited |
| Prompt/rule bundle artifact | Only version strings are frozen in AgentRun/RecommendationBasis; no promoted governed target entity or curator lifecycle | None proven | Not modelable safely | **NOT READY** | require separate target model/security gate, prompt-injection and secret review before eligibility |
| Retrieval configuration | Dataset/embedding namespace provenance exists; no promoted governed configuration target or successor lifecycle | None proven | Not modelable safely | **NOT READY** | require separate target model, namespace/source/tenant isolation and poisoning review before eligibility |

No target shares application semantics merely because it can be referenced by a
LearningProposal. A future implementation must use an explicit allow-list of
target type plus exact operation and reject unknown types.

## 6. Normative exclusion

`Standard`, `StandardEdition`, `Clause`, `RequirementControl` and certifiable
normative content remain permanently outside this boundary. Learning may not
create, modify, publish, supersede, reinterpret or derive certifiability for
them. `KnowledgeLayerRule` remains global, curated,
`non_certifiable_guidance`; neither its name nor binding converts it into a
normative requirement.

## 7. Rejection of generic mutation

The following designs are rejected:

```text
apply_learning_proposal(target_type, target_id, field, value)
update_target_from_proposal(payload)
mutate(target, field, operation, value)
```

They combine policy selection and execution, defeat least privilege, allow
unbounded fields/operations, create confused-deputy risk and make target-
specific validation unverifiable. A later application gate must expose at most
one exact capability per approved target and operation, such as a capability
whose only possible result is creating a draft successor for one exact current
leaf. Conceptual names in this document grant no implementation authority.

## 8. Review lifecycle and decision semantics

The lifecycle is append-only:

```text
proposal revision created
  -> review recorded for that exact revision
  -> decision recorded for that exact revision
     -> rejected | changes_requested | approved_for_application
  -> separate authorization may be requested only for approved_for_application
```

`approved_for_application` means only **eligible to request an application
authorization**. It does not mean executable, applied, current, published,
active or deployed. Rejection and changes requested are terminal for that
decision; correction requires a new proposal revision and new review/decision.
No UPDATE of a decision is permitted; withdrawal or correction is a successor
governance record.

A review and decision must freeze: proposal ID, proposal lineage and revision,
proposal material hash, target identity/lineage/type/scope/version/hash,
reviewer/approver authority provenance, governance domains, sanitized rationale,
outcome, policy version, trace and time.

## 9. Exact proposal correction and target drift

Approval of P1 never authorizes P2. When P2 supersedes P1, every review,
decision or unused authorization for P1 is stale for P2 and cannot be rebound.
P2 requires new review, decision and authorization.

If a proposal references v3/hash H3 and any successor v4 exists, or v3 no
longer matches H3/current-leaf/published invariants, review may record the stale
finding but no new approval or authorization may be effective. Existing unused
authorization transitions conceptually to `stale`/`revoked` through append-only
governance. The proposal is never rebound to v4. A new or superseding proposal
against v4 is required.

## 10. Roles, authorities and separation of duties

| Function | Authority | Required separation |
|---|---|---|
| Effectiveness reviewer | QMS assessment authority | does not imply signal/proposal/review/approval authority |
| LearningSignal creator/deriver | allow-listed learning derivation authority | cannot review, approve, authorize or apply its derived signal |
| LearningProposal creator | attributable human/governance proposer | cannot approve or authorize own proposal |
| Proposal reviewer | qualified governance-domain reviewer | cannot be an agent/system; reviewer evidence alone is not approval |
| Proposal approver | independent human governance authority | distinct from proposer; for global targets must hold global authority |
| Target curator | existing target-specific curator authority | never inherited by learning principal or tenant user |
| Application authorizer | independent authority for exact capability invocation | separate from proposer and application executor; cannot broaden payload |
| Application executor | future technical principal for one exact capability | no generic target DML; no decision authority |
| Release authority | existing publication/activation/deployment authority | separate from version creation and learning approval |

Prohibited combinations: proposal creator approving or authorizing the same
proposal; agent/system approval; automatic approval; tenant user approving a
global mutation; learning principal becoming target curator; executor acting as
approver/authorizer; target policy authorizing its own relaxation. A reviewer
may not be the sole approver where the same person created the proposal. Global
targets require at least independent proposer and approver, plus target-curator
and release boundaries; higher-risk organizational separation may be imposed by
AdminApps policy.

## 11. AdminApps trusted authority boundary

AdminApps remains authoritative for identity, MFA, global roles, tenant access,
product access and relevant governance permissions. ISO Smart may retain only a
server-resolved, versioned authority decision reference and sanitized snapshot.
No local RBAC is invented.

Client-provided actor, role, tenant, permission, approval, MFA or authority is
never authoritative. Missing, stale, revoked, mismatched or unverifiable
authority fails before writing a review, decision or authorization. High-risk
global approval and authorization require fresh resolution under a later
explicit max-staleness policy; this v1 invents no TTL.

## 12. Tenant-to-global and cross-tenant boundary

Phase 21 proposals are tenant/Organization-scoped while all currently allow-
listed targets are global. Therefore every proposal seeking a future global
successor requires a **separate global-governance decision**. Tenant authority
can submit provenance but cannot approve, authorize, curate, publish or activate
the global target. Global review must evaluate representativeness, poisoning,
security and effect on every tenant without treating tenant evidence as global
fact.

No tenant proposal may directly influence another tenant or shared behavior.
Cross-tenant aggregation, anonymization or shared-learning analysis is a
**FUTURE SEPARATE GOVERNANCE GATE** and is not authorized by this boundary.

## 13. Application authorization boundary

A future `LearningApplicationAuthorization` must be immutable and bind exactly:

- authorization ID and version;
- one current exact proposal revision/hash;
- one exact approved decision and required reviews;
- target type, scope, ID, lineage, vN and material hash;
- one allow-listed target-specific capability and operation;
- trusted authorizer identity/authority decision reference/context version;
- target-specific policy and validation profile versions;
- issued/expiry times if policy defines them, revocation lineage and status;
- one-time idempotency identity and trace/correlation identifiers.

It contains no arbitrary field/value payload. It is not valid merely because an
approval exists. It is not transferable to a new proposal revision, target
version, capability or policy. Expired, revoked, consumed, stale or ambiguous
authorization fails closed. A source/policy-backed withdrawal creates an
append-only revocation record; history is not deleted.

## 14. Future vN to vN+1 invariant

A future successful application must preserve vN byte-for-byte and create a
new draft successor whose `previous_revision` is exactly vN and whose lineage
and immutable identity fields match target-specific rules. It must retain IDs,
versions and hashes linking to proposal, signals, Effectiveness lineage, review,
decision and authorization without copying Evidence bodies, prompts or secrets.

Creation does not imply publication, activation or deployment. Those remain
target-curator/release operations. Phase 22 does not prove or authorize the
transaction that creates vN+1.

## 15. Target-specific validation profiles

### ModelPolicy

Revalidate published current leaf, full hash, lineage/key, version uniqueness,
approved-model and data-class syntax, guardrail/human-gate schema and security
policy. Reject self-approval, guardrail removal, model allowlist expansion,
data-class broadening or human-gate relaxation unless a separate independent
governance path explicitly authorizes that exact change. Learning may never be
the authority for such relaxation.

### AgentDefinition

Revalidate published current leaf, full hash, lineage/key/name, purpose,
capability, autonomy ceiling and exact referenced published ModelPolicy.
Proposed successor must remain compatible with that exact policy. Any autonomy
increase, including A2→A3 or A3→A4, is outside this boundary and fails closed.

### KnowledgeLayerRule

Revalidate published current leaf, hash, exact KnowledgeLayer and
StandardEdition, lineage/key, logic/evidence schema, source provenance and
classification. Classification must remain `non_certifiable_guidance`; no
RequirementControl or binding semantics may be modified. Global normative
curation remains mandatory.

### Prompt/rule bundle and retrieval

Not eligible. A future gate must first establish governed target identities,
immutable versions/hashes, curator/release lifecycle and injection/secret or
namespace/source/tenant controls. Provenance strings are not mutation targets.

## 16. Idempotency, concurrency and TOCTOU

The durable application identity is the tuple:

```text
proposal revision/hash + decision ID + authorization ID + target vN/hash
+ target-specific capability/version
```

The same tuple can claim at most one successor. Exact replay returns the same
recorded result; the same idempotency key with different material is conflict.
Two application attempts serialize to one winner; later attempts are replay or
stale conflict, never a second successor.

Required future lock order is authorization/idempotency claim, proposal current
revision, decision/revocation state, exact target leaf, target lineage successor
constraint, then event/audit/outbox. Two approvers may create independent review
evidence, but only one effective decision per exact decision policy identity.
A proposal correction racing approval makes the old proposal ineligible for the
new revision. Target successor racing application yields stale target. Revocation
racing application is serialized at the authorization claim; revocation wins
before claim, while a completed atomic application remains historical fact.

Immediately before any future mutation, inside the same transaction, revalidate
proposal exact/current state, decision, authority, authorization/revocation,
target identity/version/hash/current leaf and every target-specific invariant.
Unknown or changed state rolls back with zero target effect.

## 17. Event and immutable audit design

Minimum future governance events to evaluate at implementation gate:

- `learning_proposal.reviewed` v1 for immutable review completion, including
  proposal revision/hash and categorical review result;
- `learning_proposal.decision_recorded` v1 for the exact governance decision;
- `learning_application.authorized` v1 for a separately issued exact
  authorization.

No `learning_application.completed` event is authorized until a later target-
application gate proves an application transaction. Target successor creation
must use a target-owned event, separate from proposal governance events. Existing
`learning_proposal.created` is not overloaded.

Audit must reconstruct who proposed, reviewed, approved, authorized and—only in
a later gate—applied; exact proposal/target versions and hashes; authority
provenance; outcome/reason; successor ID; and trace/event/outbox IDs. Store IDs,
hashes, categorical outcomes and sanitized rationale, never raw Evidence,
prompts, tokens, credentials, secrets or unnecessary PII.

## 18. Compensation, effectiveness and release

Deletion or overwrite of vN+1 is not rollback. A reversible target requires a
new independently governed successor restoring or replacing prior semantics.
If semantic reversibility and safe disablement cannot be demonstrated for a
target, that target remains NOT READY for application.

Future evaluation of a learning-originated change is separate from the promoted
EffectivenessCheck v1 scope. No automatic signal/proposal generation or feedback
loop follows such evaluation.

Version creation, publication, activation and deployment are separate states.
The current ModelPolicy, AgentDefinition and KnowledgeLayerRule commands already
separate draft successor creation from publication; activation/deployment is
not sufficiently modeled and remains a blocker to any later application-release
authorization, not to this inert foundation.

## 19. Security capability matrix

`R` = target-scoped read if authorized; `C` = narrow create-successor capability
only in a later target gate; `D` = denied.

| Principal | Select proposal/governance | Select target | Create successor | Publish | Activate | Delete history | Generic update |
|---|---:|---:|---:|---:|---:|---:|---:|
| Learning proposer | tenant R | reference R | D | D | D | D | D |
| Learning reviewer | scoped R | R | D | D | D | D | D |
| Learning approver | scoped/global R | R | D | D | D | D | D |
| Application authorizer | exact R | exact R | D | D | D | D | D |
| Future application executor | exact R | exact R | C only if separately granted | D | D | D | D |
| Model/agent target curator | governance R | R | existing curator path | existing separate path | D unless separately modeled | D | D |
| Normative curator | governance R | R | existing KnowledgeLayer path | existing separate path | D unless separately modeled | D | D |
| Release authority | release R | R | D by default | target-specific | target-specific | D | D |

The learning principal never receives protected-target DML. Historical DELETE
and generic UPDATE remain denied for every ordinary principal.

## 20. Future implementation acceptance gates

- [x] No generic mutation primitive is permitted.
- [x] Exact proposal revision/hash and exact target vN/hash are mandatory.
- [x] Target drift and proposal correction fail closed.
- [x] Review, decision, application authorization and application are separate.
- [x] Approval and authorization cause zero target mutation.
- [x] Separation of duties and prohibited combinations are explicit.
- [x] AdminApps authority is preserved; client authority is rejected.
- [x] Tenant-to-global mutation and cross-tenant learning are prohibited.
- [x] Target-specific capability and validation profiles are required.
- [x] vN remains immutable; any future result is draft vN+1.
- [x] Idempotency, concurrency, revocation and TOCTOU semantics are defined.
- [x] Autonomy escalation, policy self-modification and normative mutation are prohibited.
- [x] Data minimization, event/audit separation and compensation are defined.
- [x] Publication/activation/deployment remain separate or blocked.
- [ ] A later foundation gate must prove additive schema, RLS, grants, atomicity,
      rollback and concurrency without target DML.
- [ ] A still-later target-specific gate must prove one safe application
      capability before any successor can be created.

## 21. Change control

This v1 is immutable once referenced. Correction or withdrawal uses a successor
boundary and preserves this record. Any target application, new target type,
cross-tenant analysis, authority combination, autonomy change, generic writer,
new runtime executor, application event, publication/activation/deployment or
external effect requires a separate explicit Product Policy and security/
implementation gate.
