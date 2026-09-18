# KnowledgeLayerRule publication, activation and runtime-adoption policy v1

- Policy ID: `knowledge-layer-rule-publication-activation-runtime-adoption/v1`
- Version: `v1`
- Date: 2026-09-02
- Owner/system authority: ISO Smart Product Governance
- Nature: versioned, non-normative Product Policy
- Status: **APPROVED FOR INERT FOUNDATION IMPLEMENTATION GATE ONLY**
- Target: `KnowledgeLayerRule` only
- Runtime/schema/data effect in this policy gate: **ZERO**

## 1. Decision and authorization limit

ISO Smart adopts four distinct facts for every future governed
`KnowledgeLayerRule` release:

```text
VERSION_CREATED != VERSION_PUBLISHED != VERSION_ACTIVATED != RUNTIME_ADOPTED
```

This policy closes the Phase 27 publication/runtime-eligibility design blocker
and authorizes only a later gate to implement an **inert additive foundation**.
It does not authorize migration 0022 in this phase, publication, activation,
runtime adoption, runtime cutover, production, deployment, another target,
another learning operation, cross-tenant learning, automatic learning or an
external effect.

Phase 26 vN+1 and vN+2 remain draft, unpublished, not activated and not
runtime-adopted. This policy must never be interpreted as approval to change
either revision.

## 2. Source and normative boundary

The ten authoritative source artifacts support versioned Knowledge Layers,
exact rule/model provenance, governed agent execution, Human Decision Gates,
effectiveness and retained history. They do not define the publication,
activation or runtime-adoption workflow established here. These controls are
ISO Smart Product Policy, not ISO requirements.

No transition may create or alter `Standard`, `StandardEdition`, `Clause`,
`RequirementControl`, certifiable coverage or licensed normative content.
`KnowledgeLayerRule` remains global, non-certifiable guidance.

## 3. Four-state semantics

| Fact | Exact meaning | Does not imply |
|---|---|---|
| `VERSION_CREATED` | An exact append-only rule revision exists with lineage, predecessor, version and full-row hash. It starts `draft,published_at=NULL`. | Publication, activation or runtime eligibility |
| `VERSION_PUBLISHED` | An independent global publication decision approves the exact revision/hash as catalog content after curation. | Activation, runtime selection or deployment |
| `VERSION_ACTIVATED` | An independent global activation decision declares the exact published revision eligible to be considered by release governance. | Any runtime has adopted it |
| `RUNTIME_ADOPTED` | An independent release decision binds one exact activated revision to one exact global runtime-configuration transition. | Selection by newest publication, lineage head or version order |

Every transition is explicit, separately authorized, idempotent, append-only
and attributable. No transition automatically invokes the next.

## 4. Current compatibility boundary

Today publication updates `KnowledgeLayerRule.status` from `draft` to
`published`, sets `published_at` and appends a curation audit. AgentRun and
Recommendation callers supply an exact rule ID; service and database guards
accept it when that exact row is published. There is no latest-wins selector,
active/current pointer, activation artifact or adoption artifact.

A later additive migration may preserve `status/published_at` as a compatibility
projection, but post-cutover runtime must not use those columns as sufficient
eligibility. For a native publication, the immutable publication record is the
authoritative decision; a status/record mismatch is `INCONSISTENT`.

## 5. Publication contract

Future native publication creates exactly one immutable
`KnowledgeLayerRulePublication` for one exact revision. The publication and
the existing compatibility `draft -> published` projection, bounded event,
outbox and audit must commit atomically.

The record binds at least:

- publication ID and operation/version;
- exact KnowledgeLayer ID, rule lineage/key, rule revision ID/version;
- complete rule-row hash and substantive semantic fingerprint;
- exact source `StandardEdition` and source hash;
- curation approval/evidence IDs and hashes;
- publication policy ID/version/hash;
- AdminApps-resolved actor, authority decision reference and context version;
- reason, trace/correlation, idempotency/material hash; and
- publication, event, outbox, audit and recorded timestamps.

There is one successful native publication record per exact revision. Exact
replay returns it; changed material conflicts. Denied/failed attempts belong in
security/operation audit, not as a second successful publication. Multiple
different revisions in one lineage may remain historically published because
publication is not a mutable current pointer.

