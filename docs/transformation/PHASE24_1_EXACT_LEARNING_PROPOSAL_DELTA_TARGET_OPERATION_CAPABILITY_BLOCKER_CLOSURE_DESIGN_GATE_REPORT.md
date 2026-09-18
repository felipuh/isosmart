# Phase 24.1 — Exact Learning Proposal Delta + Target-Operation Capability Blocker Closure Design Gate

- Date: 2026-08-25
- Nature: contract and security design only
- Workspace: `/home/felipe/proyectos/isosmart`
- Runtime/schema/database/target effects: **ZERO**
- Verdict: **PROMOTED — ADDITIVE INERT CONTRACT FOUNDATION ONLY**

## 1. Verdict and authorization boundary

**PHASE 24.1 — EXACT LEARNING PROPOSAL DELTA + TARGET-OPERATION
CAPABILITY BLOCKER CLOSURE DESIGN GATE: PROMOTED.**

All three validation profiles are exact enough to implement and compare safely
at a later gate. This verdict does **not** select any profile or target for
application. It authorizes only a later additive, inert delta/operation-contract
foundation. That foundation must stop before executor, target mutation,
successor, application receipt, publication, activation, deployment or grants
to an application principal.

The promoted design closes the four Phase 24 design blockers by defining:

1. one immutable canonical delta owned by one exact proposal revision;
2. canonical bytes and a SHA-256 commitment with no application-time payload;
3. direct delta binding through review, decision and authorization;
4. three new, non-aliased operation identities and validation profiles;
5. a one-connection hybrid service plus dedicated database curator-primitive
   architecture for a later application gate.

No current `revise_*` capability is reinterpreted. All pre-foundation artifacts
remain permanently ineligible for application.

## 2. Entry evidence and fixed scope

Phase 24 recorded migrations 0001–0019 and the protected implementation hashes
as the frozen baseline. Direct source inspection confirms the relevant current
facts:

- `LearningProposal` stores `proposed_change_hash`, but no delta artifact;
- review, decision and authorization do not directly carry a delta identity or
  delta hash;
- authorization uses the broad `revise_model_policy`,
  `revise_agent_definition` and `revise_knowledge_layer_rule` identities;
- current curator services create draft successors and separate publication;
- published target rows and curation ledgers are protected from mutation;
- curator roles currently have broader target-table INSERT than a future
  application executor may receive.

This phase is documentation only. It does not use a database or change models,
services, runtime, events, settings, roles, grants or protected targets.

## 3. Canonical delta ownership contract

The future foundation shall introduce one `CanonicalDelta` for each new-format
`LearningProposal` revision. Ownership is a strict one-to-one relation:

```text
LearningProposal.id/revision
  <-> LearningProposal.canonical_delta_id (UNIQUE, immutable)
  <-> CanonicalDelta.learning_proposal_id (UNIQUE, immutable)
```

Both UUIDs are allocated before insertion. The proposal and delta are inserted
in one transaction using deferred exact foreign keys; neither may exist as a
committed half-pair. The proposal creation service accepts a typed operation
command, constructs and canonicalizes the delta itself, and inserts both rows.
It never accepts caller-supplied canonical bytes or a caller-supplied hash.

`CanonicalDelta` is append-only. UPDATE, DELETE, ownership reassignment and a
second delta for the same proposal are rejected. A proposal correction creates
a new proposal revision and a new delta. No delta may be attached to an already
committed proposal, copied to another revision, replaced after review, or
rebased against a later target.

The artifact contains at least:

```text
id
learning_proposal_id
canonicalization_version
delta_schema_version
operation_id
operation_version
target_type
target_id
target_lineage_id
target_version
target_hash
delta_document
canonical_bytes
delta_hash
created_at
```

`target_*` values must equal the exact immutable target snapshot on the owning
proposal. The typed profile is validated against that exact vN snapshot before
either row is inserted. `delta_document` is the parsed representation used for
typed validation; `canonical_bytes` is the authoritative hash input. Creation
must prove that parsing `canonical_bytes` yields exactly `delta_document` and
that re-canonicalizing it yields byte-for-byte identical bytes.

## 4. Canonicalization contract

The stable identifier is:

```text
iso-smart-learning-delta-canonical-v1
```

The exact rules are:

- input is a JSON object accepted by one exact `delta_schema_version`;
- unknown fields are prohibited at every object level;
- every schema field is required unless explicitly marked optional; omission
  and JSON `null` are distinct;
