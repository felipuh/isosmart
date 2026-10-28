# Phase 31.4.4B — strict physical-type correction V2.2 report

## 1. Verdict

`PHASE 31.4.4B — PROMOTED — ALL 34 V2.1 PHYSICAL-TYPE CONFLICTS CORRECTED; EXECUTION CONTRACT V2.2 STRICTLY TYPE-CONFORMANT AND AUTHORIZED FOR PRODUCER IMPLEMENTATION`

## 2. Entry 34 conflicts

Entry was Phase 31.4.5 Retry 2 NOT PROMOTED, P0=0/P1=2. The authoritative
Retry 2 blocker contains exactly 34 unique conflicts: eight UUID declarations
for physical text business identifiers and 26 descriptive strings assigned to
physical bigint fields (13 DomainEvent versions and 13 immutable-audit stream
sequences).

## 3. Git baseline

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

Initial `git diff --check` returned only the preserved unrelated warning:

```text
frontend/src/components/Layout/Sidebar.jsx:28: trailing whitespace.
+    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' }, 
```

No reset, stash, clean, stage, commit, normalization, or unrelated rewrite was
performed.

## 4. V2.1 integrity

V2.1 remained byte-identical at
`acd9e5551a04fc60356fedc2abdc4170932274913795fb6a5a4952ebf9477d85`.
Its frozen source inventory passed. Migrations 0001–0023 remain 23/23
unchanged at aggregate
`cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc`;
migration 0024 is absent.

## 5. Reading scope

The retained complete Phase31.4.4/4A semantic ledger was rechecked against the
Phase31.4.5 Retry2 report and blocker, V2.1 contract/generator/validator/tests,
V2.1 authorization/evidence, ADR-0018, Policy V2, Registry V2, Closure V2,
support producer contract, migrations defining the 34 columns, Django model
fields, event producers, immutable audit implementation, the append-audit SQL
function, and aggregate-version producer logic. No sibling repository or
external system was accessed.

## 6. Authoritative type precedence

Frozen migration SQL is authoritative for persisted physical type; Django
models confirm semantics; V2.1 generated metadata is subordinate. Approved
artifact schemas remain authoritative for non-database artifacts. No bigint
decision was made from a field name alone.

## 7. Exact conflict inventory

The machine-readable inventory is
`PHASE31_4_4B_STRICT_PHYSICAL_TYPE_CHANGESET_V1.json`. Its 34 records map
one-to-one, in blocker order, to the 34 Retry2 conflicts. No additional
physical-type defect or semantic/business-value defect was found.

## 8. Class A text/UUID analysis

The eight `operation_id`, `policy_id`, and `capability_id` occurrences are
frozen `varchar(160)`/`CharField` values and, where applicable, participate in
exact equality CHECK semantics. They are `BUSINESS IDENTIFIER TEXT`, not entity
UUIDs. UUID-looking text would still remain text under this physical schema.

## 9. Class A corrections

Each exact UTF-8 `typed_value` is byte-for-byte unchanged and has length at
most 160. Only `schema.type`, physical/database metadata,
`value_binding.database_type_or_schema_type`, and mechanically dependent
semantic metadata changed from UUID to text. UUID parsing is explicitly
prohibited for these fields.

## 10. Class B bigint/string analysis

All 26 V2.1 values were descriptive test strings, not executable persisted
business state. They were not coerced to numbers and were removed from
`typed_value`. The frozen schema requires PostgreSQL bigint and Django
`PositiveBigIntegerField`; the event CHECK is `>= 0` and audit sequence CHECK
is `> 0`.

## 11. DomainEvent aggregate-version semantics

Each event binds its exact aggregate type and aggregate ID. Existing event
producer logic computes `COALESCE(MAX(aggregate_version),0)+1` from persisted
history for that aggregate immediately before insert within the operation
transaction. The value is application/producer calculated, becomes available
only after persisted predecessor inspection, and is then reread. Existing SQL
controlled-execution paths also take an aggregate-key advisory transaction
lock; generic Python event helpers perform the same max-plus-one calculation
without inventing a static first-version invariant. Consequently no event is
falsely fixed to `1`.

