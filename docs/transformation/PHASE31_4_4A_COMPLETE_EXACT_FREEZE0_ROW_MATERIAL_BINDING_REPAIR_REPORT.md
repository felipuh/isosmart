# Phase 31.4.4A — complete exact Freeze-0 row-material binding repair

## 1. Verdict

`PHASE 31.4.4A — PROMOTED — COMPLETE FREEZE-0 FIELD BINDINGS CLOSED FOR ALL V2 MEMBERS; EXECUTION CONTRACT V2.1 AUTHORIZED FOR SUPPORT-PRODUCER IMPLEMENTATION`

## 2. Entry Phase31.4.5 blocker

Entry was `PHASE 31.4.5 — NOT PROMOTED`, P0=0/P1=2. The dispositive row was
`qms.tenant_projection::daa6bb22-660c-56f5-aadf-c63f06b01731`; six required
business fields lacked exact values.

## 3. Initial Git state

Before repository discovery, `git status --short` returned exactly:

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

`git diff --check` returned exactly the preserved warning:

```text
frontend/src/components/Layout/Sidebar.jsx:28: trailing whitespace.
+    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' }, 
```

No reset, stash, clean, stage, commit, or unrelated normalization occurred.

## 4. Frozen baseline

Migrations 0001–0023, ADR-0013–0018, Policy V2, Execution Contract V2,
Registry V2, Closure V2, producer V1, historical reports/evidence and protected
runtime/domain code remain unchanged. Migration 0024 is absent.

## 5. Reading scope

The frozen 86-file semantic-reading ledger remains complete. This correction
rechecked the Phase31.4.5 report/blocker, Phase31.4.4 report/evidence, ADR-0018,
Policy V2, V2 contract/registry/closure, producer contract, RLS design, schema
census, migrations 0001–0023, applicable models, generator and tests.

## 6. Row universe integrity

118/118 qualified identities remain in original order: 110 database rows and
8 retained artifacts across the same 53 qualified tables/indexes. No member,
table, primary key, producer, identity mode, freeze, or security scope changed.

## 7. Field-universe derivation

Model-backed columns come from the frozen migration-derived schema census.
Raw Application/release tables are extracted from frozen `CREATE TABLE`
definitions and merged with later `ALTER TABLE` fields. Artifact fields come
from typed schemas plus the three closure schemas. Total: 1,664 fields.

## 8. Value-binding taxonomy

V2's execution-ready taxonomy is preserved. Each field has exactly one
orthogonal binding from the eight allowed kinds. PREBOUND_STATIC is limited to
literal, deterministic derivation, bound-field reference, or explicitly
adopted static default.

## 9. TenantProjection complete repair

All 15 persisted columns are bound. The external synthetic UUID is
`baff5462-1031-52a3-bae4-9a00a1f9bb9c`, UUIDv5 namespace
`05611a8a-f662-5b7f-ad24-c4df48d573ec`, exact UTF-8 label
`phase31.4.4a/external-control-plane/tenant/v1`. Source version is `1`; display
is `TEST ONLY — ISO SMART AI PHASE 31.4.4A SYNTHETIC TENANT`; statuses are
`pending`/`pending`/`in_sync`. Nullable error/event/suspension/deletion fields
are explicit; native timestamps are execution-derived. No real AdminApps
tenant is claimed.

## 10. Remaining member audit

Every member records required, bound, unbound, ambiguous and conflicting
counts. Every member has unbound=0, ambiguous=0 and conflicting=0.

## 11. Nullable-field treatment

Nullable static branches are explicit `EXACT_LITERAL=null`; fields that are
legitimate persisted operation outputs retain exact execution-derived rules.
Absence is never implicit.

## 12. Conditional-field treatment

Root/predecessor, human-review, successful controlled defer, evidence,
Application, Publication and Activation branches are resolved. Future success
facts are represented by exact producer/evaluation rules, not guessed values.

## 13. Defaults treatment

No schema default is adopted as PREBOUND_STATIC. Dynamic time/UUID/session
defaults are execution-derived or native. Adopted-static-default count is 0.

## 14. Enum/check validation

Tenant, catalog, rule, recommendation, action, approval, authorization,
execution, receipt, learning, outbox and release literals were checked against
frozen model choices and migration checks. Invalid enum/check count is 0.

## 15. JSON bindings

Static JSON/JSONB bindings carry exact objects or arrays with concrete types;
review-domain and review-ID fields are arrays, while payload/findings/guardrail
material is object-shaped. Live canonical payloads remain derived.

## 16. Tenant material

Tenant material is visibly synthetic, caller-independent, RLS-compatible and
does not call or impersonate the control plane.

## 17. Organization material

Organization and process fields bind to the single synthetic tenant and exact
qualified support rows; no caller-selected organization exists.

## 18. User/actor material

The local synthetic UserProjection has exact nonfresh values. Fresh authority
fields use the complete external-authority descriptor; no person, secret, MFA
credential or real AdminApps ID is invented.

## 19. Agent catalog material

