# Phase 31.4.5A — AgentRun start event serialization decision gate

## 1. Verdict

`PHASE 31.4.5A — NOT PROMOTED`

The coherent native stream `(aggregate_type="agent_run", aggregate_id=run.id)`
is serialized for creation by `AGGREGATE_CREATION_SERIALIZED_BY_PARENT_IDENTITY`.
That proof cannot promote the exact blocking V2.2 row: V2.2 fixes the AgentRun
primary key as `b87bdcde-c623-522f-a0ac-ff81f61df8e8`, but fixes the event
aggregate ID as `51c9bad4-88fb-5608-b3c9-edd578efeeb9`, fixes a descriptive
synthetic aggregate type instead of `agent_run`, and fixes
`phase31.4.4a.synthetic` instead of `agent_run.started`. The selected native
producer hardcodes the latter three values from `run.id` and its event contract.

This is a V2.2 source-binding contradiction, not authority to add a lock.
V2.2 is preserved byte-for-byte and requires an append-only contract successor.

## 2. Entry blocker

Entry was `PHASE 31.4.5 — RETRY 3 — NOT PROMOTED` with:

```text
P1-V2_1-STRICT-PHYSICAL-TYPE-CONFLICTS=CLOSED
P1-CR2-SUPPORT-PRODUCER-ABSENT=OPEN_EVENT_CONCURRENCY_CONTRACT
P1-CR2-INPUT-HASH-INVENTORY=OPEN_PENDING_EXECUTABLE_IMPLEMENTATION
P1-V2_2-AGENT_RUN_START-EVENT-SERIALIZATION=OPEN
P0=0
```

The exact row is `eventing.domain_event::90e2d38f-9600-5701-a34c-c9827eafc88c`.

## 3. Git baseline

The required commands were the first repository operations. Exact output:

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

No reset, stash, clean, stage, commit, normalization, or sibling-repository
inspection occurred. The Sidebar line was not touched.

## 4. Entry hashes

All required predecessor bytes match:

```text
V2.2          a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d
Registry V2   58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb
Closure V2    80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425
ADR-0018      f9f6272c72e433241f66e44884b53dc804a667b32950c8ab098df6473ecf6089
Migration set cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc
```

`migration_0024_absent=true`.

## 5. Mandatory decision reading

`mandatory_decision_reading_complete=true` for this decision. Reading covered
the Retry3 report and blockers; the blocking V2.2 member and field bindings;
ADR-0017 and ADR-0018; Product Policy V2; the support-producer contract;
AgentRun, input, link, Event and Outbox models and migrations; complete start,
completion and failure services; every helper between parent creation and
event insertion; tenant transaction ownership; canonicalization; immutable
Audit append; Recommendation composition; AgentDecision and downstream paths;
event writers, claims, retries, rollback hooks, and historical harness evidence.

The source-wide writer search was completed. No live system was used.

## 6. Exact event

```text
qualified_table=eventing.domain_event
row_id=90e2d38f-9600-5701-a34c-c9827eafc88c
contract event_type=phase31.4.4a.synthetic
contract aggregate_type=PHASE31.4.4A TEST ONLY — DomainEvent:agent-run-start — aggregate_type
contract aggregate_id=51c9bad4-88fb-5608-b3c9-edd578efeeb9
contract event_id=1af3e9a8-65f7-5952-a991-1133872659f9
contract source=PHASE31.4.4A TEST ONLY — DomainEvent:agent-run-start — source
```

The row ID above is the contract member identifier; it is not the bound
physical `DomainEvent.event_id` value.

## 7. Exact producer

The contract names `phase31.4.4-agent-provenance-producer/v1`; Retry3 selects
`AgentRunCommandService._event_outbox_audit` at
`backend/foundation/agent_runtime.py:219-249` under
`start_agent_run` at lines 251-332. The helper hardcodes:

```text
event_type=agent_run.started (caller selected from EVENT_CONTRACTS)
aggregate_type=agent_run
aggregate_id=run.id
source=iso-smart-agent-runtime
```

Its `event_id` is also a fresh `uuid4()` rather than the contract's
deterministic UUIDv5. It therefore cannot emit the exact V2.2 row as bound.

## 8. Exact transaction timeline

