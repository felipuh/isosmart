# Phase 25.1 — KnowledgeLayerRule Inactive-Successor Compensation Lineage Blocker Closure Design Gate

- Date: 2026-08-25
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: source, Product Policy, data-model, security and migration design only
- Runtime/schema/database/target effects: **ZERO**
- Migration 0021: **ABSENT**
- Verdict: **PHASE 25.1 — PROMOTED**
- Authorization meaning: **EPHEMERAL PHASE 26 POC ONLY**

## 1. Verdict

**PHASE 25.1 — PROMOTED.**

The exact Phase 25 blocker is closable by an additive target-specific contract
without rewriting migrations 0001–0020 or weakening published history,
linearity, runtime selection, normative safety, legacy inertness or least
privilege.

Promotion authorizes only a later disposable PostgreSQL 18.6 Phase 26 POC for
the already-promoted KnowledgeLayerRule source-reference locator correction.
It does not authorize an application now, production, publication, activation,
deployment, migration 0021 in this phase, another target or another operation.

## 2. Entry baseline

Phase 9 and Phases 21–24.2 are promoted. Phase 25 is NOT PROMOTED. Migration
0020 is the latest migration and the application boundary remains inert: no
application executor, claim, Receipt, target writer, application event,
target-specific function or target DML grant exists.

The entry worktree was materially dirty, including unrelated backend/frontend
changes, SQLite state, untracked promoted foundation/docs and the known Sidebar
whitespace. All such work was preserved. This phase adds only this report, one
non-normative Product Policy and ADR-0013.

## 3. Exact Phase 25 blocker

The current promoted predicates are:

```text
proposal target = exact published row with no child
curator predecessor = published row with no child
database predecessor = published row in same lineage
first application result = draft/unpublished
```

Consequently an inert vN+1 cannot currently be a compensation proposal target
or predecessor of vN+2. A second child from vN is forbidden by
`previous_revision_id UNIQUE`; publishing vN+1 is forbidden by the POC.

KnowledgeLayerRule is uniquely close because forward and compensation remain
locator-only changes under the same edition/hash. ModelPolicy restoration adds
capability and AgentDefinition restoration raises autonomy; both remain
rejected and are not reopened.

## 4. Source reconciliation

All ten authoritative artifacts were byte-read directly. DOCX and XLSX passed
complete ZIP CRC reads and their document/sheet XML was inspected. Draw.io XML,
Mermaid, both CSVs, SQL, OpenAPI, master JSON and LEEME were read directly.

**SOURCE FACTS:** the sources define versioned Knowledge Layers, exact rule/
model provenance, guidance informing requirements, retained normative history,
Effectiveness followed by governed learning, Human Decision Gates and A0–A4
guardrails. They do not define application, compensation, draft-predecessor
authority, a Receipt or a generic target writer.

**DESIGN CONSEQUENCE:** the source package permits an explicit non-normative
Product Policy for an inert, version-preserving POC; it does not itself
authorize mutation or make guidance normative.

## 5. Policy reconciliation

`governed-learning-policy/v1` requires new target versions and separate human
governance. The Phase 21 authorization and implementation remain inert. The
Phase 22 boundary requires exact proposal/target binding, target-specific
capabilities, additive successors, compensation and separate release. Phase 23
adds immutable Review/Decision/Authorization but no application. Phase 24.2
adds exact delta bytes/hashes and permanent `LEGACY_INERT` semantics.

The new Product Policy is a narrow successor decision: it authorizes only an
ephemeral proof that the exact KnowledgeLayerRule operation can create inert
vN+1 and separately governed inert vN+2. It does not retroactively broaden an
old authorization or reinterpret old rows.

## 6. Current KnowledgeLayerRule schema

`KnowledgeLayerRule` is a global row with:

```text
id, knowledge_layer_id, lineage_id, rule_key, version,
previous_revision_id, status, logic_json, evidence_expectation,
source_reference, certifiability_classification, published_at, created_at
```

Identity is the logical `(knowledge_layer_id, rule_key, lineage_id)` chain;
revision identity is row `id` plus exact `version` and predecessor. One root is
allowed per `(knowledge_layer_id, rule_key)`. Version is a nonblank opaque
label, unique within lineage; vN notation means graph position, not numeric
version parsing.

## 7. Current version model

The actual states are only `draft` and `published`. “Active”, “inactive”,
“effective”, “historical” and “current” are derived concepts, not stored status
values.

