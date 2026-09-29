# V8 operational diagnostic cycle — authorization review

## Verdict

`V8_OPERATIONAL_DIAGNOSTIC_CYCLE_AUTHORIZED` — `DIAGNOSTIC_ONLY_AUTHORIZATION`. Review only; no live execution.

## Diagnostic cycle ID

`Phase 31.4 V2.5 V8 Operational Diagnostic Cycle 1`

## V8 integrity

PASS. `docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V8.json`

SHA-256: `ed7bed0108e790c93e0c40625b215dde02ae25566b2397533b11b6aae7040946`. Current protected bytes match the reconciled baseline.

## Protected sources

28/28 PASS; missing 0; unexpected membership 0; no unregistered material source identified in the reviewed path. The historical V6 launcher is registered as GOVERNANCE_TOOL in V7 and excluded from the new cycle. No whole-repository integrity claim is made.

## Historical preservation

V2.4, V1–V8, provenance discontinuity, Retry 16–19, prior diagnostics and superseded V5 Retry20 authorization preserved. 428 historical/governance files were snapshotted and rechecked unchanged. Predecessor SHA references and the V5 authorization SHA match.

## State-machine gate

PASS (static and retained test evidence). READY → PRECREATION_RUNNING → PRECREATION_PASS → STAGE_EXT_RUNNING. READY invariants are enforced, failure enters FAILED and early Stage EXT is rejected. READY → COMPLETED belongs to minimal run_diagnostic; this cycle requires run_evidence.

## Runner gate

PASS (static): canonical slug, distinct diagnostic identity, atomic manifest, explicit history, scoped labels, bounded cleanup, no global prune, failure classification, cleanup-only recovery.

## Live executor gate

PASS for implementation presence and retained tests: bootstrap, migrations, roles/session configuration, both services/readiness, dynamic endpoint, authority, delivery, readbacks, Organization, Process, Stage EXT, CaptureBundle and runtime handoff. Live success remains unproven; operational readiness remains NOT_READY. Future PASS requires actual independent evidence and complete cleanup.

## Tests

Retained V8 evidence: focused 112/112 PASS; integrity 13/13 PASS; regression 559/559 PASS. No protected-source change relative to that reconciliation. Tests were not rerun in this review.

## Migrations

V2.4 23/23 and V2.5 24/24 hashes verified directly. Retained evidence: pending/new/fake/manual 0; makemigrations PASS. No database inspection or migration application performed during this review.

## Maximum attempts

3. Attempt 2 requires the concrete blocker from attempt 1; attempt 3 requires a distinct blocker found in attempt 2. One remediation and focused tests between attempts. No fourth attempt.

## Attempt 1 policy

CURRENT V8 BYTES AS-IS. No preemptive source patches.

## Primary target

STAGE EXT 6/6 + CAPTURE_BUNDLE_READY. Stop before the 33-phase clean retry; then teardown.

## Resource isolation

Fresh PostgreSQL 18.6 instances, networks, volumes, ports, databases, app processes and manifest per attempt. No historical reuse. Verify process/container/network/volume absence and all ports closed; retain evidence. No resources allocated by this review.

## Diagnostic authorization

Cycle-scoped DIAGNOSTIC_ONLY_AUTHORIZATION. Future eligible attempts require separate one-shot diagnostic inputs bound to the cycle, exact run identity and attempt number. This cycle artifact is not itself a runner-consumable attempt authorization.

## Retry 20 authorization created

NO. Current formal authorization remains NONE; historical V5 remains superseded and unconsumed.

## Retry 20 executed

NO.

## Phase 31.5

EXECUTION_HELD.

## Authorization artifact

`docs/governance/evidence/PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_CYCLE_AUTHORIZATION_V1.json`

SHA-256: `c8633d150784c23170585627b1bf3bd738bcf62197998d5ea8e7bd3d9d08aac9`

Review evidence: `docs/governance/evidence/PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_CYCLE_REVIEW_EVIDENCE_V1.json`

## Exact next step

Execute the V8 operational diagnostic cycle under this diagnostic-only authorization.
