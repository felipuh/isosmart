# ADR-0018: Row-level execution-ready V2 contract

- Status: Accepted for a future clean Phase 31.4 retry only
- Date: 2026-09-09
- Experiment: `a3f8fd64-af24-5b31-977a-bcaf8146c563`

## Context

The Phase 31.3 package fixed identities too early, treated execution-derived
PostgreSQL values as pre-execution constants, omitted the legal supporting
LearningSignal path, and mixed native release facts with outer governance
admission. Phases 31.4–31.4.3 diagnosed these defects but did not provide a
closed successor. Phase 29 remains historical, non-rematerializable evidence
and is not an operational dependency.

## Decision

Adopt `execution-ready-v2` and Model B. A future value is executable when it is
either fixed at Freeze 0 or uniquely produced from exact frozen/live inputs by
a named producer at a named later freeze. Native timestamps and UUIDv7 audit
identities therefore need not be predicted; they must be retained before any
consumer uses them.

The authoritative execution unit is `(qualified_table, primary_key)`. The
complete future universe, field taxonomy, producer matrix, security/RLS
matrix, artifact schemas, registry, closure rule and freeze graph are in
`PHASE31_4_4_ROW_LEVEL_EXECUTION_CONTRACT_V2.json`.

The exact synthetic support path is isolated from runtime adoption. It creates
one published synthetic ModelPolicy and AgentDefinition, complete AgentRun
input/recommendation provenance, AgentDecision, ActionPlan, DryRun, human
Approval, ExecutionAuthorization, one controlled
`opportunity.defer_evaluation`, receipt, evidence, first-revision human-review
EffectivenessCheck, LearningSignal and LearningProposalSignal. It performs no
provider/tool call, deployment, runtime selection, production mutation,
normative adoption or automatic learning.

The producer is exact-fixture-only and parameterless. It accepts only the
declared experiment. It uses per-operation transactions because
`trusted_tenant_context` rejects an active outer transaction. Every operation
owns its connection and `BEGIN`, binds tenant context, validates, writes only
declared rows, revalidates immediately before commit, commits, then retains
canonical outputs before downstream use.

The producer owner is NOLOGIN, NOSUPERUSER, NOINHERIT, NOBYPASSRLS and is not a
table owner. The executor is LOGIN with the same negative attributes and is
also not an owner. Both have a fixed `pg_catalog` search path, no generic DML,
no dynamic SQL, no role escalation and no PUBLIC EXECUTE. Exact ephemeral RLS
policies bind the single fixture tenant, deny cross-tenant access and are
removed at teardown.

Migration 0022 remains unchanged. Its release children use MD5 of
`parent_uuid_text || ':' || suffix`, formatted with literal version nibble `4`
and variant nibble `8`; they are `NATIVE_RELEASE_CHILD_ID`, not UUIDv5.
Publication/Activation and their Claim deliberately reuse an ID across
different tables and are checked by qualified identity. Immutable audit rows
retain native UUIDv7 output identity.

ADR-0017 remains byte-identical and applies only to its seven Application
outputs. This ADR authorizes the enumerated deterministic identity replacements
in the V2 contract where exact preallocation is required. It does not broaden
ADR-0017.

Root bootstrap has its own pre-Application admission. The root is created as a
draft, published by a separately governed native operation, committed, and
reread in two independent read-only transactions. Only then is the complete
13-field PostgreSQL target representation canonicalized and frozen. No target
hash is predicted.

Publication and Activation each have two distinct hashes: the unchanged native
operation hash and an outer governed-admission hash. Publication admission is
pre-publication only. Checkpoint, B2, B3 and final Publication closure follow
native Publication. Activation admission requires the distinct
`publication-eligible-for-activation/v1` state and final Publication closure.

Original committed authority provenance is immutable. Replay authority is a
fresh request provenance used only for authorized retrieval or reconciliation.
The same native hash with different governed material is a conflict unless the
new request is expressly limited to retrieving the immutable prior result; it
never substitutes original provenance.

The freeze order is Freeze 0, 1, 1.5, 2, 3, 4, 5, 6, 7a, 7b, 7c, 7d, 7e, 8,
and 9. Closure is the fixed point of the live schema/FK snapshot and semantic
registry V2. Local dependencies retain full canonical material; fresh external
authority retains a frozen provenance reference.

## Consequences

This decision authorizes only eligibility for a future isolated PostgreSQL
18.6 retry. It does not authorize database creation or execution in this phase,
does not authorize RuntimeAdoption, and does not advance to Phase 32. The old
root, B2 and B3 digests are superseded pre-execution expectations that were
never executed. The old Delta remains historical and non-executable.

