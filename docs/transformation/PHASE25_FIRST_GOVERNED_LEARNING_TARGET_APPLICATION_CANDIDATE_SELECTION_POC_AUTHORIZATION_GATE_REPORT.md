# Phase 25 — First Governed Learning Target Application Candidate Selection + Ephemeral POC Authorization Gate

- Date: 2026-08-25
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: source, Product Policy, security and POC-authorization design gate
- Runtime/schema/database/target effects: **ZERO**
- Migration 0021: **ABSENT**
- Verdict: **PHASE 25 — NOT PROMOTED**

## 1. Verdict

**PHASE 25 — NOT PROMOTED.**

Exactly zero of the three Phase 24.2 candidates passes every mandatory gate.
All three fail the mandatory governed-compensation gate under the actual
promoted target lifecycle:

1. the first application result must be `draft`, inactive and unpublished;
2. proposal creation and governance accept only an exact **published current
   leaf** as a target;
3. every canonical target curator and database predecessor trigger accepts only
   a **published** predecessor; and
4. predecessor uniqueness plus current-leaf checks prevent bypass by branching
   another successor from vN.

Therefore an inert vN+1 cannot be the target or predecessor of the required
separately governed vN+2 compensation. ModelPolicy and AgentDefinition have an
additional blocker: restoring prior semantics would respectively add an
approved model or raise autonomy, neither of which is an authorized Phase 24.2
operation. Compensation is mandatory and is not relaxed merely to select the
otherwise preferable KnowledgeLayerRule candidate.

No target, operation or delta schema is selected or authorized for application.
No Product Policy or ADR implying selection is created.

## 2. Entry baseline

Phases 21, 22, 23, 24.1 and 24.2 are promoted at entry. Migration 0020 is the
latest migration and the exact-delta foundation remains inert. The following
entry guarantees were directly reconciled:

- proposal-owned canonical delta bytes and SHA-256;
- `iso-smart-learning-delta-canonical-v1`;
- direct Proposal -> Review -> Decision -> Authorization binding;
- permanent `LEGACY_INERT` classification for incomplete legacy tuples;
- three exact target-operation v1 contracts;
- zero target application executor, receipt, application event or target DML
  grant; and
- published target history, predecessor uniqueness and separate publication.

The worktree was already materially dirty. All pre-existing backend/frontend
changes, the modified SQLite file and the known Sidebar whitespace were left
untouched.

## 3. Source and Product Policy reconciliation

All ten authoritative artifacts were read directly. SHA-256 read all exact
bytes; DOCX and XLSX ZIP members passed complete CRC reads; their XML was
inspected; Draw.io XML, Mermaid, JSON, SQL, OpenAPI, both CSVs and LEEME were
parsed/read directly.

The evidence categories are kept distinct:

- **AUTHORITATIVE SOURCE FACT:** the sources separate Effectiveness, learning,
  human decision, A0-A4, guardrails, model/rule versions, Knowledge Layers and
  non-destructive normative history. They do not authorize automatic target
  mutation, application, a reverse operation or cross-tenant learning.
- **PRODUCT POLICY DECISION:** governed learning remains human-governed,
  target/version exact, global-authority controlled, non-normative, no-autonomy-
  increase, no-human-gate-weakening and non-runtime-effective until separate
  publication/activation.
- **PROMOTED CODE/CONTRACT FACT:** Phase 24.2 defines three exact schemas and
  hashes; current target services create only draft successors from published
  current leaves; database constraints prevent forks and destructive history.
- **DESIGN INFERENCE:** a mandatory vN+2 compensation cannot be claimed while
  the only permitted vN+1 remains ineligible as both proposal target and
  predecessor. A later blocker-closure policy/versioning design is required.

No source statement is represented as a new ISO requirement and no previous
authorization is broadened.

## 4. Source/policy/implementation matrix

