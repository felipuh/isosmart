# Phase 31.4.5A Retry 1 — AgentRun DomainEvent source-identity correction V2.3

## 1. Verdict

`PHASE 31.4.5A — RETRY 1 — PROMOTED — AGENTRUN DOMAIN EVENT SOURCE IDENTITY CORRECTED IN V2.3; NATIVE STREAM SOURCE-REACHABLE AND EXISTING SERIALIZATION INVARIANTS PROVEN; NO NEW LOCK REQUIRED`

This is an offline contract promotion only. It creates no producer, database,
PostgreSQL process, container, role, migration, event, or lifecycle state.

## 2. Entry hygiene

The first repository commands were `git status --short` and
`git diff --check`. Exact output:

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
frontend/src/components/Layout/Sidebar.jsx:28: trailing whitespace.
+    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' }, 
```

All pre-existing work and the Sidebar whitespace were preserved. No reset,
stash, clean, stage, commit, normalization, or sibling-repository access
occurred.

## 3. Mandatory reading and predecessor integrity

`mandatory_source_identity_reading_complete=true`.

Reading covered the complete Phase31.4.5A report and decision evidence/tests;
Retry3 report; V2.2 and its changeset; ADR-0018; Product Policy V2; Registry V2;
Closure V2; support producer contract; AgentRun models and migrations;
DomainEvent, Outbox, and immutable Audit models/migrations; complete start,
completion, failure, `_event_outbox_audit`, `_state`, and payload paths; tenant
transaction ownership; same-stream writers; and all V2.2 references to the
affected members.

```text
V2.2        a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d
Registry V2 58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb
Closure V2  80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425
migrations  cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc
```

V2.2 remains byte-for-byte unchanged. All 23 migrations 0001–0023 retain the
frozen aggregate hash and migration 0024 is absent.

## 4. Declared AgentRun event inventory

`contract_agentrun_event_member_count=2`.

| row_id | purpose | native event | aggregate key | selected source |
|---|---|---|---|---|
| `90e2d38f-9600-5701-a34c-c9827eafc88c` | AgentRun start | `agent_run.started` | `agent_run` / reference to `AgentRun.id` | `_event_outbox_audit` under `start_agent_run` |
| `47be0b7e-10d0-5e96-94fd-fcaa8ad14cfd` | AgentRun completion | `agent_run.completed` | `agent_run` / reference to `AgentRun.id` | `_event_outbox_audit` under `complete_agent_run_with_recommendation` |

The native `agent_run.failed` writer is present and was included in the
same-stream writer proof. No failure member exists in the 118-member contract,
so none was added.

## 5. Source-reachability correction

V2.3 is a full append-only successor with:

```text
contract_version=2.3
predecessor_version=2.2
predecessor_sha256=a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d
change_scope=AGENTRUN_DOMAIN_EVENT_SOURCE_IDENTITY_CORRECTION
architecture_changed=false
row_universe_changed=false
producer_architecture_changed=false
security_changed=false
freeze_model_changed=false
```

Both events now use the native event type, `aggregate_type=agent_run`, an exact
reference to `qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8.id`, source
`iso-smart-agent-runtime`, a reference to `AgentRun.trace_id`, and the exact
execution-derived `_state(...)` payload construction. Correlation and causation
remain explicit NULL. Aggregate version remains execution-derived by
`COALESCE(MAX(aggregate_version),0)+1` over the corrected coherent key.

The linked Outbox references the event, begins `pending` with
`publish_attempts=0`, and preserves native timestamp/status allocation. Its
fixed ID remains an enumerated ADR-0018 identity-only substitution.

The linked Audit now uses stream/entity type `agent_run`, stream/entity ID
references to `AgentRun.id`, the native event action, actor type `worker`, the
exact synthetic caller actor input, `AgentRun.trace_id`, and execution-derived
canonical metadata. Audit identity remains native UUIDv7; sequence and
predecessor hash remain allocated by `audit.append_immutable_audit`.

The old aggregate IDs `51c9bad4-88fb-5608-b3c9-edd578efeeb9` and
`91792d67-eb35-5e1d-9c62-c285f7b97057` are present only in historical
classification as `SUPERSEDED_SOURCE_UNREACHABLE_FIXTURE_BINDING`. Synthetic
test-only classification remains in governance metadata, not protocol fields.

## 6. Identity exceptions

Native Event IDs are caller-supplied UUID4 values; native Outbox IDs are ORM
UUID4 defaults. ADR-0018 already authorizes the enumerated deterministic
fixture identities in the V2 contract, and the corresponding row identities
are unchanged in V2.3. No exception was created or expanded.

```text
native_event_id_matches_contract=false
ADR0018_explicit_identity_exception_covers_event_id=true
ADR0018_explicit_identity_exception_covers_outbox_id=true
semantic_parity_requirements_complete=true
unapproved_event_identity_substitution=0
unapproved_outbox_identity_substitution=0
unapproved_audit_identity_substitution=0
```

## 7. Exact changeset and binding counts

The machine changeset documents exactly 32 changed fields; all 1,632 other
field bindings are byte-equivalent to V2.2.

| binding kind | V2.2 | V2.3 | delta |
|---|---:|---:|---:|
| EXACT_LITERAL | 753 | 749 | -4 |
| DETERMINISTIC_DERIVATION | 210 | 200 | -10 |
| REFERENCE_TO_BOUND_FIELD | 195 | 205 | +10 |
| EXECUTION_DERIVED_PERSISTED | 426 | 430 | +4 |
| EXECUTION_DERIVED_EXTERNAL_AUTHORITY | 46 | 46 | 0 |
| NATIVE_OUTPUT | 27 | 27 | 0 |
| ADR0017_MAPPED_OUTPUT | 7 | 7 | 0 |

```text
member_count=118
database_rows=110
artifacts=8
fields=1664
```

Registry V2 and Closure V2 express semantic member edges/dispositions rather
than the replaced field values. Both remain correct and byte-identical; no
successor Registry or Closure was required.

## 8. Serialization reproof

The corrected start event is keyed by `(agent_run, AgentRun.id)`. The exact
deterministic AgentRun parent INSERT occurs before MAX+1. Two attempts at the
same fixture parent contend at the primary-key unique index; the loser cannot
pass the parent INSERT while the winner is in the allocation window.

```text
start_serialization_invariant=AGGREGATE_CREATION_SERIALIZED_BY_PARENT_IDENTITY
later_writer_serialization_domain=AgentRun.id
same_aggregate_writer_inventory_complete=true
start_source_reachable=true
completion_source_reachable=true
start_serialization_proven=true
completion_serialization_proven=true
failure_writer_domain_proven=true
allocation_window_mutual_exclusion_proven=true
new_lock_required=false
```

Completion and failure each acquire `SELECT FOR UPDATE` on that same AgentRun
before event allocation. Under READ COMMITTED they cannot see an uncommitted
new parent; after it becomes visible they lock it. They serialize with each
other. The DomainEvent stream-version index is not UNIQUE and contributes
nothing to this proof. There is no event-version retry loop, AgentRun start
idempotency key, or get-existing replay path.

Allocation behavior is unchanged native behavior. Retention verification is a
read-only persisted reread and does not alter producer behavior.

## 9. Offline validation

```text
V2.3 strict validator: PASS
V2.3 source-reachability validator: PASS
V2.3 source/negative/serialization tests: 11 PASS
V2.2 serialization regression tests: 8 PASS
V2/V2.1/V2.2 contract regressions: 91 PASS
V2.2 permanent strict validator: PASS
JSON parsing: PASS
Python compile: PASS
Django check: PASS — 0 issues
makemigrations --dry-run --check: PASS — No changes detected
fixed-hash audit: PASS
migrations_0001_0023_unchanged=true
migration_0024_absent=true
protected_runtime_changes=0
```

The first V2.3 invocation used `backend/.venv/bin/python` while already in the
`backend` directory and returned `No such file or directory`; it performed no
validation. Two later `-m foundation...` invocations were launched from the
repository root and returned `ModuleNotFoundError`; they also performed no
validation. The corrected `.venv/bin/python` invocations from `backend` passed.
An initial compile invocation named the new test without its `foundation/`
prefix and returned `[Errno 2]`; the corrected compile passed. No PASS is
attributed to any failed invocation.

## 10. Artifacts and hashes

```text
V2.3 contract       c982588956bb6009dc2489f1a724afcfe223dda0af2b7fcb884693f43f66c1d6
changeset           aff64ee5163934e8a86aeaa455ff8953f0fa4a2e69675466d74b2540d9bb4172
source evidence     2cd3326cf480c7a5700dd85b569670a7190cedb0e5e88f76a57aa548d72069fc
authorization       3a44dbb51e4721c7d1f71998547bdfe014700fcc321a175edd2f9161312aec36
strict validator    7a95d321e162c21303a13729a01d9627fc0f764204cd05a621c0e8bc86ef74a5
source validator    6f7e0de8f567066d5ca9f3a435f276af9669ffe6467c439aa7279c823d4bf716
tests               55660b5386bcce11fe8af5ec6cd43be7c3f6b6469eb72f223d84638e7fb186dd
generator           eb9bf80eae1e2db86be159906095451f6a5a68db78ee5ba92cde30c479138af2
```

## 11. Live criteria and zero effects

```text
PostgreSQL startup=NOT EXECUTED
event write=NOT EXECUTED
concurrency race=NOT EXECUTED
lock acquisition=NOT EXECUTED
producer implementation=NOT EXECUTED
Application=NOT EXECUTED
Publication=NOT EXECUTED
Activation=NOT EXECUTED
RuntimeAdoption=NOT EXECUTED
```

```text
database effects=0
PostgreSQL effects=0
container effects=0
roles effects=0
migration effects=0
producer implementation effects=0
event write effects=0
Application effects=0
Publication effects=0
Activation effects=0
RuntimeAdoption effects=0
resolver invocation=0
production effects=0
staging effects=0
shared DB effects=0
real AdminApps effects=0
MedSupplier effects=0
external API effects=0
Phase29 reconstruction effects=0
```

## 12. Blocker accounting

```text
P1-V2_1-STRICT-PHYSICAL-TYPE-CONFLICTS=CLOSED
P1-V2_2-AGENT_RUN_START-EVENT-SERIALIZATION=CLOSED
P1-V2_2-AGENT_RUN-SOURCE-IDENTITY=CLOSED
P1-CR2-SUPPORT-PRODUCER-ABSENT=OPEN_IMPLEMENTATION_ONLY
P1-CR2-INPUT-HASH-INVENTORY=OPEN_PENDING_IMPLEMENTATION
P0=0
P1=0 (source-identity/serialization correction gate only)
```

## 13. NEXT_CODEX_PROMPT

```text
# ISO SMART AI — PHASE 31.4.5B — REMAINING V2.3 DOMAIN EVENT PRODUCER SOURCE-REACHABILITY + SERIALIZATION AUDIT — OFFLINE ONLY