- `null` is prohibited in v1 except where a profile explicitly names a nullable
  field; none of the three v1 payloads below uses `null`;
- object keys are serialized in ascending Unicode code-point order;
- output uses UTF-8 without BOM and no insignificant whitespace;
- strings use JSON escaping, with control characters escaped, quotation mark
  and reverse solidus escaped, and all other Unicode emitted as UTF-8; lone
  surrogate code points are rejected;
- booleans are lowercase `true` and `false`;
- only integers are allowed as JSON numbers in v1; they use minimal base-10
  form, with no leading zero and no negative zero; floats, exponent notation,
  NaN and infinity are prohibited;
- arrays are ordered and order is significant unless the selected schema says
  it is a set-array; set-arrays are rejected unless their non-empty string
  members are unique and already sorted by Unicode code point;
- UUIDs are lowercase RFC 4122 hyphenated strings; hashes are 64 lowercase hex
  characters; trimming or case normalization is never performed implicitly;
- the canonical document is serialized directly; no outer implementation
  envelope, defaults or implementation-time reinterpretation is added.

The exact top-level document has these keys and no others:

```json
{
  "canonicalization_version": "iso-smart-learning-delta-canonical-v1",
  "delta_schema_version": "<exact profile schema>",
  "operation_id": "<exact operation>",
  "operation_version": "v1",
  "payload": {},
  "target_hash": "<sha256>",
  "target_id": "<uuid>",
  "target_lineage_id": "<uuid>",
  "target_type": "<exact type>",
  "target_version": "<exact current version>"
}
```

The commitment is:

```text
delta_hash = lowercase_hex(SHA-256(canonical_bytes))
```

The stored bytes, parsed document and hash must agree at creation, review,
decision, authorization and any future application. A canonicalization or
schema change requires a new stable version; no reader may silently upgrade or
reinterpret v1.

## 5. End-to-end immutable binding

Every new-format governance artifact directly carries the following immutable
tuple, not merely an enclosing material hash:

```text
learning_proposal_id
proposal_revision_snapshot
canonical_delta_id
canonicalization_version
delta_schema_version
operation_id
operation_version
delta_hash
target_type + target_id + target_lineage_id + target_version + target_hash
```

The chain is therefore:

```text
LearningProposalRevision
  -> CanonicalDelta -> canonical_bytes -> delta_hash
  -> LearningProposalReview
  -> LearningProposalDecision
  -> LearningApplicationAuthorization
```

Review creation loads the proposal-owned artifact and independently verifies
its bytes, schema, target and hash. Decision creation requires a complete set of
reviews with that identical tuple. Authorization requires an approved decision
with that identical tuple and the exact new operation ID/version. Composite
constraints and service validation reject mixed tuples. Existing
`proposal_material_hash`, `review_set_hash`, decision identity and authorization
idempotency hashes must incorporate the entire tuple in their own canonical
material.

Changing any byte, field, schema, operation, target identity or target hash
requires a new proposal revision, new canonical delta and entirely new review,
decision and authorization chain. No application request contains a delta
payload; it identifies only the exact authorization and expected delta hash.

## 6. Permanent legacy inertness

The later additive migration must add nullable binding fields without defaults
to preserve history. An artifact is `CANONICAL_DELTA_V1_ELIGIBLE` only when the
entire tuple in section 5 is present, internally exact, and was created through
the new-format creation path. Otherwise it is:

```text
LEGACY_INERT / NOT_APPLICATION_ELIGIBLE
```

This includes every pre-Phase-24.1 proposal, review, decision and authorization
that lacks any of `canonical_delta_id`, `canonicalization_version`,
`delta_schema_version`, `operation_id`, `operation_version` or `delta_hash`.
Legacy rows may remain readable as history but may never be updated, backfilled,
defaulted, upgraded, rebound to a new delta, or used as the predecessor material
for an eligibility conversion. Creating a delta later for an old proposal does
not change its state. Only a wholly new proposal revision and governance chain
can use the new contract.

Database constraints/triggers, services and tests must all use the positive
complete-tuple predicate. Absence never means a default version or operation.

## 7. Exact new operation identities

The only designed operation identities are:

