# ISO SMART AI — Phase 31.3 new complete retained synthetic lifecycle design and authorization gate

- Decision date: 2026-09-04 (`America/Costa_Rica`)
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: design, governance and future authorization only
- Database/lifecycle execution: none

## 1. Decision summary

The gate decision is recorded once in §60. The package authorizes eligibility
only for one future isolated ephemeral creation-through-Activation POC. It does
not say that any new fixture, Publication or Activation exists.

## 2. Entry baseline and initial Git status

The required initial `git status --short` and targeted `git diff --check` were
run before edits. Entry porcelain was:

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

The targeted entry whitespace check passed when the explicitly preserved
`frontend/src/components/Layout/Sidebar.jsx:28` warning was excluded. No entry
file was staged, stashed, reset, normalized, reformatted or committed.

## 3. Frozen baseline

Migrations 0001--0023, migration 0024 absence, Phase 25.1--31.2 reports,
ADR-0013--0016, existing policies, four historical evidence files, ten
authoritative sources, protected runtime/application code, and Phase 28.3/29
fixture/evidence remain byte-frozen. Entry hashes were captured before edits
and compared at exit. Hash equality proves byte integrity, not semantic
completeness.

## 4. Mandatory reading actually completed

Semantic review covered `AGENTS.md`; lifecycle-relevant sections of Phase
25.1--31.2 reports; ADR-0013--0016; all governed-learning, source-reference,
Publication, Activation, RuntimeAdoption, repair, retained-candidate,
Publication-POC, Activation-POC and retention-closure policies; migrations
0008, 0021--0023 plus relevant 0001--0003, 0009 and 0018--0020 schema/event/
authority context; retained Phase 28.3 and 29 evidence/dispositions; Phase 29
export/verifier/harness; Phase 31 diagnostic/tests; release/evidence,
application, eventing, audit, models, AgentRun, Recommendation and resolver
code; PostgreSQL harness patterns; RLS design and ADR-0003. Large reports and
migrations were reviewed by relevant sections rather than claimed as complete
full-file prose reading. All frozen inventories also received full-byte SHA-256
verification, which is distinct from semantic review. No sibling repository or
network/external environment was inspected.

## 5. Permanent Phase 29 classification

Publication `e97576de-d4ef-520d-8592-d376ed401221`, candidate
`01a0682b-dfc8-7b49-a601-f9bda29a70a5`, and missing audit
`12d811ab-c3b4-4615-8972-75008a36e327` remain untouched.

```text
classification=HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE
incident=RETENTION_CLOSURE_BREACH
historical_publication_verified=true
retention_closure_complete=false
faithful_rematerialization_allowed=false
activation_input_allowed=false
runtime_adoption_input_allowed=false
historical_reporting_allowed=true
reconstruction_allowed=false
CREATED=true
APPLICATION_GOVERNED=true
PUBLISHED=true
ACTIVATED=false
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
```

Phase 29 is historical evidence only. There is no retry, reconstruction,
continuity, recovery, bootstrap use, FK replacement/weakening or ID reuse.

## 6. Objective, scope and new namespace

Exactly one future synthetic experiment terminates at Activation:

```text
source -> root rule creation -> governed Application candidate s1
       -> native Publication -> first Activation -> retained closure
RuntimeAdoption=OUT_OF_SCOPE
Runtime Effective=FALSE
```

Namespace material is
`https://iso-smart.local/phase31.3/complete-retained-synthetic-lifecycle/v1`,
namespace UUID `05611a8a-f662-5b7f-ad24-c4df48d573ec`, and experiment ID
`a3f8fd64-af24-5b31-977a-bcaf8146c563`. UUIDv5 label mappings and migration
0022 child-ID derivation are frozen in the lifecycle spec. Eighty-three distinct
UUIDs in the spec had zero collision with retained Phase 28.3/29/31 evidence.

## 7. Deterministic identity inventory

