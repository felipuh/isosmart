# Phase 31.4 — Clean Retry 2 — complete retained synthetic creation-through-activation PostgreSQL 18.6 POC

## 1. Verdict

`PHASE 31.4 — CLEAN RETRY 2 — NOT PROMOTED`

The execution stopped before PostgreSQL creation. Two P1 blockers prevent conformance execution without redesigning or inventing missing V2 authority:

1. The package does not publish expected SHA-256 values for every mandatory operational V2 input, so `V2_input_integrity=true` cannot be proved.
2. The approved supporting fixture producer is specified but has no installable executable implementation in the repository.

## 2. Entry Phase 31.4.4

Accepted entry claim: `PHASE 31.4.4 — PROMOTED — ROW-LEVEL EXECUTION-READY V2 CONTRACT COMPLETE; FUTURE CLEAN PHASE 31.4 RETRY ELIGIBLE`.

The entry authorized conformance execution only. It did not authorize redesign of V2 or creation of a missing producer.

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

The exact initial `git diff --check` was:

```text
frontend/src/components/Layout/Sidebar.jsx:28: trailing whitespace.
+    { name: t('navigation.risks'), path: '/risks', icon: AlertTriangle, group: 'control' }, 
```

The pre-existing whitespace was preserved. No reset, stash, clean, stage, commit, normalization, or sibling-repository access occurred.

## 4. V2 hashes

Published expected hashes that matched observed bytes:

| Input | SHA-256 | Result |
|---|---|---|
| Execution Contract V2 | `962ec0b393b49c3c0a2894e32bb9a3246cbf7793cfd600391248634bee56f70b` | PASS |
| Registry V2 | `58b8278cbe05b0b5056e058bb3db1eecfc4d576cbef3dc5383c5e894900730fb` | PASS |
| Expected Closure V2 | `80eb1e7f8e857712aa49bcca98f3d27da2b525ba98df16fa34651cf8254cc425` | PASS |
| ADR-0017 | `82501ef34edc6d7e76e0971d3d2607c58f229a1dd4dd26696dd227fb7e994edb` | PASS |
| Migration 0022 | `afefd7100a18e5c7324efaeb1af656225b309fd86f08673a8742f7f9f6c2e618` | PASS |

Observed hashes without a published expected value in the Phase 31.4.4 package:

| Mandatory input | Observed SHA-256 | Result |
|---|---|---|
| Phase 31.4.4 report | `29ed29048545d3d1cffa02c80edfb9faa5f2c3e58a62d2efe3189f43461dd1b7` | UNVERIFIABLE |
| ADR-0018 | `f9f6272c72e433241f66e44884b53dc804a667b32950c8ab098df6473ecf6089` | UNVERIFIABLE |
| Product Policy V2 | `bf92aa4aafdaa99e27f90fc3c2766cd3a8fa85214f26a4fe7ffbbd1a7397cad2` | UNVERIFIABLE |
| Supporting producer contract | `9ca5530bf24e0dc90b004b0b88fa86c344646e5991a5c65659eaae3dae2e795e` | UNVERIFIABLE |
| Offline validation evidence | `1517a4c4fe9112802d46da6073c852d5ad3cfb10bc25e5819dfc5615358b2b05` | UNVERIFIABLE |
| Mandatory reading ledger | `90ef2be1190fc86067c274053428904341cf41748ff4734fa4a6cdd4c9c65ae2` | UNVERIFIABLE |

Observed hashes were not promoted to expected hashes. `V2_input_integrity=false` because the required comparison cannot be completed from a declared frozen inventory.

## 5. Mandatory reading

`mandatory_reading_complete=false`. AGENTS.md, the Phase 31.4.4 gate report, ADR-0018, Product Policy V2, supporting producer contract, offline evidence, acceptance-test/verifier entry points, and the relevant integrity inventories were read. Execution stopped when the blocking missing-hash inventory and missing-producer conditions were confirmed. Unread items are `NOT EXECUTED`, never PASS.

## 6. PostgreSQL environment

NOT CREATED. PostgreSQL/container/database/volume/role creation attempts: 0.

## 7. Render profile

NOT EXECUTED. No server existed to verify PostgreSQL 18.6, encoding, locale, collation, timezone, DateStyle, IntervalStyle, standard strings, or extra-float-digits.

## 8. Migrations

All 23 individual frozen migration file hashes match the declared Phase 31.4.3/31.4.4 inventory. `migration_0024_absent=true`. Applying migrations: NOT EXECUTED.

## 9. Catalog constraints

Live catalog verification: NOT EXECUTED.

## 10. Row universe

The V2 design declares 118 rows across 53 table/artifact indexes. Operational conformance: NOT EXECUTED.

## 11. Identities

Design taxonomy observed. Live identity production and collision checks: NOT EXECUTED.

## 12. Supporting producer