## 6. Publication preconditions

Immediately before commit, under the exact revision/lineage lock, publication
must revalidate:

1. exact draft revision, lineage, predecessor, version and full-row hash;
2. exact semantic fingerprint and source-reference grammar;
3. published source edition ID/hash and complete provenance;
4. current lineage-leaf status and no stale/intervening successor;
5. no normative contamination or certifiability change;
6. the applicable Product Policy and governance hash/version;
7. independent human/global curator approval;
8. fresh AdminApps-resolved publication authority; and
9. absence of a conflicting publication claim/record.

Any drift, missing evidence, unknown policy, stale target or authority failure
fails closed. The Phase 26 application executor and
`LearningApplicationAuthorization` never satisfy publication authority.

## 7. Activation contract

Activation requires its own immutable `KnowledgeLayerRuleActivation`; a
mutable `is_active` flag is not authoritative history. It binds:

- activation ID and operation/version;
- exact publication evidence ID, rule revision ID/version/hash and semantic
  fingerprint;
- exact KnowledgeLayer/rule lineage;
- fixed scope `global_knowledge_layer_runtime` for that rule lineage;
- exact predecessor activation supplied by the request, if any;
- release/compatibility validation and governance policy/hash;
- AdminApps-resolved activator authority and actor;
- reason, optional source/policy-backed `effective_from`, trace and timestamps;
- idempotency/material hash; and
- exact activation event, outbox and immutable audit IDs.

This architecture defines no environment-, organization-, tenant- or
agent-specific rule activation. Such scopes require a later policy. Activation
does not update rule content, bindings, provenance or runtime configuration.

## 8. Activation preconditions

Activation revalidates under lock:

1. exact native publication record or truthful legacy publication evidence;
2. exact published revision, target hash and semantic fingerprint;
3. exact expected predecessor activation and unforked activation stream;
4. no stale/superseded competing activation decision;
5. runtime contract compatibility;
6. activation/release policy and governance hash/version; and
7. fresh independent AdminApps-resolved activation authority.

An unpublished revision can never be activated. Same-revision exact replay is
idempotent. Competing revisions against the same predecessor serialize: one
wins and the other is stale/conflict. A recovery activation of an older
published revision is permitted only through an explicit recovery policy and
incident/reason provenance; it is never inferred from target lineage.

## 9. Runtime-adoption contract

Future runtime selection is represented by one immutable
`KnowledgeLayerRuleRuntimeAdoption`. The record is the sole authoritative
adoption evidence; no separate adoption Receipt is created. Claims, events and
audits support reconciliation but do not duplicate its authority.

The adoption binds at least:

- adoption ID, kind (`NATIVE`, `RECOVERY` or approved `LEGACY_BOOTSTRAP`) and
  operation/version;
- exact global rule scope and rule lineage;
- exact activation ID and publication evidence;
- exact KnowledgeLayerRule revision ID/version/hash and semantic fingerprint;
- exact predecessor adoption ID supplied by the release request;
- adoption/release authority and AdminApps decision provenance;
- deployment/release/configuration reference and immutable hash;
- compatibility result, governance policy/hash, reason and incident reference
  when applicable;
- optional source/policy-backed `effective_from`;
- trace/correlation, idempotency/material hash and timestamps; and
- exact adoption event, outbox and immutable audit IDs.

Normal and recovery adoptions require an exact Activation. Only an explicitly
approved `LEGACY_BOOTSTRAP` may omit activation, and its database constraint
must require the exact truthful legacy fields in section 13 instead.

## 10. Exact-ID runtime resolution

After a separately governed cutover, trusted release configuration supplies
one exact `runtime_adoption_id`. Runtime resolves:

```text
exact runtime_adoption_id
  -> exact immutable adoption
  -> exact activation (except truthful LEGACY_BOOTSTRAP)
  -> exact publication evidence
  -> exact KnowledgeLayerRule revision and hash
```

The scope, hashes, policy/configuration reference and authority state must all
match. Missing, disabled, mismatched or unknown adoption fails closed.

