# Phase 24.2 — Exact Learning Delta + Target Operation Contract Inert Foundation

- Date: 2026-08-25
- Workspace: `/home/felipe/proyectos/isosmart`
- Authorization: Phase 24.1 promoted additive inert contract foundation only
- PostgreSQL: official isolated 18.6 image
- Final database run: `20260825T214926Z_d18762`
- Target successors/application/external effects: **ZERO**
- Verdict: **PROMOTED — ZERO P0/P1 BLOCKERS**

## 1. Phase 24.1 contract mapping

Phase 24.2 implements only the Phase 24.1 foundation: proposal-owned canonical
delta material, deterministic versioned canonicalization, direct immutable
binding through review/decision/authorization, permanent legacy inertness, and
three exact typed operation profiles. It does not select a profile, apply a
proposal, write a target, create a successor, publish, activate, deploy, create
an application receipt/event/executor, or install a curator application
function.

Architecture D remains a future boundary only: one connection and a dedicated
canonical database primitive. Migration 0020 contains inert validation helpers,
not a target curator primitive. No function performs target DML.

## 2. Migration and schema

Migration `0020_exact_learning_delta_target_operation_contract` is the only new
migration. It adds tenant/Organization-scoped
`qms.learning_proposal_canonical_delta`, a deferred immutable one-to-one pair
with `LearningProposal`, and nullable complete-tuple columns on proposal,
review, decision and authorization.

The new table stores the parsed document, exact UTF-8 bytes and SHA-256. Both
foreign-key directions are `DEFERRABLE INITIALLY DEFERRED`, so preallocated
proposal/delta UUIDs commit together or neither commits. Existing rows receive
no defaults and no backfill. Empty-history `0019 -> 0020 -> 0019 -> 0020`
passed; downgrade after retained exact history is denied.

Database triggers reject UPDATE, DELETE, replacement and rebinding. Complete-
tuple constraints permit only all-null legacy state or a fully specified v1
binding. The authorization constraint preserves old `revise_*` history while
requiring new-format authorizations to use their exact operation ID/version.

## 3. Canonicalization algorithm

Identifier: `iso-smart-learning-delta-canonical-v1`.

The canonicalizer accepts one exact schema object; rejects unknown fields,
null, floats, exponent/non-finite numbers, non-string object keys, unsupported
types and lone Unicode surrogates; emits sorted Unicode-code-point keys,
ordered arrays, minimal integers, UTF-8 without BOM, no insignificant
whitespace and deterministic JSON escaping. UUIDs and hashes are exact lowercase
forms. Set-arrays are non-empty, unique and already sorted.

The database independently verifies UTF-8 parsing, exact recursive canonical
serialization, exact top-level keys, tuple equality and:

```text
delta_hash = lowercase_hex(SHA-256(canonical_bytes))
```

Canonical bytes are built by the service from a typed command. Callers cannot
supply canonical bytes or a hash to the exact-format creation path.

## 4. Exact delta schemas and validation profiles

| Target | Operation ID/version | Schema | Exact allowed surface |
|---|---|---|---|
| ModelPolicy | `learning.model_policy.approved_models.remove` / `v1` | `learning-model-policy-approved-model-removal-delta-v1` | non-empty sorted set of already-approved models plus successor version; additions, substitutions and unrelated fields rejected |
| AgentDefinition | `learning.agent_definition.autonomy.reduce` / `v1` | `learning-agent-definition-autonomy-reduction-delta-v1` | integer `0 <= new < current <= 4` plus successor version; equality, increase and unrelated changes rejected |
| KnowledgeLayerRule | `learning.knowledge_layer_rule.source_reference.correct` / `v1` | `learning-knowledge-layer-rule-source-reference-correction-delta-v1` | locator-only correction under exact `iso-smart-source-ref-v1` grammar, published edition UUID and source hash; guidance/linkage/classification changes structurally absent |

Unit vectors prove all three accepted paths and their negative surfaces. No
arbitrary mutation map, generic target type, wildcard operation, status/field/
value payload or application-time replacement exists.

## 5. End-to-end hash binding

The exact immutable tuple is directly carried by every new-format artifact:

```text
proposal id/revision/material hash
+ canonical_delta_id/canonicalization/schema
+ operation id/version/delta_hash
+ exact target type/id/lineage/version/hash
```

Review reloads the proposal-owned bytes, independently re-canonicalizes and
rehashes them, and copies the tuple. Decision requires every selected review to
carry that identical tuple. Authorization requires the decision and proposal
tuple and the exact new operation identity. Proposal material, review-set,
decision-identity and authorization-idempotency hashes include the tuple.

