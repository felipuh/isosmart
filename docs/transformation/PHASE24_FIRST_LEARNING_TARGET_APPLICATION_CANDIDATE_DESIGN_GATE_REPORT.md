# Phase 24 — First Learning Target Application Candidate Design Gate

- Date: 2026-08-25
- Nature: source/policy reconciliation + security design gate; documentation only
- Workspace: `/home/felipe/proyectos/isosmart`
- Runtime/schema/database/target effects: **ZERO**
- Verdict: **NOT PROMOTED — NO TARGET/OPERATION SELECTED**

## 1. Verdict

**PHASE 24 — FIRST LEARNING TARGET APPLICATION CANDIDATE SOURCE/POLICY +
SECURITY DESIGN GATE: NOT PROMOTED.**

No candidate satisfies every blocking criterion. The common P1 blocker is that
Phase 21 freezes only `LearningProposal.proposed_change_hash`; it does not
persist canonical proposed-delta material, a content-addressed delta reference,
or a target-specific delta schema that an application can consume without an
application-time replacement payload. Phase 23 binds that hash indirectly
inside `proposal_material_hash`, but it cannot recompute it from absent material.

A second common P1 blocker is capability exactness. Phase 23 authorizes only
`revise_model_policy`, `revise_agent_definition`, and
`revise_knowledge_layer_rule`. Each maps to an existing curator command whose
input surface is wider than the safe first-operation subset. Reinterpreting one
of those capabilities as a new narrower operation would change its contract
after authorization. No application-specific, atomically composable,
least-privilege seam exists yet.

Therefore this phase creates only this report. It creates no Product Policy,
ADR, migration, executor, receipt, event, grant, target row, successor, publish,
activation, deployment, or external effect.

## 2. Entry baseline

The Phase 23 report records PROMOTED with PostgreSQL 18.6, 185/185 backend tests,
87/87 foundation tests, immutable review/decision/authorization artifacts,
exact proposal and target freeze, `VALID|STALE` semantics, three separate
governance principals, ENABLE+FORCE RLS, protected-target DML denial and zero
application capability. Migrations 0001–0019 form the frozen entry baseline.

The initial worktree was already materially dirty, including untracked Phase
foundation and governance history plus unrelated backend/frontend edits. The
entry `git status` was recorded before this report and all unrelated changes
were preserved.

## 3. Source and policy reconciliation

The ten authoritative artifacts were read directly. DOCX and all XLSX package
members passed ZIP reads; their XML was inspected. Draw.io XML, Mermaid, both
CSVs, reference DDL, OpenAPI, master JSON and LEEME were read directly. Their
SHA-256 values match the source manifest 10/10.