The native order, from source rather than names, is:

1. Before BEGIN, normalize `trace_id`, capture `started_at`, allocate `run_id`
   with `uuid4()`, normalize autonomy, and require nonempty inputs
   (`agent_runtime.py:258-261`).
2. `trusted_tenant_context` opens the outermost `transaction.atomic` BEGIN
   (`tenant_context.py:54-66`).
3. Set and verify transaction-local tenant, actor, and trace settings
   (`tenant_context.py:21-33,64-65`).
4. Read Organization, published AgentDefinition, and published ModelPolicy;
   validate exact policy/capability/model/autonomy (`agent_runtime.py:263-282`).
5. INSERT AgentRun (`agent_runtime.py:283-295`). Its primary-key and redundant
   tenant/organization/ID unique indexes participate in uniqueness checking;
   this is not an explicit parent row lock.
6. For each input, read published Edition, matching Requirement, published
   Rule and Evidence, then INSERT AgentRunInput (`agent_runtime.py:296-324`).
7. Render state (`agent_runtime.py:325`, `_state` at 410-435).
8. Read MAX for native key `("agent_run", run.id)` and add one
   (`agent_runtime.py:221-225`).
9. INSERT DomainEvent (`agent_runtime.py:227-235`).
10. INSERT TransactionalOutbox (`agent_runtime.py:236-240`).
11. Validate/canonicalize Audit input, acquire the audit stream's
    transaction-scoped advisory lock, read its predecessor, and INSERT the
    immutable Audit (`agent_runtime.py:241-248`; `audit.py:57-73`; migration
    0003 lines 288-344).
12. Evaluate the deliberate failure hook (`agent_runtime.py:330-331`).
13. On context exit, execute the deferred AgentRun-input completeness trigger
    (migration 0011 lines 286-293,338-339), then COMMIT.

The native service has no repeated fresh-authority/precommit validation beyond
its reads, the failure hook, database constraints, and the deferred input
constraint. The future exact producer contract separately requires immediate
precommit revalidation; it has not been implemented.

## 9. AgentRun identity semantics

Native `start_agent_run` uses a fresh `uuid4()` and accepts no `run_id` or
idempotency key. V2.2 instead declares the exact AgentRun row as
`UUIDV5_FIXTURE_ASSIGNED` with primary key
`b87bdcde-c623-522f-a0ac-ff81f61df8e8`, authorized as an enumerated ADR-0018
fixture identity.

The requested `51c9bad4-88fb-5608-b3c9-edd578efeeb9` is not the AgentRun ID.
It is a separate deterministic UUIDv5 output bound to the blocking event's
`aggregate_id`. Thus it is a predetermined fixture field identity, not native
generated identity and not idempotency-derived identity. A parameterless future
producer would have to load it from the exact contract; the native service has
no parameter through which it can be supplied.

## 10. Parent insert semantics

For a coherent deterministic run identity, two INSERTs of the same
`qms.agent_run.id` contend at the primary-key unique index. PostgreSQL waits
for the transaction owning the uncommitted conflicting index entry. Winner
COMMIT makes the waiter fail uniqueness before returning from INSERT; winner
ROLLBACK permits the waiter to finish INSERT and continue. Therefore the loser
cannot reach MAX while the winner is in the allocation window.

This proves `AGGREGATE_CREATION_SERIALIZED_BY_PARENT_IDENTITY` only when the
event aggregate ID equals the inserted AgentRun primary key.

## 11. PK and natural uniqueness

Migration 0011 lines 96-132 define `id uuid PRIMARY KEY` and
`UNIQUE(tenant_id,organization_id,id)`. The latter repeats the ID rather than
creating a business natural key. No uniqueness constraint identifies equal
run material, trace, Definition, Policy, or inputs. Native identical requests
therefore create distinct UUIDs and distinct runs.

## 12. Idempotency and claim semantics

Start has no idempotency key, claim row, receipt, catch/retry loop, or
get-existing branch. Claims and idempotency in controlled execution and
Application are separate aggregates and do not govern AgentRun creation.

## 13. Same-run concurrent-start reachability

For native calls with identical arguments, T1 and T2 receive different UUID4
run IDs; both may reach MAX, but for different streams. They are not the
same-run hypothesis.