Core identities are source `72d038c3-4ee5-5d40-a75b-398133dbed00`, source
manifest `2bd274fb-3844-532e-8e76-e276153cad2e`, Standard
`9b9a75f6-f3dc-5089-9b27-6aff45ca0556`, StandardEdition
`98939c5e-1a06-53c9-bbf9-07b21d81feb1`, KnowledgeLayer
`ca734de0-7bfe-51e4-acce-639cc5f26f1d`, root/lineage
`bc5f4f17-294d-5abd-b27b-2d296921ffdf`, candidate
`a55716fa-63c7-54eb-bda2-9c9666613b1a`, Proposal
`a0c36b62-ab9e-5852-9228-19891ec48217`, Delta
`96895eeb-41a6-546a-a270-a72147271a4c`, Review
`54aa2fd0-1449-51bc-b543-5e607c84b59a`, Decision
`dbbf331b-0388-51a9-bca7-e9d1bbf84dd5`, Application Authorization
`4768a437-735b-5afb-903a-b362443fb1bf`, Receipt
`b35d11e1-6848-50b2-b760-dd09d38f0acb`, Publication
`cf4db0d2-a312-5a44-91cf-6e14f5cd600e`, and Activation
`676ad5e4-e167-5336-93ae-5a9f1d4388d3`. Every remaining trace, claim,
event, Outbox, Audit, policy, capability, evidence, manifest and disposition
identity is frozen machine-readably. No RuntimeAdoption ID is allocated.

## 8. Exact source fixture and provenance

The exact UTF-8 source is retained as a file, not generated later. Its media
type is `text/plain; charset=utf-8`, schema
`iso-smart-synthetic-source-lines/v1`, canonicalization
`exact-utf8-bytes/v1`, and SHA-256
`e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b`.
It is synthetic, non-authoritative, non-normative, non-licensed, test-only,
non-production, non-certifiable, has zero external business effect and makes
no Phase 29 continuity claim. Locator-before/after hashes are respectively
`32b1e083...81b` and `830e154a...289`; exact strings are frozen in the spec.
Only fixture creation, Application, Publication, Activation and offline
verification are permitted. Runtime, certification and deployment are denied.

## 9. New lineage and candidate contract

The linear rule graph is exact root `s0`, predecessor `NULL`, followed by
candidate `s1`, predecessor root. Root full-material hash is
`3421457f...3af`; exact Application target-row hash is `dbaa2e4e...7db`.
Candidate full-material hash is `e188e130...e3a`, Phase 26 substantive
fingerprint is `23cbf182...4a6`, and Phase 27.2 lifecycle hash is
`93a4e545...f2b`. Algorithms and canonical inputs are frozen. Logic remains
fixture-only, guidance-only and runtime-inert. Selection is exact ID + hashes +
predecessor graph; latest/current/head/max/newest/time selection is prohibited.

Synthetic Standard/Edition/Clause/RequirementControl/Layer support rows are
included solely because frozen FK/publication guards require them. They are
explicitly non-normative and fully retained; no licensed or authoritative
content is present.

## 10. Complete governed Application graph

The exact graph freezes Proposal, canonical Delta, one Review, Decision,
Application Authorization, independent executor authority, claim, candidate,
target event, Outbox, eight-field curation audit, Receipt, immutable
application Audit and curator evidence. Delta SHA-256 is
`06f75de7...19e`; it can change only the locator-before to locator-after in
the same exact synthetic StandardEdition/source hash and create `s1`.

All proposal/review/decision/authorizer/executor/curator actors, permission
names, global scope, policy, fresh authority slots and traces are fixed.
Automatic learning and compensation are not authorized. The transaction is
all-or-zero and cannot mutate any object outside the exact synthetic target.

## 11. Actor/SOD matrix

The eleven actor UUIDs are pairwise distinct: proposer, reviewer, proposal
approver, application authorizer, application executor, curator, publisher,
activator, future adopter placeholder, repair authority, and capability-control
authority. Publisher differs from activator; activator differs from adopter.
Executor and curator do not inherit Publication/Activation. Repair cannot
publish/activate/adopt. Capability control cannot execute the lifecycle. All
prohibited pairings are machine-enumerated and checked at admission and
immediately before commit.

## 12. Publication and complete curation-audit contract

Publication is exact native Publication `cf4db0d2...600e`, candidate `s1`,
publisher `14e64261...1253`, claim equal to Publication ID, event
`0ff9868e...11e2`, Outbox `37816380...f7f6`, governance Audit
`5f33e3ba...a5cc`, and trace `3eabb59e...b442`. Candidate/source/Application,
policy, capability, fresh authority, compatibility/release and operation
hashes are mandatory.