| State/concept | Material mutable? | Can have successor now? | Can be predecessor now? | Can be published? | Runtime eligible? | Current leaf? | Historical? | Allowed governed operation now? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| root draft | no; only publish transition, delete technically possible if unreferenced | no | no | yes | no | yes until child (child currently impossible) | no | publish only |
| non-root draft | no; only publish transition | no | no | yes | no | yes | no | publish only |
| published leaf | no | yes | yes | already | yes only by exact-ID consumer | yes | no | current curator revise; proposal target |
| published ancestor | no | already has one child | no second child | already | yes if exact historical ID is referenced | no | yes | read/provenance only |
| lineage head | depends on stored status | current contract only if published | current contract only if published | if draft | only if published and exact-ID selected | yes by definition | no | conflated with published leaf in proposal/curator |

The database permits DELETE of an unreferenced draft, but no promoted command
uses it and the future application contract prohibits it. Once application
history exists, retained-history policy makes deletion/downgrade forbidden.

## 8. Current publication model

Every INSERT must begin `draft,published_at=NULL`. Publication is the only
permitted UPDATE and must be atomic `draft -> published` with a non-null
timestamp. It requires the source StandardEdition to be published. Published
rows are immutable and cannot be deleted. Publication is a separate curator
command and no save hook or trigger publishes on successor creation.

## 9. Current runtime-selection model

AgentRun and Recommendation commands accept exact
`knowledge_layer_rule_id` values and query that exact ID with
`status=published`. Database triggers independently require exact published
rules for AgentRunInput, RecommendationBasis and KnowledgeLayerBinding.

There is no lineage-wide active pointer. Runtime-effective means an exact
published revision selected/reference-bound for a use, not the current leaf.
Creating a draft child changes neither those exact IDs nor their status.

## 10. Current lineage model

Root uniqueness, root `lineage_id=id`, same-layer/rule-key predecessor FK,
same-lineage trigger, one-to-one/unique predecessor, no-self check and cycle
guard produce one linear chain. Current leaf is derived as “no row has this ID
as predecessor”. The only incompatible rule is the trigger's published-
predecessor requirement.

## 11. Current curator model

`revise_knowledge_layer_rule` locks an exact row, requires `published`, rejects
an existing child, accepts logic/evidence/source fields, inserts one draft and
appends `normative.curation_audit`. `publish_knowledge_layer_rule` is separate.

The normative curator has generic catalog INSERT within its curated domain,
but no material UPDATE/DELETE. It is not a safe learning-application principal.
Its behavior must remain published-predecessor-only.

## 12. Source-reference semantic boundary

The Phase 24.2 grammar is:

```text
iso-smart-source-ref-v1:<edition UUID>:<64 lowercase hex source hash>:<locator>
```

The locator is 1–256 allowed ASCII characters, starts alphanumeric, has no
whitespace/query/credentials/free-form guidance, and is byte-compared. The
edition UUID and source hash are independently matched to the exact published
StandardEdition reached through the KnowledgeLayer.

`logic_json` and `evidence_expectation` carry substantive guidance; the locator
is structurally isolated. Classification, Layer, edition, rule key and bindings
are independent fields/relations. The boundary therefore passes.

## 13. Allowed delta

Only this exact existing delta is allowed:

```json
{
  "current_source_reference": "<exact validated R-old>",
  "new_source_reference": "<exact validated R-new>",
  "standard_edition_id": "<exact UUID>",
  "standard_edition_source_hash": "<exact SHA-256>",
  "successor_version": "<exact nonblank unused label>"
}
```

Only the locator may differ. Forward is R1→R2. Compensation is independently
canonicalized R2→R1 against vN+1. Both use the same operation/schema validator;
no `restore`, snapshot, copy-all-fields or application-time payload exists.

## 14. Frozen fields

Frozen for both transitions: `knowledge_layer_id`, `lineage_id`, `rule_key`,
`logic_json`, `evidence_expectation`, classification, reference scheme, edition
UUID, edition source hash, Standard/StandardEdition, RequirementControl,
bindings, applicability/relationship/priority/rationale, tenant/global scope
and substantive meaning.

Generated/contractual revision fields are new row ID, exact governed version,
exact predecessor, `status=draft`, `published_at=NULL`, `created_at` and curation
provenance. vN and vN+1 are never mutated or re-pointed.

## 15. Semantic fingerprint