BLOCKED. Repository search found the identifier `phase31.4.4-exact-support-producer/v1` only in the machine-contract generator and declarative artifacts. No installable SQL/Python producer, Phase 31.4 execution harness, or exact role/policy bootstrap exists. Creating one here would redesign/implement a missing producer during conformance execution, expressly forbidden by the entry contract.

## 13. Producer security

NOT EXECUTED. The owner/executor roles were not created.

## 14. Grants

NOT EXECUTED.

## 15. RLS

NOT EXECUTED.

## 16. Transaction composition

NOT EXECUTED.

## 17. Synthetic catalog

NOT EXECUTED.

## 18. AgentRun

NOT EXECUTED.

## 19. AgentRunInput

NOT EXECUTED.

## 20. Recommendation provenance

NOT EXECUTED.

## 21. AgentDecision

NOT EXECUTED.

## 22. ActionPlan

NOT EXECUTED.

## 23. DryRun

NOT EXECUTED.

## 24. Approval

NOT EXECUTED.

## 25. ExecutionAuthorization

NOT EXECUTED.

## 26. Controlled execution

NOT EXECUTED. External business effects: 0.

## 27. Receipt

NOT EXECUTED.

## 28. Evidence

NOT EXECUTED.

## 29. Effectiveness

NOT EXECUTED.

## 30. LearningSignal

NOT EXECUTED. Automatic learning effects: 0.

## 31. ProposalSignal

NOT EXECUTED.

## 32. Freeze 1.5

NOT EXECUTED.

## 33. Root admission

NOT EXECUTED.

## 34. Root creation

NOT EXECUTED.

## 35. Root publication

NOT EXECUTED.

## 36. Dual target reread

NOT EXECUTED.

## 37. B1 operational result

`B1_operationally_verified=false`; NOT EXECUTED.

## 38. Proposal/Delta

NOT EXECUTED.

## 39. Review

NOT EXECUTED.

## 40. Decision

NOT EXECUTED.

## 41. Authorization

NOT EXECUTED.

## 42. ADR-0017 parity

NOT EXECUTED. ADR-0017 bytes match the published expected hash.

## 43. Application

NOT EXECUTED.

## 44. Publication governed admission

NOT EXECUTED.

## 45. Native Publication

NOT EXECUTED.

## 46. Publication replay/concurrency

NOT EXECUTED.

## 47. Checkpoint

NOT EXECUTED.

## 48. B2

`B2_verified=false`; NOT EXECUTED.

## 49. B3

`B3_verified=false`; NOT EXECUTED.

## 50. Publication closure

`publication_closure_complete=false`; NOT EXECUTED.

## 51. Export/live comparison

`publication_export_matches_live=false`; NOT EXECUTED.

## 52. Publication eligibility

`publication_eligible_for_activation=false`; NOT EXECUTED.

## 53. Activation governed admission

NOT EXECUTED.

## 54. Native Activation

NOT EXECUTED.

## 55. Activation replay/concurrency

NOT EXECUTED.

## 56. Rollback

NOT EXECUTED. No lifecycle rows were written.

## 57. TOCTOU

NOT EXECUTED.

## 58. Hostile tests

NOT EXECUTED.

## 59. Ambiguous commits

NOT EXECUTED. No commit was attempted.

## 60. Complete closure

`retention_closure_complete=false`; NOT EXECUTED.

## 61. RuntimeAdoption zero

No database was created and no resolver was called. RuntimeAdoption attempts/effects: 0.

## 62. Runtime invariance

No runtime file was intentionally modified by this retry. Full protected-file before/after runtime proof: NOT EXECUTED because execution stopped at precreation integrity.

## 63. Learning invariance

Automatic-learning mutation attempts/effects: 0.

## 64. Normative invariance

Normative mutation/claim effects: 0.

## 65. Pre-teardown state

`CREATED=false`, `APPLICATION_GOVERNED=false`, `PUBLISHED=false`, `ACTIVATED=false`, `RUNTIME_ADOPTED=false`, `RUNTIME_EFFECTIVE=false`.

## 66. Teardown authorization

Not applicable and not authorized: the required lifecycle predicates are false.

## 67. Teardown

No teardown was needed because no database, container, volume, functions, policies, roles, grants, credentials, or temporary execution environment were created.

## 68. Producer/adapter removal

No producer or adapter was installed. Removal: NOT APPLICABLE.

## 69. Post-teardown verification

NOT EXECUTED. The requested successful post-teardown state is impossible because creation-through-activation did not occur.

## 70. Tamper-negative tests

NOT EXECUTED. No retained live execution package existed to tamper.

## 71. Evidence hashes

The companion detached SHA-256 ledger hashes this report and the precreation blocker evidence. No execution-material canonical hashes exist.

## 72. Foundation/backend regression

NOT EXECUTED. Conformance stopped before database creation; regression results from Phase 31.4.4 were not reused as operational evidence.