| Target | Operation ID | Version | Delta schema |
|---|---|---|---|
| `ModelPolicy` | `learning.model_policy.approved_models.remove` | `v1` | `learning-model-policy-approved-model-removal-delta-v1` |
| `AgentDefinition` | `learning.agent_definition.autonomy.reduce` | `v1` | `learning-agent-definition-autonomy-reduction-delta-v1` |
| `KnowledgeLayerRule` | `learning.knowledge_layer_rule.source_reference.correct` | `v1` | `learning-knowledge-layer-rule-source-reference-correction-delta-v1` |

They are not aliases for `revise_model_policy`, `revise_agent_definition` or
`revise_knowledge_layer_rule`. No wildcard, generic `revise`, arbitrary target,
arbitrary field patch or arbitrary JSON operation is permitted. The old
capabilities continue to mean only what they mean today and confer no learning
application authority.

## 8. Profile 1 — ModelPolicy approved-model removal only

Payload keys are exactly:

```json
{
  "removed_models": ["<exact model identifier>"],
  "successor_version": "<exact nonblank version>"
}
```

`removed_models` is a set-array: non-empty, unique, nonblank strings already in
canonical sort order. Every entry must occur in vN `approved_models`. The
successor list is deterministically calculated by removing every occurrence of
those exact strings from vN while preserving the relative order of remaining
entries. At least one array element must be removed and the successor list must
differ from vN. No model can be added, substituted, case-folded or normalized.

The successor must satisfy:

```text
lineage_id          = vN.lineage_id
policy_key          = vN.policy_key
previous_revision   = vN.id
approved_models     = deterministic removal result
data_classes        = vN.data_classes exactly
guardrails          = vN.guardrails exactly
human_gate_rules    = vN.human_gate_rules exactly
status              = draft
published_at        = NULL
version             = payload.successor_version
```

The exact target is a published, immutable current leaf whose full canonical row
hash equals `target_hash`. `successor_version` must be unused for the lineage and
policy key. ID, timestamps and curation-audit identity are generated by the
curator primitive and are not delta inputs.

This proves removal only, no addition, no guardrail or human-gate weakening, no
autonomy change, no data-class broadening, and all unrelated fields frozen. The
created successor is non-published and non-active. The profile **PASSES** as an
exact comparison contract; it is not selected for application.

## 9. Profile 2 — AgentDefinition autonomy reduction only

Payload keys are exactly:

```json
{
  "new_autonomy_max": 0,
  "successor_version": "<exact nonblank version>"
}
```

`new_autonomy_max` is an integer in `[0,4]`. Existing A0–A4 semantics already
store the order as integers 0–4; the exact predicate is:

```text
0 <= new_autonomy_max < vN.autonomy_max <= 4
```

Equality is rejected as a no-op and an increase is rejected. The successor is:

```text
lineage_id          = vN.lineage_id
agent_key           = vN.agent_key
name                = vN.name
previous_revision   = vN.id
purpose             = vN.purpose exactly
capability          = vN.capability exactly
autonomy_max        = payload.new_autonomy_max
model_policy_id     = vN.model_policy_id exactly
status              = draft
published_at        = NULL
version             = payload.successor_version
```

The target and version predicates are identical to section 8. Purpose,
capability, name and exact ModelPolicy linkage cannot be supplied or changed by
the operation. The profile **PASSES** as an exact comparison contract; it is not
selected for application.

## 10. Profile 3 — KnowledgeLayerRule validated source-reference correction only

This operation is deliberately narrower than arbitrary text replacement. It is
eligible only when both old and new references use this exact grammar:

```text
iso-smart-source-ref-v1:<standard-edition-uuid>:<64-lowercase-hex-source-hash>:<locator>
```

`locator` is 1–256 ASCII characters from `[A-Za-z0-9._:/#-]`, begins with an
alphanumeric character, contains no whitespace, query string, credentials or
free-form guidance, and is compared byte-for-byte. Payload keys are exactly:

```json
{
  "current_source_reference": "<exact current value>",
  "new_source_reference": "<exact corrected value>",
  "standard_edition_id": "<uuid>",
  "standard_edition_source_hash": "<sha256>",
  "successor_version": "<exact nonblank version>"
}
```

Deterministic validation requires that:

1. vN is the exact published current leaf and its `source_reference` equals
   `current_source_reference` byte-for-byte;
2. the rule's `KnowledgeLayer.standard_edition_id` equals the payload edition;
3. that `StandardEdition` is published and its non-null `source_hash` equals the
   payload hash;