Work exclusively in /home/felipe/proyectos/isosmart. Entry verdict: Phase 31.4.5A Retry 1 promoted the full append-only contract docs/governance/fixtures/PHASE31_4_5A_RETRY1_ROW_LEVEL_EXECUTION_CONTRACT_V2_3.json with SHA-256 c982588956bb6009dc2489f1a724afcfe223dda0af2b7fcb884693f43f66c1d6. Preserve V2.3, V2.2, V2.1, V2, Registry V2, Closure V2, ADR-0017, ADR-0018, Product Policy V2, migrations 0001–0023, protected runtime/domain code, all historical evidence, all unrelated work, and frontend/src/components/Layout/Sidebar.jsx:28. Before repository discovery run git status --short and git diff --check and record exact output.

This phase is offline audit only. Do not create/start PostgreSQL or containers; create databases or roles; apply migrations; implement or install the support producer; implement a harness; change runtime code; execute lifecycle operations; invoke RuntimeAdoption or the resolver; call external systems; access AdminApps, MedSupplier, design-system, or sibling repositories; create migration 0024; deploy; or advance Phase 32. Do not reset, stash, clean, stage, commit, normalize, or reformat unrelated work.

Audit every remaining declared V2.3 eventing.domain_event member one by one, excluding only the two already-promoted AgentRun members 90e2d38f-9600-5701-a34c-c9827eafc88c and 47be0b7e-10d0-5e96-94fd-fcaa8ad14cfd. Enumerate the complete remaining set before conclusions. For each row record row_id, fixture purpose, declared producer, selected native/promoted producer, exact operation, transaction owner, source location, native event type, schema version, aggregate type, aggregate identity rule, DomainEvent identity allocation, every payload construction rule, source, trace/correlation/causation behavior, occurred/recorded timestamps, payload hash, aggregate-version allocation, replay behavior, and any retention reread.

