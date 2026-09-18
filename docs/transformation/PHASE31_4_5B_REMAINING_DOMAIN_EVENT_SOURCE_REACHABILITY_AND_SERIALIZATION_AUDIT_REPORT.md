# Phase 31.4.5B Remaining DomainEvent Source-Reachability and Serialization Audit

## 1. Verdict

`PHASE 31.4.5B — PROMOTED — ALL 13 DECLARED DOMAIN EVENT ROWS SOURCE-REACHABLE; EVENT/OUTBOX/AUDIT IDENTITIES AUTHORIZED; SAME-AGGREGATE WRITER INVENTORIES COMPLETE; VERSION SERIALIZATION CONTRACTS CLOSED; PRODUCER IMPLEMENTATION MAY RESUME`

This is an offline source/contract promotion only. It is not PostgreSQL acceptance and does not implement the producer.

## 2. Entry authorization

Authorized predecessor: `PHASE 31.4.5A — RETRY 1 — PROMOTED`.

V2.3 required/observed SHA-256: `c982588956bb6009dc2489f1a724afcfe223dda0af2b7fcb884693f43f66c1d6` — PASS.

## 3. Git baseline

Initial `git status --short`:

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

Initial `git diff --check`:

```text
frontend/src/components/Layout/Sidebar.jsx:28: trailing whitespace.
+    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' },[one trailing space]
```

This is the known preserved warning. No reset, stash, clean, stage, commit, or unrelated reformat occurred. A repository-discovery command issued before the attachment prohibition had been fully read listed `AGENTS.md` paths in sibling repositories and one protected Podman path; it did not read sibling file contents or modify anything. No later sibling access occurred.

## 4. Predecessor hashes

| Artifact | SHA-256 |
|---|---|
| V2 | `962ec0b393b49c3c0a2894e32bb9a3246cbf7793cfd600391248634bee56f70b` |
| V2.1 | `acd9e5551a04fc60356fedc2abdc4170932274913795fb6a5a4952ebf9477d85` |
| V2.2 | `a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d` |
| V2.3 | `c982588956bb6009dc2489f1a724afcfe223dda0af2b7fcb884693f43f66c1d6` |
| Registry V2 | `58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb` |
| Closure V2 | `80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425` |

All hashes embedded by V2.3 and all migration/source hashes validated. Migrations 0001–0023 are unchanged; migration 0024 is absent; protected runtime changes from this phase are zero.

## 5. DomainEvent enumeration

| Row ID | Fixture purpose | Declared producer | Declared/native operation in V2.4 | Event type | Aggregate type / ID binding | Promoted |
|---|---|---|---|---|---|---|
| `90e2d38f-9600-5701-a34c-c9827eafc88c` | agent-run-start | agent-provenance/v1 | `start_agent_run` | `agent_run.started` | `agent_run` / AgentRun.id | yes |
| `47be0b7e-10d0-5e96-94fd-fcaa8ad14cfd` | agent-run-complete | agent-provenance/v1 | `complete_agent_run_with_recommendation` | `agent_run.completed` | `agent_run` / AgentRun.id | yes |
| `b043e2e7-7210-5c11-a718-c22aa97574db` | agent-decision | controlled-opportunity/v1 | `record_agent_decision` | `agent_decision.recorded` | `agent_decision` / AgentDecision.id | no |
| `d087529c-6a0e-5386-ad10-39992d4f5405` | action-plan-prepared | controlled-opportunity/v1 | `prepare_action_plan` | `action_plan.prepared` | `action_plan` / ActionPlan.id | no |
| `bc7bdbed-f01c-50f1-9ad9-8dea8106f586` | human-approval | controlled-opportunity/v1 | `record_human_approval` | `approval.recorded` | `approval` / Approval.id | no |
| `87e477b2-b854-55e2-95a5-2ed0785d6f39` | execution-authorization | controlled-opportunity/v1 | `authorize_action_plan` | `execution_authorization.granted` | `execution_authorization` / Authorization.id | no |
| `77465ad0-559f-5317-9c26-c029e0cb16f6` | controlled-opportunity-execution | controlled-opportunity/v1 | `foundation_0015_controlled_opportunity_execution` | `action_execution.succeeded` | `action_execution` / ActionExecution.id | no |
| `39b7cc2f-00ff-589d-b0c4-812cb35595e8` | effectiveness-check | effectiveness/v1 | `record_effectiveness_check` | `effectiveness_check.recorded` | `effectiveness_check` / Check.id | no |
| `8f2146ff-48c5-5095-b034-73bb2f0b5894` | learning-signal | learning-signal/v1 | `create_signal` | `learning_signal.created` | `learning_signal` / Signal.id | no |
| `005da83c-7a57-5fc5-8162-fa657a75304b` | learning-proposal | governed-learning/v2 | `create_proposal` | `learning_proposal.created` | `learning_proposal` / Proposal.id | no |
| `7fc5b06e-b3ca-5a98-a250-d96ee3307b4c` | learning-review | governed-learning/v2 | `record_learning_proposal_review` | `learning_proposal.reviewed` | `learning_proposal_review` / Review.id | no |
| `82dd0d51-fc95-50c4-8047-d31b0acc1ea4` | learning-decision | governed-learning/v2 | `record_learning_proposal_decision` | `learning_proposal.decision_recorded` | `learning_proposal_decision` / Decision.id | no |
| `8bf2bb5b-4cea-5aa0-9a05-18fec0cf049c` | learning-authorization | governed-learning/v2 | `authorize_learning_proposal_application` | `learning_application.authorized` | `learning_application_authorization` / Authorization.id | no |