4. both references contain that same edition UUID and source hash;
5. only the locator differs and the two complete references are unequal;
6. no external lookup occurs and no unstructured reference is converted by
   default.

The successor is:

```text
knowledge_layer_id              = vN.knowledge_layer_id
lineage_id                      = vN.lineage_id
rule_key                        = vN.rule_key
previous_revision               = vN.id
logic_json                      = vN.logic_json exactly
evidence_expectation            = vN.evidence_expectation exactly
source_reference                = payload.new_source_reference
certifiability_classification   = non_certifiable_guidance, equal to vN
status                          = draft
published_at                    = NULL
version                         = payload.successor_version
```

Every existing `KnowledgeLayerBinding` remains unchanged and linked to its exact
historical rule revision. RequirementControl and StandardEdition linkage are
unchanged. No logic, evidence expectation, rationale, guidance text,
classification, binding or normative material is editable. A row with a free-
text, null, malformed, cross-edition or unverifiable source reference is simply
ineligible for this operation and requires ordinary normative curation.

This makes provenance correction mechanically distinguishable from substantive
guidance mutation and preserves published history by successor only. The
profile **PASSES** as an exact comparison contract; it is not selected for
application.

## 11. Capability architecture comparison

| Criterion | A. constrained application/service | B. target-specific `SECURITY DEFINER` wrapper | C. dedicated target-curator function | D. hybrid service + dedicated DB capability |
|---|---|---|---|---|
| One-connection atomicity | possible only if service role has all DML | possible | possible | **yes: one Django alias/connection and one outer transaction** |
| Canonical curator reuse | current Python service reusable | wrapper cannot call Python; direct DML risks parallel logic | becomes canonical if all callers delegate | **service orchestrates; shared function owns exact target successor semantics** |
| Duplicate business logic | low initially | high unless wrapper becomes primitive | low | **low; existing/new exact-operation service paths delegate to primitive** |
| DB least privilege | weak | strong if narrow | strong | **strong** |
| Executor generic target DML | required or hard to avoid | none | none | **none** |
| Target-table ownership | ordinary DML role | function owner | function owner | **non-login function owner with minimum target/audit rights** |
| Owner requirements | broad login role | non-login, no inheritance to executor | non-login | **non-login, not runtime/executor, minimum direct grants** |
| `search_path` safety | service dependent | must be fixed | must be fixed | **fixed to `pg_catalog`; all objects schema-qualified** |
| Dynamic SQL | avoidable | prohibited | prohibited | **prohibited** |
| RLS/global catalog behavior | awkward across qms/global aliases | owner must handle deliberately | explicit | **qms governance revalidated by service; global target touched only by exact function** |
| Transaction ownership | Django | Django or caller | caller | **one outer Django `atomic()` owns commit/rollback** |
| Django composition | easy but overprivileged | possible via cursor | possible | **natural: service and function use same connection** |
| Rollback | possible | possible | possible | **successor, target audit, receipt and learning audit roll back together** |
| Maintainability | familiar but unsafe privilege | wrapper drift risk | good primitive, more DB orchestration | **best separation: application orchestration in service, target rules in primitive** |
| Result | reject | reject as standalone wrapper | acceptable building block | **selected for future application design** |

Architecture D is selected as the only future application architecture. This
is an architecture selection, not a target/profile selection and not
implementation authority.

For each profile, the database capability must be a separately named, statically
typed function. It accepts only the exact authorization identity, expected
delta hash and trace identity; it resolves target and delta through immutable
joins. It does not accept target table/name, operation ID, arbitrary target ID,
field name, successor document or JSON patch. The operation ID/version is fixed
inside the function contract.

The function is the canonical primitive for that exact successor operation.
Any curator-facing service that offers the same narrow operation must delegate
to it; no ORM copy of its predicates is allowed. Existing broad human
`revise_*` commands remain distinct and do not become application seams. Shared
published-leaf, predecessor, row-freeze and audit semantics are factored into
the primitive and retained DB triggers rather than copied into the application
orchestrator.

Function requirements are: `SECURITY DEFINER`; owner is a non-login role with
only SELECT/INSERT on the exact target and INSERT on its exact curation ledger;
`SET search_path = pg_catalog`; every non-catalog object is schema-qualified;
no dynamic SQL; PUBLIC EXECUTE revoked; executor membership in owner/curator
roles prohibited; and EXECUTE granted only for the exact target function at a
later separately authorized application gate.

## 12. One-connection transaction invariant