The exact `normative.curation_audit` ID is
`5fa5038d-3042-481f-8162-e1144eebc815`. All eight fields—ID, action,
entity_type, entity_id, actor_id, trace_id, payload_hash and occurred_at—must be
exported as canonical typed material before teardown. The timestamp is the
declared fresh transaction slot; all other fields are frozen. UUID-only
retention fails closure. This makes the Phase 29 defect impossible by design.

## 13. Activation and first-predecessor semantics

Activation `676ad5e4...88d3` binds exact Publication, candidate/lineage/version,
all candidate/source/Publication evidence hashes, compatibility hash
`43c72090...bc9`, release evidence hash `5583dd29...5a`, activator, authority,
policy, capability, claim, event `237fd48c...c1a1`, Outbox
`68df6cc0...bec1`, Audit `b51984ce...2ee9`, and trace
`fea8eeb5...98ba`. Activation predecessor is explicitly `NULL`, meaning the
first Activation in this exact lineage. It is distinct from the rule
predecessor and any Publication predecessor notion.

The only event is `knowledge_layer_rule.activation_recorded` schema `v1`; it
means governance passed and makes no runtime, deployment, certification,
normative, learning or production claim. Success state is exactly CREATED,
APPLICATION_GOVERNED, PUBLISHED and ACTIVATED true; RUNTIME_ADOPTED and
RUNTIME_EFFECTIVE false.

## 14. Fresh authority and capability contracts

Every privileged boundary has a fixed actor/permission/policy/identity slot.
At execution, server resolution supplies only the declared fresh decision
fields and must retain decision ID/context version, actor, permission, global
scope, MFA, active access, evaluation/expiry, policy binding and decision hash.
Admission and immediate-precommit re-resolution are required. Client, stale,
expired, cached-only, revoked or mismatched authority denies.

Application, Publication, Activation, RuntimeAdoption, repair and capability
control are independent append-only streams. The first three must be enabled
twice; RuntimeAdoption is disabled and unused. Disablement never rewrites
history/runtime; re-enable is a new successor decision. No capability implies
another.

## 15. Idempotency, lock order and concurrency

Canonical Application/Publication/Activation materials bind exact artifact,
target/upstream evidence, all hashes, actors, fresh authority, policy,
capability, idempotency hash, trace, versions and deterministic graph IDs.
Same key/material replays or waits; changed material or reused artifact ID
conflicts; timeout cannot steal a claim.

Global lock order is claim/idempotency, stream/predecessor slot, upstream
artifact/evidence, candidate/target, authority, capability, then deterministic
event/Outbox/Audit streams. A holder may never seek an earlier lock.

The machine concurrency matrix covers identical, changed-material, competing
predecessor, stale predecessor, authority-revocation and capability-disable
races at all three boundaries. Exactly one winner/replay is possible; no root
or successor fork is permitted.

## 16. TOCTOU and atomic transactions

Immediately before commit, each boundary rechecks candidate identity and all
three hashes, exact Publication/validity/closure, source provenance,
predecessor and absence of competitor, authority/MFA/access/permission/scope,
SOD, policy/hash, capability leaf/state, idempotency material and zero
RuntimeAdoption. Drift raises inside the transaction.

Publication atomically retains claim, full curation audit, candidate published
projection, Publication, event, Outbox and governance Audit. Activation
atomically retains claim, Activation, event, Outbox and immutable Audit; it
reads/locks without mutating candidate/Publication and creates no
RuntimeAdoption. Missing transaction members are never COMMITTED.

## 17. Event, Outbox and immutable Audit contracts

Application, Publication and Activation events have distinct fixed v1 types,
bounded IDs/hashes/state/trace payloads, no secrets or licensed content, and
exact pending Outboxes. Each boundary has a separately typed immutable,
payload-hashed Audit. Activation Audit binds candidate, Publication,
Activation, predecessor, actor, authority, policy, capability, operation and
evidence hashes, trace and timestamp. Governance Audit and curation audit are
distinct and neither may be updated, deleted or substituted.

## 18. Rollback matrices