| Field | Candidate A — ModelPolicy | Candidate B — AgentDefinition | Candidate C — KnowledgeLayerRule |
|---|---|---|---|
| TARGET | `ModelPolicy` | `AgentDefinition` | `KnowledgeLayerRule` |
| EXACT OPERATION | approved-model removal only | strict autonomy reduction only | validated source-reference locator correction only |
| AUTHORITATIVE SOURCE SUPPORT | model/version/guardrail/human-gate provenance | A0-A4, capability, model-policy and human-gate separation | versioned non-certifiable Knowledge Layer guidance and source provenance |
| PRODUCT POLICY SUPPORT | restrictive removal; all policy security fields frozen | strict decrease; no capability/purpose/policy change | provenance-only, guidance/classification/linkages frozen |
| PHASE 24.2 CONTRACT | exact v1 schema exists | exact v1 schema exists | exact v1 schema exists |
| CURRENT VERSIONING | lineage/version/unique predecessor | lineage/version/unique predecessor | layer + lineage/rule key/version/unique predecessor |
| CURRENT PUBLICATION STATE | `draft|published` | `draft|published` | `draft|published` |
| CURRENT CURATOR | agent catalog curator | agent catalog curator | normative curator |
| CURRENT CANONICAL COMMAND | `revise_model_policy` | `revise_agent_definition` | `revise_knowledge_layer_rule` |
| GLOBAL/TENANT SCOPE | global | global | global |
| SECURITY-SENSITIVE FIELDS | models, data classes, guardrails, human gates | purpose, capability, autonomy, ModelPolicy | logic, evidence expectation, source reference, classification and bindings |
| ALLOWED DELTA | remove exact already-approved model identifiers | `0 <= new < current <= 4` | change locator only under exact edition/source hash |
| FROZEN FIELDS | lineage/key/data classes/guardrails/human gates/status semantics | lineage/key/name/purpose/capability/ModelPolicy/status semantics | layer/lineage/key/logic/evidence/classification/bindings/edition linkage |
| SUCCESSOR SEMANTICS | exact published current vN -> draft vN+1 | exact published current vN -> draft vN+1 | exact published current vN -> draft vN+1 |
| DRAFT/INACTIVE POSSIBLE? | yes | yes | yes |
| ROLLBACK/COMPENSATION | blocked: draft predecessor forbidden; restoration is additive | blocked: draft predecessor forbidden; restoration raises autonomy | semantically same surface, but draft predecessor/target forbidden |
| APPLICATION READINESS | FAIL | FAIL | FAIL |
| BLOCKER | mandatory compensation and reverse-operation authority | mandatory compensation and no-autonomy-increase | mandatory compensation lifecycle |
| RATIONALE | no authorized operation can restore M; vN+1 cannot lead to vN+2 while inert | no authorized operation can restore prior ceiling; vN+1 cannot lead to vN+2 while inert | locator restoration is narrow, but promoted lifecycle makes vN+2 impossible without publication or a new versioning contract |

## 5. Candidate safety matrix

`PASS WITH RESTRICTIONS` is not a mandatory-gate pass. A mandatory `FAIL`
eliminates the candidate.

| Mandatory area | ModelPolicy | AgentDefinition | KnowledgeLayerRule |
|---|---|---|---|
| Exact operation/schema/canonical delta | PASS | PASS | PASS |
| Exact Proposal/Review/Decision/Authorization tuple | PASS | PASS | PASS |
| Source + Product Policy support | PASS | PASS | PASS |
| vN immutable; no overwrite/delete/rebinding | PASS | PASS | PASS |
| One draft vN+1; no fork | PASS | PASS | PASS |
| Publication/activation separate | PASS | PASS | PASS |
| Runtime invariance expressible | PASS | PASS | PASS |
| Target/delta hash and drift fail-closed | PASS | PASS | PASS |
| Target-specific least-privilege capability possible | PASS | PASS | PASS |
| Canonical curator reuse without duplicate rules | PASS | PASS | PASS |
| Idempotency/concurrency/TOCTOU/atomicity designable | PASS | PASS | PASS |
| Receipt/event/audit/forced rollback designable | PASS | PASS | PASS |
| Compensation through separately governed vN+2 | **FAIL** | **FAIL** | **FAIL** |
| Compensation stays within authorized safe governance | **FAIL** | **FAIL** | **FAIL** |
| No autonomy/human-gate/guardrail weakening | PASS | PASS | PASS |
| No normative/cross-tenant/external effect | PASS | PASS | PASS |
| **Outcome** | **FAIL** | **FAIL** | **FAIL** |

## 6. ModelPolicy analysis

The forward delta is exact and subtractive. Phase 24.2 deterministically removes
only existing list members and structurally excludes data classes, guardrails
and human-gate rules. `revise_model_policy` locks a published current leaf,
creates a draft, and publication is a separate command. Runtime starts runs
against explicitly supplied published ModelPolicy IDs; no latest-policy lookup
or automatic AgentDefinition relink was found.