The PostgreSQL run proved one identical tuple across proposal, delta, review,
decision and authorization. Old `revise_model_policy` was rejected for an exact
ModelPolicy delta. Exact authorization replay returned the same artifact;
concurrent exact proposal/delta creation produced independent one-to-one pairs
with identical deterministic content hashes.

## 6. Permanent legacy inertness

Every pre-contract or deliberately hash-only proposal/review/decision/
authorization is classified `LEGACY_INERT`. Eligibility uses a positive
complete-tuple predicate; partial tuples also classify inert. Migration 0020
does not attach, infer, default, backfill or reinterpret any delta.

PostgreSQL created a complete legacy governance chain after migration and proved
all four artifacts remained inert. The old capabilities remain historical
metadata only and cannot authorize an exact-format chain.

## 7. Atomicity, immutability and concurrency

Exact proposal creation uses the existing single outer Django transaction:
canonical delta + proposal + signal links + authorized
`learning_proposal.created` event + TransactionalOutbox + ImmutableAuditLog.
No new event was invented.

Forced failure after delta, proposal, links, event, outbox, audit and before
commit passed 7/7 with zero half-pairs or partial governance provenance. Raw
UPDATE of canonical delta was denied. Deferred bidirectional FKs, unique owner
relations, append-only triggers and exact tuple checks reject replacement and
rebinding.

## 8. RLS, grants and Architecture D boundary

`learning_proposal_canonical_delta` has both ENABLE and FORCE RLS. Its SELECT
policy is tenant-context scoped for the four existing governance principals;
only learning governance receives INSERT. Review, approver and authorizer are
read-only. PUBLIC has no execution right on Phase 24.2 functions.

The complete-binding helper is executable only by those four principals because
PostgreSQL CHECK constraints require it. Canonical-byte validation is a fixed-
signature, fully qualified, fixed-search-path inert validation function. There
is no dynamic SQL, target mutation, application dispatch or generic primitive.

Catalog assertions proved every Phase 24.2 principal has zero INSERT/UPDATE/
DELETE over ModelPolicy, AgentDefinition and KnowledgeLayerRule. No executor,
curator role, target DML grant or application-function EXECUTE grant was added.

## 9. Threat and security matrix

| Threat | Control/result |
|---|---|
| payload substitution | proposal-owned exact bytes only; independent service/DB recomputation PASS |
| unknown/reinterpreted schema | exact top-level/payload keys and version pair; fail closed PASS |
| delta replacement/rebinding | deferred one-to-one FKs plus append-only triggers PASS |
| stale/latest target | exact target identity/version/hash in every artifact; no `latest` lookup PASS |
| capability aliasing | three new IDs; old `revise_*` rejected for exact chain PASS |
| model expansion/guardrail weakening | removal-only typed schema; unrelated fields absent PASS |
| autonomy no-op/escalation | strict A0–A4 decrease predicate PASS |
| normative/guidance mutation | locator-only same-edition/source-hash grammar PASS |
| legacy authority resurrection | all-null/complete positive predicate; no defaults/backfill PASS |
| tenant/cross-Organization access | composite tenant/Organization FKs and ENABLE+FORCE RLS PASS |
| raw SQL/direct mutation | table ACL plus immutable triggers PASS |
| privileged function abuse | fixed signature/search path, qualified objects, no dynamic SQL, PUBLIC revoked PASS |

## 10. Protected-target invariance and zero application

Count plus ordered full-row digests for ModelPolicy, AgentDefinition,
KnowledgeLayerRule, Standard, StandardEdition, Clause and RequirementControl
were identical before and after rollback, success, governance, replay,
concurrency and negative tests. Exactly zero target successors were created.

`agent_runtime.py` remained `6767e209…` and `knowledge_layer.py` remained
`ad355cd3…`. Changes in `models.py` are confined to additive inert learning
metadata models/fields; target model definitions and curator services were not
changed. Repository scans and the event set prove no application executor,
target writer, target DML grant or application/target/autonomy event exists.

## 11. Verification results

| Gate | Result |
|---|---|
| Exact canonicalization/profile tests | 10/10 PASS |
| Full foundation suite | 97/97 PASS |
| Full backend apps suite | 195/195 PASS |
| Django system check | PASS, zero issues |
| `makemigrations --check --dry-run` | PASS, no drift |
| Python compilation | PASS |
| PostgreSQL 18.6 Phase 24.2 | PASS, run `20260825T214926Z_d18762` |
| Migration 0020 empty-history F/R/F | PASS |
| Exact rollback boundaries | 7/7 PASS |
| Inherited Phase 13/14/16/17/19 PostgreSQL gates | PASS |
| Exact Phase 21 proposal/event/outbox/audit path on latest schema | PASS |
| Exact Phase 23 review/decision/authorization path on latest schema | PASS |
| Protected target invariance | PASS |
| Teardown | container, volume, roles/database and temporary directory absent PASS |

