# PHASE 31.4 V2.5 Operational Live Executor Remediation

## Verdict

`OPERATIONAL_LIVE_EXECUTOR_FAIL`

The code blockers B1/B2/B3 are remediated and focused tests pass, but the mandatory live diagnostic exhausted 3/3 attempts before reaching database allocation. A code-pass verdict is therefore not supportable.

## B1 evidence entrypoint

The runner CLI now exposes `evidence`. It constructs the operational adapter and invokes `run_evidence()` with the protected PRECREATION callback and the live Stage EXT callback. Stage EXT creates the `CaptureBundle`, calls `build_v25_runtime()`, and formal evidence mode invokes `run_clean_retry()`.

## B2 synthetic/default removal

Operational modes have no default success implementation. They reject `test_only` adapters and require real migration state, role/session verification, PID > 0, HTTP readiness, outbox/delivery/ingress evidence, and independent readbacks. Test fakes are admitted only with explicit `mode="test"`.

## B3 superseding authorization

The runner selects one exact authorization artifact and rejects an artifact linked as superseded. An additive `AUTHORIZATION_INDEX.json` marks the preserved V5 artifact `SUPERSEDED / UNCONSUMED / DO_NOT_CONSUME`. The original V5 file remains byte-identical.

## Operational runner command

`python -m foundation.phase31_4_v2_5_disposable_runner evidence --repository-root ... --run-id ... --authorization ... --authorization-sha256 ... --current-integrity-generation ... --integrity-sha256 ... --evidence-root ...`

## Live adapters

`SubprocessOperationalAdapter` retains commands, timestamps and logs; starts real child processes; performs HTTP readiness; and exposes explicit AdminApps bootstrap, ISO Smart bootstrap, authority, delivery, projection, Organization and Process operations.

## DB bootstrap

Implemented fail-closed. Diagnostic: not reached.

## Migrations

Both Django migration commands and zero-pending verification are implemented. Diagnostic: not reached.

## PostgreSQL roles

Required login/owner roles and session settings are created and independently queried. Diagnostic: not reached.

## AdminApps service

Dynamic port, real PID, readiness URL and retained combined log are mandatory. Diagnostic: not reached.

## ISO Smart service

Dynamic port, real PID, readiness URL and retained combined log are mandatory. Diagnostic: not reached.

## Event delivery

Outbox ID, delivery result, ingress receipt and both returned projection IDs are mandatory. Diagnostic: not reached.

## Projection readbacks

TenantProjection and UserProjection use separate adapter calls and DB/service reads. Diagnostic: not reached.

## PRECREATION

The live executor calls the existing `verify_precreation_integrity`/`PrecreationIntegrityExecutor` path. V6 now fails closed on material source drift, as required.

## Stage EXT

Actual diagnostic result: `0/6`. The diagnostic launcher failed before resource allocation in all attempts, so no identity was claimed.

## CaptureBundle

Construction is gated on 6/6 independently read identities and rejects fixture, historical, literal, fallback and synthetic provenance. Diagnostic bundle: not created.

## Runtime handoff

The handoff uses `build_v25_runtime(project_root, capture_bundle, retry_id)`. Formal evidence mode wires `run_clean_retry()`; the bounded diagnostic explicitly does not.

## Authorization versioning

Multiple immutable authorization JSON files are permitted in `authorizations/` under one canonical root. Identity fields include authorization ID, run ID, baseline generation/SHA, issued timestamp, supersedes linkage and consumed state.

## Supersession enforcement

Explicit successor linkage and the immutable authorization index cause `AUTHORIZATION_SUPERSEDED`; consumption remains one-shot.

## Evidence-root collision semantics

Historical authorization material alone is allowed. `RESOURCE_MANIFEST.json` yields `EXECUTION_ALREADY_STARTED`; consumption markers yield `AUTHORIZATION_ALREADY_CONSUMED`; indexed/linked predecessors yield `AUTHORIZATION_SUPERSEDED`.

## Diagnostic attempts

Used `3 / 3`.

1. Import path defect; no authorization consumption or resources.
2. Django setup ordering defect; no authorization consumption or resources.
3. Python package-name collision; no authorization consumption or resources.

No fourth attempt was made. Post-attempt Podman inspection found no matching resources.

## Operational diagnostic

`FAIL — 0/6`, classified `LIVE_EXECUTOR_OPERATIONAL_DIAGNOSTIC`. Retry 20 was not involved.

## Focused tests

`27 passed / 0 failures / 0 errors`.

## Full backend regression

`548 total: 542 passed, 2 failures, 4 errors`. All six non-passes are the expected V6 protected-source drift and dependent PRECREATION/operational-manifest failures. The required `0 failures / 0 errors` state was not reached.

## Files modified

- `backend/foundation/phase31_4_v2_5_live_executor.py`
- `backend/foundation/phase31_4_v2_5_operational_adapters.py`
- `backend/foundation/phase31_4_v2_5_disposable_runner.py`
- focused live-executor and runner tests
- repository operational action and diagnostic launchers
- additive authorization index and diagnostic artifacts
- this report and its JSON companion

## V6 integrity impact

`INTEGRITY_RECONCILIATION_REQUIRED`. V6 was not modified.

## Historical artifacts modified

`NONE`

## V5 authorization

`SUPERSEDED / UNCONSUMED / DO_NOT_CONSUME`

## Formal V6/V7 Retry 20 authorization created

`NO`

## Retry 20 executed

`NO`

## Phase 31.5

`EXECUTION_HELD`

## Exact next step

Reconcile the material sources into a V7 successor integrity generation.