The candidate nevertheless fails compensation twice:

1. vN+1 is draft, while both `revise_model_policy` and the database revision
   trigger require a published predecessor; and
2. restoring model M is additive relative to vN+1, while the only promoted
   exact operation is removal-only. No exact add operation, stronger reverse
   policy, delta schema or capability exists.

Publishing vN+1 merely to enable compensation is outside the POC and would
violate the mandatory inactive/unpublished boundary. Forking another successor
from vN is prevented by `previous_revision_id UNIQUE` and current-leaf checks.

**Result: FAIL.**

## 7. AgentDefinition analysis

The forward predicate is canonical and strict:
`0 <= new_autonomy_max < vN.autonomy_max <= 4`. Purpose, capability, name and
ModelPolicy linkage are absent from the delta and frozen. The curator creates a
draft from a locked published current leaf; runtime uses an exact published
AgentDefinition ID and exact ModelPolicy ID rather than adopting a latest row.

The candidate fails because vN+1 cannot be a predecessor while draft, and
restoring the prior ceiling would be an autonomy increase relative to vN+1.
The governed-learning policy has no authorized autonomy-increase operation and
no stronger reverse gate. Accepting a non-compensatable inert draft is expressly
insufficient because compensation is mandatory.

**Result: FAIL.**

## 8. KnowledgeLayerRule analysis

Phase 24.2 mechanically separates the source reference from substantive
guidance: only `source_reference` exists in the payload, both references must
use the exact `iso-smart-source-ref-v1` grammar, edition UUID and source hash
must remain equal, and only the locator may differ. `logic_json`,
`evidence_expectation`, classification, KnowledgeLayer/StandardEdition and all
existing bindings remain frozen. This is the smallest semantic surface and the
only candidate whose conceptual forward and reverse deltas stay within the same
operation profile.

Creating vN+1 does not publish it and does not change existing exact
KnowledgeLayerRule references used by AgentRun/Recommendation. Runtime reads
exact published rule IDs. However, the same promoted lifecycle blocks the
mandatory reverse correction: a draft vN+1 is neither an eligible proposal
target nor a permitted predecessor for vN+2. The operation could restore the
locator only after vN+1 publication, which this POC cannot perform.

**Result: FAIL / nearest candidate, but not selectable.**

## 9. Mandatory-gate result

All 33 mandatory candidate requirements were evaluated. Every non-compensation
area passes at this design level under the Phase 24.1 Architecture D
restrictions. The two mandatory compensation checks fail for every candidate.

The exact common failed assertions are:

- `[ ] compensation through vN+2`;
- `[ ] compensation does not violate governance`; and
- consequently `[ ] application readiness`.

Candidate-specific additional failures are:

- ModelPolicy: reverse restoration is capability-expanding and has no exact
  authorized operation;
- AgentDefinition: reverse restoration raises autonomy and conflicts with the
  current no-autonomy-increase rule.

No gate is waived or converted to `PASS WITH RESTRICTIONS`.

## 10. Safety tie-break

The mandatory tie-break is **not reached** because it applies only when more
than one candidate receives full PASS. KnowledgeLayerRule would rank first on
same-surface compensation, semantic size and absence of autonomy/human-gate
fields, but ranking cannot cure a mandatory FAIL and is not selection.

## 11. Selection and exact target contract

- Selected candidate: **NONE**
- Exact target: **NONE**
- Authorized operation ID/version: **NONE**
- Authorized delta schema: **NONE**
- Authorized target-specific capability: **NONE**
- Phase 26 application POC: **NOT AUTHORIZED**

The three existing comparison identities remain inert contracts only:

| Candidate | Operation ID | Version | Delta schema | Phase 25 state |
|---|---|---|---|---|
| ModelPolicy | `learning.model_policy.approved_models.remove` | `v1` | `learning-model-policy-approved-model-removal-delta-v1` | evaluated, not selected |
| AgentDefinition | `learning.agent_definition.autonomy.reduce` | `v1` | `learning-agent-definition-autonomy-reduction-delta-v1` | evaluated, not selected |
| KnowledgeLayerRule | `learning.knowledge_layer_rule.source_reference.correct` | `v1` | `learning-knowledge-layer-rule-source-reference-correction-delta-v1` | evaluated, not selected |

## 12. Allowed delta and frozen fields

