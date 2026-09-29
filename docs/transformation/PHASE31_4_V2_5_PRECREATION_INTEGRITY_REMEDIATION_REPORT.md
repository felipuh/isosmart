# Phase 31.4 V2.5 — PRECREATION_INTEGRITY Remediation V1

## Verdict

`PRECREATION_INTEGRITY_REMEDIATION_FAIL`

Implementation is complete, but governance PASS is withheld because the protected runtime and verifier changed and the untouched current V2 baseline now correctly rejects those bytes. State: `CODE_REMEDIATED / CURRENT_INTEGRITY_SUCCESSOR_RECONCILIATION_REQUIRED`.

## Retry 17 blocker addressed

Yes, in code. Retry 17 failed because `PRECREATION_INTEGRITY` had no registered operation, assertions, or retained-evidence contract. It now has all three and stops the phase runner before `INITIAL_OPPORTUNITY` or any later phase when it returns `FAIL`.

## Executor

`PrecreationIntegrityExecutor`

## Operation

`verify_precreation_integrity`

Claimed guarantee: `Pre-creation source, contract, authority and protected-material integrity are verified before any runtime domain effect is allowed.`

## Assertions

- Current V2.5 source integrity.
- Historical V2.4 integrity and exact SHA-256.
- Protected-source presence, membership, hashes, verifier protection, and unexplained drift.
- Protected migration material membership and hashes, without applying migrations.
- Authoritative V2.5 contract existence, generation, and current-source binding.
- Fail-closed verifier semantics: no default PASS, `PhaseExecutionResult` propagation, evidence schema version, and capture/readback schema version.
- Unique run ID, explicit Retry 16/17 rejection, exclusive evidence directory, and no historical overwrite.
- Authority configuration references only: AdminApps endpoint, credential, entitlement/product, and actor source contract. No live authority claim is made.
- Required evidence serialization.

## Evidence contract

The operation writes a single new retained record at `docs/governance/evidence/runs/<run-id>/PRECREATION_INTEGRITY/precreation_integrity.json`. Directory creation is exclusive. Existing directories fail closed and are never overwritten.

The record contains phase, executor, operation, status, current manifest path/hash, historical result, protected-source count/mismatches, migration result, contract result, verifier result, run identity result, assertions, evidence paths/hashes, error, and timestamps.

## Read-only guarantee

The operation performs filesystem reads and creates only its new governance evidence record. It does not open a database connection, execute a migration, contact AdminApps, invoke a domain service, or create any tenant, user, organization, process, opportunity, agent, recommendation, action plan, or authorization.

## Tests added

Ten focused cases cover valid PASS, current hash mismatch, missing protected source, historical V2.4 mismatch, missing contract, malformed integrity JSON, duplicate run/evidence directory, missing approval evidence reference, returned-FAIL propagation, and stopping before `INITIAL_OPPORTUNITY`.

## Focused result

`PASS` — 39 tests across PRECREATION_INTEGRITY, the V2.5 runtime, and the verifier remediation.

Historical integrity: `PASS` — 3 tests. V2.4 remains `a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387`.

## Integrity result

`FAIL_EXPECTED_PENDING_SUCCESSOR_RECONCILIATION`.

The current V2 baseline was not modified. It correctly detects:

- Runtime protected hash changed from `7ed7430abe798d6fd31b2bc27344abde35a7ab7df9e2ef13b51f1ddb7b03fd00` to `70997fb33eb22c9576cb7def0cd5ccdff9d61deebad4621072920b5acf5efb19`.
- Verifier protected hash changed from `a716e139f15d4b3f247ec4db56b339bad0e8a29ef06030a00aa9542e7195a35f` to `61a6fa21f01c27bd6713154512045926c4d3d65d410d0d572922ea1ef21dc639`.
- The new protected helper has SHA-256 `9fc0efcc14fee9587a041b8c81dffde2d447f82e16d4df495571b7358cb854eb` and is not yet registered by an approved successor generation.

No hashes were silently updated and no manifest was weakened.

## Full regression

`FAIL` — 509 tests, 0 assertion failures, 4 errors. All four errors are current-integrity enforcement caused by the intentionally unreconciled protected-source evolution. No functional regression test failed.

## Files modified

- `backend/foundation/phase31_4_v2_5_precreation_integrity.py`
- `backend/foundation/phase31_4_v2_5_runtime.py`
- `backend/foundation/phase31_4_v2_5_verifier_remediation.py`
- `backend/foundation/test_phase31_4_v2_5_precreation_integrity.py`
- `backend/foundation/test_phase31_4_v2_5_runtime.py`
- `docs/governance/evidence/PHASE31_4_V2_5_PRECREATION_INTEGRITY_REMEDIATION_V1.json`
- `docs/transformation/PHASE31_4_V2_5_PRECREATION_INTEGRITY_REMEDIATION_REPORT.md`

The worktree already contained unrelated and overlapping changes; they were preserved.

## Historical artifacts modified

None.

## Phase 31.5

`EXECUTION_HELD`

## Live retry executed

`NO`

## Next exact step

Perform a separate V2-governed current-integrity successor reconciliation covering the runtime, verifier, and precreation helper.
