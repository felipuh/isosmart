# Phase 31.4.4 — Row-level execution contract closure gate

## 1. Verdict

`PHASE 31.4.4 — PROMOTED — ROW-LEVEL EXECUTION-READY V2 CONTRACT COMPLETE; FUTURE CLEAN PHASE 31.4 RETRY ELIGIBLE`

## 2. Entry B1–B4

Entry was B1=false, B2=false, B3=false, B4=false with P0=0/P1=4. Exit is
B1=true, B2=true, B3=true, B4=true with P0=0/P1=0.

## 3. Git baseline

The exact initial `git status --short` was:

```text
 M backend/backend/settings.py
 M backend/integration/assistant_memory_views.py
 M backend/integration/serializers.py
 M backend/integration/tests.py
 M backend/integration/views.py
 M backend/leadership/serializers.py
 M backend/leadership/views.py
 M backend/test_default.sqlite3
 M frontend/src/components/Assistant/VirtualAssistantPanel.jsx
 M frontend/src/components/Auth/OnboardingGuard.jsx
 M frontend/src/components/Common/CrudEmptyState.jsx
 M frontend/src/components/Common/CrudErrorBanner.jsx
 M frontend/src/components/Common/CrudPageHeader.jsx
 M frontend/src/components/Layout/Header.jsx
 M frontend/src/components/Layout/Layout.jsx
 M frontend/src/components/Layout/Sidebar.jsx
 M frontend/src/context/I18nContext.jsx
 M frontend/src/features/improvement/pages/ImprovementCorrectiveActionsPage.jsx
 M frontend/src/features/improvement/pages/ImprovementNonconformitiesPage.jsx
 M frontend/src/features/operations/pages/CustomerRequirementsPage.jsx
 M frontend/src/index.css
 M frontend/src/pages/ForgotPasswordPage.jsx
 M frontend/tests/e2e/assistant-runtime.spec.js
 M frontend/vite.config.js
?? AGENTS.md
?? backend/foundation/
?? backend/leadership/tests.py
?? backend/logs/
?? docs/adr/
?? docs/governance/
?? docs/operations/
?? docs/transformation/
?? frontend/tests/e2e/onboarding-guard-runtime.spec.js
```

Initial `git diff --check` returned the preserved pre-existing error:

```json
"frontend/src/components/Layout/Sidebar.jsx:28: trailing whitespace.\n+    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' }, \n"
```

## 4. Hash baseline

The frozen migration-set hash remains
`cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc`.
ADR-0017 remains
`82501ef34edc6d7e76e0971d3d2607c58f229a1dd4dd26696dd227fb7e994edb`;
migration 0022 remains
`afefd7100a18e5c7324efaeb1af656225b309fd86f08673a8742f7f9f6c2e618`.

## 5. Mandatory reading

`mandatory_reading_complete=true`. All 82 paths in the Phase 31.4.3 ledger plus
four associated Phase 31 preflight/audit runner and test modules (86 total)
were read completely for semantic behavior, including the reports, diagnostics,
tests, ADRs, policies, fixtures, migrations, complete Phase 26 harness, Phase
28.3 paths and relevant service/security/audit/event/recovery code. The complete
per-file record is `PHASE31_4_4_MANDATORY_READING_LEDGER_V1.json`; hash, JSON,
AST and model-metadata checks were not treated as substitutes.

## 6. Row universe

`row_universe_complete=true`. The V2 machine contract declares 118 exact rows
across 53 qualified tables/artifact indexes. No producer may write outside it.

## 7. Identity taxonomy

Every row has exactly one allowed identity mode. Collision identity is
`(qualified_table, primary_key)`, never UUID alone.

## 8. Native release identity rules

Migration 0022's MD5 parent/suffix formatter and version/variant nibbles are
preserved exactly and tested against Publication and Activation vectors.

## 9. ADR0017 boundary

ADR-0017 is byte-identical and maps exactly seven Application outputs. All
other enumerated deterministic replacements are adopted by ADR-0018.

## 10. Support graph

The declared chain is tenant/organization/user/process and normative supports;
under-evaluation Opportunity; provenance; decision; plan; dry run; human
approval; authorization; controlled defer; deferred revision; receipt;
Evidence; Effectiveness; LearningSignal; ProposalSignal.

## 11. Catalog fixture

One published synthetic ModelPolicy and one published synthetic AgentDefinition
plus four distinct eight-field governance curation audits are exact rows.
Classification is `ISOLATED_SYNTHETIC_CATALOG_FIXTURE`; runtime adoption,
provider/tool/model execution, deployment and normative authority are false.

