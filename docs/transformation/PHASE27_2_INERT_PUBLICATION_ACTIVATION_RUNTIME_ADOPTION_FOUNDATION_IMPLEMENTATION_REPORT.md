# ISO Smart AI — Phase 27.2 inert publication, activation and runtime-adoption foundation implementation

- Date: 2026-09-03 (`America/Costa_Rica`)
- Workspace: `/home/felipe/proyectos/isosmart`
- Nature: additive inert PostgreSQL foundation and explicit service/test boundary
- Runtime cutover/publication of Phase 26 successors/deployment/external effects: **ZERO**
- Final PostgreSQL run: `20260903T141608Z_564211`, PostgreSQL 18.6, Podman, isolated database/roles/volume
- Verdict: **PHASE 27.2 — PROMOTED FOR INERT FOUNDATION ONLY**

## 1. Verdict

**PROMOTED.** Migration 0022, typed services and the isolated PostgreSQL proof
matrix implement separate immutable Publication, Activation and RuntimeAdoption
facts. The exact-ID resolver succeeds only for a complete native adoption graph.
It is not imported or called by Recommendation, AgentRun or governed agent
runtime. There are 0 P0 and 0 P1 blockers inside this inert-foundation scope.

Promotion does not authorize publishing or activating either Phase 26
successor, runtime cutover, production, deployment or automatic learning.

## 2. Migration evolution

`0022_inert_rule_publication_activation_runtime_adoption` depends only on 0021
and is additive. On populated Phase 26 state, the matrix proved
`0021 -> 0022 -> 0021 -> 0022` while 0022 history was empty. After synthetic
0022 history existed, reverse failed closed with
`0022 is operationally forward-only after retained governance history exists`.
Migrations 0001–0021 remained byte-identical to their promoted hashes.

## 3. Exact schema/artifacts

Global append-only relations introduced:

| Schema | Artifact |
|---|---|
| `normative` | `knowledge_layer_rule_publication` |
| `normative` | `knowledge_layer_rule_activation` |
| `normative` | `knowledge_layer_rule_runtime_adoption` |
| `normative` | `knowledge_layer_rule_governance_claim` |
| `normative` | `knowledge_layer_rule_governance_event` |
| `normative` | `knowledge_layer_rule_governance_disposition` |
| `normative` | `knowledge_layer_rule_capability_decision` |
| `eventing` | `knowledge_layer_rule_governance_outbox` |
| `audit` | `knowledge_layer_rule_governance_audit` |

No artifact has `tenant_id`. Immutable triggers reject UPDATE/DELETE. Publication,
Activation and Adoption freeze rule/layer/lineage/version/material hash/semantic
fingerprint, authority, policy, reason, idempotency/material, trace and exact
claim/event/outbox/audit IDs.

## 4. Publication semantics

`publish_knowledge_layer_rule_v1` accepts one exact draft rule and expected
material hash. In one transaction it creates a claim, compatibility curation
audit, changes only the legacy `status/published_at` projection, and appends the
Publication/Event/Outbox/Audit graph. Counts proved Publication caused
Activation delta 0 and RuntimeAdoption delta 0. Exact replay returns the same
artifact; changed identity/material conflicts.

## 5. Activation semantics

`activate_knowledge_layer_rule_v1` accepts one exact Publication ID, recomputes
the exact rule hash, enforces publisher/activator separation and freezes an exact
predecessor. It appends eligibility evidence only. RuntimeAdoption delta after
Activation was 0. A unique-null-not-distinct `(lineage_id,
predecessor_activation_id)` constraint plus behavioral race proof prevents forks.

## 6. RuntimeAdoption semantics

`adopt_knowledge_layer_rule_runtime_v1` accepts one exact Activation ID and exact
expected predecessor adoption. It reloads Publication through Activation and
requires exact IDs/rule/hash across all records. It never deploys, calls runtime,
creates learning, or mutates the target. A unique-null-not-distinct predecessor
constraint and a two-connection race allowed exactly one successor.

## 7. Exact-ID resolver

The only interface is `resolve(*, runtime_adoption_id)` and the only SQL selector
is `WHERE a.id=p_runtime_adoption_id`. Resolution joins exact Adoption -> exact
Activation -> exact Publication -> exact KnowledgeLayerRule, checks all frozen
IDs/hashes and recomputes material. Missing, invalid, legacy-bootstrap or mixed
graphs fail closed. Direct rule, layer, Publication and Activation IDs; `current`,
`latest`, versions, revisions and timestamps all failed.

