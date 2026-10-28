# Historical lifecycle evidence and Transitive Retention Closure policy v1

- Policy ID: `historical-lifecycle-evidence-transitive-retention-closure-policy/v1`
- Version: `v1`
- Date: 2026-09-04
- Owner/system authority: ISO Smart Product Governance
- Nature: versioned, append-only, non-normative Product/Governance Policy
- Status: **APPROVED FOR GOVERNANCE / FUTURE RETENTION GATES**
- Operational authority: **NONE**

## 1. Purpose

This policy separates historical truth, evidence completeness, faithful
rematerialization, Activation eligibility and RuntimeAdoption eligibility. It
governs incomplete retained lifecycle evidence and defines prospective
`TRANSITIVE RETENTION CLOSURE / v1` for Publication, Activation and
RuntimeAdoption proof-of-concept environments.

It does not authorize reconstruction, a Phase 31 retry, Publication mutation,
Activation, RuntimeAdoption, runtime use, production, staging, deployment,
database creation or migration.

## 2. Governing principles

```text
historical verification capability
!= rematerialization capability
!= Activation capability
!= RuntimeAdoption capability
```

No capability or authority is inherited across those boundaries.

Historical truth, evidence completeness, rematerialization eligibility and
operational lifecycle eligibility are distinct states and MUST NOT be
conflated. Ephemeral lifecycle evidence is complete only when every mandatory
transitive relational and semantic dependency required for the intended future
operation has a governed retained disposition.

## 3. Historical classifications

`HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE` means all of the following:

- the historical lifecycle fact is proven at its retained evidence level;
- that retained evidence and the classification decision remain immutable;
- at least one mandatory dependency needed by the applicable frozen contract
  is not present as authentic canonical retained material;
- faithful import or rematerialization from that evidence package is denied;
- missing material must not be inferred, regenerated, replaced or synthesized;
- the artifact is historical/read-only and is not an operational predecessor,
  recovery target, migration bootstrap source or live release seed; and
- it grants no Publication, Activation, RuntimeAdoption, runtime, production or
  deployment authority.

The classification is append-only. Authentic newly supplied evidence may be
assessed only through a separately approved evidence-ingestion gate and a new
linked evidence package/decision. It never rewrites the original package or
erases the historical fact that its closure was incomplete at teardown.

## 4. Phase 29 binding decision

Exact Publication `e97576de-d4ef-520d-8592-d376ed401221` is classified:

```text
classification = HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE
retention_incident = RETENTION_CLOSURE_BREACH
historical_publication_verified = true
retention_closure_complete = false
faithful_rematerialization_allowed = false
activation_input_allowed = false
runtime_adoption_input_allowed = false
historical_reporting_allowed = true
reconstruction_allowed = false
```

The missing member is historical
`normative.curation_audit.id = 12d811ab-c3b4-4615-8972-75008a36e327`, required
by the frozen `NOT NULL UNIQUE ON DELETE RESTRICT` Publication foreign key.
Phase 29's Publication verdict is not invalidated. Phase 31.1's absence finding
is not weakened. Both remain true.

## 5. Allowed and prohibited uses

| Use | Decision | Condition |
|---|---|---|
| Historical report display | ALLOW | Label the classification and breach |
| Immutable audit history | ALLOW | Preserve provenance and do not imply closure |
| Research/analytics | ALLOW | Historical/non-operational context only |
| Evidence export | ALLOW | Export unchanged with classification |
| Cryptographic comparison | ALLOW | Compare only material actually retained |
| Activation input/predecessor | DENY | Mandatory graph material is missing |
| RuntimeAdoption input | DENY | No faithful Activation chain exists |
| Deployment/release input | DENY | No operational eligibility |
| Recovery target | DENY | Recovery would require reconstruction |
| Migration bootstrap source | DENY | Frozen FK graph cannot be satisfied faithfully |
| Production/live release seed | DENY | Historical proof grants no runtime authority |

## 6. Reconstruction prohibition

A missing historical dependency must never be supplied by a likely tuple,
fixture, deterministic helper, adjacent evidence, operator assertion, new row
under the same UUID, replacement audit, manifest rewrite, relaxed constraint or
schema reinterpretation. Reproducibility is not retention. A breach never
triggers automatic repair or candidate substitution.

## 7. TRANSITIVE RETENTION CLOSURE / v1

