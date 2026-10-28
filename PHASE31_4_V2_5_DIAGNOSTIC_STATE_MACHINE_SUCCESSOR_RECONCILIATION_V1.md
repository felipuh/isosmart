# Phase 31.4 V2.5 diagnostic state-machine successor reconciliation V1

## Verdict

`DIAGNOSTIC_STATE_MACHINE_SUCCESSOR_RECONCILIATION_PASS`

## V7

`docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V7.json`

SHA-256: `44b161084700ae3892cb3e49d054de35ef1403409c69eeae9d370b46565d2ca8`

V7 is preserved and unchanged. V1–V7, V2.4, the provenance discontinuity, Retry 16–19 evidence, all prior diagnostic cycles, and the superseded V5 Retry 20 authorization remain historical records.

## V8

`docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V8.json`

SHA-256: `ed7bed0108e790c93e0c40625b215dde02ae25566b2397533b11b6aae7040946`

V8 is a verified successor of V7 for the explicitly reviewed diagnostic state-machine remediation.

## Protected sources

- V7: 28.
- V8: 28.
- Unchanged: 26.
- Modified: 2.
- New, removed, missing, unexpected: 0.

The complete 28-source SHA-256 map is recorded in V8. A byte-for-byte recheck after generation found no mismatch.

## Modified protected sources

- `backend/foundation/phase31_4_v2_5_disposable_runner.py`: `LEGITIMATE_DIAGNOSTIC_STATE_MACHINE_EVOLUTION`; V7 `5d9a9cb42a28db33bc2df8c70652a98682eac90cc2b68c5c36d14b1e7dff40d9` → V8 `376626b5a06d066f2c1f82f5b22dea136071fdd9a5f37fb732daa39101874fc5`.
- `backend/foundation/phase31_4_integrity_generations.py`: `GOVERNANCE_ARTIFACT`; V7 `c8ec3af921a13a02fcd983762623a29652a0898923f3add82b2b1a51c334c15b` → V8 `f6ceb77e72d2f321f56379b6fe4c6c59444fba72f5aa21349623fed9f33f5684`.

## New protected sources

None.

## Unexpected drift

None. Against V7's authoritative protected-source map, only the runner changed before reconciliation. The guard change is the required V8 governance promotion. Test files are `TEST_ONLY`; the remediation, V8, and reconciliation records are `GOVERNANCE_ARTIFACT`; every other preexisting worktree difference is `UNRELATED_PREEXISTING`.

## Corrected transition graph

The historical defect replaced the diagnostic `READY` exits with only `COMPLETED | FAILED`, even though the operational diagnostic uses `run_evidence()` and the formal graph already allowed PRECREATION.

The corrected diagnostic allowlist is:

`READY -> PRECREATION_RUNNING | COMPLETED | FAILED`

The operational success order remains:

`READY -> PRECREATION_RUNNING -> PRECREATION_PASS -> STAGE_EXT_RUNNING`

There is no arbitrary forward transition, any-state transition, PRECREATION skip, early Stage EXT, terminal replay, or cleanup bypass.

## READY invariants

PRECREATION requires successful allocation; persisted `adminapps` and `isosmart` resources; complete unique host ports and database identities; created volumes/networks; running containers; PostgreSQL 18.6; readiness and connectivity PASS; `SELECT 1 == 1`; and an atomic on-disk `READY` manifest matching the in-memory revision and resources.

## PRECREATION ordering

Only `READY -> PRECREATION_RUNNING -> PRECREATION_PASS` advances. A failure enters `FAILED` and Stage EXT is not called.

## Stage EXT ordering

Only `PRECREATION_PASS -> STAGE_EXT_RUNNING` enters Stage EXT. Failure goes to `FAILED`; it cannot advance.

## Minimal diagnostic stop semantics

`READY -> COMPLETED` is reachable only through `run_diagnostic()` after it verifies `RUNNER_ENVIRONMENT_DIAGNOSTIC`. Operational diagnostics and formal evidence/retry paths use `run_evidence()` and must traverse PRECREATION and Stage EXT. It is not an evidence bypass.

## Manifest history

Every transition records `from`, `to`, timestamp (`at`), `reason`, run ID, run slug, execution kind, and validation attempt. Persistence writes a temporary file, fsyncs it, atomically replaces the manifest, and fsyncs the parent directory.

## Migrations

V2.4 `23/23 PASS`; V2.5 `24/24 PASS`; pending `0`; new `0`; fake `0`; manual patches `0`; `makemigrations --check --dry-run = PASS` (`No changes detected`).

## Focused tests

`112/112 PASS`; failures `0`; errors `0`.

## Integrity tests

`13/13 PASS`; failures `0`; errors `0`. V7 identity is pinned, V1–V7 remain historical, V8 validates current bytes, and future runner drift fails closed.

## Full backend regression

`559/559 PASS`; failures `0`; errors `0`. The previous six V7-drift failures/errors are resolved without weakening integrity tests.

## Source checkpoint P0/P1

`P0=0`; `P1=0`.

## Operational readiness

`NOT_READY`

Source-integrity PASS does not establish operational PASS. Stage EXT remains `LIVE_REVALIDATION_PENDING`.

## Last diagnostic

`0/6 / 3 of 3 exhausted`

## Retry 20 authorization

`NONE`

## Retry 20 executed

`NO`

## Phase 31.5

`EXECUTION_HELD`

## New diagnostic cycle readiness

`READY_FOR_NEW_V8_OPERATIONAL_DIAGNOSTIC_CYCLE`

## Exact next step

Authorize one separately bounded V8 operational diagnostic cycle.