## 12. Audit sequence semantics

`AuditWriterService` delegates sequence allocation to
`audit.append_immutable_audit`. The function takes a transaction-scoped
advisory lock keyed by tenant, stream type, and stream ID; reads the latest
sequence and entry hash; assigns predecessor sequence plus one or `1` only for
an actually empty stream; builds the hash chain; inserts atomically; and
returns the native audit ID. Concurrent appends to the same stream serialize
under that lock.

## 13. Class B binding decisions

All 26 fields are `EXECUTION_DERIVED_PERSISTED`. Every binding records `kind`
and `binding_kind`, unchanged producer/version, exact source state, structured
preimage, earliest availability, existing transaction boundary, freeze,
verification rule, bigint representation, and
`expected_literal_if_static=null`. There is no fake integer or fifth binding
option.

## 14. Freeze compatibility

All corrected live values become available inside their already declared
member transaction and are retained at the member's existing freeze. There are
zero freeze changes and the 15-point Freeze0→Freeze9 order is byte-identical.

## 15. Producer compatibility

Every one of the 26 rows keeps its V2.1 producer and version. Event version
allocation and audit sequence allocation were already authorized live
producer-derived behavior under ADR-0018. No producer, capability, parameter,
or transaction architecture was added.

## 16. 118-member preservation

The complete V2.2 material remains 118 members: 110 database rows and eight
artifacts, with 1,664 fields. No row, table, primary key, identity mode,
producer, security scope, or closure disposition changed.

## 17. Full strict type scan

The permanent validator checked all 1,664 field bindings and all 753 V2.2
`EXACT_LITERAL` bindings. Results: physical/schema/type mismatches=0,
nullability mismatches=0, enum/CHECK mismatches=0, unresolved references=0,
cycles=0, deterministic-preimage errors=0, and execution-derived
producer/freeze errors=0.

## 18. Exact-literal before/after counts

```text
v2_1_exact_literal_count=779
v2_2_exact_literal_count=753
reclassified_exact_literal_count=26
779 - 753 = 26
```

Only the 26 bigint conflicts left `EXACT_LITERAL`; the eight Class A values
remain exact literals.

## 19. Binding-kind before/after counts

| Binding kind | V2.1 | V2.2 | Delta |
|---|---:|---:|---:|
| EXACT_LITERAL | 779 | 753 | -26 |
| DETERMINISTIC_DERIVATION | 210 | 210 | 0 |
| REFERENCE_TO_BOUND_FIELD | 195 | 195 | 0 |
| ADOPTED_STATIC_SCHEMA_DEFAULT | 0 | 0 | 0 |
| EXECUTION_DERIVED_PERSISTED | 400 | 426 | +26 |
| EXECUTION_DERIVED_EXTERNAL_AUTHORITY | 46 | 46 | 0 |
| NATIVE_OUTPUT | 27 | 27 | 0 |
| ADR0017_MAPPED_OUTPUT | 7 | 7 | 0 |

The sole delta is the exact 26-record Class B reclassification.

## 20. Nullability

All exact literals and all 34 corrected fields were checked. No null was used
to evade a mismatch; `nullability_mismatches=0`.

## 21. Enum/CHECK

The complete known enum/CHECK matrix passes. Bigint positivity and PostgreSQL
range behavior are enforced by the validator and negative tests.
`enum_check_mismatches=0`.

## 22. Type consistency

Normalized frozen physical type, V2.2 `schema.type`, and binding-declared type
agree for every applicable field. Exact literals enforce JSON representation:
UUID string, UTF-8 text, non-boolean integer, native boolean, and structured
JSON. No descriptive bigint string remains.

## 23. V2.2 contract