For an ADR-0018 exact producer attempting the same coherent AgentRun ID, T2 is
stopped at parent INSERT as described in section 10. Both cannot legally reach
MAX for the same `run.id`.

Therefore `same_run_concurrency_reachability_resolved=true` and the answer to
the primary question is **no for the coherent native key**. That result does
not cover the exact blocking row because its contract aggregate ID is not
`run.id`.

## 14. Replay reachability

After a coherent exact first transaction commits, another deterministic parent
creation is rejected at AgentRun primary-key insertion. It does not return the
existing result, does not re-enter `_event_outbox_audit`, and does not allocate
another version. Native replay with the same inputs is not replay at all: it
creates a fresh run UUID and a new stream.

Product Policy V2 allows fresh-authority read-only retrieval/reconciliation of
an immutable prior result. It does not authorize a second start event or rewrite
original provenance. `replay_reachability_resolved=true`.

## 15. Failure windows

- A — failure before AgentRun INSERT: zero persisted effects; a retry may start
  from the beginning.
- B — AgentRun inserted, failure before event: outer transaction rollback
  removes parent and inputs; a retry may insert the identity and proceed.
- C — event inserted, failure before Outbox/Audit: outer transaction rollback
  removes event and every earlier write; any Outbox/Audit already written is
  also rolled back. A retry may start from the beginning.
- D — ambiguous client result after COMMIT: the committed graph remains.
  Deterministic duplicate creation fails before event allocation; authorized
  read-only reconciliation is required.

No window leaves a committed parent without its start event through the native
transaction boundary. `failure_window_analysis_complete=true`.

## 16. Same-aggregate writer inventory

`same_aggregate_writer_inventory_complete=true`.

| Producer | Event | Owner | Formula | Serialization | Relative timing / same key |
|---|---|---|---|---|---|
| `start_agent_run -> _event_outbox_audit` | `agent_run.started` | `trusted_tenant_context` | MAX+1 | coherent parent creation uniqueness | first event; `agent_run/run.id` |
| `complete_agent_run_with_recommendation -> _event_outbox_audit` | `agent_run.completed` | `trusted_tenant_context` | MAX+1 | `SELECT FOR UPDATE` AgentRun at line 339 | after visible running parent; same key |
| `fail_agent_run -> _event_outbox_audit` | `agent_run.failed` | `trusted_tenant_context` | MAX+1 | `SELECT FOR UPDATE` AgentRun at line 394 | after visible running parent; same key |

Recommendation creation writes `recommendation/recommendation.id`.
AgentDecision, Approval, action preparation/authorization/execution,
effectiveness and learning paths use their own aggregate types and IDs.
Decision creation locks AgentRun but does not write its event stream. No other
runtime or migration producer writes `agent_run/run.id`.

## 17. Start versus later-writer concurrency

The configured service does not override isolation, so the operation uses the
PostgreSQL backend's default READ COMMITTED behavior. A completion/failure query
cannot see the uncommitted newly inserted AgentRun. If its statement snapshot
precedes start COMMIT, `.get()` finds no row and it cannot emit. If it starts
after COMMIT, it obtains `SELECT FOR UPDATE` on the now-visible parent before
MAX. Completion and failure also serialize against each other on that row.

This proves no native later writer overlaps the coherent start allocation
window. It does not create an identity relation missing from V2.2.

## 18. Existing lock inventory

Start has no parent row lock, event advisory lock, or isolation escalation.
Parent insertion uniqueness is the relevant coherent creation invariant.
Completion and failure use the parent row lock. Immutable Audit later takes a
distinct advisory lock over `tenant:stream_type:stream_id`; because it is
acquired after DomainEvent insertion it cannot serialize event allocation.
Controlled-execution and Application locks have unrelated namespaces and were
not reused.

## 19. Uniqueness-constraint analysis

DomainEvent has an event UUID primary key and
`UNIQUE(tenant_id,event_id)`. Its
`(tenant_id,aggregate_type,aggregate_id,aggregate_version)` object is a plain
index, not UNIQUE (migration 0003 lines 47-71). There is consequently neither
an allocation mechanism nor even a stream-version collision constraint in the
frozen schema. No conflict-and-retry allocation loop exists.