No Phase 25 application delta is allowed. Phase 24.2 validation contracts remain
readable and inert. Every target field, row and runtime selection remains
frozen. No caller payload, default, latest lookup or application-time
recalculation is authorized.

## 13. vN/vN+1 and runtime invariance proof design

The forward design is otherwise expressible for all candidates:

- lock the exact published current vN and recompute its canonical full-row hash;
- invoke one target-specific operation;
- retain vN byte-for-byte;
- create exactly one vN+1 with exact predecessor and lineage;
- require `status=draft`, `published_at=NULL`;
- assert no publication/activation/current-pointer change; and
- compare exact runtime-selected IDs before/after.

Runtime assertions would be:

- ModelPolicy: existing AgentDefinition linkage and explicit run policy ID are
  unchanged;
- AgentDefinition: explicitly selected published definition ID is unchanged;
- KnowledgeLayerRule: AgentRunInput/RecommendationBasis exact published rule
  IDs and bindings are unchanged.

These forward assertions do not resolve the vN+2 compensation blocker.

## 14. Exact governance chain, hashes and legacy boundary

Any future attempt would have to revalidate one identical immutable tuple:

```text
proposal ID/revision/material hash
+ canonical delta ID/canonicalization/schema/operation/version/delta hash
+ review IDs and review-set hash
+ approved decision
+ VALID authorization
+ exact target type/ID/lineage/version/hash
```

`delta_hash` must be recomputed from stored canonical bytes using
`iso-smart-learning-delta-canonical-v1` and equal Proposal, Review, Decision and
Authorization. The target hash must be recomputed from the exact target row.
Any mismatch is stale/deny.

Incomplete or old tuples remain permanently `LEGACY_INERT`. No default,
backfill, upgrade, rebinding or old `revise_*` alias gains eligibility.

## 15. Target drift, TOCTOU, idempotency and concurrency

The future fail-closed lock/revalidation sequence remains:

```text
Proposal -> Review -> Decision -> Authorization -> application identity
-> exact target lineage/current-leaf lock -> target hash
-> canonical delta bytes/hash/profile -> exact target capability
```

The designed application identity is:

```text
proposal revision + decision + authorization + target vN/hash
+ operation ID/version + delta hash
```

Exact replay would return one immutable receipt/result; changed provenance would
conflict. Two attempts against vN must serialize to one successor and one
replay/conflict/stale result. `previous_revision_id UNIQUE` is the final fork
defense. These controls are not implemented or authorized in Phase 25.

## 16. Architecture D and curator boundary

The only acceptable future boundary remains:

```text
one trusted application service / one physical connection / one outer transaction
-> governance revalidation
-> target lock + exact hash/profile validation
-> one target-specific canonical database primitive
-> canonical curator semantics
-> one inert successor + target curation audit
-> immutable application receipt/audit
-> one commit
```

The current broad human curator commands are not application authority. A future
implementation would have to factor the shared successor rules into the
canonical primitive and make the human and application paths delegate to it;
copying the rules into parallel Python/SQL paths is prohibited.

## 17. Least privilege and target-specific security matrix

No Phase 25 principal or grant is created. The required future principal is a
dedicated global target-application executor, distinct from proposer, reviewer,
approver, authorizer, Effectiveness reviewer, curator and release authority.

Candidate capability identifiers, if a later blocker-closure gate ever selects
one, must equal the exact operation ID/version above. They may not alias
`revise_*`, accept a target type, field/value, arbitrary payload or wildcard.

| Principal | Read exact target | Generic I/U/D | Candidate-specific successor capability | Publish | Activate | Approve | Authorize |
|---|---:|---:|---:|---:|---:|---:|---:|
| APP | yes | denied | denied | denied | denied | denied | denied |
| WORKER | yes | denied | denied | denied | denied | denied | denied |
| Learning proposer | exact reference | denied | denied | denied | denied | denied | denied |
| Learning reviewer | exact read | denied | denied | denied | denied | review only | denied |
| Learning approver | exact/global read | denied | denied | denied | denied | yes | denied |
| Learning authorizer | exact/global read | denied | denied | denied | denied | denied | yes |
| Future application executor | exact read | denied | **not authorized** | denied | denied | denied | denied |
| Agent catalog curator | catalog read | current scoped curator grants | existing human commands only | separate | denied | denied | denied |
| Normative curator | catalog read | current scoped curator grants | existing human commands only | separate | denied | denied | denied |
| Release authority | target read | denied by default | denied | target-specific | separately governed | denied | denied |