Counts: `total_declared_DomainEvent_rows=13`, `already_promoted_rows=2`, `remaining_rows=11`, `duplicate_rows=0`, `unknown_rows=0`.

## 6. Authoritative 13-row matrix

Every row has: source/event/aggregate/identity/payload/source match = true; Event identity authorized = true; Outbox reachable/identity authorized = true; Audit expected/reachable/identity authorized = true; writer inventory complete = true; serialization proven = true; downstream references resolved = true.

| Row ID | Serialization | Status |
|---|---|---|
| `90e2d38f-9600-5701-a34c-c9827eafc88c` | `PARENT_CREATION_IDENTITY_SERIALIZATION` | PASS |
| `47be0b7e-10d0-5e96-94fd-fcaa8ad14cfd` | `PARENT_ROW_SELECT_FOR_UPDATE` | PASS |
| `b043e2e7-7210-5c11-a718-c22aa97574db` | `PARENT_ROW_SELECT_FOR_UPDATE` | PASS |
| `d087529c-6a0e-5386-ad10-39992d4f5405` | `PARENT_CREATION_IDENTITY_SERIALIZATION` | PASS |
| `bc7bdbed-f01c-50f1-9ad9-8dea8106f586` | `PARENT_CREATION_IDENTITY_SERIALIZATION` | PASS |
| `87e477b2-b854-55e2-95a5-2ed0785d6f39` | `PARENT_CREATION_IDENTITY_SERIALIZATION` | PASS |
| `77465ad0-559f-5317-9c26-c029e0cb16f6` | `SOURCE_AUTHORIZED_ADVISORY_XACT_LOCK` | PASS |
| `39b7cc2f-00ff-589d-b0c4-812cb35595e8` | `PARENT_CREATION_IDENTITY_SERIALIZATION` | PASS |
| `8f2146ff-48c5-5095-b034-73bb2f0b5894` | `PARENT_CREATION_IDENTITY_SERIALIZATION` | PASS |
| `005da83c-7a57-5fc5-8162-fa657a75304b` | `PARENT_CREATION_IDENTITY_SERIALIZATION` | PASS |
| `7fc5b06e-b3ca-5a98-a250-d96ee3307b4c` | `PARENT_CREATION_IDENTITY_SERIALIZATION` | PASS |
| `82dd0d51-fc95-50c4-8047-d31b0acc1ea4` | `SOURCE_PROVEN_TRANSACTIONAL_STATE_EXCLUSION` | PASS |
| `8bf2bb5b-4cea-5aa0-9a05-18fec0cf049c` | `SOURCE_PROVEN_TRANSACTIONAL_STATE_EXCLUSION` | PASS |

The complete per-column matrix is embedded in V2.4 under `remaining_domain_event_source_audit.matrix`.

## 7. Promoted AgentRun rows