## 12. AgentRun

The exact run freezes definition, policy, tenant, organization, capability,
autonomy zero, synthetic model provenance, timestamps, trace, running→completed
status and retention. No provider/tool call exists.

## 13. Inputs/bases/output provenance

One AgentRunInput, one RecommendationBasis, one Recommendation and one
AgentRunRecommendation are declared. The six-column input/basis equality key is
frozen and checked in both directions.

## 14. AgentDecision

The AgentDecision is an independent synthetic-agent record and precedes the
ActionPlan. It is not human Approval.

## 15. ActionPlan/DryRun

The only action is `opportunity.defer_evaluation`; target, hashes,
preconditions, reversibility, impact, dry-run result and trace are exact.

## 16. Approval

Approval is a later human decision with fresh authority and separate identity,
not a reuse of AgentDecision or Review.

## 17. ExecutionAuthorization

Authorization binds plan, dry run, Recommendation, AgentDecision, AgentRun,
AgentDefinition, ModelPolicy, approval, impact, reversibility and authority.

## 18. Controlled execution

Exactly one internal controlled defer operation is permitted. No external
business effect exists.

## 19. Receipt

The exact immutable receipt binds execution, plan hash, before/after revisions,
result hash, executor and trace.

## 20. Opportunity revisions

Revision 1 is `under_evaluation`; revision 2 is `deferred`, names revision 1 as
predecessor and preserves lineage, process, tenant and organization.

## 21. Evidence

The eligible revision is `NON-OFFICIAL TEST FIXTURE`, revision 1, predecessor
NULL, with canonical content hash and no licensed ISO material.

## 22. Effectiveness

Revision 1 binds succeeded execution, receipt, both Opportunity revisions,
evidence and human authority. `due_at` is deferred creation plus one second and
`assessed_at=due_at`. Outcome is derived as effective only from exact observed
deferred evidence; it is not predeclared merely to enable learning.

## 23. LearningSignal

The persisted row uses only model columns and freezes the complete one-revision
Effectiveness history. The retained semantic envelope separately says synthetic
true, automatic_learning false, normative false and production false.

## 24. ProposalSignal

One composite semantic link naturally associates the Proposal with the actual
LearningSignal; no trigger or FK bypass is authorized.

## 25. Supporting producer

`phase31.4.4-exact-support-producer/v1` is parameterless and accepts only the
declared experiment. Arbitrary table/model/UUID/operation/actor/JSON/target or
field arguments are impossible.

## 26. Transaction composition

Each operation owns connection and BEGIN, binds trusted context, validates,
writes, immediately revalidates, commits and retains. There is no giant outer
transaction around native services.

## 27. Producer security

Owner and executor are exact non-owner, NOSUPERUSER, NOINHERIT, NOBYPASSRLS
roles; owner is NOLOGIN. Search path is `pg_catalog`; no dynamic SQL or PUBLIC
EXECUTE exists.

## 28. Table privilege matrix

All 53 touched tables have an explicit row in `security_rls_matrix`. Execution
is through exact functions; generic INSERT/UPDATE/DELETE grants are false.

## 29. RLS matrix

Every tenant table has a forced exact-role, exact-tenant ephemeral policy with
both USING and WITH CHECK semantics. A grant without policy fails validation.

## 30. Audit identity rules

Immutable audit uses execution-derived native UUIDv7 and is retained before
use. Governance, normative curation, immutable stream and 0022 release audits
remain distinct.

## 31. B1 root bootstrap

B1 is closed by draft→governed native publication→commit→two independent
read-only rereads→PostgreSQL byte equality→full target freeze.

## 32. Root admission

`knowledge-layer-rule-root-bootstrap-governed-admission/v1` binds only causally
available pre-root facts and never depends on candidate Application/B2/B3.

## 33. PostgreSQL render profile

The required profile is PostgreSQL 18.6, UTF8 server/client, UTC, ISO,YMD,
iso_8601, standard strings on, libc/C.UTF-8 collation and ctype, and
extra_float_digits=3 (asserted but immaterial to the no-float canonical set).

## 34. Root target artifact

The typed schema retains all 13 persisted fields, raw JSONB, canonical bytes,
full hash, schema/migration identity, dual-read provenance and render snapshot.
Mode is `EXECUTION_DERIVED_PERSISTED`.

## 35. Proposal V2

Proposal is created only after Freeze 1 and 1.5. Rationale, effect, risks,
domains, revision, predecessor NULL, signal and target are exact at Freeze 0 or
uniquely derived.

