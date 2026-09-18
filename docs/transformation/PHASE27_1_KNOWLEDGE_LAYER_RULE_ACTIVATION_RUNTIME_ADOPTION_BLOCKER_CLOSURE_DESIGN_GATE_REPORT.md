# ISO Smart AI — Phase 27.1 KnowledgeLayerRule activation/runtime-adoption blocker closure design gate

- Date: 2026-09-02
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: design, governance, data-model and security blocker-closure gate
- Runtime/schema/database/target/external effects: **ZERO**
- Migration 0022: **ABSENT**
- Verdict: **PHASE 27.1 — PROMOTED**
- Authorization meaning: **INERT FOUNDATION IMPLEMENTATION GATE ONLY**

## 1. Verdict

**PHASE 27.1 — PROMOTED.** The Phase 27 blocker is closed at design level by
an exact additive contract that separates created, published, activated and
runtime-adopted facts. There are zero P0/P1 design blockers to a future inert
foundation implementation.

Promotion does not authorize migration 0022 now, publication, activation,
runtime adoption, runtime cutover, production, deployment, another target,
another learning operation, cross-tenant learning, automatic learning,
normative mutation or external effects.

## 2. Exact Phase 27 blocker

Current runtime requires an exact caller-supplied KnowledgeLayerRule ID, so no
latest-wins bug exists. The blocker is that the only additional predicate is
`status=published`: publication itself establishes runtime eligibility. There
is no independent Activation or RuntimeAdoption artifact, authority, lineage or
exact adoption ID.

## 3. Current publication behavior

Repository answers A–H:

| Question | Verified answer | Evidence |
|---|---|---|
| A. What does published mean? | An exact draft row is locked, changed to `status=published`, assigned `published_at`, and receives `knowledge_layer_rule.published` curation audit in one transaction. Source edition publication is enforced by the database guard. Published rows are immutable. | `models.py:467-502`; `knowledge_layer.py:143-162`; migration 0009 rule guard |
| B. What makes it runtime eligible? | Exact ORM queries use `id=<supplied ID>, status=published`; database triggers independently require that exact row status for RecommendationBasis and AgentRunInput. | `recommendation.py:139-143`; `agent_runtime.py:306-310`; migrations 0010/0011 validators |
| C. Does runtime select exact IDs? | Yes. Both command inputs contain an exact `knowledge_layer_rule_id`; no version/lineage selector is used. | `recommendation.py:69-76,132-143`; `agent_runtime.py:251-259,299-310` |
| D. Where is the ID chosen? | Upstream caller-supplied `basis[]`/`inputs[]` dictionaries. The repository contains no runtime chooser that resolves a lineage to an ID. | same command signatures and loops; repository-wide search |
| E. When is publication checked? | At service admission/selection and again at database insert execution for frozen basis/input rows. | ORM queries plus migration triggers |
| F. Active/current/runtime pointer? | None for KnowledgeLayerRule. `status/published_at` are the only row lifecycle state; “head” is derived only for curation/governance. | model/search evidence |
| G. Multiple published revisions? | Yes. No one-published-per-lineage constraint exists; Phase 9 harness publishes successive rule1/rule2/rule3 revisions. | migration 0009 DDL; `postgres_phase9_harness.py:160-195` |
| H. Can unpublished revisions be referenced by runtime? | No new AgentRunInput, RecommendationBasis or Binding can reference one because service and DB guards reject it. Drafts may appear in non-runtime learning application history/governance, including Phase 26 compensation targeting, which does not make them runtime eligible. | migrations 0009/0010/0011 and Phase 26 contract |

## 4. Current runtime resolution

Current resolution is:

```text
caller basis/input.knowledge_layer_rule_id
  -> SELECT exact KnowledgeLayerRule(id, status='published')
  -> freeze exact rule FK/version in AgentRun/Recommendation provenance
```

There is no `ORDER BY version`, `MAX(version)`, newest timestamp, lineage-head
or most-recent-published fallback. Publication is checked at both ORM and DB
write boundaries, but activation/adoption is checked nowhere because it does
not exist.

## 5. Four-state model

```text
VERSION_CREATED
  -> VERSION_PUBLISHED
  -> VERSION_ACTIVATED
  -> RUNTIME_ADOPTED
```

Every arrow requires a separately authorized immutable artifact and does not
trigger the next. The facts are intentionally non-equivalent.

## 6. Version-created semantics

