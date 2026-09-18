# ISO SMART AI — Phase 31.2 unavailable historical transitive dependency governance decision gate

- Decision date: 2026-09-04 (`America/Costa_Rica`)
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: governance, architecture and retention design only

## 1. Verdict

`PHASE 31.2 — PROMOTED`

Promotion resolves governance only; it does not make Phase 29 rematerializable
or unblock Activation. ISO Smart preserves the historical Publication, records
`RETENTION_CLOSURE_BREACH`, classifies its retained package
`HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE`, and permanently denies that
package as operational input. Future progress uses a new, separately governed
synthetic lifecycle with closure proved before teardown, not Phase 29 recovery.

## 2. Entry baseline

Entry verdict was `PHASE 31.1 — NOT PROMOTED — AUTHENTIC RETAINED
CURATION-AUDIT EVIDENCE NOT FOUND`. It is final for current evidence; no repeat
forensic search occurred. Entry and exit state:

```text
CREATED=true
APPLICATION_GOVERNED=true
PUBLISHED=true
ACTIVATED=false
RUNTIME_ADOPTED=false
RUNTIME_EFFECTIVE=false
database_reconstructed=false
```

## 3. Frozen state

Migrations 0001--0023, ten sources, Phase 25.1--31.1 history, ADR-0013--0015,
existing policies, retained evidence and runtime/application code stayed
byte-frozen. Migration 0024 is absent. Only this report, a new append-only
policy and successor ADR-0016 are added.

## 4. Exact historical Publication

```text
candidate_id=01a0682b-dfc8-7b49-a601-f9bda29a70a5
lineage_and_rule_predecessor=da72872a-3f3c-5fcd-86f7-0ed33e453522
version=sN+1
full_material_hash=caa24592b509334af4cd60fd7d3f3c43989d864d3f1c6e6d0d3bf83a81871f81
semantic_fingerprint=8465956c1daf27a9838bc1bfb468af3f518ae255b4662b2df40e7b8648516192
lifecycle_hash=0adfd8075cc720140c6e1f0393d286799edac8f352efd9f1969816be83c51e52
publication_id=e97576de-d4ef-520d-8592-d376ed401221
```

Phase 29 proved the native Publication, claim, event, Outbox and governance
Audit, offline release graph, zero Activation/RuntimeAdoption and teardown.
That verdict remains true and unchanged.

## 5. Missing dependency

`normative.curation_audit.id = 12d811ab-c3b4-4615-8972-75008a36e327` is
missing. Frozen migration 0022 makes
`KnowledgeLayerRulePublication.curation_audit_id` a `NOT NULL UNIQUE` FK to it
with `ON DELETE RESTRICT`. The retained Publication has only its UUID, not the
canonical eight-field row.

## 6. Phase 31.1 forensic conclusion

Phase 31.1 found zero authentic complete retained occurrences. UUID references,
adjacent graph fields, harness code and a likely tuple are not retained row
material. Governance Audit `6a3ed87d-a992-4406-8ac8-233017301d35` and curator
evidence `471971df-986f-5a99-ad15-1838f5772e34` are distinct types. No new
authentic pre-teardown evidence was supplied.

## 7. Historical fact vs rematerialization distinction

```text
Historical publication fact: TRUE
does not imply Faithful rematerialization: TRUE
does not imply Activation eligibility: TRUE
does not imply Runtime adoption eligibility: TRUE
```

Here the first is true and the latter three are false. A downstream retention
defect is not proof that Publication never occurred.

## 8. Governance options matrix

| Option | Decision | Rationale |
|---|---|---|
| A — reconstruct the audit | REJECT | Fabricates history |
| B — relax/remove FK | REJECT | Weakens the promoted contract and falsifies closure |
| C — call it rematerializable | REJECT | Contradicts Phase 31.1 |
| D — historical but operationally non-rematerializable | SELECT | Preserves truth and fails continuation closed |
| E — new governed experiment with complete closure | SELECT AS CONTINUATION | New proof without rewriting Phase 29 |

## 9. Selected governance treatment

Keep Phase 29 immutable; append the classification and breach decision; permit
labelled historical visibility; deny all rematerialization-dependent use. No
grandfathering, candidate substitution or automatic repair is allowed.

## 10. Historical Publication classification

`HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE` means the historical fact is
proven at its retained level but the package cannot satisfy its frozen contract
faithfully and grants historical capability only. The classification and
breach-at-teardown fact are immutable. Newly supplied authentic evidence would
require a separate linked append-only assessment, never a rewrite.

## 11. Allowed historical uses

Allow historical report display, audit history, explicitly historical
analytics/research, unchanged export and cryptographic comparison of material
actually retained. Every view/export must expose the classification and breach.

## 12. Prohibited operational uses

Deny Activation or RuntimeAdoption input, deployment/release input, recovery
target, migration bootstrap, production bootstrap and live release seed. It
authorizes no staging, runtime or production use.

## 13. Reconstruction prohibition

Never regenerate the audit from code or adjacent facts, reuse its UUID for a
new row, substitute another record, merge separately typed evidence, rewrite a
manifest, or relax/reinterpret schema. Reproducibility is not retention.

## 14. Activation consequence

Activation from Publication `e97576de-d4ef-520d-8592-d376ed401221` is denied.
Do not retry Phase 31 against this package. Activation delta remains zero.

## 15. RuntimeAdoption consequence

Phase 32 remains blocked. RuntimeAdoption needs a new faithfully retained
Activation chain, `closure_complete=true` and a separately approved gate.

## 16. Superseding/new-experiment option

The preferred path is a new separately governed synthetic fixture: new source,
lineage, candidate and governance/lifecycle IDs; independently gated
Application, Publication and Activation; complete closure before teardown; no
Phase 29 continuity/recovery claim; no RuntimeAdoption. This phase does not
create or authorize its execution.

## 17. Transitive Retention Closure principle

`TRANSITIVE RETENTION CLOSURE / v1`: before ephemeral teardown, every immutable
relational and semantic dependency needed to verify, rematerialize, reconcile
or continue a retained graph must have canonical retained material or an
approved pre-teardown non-rematerializable disposition. No omission is implicit.
The intended future operation is part of the declaration.

## 18. Closure roots

Roots are `KnowledgeLayerRulePublication`, `KnowledgeLayerRuleActivation` and
`KnowledgeLayerRuleRuntimeAdoption`. Traversal starts at an exact root and uses
the schema/FK snapshot plus semantic preconditions for its operation version.

## 19. Relational dependency closure

Inspect `NOT NULL`, nullable-but-material, `UNIQUE`, composite and self-FKs and
delete behavior. Traverse claim/artifact/event/Outbox/Audit and target/source/
lineage relations required for integrity. Resolve cycles by stable identity.
A UUID alone is not full retention.

Publication's lower bound is rule, layer, curation audit, claim, event, Outbox
and Audit. Activation adds Publication closure and predecessor Activation when
present. Native RuntimeAdoption adds Activation/Publication closure and
predecessor adoption when present.

## 20. Semantic dependency closure

Registered edges include source material/provenance; application Proposal/
Delta/Review/Decision/Authorization/Receipt; curator evidence; policy; external
authority; capability; idempotency; compatibility/release configuration;
lineage/predecessor/SOD; manifests/dispositions; and asserted zero downstream
state. They are versioned rather than inferred ad hoc.

## 21. Dependency disposition taxonomy

Every reachable dependency receives exactly one:

- `RETAIN_FULL_CANONICAL_MATERIAL`;
- `REFERENCE_ONLY_ALLOWED_BY_APPROVED_POLICY`;
- `INTENTIONALLY_NON_REMATERIALIZABLE`; or
- `EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE`.

Reference-only cannot satisfy a mandatory rematerialization FK. Unknown,
missing, conflicting or multiple dispositions make closure incomplete.

## 22. Canonical retention contract

Full material requires exact identity, schema version, required fields,
canonicalization version, canonical bytes or lossless typed representation,
material hash, provenance, retention time, cross-links and integrity proof.
UUIDs, reports, test expectations, code and denormalized subsets do not qualify.

## 23. Pre-teardown closure gate

```text
compute_retention_closure()
verify_retention_closure()
export_retention_closure()
re_read_live_graph()
compare_export_to_live_graph()
```

Teardown authorization and promotion require `closure_complete=true`. Failure
closes teardown. A dual-control governance override may only produce an
immutable intentionally non-rematerializable result, never closure or
operational eligibility.

## 24. Post-teardown verification

