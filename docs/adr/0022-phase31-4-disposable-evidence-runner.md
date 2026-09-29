# ADR-0022: Disposable evidence runner as a governed execution boundary

- Status: Accepted for implementation; execution held pending validation and successor integrity reconciliation
- Date: 2026-09-23
- Scope: future Phase 31.4 V2.5 disposable evidence runs and isolated runner diagnostics
- Complements: ADR-0021; does not supersede or rewrite historical run evidence

## Context

Retry 19 consumed its one-shot authorization and stopped fail-closed before useful bootstrap. Its run-scoped manifest was under `docs/governance/evidence/runs/Phase_31.4_V2.5_Clean_Retry_19/RESOURCE_MANIFEST.json`, while a bootstrap helper attempted to read a separately constructed flat path, `docs/governance/evidence/PHASE31_4_CLEAN_RETRY_19_RESOURCE_MANIFEST.json`. The same class of defect permits independent components to disagree between spellings such as `Phase_31.4_V2.5_Clean_Retry_19` and `Phase_31.4.V2.5_Clean_Retry_19`.

This is a tooling-path failure, classified as `DISPOSABLE_EXECUTION_TOOLING_BLOCKER`; it is not evidence of a PostgreSQL reachability failure. Retry 19 did not live-revalidate Stage EXT. It has no active processes or resources, made no code change, and its completed cleanup remains valid. Its authorization, execution state, resource history, and evidence paths are historical facts and must not be amended to make the run resumable or successful.

The V4 current-source integrity generation and the AdminApps endpoint successor reconciliation remain valid. The required remediation is a reusable runner for a future, separately authorized run with a new run ID, authorization, evidence root, manifest, and disposable resources. It is not a Retry 19 continuation path.

## Decision

### One immutable run context and one canonical slug

Every runner component, callback, and repository wrapper receives one immutable run context containing at least:

- run ID;
- authorization artifact path and expected SHA-256;
- current integrity generation and expected integrity SHA-256;
- evidence root;
- execution classification; and
- canonical run slug.

The canonical slug is either explicitly declared by the authorization or derived from the run ID by one shared deterministic function. The runner validates that the authorization's run ID and evidence root match the supplied context and that the evidence-root basename is the canonical slug. Allocation, bootstrap, phase callbacks, cleanup, and wrappers use that resolved context; they may not reconstruct a filename, retry-specific path, or alternate slug locally.

A mismatch between any supplied, authorized, derived, or persisted identity fails closed before resource activity. An existing manifest or other evidence of a prior execution is an evidence-root collision, not an invitation to continue it.

### One-shot authorization in an external ledger

Before any external resource command, the runner verifies that the authorization exists, its SHA-256 matches, its run ID and evidence root match, its declared integrity authority matches, it is unused, and the evidence root is fresh.

Consumption is then recorded with exclusive atomic creation in an append-only authorization-consumption ledger outside the run's evidence root, keyed by authorization SHA-256 and bound to the run ID, canonical slug, evidence root, execution classification, and consumption timestamp. The run root retains a run-scoped consumption record, but deleting, damaging, or partially creating that root cannot make the authorization reusable. Concurrent creation of the same ledger entry has one winner; every later attempt returns `AUTHORIZATION_ALREADY_CONSUMED` and fails closed.

Consumption precedes allocation. If the process stops after ledger creation but before manifest completion, the authorization remains consumed. Forensic completion and cleanup may follow, but the business run may not be replayed.

### Atomic, evolution-safe resource manifest

Each run creates a new `RESOURCE_MANIFEST.json`. Critical revisions are written through a same-filesystem temporary file, file synchronization, atomic replacement, and parent-directory synchronization before the runner advances. The manifest is logically append-only for state transitions and resource events: current-state projections may evolve, but earlier transition and event records are not removed or rewritten.

The manifest records at least the run ID, canonical slug, authorization SHA-256 and consumption record, integrity generation and SHA-256, evidence root, execution classification, allocation state, resource roles, deterministic names, labels, container IDs, networks, volumes, host ports, database names, timestamps, state transitions, last confirmed state, runner step, safe command metadata, failure details, cleanup obligations, and post-teardown absence results.

Resource intent, including deterministic names and required labels, is persisted before each external create operation. The observed result is persisted immediately afterward. Thus an interruption between creation and observation still leaves enough identity to inspect and clean up the possible orphan without guessing from process memory.

### Explicit state machine

Formal evidence runs use the ordered state machine:

`AUTHORIZED -> ALLOCATING -> RESOURCES_ALLOCATED -> BOOTSTRAPPING -> READY -> PRECREATION_RUNNING -> PRECREATION_PASS -> STAGE_EXT_RUNNING -> STAGE_EXT_PASS -> COMPLETED -> TEARDOWN_COMPLETE`