A revision exists with exact lineage, predecessor, version and full-row hash.
It is `draft,published_at=NULL`, not approved catalog content, not activatable
and not runtime eligible. Creation does not copy or repoint bindings/provenance.

## 7. Publication semantics

Publication is global curation approval of exact catalog content. Future native
publication creates one immutable `KnowledgeLayerRulePublication` and updates
the compatibility `status/published_at` projection atomically. Publication
alone leaves activation and runtime configuration unchanged.

One successful native publication record exists per exact revision; exact
replay returns it. Multiple historically published revisions may coexist.
Denied attempts are audits, not competing successful decisions.

## 8. Activation semantics

Activation is a new immutable `KnowledgeLayerRuleActivation` authorizing an
exact published revision/hash as eligible for release consideration in the
fixed global rule-lineage scope. It has independent authority, policy,
predecessor, reason, compatibility evidence, trace and time. It neither mutates
the rule nor proves runtime use.

## 9. Runtime-adoption semantics

Runtime adoption is a new immutable
`KnowledgeLayerRuleRuntimeAdoption` representing an exact release/configuration
transition to one activated revision. It requires its own authority and exact
predecessor adoption. Activation never switches runtime automatically.

## 10. RuntimeAdoption artifact design

Required fields are adoption ID/kind/operation version; exact global
lineage/scope; rule ID/version/full hash/semantic fingerprint; exact activation
and publication evidence; predecessor adoption; AdminApps authority decision;
release/configuration reference/hash; compatibility/governance hashes; reason,
optional incident and source-backed `effective_from`; idempotency/material
hash; trace/timestamps; event/outbox/audit IDs.

`RuntimeAdoption` is the sole adoption source of truth. A second Receipt would
be redundant. An admitted operation claim is reconciliation evidence, not a
second adoption authority.

## 11. Activation artifact design

Required fields are activation ID/operation version; publication evidence;
exact rule/KnowledgeLayer/lineage/version/hashes; fixed global scope; exact
predecessor activation; release-policy and compatibility hashes; independent
actor/authority decision; reason, optional source-backed `effective_from`,
idempotency/material hash, trace/timestamps and event/outbox/audit IDs.

A mutable `is_active` flag alone is prohibited.

## 12. Append-only history

Publication, activation, adoption, recovery, capability disablement and
claim disposition are append-only. Old records are never updated, deleted,
unpublished, deactivated or relabeled. Status projections cannot replace the
authoritative history.

## 13. No pointer rewind

Recovery never silently sets `runtime_rule_id=old_revision_id`. It creates a
new governed adoption, changes trusted release configuration to that exact new
adoption ID, and retains before/after adoption and incident provenance.

## 14. Target lineage vs adoption lineage

```text
rule lineage:      vN -> vN+1 -> vN+2
adoption lineage:  A1 -> vN; A2 -> vN+1; A3 -> vN (recovery)
```

Rule predecessor describes content history. Adoption predecessor describes
runtime release history. Neither substitutes for the other.

## 15. Exact-ID resolution

Future runtime receives one exact `runtime_adoption_id` from trusted release
configuration and verifies exact adoption, scope, activation, publication
evidence, rule ID/version/hash and configuration hash. Any absence or mismatch
fails closed. Latest, max, head, leaf and most-recent publication are forbidden
as runtime fallbacks.

## 16. Legacy runtime compatibility

The incremental path preserves current exact-rule-ID runtime while migration
0022+ first adds only inert structures. A later adapter may map the trusted
configured exact rule ID to one pre-created exact adoption ID. It cannot query
by lineage/head/publication or infer any governed learning successor. A later
cutover changes runtime inputs only after separate authorization and tests.

## 17. Existing-history migration

AgentRunInput, RecommendationBasis and KnowledgeLayerBinding continue to point
to exact historical rule IDs. They are never rewritten to adoption IDs.
Existing published rows remain truthful. Expand/contract uses additive tables,
compatibility validation and forward fixes; destructive backfill is forbidden.

## 18. Legacy bootstrap truthfulness

`LEGACY_EVIDENCE_IMPORT` may identify actual pre-existing publication state,
timestamp, curation audit and hashes without claiming a new historical
decision. If continuity requires importing the configured vN, a separately
approved `LEGACY_BOOTSTRAP` adoption states that it imports pre-existing runtime
selection, has no fabricated activation (`activation_id=NULL`,
`historical_activation_claim=false`) and records import time separately.