## 20. Existing serialization conclusion

```text
coherent_native_existing_serialization_sufficient=true
coherent_native_invariant=AGGREGATE_CREATION_SERIALIZED_BY_PARENT_IDENTITY
exact_V2_2_blocking_event_existing_serialization_sufficient=false
allocation_window_mutual_exclusion_proven_for_exact_blocking_event=false
```

The failed premise is exact: `same aggregate_id == same AgentRun PK` is false
in V2.2. The contract aggregate type and event type also contradict source.

## 21. Conflict/retry semantics

No DomainEvent version-conflict retry exists. Parent primary-key conflict is a
pre-allocation rejection, not an event-version retry. No source catches that
error to retrieve the prior AgentRun. V2.2 does not authorize uniqueness
failure plus retry as allocation semantics.

## 22. New-lock necessity

No new lock is authorized. Locking either `run.id` or the contract's unrelated
event key would conceal rather than repair the broken source binding. The
contract must first establish which stream resource the event represents.

```text
new_lock_required=UNDECIDABLE_UNTIL_CONTRACT_SUCCESSOR
new_narrow_serialization_semantic_authorized=false
implementation_change_required=false
```

## 23. All-writers participation rule

For the coherent native stream, all three actual writers participate in one
parent-identity domain: creation uniqueness first, then parent row locks for
state transitions. For the exact V2.2 event key, no selected source writer is
reachable, so all-writer participation cannot be truthfully claimed. A
start-only advisory lock is rejected.

## 24. Proposed narrow semantic

None. This gate does not choose a lock namespace, key, primitive, or retry
policy. The minimum next change is an append-only contract successor that binds
the start and completion events to the exact AgentRun ID and native event
semantics, then reruns this decision proof.

## 25. Lock ordering

No new lock means no new lock-order edge. Existing native order is tenant
context, parent insertion or parent row lock, DomainEvent allocation/insert,
Outbox insert, then Audit advisory lock. The controlled-execution and
Application locks are outside this event stream. Lock-order promotion for a
hypothetical new event lock is intentionally not claimed.

## 26. Post-insert reread decision

The ORM INSERT argument is authoritative for the allocated integer because
`aggregate_version` is supplied, not database-generated. The native helper
discards the created DomainEvent object and performs no reread. V2.2 explicitly
requires a persisted reread and JSON-integer equality for retention, so a
future support producer must reread after INSERT (or postcommit before the next
consumer as its freeze contract requires). That read-only retention step does
not alter allocation semantics. It cannot execute until the event binding is
corrected.

## 27. Registry and Closure impact

Registry V2 and Closure V2 remain byte-identical. The discovered contradiction
concerns how an already retained member is produced, not retained membership.
Any future finding that semantic edges must change is a separate blocker.

## 28. Security impact

`security_changed=false`; RLS and privileges were not modified. No advisory
lock was introduced. PostgreSQL transaction-level advisory locks would not by
themselves require a new table privilege, but that observation grants no lock
authority.

## 29. ADR decision

```text
architecture_changed=false
ADR0019_required=false
ADR0019_created=false
contract_successor_required=true
```

ADR-0019 would be misleading because no new serialization semantic was closed.
This is the contract-successor stop required when V2.2 must materially change.

## 30. Offline tests

`backend.foundation.test_phase31_4_5a_agent_run_start_serialization` executed
8 tests: all PASS. They freeze the predecessor hash/0024 absence, reject the
false parent-identity counterexample, prove native insertion ordering and
event-key use, prove later-writer row locking, identify absent start
idempotency, and prove the DomainEvent stream-version index is non-unique.

The V2.2 strict-type validator also remains the appropriate predecessor gate.
Two path-style invocations failed at import time without validation because the
validator must be invoked as a package module. The correctly scoped command
`./.venv/bin/python -m foundation.phase31_4_4b_strict_type_validator` passed:
118 members, 1,664 fields, 753 exact literals, 426 execution-derived persisted
bindings, and zero errors. No PASS is claimed for either failed invocation.

## 31. Live criteria NOT EXECUTED

```text
PostgreSQL concurrency=NOT EXECUTED
event write=NOT EXECUTED
lock acquisition=NOT EXECUTED
race test=NOT EXECUTED
```