Future identifier:
`iso-smart-knowledge-layer-rule-substantive-fingerprint-v1`.

Canonical input includes target type, KnowledgeLayer ID/type, Standard and
StandardEdition IDs, edition source hash, lineage, rule key, exact canonical
`logic_json`, exact canonical `evidence_expectation`, fixed classification and
source-reference scheme. It excludes row ID, predecessor, version label,
status/publication/creation timestamps and the locator.

```text
before_semantic_hash = SHA-256(canonical fingerprint input for predecessor)
after_semantic_hash  = SHA-256(canonical fingerprint input for successor)
required: before_semantic_hash = after_semantic_hash
```

Binding invariance is separate: hash the ordered full rows of all existing
bindings referencing revisions in the lineage before/after; require equality.
Protected Standard/Edition/Clause/RequirementControl row-set digests also
remain equal. This avoids pretending a new draft inherits a published binding.

## 16. vN semantics

vN remains immutable, published and eligible for exact-ID runtime use. After
vN+1 it becomes a historical lineage ancestor but remains the same published
row. Existing bindings/runs/recommendations continue to reference it exactly.
No “superseded” status is invented.

## 17. vN+1 semantics

vN+1 is the one child of vN, current lineage head, `draft`, unpublished,
inactive and not runtime-eligible. Its only material difference is locator R2.
It has its own ID/version/hash/audit/event/Receipt. It is immutable after
creation under application retained-history rules.

## 18. vN+2 semantics

vN+2 is the one child of vN+1, current lineage head, `draft`, unpublished,
inactive and not runtime-eligible. Its locator is the original safe R1 under a
new exact delta and governance chain. vN and vN+1 remain unchanged.

## 19. Lineage-head semantics

The invariant is:

```text
exactly one root + at most one child per row + every non-root has one predecessor
=> exactly one current leaf/head for each connected rule lineage
```

After forward, head=vN+1. After compensation, head=vN+2. Head says nothing
about publication or runtime adoption.

## 20. Runtime-effective semantics

Current runtime has no single stored “effective pointer”. Runtime eligibility
is `published`; actual use is an exact FK/ID chosen for a run, recommendation or
binding. For the POC, “runtime remains on vN” means all pre-existing exact
references and their published validation remain vN and no reference to vN+1/
vN+2 is created. This is stronger than relying on a mutable current pointer.

## 21. No-latest-wins proof

Repository inspection found exact-ID lookups with `status=published` in
AgentRun, Recommendation, bindings and their database guards. No runtime
`ORDER BY version DESC LIMIT 1`, max-version, latest revision or leaf lookup was
found for KnowledgeLayerRule. Proposal governance does use current-leaf
derivation, but it is governance eligibility, not runtime selection.

Phase 26 must retain repository scans and behavioral before/after exact-ID
assertions. Any latest-wins path is a P1 failure.

## 22. Publication separation

Successor INSERT is forced to draft/null publication. Publication uses a
separate curator command and column UPDATE grant. The future executor and
application function receive neither. Receipt explicitly says
`result_published=false`.

## 23. Activation separation

There is no separate activation field. In current target semantics,
“activation” is represented only by exact published selection/use. Because the
successors are draft and receive no binding/runtime reference, they cannot be
active. The POC cannot introduce an activation pointer or release action.

## 24. Forward governance chain

Forward requires exact Proposal revision, CanonicalDelta, all selected Reviews,
approved Decision, VALID Authorization, target vN ID/lineage/version/full-row
hash, operation/schema/canonicalization/delta hash, actor authority and an
independent idempotency identity. Every tuple is reloaded and recomputed under
lock. Authorization permits one inert successor only.

## 25. Compensation governance chain

Compensation requires new Proposal C, Delta C, Reviews C, Decision C,
Authorization C and idempotency identity C. It targets exact vN+1, not vN, and
references exact forward Receipt. Authorization F is categorically ineligible.
No automatic compensation or proposal generation occurs.

## 26. Canonical delta/hash

Both deltas use `iso-smart-learning-delta-canonical-v1` and the existing
KnowledgeLayerRule operation/schema. Canonical bytes are proposal-owned and
immutable. The application request supplies identifiers and expected hashes,
never `source_reference`.

Forward and compensation hashes differ because target ID/version/hash,
successor version and direction differ. Any unexpected byte-identical hash is
handled as an exact-material conflict, not assumed valid.

## 27. LEGACY_INERT behavior