Offline proof must show all members exist, hashes/cross-links match, no member
requires reconstruction, and every intentional omission was classified before
teardown. An unclassified missing mandatory member emits
`RETENTION_CLOSURE_BREACH`.

## 25. Retention closure breach semantics

The historical event may remain valid, but its evidence is incomplete for an
intended operation. History stays immutable; reconstruction is forbidden;
dependent continuation fails closed; governance/incident review is required.
No regeneration, fixture import, manifest rewrite, schema relaxation,
replacement, candidate switch or lifecycle advance occurs automatically.

Phase 29 receives this retrospective classification only through append-only
governance, without rewriting its verdict or evidence.

## 26. Operational consequence matrix

| Use | Result |
|---|---|
| Historical display/audit/analytics | ALLOW with classification |
| Unchanged export/retained-material comparison | ALLOW with breach metadata |
| Faithful import/rematerialization | DENY |
| Activation/RuntimeAdoption | DENY |
| Deployment/recovery/migration bootstrap | DENY |
| Production/live seed | DENY |

## 27. Capability separation

Historical verification, rematerialization, Activation and RuntimeAdoption are
distinct capabilities. Evidence or authority at one boundary supplies no
permission, presumption or fallback at another. `PUBLISHED=true` is not
operational authority.

## 28. Schema snapshot design

Retain migration-set hash; relevant types, nullability, unique/check/FK
constraints and delete behavior; FK topology; semantic-registry version; and
closure-algorithm version. This freezes which edges were mandatory at teardown.

## 29. Semantic dependency registry

A versioned registry maps artifact/operation versions to edge, cardinality,
target type, permitted disposition, canonical/hash rule and verification rule.
It covers authority, policy, source, predecessor, event/Outbox/Audit,
idempotency, capability, lineage and release/configuration. Changes are
additive and never reinterpret an exported closure.

## 30. External authority provenance

AdminApps decisions use `EXTERNAL_AUTHORITY_REFERENCE_WITH_FROZEN_PROVENANCE`:
decision ID, authority/context version, policy, actor, permissions, scope, MFA,
active access, server-resolved status, evaluation/expiry, decision hash and
lifecycle binding. This is not a local AdminApps row or reusable fresh
authority. AdminApps was not accessed.

## 31. Migration governance

Migrations 0001--0023 remain byte-identical; 0024 is absent. Evolution with
retained history must preserve graph meaning and cannot reinterpret missing
dependencies. Additive work requires separate approval and snapshot/registry
versions.

## 32. Evidence manifest evolution

Future manifests include closure version/root/intended operations; required,
retained, non-rematerializable, external and reference-only counts; member
dispositions/hashes/cross-links; closure digest; schema/FK snapshot hash;
registry/algorithm/verifier versions; verification state/time; and
`closure_complete`. Existing manifests remain unchanged.

## 33. Future POC rules

No future Publication/Activation/RuntimeAdoption POC promotes unless
`retention_closure_complete=true` before teardown. Teardown with incomplete
closure yields closure-breached, non-rematerializable evidence. This is
prospective and does not rewrite prior phases.

## 34. Phase 29 exact classification

```text
publication_id=e97576de-d4ef-520d-8592-d376ed401221
classification=HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE
retention_incident=RETENTION_CLOSURE_BREACH
historical_publication_verified=true
retention_closure_complete=false
faithful_rematerialization_allowed=false
activation_input_allowed=false
runtime_adoption_input_allowed=false
historical_reporting_allowed=true
reconstruction_allowed=false
```

Thus Publication occurred, the audit was not retained, and faithful
rematerialization under the frozen FK is unavailable.

## 35. Activation roadmap

Do not retry Phase 31. Authentic user-supplied evidence could enter a separate
append-only evidence gate, but the selected roadmap is a new synthetic
end-to-end design/authorization gate with closure enforced before database or
candidate creation.

## 36. RuntimeAdoption roadmap

Phase 32 stays blocked until a new Activation chain is faithfully retained,
has `closure_complete=true`, and receives an independent next-gate approval.

## 37. Governance Policy

Created
`docs/governance/HISTORICAL_LIFECYCLE_EVIDENCE_AND_TRANSITIVE_RETENTION_CLOSURE_POLICY_V1.md`,
ID `historical-lifecycle-evidence-transitive-retention-closure-policy/v1`,
status `APPROVED FOR GOVERNANCE / FUTURE RETENTION GATES`, SHA-256
`7d5ed091f0d2c163dbf7b6b276e2978afd8086083435002a87270d4f11948f8d`.
It grants no operational authority.