The two AgentRun rows reuse the promoted 31.4.5A Retry1 proof. Start inserts its new AgentRun parent before allocation; completion and the legal failure sibling lock AgentRun with `select_for_update` before allocation. Native protocol is `agent_run.*`, source is `iso-smart-agent-runtime`, the payload is `_state(...)`, and Event/Outbox identities use the existing ADR-0018 fixture exception. No decision was reopened.

## 8. Eleven remaining rows

All eleven independently close source reachability, identity authority, version allocation, Outbox, Audit, and downstream retention. No sibling row is used as a substitute for a row-level proof.

## 9. Source producer mappings

| Rows | Frozen source |
|---|---|
| agent decision, human approval | `backend/foundation/human_decision.py` |
| action plan, execution authorization | `backend/foundation/action_authorization.py` |
| controlled execution | `backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py` |
| effectiveness | `backend/foundation/effectiveness.py` |
| signal, proposal | `backend/foundation/governed_learning.py` |
| review, decision, learning authorization | `backend/foundation/learning_proposal_governance.py` |
| immutable audit allocation/serialization | `backend/foundation/audit.py`; migration 0003 |

V2.4 freezes the exact source hashes for these files.

## 10. Event protocol

All Event fields were audited: `event_id`, `tenant_id`, `event_type`, `schema_version`, `aggregate_type`, `aggregate_id`, `aggregate_version`, `occurred_at`, `recorded_at`, `trace_id`, `correlation_id`, `causation_id`, `source`, `payload`, and `payload_hash`. V2.4 binds native event/source literals, artifact identity references, source-built payload/hash, operation trace, optional correlation, NULL causation, schema version 1, and persisted timestamps.

## 11. Event identities

Native producers allocate `uuid4()` except the controlled SQL operation, which allocates `uuidv7()`. V2.4 does not claim those predetermined values are native. Exact fixture substitution remains solely the enumerated ADR-0018 exception already present in V2; no exception was added or broadened.

`unapproved_event_identity_substitutions=0`.

## 12. Outbox mappings

Every event is followed in the same transaction by one `eventing.transactional_outbox` row linked through `domain_event_id`, with the same tenant, `pending`, `publish_attempts=0`, `available_at=occurred_at`, and native database timestamps/default NULL lease/publication/error fields.

## 13. Outbox identities

Python producers allocate the Outbox UUID through the model default (`uuid4()`); controlled SQL uses `uuidv7()`. Exact fixture values are covered by the existing ADR-0018 enumerated substitution. `unapproved_outbox_identity_substitutions=0`.

## 14. Audit mappings

All eleven operations append immutable audit in the same transaction after Outbox. Native action equals event type. Stream/entity are the native aggregate, except Effectiveness uses the ActionExecution lineage as `stream_id` while auditing the EffectivenessCheck entity. Controlled execution uses `execution_service`; decision/preparation use `worker`; approval/effectiveness use `human`; governed learning uses `human_governance`; execution authorization uses `governance_service`.

## 15. Audit identities

`audit.append_immutable_audit` exclusively allocates UUIDv7. The contract retains `NATIVE_OUTPUT`; no caller-supplied audit ID is invented. `unapproved_audit_identity_substitutions=0`.

## 16. Payload, source, and trace semantics

Payloads are the exact native operation state dictionaries/JSONB, canonicalized by the frozen producer; payload hashes are native SHA-256 canonical hashes. Trace comes from the operation/artifact. Correlation is copied only where the producer supports it; otherwise it is NULL. Causation is NULL because these producers do not supply it. Synthetic classification remains governance metadata, never a native protocol field.

## 17. Aggregate-version allocation

Agent decision, approval, signal, review, decision, and learning authorization emit first-event version 1. Effectiveness and proposal copy their persisted revision. Action plan and execution authorization use the source `MAX()+1`. Controlled execution uses SQL `MAX()+1` under its exact advisory transaction lock. AgentRun retains the promoted allocation proof.

The index on `(tenant_id, aggregate_type, aggregate_id, aggregate_version)` is `PLAIN_INDEX`, not UNIQUE. No serialization claim relies on it.

## 18. Same-aggregate writer inventories