The exact shape is defined, but no bootstrap is authorized here. Future
implementation/cutover is blocked without an approved exact inventory. Phase
26 vN+1/vN+2 are categorically excluded.

## 19. Publication authority

Publication requires a fresh AdminApps-resolved global publication permission
and independent human/global curator approval. It is not granted by Phase 26
execution, LearningApplicationAuthorization, tenant governance or client
claims. The target executor has no publication capability.

## 20. Activation authority

Activation requires a separate fresh global activation permission and release
policy. Publication authority, curator status and learning proposer/reviewer/
approver/authorizer roles do not imply activation. Publisher and activator are
different actors for the same revision by default.

## 21. Adoption authority

Adoption requires separate global runtime-adoption/release authority over the
exact configuration transition. It is not the application executor, generic
curator, publisher or sole activator. Activator and adopter are different
actors for the same release chain.

## 22. Separation of duties

| Role | Allowed | Prohibited for same chain |
|---|---|---|
| proposer | submit exact proposal | review/approve/authorize/apply/publish/activate/adopt own change |
| reviewer | scoped review | sole approval/authorization/release |
| approver | exact decision | execution and release transitions |
| application authorizer | authorize fixed capability | execution/publication/activation/adoption |
| target executor | invoke exact Phase 26 capability | all curation/release/repair |
| curator | approve content/source | sole publication of own revision |
| publisher | record publication | activation of same revision |
| activator | record activation | adoption of same activation |
| adopter/release authority | exact config transition | executor or sole activator role |
| repair authority | inspect/classify/disable/request recovery | target DML, publish, activate, adopt, rewrite |

Same-chain constraints are default deny. A future emergency exception requires
explicit dual-control policy and is not authorized.

## 23. AdminApps boundary

AdminApps remains system of record for identity, MFA, global roles, product
access and governance permissions. ISO Smart retains exact server-resolved
decision provenance; it creates no competing local global RBAC. Missing, stale,
revoked, mismatched or client-supplied authority fails closed.

## 24. Publication preconditions

Under lock and immediately before commit: exact draft revision/lineage/version/
hash; semantic fingerprint; validated source reference and published edition
hash; complete provenance; current leaf/no stale successor; Product Policy and
governance hash; no normative contamination; independent global curation and
publication authorities; capability enabled; no conflicting claim/record.

## 25. Activation preconditions

Exact published revision and publication provenance; unchanged target/
semantic hashes; exact expected predecessor activation; no stale/superseded
competing decision; runtime compatibility; activation/release policy and
governance hash; enabled capability and fresh activation authority. Unpublished
activation is impossible.

## 26. Adoption preconditions

Exact activated revision and Activation; exact publication evidence; exact
expected current adoption predecessor; compatibility and trusted deployment/
release/configuration target; governance hash; trace; enabled adoption
capability and fresh release authority. Direct adoption of an unactivated
revision is denied except the tightly constrained, separately approved truthful
legacy-bootstrap import.

## 27. Global governance

KnowledgeLayerRule is global/shared. The only designed scope is
`global_knowledge_layer_runtime` per exact rule lineage. No environment,
Organization, tenant or agent sub-scope is invented. Tenant-derived evidence
cannot publish, activate or adopt global behavior, and no tenant A evidence can
alter tenant B runtime without explicit global governance.

## 28. Event design

Future distinct global events are:

- `knowledge_layer_rule.published` v1: exact native publication committed;
- `knowledge_layer_rule.activation_recorded` v1: exact eligibility decision
  committed, no runtime-use claim;
- `knowledge_layer_rule.runtime_adopted` v1: exact configuration transition
  committed.

They do not reuse the Phase 26 application event and do not auto-trigger the
next stage. Payloads are bounded IDs/hashes/state/authority/trace only.

## 29. Audit design

Immutable audit reconstructs who, exact revision/hash, why, authority, policy,
publication/activation/adoption predecessors, before/after adoption,
configuration, incident, trace and timestamps for creation through recovery.
No licensed content, Evidence body, raw prompt, credential, token or secret is
copied.

## 30. Concurrency

Publication has one logical successful record per revision. Activation and
adoption requests supply exact expected predecessors; database uniqueness
permits one successor per predecessor/scope. Fixed stream locks plus material
and idempotency hashes yield exact replay, conflict or stale—never duplicate
publication or forked/ambiguous runtime targets.

## 31. TOCTOU

