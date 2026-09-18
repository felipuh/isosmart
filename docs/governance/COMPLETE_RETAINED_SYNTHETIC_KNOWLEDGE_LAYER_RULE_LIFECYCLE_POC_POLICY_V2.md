# Complete retained synthetic KnowledgeLayerRule lifecycle POC policy V2

Status: approved architecture for future clean Phase 31.4 retry eligibility
only. No database or lifecycle execution is authorized by this document.

This policy adopts ADR-0018 and the exact machine contract
`phase31.4.4-row-level-execution-contract/v2` for experiment
`a3f8fd64-af24-5b31-977a-bcaf8146c563`. The V2 contract exclusively supersedes
the Phase 31.3 root-target, Delta, B2 and B3 operational expectations. Phase
31.3 remains historical design evidence and ADR-0017 remains unchanged.

## Authorized future scope

One isolated, ephemeral PostgreSQL 18.6 proof may later execute the exact V2
row universe in freeze order. It may create only the declared non-official,
synthetic, non-normative fixture; perform one controlled
`opportunity.defer_evaluation`; record the resulting effectiveness and learning
provenance; apply the exact source-reference correction; publish; establish
checkpoint/B2/B3/final closure; and activate only after publication eligibility.

The isolated synthetic catalog fixture is recordkeeping provenance. It cannot
change a runtime selector, production ModelPolicy or AgentDefinition, invoke a
provider/tool/model, deploy, claim normative authority, cause automatic
learning, or create RuntimeAdoption.

## Binding contracts

- Row universe, identities, per-field taxonomy, producer and RLS/privilege
  matrices: `PHASE31_4_4_ROW_LEVEL_EXECUTION_CONTRACT_V2.json`.
- Semantic dependency edges:
  `PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json`.
- Expected fixed-point closure:
  `PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json`.
- Support producer security and transaction composition:
  `PHASE31_4_4_SUPPORTING_FIXTURE_PRODUCER_CONTRACT_V1.md`.

All non-time business material is fixed at Freeze 0. Later values must be
execution-derived persisted output or fresh external authority under the exact
field taxonomy. Blank text, unknown fields, unknown freezes, arbitrary producer
arguments and predicted future digests fail closed.

## Admission and replay

Root bootstrap, Publication and Activation use the typed admissions named in
the machine contract. Publication admission cannot contain B2, B3, closure or
Activation facts. Publication eligibility is a separate postpublication state.
Activation requires it.

Native and governed hashes are retained separately. Original authority is
immutable. A later fresh authority may retrieve/reconcile a prior immutable
result but may not replace the original authority. Changed governed material is
a conflict.

## Retention and teardown

Every local dependency is retained as full canonical material before teardown.
External authority is retained with frozen provenance. Closure is computed to a
fixed point from the live schema/FK snapshot and registry V2 before teardown
authorization. Teardown removes the exact ephemeral functions, policies and
roles. Phase 29 identities are never reconstructed, bootstrapped or reused.