| Aggregate | All legal writers | Exclusion before allocation |
|---|---|---|
| `agent_run` | start, complete, fail | parent creation; later `select_for_update(AgentRun.id)` |
| `agent_decision` | `record_agent_decision` | AgentRun row lock plus new decision parent |
| `action_plan` | `prepare_action_plan` | new parent PK/idempotency constraint before event |
| `approval` | human approval/rejection/change request through `_record` | new Approval parent PK before event |
| `execution_authorization` | `authorize_action_plan` | new parent/immutable idempotency state before event |
| `action_execution` | Python `ActionExecutionCommandService`; SQL controlled execution | new ActionExecution parent; SQL additionally uses exact per-aggregate advisory lock |
| `effectiveness_check` | `record_effectiveness_check` | new check parent; predecessor constraints reject stale competitors |
| `learning_signal` | `create_signal` | new signal parent before event |
| `learning_proposal` | `create_proposal` | new proposal revision parent before event |
| `learning_proposal_review` | `record_learning_proposal_review` | new review parent before event |
| `learning_proposal_decision` | `record_learning_proposal_decision` | proposal lock/one-decision state; replay/conflict before event |
| `learning_application_authorization` | `authorize_learning_proposal_application` | idempotency state; replay/conflict before event |

`all_same_aggregate_writer_inventories_complete=true`.

## 19. Transaction timelines

Python command families: begin trusted tenant transaction → bind tenant/authority → read and validate upstream state → acquire the source-declared row/state exclusion where applicable → insert the aggregate parent → allocate/copy version → insert DomainEvent → insert Outbox → append immutable Audit → failure hook/revalidation → commit.

Controlled SQL: begin caller transaction → tenant and governance checks → idempotency row lock → insert ActionExecution → lock Opportunity → business revision/receipt → source advisory lock → `MAX()+1` → Event → Outbox → Audit → failure hook → commit.

## 20. Serialization classifications

Only the allowed classifications shown in the 13-row matrix are used. The allocation-window property holds: no second legal transaction can reach Event version allocation for the same aggregate identity, or it is rejected/stopped by the parent PK, row lock, idempotency/immutable state, or frozen advisory transaction lock first.

`every_allocation_window_has_source_proven_serialization=true`; `unresolved_event_concurrency_contracts=0`.

## 21. Replay

Native idempotent operations return the immutable existing artifact or raise a material conflict before a new Event. Non-idempotent creation operations have no invented retry/replay promise. Controlled execution locks and returns its existing receipt on an identical idempotency replay.

## 22. Rollback

Failure hooks before/after artifact, Event, Outbox, and Audit are within the owning transaction. An exception before commit rolls back the entire applicable unit. No live fault injection ran in this phase.

## 23. Ambiguous commit

No new ambiguous-commit behavior is invented. Callers may use only existing idempotent retrieval/reconciliation semantics where the frozen operation supplies them; otherwise outcome is not claimed by this offline audit.

## 24. Retention rereads

Allocation semantics remain native. Authorized post-commit read-only rereads are retention verification only and do not alter identity or version allocation.

## 25. Downstream references

Event IDs, event types, aggregate tuple/version, payload/hash/source, Outbox IDs, Audit outputs, Registry edges, checkpoint/support graph, closure material, and retained evidence were scanned. All V2.4 operational references resolve; Registry and Closure membership/disposition remain unchanged.

`all_downstream_references_resolved=true`.

## 26. Source-unreachable findings

V2.3’s remaining 11 rows used `phase31.4.4a.synthetic` plus descriptive aggregate/source/payload/audit literals. Those bindings are classified `SUPERSEDED_SOURCE_UNREACHABLE_FIXTURE_BINDING`. V2.3 bytes remain untouched; V2.4 carries no operational reference to those protocol literals.

## 27. V2.4 decision

V2.4 was required. All corrections are source-proven and non-architectural; the row universe, producer ownership, security, transactions, and identity exception are unchanged; no lock was added.

V2.4 SHA-256: `a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387`.

## 28. V2.3 to V2.4 changeset

The machine-readable changeset contains all 231 changed field bindings, each with old/new binding, native source, reason, impact flags, and downstream consumers.

Changeset SHA-256: `4204d022492de843d7f6763dfb05f3ce7ec5e166fc4c14de4b8b2c4cb80f27de`.

`undocumented_contract_differences=0`.

## 29. Registry impact

Registry V2 contains qualified identity edges rather than the corrected protocol literals. Its exact hash is unchanged; no Registry successor is needed.

## 30. Closure impact

Closure V2 remains a 118-member fixed point with unchanged retention disposition and exact hash. No Closure successor is needed.