Before teardown of an ephemeral governed lifecycle environment, every
immutable relational dependency required to faithfully verify, rematerialize,
reconcile or continue the retained graph MUST itself be retained canonically
or be explicitly classified as intentionally non-rematerializable before
teardown. No implicit omission is permitted.

Closure is evaluated against both the exact schema contract and a versioned
semantic-dependency registry. Its intended future operation is explicit:
historical verification, rematerialization, reconciliation, Activation,
RuntimeAdoption or another approved purpose. A weaker intended purpose must not
be used later as authority for a stronger purpose.

## 8. Closure roots and minimum edge families

### Publication root

Root: `KnowledgeLayerRulePublication`.

Relational edges include the exact KnowledgeLayerRule, KnowledgeLayer,
curation audit, governance claim, governance event, Outbox and immutable Audit.
Semantic edges include candidate/source material and provenance, lineage and
predecessor graph, application Proposal/Delta/Review/Decision/Authorization/
Receipt graph, curator evidence, publisher authority, policy, capability
decision, idempotency material, retained manifests and disposition.

### Activation root

Root: `KnowledgeLayerRuleActivation`.

Relational edges include exact Publication and all of its closure, exact rule
and layer, predecessor Activation when present, claim, event, Outbox and Audit.
Semantic edges include compatibility material, activator authority and
separation of duties, policy, capability decision, idempotency/predecessor
state, retained manifest and disposition, plus proof of zero RuntimeAdoption
when that is the asserted lifecycle state.

### RuntimeAdoption root

Root: `KnowledgeLayerRuleRuntimeAdoption`.

For native adoption, relational edges include exact Activation, Publication
and their complete closures, rule, layer, predecessor adoption when present,
claim, event, Outbox and Audit. Semantic edges include exact release/config
material and hash, adopter authority/SOD, environment or scope, policy,
capability decision, idempotency, runtime acknowledgement, retained manifest
and disposition. A separately approved truthful legacy-bootstrap kind has its
own explicit null-Activation contract and may never assert historical
Activation.

The lists above are lower bounds. The closure engine must derive all enforced
edges from the schema snapshot and all registered semantic preconditions; it
must not rely on a hand-maintained list alone.

## 9. Relational closure algorithm

For each root and reachable member, the future design must:

1. freeze the root identity, intended operation and schema/FK snapshot;
2. traverse every `NOT NULL`, nullable-but-material, `UNIQUE`, self-referential
   and composite foreign key in deterministic order;
3. traverse event/Outbox/Audit, claim/idempotency, authority/provenance,
   exact-source and predecessor/successor links required by constraints or
   verification semantics;
4. merge the registered semantic edges for the artifact type/version;
5. assign exactly one approved disposition to every reached dependency;
6. reject missing, conflicting, multiply classified or unclassified mandatory
   dependencies;
7. canonicalize, hash and cross-link the resulting closure manifest; and
8. re-read the live graph and compare it byte/material-wise before teardown.

Cycles and repeated nodes are resolved by stable identity, never by truncating
traversal. A UUID reference without its governed material is not closure.

## 10. Closed dependency-disposition taxonomy

Every dependency reachable from a retained lifecycle root receives exactly one
of these dispositions:

- `RETAIN_FULL_CANONICAL_MATERIAL`: local immutable material required for the
  intended verification/rematerialization/continuation.
- `REFERENCE_ONLY_ALLOWED_BY_APPROVED_POLICY`: a reference is sufficient only
  where an identified approved policy explicitly says the target material is
  unnecessary for the declared intended operation. It is prohibited for a
  mandatory FK row needed for rematerialization.
- `INTENTIONALLY_NON_REMATERIALIZABLE`: declared before teardown; preserves a
  historical package while explicitly denying later operations that require
  the omitted material.
- `EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE`: the source system is
  external and the complete frozen decision provenance required below is
  retained locally without claiming a local source-system row.

No default, inferred or `UNKNOWN` disposition is allowed at teardown.

## 11. Canonical material contract

`RETAIN_FULL_CANONICAL_MATERIAL` requires exact object/row identity, schema
version, all required fields, canonicalization version, canonical bytes or an
equivalent lossless typed representation, material hash, source/provenance,
retention timestamp, bidirectional cross-links and successful integrity
verification. A UUID, narrative, code path or denormalized subset is
insufficient.