## 8. No-latest proof

The exact executable search across `knowledge_rule_release.py`, migration 0022,
`agent_runtime.py` and `recommendation.py` found zero occurrences of
`latest_published`, revision/created-at descending selectors, `max(version)`,
`max(revision)`, `.first()`, runtime lineage-leaf fallback or mutable current
pointer names. The only leaf derivation in 0022 is for append-only capability
decisions, never for resolving a rule. Runtime resolver line 532 is exact-ID.

The broad search produced 167 textual matches. Every matched file was inspected:

| Matches | File | Disposition |
|---:|---|---|
| 15 | `docs/governance/GOVERNED_LEARNING_PROPOSAL_REVIEW_APPLICATION_BOUNDARY_V1.md` | historical target-current design, no adoption resolver |
| 15 | `postgres_phase21_harness.py` | EffectivenessCheck fixture selection/tests only |
| 12 | `docs/governance/CONTROLLED_QMS_ACTION_POLICY_V1.md` | Opportunity/QMS state terminology |
| 11 | `KNOWLEDGE_LAYER_RULE_RUNTIME_ADOPTION_AND_OPERATIONAL_REPAIR_DESIGN_V1.md` | explicit prohibition text |
| 10 | `KNOWLEDGE_LAYER_RULE_PUBLICATION_ACTIVATION_RUNTIME_ADOPTION_POLICY_V1.md` | exact-ID policy/prohibition text |
| 8 | `postgres_phase26_harness.py` | fixtures and negative runtime scan |
| 6 | `KNOWLEDGE_LAYER_RULE_GOVERNED_SOURCE_REFERENCE_APPLICATION_POLICY_V1.md` | Phase 26 application lineage, not runtime resolution |
| 6 | `GOVERNED_LEARNING_IMPLEMENTATION_AUTHORIZATION_V1.md` | learning analysis selection policy |
| 5 | `EFFECTIVENESS_CHECK_POLICY_V1.md` | effectiveness lineage/prohibition |
| 5 | `postgres_phase27_2_harness.py` | negative exact-ID assertions |
| 5 | `learning_delta.py` | field named current source reference, exact target-bound delta |
| 4 | `GOVERNED_LEARNING_POLICY_V1.md` | EffectivenessCheck sampling |
| 4 | `0013-knowledge-layer-rule-lineage-head-runtime-effective-separation.md` | explicit no-latest decision |
| 4 | `postgres_phase19_harness.py` | EffectivenessCheck queue fixtures |
| 4 | `action_authorization.py` | ActionPlan outcome handling, unrelated to Rule |
| 3 | `0014-separate-knowledge-layer-rule-publication-activation-runtime-adoption.md` | explicit rejected alternatives |
| 3 | `postgres_phase23_harness.py` | Proposal fixture selection |
| 3 | migration 0021 | exact Phase 26 target-leaf validation only |
| 3 | `governed_learning.py` | exact Effectiveness/target lineage validation |
| 3 | `action_execution.py` | execution receipts, unrelated to Rule resolution |
| 2 | `test_knowledge_rule_release.py` | negative selector tests |
| 2 each | `risk_objective.py`, `qms_context.py`, Phase 5/7/10/24.2 harnesses, migrations 0018/0019, `learning_proposal_governance.py`, `eventing.py`, `change_performance.py`, `agent_runtime.py` | unrelated aggregate current-state/fixture logic; Agent runtime uses exact caller-supplied Rule ID |
| 1 each | ADR-0011/0012, `test_learning_delta.py`, `projection_writer.py`, Phase 9/12 harnesses, migration 0007/0015, `knowledge_layer.py`, `human_decision.py`, `effectiveness.py`, `document_evidence.py` | unrelated history, negative test or exact revision guard |

No inspected match can resolve a KnowledgeLayerRule for RuntimeAdoption.

## 9. Legacy publication evidence import

`LEGACY_EVIDENCE_IMPORT` requires a published rule created before foundation
installation, its exact historical `knowledge_layer_rule.published` curation
audit, exact material hash and evidence reference. Database constraints force
`workflow_approved=false`, preserve nullable historical publication time, and
store a distinct non-null import time. The native representation cannot be
forged through this command.

## 10. Legacy runtime bootstrap