Each command re-resolves authority and capability state and revalidates exact
target/artifact/hash/policy/predecessor immediately before write. Publication
revalidates source/curation/leaf, activation revalidates publication/target/
compatibility, and adoption revalidates activation/current adoption/config.
Drift rolls back and fails closed.

## 32. Recovery

A problematic adopted revision is recovered by a new `RECOVERY` adoption of an
exact approved safe revision, with new authority, incident, reason, predecessor
and before/after evidence. If no existing activation authorizes the safe
revision, a new recovery activation is recorded first. No version is deleted,
unpublished or rewritten.

## 33. Capability disablement

Four exact capabilities are independently fenced: application, publication,
activation and adoption. Each disable/re-enable is append-only and checked at
admission and precommit. Disabling blocks only new decisions; it preserves all
history and does not change the currently configured exact adoption. Existing
Phase 27 application-disablement semantics are retained.

## 34. Ambiguous COMMIT — application

Phase 27's classifier remains unchanged: `COMMITTED`, `NOT_COMMITTED`,
`ABANDONED`, `INCONSISTENT`. COMMITTED requires the complete claim, governance,
delta, target, Receipt, event/outbox and audit graph. Target state alone is
never sufficient and a Receipt is never reconstructed.

## 35. Ambiguous COMMIT — publication

COMMITTED requires exact claim, publication, compatibility status projection,
curation evidence, event/outbox and audit to match bidirectionally.
`status=published` alone is insufficient. Missing/mismatched immutable
publication provenance is INCONSISTENT, not a reason to backfill approval.

## 36. Ambiguous COMMIT — activation

COMMITTED requires exact claim, Activation, publication/target hashes,
predecessor, event/outbox and audit. A row that merely looks activated, an event
alone or target status cannot establish commit. Lost response is reconciled by
the preallocated activation ID.

## 37. Ambiguous COMMIT — adoption

COMMITTED requires exact claim, RuntimeAdoption, activation, predecessor,
target revision/hash, configuration hash, event/outbox and audit. A lost
response is resolved by exact adoption ID. Blindly issuing another adoption is
prohibited.

For every boundary, NOT_COMMITTED means no durable claim/artifact/side artifact;
ABANDONED means a claim plus explicit append-only terminal disposition and no
transition; INCONSISTENT means any partial/orphan/mismatch. Timeout alone never
creates ABANDONED or permits claim stealing.

## 38. Repair authority

The separate repair principal can inspect bounded reconciliation views,
classify, disable one exact capability, append an incident/operator decision
and request separately governed recovery. It cannot execute generic target DML,
publish, activate, adopt, rewrite Receipt/Event/Audit, alter lineage, own schema
or issue arbitrary SQL. Operational repair alone cannot switch runtime.

## 39. Observability

Sanitized fields: operation/application ID, target lineage and revision IDs,
publication/activation/adoption IDs, trace, hashed idempotency/material,
boundary state, timestamps, reconciliation outcome and capability status. No
raw licensed content, Evidence body, prompts, PII beyond approved opaque actor
references, credentials or secrets.

## 40. Alerts

Conceptual local alert classes: inconsistent application, abandoned claim,
publication mismatch, activation mismatch, adoption mismatch, stale target,
repeated failed adoption, capability unexpectedly enabled, and unauthorized
publication/activation/adoption attempt. This gate introduces no external
telemetry dependency.

## 41. Retained history

Once any governed history exists, destructive reverse migration is forbidden.
Application Receipts, rule successors, publication evidence, activation and
adoption lineages, capability decisions, events and audits must survive code/
schema changes. Use expand/contract, compatibility reads, observation and
forward fixes; migration rollback is not business recovery.

## 42. Future migration design

The minimum core is three distinct tables because each fact has different
authority, preconditions and history:

1. `KnowledgeLayerRulePublication` (including constrained truthful legacy
   evidence kind);
2. `KnowledgeLayerRuleActivation`;
3. `KnowledgeLayerRuleRuntimeAdoption`.

Supporting exact operation claims/dispositions, capability decisions and
event/audit references may be shared only through closed enums and fixed typed
commands; they may not become generic target dispatch. Migration 0022+ must be
additive and inert, create no business records, and leave current runtime
unchanged. The three core artifacts are global and receive no fake tenant ID;
their defense is fixed-function ACL/ownership/default deny. Any tenant-scoped
supporting claim uses composite tenant/Organization defense plus ENABLE+FORCE
RLS.