## 38. ADR

ADR-0016 records the architectural separation and mandatory closure decision.
ADR-0013--0015 are unchanged. ADR-0016 SHA-256 is
`8a6ceb5d210045f012bba6b0e5ace378da8cbfe4f77a20f34be6009e4d5f0745`.

## 39. Hash/integrity checks

- Migrations `23/23 MATCH`; 0024 absent.
- Authoritative sources `10/10 MATCH`.
- Phase 28.3 evidence bytes: `9272458c...7edd`, `b8a7c9d5...4536`, MATCH.
- Phase 29 evidence bytes: `fade372e...4b72`, `57633c70...ae9f`, MATCH;
  canonical hashes remain `51f0b207...f5366`, `fff3b225...158f1`.
- Phase 31/31.1 reports: `a2909cd4...4daa`, `fc0a4820...82e`, unchanged.
- Relevant prior policies/ADRs and protected runtime match the exact Phase 31.1
  inventories; no protected file changed.

Hash equality proves byte integrity, not semantic completeness by itself.

## 40. Validation and operational tests

- Phase 29 offline lifecycle verifier: PASS; seven-state output matches §2.
- Phase 31 offline regressions: `8/8 PASS`.
- Full Foundation dummy-backend suite: `136/136 PASS`.
- Django `4.2.22`, system check: PASS, zero issues.
- `makemigrations foundation --check --dry-run`: PASS, no changes.
- Phase 31.2 documentation structure/whitespace: PASS.
- PostgreSQL/operational lifecycle tests: `NOT EXECUTED`.

## 41. Git hygiene

Initial `git status --short` was captured. Pre-existing work and Sidebar line 28
whitespace were preserved. This phase changes only three append-only documents.
Nothing was staged, stashed, reset, reformatted or committed. `git diff --check`
retains only the known unrelated Sidebar warning; new files pass a separate
whitespace scan.

## 42. Zero effects

```text
database effects = 0
PostgreSQL effects = 0
Publication mutation effects = 0
Activation effects = 0
RuntimeAdoption effects = 0
runtime cutover effects = 0
production effects = 0
staging effects = 0
shared DB effects = 0
normative effects = 0
automatic learning effects = 0
external business effects = 0
historical reconstruction effects = 0
```

## 43. P0/P1/blocker status

```text
P0 = 0
P1 = 0
governance ambiguity blockers = 0
operational Activation blocker = RETENTION_CLOSURE_BREACH
Phase 32 = BLOCKED
```

The operational blocker intentionally remains; governance ambiguity does not.

## 44. Residual risks

Consumers could confuse `PUBLISHED=true` with operational eligibility unless
classification accompanies every view/export. A future registry could omit
semantic edges without independent review. Frozen external authority might be
misused as fresh authority. Teardown overrides could normalize incomplete
retention without dual control. Later implementation must prove the policy's
fail-closed controls.

## 45. Final verdict

`PHASE 31.2 — PROMOTED`

The Publication remains historically true; its audit remains unavailable; the
package is permanently non-rematerializable and operationally denied; no
reconstruction/FK weakening is allowed; and future progress requires a new
independently governed synthetic lifecycle with closure before teardown.
Activation and RuntimeAdoption remain false and blocked.

## 46. Exactly one continuation prompt

