# Phase 31.4 V2.5 diagnostic state-machine remediation V1

## Verdict

`DIAGNOSTIC_STATE_MACHINE_CODE_PASS / INTEGRITY_RECONCILIATION_REQUIRED`

## Root cause

Attempt 3 reached `POSTGRES_READY` for both PostgreSQL 18.6 databases and then failed with `INVALID_STATE_TRANSITION`. The formal evidence graph already allowed `READY -> PRECREATION_RUNNING`, but `DIAGNOSTIC_TRANSITIONS` copied that graph and replaced all successors of `READY` with only `COMPLETED` and `FAILED`. The operational diagnostic calls `DisposableEvidenceRunner.run_evidence`, so its legitimate PRECREATION entry was rejected by the diagnostic-only override.

## State model source

- State enum, allowlists, validator, manifest history and runner callers: `backend/foundation/phase31_4_v2_5_disposable_runner.py`.
- Diagnostic orchestration caller: `docs/governance/tools/run_phase31_4_v2_5_operational_diagnostic.py`.
- Formal and diagnostic operational paths both use `DisposableEvidenceRunner.run_evidence`.

## Rejected transition

`READY -> PRECREATION_RUNNING`

Old diagnostic successors from `READY`:

`COMPLETED | FAILED`

## Corrected transition

Corrected diagnostic successors from `READY`:

`PRECREATION_RUNNING | COMPLETED | FAILED`

The explicit allowlist remains intact. `COMPLETED` is retained only for the existing minimal environment diagnostic's intentional stop at READY; the operational diagnostic now follows the same PRECREATION and Stage EXT transitions as formal evidence.

The verified success order is:

`AUTHORIZED -> ALLOCATING -> RESOURCES_ALLOCATED -> BOOTSTRAPPING -> READY -> PRECREATION_RUNNING -> PRECREATION_PASS -> STAGE_EXT_RUNNING -> STAGE_EXT_PASS -> COMPLETED -> TEARDOWN_COMPLETE`

## Preconditions

`READY -> PRECREATION_RUNNING` now fails closed unless the atomic resource manifest proves all of the following:

- allocation succeeded and both `adminapps` and `isosmart` resources exist;
- host ports and database names are complete and unique;
- each volume and network is `CREATED`;
- each container is `RUNNING`;
- each observed server is PostgreSQL 18.6;
- each PostgreSQL status is `READY`;
- each real connection is `PASS` and `SELECT 1` returned `1`;
- the on-disk atomic manifest is at `READY` with the current revision and resource set.

For the intended two-role run, these checks apply independently to `adminapps` and `isosmart`.

## PRECREATION transitions

The explicit graph permits exactly:

- `READY -> PRECREATION_RUNNING`;
- `PRECREATION_RUNNING -> PRECREATION_PASS` on PASS;
- `PRECREATION_RUNNING -> FAILED` on failure.

PRECREATION failure does not enter Stage EXT. Replayed `PRECREATION_PASS` and PRECREATION before READY remain invalid.

## Stage EXT transition

`PRECREATION_PASS -> STAGE_EXT_RUNNING` is statically valid. Stage EXT before `PRECREATION_PASS` remains invalid. No later Stage EXT behavior was changed.

## Failure transitions

`READY`, `PRECREATION_RUNNING`, `PRECREATION_PASS`, and `STAGE_EXT_RUNNING` can each reach `FAILED`. No failure state was loosened or bypassed.

## Cleanup transitions

Both successful and failed operational diagnostic paths were exercised offline with fakes:

- success reaches `COMPLETED -> TEARDOWN_COMPLETE`;
- PRECREATION failure reaches `PRECREATION_RUNNING -> FAILED -> TEARDOWN_COMPLETE`;
- Stage EXT is not called after PRECREATION failure.

Resource ownership and cleanup selection rules were not changed.

## Manifest/state-history behavior

Every transition continues to be appended before the atomic manifest write. Each entry now persists `from`, `to`, timestamp (`at`), `reason`, `run_id`, `run_slug`, `execution_kind`, and `validation_attempt`, in addition to its sequence. There are no invisible state mutations.

## Tests added

Coverage now includes:

- valid `READY -> PRECREATION_RUNNING`;
- valid `PRECREATION_RUNNING -> PRECREATION_PASS`;
- valid `PRECREATION_PASS -> STAGE_EXT_RUNNING`;
- failure from `PRECREATION_RUNNING`, `PRECREATION_PASS`, and `STAGE_EXT_RUNNING` through teardown;
- invalid PRECREATION before READY;
- invalid Stage EXT before PRECREATION PASS;
- invalid terminal PRECREATION replay;
- rejection of premature or non-durable READY;
- ordered manifest history with run/diagnostic identity;
- the same protected operational path in diagnostic and formal modes;
- diagnostic PRECREATION failure cleanup and Stage EXT suppression.

## Focused tests

- Runner plus live executor: **33/33 PASS**.
- Runner, live executor and PRECREATION: **41/43 PASS**, with exactly 2 expected PRECREATION failures caused by deliberate V7 protected-source drift.
- Integrity generation guards: **10/12 PASS**, with exactly 2 expected errors identifying the same runner drift.

No Podman, PostgreSQL, service, or live diagnostic process was invoked; the runner tests use in-memory fakes.

## Full regression

Backend regression: **558 total; 552 pass; 2 failures; 4 errors**.

All six non-passing results derive from the required protected-source drift:

- three direct V7 verification failures;
- one operational-manifest successor check that wraps V7 verification;
- two PRECREATION tests that correctly fail closed when V7 verification detects the drift.

Unrelated functional failures: **0**.

## Files modified

- `backend/foundation/phase31_4_v2_5_disposable_runner.py`
- `backend/foundation/test_phase31_4_v2_5_disposable_runner.py`
- `PHASE31_4_V2_5_DIAGNOSTIC_STATE_MACHINE_REMEDIATION_V1.json`
- `PHASE31_4_V2_5_DIAGNOSTIC_STATE_MACHINE_REMEDIATION_REPORT.md`

## V7 integrity impact

V7 remains unchanged at SHA-256 `44b161084700ae3892cb3e49d054de35ef1403409c69eeae9d370b46565d2ca8`. The protected runner source necessarily changed, so the prior `28/28 PASS` generation now correctly reports drift. V7 was not updated and integrity enforcement was not weakened.

## Live diagnostic executed

`NO`

## Retry 20 executed

`NO`

No formal Retry 20 authorization was created.

## Stage EXT

`LIVE_REVALIDATION_PENDING / last diagnostic 0/6`

## Phase 31.5

`EXECUTION_HELD`

## Exact next step

`Perform a V8 successor integrity reconciliation before opening a new operational diagnostic cycle.`