## 31. Security impact

`security_changed=false`; `RLS_changed=false`; `privilege_changed=false`; `transaction_ownership_changed=false`.

## 32. Lock decision

`new_lock_required=false`. V2.4 documents only locks/exclusion already present in frozen source.

## 33. ADR decision

`architecture_changed=false`; `ADR0019_required=false`. ADR-0018 is neither edited nor expanded.

## 34. Strict validation

On V2.4: physical type mismatches 0; nullability mismatches 0; enum/CHECK mismatches 0; unbound required fields 0; ambiguous bindings 0; conflicting bindings 0; reference cycles 0; deterministic preimage errors 0; execution-derived producer/freeze errors 0.

`strict_binding_type_reference_defects=0`.

## 35. Source-reachability validator

Permanent validator: `backend/foundation/phase31_4_5b_source_reachability_validator.py`. It validates exact predecessor/artifact hashes, 118/1664 universe, exact changeset, 13-row matrix, native protocol, identity flags, Outbox/Audit linkage, source hashes, writer/serialization predicates, plain-index classification, migration hashes, and fixed-digest inventory.

## 36. Negative tests

Seven focused tests reject wrong event/aggregate/source/payload/causation, wrong aggregate identity, wrong Outbox initialization, unapproved Event/Outbox/Audit identity, incomplete writer inventory, unresolved serialization, false unique-index/retry claims, dangling superseded protocol, and incomplete matrix/changeset. Result: 7/7 PASS.

## 37. Full offline regression

- V2.4 validator: PASS, 13 rows, 13 matrix PASS, 0 errors.
- V2.3 validator: PASS, 118 members, 1664 fields, 2 AgentRun rows.
- V2.2 strict validator: PASS, 118 members, 1664 fields, zero strict defects.
- V2.1 validator: PASS.
- V2 regression/Phase 31 Django suite: 192 tests, PASS; system check 0 issues.
- Phase 31.4.4 offline verifier: 155 tests, PASS; 367 Python files compiled; Django 4.2.22; dry-run migrations PASS; all attempt counters 0.
- Phase 31.4.3 offline verifier: 103 tests, PASS; all attempt counters 0.
- JSON parsing: 32 governance JSON files PASS.
- Python compilation of generator/validator/tests: PASS.
- Django `check`: PASS, 0 issues.
- `makemigrations --check --dry-run`: PASS, no changes detected.

An earlier raw `unittest discover` invocation ran 167 tests: 161 passed and six errored because that invocation omitted Django settings/package context. The authoritative rerun through `manage.py test` passed all 192 tests; this was invocation correction, not a source change.

## 38. Hashes

| New artifact | SHA-256 |
|---|---|
| V2.4 | `a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387` |
| changeset | `4204d022492de843d7f6763dfb05f3ce7ec5e166fc4c14de4b8b2c4cb80f27de` |
| validator | `10c8827ddd53fac92b44e4105bb61eec7f2114991309118bf3d3cc48c47e6308` |
| negative tests | `6672dc688e6748af292090178eb186aa90f0d32b309831265233bd247b4d8456` |
| generator | `934cbaf66895b9e68cc96a7c1c16bd9e2359d69ffe8de70871c52efe5c1e999a` |

## 39. Git hygiene

Only Phase 31.4.5B governance artifacts, generator, validator, tests, and this report were added. The known Sidebar whitespace warning and all unrelated dirty files were preserved. Final exact status/diff check is recorded after report creation in the handoff; report creation itself does not change protected runtime/domain sources.

## 40. Zero effects

```text
database effects=0
PostgreSQL effects=0
container effects=0
role effects=0
migration effects=0
producer implementation effects=0
producer installation effects=0
DomainEvent effects=0
Outbox effects=0
Audit effects=0
Opportunity effects=0
Effectiveness effects=0
LearningSignal effects=0
Proposal effects=0
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
database_attempts=0
network_attempts=0
container_attempts=0
lifecycle_attempts=0
resolver_invocations=0
```

Live criteria:

```text
PostgreSQL startup=NOT EXECUTED
DomainEvent writes=NOT EXECUTED
Outbox writes=NOT EXECUTED
Audit writes=NOT EXECUTED
race tests=NOT EXECUTED
lock acquisition=NOT EXECUTED
rollback fault injection=NOT EXECUTED
ambiguous commit test=NOT EXECUTED
producer implementation=NOT EXECUTED
```