The full materialized successor is
`PHASE31_4_4B_ROW_LEVEL_EXECUTION_CONTRACT_V2_2.json`, version 2.2, predecessor
2.1/hash `acd9e555…7d85`, and scope
`STRICT_PHYSICAL_TYPE_CORRECTION_FOR_34_BINDINGS`. Architecture, row universe,
security, freeze model, Registry, and Closure flags are all false for change.

## 24. 34-item changeset

The append-only changeset records member, field, old/new schema type, old/new
binding kind, old typed value, new literal or derivation, physical type, source
evidence, and business/architecture impact for exactly 34 items. Class A
business semantics are unchanged. Class B records that prior text was
non-executable diagnostic material.

## 25. Registry invariance

Registry V2 is byte-identical at
`58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb`.
No semantic edge changed.

## 26. Closure invariance

Closure V2 is byte-identical at
`80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425`.
No member or disposition changed.

## 27. Security/RLS invariance

The complete security/RLS matrix equals V2.1 byte-for-byte inside V2.2. No
role, privilege, policy, table owner, tenant scope, or external-authority rule
changed.

## 28. ADR decision

ADR-0018 is preserved byte-identically at
`f9f6272c72e433241f66e44884b53dc804a667b32950c8ab098df6473ecf6089`.
The corrections use its existing rule for uniquely produced live persisted
values. `architecture_changed=false`; `ADR0019_required=false`.

## 29. Correction authorization

The narrow append-only authorization preserves V2.1 as history, makes V2.2
the future operational contract, preserves B1–B4/Registry/Closure/ADR-0018,
leaves producer implementation pending, and prohibits RuntimeAdoption.

## 30. Fixed-hash audit

Every fixed 64-hex digest is inventoried as `STATIC_PREIMAGE_INCLUDED`,
`SOURCE_BYTES_HASH`, `CANONICAL_POLICY_HASH`, or
`HISTORICAL_REFERENCE_ONLY`. No live numeric value is represented as a future
digest. `fixed_hash_without_preimage=0`.

## 31. Validator upgrade

The V2.2 validator permanently checks binding presence/uniqueness, row and
field universes, references/cycles, physical/schema/binding type consistency,
literal representation, nullability, enum/CHECK values, deterministic
preimages, execution-derived producer/freeze/source/verification completeness,
the exact 34-item correction, fixed hashes, migrations, detached inputs,
Registry, Closure, security, and RuntimeAdoption prohibition.

## 32. Positive tests

The V2.2 validator passed. Seventeen focused V2.2 tests passed, including the
complete 34-record inventory and count reconciliation. The combined V2,
V2.1, and V2.2 suite ran 91 tests with zero failures/errors. The V2.1 validator
also passed independently.

## 33. Negative tests

Tests reject descriptive aggregate/audit strings, negative sequence, bool as
integer, out-of-range bigint, unrelated aggregate event, unrelated audit
stream, missing producer, missing verification rule, arbitrary text in UUID,
text forced to UUID, string boolean, serialized JSON string, NULL on NOT NULL,
and invalid enum/CHECK material.

## 34. Django/offline validation

All checks used `backend/.venv`; Django is 4.2.22. JSON parsing, deterministic
regeneration, in-memory compilation of 364 Python files, Django system check,
and `makemigrations --check --dry-run` passed (`No changes detected`). No
`.venv312`, database, network, container, lifecycle service, or resolver was
used.

## 35. Migration/source/protected hashes

Migrations 0001–0023 and the inherited authoritative source inventory pass;
migration-set hash is `cb324085…28fc`, migration 0024 is absent, V2.1 is
`acd9e555…7d85`, Policy V2 is `bf92aa4a…cad2`, producer contract is
`9ca5530b…795e`, and protected runtime changes=0.

## 36. New artifact hashes

