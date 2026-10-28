# KnowledgeLayerRule runtime-adoption and operational-repair design v1

- Design ID: `knowledge-layer-rule-runtime-adoption-and-operational-repair/v1`
- Date: 2026-09-02
- Owner/system authority: ISO Smart Product Governance
- Nature: blocking future-state design; not an implementation authorization
- Status: **BLOCKED / NOT APPROVED FOR IMPLEMENTATION**
- Production, publication, activation, runtime adoption and recovery effects: **PROHIBITED**

## 1. Decision and current blocker

Publication, activation and runtime adoption must be separate governed facts.
The current architecture cannot establish that boundary:

- `KnowledgeLayerRule` has only `draft` and `published` states plus
  `published_at`;
- `publish_knowledge_layer_rule` changes the row from `draft` to `published`;
- AgentRun and Recommendation resolve a caller-supplied exact rule ID by
  requiring only `status=published`; and
- no activation, runtime-adoption, adoption-release or adoption-revocation
  artifact exists.

The exact-ID lookup means current runtime does **not** use a latest-revision
selector. It nevertheless makes publication the only persisted runtime-
eligibility gate. A caller can supply a newly published exact revision without
a separate activation/adoption decision. Publication is therefore conflated
with runtime eligibility at the runtime boundary.

This is a Phase 27 blocker. No future learning-derived version may be published,
activated or runtime-adopted until a separately authorized implementation gate
introduces and proves the explicit records below.

## 2. Required future state transitions

The future state machine has four append-only transitions. Separating
activation from observed runtime adoption is stricter than treating them as a
single transition and makes deployment acknowledgement auditable.

| Transition | Required durable result | Forbidden implication |
|---|---|---|
| `VERSION_CREATED` | Exact vN+1 exists with lineage, predecessor, version and full-row hash; `draft`; `published_at=NULL` | Publishable, active or runtime-effective |
| `VERSION_PUBLISHED` | An immutable publication record approves the exact revision/hash as publishable | Activation or runtime use |
| `VERSION_ACTIVATED` | An immutable activation decision binds exact publication, revision/hash, environment/scope, actor, authority, reason and before/after adoption intent | Proof that any runtime adopted it |
| `RUNTIME_ADOPTED` | An immutable runtime-adoption acknowledgement binds the exact activation and exact revision/hash to a named runtime release/configuration | Selection of a lineage head, greatest version or newest publication |

Every transition has its own operation ID/version, idempotency identity,
authority, timestamp, event/outbox and immutable audit. A later transition
references its exact predecessor artifact. State is never inferred from the
version label, lineage leaf, creation time, publication time or a greatest-row
query.

The runtime contract must receive or resolve an exact `runtime_adoption_id` and
then verify its exact revision/hash and scope. Supplying only a rule ID plus
`status=published` must cease to be sufficient. Distribution of an adoption ID
is configuration release governance, not a database `latest` query.

## 3. No latest-wins rule

The following selectors are prohibited for runtime adoption:

- greatest or maximum `version`;
- newest `created_at`, `published_at`, activation time or adoption time;
- lineage head/leaf;
- last row by sequence without an exact governed adoption reference;
- an implicit mutable `current` pointer with no transition evidence; and
- fallback from a missing adoption to any published revision.

Failure to resolve the exact adoption, revision, hash and scope fails closed.
Historical AgentRun, RecommendationBasis and other provenance continue to bind
exact rule IDs and versions.

## 4. Ambiguous COMMIT reconciliation contract

Reconciliation is read-only classification of durable evidence. The existence
of vN+1, vN+2, a lineage child, a published row or any target state is never
sufficient evidence of `COMMITTED`.

`COMMITTED` requires one internally consistent durable graph containing:

1. the exact application claim and idempotency/application identity;
2. the exact Proposal ID, revision and material hash;
3. the exact selected Reviews and review-set hash;
4. the exact Decision and approved outcome;
5. the exact ApplicationAuthorization and authorization snapshot;
6. the exact operation ID and operation version;
7. the exact canonicalization/schema versions and canonical delta hash;
8. the exact target-before ID, lineage, version and recomputed full-row hash;
9. the exact result ID, lineage, version, predecessor and recomputed full-row
   hash;
10. the exact immutable Receipt;
11. the exact target event, outbox row and target curation audit; and
12. the exact application audit and application event/outbox when the governed
    operation contract requires them.

All foreign references, unique identities, hashes, actor/authority facts and
before/after values must match in both directions. The reconciler re-derives
canonical hashes from stored canonical bytes and target rows; it does not trust
denormalized claims alone.