Standard/Edition/Clause/RequirementControl/KnowledgeLayer/Rule, ModelPolicy,
AgentDefinition and curation rows have exact non-time values. Published
synthetic catalog states and `non_certifiable_guidance` are validated.

## 20. AgentRun material

Definition/policy/capability/autonomy-zero/model provenance, input and trace
bindings are exact. Provider/tool calls remain zero.

## 21. Recommendation provenance

AgentRunInput, Recommendation, RecommendationBasis and link fields resolve to
bound qualified members; derivation/hash fields name exact producers and
freeze points.

## 22. Opportunity material

Revision 1 is exactly `under_evaluation`; revision 2 is exactly `deferred` and
binds the controlled action and predecessor path. All content is test-only.

## 23. Action execution material

Plan, dry run, human Approval, authorization, controlled execution and receipt
separate static action intent, fresh authority, native time and persisted
hash/output derivation. No rationale/impact/reversibility slot is missing.

## 24. Evidence

Evidence is non-official, synthetic and unlicensed; complete static metadata is
bound and canonical content/hash production is exact and retained.

## 25. Effectiveness

The first human-review revision binds its complete lineage. Outcome is produced
from the exact future evidence evaluation rule rather than predeclared as an
unverified fact.

## 26. LearningSignal

All persisted fields and the separate synthetic/nonautomatic/nonnormative
semantic envelope are bound. No automatic learning occurs.

## 27. Proposal/Review/Decision

Rationale, effect, risks, domains, correction operation/schema, findings,
review set, decision rule and policy are exact. Target/hash equality remains a
named persisted derivation where it depends on future rereads.

## 28. Root support

Model B remains unchanged. Root target time/full-row hash is not predicted;
dual persisted reread and exact canonicalization remain authoritative.

## 29. B2/B3

Static schema/policy/assertion fields are exact. Live observations and digests
remain execution-derived, and neither B2 nor B3 is self-referential.

## 30. Governed admissions

Root, Publication and Activation actor slots, operation, permission, scope,
policy, capability, schema and canonicalization are exact. Fresh authority is
evaluated and revalidated at the operation boundary.

## 31. Field-source graph

The machine graph contains 1,664 field nodes and 195 bound-field references.
All references terminate; reference-cycle count is 0.

## 32. Completeness counts

```text
member_count=118
db_row_count=110
artifact_count=8
field_count_total=1664
prebound_static_count=1184
execution_derived_persisted_count=400
execution_derived_external_authority_count=46
native_output_count=27
adr0017_mapped_output_count=7
exact_literal_count=779
deterministic_derivation_count=210
reference_binding_count=195
adopted_static_default_count=0
unbound_required_field_count=0
ambiguous_binding_count=0
conflicting_binding_count=0
reference_cycle_count=0
```

Binding-kind counts sum to 1,664; taxonomy counts are orthogonal.

## 33. V2.1 successor

The full materialized successor is
`PHASE31_4_4A_ROW_LEVEL_EXECUTION_CONTRACT_V2_1.json`, version 2.1, scope
`FREEZE0_EXACT_FIELD_BINDING_REPAIR`, architecture unchanged, universe
unchanged. A future producer consumes it directly.

## 34. V2→V2.1 differences

V2.1 adds complete physical/artifact field schemas, one binding per field,
field graph/counts, the exact TenantProjection boundary, source-integrity
inventory and promotion predicates. It does not change operational topology.

## 35. Registry impact

Registry V2 is unchanged; the binding repair adds no semantic edge.

## 36. Closure impact

Closure V2 is unchanged; membership and retention disposition are unchanged.

## 37. Security/RLS impact

The 53-entry security/RLS matrix is byte-equivalent inside V2.1. No privilege,
policy or tenant-context change is required.

## 38. ADR decision

`new_architectural_decision=false`; `ADR0019_required=false`; ADR-0018 remains
the governing architecture.

## 39. Policy/change-control authorization

The append-only correction authorization supersedes V2 only for future field
bindings, preserves Phase31.4.4 historically, excludes Phase29 and prohibits
RuntimeAdoption. The original producer file remains unchanged.

## 40. Fixed-hash audit

Fixed digests are governed by the four allowed classifications. Future digests
use descriptors. `fixed_hash_without_preimage=0`.

## 41. Positive tests

The new validator passed; 22 focused tests passed; combined V2/V2.1 tests ran
74 with zero failures/errors; the guarded Phase31.4.4 regression ran 155 with
zero failures/errors. 118/118 members and 1,664/1,664 fields are represented.

## 42. Negative tests

Tests reject each original tenant omission, any missing/duplicate binding,
invalid enum, ambiguous nullable, dynamic static default, incomplete preimage,
unresolved/cyclic reference, placeholder/caller input, real AdminApps,
RuntimeAdoption and row/table/key/producer/security/freeze drift. Migration and
authoritative-source hashes fail closed.

## 43. Migration/source/protected hashes