The future application service must use one configured database alias and one
physical connection under one outer transaction:

```text
BEGIN
-> bind trusted application identity
-> lock/revalidate exact proposal revision and CanonicalDelta
-> lock/revalidate exact reviews, decision and authorization
-> verify canonical bytes/schema/hash and exact operation profile
-> lock exact target vN/current-leaf lineage
-> invoke the exact dedicated curator primitive on this connection
-> create inert vN+1 and target-owned curation audit
-> append application receipt and immutable learning audit
-> COMMIT
```

There is no nested connection alias for the target mutation, autonomous
transaction, background dispatch, external call or after-commit target write.
Any failure rolls back governance claim, vN+1, target audit, receipt and learning
audit. Django's outer transaction owns the only commit; the function neither
commits nor opens a transaction.

## 13. Executor least privilege

The future executor role has no INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES,
TRIGGER or ownership rights on `governance.model_policy`,
`governance.agent_definition`, `normative.knowledge_layer_rule`, their sibling
catalog tables or curation ledgers. It is not a member of either current curator
role and cannot `SET ROLE` to a function owner.

It may eventually receive only the minimum qms governance/receipt/audit rights
and EXECUTE on one explicitly selected target-operation function. There is no
generic function, wildcard capability, arbitrary operation/payload dispatcher
or target-table parameter. Negative ACL tests and catalog queries must prove
zero generic target DML before any application promotion.

## 14. Later additive inert foundation acceptance boundary

This verdict authorizes a later gate to implement only:

- the immutable `CanonicalDelta` artifact and exact one-to-one proposal binding;
- the canonicalizer and the three typed schema validators;
- nullable, direct binding fields on review/decision/authorization with
  permanent legacy-inert rules;
- the three new operation constants/contracts;
- creation/review/decision/authorization tests proving the exact chain;
- documentation and additive migration needed for those inert artifacts.

That later gate must still create no executor, curator application function,
receipt, application event, target successor, target DML grant, publication or
activation path. Architecture D is recorded now so the inert foundation does
not accidentally choose an incompatible connection or capability shape.

## 15. Required later verification matrix

The additive inert foundation gate must prove at least:

1. proposal and delta commit together or neither commits;
2. exactly one delta per proposal revision and exactly one owner per delta;
3. all mutation, deletion, replacement and rebinding attempts fail;
4. canonical Unicode, escaping, key ordering, integer, array and null vectors;
5. unknown fields, floats, duplicate/unsorted set members and malformed IDs fail;
6. stored bytes round-trip and SHA-256 recomputation match;
7. application-time/caller-supplied delta material is impossible;
8. each profile accepts its exact allowed change and rejects every unrelated
   field change;
9. ModelPolicy addition/substitution, guardrail/human-gate/data-class change
   fails;
10. AgentDefinition equality/increase and purpose/capability/policy change fails;
11. Knowledge reference free text, cross-edition/hash, guidance/evidence/binding
    change fails;
12. review, decision and authorization bind identical delta tuples;
13. any changed delta requires a new proposal revision and governance chain;
14. every legacy artifact remains `LEGACY_INERT` and cannot be backfilled;
15. old `revise_*` capabilities never satisfy any new operation check;
16. no target/application runtime path or generic DML capability exists;
17. migrations 0001–0019 and protected targets remain byte-for-byte unchanged;
18. forced rollback leaves no proposal/delta half-pair or governance artifact.

Any failure is a P1 blocker and yields NOT PROMOTED.

## 16. Threat closure

| Threat | Exact closure |
|---|---|
| application payload substitution | application supplies no payload; proposal-owned canonical bytes only |
| hash of absent/reinterpreted material | bytes, parsed document, schema and hash stored and reverified |
| delta replacement/rebinding | one-to-one deferred FKs plus append-only guards |
| stale/latest target recomputation | exact target tuple/hash embedded in delta and governance chain |
| capability aliasing | three new exact IDs; old `revise_*` explicitly ineligible |
| generic patch/DML | typed schemas/functions; no dispatcher or executor target DML |
| model allowlist expansion | deterministic removal-set predicate |
| autonomy escalation/no-op | integer strict-decrease predicate |
| normative guidance mutation | only validated locator changes; guidance/bindings frozen |
| legacy privilege resurrection | complete-tuple positive eligibility; no defaults/backfill |
| two-connection partial commit | one Django connection and outer transaction |
| definer escalation | non-login minimum owner, fixed path, qualified SQL, no dynamic SQL, PUBLIC revoke |