| Target | Source support | Product Policy support | Current model | Current versioning | Current curator | Current command | Published immutability | Successor semantics | Application possibility | Blocker | Rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ModelPolicy` | provenance, models, guardrails, human gate and A0–A4 concepts | global critical policy; learning cannot relax it | separate global row | lineage + unique version + exact predecessor | agent catalog curator | `revise_model_policy` | DB trigger; only draft→published material-preserving update | published current leaf → draft exact successor | conditional only | no frozen delta; command/capability too broad; safe partial order incomplete | all four material fields can affect governance/runtime |
| `AgentDefinition` | purpose/capability/policy/autonomy concepts | global runtime governance; no purpose/capability broadening or autonomy increase | separate global row linked to exact published policy | lineage + unique version + exact predecessor | agent catalog curator | `revise_agent_definition` | DB trigger; only draft→published material-preserving update | published current leaf → draft exact successor | conditional only | no frozen delta; command/capability too broad; no DB monotonicity | free-text purpose and capability semantics cannot be compared safely |
| `KnowledgeLayerRule` | versioned non-certifiable guidance and provenance | global normative curation; never normative requirement | global rule row under exact KnowledgeLayer/Edition | lineage + unique version + exact predecessor | normative curator | `revise_knowledge_layer_rule` | DB trigger; only draft→published material-preserving update | published current leaf → draft exact successor | closest candidate, still not ready | no frozen delta; broad command; free-text source trust absent | logic/evidence/source can change; only a source-reference correction looked narrow enough |
| Prompt/rule bundle | version strings only | expressly NOT READY | provenance strings, no target | none | none | none | unprovable | none | ineligible | no promoted target identity/lifecycle | provenance is not a mutation target |
| Retrieval configuration | namespace/dataset provenance only | expressly NOT READY | provenance strings, no target | none | none | none | unprovable | none | ineligible | no promoted target identity/lifecycle | no curator, source allowlist or tenant-safe successor semantics |

The distinctions used by this gate are:

- **AUTHORITATIVE SOURCE FACT:** the sources separate Effectiveness, learning,
  human decision, guardrails, autonomy and version provenance; they model the
  three target concepts and non-destructive normative history. They do not
  define proposal application, delta storage, executor authority or generic
  self-modification.
- **PRODUCT POLICY DECISION:** governed learning is inert until separate human
  review, exact decision, exact authorization and a later target-specific gate;
  tenant evidence cannot authorize global behavior; published history,
  normative content, human gates and autonomy ceilings are protected.
- **ARCHITECTURAL INFERENCE:** because a hash without retrievable canonical
  material cannot supply an approved delta, a frozen delta artifact/schema is
  required before application. Because curator commands accept different broad
  field sets, each first operation needs its own capability ID/version and
  validation profile.

No existing policy or authorization was broadened.

## 4. Candidate inventory and exact evaluated operations

The gate did not preselect a target. It evaluated one exact, maximally narrow
operation shape for each primary target:

| Target | Exact evaluated operation | Proposed allowed change | Frozen material | Result |
|---|---|---|---|---|
| `ModelPolicy` | `create_model_policy_draft_successor_by_approved_model_removal` | remove one or more exact entries; never add | key, lineage, data classes, guardrails, human gates, status/publication | FAIL |
| `AgentDefinition` | `create_agent_definition_draft_successor_by_autonomy_reduction` | lower `autonomy_max` only | key/name, purpose, capability, ModelPolicy, status/publication | FAIL |
| `KnowledgeLayerRule` | `create_knowledge_layer_rule_draft_successor_by_source_reference_correction` | replace only a validated source reference | layer/edition, lineage/key, logic, evidence expectation, classification, bindings, status/publication | FAIL |

These operation shapes are analysis labels only. They are not capabilities,
policies or implementation authority.

## 5. Candidate safety matrix

`PASS WITH RESTRICTIONS` is not treated as a blocking-gate pass.

| Criterion | ModelPolicy | AgentDefinition | KnowledgeLayerRule |
|---|---|---|---|
| Source support | PASS | PASS | PASS |
| Policy support | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| Versioned | PASS | PASS | PASS |
| Published immutability | PASS | PASS | PASS |
| Draft/inactive successor possible | PASS | PASS | PASS |
| Curator boundary | PASS | PASS | PASS |
| Narrow capability possible | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| No logic duplication | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| Autonomy safe | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS |
| Human-gate safe | PASS WITH RESTRICTIONS | PASS | PASS |
| Guardrail safe | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| Global governance safe | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| Idempotent | FAIL | FAIL | FAIL |
| Concurrent-safe | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| TOCTOU-safe | FAIL | FAIL | FAIL |
| Compensatable | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| Auditable | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| Eventable | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS |
| No normative impact | PASS | PASS | PASS WITH RESTRICTIONS |
| No cross-tenant effect | PASS while draft | PASS while draft | PASS while draft |
| Implementation readiness | FAIL | FAIL | FAIL |
| **Outcome** | **FAIL** | **FAIL** | **FAIL** |

Idempotency and TOCTOU fail at the application boundary because the exact delta
material cannot be loaded and recomputed. Existing target predecessor uniqueness
does prevent two target forks, but it does not prove one logical application
result for an absent delta/capability contract.

## 6. Selection

No target and no operation are selected. The tie-break was not reached.

`KnowledgeLayerRule` source-reference correction is the nearest future candidate
because it can freeze runtime logic, evidence expectations, classification,
bindings and all autonomy/human-gate fields while creating an unpublished draft.
It still fails mandatory gates: source reference has no frozen proposed value or
canonical schema; no trusted-source registry/validation contract exists; and
the authorized `revise_knowledge_layer_rule` capability also permits logic and
evidence changes.

## 7. Allowed delta and frozen fields

There is no approved Phase 24 delta. Any future blocker-closure gate must first
define one immutable target-operation delta envelope containing at least:

```text
operation_id + operation_version + target_type + exact target tuple
+ exact allowed field(s) + canonical before value/hash + canonical after value/hash
+ delta_schema_version + canonicalization_version + delta_hash
```

It must be created with the proposal, stored or content-addressed under a
promoted immutable retrieval contract, and included in review, decision and
authorization material. Supplying the after value at application time is
prohibited even when its hash happens to match.

All fields remain frozen in this phase. For any later first operation, IDs,
lineage, key/name, predecessor, current vN, status, publication timestamp,
created timestamp, scope and every field outside the exact allowlist must be
copied from vN or generated by canonical version semantics, never accepted from
the application caller.

## 8. vN immutability and vN+1 semantics

The current DB foundations already provide useful invariants:

- vN published rows reject material UPDATE and DELETE;
- `previous_revision_id` is unique, preventing two ordinary successor forks;
- successor INSERT requires the exact published predecessor and same lineage;
- existing curator commands lock vN and reject a non-current leaf;
- new rows are `draft` with `published_at=NULL`.

A future application must preserve those invariants, reference vN explicitly,
and return exactly one draft vN+1. It must not use a latest/current pointer,
publish, activate, deploy, select the new row at runtime or alter vN. Version
labels must come from a deterministic target-specific contract; arbitrary caller
version strings are not sufficient for an application seam.

## 9. Proposal, decision and authorization linkage

Phase 23 correctly freezes proposal ID/revision/predecessor/material hash,
decision/reviews, authorization, target type/ID/lineage/version/hash,
capability/version, actor authority and idempotency material. Its
`proposal_material_hash` includes `proposed_change_hash`.

The missing link is the material committed by `proposed_change_hash`. The
database has no `proposed_delta`, delta artifact ID, immutable object reference,
canonicalization version or schema version. Consequently a future application
could only receive material from its caller or another ungoverned source. That
would violate proposal freeze even if it recomputed to the stored digest.

The authorization capability is also insufficiently exact for the evaluated
operations. `revise_*` names authorize the full canonical curator input surface,
not removal-only, autonomy-reduction-only or source-reference-correction-only.

## 10. Target drift and delta hash

Target drift semantics are otherwise sound: any existing successor, non-
published target, lineage/version mismatch or full-row hash mismatch makes the
proposal/authorization stale; no silent rebase is allowed. A new proposal or
explicit future governed revalidation is required.

The stored `proposed_change_hash` has valid SHA-256 shape, but no deterministic
delta serialization is defined. The future formula must be, conceptually:

```text
delta_hash = SHA-256(canonical_json_vX(target-specific-delta-schema-vY))
```

Application must load that exact frozen material by proposal-owned identity,
recompute it immediately before mutation, compare it with proposal, decision
and authorization commitments, and fail closed on any mismatch.

## 11. Candidate-specific analysis

### ModelPolicy

The model and command support lineage, publication separation, exact predecessor,
approved models, data classes, guardrails, human gates and a curator ledger.
However the current `revise_model_policy` accepts replacements for all four
material fields. Safe monotonicity is not defined for arbitrary JSON guardrails
or human-gate rules. The evaluated removal-only operation could be modeled as a
set contraction while freezing all other material, but that operation/delta is
not frozen or authorized. ModelPolicy therefore fails.

### AgentDefinition

The model and command support lineage, publication separation, exact predecessor,
purpose, capability, autonomy and exact published ModelPolicy linkage. The
evaluated operation would require `0 <= new_autonomy_max < old_autonomy_max`,
with purpose, capability and ModelPolicy copied from vN. Current DB/service
validation checks only A0–A4 shape and policy publication, not monotonicity. The
current capability also accepts purpose/capability/policy replacement. The exact
delta is absent. AgentDefinition therefore fails.

### KnowledgeLayerRule

The model and command preserve exact KnowledgeLayer/Edition, lineage/key,
classification `non_certifiable_guidance`, draft/publication separation and a
normative-curation ledger. Bindings reference exact published rule revisions and
would remain historical. The evaluated source-reference-only operation would
freeze logic, evidence expectation, classification and all bindings, giving no
runtime or normative content change until separate publication. But
`source_reference` is unconstrained free text, no trusted source identity policy
exists, the exact proposed value is absent, and the current capability permits
logic/evidence replacement. KnowledgeLayerRule therefore fails.

Prompt/rule bundles and retrieval configuration remain ineligible, not failed
primary candidates: neither is a promoted target entity with predecessor,
curator, immutable material hash, publication or activation lifecycle.

## 12. Autonomy, human gates and guardrails

No Phase 24 operation changes autonomy, human gates or guardrails.

- ModelPolicy: guardrails, human-gate rules and data classes would have to be
  immutable for a first operation; approved-model contraction would still need
  independent policy/security review.
- AgentDefinition: only a provable autonomy decrease was evaluated; purpose,
  capability and ModelPolicy would remain exact. No current DB rule enforces
  that monotonic relation.
- KnowledgeLayerRule: has no autonomy/human-gate fields, but logic can influence
  recommendations. The evaluated operation froze logic and evidence expectation.

No generic partial order is invented for arbitrary JSON. Uncomparable security
fields remain immutable.

## 13. Global and cross-tenant governance

All three primary targets are global. Tenant/Organization-scoped proposals are
evidence only. Any future exact delta requires fresh global review, a global
approved decision, a separate global application authorization, the exact
target curator capability and an application actor distinct from creator,
effectiveness reviewer, learning reviewer, approver and authorizer.

Draft creation must not alter runtime selection, so Tenant B behavior remains
unchanged. Publication, activation and runtime selection require later separate
global gates. No fake tenant ID may be added to a global catalog or global
curation event.

## 14. Curator and least-privilege capability boundary

The canonical curator services must remain the single source of target business
logic. A future learning application may not ORM-save a target row directly.

Options evaluated:

| Option | Least privilege | Global catalog/RLS | Transaction composition | Logic duplication | Result |
|---|---|---|---|---|---|
| A. Existing curator service with current curator role | weak: role can INSERT across its whole catalog | correct use of global ACLs; no fake RLS | difficult to combine executor governance + curator alias + receipt atomically | low | reject as application seam |
| B. target-operation `SECURITY DEFINER` function | strong if only exact typed delta and EXECUTE are granted | suitable for global catalog; owner non-login; fixed `search_path` required | one DB transaction possible | medium unless function becomes canonical primitive | preferred only after design/implementation proof |
| C. dedicated target curator function used by both human curator and application | strongest practical boundary | ACL/function ownership explicit; runtime gets no table DML | supports one atomic transaction | low if existing command delegates to it | preferred future architecture |
| D. application executor receives curator credentials/DML | unacceptable | bypasses intended separation | composable but overprivileged | low | prohibited |

For B/C, revoke PUBLIC EXECUTE; owner must be non-login/non-runtime; pin
`search_path` to `pg_catalog` plus explicit qualified schemas; reject dynamic
SQL; accept no arbitrary JSON envelope; lock exact proposal/decision/auth/target;
and expose no publish, activation, UPDATE or DELETE. Phase 24 implements none of
these options.

## 15. Idempotency, concurrency and TOCTOU

Future durable identity must be:

```text
proposal ID/revision/material hash + decision ID + authorization ID
+ exact target vN/hash + exact target-operation capability/version
+ exact canonical delta hash
```

Exact replay returns the same receipt and successor. Same idempotency key with
different provenance conflicts. Two simultaneous attempts must lock in a fixed
order: application claim, proposal lineage/revision, decision, authorization,
delta artifact, target lineage/current leaf, predecessor uniqueness, then audit
and receipt. One creates vN+1; the other is replay/conflict/stale. Deadlock or
serialization error is never success.

Immediately before INSERT, the transaction must revalidate proposal currentness
and material, exact approved decision/reviews, exact valid unused authorization,
authority, operation capability/version, exact delta material/hash/schema,
target vN/current leaf/full-row hash and target-specific invariants. The missing
delta material makes this proof impossible today.

## 16. Transaction, event, audit and receipt model

The future transaction boundary is:

```text
revalidate governance and frozen delta
-> lock authorization/application identity
-> lock target vN and current leaf
-> invoke canonical target-specific successor primitive
-> append target curation audit/event
-> append immutable LearningApplicationReceipt and learning audit
-> commit
```

No external provider call occurs inside or after this POC transaction.

Target curation semantics remain distinct from learning lifecycle semantics.
ModelPolicy/AgentDefinition currently use `governance.curation_audit`;
KnowledgeLayerRule uses `normative.curation_audit`. Those target-owned actions
must not be replaced by a generic learning event. A later application event may
be designed only with its own approved contract; no event is created here.

A future immutable `LearningApplicationReceipt` must prove proposal revision and
material hash, decision, authorization, target vN/hash, target vN+1/hash,
operation capability/version, delta hash/schema, application actor, curator
audit/event reference, learning audit reference, trace and timestamps. It means
draft successor creation only, never publication, activation or deployment.

## 17. Compensation and learning-change effectiveness

Compensation never deletes or overwrites vN+1. It requires independent
governance and a new vN+2 successor restoring approved prior semantics or
another target-specific safe state. Model removal, autonomy reduction and source
reference correction are conceptually reversible through later successors, but
none receives authority here.

Effectiveness of a future learning-originated change requires a separate
`LearningChangeEffectiveness` policy/boundary linked to exact successor,
publication/activation interval, evaluated population and evidence. It is not
the existing Opportunity `EffectivenessCheck` and cannot automatically produce
another signal/proposal/application loop.

## 18. Publication and activation separation

All three current curator commands create drafts and publish separately.
Successor creation therefore need not be runtime-effective. Activation and
runtime selection are not sufficiently modeled and remain prohibited. The
future application capability must have no EXECUTE/permission path to publish,
activate, deploy or change runtime selection. A hidden default-to-latest query
must be rejected by tests before any later promotion.

## 19. Data minimization

Future provenance stores IDs, versions, canonical hashes, the minimal approved
delta artifact, policy/capability versions, authority references and trace. It
does not copy raw Evidence, documents, secrets, tokens or prompts. A source
reference requires its own trust/classification policy and must not become a
channel for raw confidential content.

## 20. Threat matrix

| Threat | Required control | Current result |
|---|---|---|
| malicious approved proposal | target-operation schema + independent review + exact frozen delta | BLOCKED: material absent |
| stale target | exact vN/current-leaf/full-row hash lock | designed/present in prior layers |
| stale decision | exact proposal/reviews/material revalidation | designed/present |
| stale authorization | exact authorization + drift/currentness check | designed; application claim absent |
| delta tampering | load proposal-owned material and recompute canonical hash | BLOCKED |
| target hash mismatch | recompute immediately before INSERT | designed |
| duplicate application | durable tuple + immutable receipt uniqueness | BLOCKED: receipt/claim absent by design |
| successor fork | unique predecessor + row/lineage lock | target constraint present |
| self-application | separate trusted application actor and DB principal | BLOCKED: actor boundary not implemented |
| tenant→global escalation | global governance + curator capability; tenant evidence only | designed |
| cross-tenant behavior | draft/inactive only; no latest adoption | designed; runtime-selection test required |
| autonomy escalation | freeze or DB-enforced decrease | missing candidate operation constraint |
| guardrail weakening | fields frozen; no semantic JSON comparison | missing candidate operation profile |
| human-gate removal | fields frozen | missing candidate operation profile |
| policy self-relaxation | independent policy/security authority; no learning relax path | ModelPolicy candidate rejected |
| KnowledgeLayer normative contamination | fixed classification; logic/bindings frozen; normative DML denied | source trust profile absent |
| curator privilege escalation | executor gets EXECUTE only, no table DML/role inheritance | capability seam absent |
| generic DML bypass | ACL denial + target-specific primitive | target ACL baseline good; seam absent |
| SECURITY DEFINER abuse | fixed search path, qualified names, non-login owner, no dynamic SQL, PUBLIC revoke | not implemented |
| unsafe search path | catalog assertion + adversarial shadow object test | not implemented |
| audit forgery | canonical target curator ledger + immutable learning audit | receipt linkage absent |
| hidden activation | draft status + no publish grants + explicit runtime selection | activation model/test absent |
| automatic runtime adoption | forbid latest selection; compare runtime behavior before/after | test absent |
| compensation abuse | new independently authorized successor; no DELETE | designed only |

No current residual threat authorizes application.

## 21. Future Phase 25 acceptance test plan

Phase 25 is **not authorized** by this verdict. After the exact blockers are
closed and Phase 24 is rerun successfully, its ephemeral PostgreSQL 18.6 plan
must include all of the following:

1. exact proposal accepted;
2. wrong proposal rejected;
3. wrong decision rejected;
4. wrong authorization rejected;
5. wrong operation capability/version rejected;
6. target hash mismatch rejected;
7. target version drift rejected;
8. canonical delta hash mismatch rejected;
9. stale target current leaf rejected;
10. concurrent second application conflicts/replays/stales;
11. exact replay returns the same successor/receipt;
12. generic target DML denied;
13. unauthorized curator denied;
14. proposal creator cannot self-apply;
15. tenant authority cannot mutate a global target;
16. vN complete row/hash unchanged;
17. exactly one vN+1 exists;
18. vN+1 remains draft/inactive;
19. runtime selection/behavior unchanged;
20. autonomy unchanged or strictly reduced by the exact selected contract;
21. human gates unchanged;
22. guardrails unchanged or provably stricter under the selected contract;
23. Standard/Edition/Clause/RequirementControl/bindings unchanged;
24. successor + curator ledger/event + learning audit + receipt atomic;
25. forced rollback leaves no vN+1;
26. receipt failure rolls back successor;
27. audit failure rolls back successor;
28. target event/ledger failure rolls back successor;
29. compensation creates a governed successor and never deletes;
30. publication/activation/runtime-adoption capabilities absent;
31. no external effects;
32. disable/reversal preserves history.

Additional blocker-closure tests must prove canonical delta round-trip,
application without caller-supplied material, capability/profile exactness,
fixed `SECURITY DEFINER` search path if chosen, executor zero target-table DML,
and one-connection transaction composition.

## 22. Governance artifact and ADR

No `FIRST_GOVERNED_LEARNING_TARGET_APPLICATION_POLICY_V1.md` was created because
no candidate passed. No successor ADR was created. Producing either would imply
a selection that the evidence does not support and would silently broaden the
Phase 22/23 authorization boundary.

## 23. Frozen integrity

### Migrations

Direct SHA-256 verification matched all 19 frozen migrations:

| Migration | SHA-256 | Result |
|---|---|---|
| 0001 | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` | MATCH |
| 0002 | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` | MATCH |
| 0003 | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` | MATCH |
| 0004 | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` | MATCH |
| 0005 | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` | MATCH |
| 0006 | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` | MATCH |
| 0007 | `c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec` | MATCH |
| 0008 | `285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032` | MATCH |
| 0009 | `412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc` | MATCH |
| 0010 | `c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79` | MATCH |
| 0011 | `cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2` | MATCH |
| 0012 | `7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc` | MATCH |
| 0013 | `06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b` | MATCH |
| 0014 | `ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33` | MATCH |
| 0015 | `5e297591c8096938c90b6748d0d3ed22a8099cf8f4537e7f65f8bc6fa5beaba3` | MATCH |
| 0016 | `e922ff20285751193382a17d9fe7e71726511bff659f4e66b97748e6ad43cdd5` | MATCH |
| 0017 | `580f16d1cdb10c30bae8f3e3c1667c3c4d2552b895fc9dea053d2c9b6adfaa38` | MATCH |
| 0018 | `703a85885a67df953f38ef35302205caeddea249104683f4f751ab20ece0696b` | MATCH |
| 0019 | `c188b638124404bba10cae4c94a678053d49d7a1d07c6e455a48e46524064b50` | MATCH |

Migration 0020 is absent.

### Authoritative sources

The exact source hashes are:

`8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c`,
`e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa`,
`11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3`,
`952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5`,
`ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3`,
`30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6`,
`de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e`,
`29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8`,
`c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb`,
`eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db`:
**10/10 MATCH**.

### Frozen governance prerequisites

| Artifact | SHA-256 | Result |
|---|---|---|
| Governed Learning Policy v1 | `7d9c2fe30548bd18d390d119889c87a93595ac281fa3326691fe486bee49c4ec` | MATCH |
| Phase 21 implementation authorization | `04458c4f1ccead125dd98ddac946ec9d77f8b0212412d13128355b10129c875c` | MATCH |
| Phase 22 governance boundary | `2d5beaebd5b2df1378c0f425354b45d52ff23dd1a5d158adad46572f7656c514` | MATCH |
| Phase 22 ADR-0012 | `4fd6b330081ad4cd24bb55792bf10e9529033156c43d70eba0868be25a403fd0` | MATCH |
| Phase 21 report | `682dc465b1936b0f80478d1110628498b668ffbc36cd8fb50a7cc57068d50980` | MATCH |
| Phase 22 report | `a94ba44e4b968aa2d117d99ebe03f4e094c4e1e684fb380ddc40c220efe3a1b2` | MATCH |
| Phase 23 report | `4cfe38a2c0f3b5686571d6b892b913b7e1d973c256160af0f9731a247de58656` | MATCH |
| Effectiveness Policy v1 | `3e2f2b5b3f335bcb425c4b3d8043c2b541de56b0a7b14fbc63b8f48e4392758f` | MATCH |
| Controlled QMS Action Policy v1 | `29829c38745db67985fb1523837c79276508bdc9d2136b64442ea238ed13566f` | MATCH |

## 24. Protected-target invariance and runtime-change evidence

This gate did not open a database and did not execute a target command. It made
no code, schema, migration, grant, RLS, settings, event allowlist, test or
runtime change. ModelPolicy, AgentDefinition, KnowledgeLayerRule, Standard,
StandardEdition, Clause, RequirementControl, KnowledgeLayerBinding and prompt/
retrieval provenance remain unchanged.

The entry protected implementation hashes were recorded and are rechecked at
final verification:

| File/boundary | Entry SHA-256 |
|---|---|
| `backend/foundation/models.py` | `5c809744810abeee1e956102f4d14d653e70b2064ee26026580dce8eaf2e5be7` |
| `backend/foundation/agent_runtime.py` | `6767e2098365536b88d4d8e9afdaef0f8b796383c79d7f40e0e0ea91b964ec2d` |
| `backend/foundation/knowledge_layer.py` | `ad355cd34fa7a03f1ba30cbe2e78f8a1a8de7859d0b05be337639e2c1c4597c3` |
| `backend/foundation/governed_learning.py` | `1a544de5133eaa4966a013c93d98ce67bdb786ef6f8b564628bbee4004b7dc97` |
| `backend/foundation/learning_proposal_governance.py` | `186e36a0603b11861e8c003626c23ef2a1c4bd22b3c961142e47d7656e0c2e4b` |

No expensive PostgreSQL or full backend suite was rerun for this documentation-
only gate, as required. Verification is limited to hashes, path/diff inspection
and whitespace checks.

## 25. Git hygiene and residual blockers

The only intended Phase 24 change is this report. The unrelated dirty worktree
was preserved. Repository-wide `git diff --check` may retain the pre-existing
`frontend/src/components/Layout/Sidebar.jsx:28` trailing-whitespace finding;
this report is checked separately and must be clean.

Blocking items are:

1. **P1 — exact delta material absent:** `LearningProposal` stores only a hash;
   no application can consume proposal-owned material or recompute the hash.
2. **P1 — operation/capability mismatch:** Phase 23 `revise_*` capabilities are
   wider than every evaluated first-operation allowlist and cannot be silently
   reinterpreted.
3. **P1 — least-privilege atomic seam absent:** existing curator roles have
   broader catalog INSERT rights and their current service aliases do not prove
   one-connection composition with application claim, target ledger, audit and
   receipt.
4. **P1 candidate-specific validation absent:** no DB/service contract proves
   ModelPolicy removal-only semantics, AgentDefinition autonomy decrease, or
   KnowledgeLayerRule trusted source-reference correction.

There are 0 P0 blockers because no application is authorized or implemented.
There are 4 P1 blockers to selecting and implementing a first operation.

## 26. Final verdict

**PHASE 24 — FIRST LEARNING TARGET APPLICATION CANDIDATE SOURCE/POLICY +
SECURITY DESIGN GATE: NOT PROMOTED.**

The fail-closed result preserves vN history, global governance, human gates,
guardrails, autonomy, normative separation, tenant isolation and the Phase
21–23 inert boundary. Phase 25 application POC is not authorized.

| Candidate/component | State | Evidence | Risk/next action |
|---|---|---|---|
| ModelPolicy removal-only candidate | FAIL | no frozen delta; broad `revise_model_policy`; JSON safety comparison incomplete | define delta/operation profile before reconsideration |
| AgentDefinition autonomy-reduction candidate | FAIL | no frozen delta; broad `revise_agent_definition`; monotonic DB rule absent | define exact decrease-only contract before reconsideration |
| KnowledgeLayerRule source-reference candidate | FAIL / NEAREST | no frozen delta; broad `revise_knowledge_layer_rule`; source trust contract absent | close shared blockers, then validate source registry semantics |
| Prompt/rule bundle | INELIGIBLE | provenance string only | separate target lifecycle gate |
| Retrieval configuration | INELIGIBLE | no promoted target/curator/version lifecycle | separate target and poisoning/isolation gate |
| Frozen migrations | PASS | 19/19 SHA-256 MATCH; no 0020 | preserve |
| Authoritative sources | PASS | 10/10 direct read and hash MATCH | preserve |
| Governance history | PASS | prerequisite hashes MATCH | preserve |
| Protected targets/runtime | PASS | documentation-only; protected implementation hashes unchanged | retain zero-effect boundary |
| Phase 24 promotion | **NOT PROMOTED** | no candidate passes all mandatory gates | run blocker-closure gate only |

## NEXT_CODEX_PROMPT

Execute PHASE 24.1 — EXACT LEARNING PROPOSAL DELTA + TARGET-OPERATION CAPABILITY
BLOCKER CLOSURE DESIGN GATE exclusively in `/home/felipe/proyectos/isosmart`.
Do not select or apply a learning target, create a target successor, add migration
0020, create an executor/receipt/event/grant, deploy, use any database, or produce
external effects. Preserve migrations 0001–0019, all ten authoritative sources,
Phase 21–23 governance history and every protected target byte-for-byte. Design
only: (1) an immutable proposal-owned or content-addressed canonical delta
artifact that is created with a LearningProposal revision and can be loaded
without application-time payload replacement; (2) deterministic versioned
canonicalization and target-specific delta schemas whose hash is bound directly
through review, decision and authorization; (3) new exact operation IDs/versions
that do not reinterpret the existing `revise_*` capabilities; (4) a
one-connection least-privilege capability architecture reusing canonical curator
logic, comparing constrained service and target-specific SECURITY DEFINER/
dedicated-curator-function options with fixed search path and no table DML for
the executor; and (5) target-specific validation profiles for ModelPolicy
approved-model removal only, AgentDefinition autonomy reduction only, and
KnowledgeLayerRule validated source-reference correction only. Prove on paper
that old proposals/authorizations lacking exact delta material remain inert and
cannot be upgraded or rebound. Emit PROMOTED only if the frozen delta,
capability, atomicity and validation contracts are exact enough for a later
additive inert foundation implementation gate; otherwise emit NOT PROMOTED with
only remaining exact blockers and exactly one next prompt.