Only complete positive tuples qualify. Old, partial, hash-only or aliased
`revise_knowledge_layer_rule` chains remain `LEGACY_INERT` forever. The future
design adds no defaults, backfill, inference, attachment, upgrade or rebinding.
Legacy artifacts cannot authorize forward or compensation.

## 28. Target hash

`target_hash` remains the canonical SHA-256 of the complete exact target row,
including source reference and publication state. Forward binds vN/HN;
compensation binds vN+1/HN1. Result hashes are recomputed from inserted full
rows and stored in Receipts. The semantic fingerprint is additional and cannot
replace the full-row target hash.

## 29. TOCTOU

Inside the single mutation transaction revalidate: application identity,
complete governance chain, Authorization validity, operation/schema/hash,
target ID/lineage/version/hash, exact current head, expected predecessor,
absence of child, source reference, semantic fingerprint, publication/runtime
state and, for compensation, forward Receipt/original R1. Any drift denies and
rolls back.

## 30. Locking

Fixed future lock order:

1. deterministic application idempotency advisory key and claim row;
2. Authorization, Decision, Proposal, selected Reviews and CanonicalDelta;
3. KnowledgeLayerRule logical lineage identity/root;
4. expected current leaf/predecessor row;
5. target curation stream/ledger identity;
6. target event/outbox stream identity;
7. Receipt/application-audit stream.

No reverse-order acquisition is permitted. Serialization/deadlock/unique
failure is not success and is reconciled by the durable identity.

## 31. Idempotency

Forward identity is the canonical hash of Proposal revision, Decision,
Authorization, operation ID/version, delta hash and vN ID/version/hash.
Compensation has an independent identity and additionally binds the forward
Receipt and vN+1 ID/version/hash.

Exact replay returns the same successor/Receipt with `replayed=true`. Same key
or claim with changed provenance is conflict. A completed Receipt is never
reassigned.

## 32. Concurrency

Two forward attempts serialize: one creates vN+1; the other returns exact
replay or stale/conflict. Two compensations do the same for vN+2. A forward or
other governed successor race locks the lineage; an intervening child makes
the loser stale. Unique predecessor is the final database no-fork defense.

## 33. No-fork guarantees

The future migration preserves `previous_revision_id UNIQUE`. It does not add a
second edge table or mutable head pointer. Draft succession is allowed only for
the exact application owner/path, and only from the locked unique head. Fork,
cycle, self-reference, reverse edge and predecessor UPDATE remain rejected.

## 34. Stale compensation

Compensation denies if vN+1 is not current head, is published, has a child,
differs in full-row hash/source reference/fingerprint, lacks an exact forward
Receipt, was produced by different governance, or has intervening binding/
runtime/protected-state drift. No rebase to the new head is allowed.

## 35. KnowledgeLayerBinding behavior

Bindings reference an exact KnowledgeLayerRule row, exact StandardEdition and
exact RequirementControl. Published bindings are immutable. Successor creation
does not copy, update or re-resolve bindings. Existing vN bindings remain vN;
vN+1/vN+2 receive none in the POC.

## 36. Recommendation provenance behavior

RecommendationBasis stores an exact KnowledgeLayerRule FK and its database
guard requires that exact row to be published. Existing basis rows are
append-only and retain vN. Draft successors cannot satisfy a new basis insert.

## 37. AgentRun provenance behavior

AgentRunInput stores an exact KnowledgeLayerRule FK; start validation and DB
trigger require published status. Existing inputs retain vN and match
RecommendationBasis exactly. Draft successors are not selectable.

## 38. Normative safety

RequirementControl remains `normative_requirement`; KnowledgeLayer/Rule remain
`non_certifiable_guidance`; binding effect remains `guidance_only`. The
operation touches no Standard, StandardEdition, Clause, RequirementControl,
EvidenceCoverage, binding or certifiability field and stores no licensed text.
It makes no ISO correctness/certification claim.

## 39. Global governance

KnowledgeLayerRule is global curated data. Tenant/Organization signals remain
evidence and never become mutation authority. Forward and compensation require
fresh global governance and exact AdminApps-backed authority contexts. No
tenant principal receives global DML or influences another tenant at runtime.

## 40. Target application principal

Future principal:
`learning_knowledge_rule_application_executor` (or exact equivalent).