`LEGACY_BOOTSTRAP` requires a pre-foundation published rule/hash and rejects any
rule produced as `learning_target_application_receipt.after_rule_id`. Constraints
force `activation_id=NULL`, `publication_id=NULL`,
`historical_activation_claim=false`, a distinct bootstrap import time and no
asserted historical effective time. It is deliberately not resolvable by the
new strict native resolver. Both Phase 26 successors were rejected.

## 11. Authority model

Separate exact dataclass types and AdminApps-resolved permissions exist for
Publication, Activation, Adoption, Repair and Capability control. Every mutation
requires current MFA/access/global scope plus authority-context, decision and
governance-policy versions. The database rechecks session-bound trusted facts.
Revoking access denied the next operation while the first artifact's authority
snapshot remained byte-stable.

## 12. Separation of duties

The Python boundary rejects authority-type substitution. Database functions are
granted to exactly one mutation principal. Publisher cannot activate/adopt;
Activator cannot publish/adopt; Adopter cannot publish/activate or mutate target;
Phase 26 executor and APP/WORKER/PROJECTOR/AUDIT WRITER cannot publish, activate
or adopt. Repair cannot do any of those. Publisher/Activator/Adopter actor IDs
must also differ along the same chain.

## 13. PostgreSQL roles and catalog evidence

The isolated run created six LOGIN roles (publisher, activator, adopter,
resolver, repair, controller) and one NOLOGIN governance-function owner. All were
NOSUPERUSER, NOINHERIT and NOBYPASSRLS. Catalog checks used `pg_roles`, `pg_proc`,
`information_schema`, `has_schema_privilege`, `has_table_privilege` and
`has_function_privilege`. Owner schema CREATE was temporary during ownership
transfer and revoked at migration completion.

## 14. Capability ACLs

PUBLIC EXECUTE is absent. Each public typed function is granted only to its
principal; private helpers remain unavailable. Read access is table-specific.
Global writes occur only through fixed SECURITY DEFINER functions. All privileged
functions have owner `foundation_klr_gov_owner_<run>` and fixed
`search_path=pg_catalog`. A hostile caller `search_path=pg_temp,public` did not
alter resolution. There is no SQL/payload dispatcher.

## 15. Event contracts

Schema-v1 event types are `knowledge_layer_rule.published`,
`publication_evidence_imported`, `activation_recorded`, `runtime_adopted` and
`legacy_runtime_bootstrapped`. Payloads contain bounded IDs/hashes/state/trace,
explicit `next_stage_requested=false` or `deployment_requested=false`, and no
content/secrets. No event trigger invokes the next stage; only immutability and a
test-only deferred commit-window trigger exist.

## 16. Audit

Each successful operation appends one global immutable audit row with operation,
artifact, exact rule, actor, authority context/decision/policy, material hash,
trace and canonical payload hash. The audit and graph IDs are bidirectionally
checked by reconciliation. Raw rule/evidence/prompt/license content is absent.

## 17. Atomicity

Publication, Activation and Adoption each commit claim + artifact + event +
outbox + audit in one Django/PostgreSQL transaction. Publication additionally
includes compatibility state and curation audit. Exact replays are read-only.

## 18. Rollback matrices

All three operations passed 6/6 failure points: after claim, event, outbox,
audit, artifact and immediately before commit (**18/18 total**). Every failure
left zero partial graph; Publication also restored the draft status/timestamp.

## 19. Concurrency

Two real Activation attempts from exact predecessor A1 produced one successor
and one denial; catalog count from A1 was one. Two real Adoption attempts from
exact predecessor adoption A1 produced one successor and one denial. Unique
predecessor constraints independently enforce the same result.

## 20. TOCTOU

Commands check authority/capability on admission; lock/share the exact upstream
artifact; recompute target hash; validate exact predecessor; append; recompute
hash and capability again immediately before return/commit. Immutable target
guards prevent material drift after publication. Stale predecessor and bad hash
attempts failed closed.

## 21. Reconciliation state machine

Typed reconciliation functions return exactly `COMMITTED`, `NOT_COMMITTED`,
`ABANDONED` or `INCONSISTENT`. COMMITTED requires the exact complete graph;
NOT_COMMITTED requires no durable operation evidence; ABANDONED requires an
append-only disposition plus claim and no governed artifact graph; any orphan or
mismatch is INCONSISTENT.

## 22. Ambiguous commit results