```text
contract V2.2 a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d
changeset 3d91f1b1f9305c2a7f26381e12ce6f27e7b13a327371042447460c52554fa1ad
generator 35cf5f8d679c8beae05154f11cd61d38accf938d3a173fd16741110137ba57df
validator 29f005a121640f74a161a88161af9480792a9db84abf6d95073fa094e3659daf
tests 4f76af7f5ae4f3662b4c350bbadcc41d8a922de017ec97251ed1f7e8927786f2
correction authorization 0113c21e8207462099a1dcf1f3806400e4bc43806b7e880f85820024f92e29d3
validation evidence 6569a3c1fa28938d0f041995d697d9157bc5a93531b0cbf1b4a495698e2d86f2
```

An exact report byte hash cannot be embedded in the bytes it hashes without a
self-referential fixed-point problem; its detached exact SHA-256 is published
in the completion handoff, matching the established Phase31.4.4A practice.

## 37. Git hygiene

Only append-only Phase31.4.4B contract, changeset, generator, validator, tests,
authorization, evidence, and report files were added. V2.1 and all unrelated
work remain untouched. Final `git diff --check` retains only the pre-existing
Sidebar line 28 warning.

## 38. Zero effects

All PostgreSQL operational criteria remain explicitly unexecuted:

```text
PostgreSQL startup=NOT EXECUTED
DB creation=NOT EXECUTED
role creation=NOT EXECUTED
migration application=NOT EXECUTED
producer implementation=NOT EXECUTED
producer installation=NOT EXECUTED
producer execution=NOT EXECUTED
Application parity=NOT EXECUTED
Application=NOT EXECUTED
Publication=NOT EXECUTED
B2=NOT EXECUTED
B3=NOT EXECUTED
closure=NOT EXECUTED
Activation=NOT EXECUTED
RuntimeAdoption=NOT EXECUTED
```

```text
database effects=0
PostgreSQL effects=0
container effects=0
role effects=0
migration execution effects=0
producer implementation effects=0
producer installation effects=0
support fixture effects=0
Opportunity effects=0
Effectiveness effects=0
LearningSignal effects=0
Proposal effects=0
Application effects=0
Publication effects=0
Activation effects=0
RuntimeAdoption effects=0
resolver invocation=0
runtime cutover effects=0
production effects=0
staging effects=0
shared DB effects=0
real AdminApps effects=0
MedSupplier effects=0
external API effects=0
normative effects=0
automatic learning effects=0
external business effects=0
Phase29 reconstruction effects=0
```

## 39. Blocker accounting

`P1-V2_1-STRICT-PHYSICAL-TYPE-CONFLICTS=CLOSED`.

The original Clean Retry blockers remain open exactly as expected:

```text
P1-CR2-SUPPORT-PRODUCER-ABSENT=OPEN_IMPLEMENTATION_ONLY
P1-CR2-INPUT-HASH-INVENTORY=OPEN_PENDING_IMPLEMENTATION_MEMBERS
```

## 40. P0/P1

For this V2.2 correction gate, `P0=0` and `P1=0`. This does not close or hide
the two pending implementation blockers above.

## 41. Residual risks

The parameterless support producer, SQL/security/RLS installer, Clean Retry
harness, authoritative operational manifest, and PostgreSQL proof do not yet
exist. Event-version concurrency must follow each existing producer's exact
transaction/locking semantics during implementation; this offline contract
does not claim a live concurrency result.

## 42. Final verdict

`PHASE 31.4.4B — PROMOTED — ALL 34 V2.1 PHYSICAL-TYPE CONFLICTS CORRECTED; EXECUTION CONTRACT V2.2 STRICTLY TYPE-CONFORMANT AND AUTHORIZED FOR PRODUCER IMPLEMENTATION`

## 43. NEXT_CODEX_PROMPT