Required attributes: LOGIN only if the one-connection service needs it,
NOSUPERUSER, NOINHERIT, NOBYPASSRLS, non-owner, no role creation/database
creation/replication, no curator/owner membership and no SET ROLE path. It has
exact governance read/claim/Receipt/audit rights and EXECUTE on one wrapper,
not target-table DML.

## 41. Target-specific capability

The fixed capability may accept only exact Authorization ID, expected delta
hash, idempotency identity and trace/correlation identifiers. It resolves all
target/operation/material through immutable joins. It has no target type,
field, value, status, publication, arbitrary target ID, operation selector,
payload or dynamic SQL parameter.

## 42. Architecture D

One trusted application service uses one alias, one physical connection and
one outer `transaction.atomic(savepoint=False)`. It orchestrates governance,
locks, claims, Receipt and audit. A dedicated canonical DB primitive owns the
target successor boundary. The function never commits and no second alias,
autonomous transaction, background target write or external call exists.

## 43. Canonical curator reuse

Phase 26 must extract a private shared domain primitive for predecessor,
lineage, version uniqueness, draft-result, immutable copied fields and
normative curation ledger. Existing curator and application wrappers delegate
to it. The private primitive is not granted to executor/PUBLIC.

The curator wrapper continues to require a published predecessor and preserves
its public Python signature, validation, publication separation, errors and
audit. Golden parity tests compare current success and denial vectors before
and after extraction. No parallel ORM/SQL business-rule implementation passes.

## 44. SECURITY DEFINER analysis

If used, all wrapper/private functions have exact signatures, fixed
`search_path=pg_catalog`, qualified relations/functions, no dynamic SQL and
PUBLIC EXECUTE revoked. Owners are dedicated NOLOGIN/NOSUPERUSER/NOINHERIT/
NOBYPASSRLS roles. Executor can execute only the application wrapper; curator
can execute only the curator wrapper; neither can execute the private core.

Custom GUC alone is not an authority because callers can set custom GUCs. Any
GUC may be trace context only; database authorization is established by ACL,
immutable claim/governance joins and unreachable owners.

## 45. Function-owner privileges

No function owner owns target tables/sequences or schemas, has schema CREATE,
role membership, SET ROLE, BYPASSRLS, LOGIN, ALTER, TRIGGER, TRUNCATE or
publication-column UPDATE. The minimum mutation owner may receive column-level
INSERT plus exact ledger/event rights, but is unassumable and its raw insert is
constrained by trigger/claim/lineage invariants. Catalog tests prove no other
function/grant exposes it.

## 46. Receipt contract

Forward Receipt fields:

- application ID/identity hash and exact Proposal revision;
- Review IDs/set hash, Decision and Authorization;
- operation ID/version, canonicalization, schema and delta hash;
- target lineage and before ID/version/full hash;
- result ID/version/full hash and exact predecessor;
- before/after semantic hash and binding/protected-state hashes;
- result draft/publication/runtime facts;
- actor/authority, trace/correlation, timestamps;
- target curation audit, target event and outbox references;
- compensation eligibility; and
- `external_effects=false`, `runtime_effect_changed=false`.

Compensation Receipt adds forward Receipt, compensated vN+1, original vN/R1
provenance and exact compensation chain. It never calls the operation rollback.

## 47. Event semantics

Existing target curation has an append-only `normative.curation_audit`, not a
DomainEvent/outbox. It cannot be misleadingly renamed. Phase 26 may add exactly
one global target-domain event:

```text
knowledge_layer_rule.source_reference_corrected / schema v1
```

It records bounded IDs/hashes, predecessor/result, draft/unpublished/runtime-
unchanged facts and trace, with explicit global scope and no fake tenant. A
matching platform/global outbox is atomic. No learning-application lifecycle
event is authorized; Receipt/audit provide that provenance.

## 48. Audit semantics

Target curation audit and application audit are distinct. Audit preserves
actor/authority, exact chain, target/result hashes, delta/semantic hashes,
operation, Receipt/event/outbox IDs and trace. It stores no raw licensed
content, Evidence body, prompt, credential, secret or arbitrary source text.

## 49. Transaction model

```text
claim/idempotency
-> governance and Authorization validation
-> lineage/head lock
-> target/source/full-hash revalidation
-> canonical delta validation
-> semantic-fingerprint equality
-> private canonical successor primitive
-> vN+1 or vN+2 draft
-> curation ledger
-> target event + global outbox
-> immutable Receipt + application audit
-> commit
```