Application has 13 injection points, Publication 12 and Activation the required
12 from claim through precommit. Every injected failure gives zero deltas for
the boundary graph and preserves predecessor/protected state. Every Activation
failure additionally gives Activation/event/Outbox/Audit, RuntimeAdoption and
runtime-effect deltas zero. The exact points and postconditions are frozen in
the spec.

## 19. Ambiguous commit and repair restrictions

Outcomes are exactly COMMITTED (complete mutually matching graph),
NOT_COMMITTED (total durable absence), ABANDONED (claim plus separately
authorized append-only disposition and no committed graph), and INCONSISTENT
(partial/mismatched graph). Timeout is not abandonment. There is no blind
retry, status inference, evidence fabrication, automatic reconstruction or
automatic repair. Repair can inspect/classify/disable/request governance only;
it cannot publish, activate, adopt, mutate history or transfer claims.

## 20. Least privilege and SECURITY DEFINER design

Future activator is LOGIN, NOSUPERUSER, NOINHERIT, NOBYPASSRLS, non-owner, with
only EXECUTE on the exact Activation boundary. It has no DML, CREATE, role
escalation, Publication, RuntimeAdoption, Application, repair or capability
control. The exact-ID adapter owner is dedicated NOLOGIN, NOSUPERUSER,
NOINHERIT, NOBYPASSRLS, non-table-owner; uses `search_path=pg_catalog`, fully
qualified objects, no dynamic SQL/arbitrary selectors; PUBLIC EXECUTE is
revoked and only the exact executor is granted EXECUTE.

## 21. Exact-ID execution adapter decision

Frozen migration 0021 dynamically calls `uuidv7()` for Application outputs.
To satisfy preallocated identities without migration mutation, Phase 31.4 must
install an ephemeral exact-ID adapter whose complete restrictions are frozen
in the policy/spec. It reproduces migration 0021 validations, locks,
atomicity and evidence but accepts only this specification's IDs/material.
It is not migration 0024, cannot survive teardown, and cannot be generic.
Behavioral drift from migration 0021 is P1. This is the only new architectural
decision; therefore no successor ADR was needed beyond the new Product Policy.

## 22. Hostile matrix

The exact future denials cover PUBLIC; proposer/publisher/executor/curator/
adopter/worker/repair role misuse; spoofed actor/MFA/scope; stale/revoked
authority; wrong candidate/Publication/source/full/fingerprint/lifecycle/
evidence/policy/predecessor; disabled capability; hostile search path; direct
DML; latest/current/head/version/time selectors; and claim theft. Each denial
requires every protected delta zero.

## 23. Schema/FK snapshot design

Snapshot ID is `8b60018d-21b2-53a9-a428-6354672fa3a5`; migration-set hash is
`cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc`.
The snapshot covers 23 relevant tables, columns, nullability in the column
contracts, PK/UNIQUE/composite/CHECK constraints, FKs/self-FKs with RESTRICT,
append-only guards, root/lineage/predecessor rules, registry and closure
versions. Its canonicalization and live-catalog comparison are frozen.

## 24. Semantic dependency registry and dispositions

Registry `phase31.3-transitive-retention-registry/v1` contains 56 independently
machine-validated edges spanning source/provenance/support rows, rule lineage,
Proposal/Delta/Review/Decision/Authorization/Receipt, every privileged external
authority, curator evidence, both curation audits, policy, capability,
idempotency, candidate, compatibility/release, event, Outbox, immutable Audit,
manifests/dispositions and zero-downstream assertions.

Every successful-package local dependency has
`RETAIN_FULL_CANONICAL_MATERIAL`; external decisions alone use
`EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE`. Reference-only and
intentional non-rematerializability are not used for a successful package.
Unknown/missing/conflicting/multiple dispositions fail closure. Registry
evolution is additive/versioned and cannot reinterpret an export.

## 25. Publication and Activation closure

Publication's lower bound is fully enumerated in the closure specification and
includes the complete source/support/lineage/Application/curation/Publication
graph, authority, policy, capability, operation, compatibility, schema,
registry, manifest and disposition. Activation includes that entire closure
plus Activation claim/artifact/null predecessor/authority/policy/capability/
event/Outbox/Audit/SOD/compatibility/release/zero-runtime evidence. Schema and
registry discovery can only add mandatory members, never remove the lower
bound.

## 26. Closure algorithms and canonical retained material

