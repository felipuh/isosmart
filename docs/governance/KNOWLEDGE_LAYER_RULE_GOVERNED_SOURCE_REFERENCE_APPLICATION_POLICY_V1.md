# KnowledgeLayerRule Governed Source-Reference Application Policy v1

- Policy ID: `knowledge-layer-rule-governed-source-reference-application-policy/v1`
- Version: `v1`
- Date: 2026-08-25
- Owner/system authority: ISO Smart Product Governance
- Nature: non-normative Product Policy
- Status: **APPROVED FOR EPHEMERAL PHASE 26 POC ONLY**
- Production, publication, activation, deployment and external effects: **PROHIBITED**

## 1. Decision

ISO Smart Product Governance authorizes only an ephemeral Phase 26 proof of
concept for the existing exact operation:

```text
target_type        = KnowledgeLayerRule
operation_id       = learning.knowledge_layer_rule.source_reference.correct
operation_version  = v1
delta_schema       = learning-knowledge-layer-rule-source-reference-correction-delta-v1
canonicalization   = iso-smart-learning-delta-canonical-v1
```

The POC may prove one governed forward transition from a published exact
revision vN to one inert draft successor vN+1 and one separately governed
compensation from that exact inert vN+1 to one inert draft successor vN+2.
It authorizes no other target, field, operation or successor.

## 2. Semantic boundary

The only changeable value is the locator component of an existing validated
source reference with this exact grammar:

```text
iso-smart-source-ref-v1:<published-standard-edition-uuid>:<exact-source-sha256>:<locator>
```

The edition UUID and source hash must be identical before and after. The
locator must satisfy the already-promoted Phase 24.2 grammar. The exact
`KnowledgeLayer`, lineage, rule key, logic JSON, evidence expectation,
classification, edition relationship and all bindings are frozen. The
classification remains `non_certifiable_guidance`.

The deterministic substantive semantic fingerprint excludes only revision
identity/publication metadata and the locator. It includes the source-reference
scheme, exact edition and source hash. Its before and after values must be
equal. Existing binding and historical-provenance sets are checked separately
and must be unchanged.

## 3. Version and lineage decision

`vN`, `vN+1` and `vN+2` mean consecutive graph revisions, not arithmetic
parsing of the existing free-form `version` label.

```text
vN (published, runtime-eligible) -> vN+1 (draft, inert) -> vN+2 (draft, inert)
```

There is exactly one root and at most one child per revision. The current
lineage head is the unique row with no child. A lineage head is not a runtime-
effective revision. Creating a child never publishes or activates it and never
changes exact published rule references used by bindings, RecommendationBasis,
AgentRunInput or other historical provenance.

The ordinary curator remains published-predecessor-only. Draft-predecessor
succession is permitted only inside the exact governed application capability,
and only when the draft is the exact current head produced by a complete
forward application Receipt.

## 4. Runtime, publication and activation

Runtime accepts an explicitly supplied exact `KnowledgeLayerRule` ID only when
that row is published. It does not select a lineage head or the greatest
version. The POC must prove that no `latest`, maximum-version or leaf lookup is
used for runtime adoption.

Both successors must have `status=draft` and `published_at=NULL`. The
application executor has no publication or activation capability. Existing
published bindings and runtime provenance remain on exact vN. Publication and
any future activation/release remain separate, unauthorized governance acts.

## 5. Forward governance

Forward application requires one complete, exact and immutable chain:

```text
LearningProposal revision + CanonicalDelta
-> LearningProposalReview
-> approved LearningProposalDecision
-> VALID LearningApplicationAuthorization
```

Every artifact must carry the same proposal, target vN, operation, schema,
canonicalization and delta-hash tuple. `LEGACY_INERT` or partially populated
tuples are permanently ineligible. No application-time change payload is
accepted.

## 6. Compensation governance

Compensation is not rollback and does not claim a runtime restoration. It is a
new, independently governed application of the same exact operation profile:

```text
forward:      R1 -> R2, target vN,   result vN+1
compensation: R2 -> R1, target vN+1, result vN+2
```

Compensation requires a new Proposal, CanonicalDelta, Review, Decision,
Authorization, idempotency identity and Receipt. It targets vN+1, references
the exact forward Receipt, proves vN+1 is the unchanged draft current head, and
recovers R1 only from the immutable vN/forward provenance. The forward
Authorization cannot be reused.

## 7. Exact application preconditions

Under one transaction and fixed lock order, the future service must revalidate:

- complete canonical-delta eligibility and exact governance tuple;
- authorization validity and application idempotency claim;
- target ID, lineage, version, full-row hash and current-head status;
- exact predecessor and absence of an intervening child;
- source reference, published edition and source hash;
- before/after substantive semantic fingerprint equality;
- `status=draft,published_at=NULL` for every result;
- for compensation, exact forward Receipt, original vN reference and unchanged
  vN+1 application result; and