## 41. Blocker accounting

```text
P1-V2_1-STRICT-PHYSICAL-TYPE-CONFLICTS=CLOSED
P1-V2_2-AGENT_RUN-START-EVENT-SERIALIZATION=CLOSED
P1-V2_2-AGENT_RUN-SOURCE-IDENTITY=CLOSED
P1-DOMAIN-EVENT-SOURCE-REACHABILITY=CLOSED
P1-DOMAIN-EVENT-SERIALIZATION=CLOSED
P1-CR2-SUPPORT-PRODUCER-ABSENT=OPEN_IMPLEMENTATION_ONLY
P1-CR2-INPUT-HASH-INVENTORY=OPEN_PENDING_IMPLEMENTATION
```

## 42. P0/P1

For this DomainEvent audit gate: `P0=0`; `P1=0`. The two explicitly deferred implementation/manifest items are not audit-gate P1 failures.

Required counts:

```text
total_declared_DomainEvent_rows=13
already_promoted_AgentRun_rows=2
remaining_rows_audited=11
all_declared_DomainEvent_rows_mapped=true
all_declared_DomainEvent_rows_source_reachable=true
all_same_aggregate_writer_inventories_complete=true
every_allocation_window_has_source_proven_serialization=true
unresolved_event_concurrency_contracts=0
unapproved_event_identity_substitutions=0
unapproved_outbox_identity_substitutions=0
unapproved_audit_identity_substitutions=0
all_downstream_references_resolved=true
undocumented_contract_differences=0
```

## 43. Residual risks

This phase proves frozen-source consistency, not live PostgreSQL locking, race behavior, rollback injection, or ambiguous-commit behavior. Those remain intentionally unexecuted. The future implementation must consume V2.4 and may not reintroduce V2.3’s superseded protocol bindings.

## 44. Final verdict

`PHASE 31.4.5B — PROMOTED — ALL 13 DECLARED DOMAIN EVENT ROWS SOURCE-REACHABLE; EVENT/OUTBOX/AUDIT IDENTITIES AUTHORIZED; SAME-AGGREGATE WRITER INVENTORIES COMPLETE; VERSION SERIALIZATION CONTRACTS CLOSED; PRODUCER IMPLEMENTATION MAY RESUME`

## 45. NEXT_CODEX_PROMPT