Compensation repeats independently against vN+1 and locks the forward Receipt.

## 50. Rollback matrix

Forward and compensation must inject failure at each point:

| # | Failure point | Required committed delta |
|---:|---|---|
| 1 | after claim | zero |
| 2 | after governance validation | zero |
| 3 | after target lock | zero |
| 4 | after target revalidation | zero |
| 5 | after delta validation | zero |
| 6 | after semantic hash validation | zero |
| 7 | before successor | zero |
| 8 | after successor | zero |
| 9 | after target event | zero |
| 10 | after target outbox | zero |
| 11 | after target curation audit/ledger | zero |
| 12 | before Receipt | zero |
| 13 | after Receipt | zero |
| 14 | after application lifecycle point (no DomainEvent authorized) | zero |
| 15 | after application audit | zero |
| 16 | after final provenance verification | zero |
| 17 | immediately before commit | zero |

Every case leaves predecessor/protected/runtime state and claim history exactly
as before. The no-application-event point asserts absence, not a write.

## 51. Future migration 0021 design

Phase 26 likely requires additive 0021 for:

- durable application claim/idempotency and immutable Receipt;
- explicit forward-Receipt compensation linkage;
- exact positive eligibility for a KnowledgeLayerRule draft head only;
- substantive fingerprint/version helpers;
- private shared successor primitive and typed wrappers;
- trigger evolution that preserves curator published-predecessor semantics and
  admits draft predecessor only for the unreachable exact application owner;
- executor/owner roles and exact grants;
- global target event/outbox and immutable application audit; and
- retained-history downgrade guard.

0021 must not alter any 0001–0020 file, operation ID, executor allowlist,
ModelPolicy/AgentDefinition contract, publication behavior or target content.
Before history it must pass forward/reverse/forward. After history its reverse
must fail with an explicit retained-history error.

## 52. Retained-history downgrade rule

After the first claim/Receipt/successor/event/audit, the owning migration is a
forward-only boundary. Operational disablement revokes wrapper EXECUTE, stops
new claims, preserves read/reconciliation and uses a forward fix. Schema
downgrade cannot delete vN+1/vN+2, Receipt, governance links, event, outbox or
audit. Compensation is a new successor, never migration rollback.

## 53. Threat matrix

| Threat | Exact design control | Result |
|---|---|---|
| lineage fork | lock + unique predecessor + exact head revalidation | closed by design |
| inactive-successor ambiguity | explicit draft-head eligibility only with forward Receipt | closed |
| latest-wins adoption | exact-ID + published runtime queries; regression scan/test | closed |
| hidden publication/activation | forced draft/null; no grants/references | closed |
| stale vN/vN+1 | full hash/head/source/fingerprint under lock | closed |
| target/semantic hash mismatch | independent recomputation, equality required | closed |
| delta/operation substitution | proposal-owned bytes, exact v1 constants | closed |
| legacy inert bypass | complete-tuple positive predicate; no backfill | closed |
| forward Authorization reuse | compensation chain/identity must be new | closed |
| tenant-to-global escalation | global authority + target wrapper; tenant DML denied | closed |
| generic curator bypass | executor not curator; curator remains published-only | closed |
| generic DML | no executor target DML; private primitive unreachable | closed |
| function-owner escalation | NOLOGIN/no membership/no CREATE/ALTER; catalog assertions | closed by design |
| successor/compensation race | fixed locks, claim, unique predecessor | closed |
| event/Receipt mismatch | same transaction + exact cross-references | closed |
| history deletion | forward-only retained-history guard | closed |
| normative contamination | frozen fields/fingerprint/protected digests | closed |
| locator changes semantics | strict grammar + same edition/hash + semantic equality | closed |
| licensed-content injection | bounded locator, no query/free text/raw content | closed |
| automatic learning | no consumer/event/Effectiveness trigger | closed |
| GUC spoofing | GUC not authority; ACL/joins/owners enforce | closed |

## 54. Mandatory design-proof matrix