## 17. No-implementation and frozen-integrity confirmation

At the end of Phase 24.1:

- migration 0020 is **ABSENT**;
- migrations 0001–0019 are unchanged;
- no model changed;
- no service or runtime implementation changed;
- no event or outbox contract was added;
- no grants, executor or database function were added;
- no receipt table exists;
- no target successor was created;
- no database was used;
- ModelPolicy, AgentDefinition, KnowledgeLayerRule, Standard,
  StandardEdition, Clause, RequirementControl and KnowledgeLayerBinding remain
  byte-for-byte unchanged.

Protected implementation entry/final hashes:

| File | SHA-256 | Result |
|---|---|---|
| `backend/foundation/models.py` | `5c809744810abeee1e956102f4d14d653e70b2064ee26026580dce8eaf2e5be7` | MATCH |
| `backend/foundation/agent_runtime.py` | `6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d` | MATCH |
| `backend/foundation/knowledge_layer.py` | `ad355cd34fa7a03f1ba30cbe2e78f8a1a8de7859d0b05be337639e2c1c4597c3` | MATCH |
| `backend/foundation/governed_learning.py` | `1a544de5133eaa4966a013c93d98ce67bdb786ef6f8b564628bbee4004b7dc97` | MATCH |
| `backend/foundation/learning_proposal_governance.py` | `186e36a0603b11861e8c003626c23ef2a1c4bd22b3c961142e47d7656e0c2e4b` | MATCH |

No PostgreSQL or backend test suite was run because this is a no-database,
documentation-only gate. Verification is limited to direct source inspection,
hashes, path/diff inspection and document checks.

## 18. Final promotion matrix

| Component | Result | Binding decision |
|---|---|---|
| Canonical ownership | PASS | one atomic immutable one-to-one proposal/delta pair |
| Canonicalization | PASS | `iso-smart-learning-delta-canonical-v1`; exact UTF-8 bytes and SHA-256 |
| End-to-end hash binding | PASS | direct tuple on proposal/review/decision/authorization |
| Legacy inertness | PASS | permanent incomplete-tuple ineligibility; no backfill/defaults |
| Exact operations | PASS | three new v1 IDs; no alias/wildcard |
| ModelPolicy profile | PASS | exact approved-model removal only |
| AgentDefinition profile | PASS | exact strict A0–A4 reduction only |
| KnowledgeLayerRule profile | PASS | same-edition/source-hash locator correction only |
| Capability architecture | PASS | D: one-connection service + dedicated canonical DB primitive |
| Executor least privilege | PASS by design | no target DML; exact EXECUTE only at a later gate |
| Target/profile selection | NOT PERFORMED | expressly outside Phase 24.1 |
| Target application | NOT AUTHORIZED | requires later selection and implementation gates |
| Phase 24.1 | **PROMOTED** | additive inert delta/operation-contract foundation only |

There are zero open P0/P1 design blockers within this gate's scope. Promotion
does not assert that the contracts are implemented or that any target is safe to
apply today.

## NEXT_CODEX_PROMPT

Execute PHASE 24.2 — ADDITIVE INERT CANONICAL LEARNING DELTA + EXACT OPERATION
CONTRACT FOUNDATION IMPLEMENTATION exclusively in
`/home/felipe/proyectos/isosmart`. Implement only the Phase 24.1 canonical delta
artifact, `iso-smart-learning-delta-canonical-v1` canonicalizer, three exact
typed delta schemas/operation identities, atomic one-to-one proposal ownership,
direct review/decision/authorization hash binding and permanent legacy-inert
eligibility rules. Use additive migration 0020 only; preserve migrations
0001–0019, authoritative sources, governance history and protected targets
byte-for-byte. Do not select a target/profile, implement target application,
create an executor/receipt/application event or SECURITY DEFINER curator
function, grant target DML/EXECUTE, create a target successor, publish/activate,
deploy, or touch production/staging/shared databases. Validate with an ephemeral
official PostgreSQL environment, exact canonicalization vectors, atomic rollback,
immutability/rebinding negatives, all three profile validators, end-to-end tuple
binding, legacy inertness, ACL denial and full required regressions. Emit
PROMOTED only with zero P0/P1 blockers; promotion authorizes only a later target
profile selection/application design gate, never application itself.