Runtime is forbidden to fall back to greatest/max version, newest created/
published/activated/adopted row, lineage head/leaf, most recent publication or
an implicit current pointer. Historical AgentRunInput and RecommendationBasis
continue to identify their exact rule IDs and are never rewritten.

## 11. Adoption lineage and no pointer rewind

Runtime-adoption lineage is distinct from rule-version lineage:

```text
Rule lineage:      vN -> vN+1 -> vN+2
Adoption lineage:  A1 -> vN; A2 -> vN+1; A3 -> vN (recovery)
```

Each adoption supplies and references its exact predecessor. The predecessor
may have at most one successor in the same scope. A recovery creates A3 and
retains A1/A2; it never updates A2, rewrites target lineage or silently sets a
pointer back to vN. Trusted release configuration switches only by distributing
the newly approved exact adoption ID.

## 12. Append-only evidence and events

Publication, activation, adoption and recovery records are immutable. Each
successful boundary creates a distinct bounded global event:

- `knowledge_layer_rule.published` v1;
- `knowledge_layer_rule.activation_recorded` v1; and
- `knowledge_layer_rule.runtime_adopted` v1.

The application event `knowledge_layer_rule.source_reference_corrected` is not
reused. Events contain IDs, hashes, categorical state, scope, authority
references and trace only—no licensed text, Evidence body, prompts or secrets.
Event/outbox/audit are atomic with their governing artifact, but dispatch does
not trigger the next governance stage.

## 13. Legacy history and truthful bootstrap

No historical AgentRun, Recommendation, Binding, rule, curation audit or Phase
26 Receipt is changed. Existing published rows must not be backfilled as if
they passed the new workflow.

A publication-evidence row may use kind `LEGACY_EVIDENCE_IMPORT` only when it
identifies the pre-existing exact `status/published_at`, curation audit (when
present), rule hash and import manifest. It explicitly records that no new
publication decision occurred. It cannot carry invented policy approval,
actor, activation or decision timestamps.

If continuity requires importing the pre-existing configured runtime vN, a
separately approved `LEGACY_BOOTSTRAP` adoption must state:

- pre-existing exact rule ID/version/hash and global lineage;
- exact legacy publication evidence;
- pre-existing trusted runtime-configuration reference/hash;
- migration manifest and bootstrap authority;
- `activation_id=NULL` and `historical_activation_claim=false`;
- no predecessor unless a truthful imported predecessor exists; and
- trace/import timestamp distinct from the unknown historical selection time.

This policy defines the truthful shape but does not authorize creating such a
record. The implementation/cutover gate remains blocked unless Product
Governance approves the exact legacy inventory and bootstrap. No governed
learning successor may be inferred or bootstrapped automatically.

## 14. Incremental migration and compatibility path

The permitted future path is:

1. additive migration 0022+ creates inert tables, constraints, RLS/ACLs,
   append-only guards, typed commands, reconciliation reads and capability
   fences; runtime remains unchanged and no business row is inserted;
2. separately inventory exact legacy publication/runtime configuration and
   obtain explicit bootstrap/cutover authorization;
3. create only approved truthful legacy evidence/adoption records or create a
   new post-migration activation/adoption for the exact current vN;
4. validate an adapter that maps the trusted configured exact rule ID only to
   its pre-created exact adoption ID—never by lineage or publication search;
5. in a later runtime gate, change inputs/configuration to exact adoption IDs,
   fail closed on absence, and retain exact rule IDs in historical records; and
6. remove the compatibility path only after reconcile/rollback evidence.

Phase 26 vN+1/vN+2 are excluded from bootstrap and remain inert.

## 15. Authorities and separation of duties

All authority contexts are server-resolved from AdminApps identity, MFA,
global roles, active access and exact governance permission. Client actor,
role, tenant, scope, approval or MFA claims are non-authoritative. ISO Smart
does not invent local global RBAC.

