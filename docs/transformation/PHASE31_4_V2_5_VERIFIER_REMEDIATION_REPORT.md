# Phase 31.4 V2.5 Verifier Remediation

Date: 2026-09-22
Verdict: **`VERIFIER_REMEDIATION_PASS`**
Status: **`CODE_REMEDIATED / LIVE_EVIDENCE_EXECUTION_PENDING`**

## Scope

This change hardens the Phase 31.4 V2.5 verifier only. No new retry was run, Retry 16 `PROMOTED` evidence was not edited, V2.4 was not edited, source artifacts were not edited, and Phase 31.5 remains `CONCEPTUALLY_ALIGNED / EXECUTION_HELD`.

## Remediation

- **Default-PASS removal and result propagation:** phase callbacks must return `PhaseExecutionResult`; returned `FAIL` remains `FAIL`, missing results fail closed, and unimplemented branches no longer return PASS.
- **Mandatory assertion/evidence enforcement:** `PhaseContract` requires an executor, named guarantee, required assertions, and evidence types before a mandatory phase can register.
- **Capture and readback model:** `LiveCapture` retains capture key, category, phase, retry, source service/operation, returned value, expected type, persisted readback, readback source, equality, and provenance. Synthetic values cannot be labeled upstream live.
- **Stage EXT and AdminApps provenance:** provenance kinds distinguish external AdminApps tenant/actor, local TenantProjection/UserProjection readbacks, ISO Smart Organization/Process, and synthetic harness data.
- **Native domain retention:** phase results retain output IDs, readback IDs, assertions, artifacts, hashes, inputs hash, and provenance fields for future serializers.
- **Event/outbox/audit verification:** `verify_event_outbox_audit` requires DomainEvent, TransactionalOutbox, and ImmutableAuditLog records linked by aggregate, trace, and payload hash.
- **Resolved graph and placeholders:** graph materialization consumes serialized captures/readbacks, rejects `captured:` and fixture placeholders, and rejects unresolved references.
- **Exact comparison:** comparison is independently recalculated and emits complete mismatch categories plus a hash of the actual materialized graph.
- **Security probes:** positive and negative probe records require principal, tenant, operation, expected/observed result, DB role, and status.
- **Transactions and teardown:** the session keeps phase results; teardown gate, teardown, and post-teardown verification are outside the business loop. Post-teardown evidence must independently observe containers, networks, volumes, DB reachability, and ports.
- **Immutability:** `AppendOnlyEvidenceStore` prevents overwrite and emits a per-retry SHA-256 manifest. Hash integrity is separate from provenance.

The `118/1664` contract is POC evidence and is not equivalent to proving the 63 source requirements or 17 onboarding stages.

## Tests

Focused command:

```text
backend/.venv/bin/python manage.py test foundation.test_phase31_4_v2_5_runtime foundation.test_phase31_4_v2_5_verifier_remediation
```

Result: **PASS, 29 tests**.

Full backend regression: **FAIL, 498 tests, 3 protected-source integrity-generation errors**. The failing checks are the existing protected-source/current-manifest guards for `phase31_4_v2_5_runtime.py` and the operational manifest chain. The runtime hash changed intentionally in this remediation; an unrelated `backend/backend/settings.py` worktree modification is also present. No integrity manifest was rewritten automatically, and no disposable PostgreSQL infrastructure was required or started.

## Remaining gaps

The implementation prepares the verifier and evidence contract. It does not create new live proof, populate a retry artifact directory, execute product operations, or authorize Retry 17. A separately approved disposable evidence run must still exercise the concrete database readbacks, event/outbox/audit queries, security/RLS probes, transaction probes, and resource absence checks.

## Governance status

- Phase 31.5: **`EXECUTION_HELD`**.
- Live retry executed: **`NO`**.
- Retry 17 created: **`NO`**.
- Product code outside verifier scope modified: **none**.
- Historical artifacts modified: **none**.
- Next authorized recommendation: **review and separately approve one disposable evidence-only run; do not execute it automatically.**