For each event, audit its exact TransactionalOutbox and immutable Audit linkage: IDs and any existing ADR identity exception, event FK, status/attempts/lease/timestamps, stream/entity/action/actor/trace, metadata, sequence, predecessor hash, and native Audit identity. Contract conforms to source; do not alter source to emit synthetic fixture protocol. Synthetic business/test classification belongs in governance metadata, never native protocol fields.

For every aggregate key, inventory every same-aggregate writer across runtime and migrations. Prove the exact allocation serialization invariant for creation and later writers, including transaction boundaries, parent or aggregate lock, acquisition order, predecessor MAX query, insert point, rollback/ambiguous-commit behavior, and whether the stream-version index is UNIQUE. Do not invent retry, idempotency, replay, lock, or transaction semantics. A read-only persisted reread may verify retention only where already authorized and must not change native allocation.

Run a complete downstream audit for event IDs, aggregate IDs/types, event types, hashes/material, Outbox/Audit links, Registry edges, Closure membership, checkpoints, support graph, and retained evidence. If an existing row is source-unreachable but can be corrected without architecture, security, row-universe, producer, or transaction-ownership change and without a new identity exception, create one full append-only V2.4 successor plus exact field changeset, narrow correction authorization, source matrix, permanent strict/source validators, and negative tests. Preserve V2.3 bytes. If Registry or Closure embeds changed exact semantics, create its append-only successor; otherwise prove and preserve its byte-identical hash. Do not add or remove any of the 118 members.