```text
PHASE 31.4.5 — RETRY 3 — V2.2 SUPPORT PRODUCER + INSTALLER + CLEAN RETRY HARNESS + AUTHORITATIVE OPERATIONAL MANIFEST CLOSURE GATE

Work exclusively in /home/felipe/proyectos/isosmart. Begin before repository discovery with git status --short and git diff --check; record exact output, preserve all unrelated work including frontend/src/components/Layout/Sidebar.jsx:28, and do not reset, stash, clean, stage, commit, normalize, inspect sibling repositories, or contact external systems.

Entry is PHASE 31.4.4B PROMOTED. Consume the full append-only docs/governance/fixtures/PHASE31_4_4B_ROW_LEVEL_EXECUTION_CONTRACT_V2_2.json directly and require its detached SHA-256 a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d. Verify the V2.2 changeset, generator, permanent strict validator, tests, authorization, validation evidence, V2.1 predecessor, ADR-0018, Policy V2, Registry V2, Closure V2, producer contract, migrations 0001–0023, and every protected/authoritative source hash before implementation. Require migration 0024 absent.

Run the permanent V2.2 strict physical-type gate before implementation. Require 118 members, 110 database rows, eight artifacts, 1,664 fields, 753 exact literals, zero physical-type/nullability/enum-CHECK mismatches, zero unbound/ambiguous/conflicting/cyclic bindings, exactly eight preserved BUSINESS IDENTIFIER TEXT literals, exactly 26 EXECUTION_DERIVED_PERSISTED bigint corrections, no descriptive bigint strings, and complete producer/freeze/verification metadata. Fail closed on any drift; do not coerce strings or invent values.

Implement the exact parameterless support producer identified by phase31.4.4-exact-support-producer/v1, its SQL installer, scoped owner/executor roles and exact tenant RLS policies, and the Clean Retry harness. Consume all V2.2 bindings directly: render EXACT_LITERAL with strict physical types; verify deterministic preimages; resolve references only after their required source freeze; obtain persisted/native values only through their named producer and transaction; derive DomainEvent.aggregate_version from the exact persisted aggregate history under the existing producer semantics; obtain ImmutableAuditLog.sequence_number only through audit.append_immutable_audit and reread it; obtain fresh external authority only through the exact fail-closed envelope with immediate precommit revalidation. Do not accept arbitrary table, model, UUID, operation, actor, JSON, target, field, or business-value parameters. Do not change producers, freezes, event/audit sequencing, business semantics, Registry, Closure, security architecture, ADR-0018, or RuntimeAdoption.

Implement structural and offline tests using backend/.venv with Django 4.2.22. Cover exact 118-member/1,664-field consumption, parameterlessness, strict type rendering, complete references/preimages, transaction ownership, role attributes, qualified SQL/search path, RLS USING/WITH CHECK, no PUBLIC execute, no dynamic/generic DML, event and audit allocation semantics, rollback/failure preservation, phase-machine guards, Publication-before-Activation, Phase29 exclusion, and RuntimeAdoption/resolver prohibition. Freeze exact implementation, installer, harness, validator, and test hashes in a complete non-self-referential authoritative operational manifest and publish the manifest SHA-256 externally.

This Retry 3 phase is implementation and offline validation only. Do not start PostgreSQL or containers, create a database or roles, execute migrations, install or execute the producer, run lifecycle services, mutate Opportunity, create EffectivenessCheck or LearningSignal, execute Proposal/Application/Publication/Activation, invoke RuntimeAdoption or its resolver, contact AdminApps/MedSupplier/network/external APIs, deploy, create migration 0024, or advance Phase 32. Report all such operational criteria NOT EXECUTED and all effects zero.

Close P1-CR2-SUPPORT-PRODUCER-ABSENT and P1-CR2-INPUT-HASH-INVENTORY only if every required implementation member exists, all offline gates pass, the authoritative operational manifest is complete and externally anchored, migrations/protected inputs remain unchanged, and P0=0/P1=0. Only after that promotion may a separate Clean Retry 3 phase execute PostgreSQL. Otherwise emit PHASE 31.4.5 — RETRY 3 — NOT PROMOTED with exact blockers and no unsafe workaround.
```
