# Phase 31.4 V2.5 V11 — Dependency parity and Attempt 2

## Verdict

`V11_ATTEMPT_2_FAIL`. The dependency blocker is resolved. A new projection-delivery blocker stopped the diagnostic; no further remediation and no Attempt 3 were executed.

## Attempt 1 blocker confirmation

`ModuleNotFoundError: No module named 'django_apscheduler'` occurred during AdminApps authority initialization under ISO Smart's Python. Attempt 1 remains CONSUMED / FAIL. All 15 snapshotted historical V11 files are byte-identical, including authorization and runtime evidence. Bearer live execution was NOT_EXECUTED in Attempt 1, not a Bearer contract failure.

## Dependency root cause

Case A: `DISPOSABLE_DEPENDENCY_INSTALLATION_GAP_CONFIRMED`.
`IS_DJANGO_APSCHEDULER_CANONICAL_DEPENDENCY = true`.
The app is unconditionally registered in `config.settings.INSTALLED_APPS`. Scheduler job enablement is a separate setting.

## Canonical dependency source

`/home/felipe/proyectos/adminapps/backend/requirements.txt`: `django-apscheduler==0.7.0`, runtime, no extras. SHA-256: `cf804dcb0092c3daaa97831806e1eefa2c91edcabdb1a7e4f9ca21dea7bfb29f`.
Both CI workflows and development instructions install this manifest. No alternate Python manifest/lockfile was found. The complete manifest includes its existing development dependency; no parallel package list was introduced. Default PyPI index, download host `files.pythonhosted.org`, artifact SHA-256 evidence retained, no index/TLS changes. No transitive lock exists in the project.

## Host/disposable parity

Host AdminApps: Python 3.9.25, pip 26.0.1, Django 4.2.22, django-apscheduler 0.7.0, APScheduler 3.11.3; unchanged. The host tests were not rerun, so no current host regression claim is made.

Previously the runner created no Python environment, installed no dependencies and used no dependency manifest. Authority used ISO Smart's Python 3.12.13 venv (module absent); AdminApps migration/service subprocesses used its host venv. The subprocess cwd was ISO Smart's repository for authority and AdminApps backend for management commands. Package cache was irrelevant because the runner performed no installation.

The remediated diagnostic provisions a fresh isolated Python 3.12.13 venv from AdminApps' canonical manifest. Authority, migrations and service use the same interpreter through `PHASE31_ADMINAPPS_PYTHON`. ISO Smart keeps its separate pinned environment. Attempt 2 did not reuse either AdminApps host venv or the earlier validation venv.

## Remediation

`REMEDIATION_COUNT = 1`. Added canonical temporary-runtime provisioning and cleanup; routed AdminApps authority/bootstrap/service/management calls to it; added parity tests and V12 integrity reconciliation. The exact versioned diff is commit `7b45775192c8d9f8906d9e2b00cedde2e8cae0a7`. The relevant previously untracked Attempt 1 causal evidence was preserved byte-for-byte in that commit. No scheduler, authentication, Bearer, dependency-manifest or migration change was made.

## Focused tests

50/50 PASS: seven parity tests plus 43 existing Bearer/readiness/adapter/integrity checks. Operational command boundary: 2/2 PASS. Retained logs are in `PHASE31_4_V2_5_ADMINAPPS_DEPENDENCY_PARITY_VALIDATION_V1`.

## Startup/import validation

`import django`, `config.settings` load, `django.setup()` and `django_apscheduler` import all PASS in the validation environment and the fresh Attempt 2 runtime. All 18 canonical direct pins verified; `pip check` PASS. `ADMINAPPS_DISPOSABLE_DJANGO_SETUP = PASS` was recorded before database allocation.

## Regression

ISO Smart: 575/575 PASS. AdminApps: 180/180 PASS under the canonical temporary Python 3.12 environment. Its CI product subset also passed 160/160. These are current executions, not reused historical counts.

## Bearer regression

`OPERATIONAL_BEARER_IDENTITY_CONTRACT = PASS`. Issuance and authenticated readiness also succeeded live in Attempt 2. `RAW_CREDENTIAL_LEAKS = 0` in retained evidence scans; credential buffer/reference cleanup recorded. No raw token is retained.

## Successor integrity

`SUCCESSOR_INTEGRITY = PASS`; V12 has 30 protected sources, predecessor V11 remains frozen. Historical V2.4 integrity and inherited migration hashes passed.

Manifest: `docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V12.json`
SHA-256: `685e04fa2e94513c357bbd6d333c2fe785e967b172234cd93faae777e25f79c2`

Reconciliation: `docs/governance/evidence/PHASE31_4_V2_5_ADMINAPPS_DEPENDENCY_PARITY_SUCCESSOR_RECONCILIATION_V1.json`
SHA-256: `8e1a0c0febdf9c06ec34d3abc062dcf595574ef89decc0f938771cbcd1e8318c`

## Remediation commit

`ATTEMPT_2_REMEDIATION_COMMIT = 7b45775192c8d9f8906d9e2b00cedde2e8cae0a7`.
Full worktree clean at the pre-authorization boundary. This was the exact HEAD used for execution.

## Attempt 2 authorization