An allowed non-teardown state may transition to `FAILED`; after cleanup and verified absence it may transition from `FAILED` to `TEARDOWN_COMPLETE`. `FAILED` and `COMPLETED` are business-terminal outcomes, while `TEARDOWN_COMPLETE` is the infrastructure-terminal state. No state may be skipped or persisted until the predicate for that state has been demonstrated and its supporting facts have been durably recorded.

Reloading a manifest never recreates an in-process continuation capability. Recovery mode can only collect forensic facts, clean up, verify absence, and close the infrastructure record.

### Allocation is distinct from PostgreSQL readiness

`ALLOCATING` and `RESOURCES_ALLOCATED` describe container-engine work only: image identity, volume/network/container creation, labels, and host-port publication. A resource is not reported as `RESOURCES_ALLOCATED` until its creation and published port have been observed and persisted.

Only after successful allocation may the runner enter `BOOTSTRAPPING` and diagnose PostgreSQL. PostgreSQL startup, exact-version verification, readiness timeout, authentication, connection, and `SELECT 1` are distinct observations with distinct failure codes. A container creation or port-publication failure remains a tooling/allocation failure; it must not be collapsed into `POSTGRES_REACHABILITY_FAILURE`. PostgreSQL-specific classification is available only after the allocation boundary has been crossed.

Any exception before bootstrap retains the runner step, exception type and message, traceback, safe invocation metadata, last manifest state, known resources, and cleanup result under `DISPOSABLE_EXECUTION_TOOLING_BLOCKER`.

### Label-scoped cleanup and recovery-only operation

Every disposable container, network, and volume carries labels binding it to the canonical run slug, authorization SHA-256, and resource role. Cleanup acts only on manifest-named resources whose labels exactly match the manifest. A missing resource is recorded as absence; a missing or mismatched label causes cleanup to refuse deletion and fail closed. Cleanup never broad-scans or removes resources by a shared textual prefix alone.

Recovery loads the persisted manifest in a cleanup-only mode. It may identify partially allocated resources, remove label-matching resources, verify their absence, and persist remaining obligations. It cannot enter bootstrap, PRECREATION, Stage EXT, or any other business state. Recovery is therefore safe teardown and forensic completion, never resumption of a consumed run.

### Diagnostics are outside the retry sequence

Runner-environment validation uses the explicit classification `RUNNER_ENVIRONMENT_DIAGNOSTIC`, its own run identity, diagnostic authorization, fresh evidence root, manifest, ledger entry, and resources. It is not Retry 20, PRECREATION or Stage EXT evidence, a Phase 31.4 evidence run, or Phase 31.5.

The minimum real diagnostic contract is allocation of an isolated PostgreSQL 18.6 resource on a dynamic loopback port, a real connection, `SELECT 1`, teardown, and verified post-teardown absence. It does not contact live AdminApps. Technical remediation permits at most three diagnostic attempts, each independently recorded; it does not create an unlimited retry loop or consume an evidence-run authorization.

This ADR defines that validation contract but does not assert that a diagnostic, a connection, `SELECT 1`, teardown, or any test suite has run or passed.

### Runner sources are integrity-material

The reusable runner implementation, `backend/foundation/phase31_4_v2_5_disposable_runner.py`, and its repository-facing wrapper, `docs/governance/tools/phase31_4_v2_5_disposable_runner.py`, materially control authorization consumption, evidence location, state transitions, resource creation, failure classification, and cleanup. They therefore belong in the protected-source set of a successor integrity generation. They may not be left unprotected merely to avoid issuing a successor baseline.

V4 is not edited or silently rehashed. It remains the immutable historical predecessor and the current authority until a separately reviewed reconciliation creates and promotes a successor generation that records the runner and wrapper hashes, preserves the V4 predecessor relation, and cites this decision. Functional runner work performed before that reconciliation can at most support the conditional disposition `RUNNER_REMEDIATION_CODE_PASS / INTEGRITY_RECONCILIATION_REQUIRED`; it cannot authorize a new formal evidence run.

## Consequences

- Retry 19 remains `CONSUMED / FAILED`; its authorization, manifest, state, and evidence are not reopened or rewritten.
- Retry 19 Stage EXT remains `LIVE_REVALIDATION_PENDING`.
- V4 and the existing AdminApps endpoint reconciliation remain authoritative until a successor integrity reconciliation is approved.
- A future formal run must start from a new authorization, run ID, canonical evidence root, manifest, ledger record, and resources.
- Interrupted execution sacrifices automatic business resumption in favor of one-shot authorization safety, deterministic forensics, and cleanup-only recovery.
- Allocation failures and PostgreSQL runtime failures become separately attributable and auditable.
- The runner and wrapper add protected-source maintenance and require a successor integrity generation before use in a future formal evidence run.
- This decision does not execute Retry 20, request or consume its authorization, contact live AdminApps, or start Phase 31.5. Phase 31.5 remains `EXECUTION_HELD`.
- The governing operational status remains `LIVE_REVALIDATION_BLOCKED_REQUIRES_NEW_AUTHORIZATION`.
- No test result or runner-environment diagnostic result is established by this ADR; those require separate retained evidence.