| Classification | Required evidence | Permitted next step |
|---|---|---|
| `COMMITTED` | The complete exact graph above exists and matches | Return the existing Receipt; never create another |
| `NOT_COMMITTED` | Authoritative durable inspection proves no claim, result or governed side artifact committed | A normal caller may initiate a new, separately authorized attempt under the operation's retry policy |
| `ABANDONED` | A durable admitted claim is explicitly terminal/expired under its own claim protocol and no governed target mutation committed | Record classification; initiate separately governed recovery if required |
| `INCONSISTENT` | Any partial, missing, duplicate, orphaned or mismatched evidence, including a successor without its exact Receipt/provenance graph | Fail closed, disable new application if warranted and escalate |

A Receipt is commit evidence produced inside the governed transaction. It must
never be synthesized, backfilled or reconstructed afterward from a target row,
event, audit, claim or operator assertion. Missing Receipt/provenance is
`INCONSISTENT`, even when the target successor appears semantically correct.

## 5. Capability disablement

Emergency disablement acts only on the exact application capability identity:

```text
capability_id      = learning.knowledge_layer_rule.source_reference.correct
capability_version = v1
executor/principal = exact dedicated application executor
```

The future control may revoke EXECUTE from that principal or append an exact
capability-disable decision enforced at admission and revalidation. It blocks
new application claims after its effective fence. Pre-fence claims and all
completed applications remain available for reconciliation according to their
durable evidence.

Disablement must not delete vN+1/vN+2, alter publication/activation/adoption
facts, rewrite Receipts or ApplicationAuthorization, edit Events/Audits, change
predecessors/lineage, or relabel historical outcomes. Re-enablement is another
governed capability transition; it is not mutation of the disable record.

## 6. Separate operational repair authority

The future repair principal is a distinct `NOLOGIN`, `NOSUPERUSER`,
`NOINHERIT`, `NOBYPASSRLS` authority reached through a separately authenticated
operator service. It is not a member of the executor, curator, publisher,
activator, runtime or migrator roles.

Its allowlist is limited to fixed-signature capabilities:

- inspect a named application identity/operation version;
- reconcile and classify `COMMITTED`, `NOT_COMMITTED`, `ABANDONED` or
  `INCONSISTENT`;
- disable the exact application capability;
- append an operator decision/audit with reason, actor, authority and evidence
  references; and
- initiate a separately governed recovery request.

It receives no generic target SELECT beyond bounded reconciliation views, no
target INSERT/UPDATE/DELETE/TRUNCATE, no arbitrary SQL execution, no
publication or activation/adoption capability, no learning-application
executor capability, no normative curator rights, no ownership, no trigger or
schema rights and no history-rewrite capability. It cannot manufacture a
Receipt or reconstruct governed history with raw SQL.

## 7. Activation rollback and recovery

Activation recovery is a new forward governance act. It is never target
revision deletion, predecessor editing, publication reversal, audit mutation
or an unaudited pointer rewind.

Two future mechanisms are permitted for a separately authorized design:

1. append a new activation and runtime-adoption transition that targets a
   previously published exact safe revision; or
2. where target semantics require content succession, create and govern a new
   successor revision, publish it, activate it and record runtime adoption.

Either mechanism must retain all earlier publication, activation and adoption
records and bind reason, actor, authority, incident/recovery reference,
before/after exact revision IDs and hashes, and before/after exact adoption
IDs. Runtime changes only when configured with the new exact adoption ID. No
historical transition is overwritten and no implicit `current` pointer is
silently reset.

## 8. Phase 26 preservation fence

Phase 27 is design and inspection only. It authorizes no migration, data
mutation, publication, activation, runtime configuration or executor use.
Phase 26 vN+1 and vN+2 therefore remain `draft`, unpublished, inactive and
non-runtime-effective. Their vN predecessor remains the only demonstrated
published/runtime-selected revision in the disposed Phase 26 environment.

The Phase 26 policy, migration and report are retained unchanged. Any future
implementation must use a new migration, policy and gate and must reproduce the
Phase 26 inertness proofs before testing publication or adoption with new
fixtures.

## 9. Promotion gates for a later implementation phase

A later phase cannot promote until real PostgreSQL tests prove:

- all four transitions and their independent authorities/records;
- publication alone is rejected by runtime;
- exact adoption succeeds and every latest/head/max fallback fails closed;
- the complete reconciliation outcome matrix, including successor-without-
  Receipt as `INCONSISTENT` and prohibition of Receipt repair;
- capability disable/re-enable without any history digest change;
- repair-role catalog/ACL denials and fixed allowlist;
- governed activation recovery with immutable before/after history; and
- unchanged Phase 26 vN+1/vN+2 inertness.

Until then the current publication/runtime conflation remains an explicit
blocker and this design grants no operational authority.