## 12. External authority provenance

`EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE` requires at minimum:
authority decision ID, authority/context version, policy, actor, permissions,
scope, MFA state, active-access state, server-resolved status, evaluation time,
expiry, decision/material hash and the lifecycle operation to which it binds.
It is an external frozen provenance record, not a locally rematerialized
AdminApps row and not reusable fresh authority.

## 13. Semantic-dependency registry

A versioned registry must declare, for each artifact kind and operation
version, required semantic edges, cardinality, expected artifact type,
disposition classes allowed, canonicalization/hash rule and verification rule.
It must cover at least authority, policy, exact source evidence, application or
publication predecessor, event/Outbox/Audit graph, idempotency claim,
capability decision, lineage predecessor/successor and release/config material.
Registry changes are additive/versioned and cannot reinterpret an old closure.

## 14. Schema snapshot

Every closure export must retain a canonical snapshot containing the migration
set hash, relevant table/column types, nullability, unique/check/FK constraints
including delete behavior, FK topology, semantic registry version and closure
algorithm version. This snapshot determines which dependencies were mandatory
at teardown and prevents a future schema from reinterpreting old evidence.

## 15. Pre-teardown gate

Future lifecycle POCs must execute conceptually:

```text
compute_retention_closure()
verify_retention_closure()
export_retention_closure()
re_read_live_graph()
compare_export_to_live_graph()
```

Teardown authorization requires `closure_complete=true`. Promotion also
requires that value before teardown. If false, teardown fails closed. An
explicit dual-control operator/governance override may permit teardown only by
creating immutable evidence that the result is
`INTENTIONALLY_NON_REMATERIALIZABLE`; it cannot set closure complete or grant
operational eligibility.

If teardown nevertheless occurs with incomplete or unclassified closure, the
result is automatically a `RETENTION_CLOSURE_BREACH` and
`HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE` where its historical root is
otherwise proven.

## 16. Post-teardown verification

Offline verification must prove every required member exists, canonical hashes
and cross-links match, no verification requires database reconstruction, and
every non-rematerializable omission was explicitly classified before teardown.
Discovery after teardown of an unclassified missing mandatory dependency emits
`RETENTION_CLOSURE_BREACH` and fails all continuation gates closed.

## 17. RETENTION_CLOSURE_BREACH

This condition means the historical event may remain valid while its evidence
package is incomplete for an intended future operation. History and retained
artifacts remain immutable; reconstruction is prohibited; rematerialization-
dependent continuation fails closed; incident/governance review is required.
It never automatically regenerates a dependency, imports a fixture, rewrites a
manifest, relaxes schema, chooses replacement evidence, changes candidate or
advances the lifecycle.

## 18. Evidence-manifest vNext obligations

Future manifests must include closure version, root type and ID, intended
future operations, required/retained/non-rematerializable/external/reference-
only counts, closure digest, schema/FK snapshot hash, semantic-registry and
algorithm versions, verification status, verifier version, verification time,
and all member identities/dispositions/material hashes/cross-links.
`closure_complete` is true only when counts and verification agree and no
unclassified required dependency exists. Existing manifests are unchanged.

## 19. Migration and change governance

Migrations 0001–0023 remain byte-frozen and 0024 remains absent for this policy.
Future schema evolution in the presence of retained history must preserve the
meaning and topology of the historical graph and must not reinterpret a
missing dependency. Any additive evolution or new experiment needs separate
approval and a new versioned schema snapshot/registry.

## 20. Future POC and roadmap rule

No future Publication, Activation or RuntimeAdoption POC can promote unless
`retention_closure_complete=true` before teardown. Phase 31 must not be retried
against the Phase 29 package. Phase 32 remains blocked.

The preferred continuation is a new, separately governed, synthetic end-to-end
lifecycle experiment with a new deterministic lineage and fixture, complete
closure retained before teardown, independent Application/Publication/
Activation gates, no Phase 29 IDs or continuity/recovery claim, and no
RuntimeAdoption. Phase 31.2 does not authorize or create that experiment.

## 21. Change control

This policy is immutable once referenced. Corrections or extensions require a
successor policy and append-only decision. Nothing in this policy may be read
as authorization to modify historical evidence, create a database, activate,
adopt, deploy or use the classified Publication operationally.