A successful commit whose response was ignored reconciled COMMITTED. Separately,
the harness opened a real adopter connection, entered a deferred COMMIT window,
terminated that backend from a peer principal, observed connection failure, and
then reconciled the exact preallocated Adoption ID as NOT_COMMITTED because no
durable graph existed. It did not classify both cases as replay. An injected
orphan event reconciled INCONSISTENT.

## 23. Capability fences

Publication, Activation and RuntimeAdoption have independent append-only fences;
the pre-existing Phase 26 application control remains separate. Publication
disable denied only new Publication and did not remove history or affect exact
resolution. Adoption disable denied only new adoption and did not unpublish,
deactivate, rewrite or make existing adoption unresolvable.

## 24. Re-enable governance

Re-enable requires a new decision referencing the exact disable predecessor and
must alternate state. The matrix retained `[false,true]`; direct UPDATE was
rejected by the immutable trigger. Actor/reason/authority/policy/time/trace are
frozen on both decisions.

## 25. Repair authority

Repair may read bounded governance evidence, call typed reconciliation and append
an explicit ABANDONED disposition only where no durable evidence exists. It has
no artifact construction, target DML, event/audit rewrite, schema CREATE or
Publication/Activation/Adoption execution. A claim cannot be stolen. Partial
state is preserved as INCONSISTENT; no artifact is reconstructed.

## 26. Observability

Observable fields are opaque operation/artifact/rule/lineage IDs, hashes,
authority versions/references, trace, timestamps, capability decisions and
reconciliation outcomes. The outbox remains pending/inert. No external telemetry,
notification or dispatcher was introduced.

## 27. Retained-history migration behavior

Empty-history forward/reverse/forward passed. Once any claim, artifact, event,
disposition or capability decision exists, destructive reverse is operationally
prohibited. History is not deleted to satisfy migration reversibility; future
evolution must be expand/contract and forward-fix.

## 28. Current runtime invariance

Before/after SHA-256 matched exactly: `agent_runtime.py`
`6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d`
and `recommendation.py`
`655fbdd18437f3d04a838c4dfad0b5b5fb3f6cc2e3d53d29fcc21a22acc6648c`.
Neither imports the new service. Protected AgentRun/Input and
Recommendation/Basis digests matched before/after. The strict resolver is callable
only through its explicit `rule_resolver` service/test alias.

## 29. Phase 26 successor invariance

The exact Phase 26 classification remained vN published/runtime-effective;
vN+1 and vN+2 draft with `published_at=NULL`. Final Publication, Activation and
RuntimeAdoption counts referencing vN+1/vN+2 were all zero. Bootstrap explicitly
rejected both successors.

## 30. Normative/protected-target invariance

ModelPolicy, AgentDefinition, Recommendation, RecommendationBasis, AgentRun,
AgentRunInput, LearningSignal and LearningProposal full count/JSON aggregate
digests matched. New operations created no LearningSignal/Proposal, confidence
change, autonomy change, compensation, model/agent mutation or certifiable
normative mutation. Synthetic test rules were non-official guidance fixtures.

## 31. Inherited regressions

The Phase 27.2 run inherited the complete Phase 26 chain and Phase 26 again
reported **113/113 PASS**, including prior Phase 9/16/17/19/20/21/23/24.2
security, lineage, RLS, atomicity and protected-state proofs.

## 32. Backend/foundation counts

- Phase 27.2 PostgreSQL: **140/140 PASS**.
- Foundation Django: **104 PASS, 0 FAIL, 0 SKIP** (Phase 26 baseline 100, delta +4).
- Explicit backend apps (`authentication core integration leadership foundation`):
  **202 PASS, 0 FAIL, 0 SKIP** (Phase 26 baseline 198, delta +4).

## 33. Django integrity

`manage.py check`: zero issues. `makemigrations --check --dry-run`: no changes.
Foundation package compilation: PASS. SQLite is used only for the isolated Django
unit suite; all database-security assertions ran against PostgreSQL 18.6.

## 34. Frozen migration hashes

Migrations 0001–0021 are **21/21 MATCH**:

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
| **0022** | **`afefd7100a18e5c7324efaeb1af656225b309fd86f08673a8742f7f9f6c2e618`** |

## 35. Source hashes

Authoritative sources remain **10/10 MATCH**: DOCX
`8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c`,
Draw.io `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa`,
Mermaid `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3`,
XLSX `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5`,
nodes CSV `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3`,
edges CSV `30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6`,
SQL `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e`,
OpenAPI `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8`,
JSON `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb`,
LEEME `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db`.
ZIP CRC, every embedded XML, CSV, JSON, YAML and text reads all passed directly.

