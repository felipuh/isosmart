# Phase 31.4 V2.5 — Verifier Remediation Current-Integrity Reconciliation

Generated: `2026-09-22T20:51:44-06:00`

Scope: integrity reconciliation only. No live retry, Retry 17, WS-A, or Phase 31.5 execution occurred.

## Verdict

**`VERIFIER_REMEDIATION_INTEGRITY_FAIL`**

The gate stopped fail-closed. The current runtime is consistent with the documented verifier-remediation intent and its focused tests pass, but the exact predecessor bytes for SHA-256 `5be7650a…` are not present as a Git blob, retained snapshot, or recoverable patch. Consequently, a byte-complete diff cannot prove that the runtime change is explained *entirely* by verifier remediation or exclude unrelated drift.

An attempted G2 candidate was created during the assessment. When the byte-causality limitation was confirmed, it was not adopted and was removed. The immutable V1 manifest remains the authoritative current-integrity generation.

Checkpoint findings: `P0=1`, `P1=0`. The P0 is unproven byte-exhaustive causality for a protected source. The staged module is recorded as a material candidate, not a P1 in an admitted generation; the P0 already blocks any successor adoption.

## Original regression failures

The final authoritative state reproduces `498 tests`, `0 failures`, and `3 errors`. These are not three independent source drifts: one runtime divergence produces two direct failures and one transitive failure.

| Test | Reported surface | Exact cause | Classification |
|---|---|---|---|
| `SupportingContractAuditTests.test_protected_sources_match` | `IntegrityGenerationError` on `phase31_4_v2_5_runtime.py` | V2.4 history passes, then V1 expects `5be7650a…` and observes `7ed7430a…`. Exact predecessor-to-current byte causality is unavailable. | `UNEXPECTED_SOURCE_DRIFT` |
| `V25CurrentOperationalIntegrityTests.test_current_manifest_passes` | Same runtime integrity error | Direct V2.5 V1 current-generation rejection of the same single runtime divergence. | `UNEXPECTED_SOURCE_DRIFT` |
| `Retry5ManifestTests.test_authoritative_manifest_and_external_hash` | `ManifestVerificationError: unapproved successor: backend/backend/settings.py` | Settings is already an approved V1 successor (`1da64d5f…` → `bd72cff9…`) and matches V1. Its check invokes the complete current guard, which fails on the runtime; the wrapper rethrows using the currently iterated settings path. | `UNEXPECTED_SOURCE_DRIFT` (transitive; misleading surface path) |

No test exposes a V2.4 or Retry 16 historical-integrity violation. The third failure is not a new settings drift and is not counted as a second protected-source divergence.

## Drift classification

Governance classification for the protected runtime is **`UNEXPECTED_SOURCE_DRIFT`** because the required “explained entirely” standard is not proven. This is a fail-closed classification: it does not assert that malicious or unrelated edits occurred; it states that the retained evidence cannot exclude them.

Available evidence does support intended causality:

- `PHASE31_4_V2_5_EVIDENCE_RECONCILIATION_V1.json` — SHA-256 `b16402b0893d03b7c17dcb199122cc5c2bbab1cf938e1e97e89444590a801067`.
- `PHASE31_4_V2_5_VERIFIER_REMEDIATION_V1.json` — SHA-256 `51cce2a90eee07421ea8c3b63deb64e8e1fd0e14eec5efaf0d2c004d017f315e`.
- Focused verifier regression is `29/29 PASS`.

That evidence is insufficient for an exhaustive source-delta claim without the predecessor bytes. In addition, the standalone `phase31_4_v2_5_verifier_remediation.py` (SHA-256 `a716e139…`) contains graph, exact-comparison, event/outbox/audit, and security primitives but is not directly imported by the current runtime; it remains `STAGED_NOT_LIVE_EXECUTED`.

## Protected sources

Authoritative generation: `V2.5_CURRENT / v1`, manifest SHA-256 `8e77d62e1cccc42d0dbeaf7c00e9007c7120201b97af2f46484bbf81893a1db0`.

| Measure | Result |
|---|---:|
| Expected V1 protected paths | 20 |
| Present protected paths | 20 |
| Hash-matching paths | 19 |
| Changed paths | 1 |
| Missing paths | 0 |
| Unexpected paths within V1 membership | 0 |
| Unprotected material candidates | 1 |

Changed: `backend/foundation/phase31_4_v2_5_runtime.py` only.

The 19 unchanged paths are recorded individually in the JSON evidence. The material candidate outside V1 is `backend/foundation/phase31_4_v2_5_verifier_remediation.py`; it was not added to an authoritative successor because the causality gate failed.

## Runtime old SHA

`5be7650ac78eae653f4e6cd0b656ab0ccd9556a75f9c41cb3edd512d6a012cfd`

## Runtime new SHA

`7ed7430abe798d6fd31b2bc27344abde35a7ab7df9e2ef13b51f1ddb7b03fd00`

## Historical integrity

**PASS.** The dedicated historical suite is `3/3 PASS`.

- Required V2.4 contract SHA-256: `a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387` — `PASS`.
- V2.4 historical manifest SHA-256: `8f055dee53d7ef34a3b47ccb9fed9885c39c0b616cc0c582c75e49edf2e0cda3`.
- Retry 16 SHA manifest: `d6e514f439e9b03fc9afa0d1bda47e9ff5c198ad9417d6244ce13f2bf1e62cb3`.
- Retry 16 promotion closure: `08b8af8c9911963844759808adbef5c2b3b663a26c34df494fbaca0cf985f328`.
- Previous/current V2.5 V1 manifest: `8e77d62e1cccc42d0dbeaf7c00e9007c7120201b97af2f46484bbf81893a1db0`.

## Current integrity

**FAIL_CLOSED.** The dedicated combined historical/current suite ran `6 tests`, with `0 failures` and `1 error`: V1 rejects the runtime hash divergence.

No successor generation remains or was adopted. The candidate `PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V2.json` was created during assessment, then withdrawn and removed; historical and current V1 hashes were not rewritten.

## Migration integrity

**PASS.** V2.4 retains 23 historical migrations. V2.5 V1 expects 24 and exactly 24 are present; membership and every hash match. `makemigrations --check --dry-run` reports `No changes detected`, and the migration diff is empty.

## Focused verifier tests

**PASS — `29/29`, 0 failures, 0 errors.**

The passing focused behavior does not substitute for protected-source causality proof.

## Full regression

**FAIL — `498 tests`, 0 failures, 3 errors (`45.276s`).**

The three errors are exactly the two direct and one transitive integrity failures listed above. No expected-failure masking or skipped guard was introduced.

## Source alignment guard

This task did not modify the 63-requirement interpretation, the 17-stage onboarding interpretation, original source artifacts, or Phase 31.5 functional scope.

## Historical artifacts modified

**None.** V2.4, Retry 16, promotion closure, evidence reconciliation, and the V2.5 V1 current-integrity generation retain their verified bytes.

## Source artifacts modified

**None.**

## Phase 31.5

`EXECUTION_HELD`

## Live retry executed

`NO`

No Retry 17 was created and WS-A was not executed.

## Disposable evidence run status

`NOT_READY`

## Exact next step

Recover and supply the exact predecessor runtime blob whose SHA-256 is `5be7650ac78eae653f4e6cd0b656ab0ccd9556a75f9c41cb3edd512d6a012cfd`.