## 73. Migration/source/protected hashes

- 23/23 migration file hashes matched; mismatches: 0.
- 223/223 previously protected file hashes matched; mismatches: 0.
- Migration 0024 is absent.
- The declared aggregate migration-set value remains `cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc`; individual file verification passed.
- Required new V2 control-document expected hashes are incomplete, which blocks the new operational input inventory.

## 74. Git hygiene

Only this append-only report and its append-only blocker evidence/ledger were created. The known Sidebar whitespace and all unrelated work were preserved.

## 75. Zero effects

```text
production effects=0
staging effects=0
shared DB effects=0
real AdminApps effects=0
MedSupplier effects=0
external API effects=0
deployment effects=0
RuntimeAdoption effects=0
runtime cutover effects=0
normative effects=0
automatic learning effects=0
external business effects=0
Phase29 reconstruction effects=0
PostgreSQL creation effects=0
lifecycle write effects=0
```

## 76. P0/P1

P0=0; P1=2.

- `P1-CR2-INPUT-HASH-INVENTORY`: mandatory operational V2 inputs lack published expected hashes.
- `P1-CR2-SUPPORT-PRODUCER-ABSENT`: the exact approved supporting producer has no executable implementation.

## 77. Residual risks

Execution remains unsafe until an offline successor gate publishes a complete detached expected-hash inventory and promotes the exact bounded producer implementation, including its roles, policies, grants, functions, transaction boundaries, teardown, and tests. Deriving either during the clean retry would erase the distinction between design authorization and conformance execution.

## 78. Final verdict

`PHASE 31.4 — CLEAN RETRY 2 — NOT PROMOTED`

No Phase 32 advancement is permitted.

## 79. Exactly one NEXT_CODEX_PROMPT

```text
PHASE 31.4.5 — COMPLETE V2 OPERATIONAL INPUT HASH INVENTORY + EXACT SUPPORTING PRODUCER IMPLEMENTATION CLOSURE GATE — OFFLINE DESIGN/IMPLEMENTATION ONLY

Work exclusively in /home/felipe/proyectos/isosmart. Preserve all unrelated work and the known frontend/src/components/Layout/Sidebar.jsx:28 trailing whitespace. Do not access sibling repositories. Before discovery, record git status --short and git diff --check.

Use the Phase 31.4 Clean Retry 2 precreation blocker evidence and report as entry. Do not create PostgreSQL, execute lifecycle writes, invoke RuntimeAdoption or its resolver, contact external systems, or advance to Phase 32.

Close exactly two P1 blockers. First, publish a detached, authoritative expected SHA-256 inventory covering every operational V2 input required by Clean Retry 2, including the Phase 31.4.4 report, ADR-0018, Product Policy V2, Execution Contract V2, Registry V2, Expected Closure V2, supporting producer contract, all governed-admission/evidence/checkpoint schemas, offline validation evidence, mandatory reading ledger, migrations 0001–0023, authoritative source fixture, and every promoted implementation file used by execution. Prove all expected/observed values and define the inventory canonicalization without deriving expected values during the later retry.

Second, implement and promote the exact parameterless phase31.4.4-exact-support-producer/v1 and the complete Phase 31.4 Clean Retry 2 execution harness specified by V2. The implementation must be exact-row-universe-bound, contain no generic table/model/UUID/actor/operation/JSON/target inputs, install only the approved NOLOGIN owner and LOGIN executor with NOSUPERUSER/NOINHERIT/NOBYPASSRLS, fixed pg_catalog search paths, fully qualified objects, no dynamic SQL, revoked PUBLIC execution, exact grants and forced tenant RLS policies, per-operation trusted-context transactions, immediate precommit revalidation, hostile/rollback/concurrency/ambiguous-commit tests, complete retention/export/live comparison, conditional teardown, and offline tamper verification. Preserve migrations 0001–0023 and keep 0024 absent.

Provide complete semantic reading evidence, executable tests that fail when either blocker recurs, byte hashes for every new artifact, P0/P1 accounting, zero-effect proof, a promotion verdict only if both blockers close, and exactly one self-contained continuation back to Phase 31.4 Clean Retry 3. Do not execute the POC in Phase 31.4.5.
```

## State table

| Predicate | State |
|---|---|
| V2 input integrity | false — incomplete expected-hash inventory |
| PostgreSQL 18.6 created | false |
| migration 0024 absent | true |
| supporting fixture verified | false — executable producer absent |
| B1 operationally verified | false |
| Application verified | false |
| Publication verified | false |
| B2/B3 verified | false/false |
| Publication closure/export match | false/false |
| Activation verified | false |
| Retention closure/export match | false/false |
| RuntimeAdoption | false |
| RuntimeEffective | false |
| database reconstructed | false |
| P0/P1 | 0/2 |
| Final | NOT PROMOTED |