Offline reasoning is not claimed as behavioral PostgreSQL proof.

## 32. Decision artifact hashes

```text
decision evidence 5a1bc305b84fb10472905303aaadea668cf9e220b7385c01ae1c1a3e8c3040df
offline tests     a792ced709ca0a58e8ed55389ed6aaa967b02ed58fbc96b7f2db93f0be01d535
```

## 33. Git hygiene

Only this report, the machine-readable evidence, and its offline source/contract
test were created. All pre-existing work remains unstaged and untouched. Final
`git diff --check` retains only the pre-existing Sidebar warning.

## 34. Zero effects

```text
database effects=0
PostgreSQL effects=0
container effects=0
role effects=0
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

## 35. P0/P1

```text
P1-V2_1-STRICT-PHYSICAL-TYPE-CONFLICTS=CLOSED
P1-CR2-SUPPORT-PRODUCER-ABSENT=OPEN_EVENT_SOURCE_BINDING_CONTRACT
P1-CR2-INPUT-HASH-INVENTORY=OPEN_PENDING_EXECUTABLE_IMPLEMENTATION
P1-V2_2-AGENT_RUN_START-EVENT-SERIALIZATION=OPEN_CONTRACT_SUCCESSOR_REQUIRED
P0=0
P1=3
```

## 36. Residual risk

V2.2's completion event has the same defect pattern: its aggregate ID is
`91792d67-eb35-5e1d-9c62-c285f7b97057`, not the AgentRun ID, and its aggregate
and event types are synthetic literals. Correcting only the start row would
leave the selected helper's single AgentRun stream split into unrelated
contract streams. The successor gate must inspect both AgentRun events without
silently broadening to the remaining 11 unrelated event rows.

Direct table grants remain a historical trust-boundary residual, but no
source-authorized direct path was found that writes the coherent AgentRun
event stream outside the three service operations.

## 37. Final verdict

`PHASE 31.4.5A — NOT PROMOTED`

The exact blocking event is not source-reachable under its selected producer,
so neither RESULT A nor RESULT B is valid. No lock, ADR, implementation,
PostgreSQL action, or Phase 31.4.5B audit is authorized.

## 38. NEXT_CODEX_PROMPT

```text
PHASE 31.4.5A RETRY 1 — AGENTRUN DOMAIN EVENT SOURCE-IDENTITY CONTRACT SUCCESSOR GATE — OFFLINE ONLY

Work exclusively in /home/felipe/proyectos/isosmart. Preserve all unrelated work, migrations 0001–0023, V2.2, Registry V2, Closure V2, ADR-0017, ADR-0018, Product Policy V2, protected runtime/domain code, historical evidence, and frontend/src/components/Layout/Sidebar.jsx:28. Do not reset, stash, clean, stage, commit, access siblings, start PostgreSQL or containers, create databases or roles, apply migrations, execute lifecycle code, implement a producer or lock, create migration 0024, invoke RuntimeAdoption or a resolver, use external systems, or advance Phase 32.

Enter from PHASE 31.4.5A — NOT PROMOTED and the evidence PHASE31_4_5A_AGENT_RUN_START_EVENT_SERIALIZATION_DECISION_V1.json. Create an append-only successor to V2.2 only if the exact frozen source proves the correction: bind both DomainEvent:agent-run-start and DomainEvent:agent-run-complete aggregate_type to "agent_run", aggregate_id by REFERENCE_TO_BOUND_FIELD to qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8.id, and event_type to the exact native EVENT_CONTRACTS values agent_run.started and agent_run.completed. Audit event source, payload, trace/correlation/causation, event IDs, Outbox links, Audit links, versions, Registry/Closure impact, and every downstream reference; do not assume these three corrections are the only contradictions. Preserve V2.2 bytes and issue a changeset plus strict offline validator/tests. If a source-faithful successor cannot be closed without changing intended fixture semantics, remain NOT PROMOTED. If it closes, rerun the Phase31.4.5A parent-identity serialization proof for the corrected exact stream. Do not begin the remaining-event Phase31.4.5B audit until this exact AgentRun stream is source-reachable and its serialization gate is promoted.
```