Versioned deterministic contracts exist for compute, verify, export, live
re-read and export/live comparison. Every full member requires identity, type,
schema, required fields, canonicalization, bytes or lossless typed material,
material hash, provenance, retention time, cross-links and integrity proof.
Reports, code, UUIDs, tests, summaries and subsets do not substitute.

## 27. Manifests, dispositions and teardown gate

Separate Publication/Activation manifest IDs and separately hashed disposition
IDs are frozen. Required manifest fields include experiment/root/intended
operations, snapshot/registry/algorithm/verifier/canonicalization versions,
disposition counts, complete inventory, member hashes/cross-links, closure
digest/time, closure/match/reconstruction flags, RuntimeAdoption count,
runtime-effect flag and manifest hash.

Ordering is execute, compute, verify, export, independently re-read live,
compare, assert closure/match, pre-teardown disposition, authorize teardown,
teardown, offline verify. Teardown is blocked by default unless
`closure_complete=true`, `export_matches_live_graph=true`, and reconstruction
is unnecessary. Dual-control override can only mark permanently
non-rematerializable/operationally ineligible and never PASS.

## 28. Closure breach and offline verifier

Any unclassified or incomplete mandatory edge produces
`RETENTION_CLOSURE_BREACH`, promotion/continuation false, Activation input false
when Publication is affected, RuntimeAdoption input false, and no automatic
repair/reconstruction. Historical truth may remain only at its proved level.

Post-teardown verification uses no database reconstruction and must return:

```text
CREATED=true
APPLICATION_GOVERNED=true
PUBLISHED=true
ACTIVATED=true
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
retention_closure_complete=true
reconstruction_required=false
```

Missing canonical material, UUID-only mandatory FK, unresolved semantic edge,
hash/cross-link mismatch, missing closure metadata or reconstruction need fails
closed.

## 29. Zero RuntimeAdoption and runtime invariance

```text
RuntimeAdoption rows delta=0
RuntimeAdoption events delta=0
RuntimeAdoption Outbox delta=0
RuntimeAdoption Audit delta=0
adoption authority use=0
resolver invocation=0
runtime cutover=0
```

`agent_runtime.py`, `recommendation.py`, runtime configuration, AgentRun,
Recommendation, resolver and selectors remain unchanged and must have matching
before/after hashes. Activation alone remains runtime ineffective. Exact-ID
checks reject implicit latest/current/head/max/newest/timestamp selection.

## 30. Automatic-learning and normative invariance

The experiment cannot create/modify LearningSignal, proposals outside the
exact fixture, autonomous review/Decision/Application, confidence,
compensation, ModelPolicy, AgentDefinition or autonomy settings. It creates no
real Standard/Edition/Clause/Control/EvidenceCoverage or certification claim;
the minimum support graph is visibly synthetic/non-authoritative and contains
no licensed ISO material. Normative and automatic-learning effects remain zero.

## 31. Execution-ready completeness assessment

Phase 31.4 need not choose source, candidate, lineage, IDs, actors, SOD,
policies, capabilities, hashes/canonicalization, dependencies, dispositions,
events, audits, Outboxes, rollback/concurrency/hostile matrices, closure,
teardown or offline outcome. It may only obtain fresh state in the exact slots
and implement the already-decided exact-ID adapter. Architectural discretion
required in Phase 31.4 is false.

## 32. New approved artifact hashes

```text
44535b47bda30a4319903d8b9f10be04890b4d9085c8955d57916f3616d9588d  COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V1.md
e458cd0bb7eb11f96ce8723b0ab4dea97e4ca60b0e47a6f7e1fb1f38cef66d6b  PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_SOURCE_V1.txt
683f7c83ff3e3e16733d63288d317f8b3a14fe9e5bfaf2e86b0cf2e86b6ab6ca  PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_LIFECYCLE_SPEC_V1.json
d5e1960801772af74d491c9c6f69a877b79f1e26b937701cf1a239114b37bf1c  PHASE31_3_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V1.json
d3455bc64957ef1aab5f618e552d9276bd6fd60e0b1ce2e7a8068e5c14c8917a  PHASE31_3_EXPECTED_RETENTION_CLOSURE_V1.json
```

The report is the handoff record rather than a self-hashed input; its byte hash
is reported externally after final validation, avoiding impossible recursive
self-hashing.