## 43. Learning-change effectiveness

Observation and assessment follow adoption as a separate future stage. A
dedicated `LearningChangeEffectiveness` or equivalent may be designed later;
QMS action EffectivenessCheck is not reused automatically. Results never feed
automatic learning or release. No activation window, SLA or SLO is invented.

## 44. Release governance

```text
version created
-> publication approved
-> activation approved
-> runtime adoption approved
-> observed
-> effectiveness assessed
```

Every stage requires its own decision. None automatically emits the next
command or changes runtime.

## 45. Threat matrix

| Threat | Design control | Status |
|---|---|---|
| publication privilege escalation | separate AdminApps permission + curator evidence + typed capability | CLOSED |
| activation privilege escalation | independent authority/policy | CLOSED |
| adoption privilege escalation | independent release authority + exact config | CLOSED |
| executor self-publishing | ACL and role separation | CLOSED |
| publisher self-activating | same-chain actor prohibition | CLOSED |
| activator self-adopting | same-chain actor prohibition | CLOSED |
| tenant to global escalation | global authority only | CLOSED |
| latest-wins fallback | exact adoption ID; all fallbacks denied | CLOSED |
| exact-ID substitution | revision/scope/config hashes | CLOSED |
| stale publication | leaf/hash/source revalidation | CLOSED |
| stale activation | exact predecessor/publication revalidation | CLOSED |
| stale adoption | exact predecessor/activation/config revalidation | CLOSED |
| duplicate/forked adoption | idempotency, lock, unique predecessor successor | CLOSED |
| hidden pointer rewind | append-only RECOVERY adoption | CLOSED |
| ambiguous commit/missing Receipt | exact graph classifier; no reconstruction | CLOSED |
| forged repair | narrow distinct principal | CLOSED |
| raw history rewrite | immutable guards + retained-history policy | CLOSED |
| legacy bootstrap fiction | explicit import kind/no historical activation claim | CLOSED |
| capability disable bypass | append-only fence checked twice | CLOSED |
| runtime auto-adoption | events cannot switch configuration | CLOSED |
| cross-tenant behavior change | no tenant release authority | CLOSED |
| normative contamination | source/fingerprint/protected digests | CLOSED |

## 46. Mandatory proof matrix

| Mandatory design proof | Result |
|---|---|
| current blocker precisely verified | PASS |
| publication/activation/adoption separately defined | PASS |
| all four states non-equivalent | PASS |
| exact-ID adoption; no latest/head/max | PASS |
| truthful history/no retroactive approvals | PASS |
| legacy bootstrap defined and still separately gated | PASS |
| independent publication/activation/adoption authorities | PASS |
| executor/publisher/activator cannot chain self-release | PASS |
| tenant cannot mutate global adoption | PASS |
| immutable publication/activation/adoption histories | PASS |
| concurrency and TOCTOU | PASS |
| four reconciliation outcomes/no target-only inference | PASS |
| no Receipt/artifact reconstruction | PASS |
| independent capability disablement preserves history | PASS |
| narrow repair and append-only recovery/no rewind | PASS |
| retained-history migration policy | PASS |
| observability/alerts | PASS |
| effectiveness/release boundary | PASS |
| Phase 26 vN+1/vN+2 remain inert | PASS — docs-only/no DB |
| zero runtime/schema/target/external changes | PASS |
| future inert implementation P0/P1 design blockers | **0** |

## 47. Governance artifact

Created
`docs/governance/KNOWLEDGE_LAYER_RULE_PUBLICATION_ACTIVATION_RUNTIME_ADOPTION_POLICY_V1.md`,
status **APPROVED FOR INERT FOUNDATION IMPLEMENTATION GATE ONLY**, SHA-256
`efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556`.
It explicitly denies publication/activation/adoption of Phase 26 successors.

## 48. ADR

Created successor
`docs/adr/0014-separate-knowledge-layer-rule-publication-activation-runtime-adoption.md`,
SHA-256
`fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952`.
ADR-0013 and all earlier ADRs remain unchanged. Rejected alternatives include
publication-as-runtime, latest-wins, mutable active flag, pointer rewind,
executor publication, generic selector and fabricated retroactive approval.

## 49. Frozen hashes

Migrations 0001–0021 are **21/21 MATCH** against the promoted values:

| Migration | SHA-256 |
|---:|---|
| 0001 | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` |
| 0002 | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` |
| 0003 | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` |
| 0004 | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` |
| 0005 | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` |
| 0006 | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` |
| 0007 | `c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec` |
| 0008 | `285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032` |
| 0009 | `412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc` |
| 0010 | `c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79` |
| 0011 | `cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2` |
| 0012 | `7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc` |
| 0013 | `06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b` |
| 0014 | `ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33` |
| 0015 | `5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3` |
| 0016 | `e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5` |
| 0017 | `580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38` |
| 0018 | `703a85885a67df953f38ef35302205caeddea249104683f4f751ab20ece0696b` |
| 0019 | `c188b638124404bba10cae4c94a678053d49d7a1d07c6e455a48e46524064b50` |
| 0020 | `491f21d3422c9c9a5866520f6623d3b9c9bea2139083f0128495dd7207d19894` |
| 0021 | `e796910c1660f701c3457b020792a158c06d3e58135a7ebba1728bd8b33c7a97` |

Migration 0022 is absent. The ten authoritative sources are **10/10 MATCH**:

| Source | SHA-256 |
|---|---|
| DOCX | `8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c` |
| Draw.io | `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa` |
| Mermaid | `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3` |
| XLSX | `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5` |
| Nodes CSV | `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3` |
| Edges CSV | `30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6` |
| SQL | `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e` |
| OpenAPI | `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8` |
| JSON | `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb` |
| LEEME | `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db` |

Direct ZIP CRC/XML/text/JSON/CSV inspection passed.

Unchanged baseline hashes include Phase 26 migration `e796910c…`, Phase 26
report `ce36196c…`, Phase 27 report `3cc3418b…`, Phase 27 design `263003d3…`,
Phase 25.1 policy `1a5f7c78…`, ADR-0013 `8fa5852a…`, Phase 25.1 report
`f0fd1e6f…`, governed-learning policy `7d9c2fe3…`, implementation authorization
`04458c4f…` and proposal/review/application boundary `2d5beaeb…`.

## 50. Protected target invariance

No database was opened and the disposed Phase 26 POC was not recreated.
Therefore Phase 27.1 created zero vN+1/vN+2, publication, activation or adoption
rows. The demonstrated classification remains:

- vN: published and runtime-effective in the Phase 26 proof;
- vN+1: created, unpublished, not activated, not adopted;
- vN+2: created, unpublished, not activated, not adopted.

Current protected implementation hashes at entry/final comparison include
models `9dd94c94…`, knowledge-layer commands `b5b599ca…`, AgentRun runtime
`6767e209…`, Recommendation `655fbdd1…`, Phase 26 application service
`99d22898…`, eventing `c7620cdf…` and audit `46145940…`; none was edited.

## 51. Git hygiene

Entry status was captured before work. The repository was already materially
dirty, including unrelated backend/frontend/SQLite changes and untracked
foundation/docs history; all were preserved. Phase 27.1 adds only its policy,
ADR and report. No runtime, model, migration, test, target, role/grant or other
workspace was modified. Final whitespace and scoped diff checks are recorded
as follows: each of the three new files is clean under `git diff --no-index
--check`; repository-wide `git diff --check` reports only the pre-existing
`frontend/src/components/Layout/Sidebar.jsx:28` trailing space, which this gate
did not modify. Final `git status` preserves the entry changes and adds no file
outside the three Phase 27.1 documents.

## 52. Residual blockers

There are **0 P0/P1 design blockers** to the future inert foundation gate.
Implementation evidence remains deliberately outstanding: migration 0022+
fidelity, truthful legacy constraints, roles/ACL/RLS/catalog proof, concurrency,
TOCTOU, ambiguous-commit corruption matrices, capability fences, runtime
invariance, regressions and teardown. Actual legacy bootstrap, cutover,
publication, activation, adoption, recovery, effectiveness and deployment each
require separate authorization.

## 53. Final verdict

**PHASE 27.1 — PROMOTED.** Publication no longer implies activation in the
future contract; activation no longer implies runtime adoption; and runtime
adoption resolves one exact immutable adoption to one exact activated rule.
Truthful legacy import, append-only recovery, independent authorities,
reconciliation and capability fences are defined without changing Phase 26
runtime or history.

Meaning: **approved to request a future inert publication/activation/runtime-
adoption foundation implementation gate only**. Phase 26 vN+1/vN+2 remain
unpublished, inactive and not runtime-adopted.