New implementation sources: service `a7b0477f48120b852d9ec510d30e85d4700f5c0ba970e3ed3c9e244b1be4d7e9`;
PostgreSQL harness `b089ddf3fc37456041677d120348cb01e036897fbc57357f94dcb05888aeb9c8`;
gate `c97802e516a8b3f958c41eef2a4c138c3b071fd9e086a0b2566b4a10e51ae11d`;
base harness `1b26cdb2f80073633b622595fc89db0b9a6bdc357332133d49e5145a52111fe4`;
unit tests `e128eead2a506d5181bc182e4cd94e18f98471832b795e675ea10e88c4c4c362`.

## 36. Governance hashes

Phase 27.1 policy remains `efdd4d8a679c7f18762bfe79c3e876e970f81fedb2848ef5cbf21e7aeb858556`;
ADR-0014 remains `fa0e376e802f80e95d3961fabf8f6fe5e337f4b312062123ffd45c31bb300952`;
Phase 27 report remains `3cc3418b48a0899cddc56636316a36cdabbd947d480e7d8e6b5f87d5863ed9e1`;
Phase 27.1 report remains `ca6bf1920200595c73dc2fb654cdce74098b1a4a329813eaf409b52b73d4e5f4`;
Phase 26 report remains `ce36196c4094addba4fb31a512582a05af0113036c3894cb20eb938d1eefedd9`.

## 37. Zero external effects

No production/database/API/AdminApps/MedSupplier/object storage/provider/tool
write, notification, deployment or runtime cutover occurred. Only local source
files and isolated test infrastructure changed. Synthetic events/outbox rows
existed only inside the destroyed ephemeral database.

## 38. Teardown

Final run endpoint `127.0.0.1:36557` and database
`foundation_gate_20260903t141608z564211` were ephemeral. Container absent,
volume absent and temporary directory absent all passed after the run. Every
earlier failed diagnostic run also reported teardown PASS.

## 39. Residual blockers

Within inert Phase 27.2 scope: **0 P0, 0 P1**. Still unauthorized and therefore
outside promotion: production deployment, actual legacy import/bootstrap,
release configuration integration, current runtime adoption, publishing or
activating either Phase 26 successor, another learning operation/target,
automatic learning and effectiveness evaluation. Phase 28 must remain design
only and select at most one inert successor for a future publication POC.

## 40. Final promotion verdict

**PHASE 27.2 — PROMOTED FOR INERT FOUNDATION IMPLEMENTATION ONLY.** All blocking
assertions A–AH passed with real PostgreSQL/catalog/behavioral evidence. The
foundation cannot make a rule runtime-adoptable without the exact native
RuntimeAdoption -> Activation -> Publication -> KnowledgeLayerRule graph. Existing
runtime remains unchanged and both Phase 26 successors remain inert.

| Component/test | State | Evidence | Risk/next action |
|---|---|---|---|
| Migration/schema | PASS | 0022 additive; empty reverse/forward; retained reverse denied | Expand/contract only |
| Exact-ID resolver | PASS | Exact UUID + complete native graph; all substitutes denied | Do not wire runtime yet |
| Publication/Activation/Adoption | PASS | Separate immutable typed artifacts; no auto-advance | Phase 28 design only |
| Hash/provenance/authority | PASS | Recomputed at each boundary; immutable AdminApps/policy snapshot | Resolve authority fresh for every future write |
| Atomicity/concurrency | PASS | 18/18 rollback; one successor per exact predecessor | Preserve constraints/functions |
| Reconciliation/ambiguous commit | PASS | Four states; real connection-loss proof; orphan is INCONSISTENT | Never reconstruct or blindly retry |
| ACL/roles/repair | PASS | Dedicated LOGINs, NOLOGIN owner, PUBLIC denied, hostile path denied | No broader grants |
| Legacy truthfulness | PASS | Import/bootstrap constraints; bootstrap resolver-inert | Actual import separately authorized |
| Runtime/Phase 26/protected state | PASS | Byte/digest invariance; vN+1/vN+2 zero references | No successor publication now |
| Regression/integrity | PASS | PG 140; foundation 104; backend 202; checks clean | Keep frozen baselines |
| External effects/teardown | PASS | Zero external effects; all ephemeral resources absent | No deployment authorized |
