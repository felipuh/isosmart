# Phase 21 — Governed Learning Foundation Implementation Report

- Date: 2026-08-24
- Scope: additive, inert governed-learning foundation only
- Authorization: `governed-learning-implementation-authorization/v1`
- Verdict: **PROMOTED — ZERO P0/P1 BLOCKERS**
- External effects/deployment: **ZERO**

## 1. Implemented boundary

Migration `0018_governed_learning_foundation` adds only:

- immutable tenant/Organization-scoped `LearningSignal`;
- immutable `LearningSignalEffectiveness` rows freezing every revision in the
  selected Effectiveness lineage;
- immutable, `governance_pending`-only `LearningProposal`;
- immutable exact `LearningProposalSignal` sample links;
- `learning_signal.created` schema v1 and `learning_proposal.created` schema v1;
- one transactional outbox record and one immutable audit append per committed
  command; and
- a distinct LOGIN, non-superuser, `NOINHERIT`, `NOBYPASSRLS`
  learning-governance principal.

There is no API, optimizer, proposal approval/application command, target writer,
automatic learning consumer, deployment, provider call or external workflow.

## 2. Blocking hardening results

| Requirement | Result | Database/runtime proof |
|---|---|---|
| A. Effectiveness derivation snapshot | PASS | exact selected check, action-execution lineage identity, revision, predecessor, outcome, creation time, current-leaf fact, derivation timestamp/policy/version and complete revision-by-revision lineage are frozen; later corrections do not rebind an old signal |
| B. Target version freeze | PASS | full exact target row JSON plus canonical SHA-256, target ID, lineage and version are frozen; stale/non-current/unpublished/hash-drift references fail closed |
| C. Global target inertness | PASS | tenant proposals referenced current global `ModelPolicy`, `AgentDefinition` and `KnowledgeLayerRule`; all three tables remained byte-state identical |
| D. No emergent auto-learning | PASS | 10 signals with repeated effective/ineffective/unknown/inconclusive outcomes produced zero changes to targets, Recommendation/runtime, retrieval, autonomy, execution authorization or normative state |
| E. No numeric derivation | PASS | no score/weight/average fields or categorical-to-numeric mapping; repository semantic scan passed |
| F. Proposal is not approval | PASS | the only database/model state is `governance_pending`; only created events exist |
| G. Protected target hashes | PASS | count plus ordered full-row JSON hashes were identical before/after signals, proposals, correction race and rollback matrices |
| H. No transitive escalation | PASS | catalog assertions denied INSERT/UPDATE/DELETE on global targets, normative catalog, Opportunity, ActionExecution and EffectivenessCheck; role attributes were non-elevated |
| I. Governance hash freeze | PASS | hashes below matched before and after the complete implementation matrix |

Additional PostgreSQL results:

- official isolated PostgreSQL 18.6: PASS;
- migration `0018` empty-history forward/reverse/forward: PASS;
- retained learning history downgrade: forward-only by design;
- signal and proposal forced rollback matrix: 14/14 PASS;
- proposal correction concurrency: one winner, one rejected fork PASS;
- tenant visibility A/none/B: `10/0/0` PASS;
- all four learning tables: `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` PASS;
- inherited Phase 13/14/16/17/19 matrices: PASS;
- scoped database, roles, container and volume teardown: PASS.

## 3. Frozen governance SHA-256

| Artifact | SHA-256 |
|---|---|
| `docs/governance/GOVERNED_LEARNING_POLICY_V1.md` | `7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec` |
| `docs/governance/GOVERNED_LEARNING_IMPLEMENTATION_AUTHORIZATION_V1.md` | `04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c` |
| `docs/governance/EFFECTIVENESS_CHECK_POLICY_V1.md` | `3e2f2b5b3f335bcb425c4b3d8043c2b541de56b0a7b14fbc63b8f48e4392758f` |
| `docs/adr/0003-postgresql-rls-and-evidence-graph.md` | `bd73915f84f0194c48b97dbefac66700df132ebb76d50fc3f1f20f047fa7e9d3` |
| `docs/adr/0005-governed-agent-runtime.md` | `e5265fc25b9da0622245e2d77ba5c33d928b066afca69f9af574b2cf285d207e` |
| `docs/adr/0009-transactional-domain-command-composition-least-privilege-executor.md` | `485f8943e2ddfdb2ff69d122a6535643debe17a2edc20d268b6fedb85ee99451` |
| `docs/adr/0011-effectiveness-assessment-governance-operational-readiness.md` | `d241d8378a6ea5c94652ca26e44c00a63710a2ca7e338d4ed6071d0e260cc542` |

The implementation did not edit any governance artifact or migration
`0001`–`0017`. The Phase 21 matrix recalculated the governance hashes before and
after execution and required exact equality.

## 4. Verification record

Executed successfully:

```text
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test foundation.tests --settings=backend.settings_test -v 1
FOUNDATION_HARNESS=.../postgres_phase21_harness.py python backend/foundation/postgres_foundation_gate.py
```

Results: Django check PASS; migration drift PASS; 82/82 foundation tests PASS;
PostgreSQL 18.6 Phase 21 and inherited regression matrix PASS; teardown PASS.

## 5. Promotion boundary

Promotion covers only inert proposal artifacts and provenance. It does not
authorize proposal approval, application, target version creation, target
mutation, scoring, automatic learning, cross-tenant aggregation, production use
or deployment. Any such capability requires a later Product Policy and separate
implementation authorization.