Any later `SECURITY DEFINER` function requires a dedicated NOLOGIN,
non-superuser, NOBYPASSRLS, NOINHERIT owner; fixed `search_path=pg_catalog`;
qualified objects; no dynamic SQL; PUBLIC revoke; exact executor EXECUTE only;
and no arbitrary target/operation/field/value argument.

## 18. Global governance and cross-tenant boundary

All three targets are global. Tenant-derived signal/proposal material is
evidence only. A future global mutation would require an exact global Decision,
global LearningApplicationAuthorization and global application actor/capability.
No tenant principal receives global target DML or derives global authority.

An inert unpublished successor would preserve Tenant B runtime behavior, but no
successor is authorized here. Cross-tenant aggregation, influence and automatic
adoption remain prohibited.

## 19. Publication and activation separation

All current curator workflows create a draft and publish separately. No hidden
publication trigger or application capability exists. Runtime paths require
explicit published IDs and do not select the new draft automatically.

Publication cannot be introduced as a compensation workaround: the first POC
explicitly prohibits it. Activation, deployment and runtime selection remain
separate and unauthorized.

## 20. Receipt, event and audit design

No receipt/event is authorized. A future immutable receipt would minimally bind
Proposal revision, Review, Decision, Authorization, operation/schema/hash,
vN and vN+1 IDs/versions/hashes, target curation audit/event, application audit,
actor, trace/timestamps and explicit `not published`/`not active` states. It
would never imply deployment.

Existing target curation ledgers are the current target-owned audit facts. A
later gate would have to decide whether a separate learning-application event
is semantically necessary. It may not use generic `target.updated` or conflate
authorization with application. No name is prematurely approved here.

## 21. Transaction and forced rollback design

If a target were eventually selected, one transaction would cover governance
locks, target lock/hash, delta validation, exact canonical curator primitive,
one inert successor, target ledger/event, receipt and application audit/event.
No external call is permitted.

Fault injection points remain:

1. after governance validation;
2. after target lock;
3. after delta validation;
4. before successor insert;
5. after successor insert;
6. after target curation event/ledger;
7. after target audit;
8. before receipt;
9. after receipt;
10. after application audit/event; and
11. immediately before commit.

Every injected failure must commit zero successor, receipt, event and audit
delta and leave vN unchanged. This is a design only, not an authorized Phase 26
test run.

## 22. Compensation blocker in detail

The promoted invariants form the following closed contradiction:

```text
first POC requires vN+1 = draft/unpublished
proposal target eligibility requires published current leaf
curator predecessor requires published revision
database predecessor trigger requires published revision
unique predecessor forbids a second branch from vN
therefore no separately governed vN+2 can be created from inert vN+1
```

For ModelPolicy, an additional exact reverse schema for model restoration would
be required and would be capability-expanding. For AgentDefinition, an exact
reverse schema would increase autonomy and needs a new stronger policy, not an
exception to the current prohibition. KnowledgeLayerRule can conceptually use
the same locator-correction surface in reverse, but it still needs a carefully
governed draft-successor-chain or equivalent versioning contract before it can
pass.

No delete, overwrite, fork, publication workaround or automatic compensation
is acceptable.

## 23. Threat matrix

| Threat | Control/evidence | Phase 25 result |
|---|---|---|
| malicious or substituted delta | proposal-owned exact bytes/schema/hash | closed by 24.2 |
| stale Proposal/Decision/Authorization | exact tuple and currentness revalidation | design retained |
| legacy bypass | positive complete-tuple eligibility only | closed |
| target drift/hash mismatch | current-leaf lock + full-row hash | design retained |
| operation/schema/version substitution | exact v1 tuple everywhere | closed |
| generic DML/function abuse | no executor/grant; exact future capability only | closed in Phase 25 |
| executor/curator escalation | separate principal, no membership/DML | future proof required |
| tenant-to-global/cross-tenant influence | global governance; tenant evidence only; draft-only | closed in Phase 25 |
| duplicate successor/fork | lock, idempotency and unique predecessor | target constraint present |
| hidden publication/activation/adoption | draft pair, explicit IDs, no publish/activate grant | forward design sound |
| guardrail/human-gate weakening | fields structurally frozen | closed |
| autonomy escalation | Agent forward strict decrease; reverse absent | reverse candidate blocked |
| normative contamination | KL logic/classification/bindings/edition frozen | closed |
| compensation abuse | separate chain required; no reverse path currently exists | **blocking, fail closed** |
| audit/receipt mismatch or partial commit | one transaction + fault matrix | future proof required |