```text
NEXT_CODEX_PROMPT

ISO SMART AI — PHASE 31.3 — NEW COMPLETE RETAINED SYNTHETIC LIFECYCLE FIXTURE DESIGN AND AUTHORIZATION GATE — DESIGN ONLY

Work exclusively in /home/felipe/proyectos/isosmart. This is design/authorization only. Read AGENTS.md; Phase 25.1--31.2 reports; ADR-0013--0016; all governed-learning and KnowledgeLayerRule application/publication/activation/runtime-adoption policies; HISTORICAL_LIFECYCLE_EVIDENCE_AND_TRANSITIVE_RETENTION_CLOSURE_POLICY_V1; migrations 0008 and 0021--0023; retained Phase 28.3/29 evidence; release/evidence services; and audit/eventing, migration/deployment and threat-model designs. Run git status first and preserve unrelated work including frontend/src/components/Layout/Sidebar.jsx:28.

Keep Phase 29 Publication e97576de-d4ef-520d-8592-d376ed401221 classified HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE with RETENTION_CLOSURE_BREACH. Do not retry Phase 31, reconstruct normative.curation_audit row 12d811ab-c3b4-4615-8972-75008a36e327, modify historical evidence/history, reuse Phase 29 IDs, claim recovery/continuity, relax an FK, modify migrations 0001--0023 or create 0024. Preserve its lifecycle CREATED=true, APPLICATION_GOVERNED=true, PUBLISHED=true, ACTIVATED=false, RUNTIME_ADOPTED=false, RUNTIME_EFFECTIVE=false, database_reconstructed=false.

Design and decide authorization for one future new deterministic synthetic end-to-end lifecycle fixture only. Before any later database/candidate creation, specify a new namespace and IDs; exact non-official/non-normative/non-licensed/test-only source bytes/provenance; a new linear KnowledgeLayerRule lineage; exact Application Proposal/Delta/Review/Decision/Authorization/Receipt; separate Publication and Activation gates, actors, fresh authority, policies, capabilities, claims, events, Outboxes and Audits; no RuntimeAdoption; exact rollback, idempotency, concurrency, TOCTOU, SOD and least privilege; and zero runtime/normative/production/external effects.

Make TRANSITIVE RETENTION CLOSURE / v1 a precondition to execution, promotion and teardown. Derive closure for Publication and Activation roots from the exact schema/FK snapshot plus a versioned semantic registry. Cover all material FKs; candidate/source/provenance; application/publication predecessors; authority/policy/capability; claim/idempotency; event/Outbox/Audit; lineage; compatibility; manifests and dispositions. Give every dependency exactly one approved disposition and require exact canonical material, hashes and cross-links; no UUID-only mandatory dependency counts as retained.

Design manifests with closure version/root/intended operations, disposition counts and members, closure digest, schema/FK snapshot hash, registry/algorithm/verifier versions, verification status and closure_complete. Require the later POC before teardown to compute, verify and export closure, re-read the live graph and compare export to live material. Teardown and promotion fail closed unless closure_complete=true; any override yields explicitly non-rematerializable evidence, never operational eligibility. Offline verification must require no reconstruction and emit RETENTION_CLOSURE_BREACH for an unclassified missing mandatory dependency.

Do not create PostgreSQL, containers, roles, volumes, DSNs, schemas, migrations, candidates or lifecycle records; change runtime; or call external systems in Phase 31.3. Do not access AdminApps, MedSupplier, providers, production, staging, shared databases or deployment. Phase 32 remains blocked. Create only append-only design/authorization documentation if the new fixture and closure contracts are exact with P0=0/P1=0. Run proportional offline/docs/hash/Django validation, mark PostgreSQL tests NOT EXECUTED, report zero effects, and return exactly one subsequent prompt authorizing at most an isolated ephemeral creation-through-Activation POC with closure proved before teardown and still no RuntimeAdoption.
```

| Component/decision | State | Evidence | Risk/next action |
|---|---|---|---|
| Phase 29 Publication fact | VERIFIED / PRESERVED | Hash-valid retained release graph | Always expose historical-only classification |
| Missing curation audit | NOT RETAINED | Phase 31.1 complete-row count 0 | Never reconstruct |
| Rematerialization | DENIED | Frozen mandatory FK | No Phase 31 retry |
| Activation/RuntimeAdoption | DENIED / BLOCKED | Incomplete closure; zero effects | Require new faithfully retained chain |
| Classification | APPROVED | Policy v1 + ADR-0016 | Append-only |
| Retention closure | APPROVED FOR FUTURE GATES | Algorithm, taxonomy, manifests | Implement only after authorization |
| Safe continuation | NEW EXPERIMENT DESIGN | New IDs/lineage, no recovery | Phase 31.3 only |
| Frozen baseline | PASS | 23 migrations, 10 sources, evidence/runtime unchanged | Keep 0024 absent |
| Validation | PASS / OPERATIONAL NOT EXECUTED | 8/8, 136/136, Django checks | PostgreSQL prohibited here |
| Phase 31.2 | PROMOTED | P0=0, P1=0 | Grants no operational authority |