| Function | Exact authority | Same-chain restrictions |
|---|---|---|
| Learning proposer | proposal only | cannot review, approve, authorize, apply, publish, activate or adopt own change |
| Learning reviewer | scoped review | cannot be sole approver/authorizer or any release actor for same change |
| Learning approver | exact proposal decision | cannot execute, publish, activate or adopt same change |
| Application authorizer | exact application capability | cannot execute or perform release transitions |
| Target application executor | fixed Phase 26 operation only | categorically denied curator, publication, activation, adoption and repair |
| KnowledgeLayer curator | content/source curation approval | cannot be sole publisher for its own revision |
| Publisher | exact publication permission | cannot imply activation and cannot activate same revision |
| Activator | exact global activation permission | cannot imply adoption and cannot adopt same activation |
| Adoption/release authority | exact runtime configuration transition | cannot be application executor or sole activator for same transition |
| Operational repair authority | inspect/classify/disable/request recovery | cannot propose evidence as authority, publish, activate, adopt or mutate history |

At minimum the actor performing each of publication, activation and adoption
must be different for one release chain. Stronger organizational separation
may be imposed by AdminApps policy. Emergency exceptions require a later
explicit dual-control policy; none is invented here.

## 16. Concurrency and TOCTOU

All three operations use a preallocated operation/artifact ID, exact material
hash, idempotency hash, fixed lock order and database uniqueness:

- publication: unique successful record per rule revision; same exact replay
  returns it; changed material conflicts;
- activation: request supplies expected predecessor activation; one logical
  activation per publication/revision, and one successor per predecessor;
- adoption: request supplies expected predecessor adoption; exactly one
  successor may commit, while competitors are replay/conflict/stale.

Each boundary re-resolves fresh authority and revalidates target/artifact/hash,
policy, capability state and expected predecessor immediately before its write.
Publication revalidates curation/source/leaf; activation revalidates publication
and compatibility; adoption revalidates activation and trusted runtime config.
Any drift fails closed.

## 17. Ambiguous commit and claims

Each boundary may use an admitted immutable operation claim plus the exact
governance artifact. Reconciliation is read-only and returns:

| State | Exact meaning |
|---|---|
| `COMMITTED` | Claim, artifact, predecessor, exact target/hash, event, outbox and audit all exist and match bidirectionally |
| `NOT_COMMITTED` | Authoritative inspection finds no claim, artifact or side artifact for the operation identity |
| `ABANDONED` | A claim exists, no governed artifact/target transition committed, and an explicit append-only abandonment decision under policy exists |
| `INCONSISTENT` | Any partial, orphaned, duplicated or mismatched durable evidence exists |

Elapsed time alone never turns a claim into `ABANDONED` and never permits
stealing. A missing artifact is not reconstructed from target state, event or
audit. No Receipt or authority record is synthesized. A lost adoption response
is reconciled by exact adoption ID, predecessor, revision/hash, event and audit;
it is never blindly retried with a new adoption.

## 18. Capability disablement

New learning applications, publications, activations and adoptions can be
disabled independently by exact capability ID/version. Disable/re-enable is an
append-only governance transition, checked at admission and again before
commit; it is not a mutable history flag.

- application disablement blocks new Phase 26 applications and preserves all
  Receipts, successors, events and audits;
- publication disablement blocks only new publication decisions;
- activation disablement blocks only new activation decisions and does not
  alter current runtime selection; and
- adoption disablement blocks runtime target switches while leaving the exact
  existing adoption visible.

Disablement never unpublishes, deactivates, rewinds, deletes or relabels history.

## 19. Repair, incident recovery and emergency boundary

The repair principal may inspect exact bounded views, classify reconciliation,
disable an exact capability, append an incident/operator decision and request
a separately governed recovery. It receives no generic target DML, arbitrary
SQL, curation, publication, activation, adoption, Receipt/event/audit rewrite,
lineage mutation, schema ownership or role inheritance.

Operational repair authority alone cannot change runtime adoption. Normal
recovery requires a new activation when needed and a new `RECOVERY` adoption
with exact incident, predecessor, safe revision and release authority. An
emergency adoption capability requires a later explicit dual-control policy,
scope and tests; it is not authorized by this v1.

## 20. Audit, observability and alerts

Immutable audit must reconstruct version creation, publication, activation,
adoption and recovery: who, authority, exact revision/hash, why, predecessor,
before/after adoption IDs, policy/configuration hashes, trace and timestamps.