```text
# ISO SMART AI — PHASE 31.4.5 — RETRY 4
# FINAL SUPPORT PRODUCER + INSTALLER + CLEAN RETRY HARNESS + AUTHORITATIVE OPERATIONAL MANIFEST CLOSURE
# OFFLINE IMPLEMENTATION ONLY — DO NOT EXECUTE POSTGRESQL — NO PHASE 32

Work exclusively in /home/felipe/proyectos/isosmart.

Authorized predecessor:
PHASE 31.4.5B — PROMOTED — ALL 13 DECLARED DOMAIN EVENT ROWS SOURCE-REACHABLE; EVENT/OUTBOX/AUDIT IDENTITIES AUTHORIZED; SAME-AGGREGATE WRITER INVENTORIES COMPLETE; VERSION SERIALIZATION CONTRACTS CLOSED; PRODUCER IMPLEMENTATION MAY RESUME

Authoritative operational contract:
docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json

Required V2.4 SHA-256:
a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387

Required predecessor evidence:
- docs/transformation/PHASE31_4_5B_REMAINING_DOMAIN_EVENT_SOURCE_REACHABILITY_AND_SERIALIZATION_AUDIT_REPORT.md
- docs/governance/evidence/PHASE31_4_5B_V2_3_TO_V2_4_CHANGESET_V1.json
- backend/foundation/phase31_4_5b_source_reachability_validator.py
- ADR-0017 and ADR-0018, unchanged
- Registry V2 SHA-256 58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb
- Closure V2 SHA-256 80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425

Entry requirements:
- verify V2.4 and every predecessor/source/migration/protected hash;
- require 118 members, 13 DomainEvent rows, 13/13 source matrix PASS;
- require unresolved_event_concurrency_contracts=0;
- require all three unapproved identity substitution counts=0;
- require migration 0024 absent and migrations 0001–0023 unchanged;
- record initial git status and diff check; preserve unrelated work and the known Sidebar line-28 warning.

Hard boundary:
- do not start PostgreSQL, Podman, or Docker;
- do not create a database or roles;
- do not apply migrations or execute lifecycle operations;
- do not invoke RuntimeAdoption or the resolver;
- do not call external systems;
- do not deploy and do not begin Phase 32;
- database/network/container/lifecycle/resolver attempts must remain zero.

Implement and freeze exactly:
1. the parameterless, experiment-locked support producer for the full V2.4 support path;
2. the SQL/security/RLS installer and reversible teardown for its ephemeral roles/policies/functions, without migration 0024;
3. the Clean Retry execution harness, but do not run it against PostgreSQL in this phase;
4. the operational manifest verifier;
5. offline implementation tests including adversarial security, identity, protocol, serialization, replay, rollback-plan, and input drift cases;
6. the complete operational input manifest containing every code, SQL, contract, policy, Registry, Closure, source, migration, installer, producer, harness, verifier, and configuration input;
7. the external manifest SHA-256 and a verifier that fails closed on missing, extra, duplicate, reordered where order matters, or changed inputs.

The producer must:
- consume V2.4, never V2.3 operational bindings;
- create only the declared 118-member future universe;
- use native operations/protocol and existing ADR-0018 identity exceptions exactly;
- retain native Audit UUIDv7 outputs before downstream use;
- preserve per-operation transaction ownership and source-proven version serialization;
- use existing locks only; add no lock or identity exception;
- maintain Event/Outbox/Audit combinations exactly as native source specifies;
- perform authorized read-only retention rereads separately from allocation;
- fail closed on authority, tenant, RLS, identity, hash, payload, source, writer-inventory, or manifest drift;
- keep Application/Publication/Activation/RuntimeAdoption inert and unexecuted.

Installer requirements:
- exact NOLOGIN owner and LOGIN executor attributes from the frozen contract;
- no superuser, inheritance, bypass-RLS, generic DML, dynamic SQL, PUBLIC EXECUTE, role escalation, or ownership bypass;
- exact fixed search paths and least privilege;
- exact fixture-tenant RLS policies with cross-tenant denial;
- idempotent install verification and complete teardown verification;
- no modification of migrations 0001–0023 and no migration 0024.

Harness requirements:
- parameterless and experiment-locked;
- verifies empty/precondition state without creating PostgreSQL here;
- verifies exact 118-member output, V2.4 bindings, retention graph, Registry/Closure fixed point, and zero prohibited effects;
- includes planned failure points, rollback assertions, replay/conflict behavior, ambiguous-commit reconciliation only where frozen source supports it, and race/lock cases for later live execution;
- never fabricates unsupported retry, identity, lock, Audit, Event, or Outbox behavior.

Required offline validation:
- V2.4, V2.3, V2.2, V2.1, and V2 validators/regressions;
- producer/installer/harness/manifest unit tests and negative tests;
- all DomainEvent matrix/writer/serialization/identity/downstream tests;
- Registry/Closure and fixed-hash audit;
- JSON parsing and Python compilation;
- Django 4.2.22 system check;
- makemigrations --check --dry-run;
- migration/source/protected hashes;
- git diff --check and final git status.

Create:
docs/transformation/PHASE31_4_5_RETRY4_FINAL_SUPPORT_PRODUCER_INSTALLER_HARNESS_AND_OPERATIONAL_MANIFEST_CLOSURE_REPORT.md

The report must include exact implementation inventory, trust/security model, producer call graph, transaction boundaries, manifest contents and external SHA-256, offline tests, hashes, Git hygiene, zero effects, blockers, residual risks, and exactly one self-contained prompt for a separate PostgreSQL 18.6 Clean Retry execution phase. Do not advance Phase 32.

Promotion requires both blockers closed:
P1-CR2-SUPPORT-PRODUCER-ABSENT=CLOSED
P1-CR2-INPUT-HASH-INVENTORY=CLOSED

If any implementation, manifest, security, identity, serialization, or offline-regression defect remains, emit PHASE 31.4.5 — RETRY 4 — NOT PROMOTED with exact blockers. Otherwise emit the exact Retry 4 promotion verdict defined by the implementation closure report, while keeping PostgreSQL execution explicitly NOT EXECUTED.
```
