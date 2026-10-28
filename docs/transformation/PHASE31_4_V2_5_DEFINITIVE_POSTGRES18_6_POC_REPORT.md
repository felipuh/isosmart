# Phase 31.4 Clean Retry 3 — NOT_PROMOTED

## Part A — source audit and V2.5 decision

Stage A stopped on a newly demonstrated native identity and revision contradiction. The machine-readable proof is [PHASE31_4_V2_5_NATIVE_IDENTITY_CONTRADICTION_V1.json](../governance/evidence/PHASE31_4_V2_5_NATIVE_IDENTITY_CONTRADICTION_V1.json). Historical V2.4 remains unchanged at SHA-256 `a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387`.

The four reported ActionPlan defects are confirmed: invalid string preconditions, A0 instead of A3, lowercase target type, and a descriptive non-UUID target ID. The audit also found invalid controlled-path parameters and dry-run material, A0 AgentRun/Decision/Authorization ceilings, an A0 AgentDefinition maximum, a missing Decision recommendation link, and an Opportunity lineage that differs from the native initial identity. These require a source-derived successor; V2.4 is not an operational contract.

Three independent identity/revision conflicts prevent certifying the requested exact live graph:

1. `RiskOpportunityObjectiveCommandService.create_opportunity` calls `_create`, which generates `entity_id = uuid4()` and stores **both** `id` and `lineage_id` as that ID (`backend/foundation/risk_objective.py:102-123,209-217`). The V2.4 initial Opportunity binds an exact UUID for `id` and a *different* UUIDv5 value for `lineage_id`. The native API has no ID input.
2. `ActionPreparationService.prepare_action_plan` validates the preconditions and then stores `id=uuid4()` (`backend/foundation/action_authorization.py:199-260`). It has no caller-supplied ActionPlan ID. The contract requires the exact member `qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a`, including event/outbox references to that member.
3. Migration 0015 calls the controlled transition with `uuidv7()` and inserts the successor Opportunity with the **prior lineage, revision + 1, and prior ID as predecessor** (`backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py:68-100,290-314`). The frozen controlled output member binds an unrelated exact UUID, a different lineage, revision 1, and a null predecessor.

These conflicts remain after correcting preconditions, autonomy, target type, target ID, and dry-run material. The required exact 118-member live comparison and offline exact target UUID cannot be established with these native APIs and frozen identities. Changing to captured native output identities would require a revised member identity/reference graph and a different offline identity proof. Supplying fixed IDs to native services would change native product interfaces. Raw row insertion or patching service behavior would violate the explicit native-validation requirement. A complete V2.5 authorization, Registry/Closure successor, and operational manifest were therefore **not** frozen.

## Part B — runtime

The requested production factory, 29 concrete operation bindings, transaction adapter, authority integration, and 33 handlers were not certified. The existing harness still needs runtime registration. No runtime claim or implementation-freeze flag was issued because Stage A did not satisfy `known offline P1 defects remained`.

## Part C — PostgreSQL 18.6

No PostgreSQL environment was created, no migration was applied, and `run_clean_retry_3()` was not called. The Stage B authorization predicate failed in Stage A. Live security, ActionPlan persistence, controlled execution, 33 phases, 118/1664 comparison, export, closure, and teardown are **unverified**. No production, staging, shared development, AdminApps, or MedSupplier system was touched.

## Measured gate

| Check | Result |
| --- | --- |
| V2.4 historical SHA-256 | PASS |
| Members / fields in historical fixture | 118 / 1664 |
| Newly demonstrated source contradictions | 3 |
| Complete offline P0/P1 | Not run; at least 3 P1 source conflicts identified |
| V2.5 operational contract | Not authorized |
| Live POC | Not started |
| Promotion | **NOT_PROMOTED** |

The gate can only be reopened by resolving the native identity and revision graph under an explicitly accepted successor contract. The present exact-identity requirements cannot all be true at once.
