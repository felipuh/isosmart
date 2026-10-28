# Phase31.5 E-07 / E-08 Repository-Local PostgreSQL Proof

Date: 2026-10-04 (America/Costa_Rica)
State: **`EXECUTION_HELD`**

## A. Governance Integrity

This is a narrow repository-local evidence slice, not Phase31.5 execution.
The adopted adjudication verdict remains **`PHASE31.5 AUTHORIZATION PATH
DERIVED — PRECONDITION REMAINS`**. The preceding technical closure verdict
remains **`PHASE31.5 E-07/E-08 PARTIALLY CLOSED — TECHNICAL PRECONDITIONS
REMAIN`**. No prior evidence was edited.

## B. Frozen Input Integrity

`docs/governance/evidence/phase31_5/18_sha256.json` was verified against its
eight payloads: **8/8 PASS**. The self-excluded manifest hash remains
`eef432a8259d8213e77c8069e6e095455e666b8796c42f0bcc52acac400bf921`.
Frozen payloads were read only.

## C. Exact Six-Prerequisite Matrix

| Prerequisite | Controlling blocker | Source provenance | Required evidence | Slice authorized |
|---|---|---|---|---|
| `P0-31_5-ENTRY-COMMITTED-CREDENTIALS` | Rotation and approved redacted scan are absent. | Adjudication §D; environment audit `findings` / `secret_handling`. | Authentic rotation and approved scan evidence. | No |
| `P1-31_5-ENTRY-DEPLOYMENT-REPRODUCIBILITY` | Runtime/base-image/dependency/topology/target-guard definition is not governed. | Adjudication §D/F/I; environment audit. | Approved deployment definition and clean-build proof. | No |
| `P1-31_5-ENTRY-SQLITE-OPERATIONAL-ESCAPE` | PostgreSQL-backed validation was absent. | Adjudication §D; environment audit `findings`; `backend/settings.py`; PostgreSQL harnesses. | Existing-migration PostgreSQL proof of the explicit non-SQLite runtime, persistence and tenant controls. | Yes |
| `P1-31_5-ENTRY-JWT-LOCALSTORAGE` | No approved replacement token contract exists. | Adjudication §D; environment audit `findings`. | Cookie/CSRF/session/refresh/revocation migration contract. | No |
| `P1-31_5-ENTRY-BACKUP-NOT-IMPLEMENTED` | Backup/restore operational contract is absent. | Adjudication §D; environment audit `findings`. | Destination, retention, encryption, restore and integrity contract. | No |
| `P1-31_5-ENTRY-WORKER-OUTBOX-OPERABILITY` | Worker/beat/dispatcher lifecycle and signals are undefined. | Adjudication §D; environment audit `worker_outbox` / `findings`. | Operations lifecycle, broker, supervision and alert contract. | No |

## D. PostgreSQL Eligibility Classification

| Prerequisite | Classification | Reason | Execution |
|---|---|---|---|
| `P0-31_5-ENTRY-COMMITTED-CREDENTIALS` | `AUTHENTIC_EXTERNAL_EVIDENCE_REQUIRED` | Local source inspection cannot prove rotation or an approved scan. | Not attempted |
| `P1-31_5-ENTRY-DEPLOYMENT-REPRODUCIBILITY` | `GOVERNANCE_REQUIRED` | Selecting the missing topology and pins would invent a deployment definition. | Not attempted |
| `P1-31_5-ENTRY-SQLITE-OPERATIONAL-ESCAPE` | `POSTGRESQL_PROOF_ELIGIBLE` | Guard, PostgreSQL settings, migrations, RLS and persistence expectations already exist in source. | Attempted |
| `P1-31_5-ENTRY-JWT-LOCALSTORAGE` | `SOURCE_SEMANTICS_MISSING` | A secure transport design is not source-defined. | Not attempted |
| `P1-31_5-ENTRY-BACKUP-NOT-IMPLEMENTED` | `SOURCE_SEMANTICS_MISSING` | Backup/restore behavior is not source-defined. | Not attempted |
| `P1-31_5-ENTRY-WORKER-OUTBOX-OPERABILITY` | `SOURCE_SEMANTICS_MISSING` | Operations behavior is not source-defined. | Not attempted |

The one eligible item satisfied the slice rules: existing schema and
migrations, explicit PostgreSQL settings, tenant/RLS behavior, transactional
outbox behavior, no external authority, no external network call, and no
Phase31.5 lifecycle command.

## E. Ephemeral Environment

The already-local immutable PostgreSQL 18.6 image was inspected before use:
`docker.io/library/postgres@sha256:7341002d2b8c7c5bdd7542a671a95b36196c0b5b888daf454ae4fc33ba5346d7`, image ID
`a6638641707cdf047e5d5c2781f437e2e809323cab22c70b280be8389fbb7878`.

The proof used the repository’s rootless Podman foundation gate with generated
ephemeral role/database/container/volume names and a loopback-only dynamic
port. Registry pull was deliberately suppressed; no external network access
occurred.

## F. Migration Result

`backend/foundation/postgres_wp2_harness.py` invoked Django migration against
the generated disposable PostgreSQL database. Existing migrations completed
before the focused test suite began. No migration was created, edited, faked,
or manually patched.

## G. Eligible Prerequisite Proofs

`P1-31_5-ENTRY-SQLITE-OPERATIONAL-ESCAPE`: **PASS / CLOSED.**

The prior source guard remains verified: operational settings reject
`USE_SQLITE_DATABASE=1`, while `backend.settings_test` explicitly permits it.
The integration settings then refuse a non-PostgreSQL default database and
require `ISO_SMART_POSTGRES_INTEGRATION=1`. The focused harness ran against
the disposable PostgreSQL default database, demonstrating the required
non-SQLite persistence path rather than treating a SQLite test as evidence.