## 36. Delta V2

The only operation is
`learning.knowledge_layer_rule.source_reference.correct/v1`. Target hash comes
from Freeze 1; Delta hash is constructed, persisted and reread at Freeze 2.

## 37. Review V2

Review records native `review_recorded` only if Freeze 2 target/Delta equality
and fresh reviewer authority pass. It is not Approval.

## 38. Decision V2

Decision may approve only a valid exact review set. Its rationale, policy,
ordered review-set hash algorithm and approver role are frozen.

## 39. Authorization V2

Authorization exists only after Proposal, Delta, Review and Decision and binds
target, capability, authorizer, policy, caller key and fresh authority.

## 40. Publication native contract

The migration 0022 native formula, inputs, atomic graph and precommit checks are
unchanged.

## 41. Publication governed admission

The V2 schema contains only pre-Publication facts and separately retains native
and governed hashes. It binds Application receipt/parity but no B2/B3/closure.

## 42. Publication replay

Exact same native and governed material retrieves the immutable prior result;
changed governed material conflicts. Fresh retrieval authority cannot replace
original operation authority.

## 43. Checkpoint

The checkpoint explicitly enumerates native Publication and preceding
Application/source members. It excludes itself, B2, B3, final closure and
Activation and passes cycle analysis.

## 44. B2 schema

ID `37d3d0bc-4387-581a-a627-f02a011250d1` uses the complete typed compatibility
schema and pre-Activation facts only.

## 45. B2 producer

After checkpoint, an independent read-only transaction observes and retains B2;
a second independent transaction verifies it. Its digest is not prebound.

## 46. B3 schema

ID `981e1753-dcd1-5f8d-8b10-49bfaed5eafb` binds Publication graph, checkpoint,
B2, source/policy, zero adoption and false runtime effect without configuration
fields or final-closure self-reference.

## 47. B3 producer

Order is native Publication, checkpoint, B2, B3, final Publication closure,
using independent reads and execution-derived digests.

## 48. Publication eligibility

The distinct postpublication artifact requires native graph, checkpoint, B2,
B3, closure and export/live equality with reconstruction_required=false.

## 49. Activation native contract

Migration 0022 Activation and its compatibility-hash input remain unchanged.

## 50. Activation governed admission

The schema binds candidate, Publication, closure, B2, B3, predecessor, fresh
authority, policy/capability/caller, both hashes, trace, zero adoption, schema
and registry with immediate precommit verification.

## 51. Activation replay

Activation uses the same immutable-original/fresh-current replay rule as
Publication and never substitutes provenance.

## 52. Original vs replay authority

Both provenance objects are explicit and separate for every replayable
operation. Changed business material is conflict.

## 53. Event/Outbox/Audit inventory

Every actual support/lifecycle/release event, outbox and audit is an individual
future row. Operations with no native event/outbox do not invent one.

## 54. Field taxonomy

The total, ordered classification rules expand against exact table columns and
artifact fields. Every field has one class, source, freeze and verifier;
`unknown_binding_count=0`.

## 55. Producer matrix

All 118 created/required rows map one-to-one to one versioned producer contract.
`producer_matrix_covers_every_created_row=true`.

## 56. Registry V2

Registry V2 has 117 row/artifact-specific edges. Each edge has source, edge,
target, cardinality, disposition, canonicalization, freeze and verifier.

## 57. Closure V2

Closure is a fixed point of the live schema/FK snapshot and Registry V2. All
local members retain full material; external authority retains frozen
provenance; unknown dispositions are zero.

## 58. Freeze graph

The exact 15-point order from Freeze 0 through Freeze 9 is acyclic. Publication
closure precedes Activation.

## 59. Fixed-hash audit

Every fixed digest is a source/preimage/policy/historical class. Future target,
Delta, B2 and B3 digests are execution-derived and not numerically fixed.
`fixed_hash_without_preimage=0`.

## 60. ADR0018

ADR-0018 is accepted and adopts execution-ready V2, Model B, row identity,
identity minimization, producer transactions/security, admission separation,
replay provenance, sequencing, eligibility, freezes and closure V2.

## 61. Product Policy successor

The V2 Product Policy authorizes only future clean retry eligibility and
explicitly supersedes defective Phase 31.3 operational expectations.

## 62. Lifecycle spec V2

The 279,997-byte consolidated machine contract is the complete lifecycle spec
V2 and contains the row universe, matrices and all consolidated typed schemas.

## 63. Positive tests