- executor authority, operation ID/version and delta hash.

Any missing, stale, conflicting or unknown value denies the whole operation.

## 8. Idempotency, concurrency and no-fork

Forward and compensation use independent durable identities. Exact replay
returns the same successor and Receipt; changed provenance is conflict. Locks,
the existing unique predecessor relation and a fixed current-head check ensure
that two callers can create at most one child. A competing successor makes the
losing attempt stale/conflict; timing never creates two children.

## 9. Capability and least privilege

The POC may introduce only a dedicated executor such as
`learning_knowledge_rule_application_executor`. It must be non-superuser,
`NOINHERIT`, `NOBYPASSRLS`, non-owner and unable to `SET ROLE` to any curator or
function owner. It receives no target-table INSERT/UPDATE/DELETE/TRUNCATE,
publication, activation, ModelPolicy, AgentDefinition or normative-curator
authority.

The executor may invoke only one fixed-signature capability that locates the
already-governed delta by identifiers/hashes. It accepts no target type, field,
arbitrary value, status, publication state, operation selector or JSON patch.

Any `SECURITY DEFINER` functions use dedicated NOLOGIN, non-superuser,
`NOINHERIT`, `NOBYPASSRLS` owners; fixed `search_path=pg_catalog`; fully
qualified objects; no dynamic SQL; PUBLIC revoke; no schema CREATE, table/
sequence ownership, role membership, `SET ROLE`, TRIGGER, ALTER or TRUNCATE
authority; and exact catalog assertions. The role with minimal target INSERT is
unreachable except through private typed functions and is guarded by target
constraints/triggers.

## 10. Canonical curator reuse

Architecture D is mandatory: one application service, one physical connection,
one outer transaction and a dedicated canonical database primitive. A private
shared domain primitive owns lineage, predecessor, draft-result, immutable
field, version uniqueness and target-curation ledger semantics. The existing
curator path and the exact governed application wrapper delegate to it.

The private primitive is not executable by runtime or the application
executor. Existing curator signature, validation, published-predecessor rule,
publication behavior, errors and audit behavior must remain equivalent and be
proved by golden parity tests. Parallel ORM/SQL business rules are prohibited.

## 11. Receipt, target event and audit

Each successful application creates one immutable Receipt binding the exact
proposal/review/decision/authorization tuple, operation/schema/canonicalization,
delta hash, target lineage, before/result IDs/versions/hashes, predecessor,
semantic fingerprints, actor, trace, timestamps, target curation audit and
target-event/outbox references. It records:

```text
external_effects=false
runtime_effect_changed=false
result_status=draft
result_published=false
```

The compensation Receipt additionally binds the forward Receipt, vN+1 and the
original safe R1 provenance. It must not imply that vN+1 was active.

The POC may define exactly one target-domain event contract,
`knowledge_layer_rule.source_reference_corrected` schema v1, with a global/
platform scope and no fake tenant. Event and outbox carry only bounded IDs,
hashes and state facts. No learning-application lifecycle DomainEvent is
authorized; Receipt plus immutable audit record the application lifecycle.

## 12. Atomicity and retained history

Claim, governance revalidation, target lock, canonical delta validation,
semantic fingerprint proof, successor, target curation ledger, target event,
outbox, Receipt and application audit commit together or not at all. There are
no provider, network, notification, filesystem or other external effects.

After the first application history exists, downgrade across the migration
that owns successor/Receipt/event/audit contracts is forward-only. Operational
disablement revokes EXECUTE and preserves all history. Schema rollback is not
compensation and must never delete or rewrite vN+1, vN+2 or provenance.

## 13. Explicit prohibitions

This policy does not authorize:

- mutation, deletion or predecessor re-pointing of vN/vN+1;
- a fork, cycle, self-predecessor or arbitrary snapshot restoration;
- publication, activation, deployment or runtime adoption;
- a second target or replacement operation identity;
- ModelPolicy or AgentDefinition rehabilitation;
- RequirementControl, Standard, StandardEdition, Clause, binding or
  certifiability mutation;
- generic curator/DML authority or an executor allowlist change;
- legacy governance upgrade/backfill;
- automatic EffectivenessCheck, LearningSignal, Proposal or optimization; or
- production, staging, shared DEV/QA, external systems or licensed content.

## 14. Authorization limit and change control

This policy authorizes only an isolated, disposable PostgreSQL 18.6 Phase 26
POC with mandatory teardown. POC promotion can mean only that the exact inert
application/compensation mechanism was demonstrated. Production use,
publication, activation, another operation, another target, broader authority
or an application lifecycle event requires a new Product Policy and gate.

Correction or withdrawal uses a successor policy; this record is never
rewritten.