Migration set 0001–0023 is
`cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc`
(23/23 individually frozen). V2 is
`962ec0b393b49c3c0a2894e32bb9a3246cbf7793cfd600391248634bee56f70b`;
Registry V2 `58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb`;
Closure V2 `80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425`;
ADR-0018 `f9f6272c72e433241f66e44884b53dc804a667b32950c8ab098df6473ecf6089`;
Policy V2 `bf92aa4aafdaa99e27f90fc3c2766cd3a8fa85214f26a4fe7ffbbd1a7397cad2`.
Protected runtime changes=0; migration 0024 absent.

## 44. New artifact hashes

```text
contract V2.1 acd9e5551a04fc60356fedc2abdc4170932274913795fb6a5a4952ebf9477d85
generator 5f2855ec25982681cc204cfe3da73c1b88c5b047419cb09276696a52d9896990
validator 8a1b70854128809623ec196179f5c7ceba1c78c3687e2c8eed8fb73462e78ad0
tests 3a49fe33dc4f906846083b477a19fe677c93d63155cae0df25f7a2d5f906d6bb
authorization 72b11531ebcd8ef2e152ceed4c7fb15ca1ff4f9a5edad482602c28d4c7abc13b
validation evidence 051a05671f3b7df74ddbe73da5d853c9a1cc3e2ef0708d43e0de833f3bee42ad
```

This report cannot contain its own file-byte digest without recursion; its
detached final digest is published by the completion handoff.

## 45. Git hygiene

Only append-only Phase31.4.4A artifacts were added. Historical artifacts and
unrelated local work were not edited. Final whitespace validation preserves
only the known Sidebar warning.

## 46. Zero effects

Database, PostgreSQL, container, role, migration execution, producer
implementation, fixture execution, Opportunity, Effectiveness, LearningSignal,
Proposal, Application, Publication, Activation, RuntimeAdoption, resolver,
cutover, production, staging, shared DB, real AdminApps, MedSupplier, external
API, normative, automatic learning, external business and Phase29
reconstruction effects are all 0.

## 47. P0/P1

For this correction gate P0=0/P1=0 and
`P1-FREEZE0-ROW-MATERIAL-BINDINGS=CLOSED`.
`P1-CR2-SUPPORT-PRODUCER-ABSENT=STILL_OPEN_IMPLEMENTATION_ONLY` and
`P1-CR2-INPUT-HASH-INVENTORY=STILL_OPEN_PENDING_IMPLEMENTATION_MEMBERS` remain
expected Phase31.4.5 implementation blockers, not defects in V2.1.

## 48. Residual risks

The producer, installer, RLS materialization, Clean Retry harness and complete
operational manifest do not yet exist. PostgreSQL behavior is deliberately not
claimed by this offline gate.

## 49. Final verdict

`PHASE 31.4.4A — PROMOTED — COMPLETE FREEZE-0 FIELD BINDINGS CLOSED FOR ALL V2 MEMBERS; EXECUTION CONTRACT V2.1 AUTHORIZED FOR SUPPORT-PRODUCER IMPLEMENTATION`

## 50. NEXT_CODEX_PROMPT

```text
PHASE 31.4.5 — RETRY 2 — COMPLETE V2.1 OPERATIONAL INPUT MANIFEST + EXACT SUPPORT PRODUCER/HARNESS IMPLEMENTATION CLOSURE GATE

Work exclusively in /home/felipe/proyectos/isosmart. Begin with git status --short and git diff --check; preserve unrelated work and the known Sidebar.jsx:28 warning. Consume PHASE31_4_4A_ROW_LEVEL_EXECUTION_CONTRACT_V2_1.json directly and verify its detached SHA-256 plus every frozen source hash before implementation. Preserve migrations 0001–0023, migration 0024 absence, ADR-0013–0018, Registry V2, Closure V2, security/RLS architecture, freeze order, Phase29 exclusion and RuntimeAdoption=false.

Implement the exact parameterless support producer, SQL installer, scoped role/RLS material and Clean Retry harness for all V2.1 bindings. Do not choose or accept any business value: render EXACT_LITERAL, verify complete deterministic preimages, resolve bound-field references after their required freeze, derive persisted/native values only at their named transaction/freeze, and obtain fresh external authority only through the exact fail-closed envelope with immediate precommit revalidation. Implement no generic table/model/UUID/JSON/field interface and no real AdminApps, MedSupplier or external dependency.

Test producer/installer/harness offline under backend/.venv and Django 4.2.22, including structural SQL, parameterlessness, exact 118-member coverage, schema/enum/JSON conformance, reference ordering, RLS/role/search-path safety, rollback/failure preservation, phase-machine guards, Publication-before-Activation, zero RuntimeAdoption and no database/network/container/lifecycle attempts. Freeze every implementation/test/harness/installer dependency hash in a complete non-self-referential authoritative operational manifest; publish the manifest SHA-256 externally. Close P1-CR2-SUPPORT-PRODUCER-ABSENT and P1-CR2-INPUT-HASH-INVENTORY only if all implementation members exist and all offline checks pass. Do not create PostgreSQL, execute migrations or lifecycle operations, contact external systems, deploy, create migration 0024, run Clean Retry 3, or begin Phase 32.
```