| Mandatory proof | Result | Evidence/design |
|---|---|---|
| source reference separable | PASS | distinct field + exact grammar |
| exact locator-only delta | PASS | Phase 24.2 v1 schema |
| semantic fingerprint equality | PASS | deterministic v1 canonical set |
| vN immutable | PASS | existing trigger + no UPDATE path |
| inert vN+1/vN+2 | PASS | forced draft/null and no runtime reference |
| vN+1 legal predecessor later | PASS BY ADDITIVE DESIGN | private exact wrapper/trigger exception only |
| one current leaf | PASS | root/child/predecessor invariants |
| runtime separate from head | PASS | exact-ID published runtime selection |
| runtime remains vN/no latest | PASS | code/DB inspection + required regression |
| publication/activation separate | PASS | distinct command; no capability |
| no fork/cycle/self/repoint | PASS | existing constraints preserved |
| forward/compensation idempotency | PASS BY DESIGN | independent claims/Receipts |
| concurrency/stale compensation | PASS BY DESIGN | fixed locks + full revalidation |
| separate governance chains | PASS | new exact chain C required |
| canonical hashes | PASS | existing canonical v1 reused |
| LEGACY_INERT | PASS | unchanged positive eligibility |
| target-specific/no generic DML | PASS BY DESIGN | fixed wrapper; executor EXECUTE only |
| canonical curator reuse/parity | PASS BY DESIGN | shared private primitive + golden tests |
| least privilege | PASS BY DESIGN | exact role/owner/ACL assertions |
| one-connection atomicity | PASS BY DESIGN | Architecture D transaction |
| full rollback matrix | PASS BY DESIGN | 17 forward + 17 compensation points |
| historical provenance unchanged | PASS | exact FKs/immutable rows |
| normative state unchanged | PASS | frozen/protected targets |
| no external effects | PASS | internal transaction only |
| additive migration path | PASS | exact 0021 design; 0001–0020 frozen |
| retained-history policy | PASS | forward-only after first history |

Every mandatory proof passes at design level. Phase 26 must prove behavioral
and catalog assertions in an isolated PostgreSQL instance; any failure revokes
its promotion.

## 55. Policy artifact

Created:
`docs/governance/KNOWLEDGE_LAYER_RULE_GOVERNED_SOURCE_REFERENCE_APPLICATION_POLICY_V1.md`.

Status is `APPROVED FOR EPHEMERAL PHASE 26 POC ONLY`. SHA-256:
`1a5f7c7838c62ba76837c26fcfa4d29655294810f74afed33fdcf69dc373bb79`.
It authorizes neither publication nor activation.

## 56. ADR

Created successor ADR:
`docs/adr/0013-knowledge-layer-rule-lineage-head-runtime-effective-separation.md`.

SHA-256:
`8fa5852a3cabf822c5213ae10bcae2a61f3910233ff1d915d4d1e1545df6a827`.
ADR-0012 and all earlier ADRs remain unchanged.

## 57. Migration hashes

Migrations 0001–0020 match the promoted exact SHA-256 values: **20/20 MATCH**.

| Migration | SHA-256 |
|---:|---|
| 0001 | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` |
| 0002 | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` |
| 0003 | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` |
| 0004 | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` |
| 0005 | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` |
| 0006 | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` |
| 0007 | `c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec` |
| 0008 | `285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032` |
| 0009 | `412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc` |
| 0010 | `c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79` |
| 0011 | `cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2` |
| 0012 | `7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc` |
| 0013 | `06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b` |
| 0014 | `ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33` |
| 0015 | `5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3` |
| 0016 | `e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5` |
| 0017 | `580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38` |
| 0018 | `703a85885a67df953f38ef35302205caeddea249104683f4f751ab20ece0696b` |
| 0019 | `c188b638124404bba10cae4c94a678053d49d7a1d07c6e455a48e46524064b50` |
| 0020 | `491f21d3422c9c9a5866520f6623d3b9c9bea2139083f0128495dd7207d19894` |

Migration 0021 is absent.

## 58. Source hashes

The authoritative source package is **10/10 MATCH**:

`8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c`,
`e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa`,
`11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3`,
`952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5`,
`ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3`,
`30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6`,
`de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e`,
`29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8`,
`c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb`,
`eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db`.

## 59. Protected-target invariance

No target command or database was used. Protected implementation hashes remain:

| File | SHA-256 | Result |
|---|---|---|
| `backend/foundation/models.py` | `9dd94c945dd0c256c3872e82b45760b06c066a4364e3dc3d833d56c09645c244` | MATCH |
| `backend/foundation/agent_runtime.py` | `6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d` | MATCH |
| `backend/foundation/knowledge_layer.py` | `ad355cd34fa7a03f1ba30cbe2e78f8a1a8de7859d0b05be337639e2c1c4597c3` | MATCH |
| `backend/foundation/learning_delta.py` | `8a3a2187567737ad2034ac6abf695dd73ce356356d3e1dd82c2e61f7fc0944cd` | MATCH |
| `backend/foundation/governed_learning.py` | `ce3fa7c87938c2e9a7253a722ce5de117f638c261e61d30033555d45179c8f52` | MATCH |
| `backend/foundation/learning_proposal_governance.py` | `d1239451fa698739aa52167b6746613ad705d57fd1c232f74c2e2ff43e0db74b` | MATCH |