For every native/promoted producer, negative tests must reject wrong event type, aggregate type or aggregate identity; impossible payload/source; unapproved Event/Outbox identity substitution; Audit mismatch; dangling superseded values; incomplete writer inventory; nonexistent serialization; retry fiction; reference cycles; physical/nullability/enum mismatches; and undocumented contract differences. Run the existing V2.3, V2.2, V2.1 and V2 regressions, fixed-hash audit, JSON parsing, Python compile, Django check, makemigrations dry-run, migration/source/protected hashes, git diff --check, and final status using only backend/.venv. Guards: database_attempts=0, network_attempts=0, container_attempts=0, lifecycle_attempts=0, resolver_invocations=0.

Promote only if all_declared_DomainEvent_rows_mapped=true, all_declared_DomainEvent_rows_source_reachable=true, all same-aggregate writer inventories are complete, every exact allocation window is serialized by a source-proven invariant, unresolved_event_concurrency_contracts=0, all downstream references are resolved, unapproved identity substitutions=0, strict binding/type/reference defects=0, architecture_changed=false, new_lock_required=false, migrations 0001–0023 unchanged, migration 0024 absent, protected_runtime_changes=0, no producer is implemented, and all live/effect counters remain zero. Otherwise emit PHASE 31.4.5B — NOT PROMOTED with the exact row, field, source, writer, or serialization blocker. No producer implementation resumes until all_declared_DomainEvent_rows_mapped=true, all_declared_DomainEvent_rows_source_reachable=true, and unresolved_event_concurrency_contracts=0; after that, return to Phase31.4.5 implementation closure, not Phase 32.
```