## 24. Phase 26 acceptance plan status

The requested 50-test target-application plan is **not instantiated or
authorized** because there is no selected target. Doing so would silently turn
an eliminated candidate into implementation scope. The 50 categories in the
Phase 25 brief remain mandatory if and only if a later gate closes compensation
and selects exactly one target.

The next gate is limited to documentation/policy/versioning blocker closure and
must test its design on paper against:

1. draft vN+1 eligibility for a separately governed compensation proposal;
2. exact no-fork draft successor semantics;
3. unchanged publication/activation/runtime selection;
4. no delete/overwrite/rebinding;
5. reverse-operation exactness and safety;
6. ModelPolicy capability-expansion governance;
7. AgentDefinition autonomy-increase prohibition;
8. KnowledgeLayerRule same-surface reverse correction;
9. unchanged legacy inertness and hash chain; and
10. compatibility with one-connection Architecture D and least privilege.

No target application test or database mutation may occur in that blocker gate.

## 25. Product Policy and ADR

`FIRST_GOVERNED_LEARNING_TARGET_APPLICATION_POLICY_V1.md` was **not created**.
Its creation is conditional on exactly one full-PASS candidate.

No successor ADR was created because there is no selected target, capability or
POC authorization. Existing ADR history remains unchanged.

## 26. Migration and source integrity

Migrations 0001-0020 match the promoted SHA-256 values exactly: **20/20
MATCH**. Migration 0020 is
`491f21d3422c9c9a5866520f6623d3b9c9bea2139083f0128495dd7207d19894`.
No 0021 exists.

Authoritative sources match the manifest exactly: **10/10 MATCH**:

`8308bde9...`, `e0a59c91...`, `11c2b461...`, `952d8ac9...`,
`ecaecd25...`, `30e3c052...`, `de1b4899...`, `29ac5c2d...`,
`c41e847e...`, `eb42315c...`.

Frozen governance prerequisites match their promoted hashes, including governed
learning policy `7d9c2fe3...`, Phase 21 authorization `04458c4f...`, Phase 22
boundary `2d5beaeb...`, ADR-0012 `4fd6b330...`, Phase 21 `682dc465...`, Phase
22 `a94ba44e...`, Phase 23 `4cfe38a...`, Phase 24 `7b01976e...` and Phase 24.1
`c00577ad...`.

## 27. Protected-target invariance and runtime-change evidence

No database was opened and no target command was invoked. There is no target
row, successor, executor, receipt, event, grant, application claim or external
effect. ModelPolicy, AgentDefinition, KnowledgeLayerRule and normative catalog
state were not changed.

Protected implementation hashes at entry/final verification are:

| File | SHA-256 | Result |
|---|---|---|
| `backend/foundation/models.py` | `9dd94c945dd0c256c3872e82b45760b06c066a4364e3dc3d833d56c09645c244` | MATCH |
| `backend/foundation/agent_runtime.py` | `6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d` | MATCH |
| `backend/foundation/knowledge_layer.py` | `ad355cd34fa7a03f1ba30cbe2e78f8a1a8de7859d0b05be337639e2c1c4597c3` | MATCH |
| `backend/foundation/learning_delta.py` | `8a3a2187567737ad2034ac6abf695dd73ce356356d3e1dd82c2e61f7fc0944cd` | MATCH |
| `backend/foundation/governed_learning.py` | `ce3fa7c87938c2e9a7253a722ce5de117f638c261e61d30033555d45179c8f52` | MATCH |
| `backend/foundation/learning_proposal_governance.py` | `d1239451fa698739aa52167b6746613ad705d57fd1c232f74c2e2ff43e0db74b` | MATCH |

The only intended Phase 25 change is this documentation report. No expensive
PostgreSQL/backend suite was rerun because no runtime, schema, test or security
artifact changed.

## 28. Git hygiene

The entry status was recorded before modifications. Unrelated local work was
preserved. The known pre-existing trailing whitespace in
`frontend/src/components/Layout/Sidebar.jsx:28` remains outside this phase.
This report is checked independently for whitespace; repository-wide
`git diff --check` is reported with the unrelated pre-existing finding
separated.

## 29. Residual blockers

P1 blockers to any Phase 26 target application POC:

1. **Common lifecycle blocker:** an inert draft vN+1 cannot be governed as the
   exact target/predecessor of vN+2 compensation.
2. **ModelPolicy reverse-operation blocker:** restoration adds a model and no
   exact stronger governed reverse contract exists.
3. **AgentDefinition reverse-operation blocker:** restoration increases
   autonomy and conflicts with current governed-learning safety policy.
4. **KnowledgeLayerRule versioning blocker:** same-surface restoration is
   semantically plausible but impossible under published-predecessor-only
   versioning while vN+1 remains inert.

There are zero P0 blockers because no application authority exists. These P1s
must be closed without weakening compensation, runtime invariance, publication,
activation, autonomy, human-gate or normative safety.

## 30. Final promotion verdict

**PHASE 25 — NOT PROMOTED.**

No ephemeral Phase 26 governed learning target application POC is authorized.
Promotion cannot be based on the likely KnowledgeLayerRule preference while its
mandatory vN+2 compensation remains impossible.

| Candidate/component | State | Evidence | Risk/next action |
|---|---|---|---|
| ModelPolicy removal | FAIL | exact forward v1; draft predecessor forbidden; reverse adds model | design stronger reverse governance and inert compensation lifecycle, or eliminate |
| AgentDefinition autonomy reduction | FAIL | exact forward v1; draft predecessor forbidden; reverse raises autonomy | retain prohibition unless separate stronger policy proves safe reversal |
| KnowledgeLayerRule source-reference correction | FAIL / NEAREST | forward/reverse share locator-only surface, but draft vN+1 cannot lead to vN+2 | design exact no-fork draft compensation lineage without publication |
| Architecture D | RETAINED | one connection + dedicated canonical DB primitive | do not implement until one target passes |
| Legacy governance | PASS / INERT | complete-tuple positive eligibility; no backfill | preserve permanently |
| Migrations 0001-0020 | PASS | 20/20 hashes match; no 0021 | freeze |
| Authoritative sources | PASS | 10/10 direct read/hash match | preserve byte-for-byte |
| Protected targets/runtime | UNCHANGED | docs-only; protected hashes match | retain zero-effect boundary |
| Product Policy/ADR | NOT CREATED | conditional on exact single selection | create only after full PASS |
| Phase 26 application POC | NOT AUTHORIZED | zero candidates pass compensation | run blocker-closure design gate only |

## NEXT_CODEX_PROMPT

Execute PHASE 25.1 — INERT SUCCESSOR COMPENSATION + REVERSE-OPERATION BLOCKER
CLOSURE DESIGN GATE exclusively in `/home/felipe/proyectos/isosmart`. Treat
Phase 25 as NOT PROMOTED and preserve migrations 0001-0020, all ten
authoritative sources, every governance artifact, target model, curator service,
normative catalog and promoted report byte-for-byte. This is documentation and
Product Policy design only: do not select or apply a target, create migration
0021, create vN+1/vN+2, executor, receipt, event, function, role or grant, use a
database, publish, activate, deploy or create external effects. Address only
the exact compensation blockers: the current proposal and curator contracts
accept only published current leaves, while the first POC must keep vN+1 draft
and unpublished; unique predecessor/current-leaf rules forbid branching from
vN; ModelPolicy restoration is additive; AgentDefinition restoration raises
autonomy; KnowledgeLayerRule locator restoration can conceptually stay within
the same provenance-only surface but cannot descend from an inert draft.
Compare fail-closed designs for a separately governed, no-fork draft-successor
compensation lineage or an equivalent additive state/version contract without
publication, activation, overwrite, delete, rebinding, generic DML, runtime
adoption or business-rule duplication. Define exact proposal eligibility,
target hashing, predecessor/current-leaf semantics, forward and reverse
operation identities/versions/schemas, stronger authority where an operation is
expansive, idempotency, concurrency, TOCTOU, least privilege, Architecture D
reuse, receipt/audit implications and rollback tests. Do not weaken the
no-autonomy-increase, human-gate, guardrail, normative, global-governance or
cross-tenant boundaries to rescue a candidate. Re-evaluate all three candidates
only for compensation readiness; emit PROMOTED only if at least one exact
compensation contract can later be implemented while keeping every successor
inactive/unpublished and all mandatory Phase 25 invariants intact. Otherwise
emit NOT PROMOTED with the remaining exact blockers and return exactly one
self-contained next prompt that still does not implement target application.