KnowledgeLayer, KnowledgeLayerRule, Binding, RequirementControl, Standard,
StandardEdition, ModelPolicy and AgentDefinition implementation/state are
unchanged. No successor, claim, Receipt, event, grant or external effect exists.

## 60. Runtime-change evidence

Only Markdown policy/ADR/report artifacts changed. No Python, migration,
schema, settings, security, test, event allowlist, executor or database state
changed. No expensive backend/PostgreSQL matrix was run, per the documentation-
only regression policy.

## 61. Git hygiene

Entry `git status` was recorded before edits. Unrelated local changes were
preserved. New Phase 25.1 files are independently whitespace-checked.
Repository-wide `git diff --check` may still report the pre-existing unrelated
`frontend/src/components/Layout/Sidebar.jsx:28` whitespace; this phase does not
modify Sidebar.

## 62. Residual blockers

There are zero P0/P1 design blockers to the exact ephemeral Phase 26 POC.
Implementation evidence still required in Phase 26 includes migration 0021
necessity/fidelity, curator golden parity, private function ACL/catalog proof,
full forward/compensation rollback, hostile-principal tests, concurrency,
runtime/provenance invariance and teardown. Any failure yields Phase 26 NOT
PROMOTED and no production authority.

Activation/publication, production enablement, cross-tenant learning, a second
target, a second operation and learning-change effectiveness remain explicitly
outside scope rather than residual authorization.

## 63. Final verdict

**PHASE 25.1 — KNOWLEDGE LAYER RULE INACTIVE SUCCESSOR + COMPENSATION
LINEAGE BLOCKER CLOSURE DESIGN GATE: PROMOTED.**

The model can be evolved additively so that published/runtime-used vN has one
inert vN+1, which has one separately governed inert vN+2, while vN stays
unchanged and exact runtime references remain on vN. The change preserves a
single chain, exact canonical deltas, substantive semantic equality, separate
publication/activation, least privilege and retained history.

Promotion means only:

```text
KNOWLEDGE LAYER RULE SOURCE-REFERENCE CORRECTION
APPROVED FOR EPHEMERAL PHASE 26 POC
```

| Component/gate | State | Evidence | Risk/next action |
|---|---|---|---|
| Exact Phase 25 blocker | CLOSED BY DESIGN | draft head separated from published exact-ID runtime eligibility | prove in isolated Phase 26 |
| Source-reference boundary | PASS | exact existing grammar; locator-only | reject any semantic field drift |
| vN→vN+1→vN+2 lineage | PASS BY ADDITIVE DESIGN | unique predecessor + private exact draft-head path | migration 0021 only if implemented |
| Runtime invariance | PASS | explicit published IDs; no latest/head runtime lookup | repeat scans/behavior tests |
| Publication/activation | DENIED | draft/null result; no grants/references | separate future policy only |
| Forward/compensation governance | PASS | separate exact chains, deltas, claims and Receipts | hostile/replay/stale tests |
| Curator reuse | PASS BY DESIGN | private shared primitive + two typed wrappers | golden parity mandatory |
| Least privilege | PASS BY DESIGN | executor EXECUTE only; unreachable NOLOGIN owners | catalog/security tests |
| Normative/history safety | PASS | fingerprint/binding/protected digests; exact FKs | full invariance matrix |
| Product Policy | APPROVED FOR POC ONLY | new non-normative v1 artifact | no production implication |
| ADR-0013 | ACCEPTED FOR POC ONLY | successor decision; old ADRs untouched | implement only after Phase 26 starts |
| Migrations/sources | PASS | 20/20 and 10/10 hashes match; 0021 absent | keep frozen |
| Protected runtime/targets | UNCHANGED | docs-only hashes match | preserve during Phase 26 setup |
| Phase 26 | AUTHORIZED EPHEMERALLY | zero Phase 25.1 P0/P1 design blockers | isolated PostgreSQL 18.6 + teardown |