## H. RLS Evidence

The existing harness exercised real PostgreSQL RLS with non-superuser,
`NOBYPASSRLS` runtime principals. It verifies same-tenant reads/writes,
cross-tenant invisibility/denial, missing-tenant-context rejection, and
connection-context cleanup. No RLS policy was disabled or bypassed.

## I. Persistence Evidence

Synthetic repository-local fixtures exercised transactional writes and
rollback. The harness’s source-defined assertions passed for committed state
and rollback absence; all resulting fixtures were destroyed with the database.

## J. Event / Outbox Evidence

The focused suite asserted local domain-event and transactional-outbox rows
with their tenant/trace bindings. No broker, webhook, consumer outside the
local harness, or external delivery was started: external effects were `0`.

## K. Lineage / Idempotency Evidence

The harness’s existing assertions passed for immutable audit linkage, shared
event/outbox lineage, replay idempotency, and duplicate handling. These are
local persistence assertions only; they do not claim AdminApps authority.

## L. Commands Executed

| Command / interpreter / directory | Result | Database effects |
|---|---|---|
| SHA-256 recomputation / system SHA-256 / repository root | 8/8 PASS | none |
| Initial baseline settings/AST invocation / Python 3.12.13 / repository root | stopped on incorrect module-path and over-broad AST expectation; immediately corrected | none |
| Source compile, SQLite operational rejection, explicit-test allowance, credential AST check / `backend/.venv/bin/python` / `backend` | 4/4 PASS | none |
| Local image inspection / Podman / repository root | digest and image ID matched | none |
| `backend/.venv/bin/python /tmp/phase315_local_pg.py` / Python 3.12.13 / repository root | PASS | generated isolated PostgreSQL only; existing migrations, synthetic fixtures and local event/outbox rows |

The first invocation of the PostgreSQL wrapper used an incorrect relative
harness path. It stopped before migrations or tests; scoped teardown passed.
The corrected invocation is the recorded proof.

## M. Test Results

The source-defined `SourceArtifactPostgreSQLIntegrationTests` suite discovered
and executed **32 tests: 32 pass, 0 fail, 0 error, 0 skip**. The PostgreSQL
harness additionally completed its source-defined RLS, transaction, outbox,
lineage and idempotency assertions. The earlier four repository-local focused
checks remain **4/4 PASS**.

## N. Cleanup Verification

Both attempted runs reported scoped teardown **PASS**. The test-owned
container and volume were absent after the corrected run. No pre-existing
container, volume, database, or shared resource was selected for deletion.

## O. External-Effect Audit

| Effect | Count |
|---|---:|
| AdminApps calls | 0 |
| External API calls | 0 |
| Webhook calls | 0 |
| External event delivery | 0 |
| Deployment effects | 0 |
| Production DB effects | 0 |
| Staging DB effects | 0 |
| Registry pulls | 0 |

## P. Updated Six-Prerequisite Matrix

| Prerequisite | Initial blocker | Proof attempted | Result | Final state |
|---|---|---|---|---|
| `P0-31_5-ENTRY-COMMITTED-CREDENTIALS` | Authentic rotation/approved scan missing | No | External evidence still required | `OPEN_EXTERNAL` |
| `P1-31_5-ENTRY-DEPLOYMENT-REPRODUCIBILITY` | Governing deployment definition missing | No | Governance still required | `OPEN_GOVERNANCE` |
| `P1-31_5-ENTRY-SQLITE-OPERATIONAL-ESCAPE` | PostgreSQL validation missing | Yes | PostgreSQL-only settings, migrations and focused persistence/RLS proof passed | `CLOSED` |
| `P1-31_5-ENTRY-JWT-LOCALSTORAGE` | Secure-token semantics absent | No | Source semantics still missing | `OPEN_SOURCE_SEMANTICS` |
| `P1-31_5-ENTRY-BACKUP-NOT-IMPLEMENTED` | Backup/restore semantics absent | No | Source semantics still missing | `OPEN_SOURCE_SEMANTICS` |
| `P1-31_5-ENTRY-WORKER-OUTBOX-OPERABILITY` | Operations semantics absent | No | Source semantics still missing | `OPEN_SOURCE_SEMANTICS` |

## Q. E-07 Result

Six prerequisites existed initially; **one** is newly closed and **one** is
cumulatively closed. E-07 still has the external credential rotation/approved
scan prerequisite: **E-07: FAIL**.

## R. E-08 Result

The SQLite operational-escape prerequisite is closed. Deployment
reproducibility, JWT storage, backup/restore, and worker/outbox operability
remain open: **E-08: FAIL**.

## S. Remaining External / Governance / Source Blockers

Remaining prerequisites are exactly: committed-credential authentic evidence;
deployment reproducibility governance; JWT token-storage semantics;
backup/restore semantics; and worker/outbox operations semantics. None is a
remaining repository-local PostgreSQL/RLS/event-persistence proof item.

## T. Phase31.5 Preservation

Phase31.5 remains **`EXECUTION_HELD`**. This proof did not run WS-A, a
Phase31.5 lifecycle, AdminApps, a worker, a broker, a deployment, or any
external delivery.

## U. Files Changed

- `docs/transformation/PHASE31_5_E07_E08_POSTGRESQL_PROOF_2026-10-04.md`
- `docs/governance/evidence/phase31_5/20_postgresql_proof_2026-10-04.json`

## V. Final Verdict

### `PHASE31.5 POSTGRESQL PREREQUISITES CLOSED — NONLOCAL PRECONDITIONS REMAIN`

No verdict authorizes Phase31.5 lifecycle execution.