Positive tests cover row/producer/identity/field/RLS completeness, native
vectors, B1, support provenance, Effectiveness/Signal, B2/B3/checkpoint,
admissions, replay, fixed hashes, Phase 29 exclusion, zero RuntimeAdoption,
registry/closure and freeze acyclicity.

## 64. Negative tests

Mutation tests reject all required hostile classes: missing producer/identity,
duplicate qualified identity, universal UUIDv5, altered native child, missing
RLS policy, nested context, generic parameters, drafts, missing provenance,
wrong ordering, incomplete Effectiveness/Signal/Proposal, predicted hashes,
publication cycles, hash collapse, replay substitution, unknown fields/freezes,
Phase 29 dependency and RuntimeAdoption.

## 65. Migration/source/protected hashes

All 23 migration and 223 protected/source hashes match the Phase 31.4.3 frozen
baseline. Migration 0024 is absent. Successor contract, registry and closure
hashes before this report were respectively
`962ec0b393b49c3c0a2894e32bb9a3246cbf7793cfd600391248634bee56f70b`,
`58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb`,
and `80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425`.

## 66. Git hygiene

Only append-only Phase 31.4.4 artifacts/tests were added. No reset, stash,
clean, stage, commit, normalization or unrelated rewrite occurred. The existing
Sidebar line 28 whitespace remains untouched.

## 67. Zero effects

```text
database effects=0
PostgreSQL effects=0
support fixture execution effects=0
Opportunity execution effects=0
Effectiveness effects=0
LearningSignal effects=0
Proposal effects=0
Application effects=0
Publication effects=0
Activation effects=0
RuntimeAdoption effects=0
resolver invocation=0
runtime effects=0
production effects=0
staging effects=0
shared DB effects=0
real AdminApps effects=0
external API effects=0
normative effects=0
automatic learning effects=0
external business effects=0
Phase29 reconstruction effects=0
```

## 68. P0/P1

P0=0; P1=0.

## 69. Residual blockers

None. PostgreSQL operational assertions remain intentionally `NOT EXECUTED` and
belong exclusively to the authorized clean retry; this is not an offline
contract blocker.

## 70. Final verdict

`mandatory_reading_complete=true`; B1=B2=B3=B4=true;
`execution_ready_v2_adopted=true`; `model_b_adopted=true`;
`row_universe_complete=true`; `taxonomy_covers_every_lifecycle_field=true`;
`producer_matrix_covers_every_created_row=true`; `freeze_graph_acyclic=true`;
`unknown_binding_count=0`; `fixed_hash_without_preimage=0`; P0=0; P1=0.

## 71. Exactly one NEXT_CODEX_PROMPT

```text
PHASE 31.4 — CLEAN RETRY 2 — ISOLATED EPHEMERAL POSTGRESQL 18.6 CREATION-THROUGH-ACTIVATION POC

Work exclusively in /home/felipe/proyectos/isosmart. Read AGENTS.md, ADR-0018,
the V2 Product Policy, PHASE31_4_4_ROW_LEVEL_EXECUTION_CONTRACT_V2.json,
PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json,
PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json, the supporting producer
contract, and the Phase 31.4.4 gate report completely. Consume V2 exclusively;
the Phase 31.3 operational target/Delta/B2/B3 expectations are superseded.

After recording git status --short and git diff --check, and only if the user
has authorized this retry, create one isolated ephemeral PostgreSQL 18.6 POC
with the exact render profile and roles/policies from V2. Never touch shared,
staging or production data. Do not use Phase 29 identities or reconstruction.

Execute exactly: support fixture → root draft → root governed publication →
commit → two independent root target rereads and Freeze 1 → supporting
Effectiveness/LearningSignal Freeze 1.5 → Proposal/Delta → Review → Decision →
Authorization → ADR-0017 reference/adapter parity → Application → Publication
governed admission → native Publication → Publication checkpoint → B2
compatibility → B3 release → final Publication closure → independent export/live
comparison → publication-eligible-for-activation → Activation governed admission
→ native Activation → complete fixed-point closure → teardown authorization →
teardown → post-teardown offline verification.

Require Publication closure before Activation, zero RuntimeAdoption and runtime
cutover, no provider/tool/model call, and exact original/replay authority
separation. Run RLS/ACL hostile and cross-tenant denial tests plus rollback,
concurrency, idempotency, governed-material conflict, native-child vector,
precommit drift and closure-before-teardown tests. Retain every execution-derived
timestamp, UUIDv7 audit ID and digest before downstream use. Compare live export
to retained closure before teardown. Report database effects precisely, do not
advance to Phase 32, and tear down only after retained closure and explicit
teardown authorization are complete.
```