The backend suite attempted pre-existing Chroma/PostHog telemetry DNS; sandbox
resolution failed and no request succeeded. Phase 24.2 code performs no network,
provider, notification or external-system call.

## 12. Frozen hashes

Migrations 0001–0019 match their promoted SHA-256 values exactly:

`0d72f262…`, `1f538ca4…`, `dadfad2c…`, `04504327…`, `96ab33a1…`,
`033242bd…`, `c7f6a203…`, `285aecb3…`, `412c6459…`, `c4f37a9a…`,
`cdb23edc…`, `7f280e24…`, `06177fde…`, `ee0e42a7…`, `5e297591…`,
`e922ff20…`, `580f16d1…`, `703a8588…`, `c188b638…`: **19/19 MATCH**.

Migration 0020 SHA-256:
`491f21d3422c9c9a5866520f6623d3b9c9bea2139083f0128495dd7207d19894`.

The ten authoritative source hashes are **10/10 MATCH**:
`8308bde9…`, `e0a59c91…`, `11c2b461…`, `952d8ac9…`, `ecaecd25…`,
`30e3c052…`, `de1b4899…`, `29ac5c2d…`, `c41e847e…`, `eb42315c…`.

Frozen governance/report prerequisites also match: governed learning policy
`7d9c2fe3…`; implementation authorization `04458c4f…`; Phase 22 boundary
`2d5beaeb…`; ADR-0012 `4fd6b330…`; Phase 21 `682dc465…`; Phase 22
`a94ba44e…`; Phase 23 `4cfe38a2…`; Phase 24 `7b01976e…`; Phase 24.1
`c00577ad…`.

## 13. External effects, teardown and residual risks

There were zero production, staging, shared database, AdminApps, MedSupplier,
provider, notification, deployment or target effects. All isolated PostgreSQL
resources were removed and absence verified after failures and final success.

Residual later-scope risks are not Phase 24.2 blockers: no target/profile is
selected; no application claim/receipt or curator primitive exists; publication,
activation, runtime adoption and compensation remain outside scope; live
AdminApps resolution is not enabled. These restrictions are intentional and
preserve zero application authority.

## 14. Promotion verdict

**PHASE 24.2 — EXACT LEARNING DELTA + TARGET OPERATION CONTRACT INERT
FOUNDATION: PROMOTED.**

Promotion authorizes only a later target-selection/application **design gate**.
It does not authorize target application, a successor, an executor, target DML,
publication, activation, deployment or external effects.

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `learning_delta.py` | PASS | deterministic v1 canonicalizer + three typed profiles; 10/10 tests | freeze v1 semantics |
| `models.py` inert learning additions | PASS | proposal-owned delta and direct nullable tuple | never backfill legacy rows |
| migration 0020 | PASS | additive; F/R/F; RLS/ACL/immutability | forward-only after retained exact history |
| `governed_learning.py` | PASS | typed delta built with proposal/event/outbox/audit atomically | no caller bytes/hash |
| `learning_proposal_governance.py` | PASS | exact tuple verified and copied end to end | no old capability alias |
| PostgreSQL harness | PASS | 18.6 rollback/concurrency/RLS/target invariance/teardown | retain isolated lifecycle |
| protected targets | UNCHANGED | complete-row digests equal; zero successor | target application remains prohibited |
| runtime/external effects | ABSENT | no executor/event/grant/network/deployment | later design gate only |

## NEXT_CODEX_PROMPT

Execute PHASE 24.3 — FIRST EXACT LEARNING TARGET PROFILE SELECTION + APPLICATION
SECURITY DESIGN GATE exclusively in `/home/felipe/proyectos/isosmart`. Treat
Phase 24.2 as an inert promoted foundation only. Read and preserve migrations
0001–0020, all authoritative sources, governance history and protected targets.
Do not implement target application, create a successor, executor, application
receipt/event, curator function, DML/EXECUTE grant, publication, activation,
deployment or external effect. Compare the three exact v1 profiles using the
implemented canonical delta and end-to-end binding evidence; select at most one
profile only if its exact target-specific curator primitive, one-connection
atomicity, least privilege, TOCTOU, idempotency, concurrency, compensation,
draft-only result, runtime invariance and security tests can be specified
without broadening any capability. Emit PROMOTED only for a later separately
authorized implementation gate with zero P0/P1 blockers; otherwise emit NOT
PROMOTED with the exact blockers. Return exactly one self-contained
`NEXT_CODEX_PROMPT`.