Allowed observability fields are operation/application ID, target lineage,
revision IDs, publication/activation/adoption IDs, trace, hashed idempotency,
state, reconciliation outcome, capability state and timestamps. Raw licensed
content, Evidence bodies, prompts, credentials, tokens and secrets are banned.

Required conceptual alert classes are inconsistent application, abandoned
claim, publication mismatch, activation mismatch, adoption mismatch, stale
target, repeated failed adoption, unexpectedly enabled capability and
unauthorized publication/activation/adoption attempt. No external telemetry
dependency is introduced by this design.

## 21. Retained history and migration policy

Migrations 0001–0021 remain frozen. A future migration is additive/expand-first
and must be reversible only while no retained governance history exists. After
the first publication, activation, adoption, capability or claim history, its
destructive reverse fails closed. Schema change then uses compatibility views,
dual-read validation, contract removal after observation and forward fixes.

No migration may delete or rewrite application Receipts, rule successors,
publication evidence, activation/adoption history, events or audits. Rollback
of code/configuration is distinct from adoption recovery and cannot rewind a
hidden pointer.

## 22. Effectiveness and release governance

The future progression is:

```text
created -> publication approved -> activation approved
        -> runtime adoption approved -> observed -> effectiveness assessed
```

Every arrow is an independent decision. A learning-derived runtime change may
later require `LearningChangeEffectiveness` or an equivalent dedicated model;
the existing QMS action `EffectivenessCheck` is not reused automatically. The
assessment cannot create a new LearningSignal, Proposal, version, activation or
adoption without a separate future policy. No deployment window, SLA or SLO is
invented here.

## 23. Threat controls

| Threat | Required control |
|---|---|
| publication/activation/adoption privilege escalation | separate AdminApps permissions, server resolution, least-privilege typed capabilities |
| executor self-publishing or chained self-release | hard role/actor separation and ACL denial |
| publisher self-activating / activator self-adopting | same-chain actor constraints and independent authority decisions |
| tenant-to-global or cross-tenant change | global governance only; tenant evidence grants no release authority |
| latest-wins/runtime auto-adoption | exact adoption ID; no latest/head/max or event consumer switch |
| exact-ID substitution | adoption/revision/scope/config hashes revalidated atomically |
| stale publication/activation/adoption | expected exact predecessor and TOCTOU revalidation |
| duplicate/forked adoption | idempotency, unique predecessor successor and serialized stream lock |
| hidden pointer rewind | recovery is a new adoption artifact |
| ambiguous commit/missing artifact | exact graph reconciliation; partial state is `INCONSISTENT` |
| forged repair | narrow separate principal; no target/release/history write |
| raw history rewrite | append-only triggers, grants and retained-history migration guard |
| legacy bootstrap fiction | explicit import kind; no invented approval/activation/time |
| capability-disable bypass | append-only exact fence checked twice; catalog/behavior tests |
| normative contamination | hashes, source validation, frozen classification and protected digests |

## 24. Future inert-foundation acceptance gate

A later implementation gate must prove on isolated PostgreSQL 18.6:

- the three immutable artifacts and truthful legacy constraints;
- distinct server-resolved authorities and same-chain separation;
- global-table ACL/ownership/`SECURITY DEFINER` least privilege with no fake
  tenant; and ENABLE+FORCE RLS on any tenant-scoped supporting claim;
- exact idempotency, concurrency, expected-predecessor and TOCTOU matrices;
- all four reconciliation outcomes with no reconstruction;
- independent capability disable/re-enable with history digests unchanged;
- append-only recovery and no pointer rewind;
- no runtime selector or configuration change;
- no publication/activation/adoption record, especially for Phase 26 vN+1/vN+2;
- migrations 0001–0021 and ten source hashes unchanged;
- full applicable regressions and teardown; and
- zero production/shared database or external effect.

Any inability to represent legacy truthfully or any path from published status
to runtime without exact adoption fails the implementation gate.

## 25. Change control

This v1 is immutable once referenced. Correction, withdrawal, emergency
authority, new scope, new target, new operation, runtime cutover, actual legacy
bootstrap, publication, activation, adoption or effectiveness implementation
requires a successor policy and separate gate. Historical policy and provenance
are never rewritten.