`docs/governance/evidence/PHASE31_4_V2_5_V11_OPERATIONAL_DIAGNOSTIC_CYCLE_1_ATTEMPT_2_AUTHORIZATION_V1.json`
SHA-256: `7d085832f05bef5498f029eaa59f7bc3fbddf62c9f0cd515c10ad0198ad40c23`.
DIAGNOSTIC_ONLY / ONE_SHOT; consumed exactly once. Parent cycle SHA remains `d5508dc362fc93b653c5c316c5259103da63b7b520d7ccbf05a6f0be8096a72f`. Authorization binds Attempt 1 evidence, remediation, reconciliation, workspace, exact HEAD and fresh run slug.

## Preflight

PASS: exact HEAD, no source drift, V12 integrity, preserved parent/Bearer authorization hashes, previous cleanup, no previous/current attempt resources, absent run evidence/manifest, unconsumed authority, available runtime, and real-runtime Django setup. The canonical dependency manifest binding was independently rechecked. Both manage.py paths were subsequently exercised by successful migrations.

## Resource allocation

Fresh run-scoped PostgreSQL containers, databases, networks, volumes and dynamic ports were allocated. DB ports: [46671, 32935]. HTTP endpoints: AdminApps http://127.0.0.1:49277, ISO Smart http://127.0.0.1:47009. These endpoints are now stopped.

## State machine

AUTHORIZED → ALLOCATING → RESOURCES_ALLOCATED → BOOTSTRAPPING → READY → PRECREATION_RUNNING → PRECREATION_PASS → STAGE_EXT_RUNNING → FAILED → TEARDOWN_COMPLETE.
The business outcome is FAIL; the infrastructure terminal state is TEARDOWN_COMPLETE.

## PostgreSQL

Both PostgreSQL 18.6 instances passed readiness, version verification and SELECT 1. Migrations pending: AdminApps 0; ISO Smart 0. ISO Smart roles and session configuration verified.

## PRECREATION

PASS; retained nine-assertion integrity evidence.

## AdminApps authority startup

PASS; import/setup completed and authority exited 0. Exact interpreter/argv/cwd, PID 16468, timestamps and exit status are retained in `authority_process.json`. Tenant and actor were created and read back; runtime Bearer issued through the unchanged contract.

## AdminApps readiness

PASS: `GET /api/integration/health/` returned HTTP 200 with the persisted X-API-Key. Raw credentials excluded.

## Bearer issuance

PASS: approved access token issued for the existing run-scoped viewer identity, passed through the anonymous pipe, fingerprint-only evidence retained and destroyed at teardown.

## ISO Smart readiness

PASS: authenticated `GET /health` returned HTTP 200 from the canonical DB-aware Django view. No Nginx liveness substitution. The service log retains status; a separate HTTP response body was not retained.

## Stage EXT

No aggregate six-control certification was produced because delivery failed before the resolver completed. Authority readbacks must not be reported as a completed Stage EXT bundle.

| Control | Result |
|---|---|
| 1/6 tenant | Authority creation + persisted readback PASS; Stage EXT certification not reached |
| 2/6 actor | Authority creation + persisted readback PASS; Stage EXT certification not reached |
| 3/6 tenant_projection | FAIL: TenantProjection.DoesNotExist during delivery readback |
| 4/6 user_projection | NOT_EXECUTED after tenant lookup failure |
| 5/6 organization | NOT_EXECUTED |
| 6/6 process | NOT_EXECUTED |

## CaptureBundle

NOT_CREATED; target CAPTURE_BUNDLE_READY not reached. No 33-phase runtime or Retry 20 was executed.

## New blocker

Classification: `OPERATIONAL_EVENT_DELIVERY_PROJECTION_BLOCKER`. Expected: delivered tenant event with a persisted matching TenantProjection. Observed: the delivery management command returned successfully, then the tenant readback raised `TenantProjection.DoesNotExist`. Traceback is retained in `delivery.log`. The manifest's `runner_step=verify_isosmart_postgres_version` is stale; the actual failing operation is `delivery`.

Source review supports one candidate: align the disposable authority producer with AdminApps' canonical transactional tenant-outbox contract. Authority currently creates/saves the organization directly; the canonical serializer explicitly calls `record_tenant_event`; the delivery command can exit normally with no pending rows. This is an omitted-outbox hypothesis, not a directly measured outbox row count. No direct outbox snapshot or complete delivery command output was retained before mandatory teardown. No correction was applied.

## Teardown

PASS. Both service processes terminated, credential references destroyed, run-scoped database containers/networks/volumes removed, and temporary Python runtime removed. No global prune.

## Zero residual verification

Independent post-teardown verification: containers=0, networks=0, volumes=0, matching run processes=0, recorded PIDs present=0, run port listeners=0, credential references=0 and disposable Python runtimes=0. This is run-scoped; unrelated existing host resources were preserved. Evidence: `final_independent_residual_check.json`.

## Repository final state

Remediation is committed; diagnostic-only authorization and evidence are archived in a separate evidence commit. Final ISO Smart worktree cleanliness is verified after that commit. No AdminApps source changes. Its pre-existing untracked `backend/test_default.sqlite3` was left in place. Final source integrity was reverified; evidence archival does not change the execution HEAD bound by the consumed authorization.

## Retry 20

Current authorization = NONE. Executed = NO. Historical authorization = SUPERSEDED_UNCONSUMED; reuse prohibited.

## Phase 31.5

EXECUTION_HELD.

## Exact next step

Independently review `new_blocker_review.json` and authorize, if appropriate, the single bounded outbox-producer remediation candidate. Any Attempt 3 requires its own focused tests, reconciliation and one-shot authorization. Attempt 3 remains NOT_STARTED. Do not reopen the closed dependency or Bearer contract, and do not authorize Retry 20 automatically.
