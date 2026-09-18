# ISO SMART AI — Phase 27 publication, activation, reconciliation and repair hardening gate

- Date: 2026-09-02
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: source and future-state operational-safety design gate
- Runtime/schema/database/target effects: **ZERO**
- Migration 0022: **ABSENT**
- Verdict: **PHASE 27 — NOT PROMOTED / BLOCKED**

## 1. Verdict

**PHASE 27 — NOT PROMOTED / BLOCKED.**

The required future controls are now explicit, but the current
`KnowledgeLayerRule` architecture conflates publication with runtime
eligibility. It contains no distinct activation or runtime-adoption artifact.
Phase 27 therefore cannot declare the future activation boundary safe and
authorizes no implementation or operational transition.

No Phase 26 target was recreated or touched. The Phase 26 vN+1/vN+2 remain
unpublished, inactive and non-runtime-effective by construction: Phase 27 made
only documentation changes and the Phase 26 POC environment had already been
destroyed after evidence capture.

## 2. Evidence and exact blocker

The current source establishes:

- `KnowledgeLayerRule.Status` contains only `draft` and `published`, with one
  `published_at` field;
- `publish_knowledge_layer_rule` performs the sole draft-to-published state
  change and records a curation audit;
- AgentRun resolves the caller-supplied exact `knowledge_layer_rule_id` with
  `status=published`;
- RecommendationBasis does the same; and
- no activation/adoption model, command, event, authority or runtime adoption
  ID exists in the Phase 26 boundary.

This is not latest-wins: both runtime paths require an exact caller-supplied
ID, and no greatest-version or lineage-leaf resolver is used. It is still an
unsafe conflation for future activation because publication is the only
persisted eligibility condition checked by runtime.

The blocking design is recorded in
`KNOWLEDGE_LAYER_RULE_RUNTIME_ADOPTION_AND_OPERATIONAL_REPAIR_DESIGN_V1`.

## 3. Future transition proof obligation

The future implementation must prove four distinct append-only facts:

```text
VERSION_CREATED (draft, unpublished, inactive, runtime unchanged)
  -> VERSION_PUBLISHED (publishable, runtime unchanged)
  -> VERSION_ACTIVATED (governed intent for exact revision/scope)
  -> RUNTIME_ADOPTED (named runtime release accepts exact activation/revision)
```

Activation and runtime adoption are intentionally separate. Every edge binds
an exact prior artifact and exact revision/hash. Runtime must resolve an exact
adoption ID; it may not select newest, greatest, published-current or lineage
head. This is a design obligation, not current-state proof.

## 4. Ambiguous COMMIT hardening

Migration 0021 already creates claim, successor, Receipt, target event/outbox,
target curation audit and application audit in one transaction. Its Receipt
contains Proposal, selected Reviews, Decision, Authorization,
operation/schema/canonicalization, delta hash, exact before/result
revisions/hashes and artifact references.

There is, however, no separately exposed operational reconciler that proves
the complete durable graph after a client-observed ambiguous COMMIT. Phase 27
therefore does not claim reconciliation readiness.

The future classifier must return `COMMITTED` only after exact bidirectional
matching of every required artifact. A successor alone is never evidence of
commit. A successor with a missing/mismatched Receipt, governance artifact,
event, outbox or audit is `INCONSISTENT`. No operator or service may synthesize
a Receipt after the transaction.

## 5. Disablement and history

Phase 26 policy already states that operational disablement revokes the exact
EXECUTE capability and preserves history. Phase 27 strengthens the future
contract: disablement is an exact capability fence for new claims only. It may
not mutate versions, publication/adoption facts, Receipts, Authorizations,
Events, Audits or lineage.

No durable disable/re-enable control plane or tested runbook exists yet, so
this remains a later implementation gate rather than a promoted capability.

## 6. Repair authority

