# Phase 31.4 V2.5 Runner Successor Reconciliation

## Verdict

`RUNNER_SUCCESSOR_RECONCILIATION_PASS`

## V4 and V5

V4 remains immutable at [PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V4.json](PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V4.json), SHA-256 `960f2a133f72e939842762986ce3ad43762302b0caa447799732740fc4571f25`.

V5 is [PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V5.json](PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V5.json), SHA-256 `64127fbf818dc77c1cdd37221ce3a16f2dc2089342268b4eecb157b487c3ca64`, and is a verified successor of V4 for the explicitly reviewed disposable evidence runner remediation. The historical provenance discontinuity is preserved and no byte continuity across that gap is claimed.

## Material inventory

V4 protected `23` sources. V5 protects `25`: `22` unchanged, one modified guard, and two new runner sources. No material source was removed, missing, or unexpected.

New protected runner sources:

- `backend/foundation/phase31_4_v2_5_disposable_runner.py` SHA-256 `fb54ae34d5df2ecad692601a253224c6083f293fc2f640052a97d98e86c1f487`
- `docs/governance/tools/phase31_4_v2_5_disposable_runner.py` SHA-256 `1182854657d4165eb6b095906e161317d9bf84ece07caf439760ea69231fa8b9`

The modified protected source is `backend/foundation/phase31_4_integrity_generations.py`, updated only to preserve V4 historical validation and enforce V5/current runner-source membership. ADR-0022 is documentation/governance material, not executable source.

## Controls confirmed

The authoritative mapping is `run ID -> canonical_run_slug -> evidence root`, owned by `canonical_run_slug`; no independent conflicting slug construction remains. Authorization is validated, durably consumed with exclusive creation, and only then may allocation occur. Reuse fails with `AUTHORIZATION_ALREADY_CONSUMED`.

The runner state machine is `AUTHORIZED -> ALLOCATING -> RESOURCES_ALLOCATED -> BOOTSTRAPPING -> READY -> PRECREATION_RUNNING -> PRECREATION_PASS -> STAGE_EXT_RUNNING -> STAGE_EXT_PASS -> COMPLETED -> TEARDOWN_COMPLETE`, with `FAILED` and cleanup-only recovery. Manifest writes are atomic and crash-safe. Resources carry run slug, authorization SHA, and role labels; cleanup is manifest-scoped and label-scoped with no global prune.

Tooling, allocation, port publication, PostgreSQL startup/readiness, and bootstrap failures remain separately classified. Retry 19 remains `CONSUMED / FAILED`; no historical manifest or evidence was made resumable.

## Diagnostic boundary

The retained [RUNNER_ENVIRONMENT_DIAGNOSTIC](runs/Phase_31.4_V2.5_Runner_Environment_Diagnostic_20260923/RESOURCE_MANIFEST.json) proves PostgreSQL 18.6 with the approved image, dynamic host port `33971`, real connectivity PASS, `SELECT 1` PASS, teardown PASS, and zero remaining resources. It does not prove PRECREATION, Stage EXT, Retry 20, or Phase 31.4 completion.

## Migrations and tests

Migrations: V2.4 `23/23 PASS`; V2.5 `24/24 PASS`; pending `0`; new `0`; fake `0`; manual patches `0`; `makemigrations --check --dry-run` PASS.

Runner, immutability, PRECREATION, verifier, runtime, graph, V1-V5 integrity, and guard integration: `79/79 PASS`. Full backend regression: `537/537 PASS`. Failures: `0`. Errors: `0`.

## Governance status

`P0=0`, `P1=0`; runner blocker: `REMEDIATED / INTEGRITY_RECONCILED`.

Retry 19 Stage EXT remains `LIVE_REVALIDATION_PENDING`. Phase 31.5 remains `EXECUTION_HELD`. Retry 20 executed: `NO`. Historical artifacts modified: `NONE`.

Disposable evidence run readiness is `READY_FOR_SEPARATE_RETRY20_GOVERNANCE_REVIEW`.

## Exact next step

Perform one separately authorized Retry 20 governance review. Do not execute Retry 20 as part of this reconciliation.
