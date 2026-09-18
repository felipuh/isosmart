# Complete retained synthetic KnowledgeLayerRule lifecycle POC policy v1

- Policy ID: `complete-retained-synthetic-klr-lifecycle-poc-policy/v1`
- Policy identity: `57b377f3-760e-5db4-a990-c625bdb5739a`
- Version: `v1`
- Date: 2026-09-04
- Owner: ISO Smart Product Governance
- Status: **APPROVED FOR FUTURE ISOLATED EPHEMERAL POC ONLY**
- Operational authority now: **NONE**

## Decision

One future isolated PostgreSQL 18.6 POC may mechanically consume the exact
Phase 31.3 specification and create the new synthetic fixture through
Activation. Eligibility is conditional on fresh server-resolved authority,
enabled append-only capabilities, exact SOD, all precommit revalidation, and
`TRANSITIVE RETENTION CLOSURE / v1`. This policy creates no lifecycle state.

The experiment namespace is
`iso-smart/phase31.3/complete-retained-synthetic-lifecycle/v1`, UUID namespace
`05611a8a-f662-5b7f-ad24-c4df48d573ec`, and experiment ID
`a3f8fd64-af24-5b31-977a-bcaf8146c563`. IDs are the UUIDv5 of the namespace
UUID and the labels frozen in the machine specification, except release graph
children, which use frozen `foundation_0022_uuid-v1`.

## Closed scope

The only allowed path is:

```text
exact synthetic source and isolated support rows
-> exact root KnowledgeLayerRule creation
-> exact governed source-reference Application creating candidate s1
-> exact native Publication
-> exact first Activation (predecessor NULL)
-> closure compute/verify/export/live comparison
-> authorized teardown
-> offline verification
```

RuntimeAdoption, resolver invocation, runtime selection/effect, deployment,
production, staging, certification, normative authority, licensed material,
automatic learning and external business effects are prohibited. The future
adopter is an SOD placeholder only; no RuntimeAdoption ID exists.

## Synthetic and historical boundary

The source is synthetic, non-authoritative, non-normative, non-licensed,
test-only, non-production, non-certifiable, and has no external business
effect. No synthetic row represents ISO content. The minimum test-only
Standard, StandardEdition, Clause, RequirementControl and KnowledgeLayer
support graph is permitted solely because frozen schema requires it; every row
must carry the closed synthetic classification and be retained canonically.

Phase 29 Publication `e97576de-d4ef-520d-8592-d376ed401221` remains
`HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE` with
`RETENTION_CLOSURE_BREACH`. It is historical evidence only. Its candidate,
missing curation audit UUID, and every Phase 28.3/29/31 identity are prohibited
as inputs. Reconstruction, continuity, recovery, replacement and FK weakening
are forbidden.

## Actors and SOD

Proposer, reviewer, proposal approver, application authorizer, application
executor, curator, publisher, activator, adopter placeholder, repair authority
and capability-control authority are the distinct exact actors in the machine
specification. No collision is permitted. Publisher and activator differ;
activator and adopter differ. Executor and curator gain no release authority.
Repair cannot publish, activate or adopt. Capability control grants no
lifecycle execution authority. SOD is tested at admission and immediately
before commit.

## Authority and capability

Every privileged boundary uses fresh, server-resolved, actor-bound authority
at admission and immediately before commit. Activation requires active access,
verified MFA, global scope and
`qms.knowledge_layer_rule.activate`. Client-supplied, cached-only, expired,
revoked, actor/scope/policy-mismatched evidence denies. Retained external
authority is frozen provenance, never reusable live authority.

Application, Publication, Activation, RuntimeAdoption, repair and capability
control are independent append-only capability streams. RuntimeAdoption stays
disabled and unused. Disablement blocks new work without rewriting history;
re-enable requires a new successor decision. Admission and precommit checks
are mandatory for Application, Publication and Activation.

## Execution adapter

Migrations 0001--0023 remain byte-frozen and migration 0024 remains absent.
Because frozen migration 0021 allocates successor graph UUIDs dynamically, the
future POC must install only inside its isolated ephemeral database a reviewed
exact-ID Phase 31.4 execution adapter. The adapter is not a migration and must:

- accept only the frozen IDs/material in the Phase 31.3 specification;
- reproduce all migration 0021 validation, lock, atomicity, event, Outbox,
  curation-audit, Receipt and immutable-audit semantics;
- reject every selector other than exact ID and hash;
- expose no generic DML or arbitrary material arguments;
- use the dedicated NOLOGIN owner and fixed safe `search_path=pg_catalog`;
- revoke PUBLIC execution and grant only the exact LOGIN executor;
- make the specified candidate and Application graph IDs deterministic; and
- be removed with the ephemeral database after verified export.

Any behavioral deviation from migration 0021 is P1 and denies execution. The
native frozen Publication and Activation boundaries remain the reference
semantics; an exact wrapper may only strengthen retained-evidence validation
and deterministic binding.

## Retention closure and teardown

Closure is derived independently from the frozen schema/FK snapshot and
semantic registry. Every reachable dependency has exactly one disposition.
Mandatory FK targets and lifecycle evidence use
`RETAIN_FULL_CANONICAL_MATERIAL`; external authority uses
`EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE`. No mandatory member is
UUID-only. Unknown, missing, conflicting or multiple dispositions cause
`RETENTION_CLOSURE_BREACH`.

The future order is lifecycle execution, closure computation, verification,
export, independent live re-read, byte/material comparison, closure and match
assertions, pre-teardown disposition, teardown authorization, teardown, then
offline verification. Teardown is blocked unless both `closure_complete` and
`export_matches_live_graph` are true. A dual-control override can only produce
permanently non-rematerializable and operationally ineligible evidence; it can
never produce PASS.

## Transaction and failure semantics

Application, Publication and Activation each have one atomic transaction.
Activation atomically creates claim, Activation, event
`knowledge_layer_rule.activation_recorded` schema v1, Outbox and immutable
Audit, and creates zero RuntimeAdoption artifacts. Missing members are not
COMMITTED. Exact reconciliation results are `COMMITTED`, `NOT_COMMITTED`,
`ABANDONED`, or `INCONSISTENT`; timeout never transfers a claim and no blind
retry or automatic repair is permitted.

## Change control

The policy, machine specification, registry, closure specification and source
bytes are an immutable set once used. Corrections require an append-only
successor gate. Phase 31.4 may fill only explicitly declared fresh authority,
capability, transaction timestamp and live schema evidence slots; it may not
choose new identities, actors, material, policies, operations, dependencies,
dispositions, tests or teardown rules.
