# ISO SMART AI Phase 31.4 V2.5 V8

## Verdict

`ATTEMPT_2_FAIL`

## Remediation applied

`docs/governance/tools/phase31_4_v2_5_operational_actions.py`, `service()` now passes `str(root / "manage.py")` to `os.execve`. The Python executable, cwd, environment, ports, readiness path, and subsequent arguments were not changed.

## Focused tests

- Direct focused service tests: `2 passed`.
- `docs/governance/tools/test_phase31_4_v2_5.py`: `V2.5 focused regression: PASS`.
- Syntax compilation: PASS.
- Pytest was unavailable in `backend/.venv`; the same test functions were executed directly with the project interpreter.

## Successor integrity

- V8 preserved as historical evidence.
- Successor: `PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V9.json`.
- V9 SHA-256: `8834bc546ccb585c917b501e20ba25bf37a4a7f1efc23b7b379ea1fd1f34933e`.
- V9 verification: PASS.

## Attempt 2 authorization

- Artifact: `PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_ATTEMPT_2_AUTHORIZATION_V1.json`.
- SHA-256: `7e8eb5b86fd2573f81092f301e18d5502c9809e3d117d7e05ef0aefb267d86b0`.
- Parent SHA-256: `c8633d150784c23170585627b1bf3bd738bcf62197998d5ea8e7bd3d9d08aac9`.
- Consumption: atomic and PASS.

## Resource allocation and state trace

Fresh AdminApps and ISO Smart PostgreSQL 18.6 containers, networks, volumes, databases, and dynamic ports were allocated. State reached:

`AUTHORIZED -> ALLOCATING -> RESOURCES_ALLOCATED -> BOOTSTRAPPING -> READY -> PRECREATION_RUNNING -> PRECREATION_PASS -> STAGE_EXT_RUNNING -> FAILED -> TEARDOWN_COMPLETE`

## PostgreSQL, migrations, and roles

PASS. Both PostgreSQL instances accepted `SELECT 1`; AdminApps and ISO Smart migrations completed with zero pending migrations. ISO Smart roles and session configuration verified.

## AdminApps startup

The approved path remediation worked: the prior missing-file error did not recur. AdminApps process launched with its absolute backend `manage.py`, but readiness endpoint `/api/integration/health/` returned HTTP `401 Unauthorized` throughout the readiness timeout. This is the exact Attempt 2 blocker. No additional remediation was applied.

## ISO Smart startup

`NOT_REACHED` because the runner stops after AdminApps readiness failure.

## Stage EXT

All controls were `NOT_EXECUTED` because startup failed before identity creation:

| Control | Resultado |
|---|---|
| 1/6 tenant | NOT_EXECUTED |
| 2/6 actor | NOT_EXECUTED |
| 3/6 tenant_projection | NOT_EXECUTED |
| 4/6 user_projection | NOT_EXECUTED |
| 5/6 organization | NOT_EXECUTED |
| 6/6 process | NOT_EXECUTED |

## CaptureBundle

`NOT_REACHED`.

## Teardown and residual resources

Teardown PASS with `ZERO RESIDUAL RESOURCES`. Containers, networks, volumes, service processes, and run-scoped resources were independently absent after cleanup. No global prune was used.

## Repository changes

- Functional source: absolute `manage.py` resolution in `service()`.
- Governance source: V9 integrity guard and current-baseline promotion.
- Tests: focused service command tests.
- Evidence: remediation review, focused tests, V9 integrity, Attempt 2 authorization/consumption, preflight, runtime manifest, logs, outcome, residual check, teardown, and this report.
- Historical V8 and Attempt 1 artifacts untouched.

## Governance status

- Retry 20 authorization: `NONE`
- Retry 20 executed: `NO`
- Phase 31.5: `EXECUTION_HELD`
- Attempt 3: `NOT_STARTED`

## Exact next step

Stop. Review the new AdminApps readiness blocker (`HTTP 401 Unauthorized`) and, only under a separate subsequent authorization, define at most one remediation candidate. Do not execute Attempt 3, Retry 20, or Phase 31.5 from this result.