The proposed repair authority is separate from executor, curator, publisher,
activator, runtime and migrator roles. It receives only fixed inspection,
classification, exact-capability disablement, operator-audit and governed-
recovery-initiation capabilities.

It receives no generic target DML, arbitrary SQL, publication, activation,
learning application, normative curation or history rewrite. Because this role
and its catalog/ACL proof do not yet exist, operational repair is designed but
not promoted.

## 7. Activation rollback/recovery

No activation exists today, so no safe activation rollback can be claimed.
The future recovery contract is a new append-only activation/adoption
transition to an exact safe published revision, or a fully governed new
successor where content semantics require it. It preserves all publication,
activation and adoption history plus exact before/after revisions, hashes,
actor, authority and reason.

Deleting a revision, editing a predecessor, changing prior records or silently
rewinding a mutable current pointer is prohibited.

## 8. Phase 27 promotion additions

| Required addition | Result | Evidence / blocker |
|---|---|---|
| Publication, activation and runtime adoption explicitly distinct, or conflation documented as blocker | **BLOCKER DOCUMENTED / FAIL FOR IMPLEMENTATION** | Current rule has only draft/published; runtime checks exact ID + published |
| Ambiguous COMMIT uses complete durable governed provenance, never target state alone | **DESIGNED / NOT IMPLEMENTED** | Exact future reconciliation graph specified; no operational reconciler exists |
| No Receipt reconstruction from incomplete evidence | **DESIGNED / PROHIBITED** | Missing Receipt is explicitly `INCONSISTENT` |
| Capability disablement blocks new applications without history mutation | **DESIGNED / NOT IMPLEMENTED** | Exact capability fence specified; no durable tested control plane |
| Repair authority has no generic target mutation or publication/activation power | **DESIGNED / NOT IMPLEMENTED** | Fixed allowlist and deny list specified; no role/catalog proof yet |
| Activation recovery preserves immutable version/adoption history | **DESIGNED / NOT IMPLEMENTED** | Append-only recovery transition specified; activation model absent |
| No latest-revision-wins runtime selection | **PASS FOR CURRENT SOURCE** | Exact-ID selectors; no version/head adoption lookup |
| Phase 26 vN+1/vN+2 remain unpublished, inactive and non-runtime-effective | **PASS / NO-EFFECT GATE** | Phase 27 has zero schema/runtime/database/target effects |

Because promotion requires every item, designed-but-unimplemented controls do
not count as PASS and the phase remains blocked.

## 9. Change boundary and retained baseline

Phase 27 adds only these two documents. It does not change models, migrations,
commands, runtime resolution, permissions, roles, Phase 26 policy/report or any
database. The inspected Phase 26 migration SHA-256 remains:

```text
e796910c1660f701c3457b020792a158c06d3e58135a7ebba1728bd8b33c7a97
```

The inspected Phase 26 report SHA-256 remains:

```text
ce36196c4094addba4fb31a512582a05af0113036c3894cb20eb938d1eefedd9
```

## 10. Exit criteria

A new Product Policy and implementation gate must, at minimum:

1. add immutable publication, activation and runtime-adoption contracts and
   independent least-privilege authorities;
2. change runtime to require an exact adoption reference rather than published
   status alone;
3. implement read-only exact-provenance reconciliation and all four outcomes;
4. implement/test exact capability disablement without history changes;
5. create and catalog-prove the narrow repair authority;
6. implement append-only activation recovery; and
7. run real PostgreSQL ambiguity, corruption, concurrency, ACL/RLS, history-
   digest and no-latest-wins matrices while retaining Phase 26 inertness.

## 11. Final statement

Phase 27 closes the design ambiguity but not the implementation gap. The exact
blocker is publication-as-runtime-eligibility in the present model. Therefore
the only safe verdict is **NOT PROMOTED / BLOCKED**, with Phase 26 vN+1/vN+2
remaining inert and no authorization to publish, activate, adopt or repair
governed history.