## 33. Frozen hashes

Migrations are `23/23 MATCH`; migration-set hash is `cb324085...8fc`; 0024 is
absent. Ten authoritative sources are `10/10 MATCH`. Retained evidence byte
hashes remain `9272458c...7edd`, `b8a7c9d5...4536`, `fade372e...4b72`, and
`57633c70...ae9f`; embedded canonical hashes also match. ADR-0013--0016 remain
`8fa5852a...827`, `fa0e376e...952`, `57da49df...fea`, and `8a6ceb5d...745`.
Phase 31/31.1/31.2 remain `a2909cd4...daa`, `fc0a4820...282e`, and
`efe192d7...06f1`. Protected models/application/release/runtime hashes remain
`9dd94c94...c244`, `99d22898...648`, `a7b0477f...5b8`,
`6767e209...ec2d`, and `655fbdd1...648c`. Full inventories were compared, not
only these abbreviated report renderings.

## 34. Validation and counts

- Phase 29 post-teardown verifier: PASS; CREATED/Application/PUBLISHED true,
  Activation/RuntimeAdoption/runtime false, database reconstruction false.
- Phase 31 offline regressions plus retained publication/release tests:
  `35/35 PASS` through Django's initialized runner.
- An earlier plain-unittest aggregation ran 26 assertions but produced two
  setup errors solely because Django settings were not initialized; it is not
  acceptance evidence and was corrected by the passing command above.
- Django `4.2.22`; system check PASS with zero issues.
- `makemigrations foundation --check --dry-run`: PASS, no changes.
- Machine JSON parse: `3/3 PASS`; registry field completeness PASS.
- Semantic registry: `56/56` edges have all required contract fields.
- Source, candidate and delta hash recomputation: `3/3 MATCH`.
- Deterministic UUID uniqueness/collision: 83 spec UUIDs, zero historical
  collisions; UUIDv5 label contract checked.
- Schema/FK snapshot structure: 23 relevant tables; dual-source closure rule
  present; documentation/new-file whitespace checks PASS.
- PostgreSQL tests: `NOT EXECUTED`.

Offline design tests are not PostgreSQL acceptance evidence.

## 35. Git hygiene

Final status preserves every entry modification and known Sidebar whitespace.
This phase adds only this report, one policy, one exact source and three JSON
design artifacts. New files pass whitespace/diff checks. Nothing was staged,
stashed, reset, normalized, committed, deleted or deployed.

## 36. Zero effects

```text
database effects = 0
PostgreSQL effects = 0
historical Publication mutation effects = 0
historical reconstruction effects = 0
new candidate execution effects = 0
Publication execution effects = 0
Activation execution effects = 0
RuntimeAdoption effects = 0
runtime cutover effects = 0
production effects = 0
staging effects = 0
shared database effects = 0
normative effects = 0
automatic learning effects = 0
external business effects = 0
AdminApps operational effects = 0
MedSupplier effects = 0
```

## 37. Promotion criteria, P0/P1 and residual blockers

All required booleans are true: history unchanged; Phase 29 reuse false; 0024
absent; fixture exact/deterministic/independent; source/Application/Publication/
Activation/SOD/authority/capability/idempotency/concurrency/rollback/TOCTOU/
least-privilege/snapshot/registry/verifier contracts complete; Publication and
Activation closure complete by design; full curation-audit retention explicit;
teardown fail-closed; no architectural choice deferred; database/Activation/
RuntimeAdoption/external effects zero.

```text
P0=0
P1=0
residual blockers=0 within future isolated POC eligibility scope
```

Residual risk is implementation deviation: Phase 31.4 must prove the exact-ID
adapter is behaviorally equivalent to migration 0021 plus stronger retention
checks on real isolated PostgreSQL. Any mismatch, incomplete live closure,
unfresh authority or failed race/rollback/hostile test stops promotion and
blocks teardown. Production, RuntimeAdoption and runtime effectiveness remain
separately prohibited, not residual blockers to this design-only gate.

## 60. Final verdict

`PHASE 31.3 — PROMOTED — DETERMINISTIC EXECUTION-READY SYNTHETIC CREATION-THROUGH-ACTIVATION FIXTURE AUTHORIZED FOR FUTURE ISOLATED EPHEMERAL POC; NO RUNTIMEADOPTION`

This is eligibility only. No fixture, Publication, Activation, RuntimeAdoption
or runtime effect occurred.

## 61. Exactly one continuation prompt

```text
NEXT_CODEX_PROMPT

ISO SMART AI — PHASE 31.4 — NEW COMPLETE RETAINED SYNTHETIC LIFECYCLE — ISOLATED EPHEMERAL POSTGRESQL 18.6 CREATION-THROUGH-ACTIVATION POC

Work exclusively in /home/felipe/proyectos/isosmart. Read AGENTS.md and the complete frozen Phase 31.3 report, Product Policy, exact source fixture, lifecycle specification, semantic registry and expected retention-closure specification. Verify their exact SHA-256 values from Phase 31.3 before any database work. Preserve all unrelated work and every frozen migration 0001--0023, historical report/ADR/policy/evidence/source/runtime artifact; migration 0024 must remain absent. Keep Phase 29 Publication e97576de-d4ef-520d-8592-d376ed401221 permanently HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE with RETENTION_CLOSURE_BREACH; do not import, reconstruct, retry, reuse or treat it as operational input.

Execute exactly one isolated ephemeral PostgreSQL 18.6 POC from the frozen Phase 31.3 specification, without regenerating or choosing IDs, actors, source bytes, lineage, candidate, hashes, policies, capabilities, events, Outboxes, Audits, dependencies, dispositions, matrices, closure rules or lifecycle architecture. The maximum allowed path is exact synthetic source/support fixture -> exact root KnowledgeLayerRule -> exact governed Application creating candidate s1 -> exact native Publication -> exact first Activation with predecessor NULL -> compute/verify/export TRANSITIVE RETENTION CLOSURE / v1 -> independent live re-read and export/live comparison -> pre-teardown disposition -> authorized teardown -> offline verification. Install only in the isolated database the frozen exact-ID Application adapter required by Phase 31.3; prove behavioral equivalence to migration 0021 and the fixed least-privilege/SECURITY DEFINER contract. Do not create migration 0024.

Resolve every privileged authority freshly server-side at admission and immediately before commit using the exact actor, permission, global scope, MFA, active access, policy binding and evidence slot frozen in Phase 31.3. Obtain fresh append-only capability decisions under the frozen identity rules; Application, Publication and Activation must be enabled twice, while RuntimeAdoption remains disabled and unused. Exercise every frozen SOD, canonical idempotency, global lock-order, concurrency, TOCTOU, atomicity, rollback, ambiguous-commit, least-privilege/RLS/ACL and hostile denial case. Any drift or partial graph must roll back or classify INCONSISTENT; do not steal claims, retry blindly, infer status, fabricate evidence or repair automatically.

Before teardown derive closure independently from the live schema/FK snapshot and the frozen semantic registry. Retain full canonical material for every mandatory local dependency, including both exact eight-field normative.curation_audit rows, and frozen provenance for each external authority. UUID-only material does not count. Teardown is blocked unless closure_complete=true, export_matches_live_graph=true and reconstruction_required=false. If closure fails, preserve the live ephemeral database for inspection by default; any separately authorized dual-control teardown override permanently yields non-rematerializable, operationally ineligible evidence and never PASS. After authorized teardown, run the offline verifier without reconstruction and require exactly CREATED=true, APPLICATION_GOVERNED=true, PUBLISHED=true, ACTIVATED=true, RUNTIME_ADOPTED=false, RUNTIME_EFFECTIVE=false, database_reconstructed=false, retention_closure_complete=true and reconstruction_required=false.

Do not invoke or create RuntimeAdoption, call its resolver, change runtime configuration/selectors, deploy, access production/staging/shared databases, contact AdminApps/MedSupplier/providers/external APIs, create licensed or authoritative content, claim certification, authorize automatic learning, or create external business effects. Preserve zero RuntimeAdoption rows/events/Outboxes/Audits, zero adoption authority use, zero resolver invocation and zero runtime cutover. Run PostgreSQL acceptance and applicable offline/Foundation/Django/hash/git hygiene tests, report exact counts and hashes, and return NOT PROMOTED on any P0/P1, incomplete closure, failed export/live comparison, reconstruction need, nonzero prohibited effect or teardown performed without the frozen gate.
```
