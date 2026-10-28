# Phase 18 — EffectivenessCheck Source/Policy Blocker Closure + Controlled Execution Operational Readiness Design Gate

**Date:** 2026-08-24

**PostgreSQL:** 18.6 official image, ephemeral only

**Final PostgreSQL run:** `20260824T212421Z_505dda`

**Effectiveness policy:** `effectiveness-check-policy/v1`, non-normative

**Verdict:** **PROMOTED**

## 1. Phase 17 entry and scope

Phase 16 and Phase 17 entered PROMOTED. The only controlled forward QMS action
remains `opportunity.defer_evaluation` over `Opportunity`, exact transition
`under_evaluation -> deferred`. `opportunity.resume_evaluation` remains a
separately planned/approved/authorized compensation. Human Approval and maximum
autonomy A3 remain unchanged under non-normative
`controlled-qms-action-policy/v1`.

Migrations 0001–0016 were treated as frozen. Phase 18 added no migration 0017,
model, table, API, executor, action, generic adapter, telemetry dependency,
deployment or environment enablement. It created only:

- `docs/governance/EFFECTIVENESS_CHECK_POLICY_V1.md`;
- `docs/operations/CONTROLLED_EXECUTION_RUNBOOK_V1.md`;
- `docs/adr/0011-effectiveness-assessment-governance-operational-readiness.md`;
- this report.

## 2. Seven-blocker closure

| # | Blocker | State | Closure |
|---:|---|---|---|
| 1 | Outcome semantics | **CLOSED** | exactly `effective`, `ineffective`, `inconclusive`, `unknown`; uncertainty meanings do not overlap |
| 2 | Actor authority | **CLOSED** | human QMS authorized reviewer only; AdminApps permissions `qms.effectiveness_check.record` and, for correction, `.supersede`; system/measurement are evidence sources only |
| 3 | Timing / due semantics | **CLOSED** | exact trusted planned `due_at` is observation-interval end/due instant, after resulting commit; no client override or global window |
| 4 | Evidence cardinality/validation | **CLOSED** | finite 1..N exact immutable revisions, no semantic numeric maximum, no exact duplicates/latest/cross-boundary/truncation |
| 5 | MeasurementDefinition linkage | **CLOSED** | conditionally required, exactly one revision when criteria/due use what/method/when; otherwise absent; no MeasurementRecord |
| 6 | Correction/version lineage | **CLOSED** | immutable complete records with linear supersession, revision +1, one leaf, no fork/self/cycle/cross-boundary/execution change |
| 7 | Event/audit semantics | **CLOSED** | one `effectiveness_check.recorded` v1 event for original/correction plus atomic Outbox/Audit; IDs/hashes/provenance, no raw blobs |

Result: **7/7 CLOSED**.

## 3. Direct authoritative-source reconciliation

All ten source artifacts were read directly in their native package/text form;
DOCX XML and all eleven XLSX sheets were inspected rather than relying only on
prior reports.

| Source | Direct source fact | Limitation / policy consequence |
|---|---|---|
| Integrated DOCX | runtime explicitly orders Execute → measure effectiveness; 6.1.3 evaluates opportunity-action results; 9.1.1 defines what/method/when; 10.2 reviews/verifies effectiveness and retains evidence; entity list names EffectivenessCheck fields | no closed outcome, actor, cardinality, exact execution FK or correction/event contract |
| Draw.io | separate `Execute` and `Effectiveness` runtime nodes; Evidence/Approval graph nodes | boundary only; no field semantics |
| Mermaid | `EXE --> EFF[Medir eficacia] --> MEM`; Human Gate precedes execution | proves separation/order, not automatic learning authority |
| XLSX (11 sheets) | DB_Entities gives `check_id; subject_type; subject_id; method; due_at; result; evidence_id`; 6.1.3/9.1.1/10.2 rows require results/effectiveness/evidence; Agent Catalog names Performance, Corrective and Evidence Verifier roles | one evidence column is a sketch; agents do not establish record authority |
| Nodes CSV | graph includes 9.1.1 measurement/evaluation and 10.2.1/10.2.2 correction/evidence requirements | no EffectivenessCheck contract |
| Edges CSV | connects 9.1.1 and 10.2 requirements to modules/layers; operations can provide data/trigger corrective analysis | no actor/outcome/cardinality/timing derivation |
| Source DDL | separate tenant EffectivenessCheck with method, nullable due/result, one Evidence FK and completion time | partial reference DDL lacks Organization, RLS, ActionExecution/Receipt provenance, lineage and governed authority |
| OpenAPI | Evidence registration and human Approval decision operations exist | no EffectivenessCheck endpoint/schema; no API added |
| Master JSON | same entity fields, CorrectiveAction relation, 6.1.3/9.1.1/10.2 semantics; Evidence Verifier validates origin/integrity/currentness/coverage | Learning Optimizer description is not authority for automatic learning; no exact assessment contract |
| LEEME | single business object + multiple normative relations and historical evidence principle | architecture principle, not lifecycle/outcome policy |

The sources prove a separate, evidence-dependent assessment after execution and
support `due_at`, method/result and measurement what/method/when. They do not
define the seven closed application semantics. Those are explicitly Product
Policy, never described as ISO requirements.

## 4. Source fact vs Product Policy vs unresolved

| Semantic | Classification | Decision/evidence |
|---|---|---|
| Effectiveness follows and differs from execution | **A — authoritative source fact** | DOCX, Mermaid, Draw.io runtime order |
| effectiveness evaluates opportunity-action results | **A** | source 6.1.3; 9.1.1; 10.2 |
| named method/due/result/Evidence fields | **A** | DOCX/XLSX/JSON/DDL |
| four exact outcomes and their meanings | **B — ISO Smart Product Policy** | policy v1 §3 |
| human-only attestation and AdminApps permission IDs | **B** | policy v1 §4 |
| exact due derivation/governed interval | **B** | policy v1 §5 |
| Evidence 1..N, exact revision rules | **B** | policy v1 §6 |
| conditional single MeasurementDefinition | **B** | policy v1 §7, bounded by Phase 6 source gate |
| immutable linear supersession | **B**, aligned with source architecture append/supersede principle | policy v1 §9 |
| one recorded event + atomic audit contract | **B**, aligned with promoted Event/Audit architecture | policy v1 §10 |
| production SLO/SLA numbers | **C — unresolved / future release blocker** | no source or current operational policy; none invented |
| independent system assessor | **C — future policy version** | explicitly prohibited in v1; does not block human-attested foundation |

No unresolved C item blocks the Phase 19 human-attested foundation contract.
Both remain fail-closed outside v1.

## 5. Product Policy decisions

The versioned policy is
`docs/governance/EFFECTIVENESS_CHECK_POLICY_V1.md`, status
**APPROVED FOR IMPLEMENTATION GATE**. It repeatedly states **NOT AN ISO
REQUIREMENT** and authorizes only later design/implementation work, not runtime
or deployment.

### Outcome taxonomy

- `effective`: performed after interval; all mandatory criteria supported and
  none disproved.
- `ineffective`: performed after interval; at least one business-objective
  criterion disproved.
- `inconclusive`: evaluation completed, but valid Evidence is conflicting,
  ambiguous or insufficient for a reliable positive/negative conclusion.
- `unknown`: evaluation could not be performed because required Evidence was
  unavailable/inaccessible/invalid or another blocking condition was recorded.

Unknown/inconclusive require reason code and explanation. Unknown still requires
at least one exact Evidence revision documenting the attempt/blocker; it does
not pretend missing evidence was available.

### Actor authority and AdminApps boundary

Only an authenticated human QMS authorized reviewer may attest v1. The trusted
server-side AdminApps decision must carry active tenant and exact Organization
scope, applicable MFA/access context and permission
`qms.effectiveness_check.record`; supersession additionally needs
`qms.effectiveness_check.supersede`. UserProjection existence or client input is
never authority.

System-assisted and measurement-derived assessment are evidence-source labels,
not actor authority. ISO Smart records external actor/authority provenance;
AdminApps remains identity/global-role/MFA/access system of record.

### Timing / `due_at`

`due_at` is the UTC end of the approved observation interval and the moment the
assessment becomes due. It is supplied only by frozen trusted effectiveness
planning context bound to execution/target/policy and approved by the reviewer;
it must be later than the deferred revision commit. Effective/ineffective/
inconclusive cannot be recorded early. No 7/30/90-day default exists.

### Evidence cardinality and validation

Minimum 1, finite N, no semantic numeric maximum. Transport protection may
batch but never truncate; failure is atomic. Exact revision ID/lineage/revision/
hash is mandatory. Same exact revision is unique. Multiple revisions of one
lineage require an explicit chronological-comparison criterion. Latest/current,
draft aliases, hash/provenance mismatch, cross-tenant and cross-Organization are
rejected. Raw content is not copied.

### MeasurementDefinition

Exactly one immutable revision is required if criteria or due derivation use
its what/method/timing; otherwise it is absent. Observations remain exact
Evidence. No MeasurementRecord, value, measured_at, unit, formula or threshold
result is asserted.

### Correction/version model

Corrections create a complete immutable superseding record. Revision increments
by one from the exact current leaf; tenant, Organization, ActionExecution,
Receipt and target remain identical. Reason, actor, authority and time are new.
Fork, self-reference, cycle, predecessor reuse, cross-boundary or destructive
edit are rejected. All history remains readable.

### Event and audit contract

Every original/correction emits one `effectiveness_check.recorded` schema v1;
revision and `supersedes_check_id` express correction. Payload carries IDs,
outcome, actor provenance, due/assessed time, evidence IDs, optional exact
MeasurementDefinition, target before/after and execution chain. It contains no
raw Evidence/prompt/secret.

Check, Evidence links, event, Outbox and ImmutableAuditLog must be one future
transaction. Audit reconstructs tenant/Organization, actor/authority,
execution/receipt/plan/authorization, target revisions, outcome/reason,
criteria hash, Evidence IDs/hashes, MeasurementDefinition, timing, trace,
event/outbox and supersession.

## 6. Effectiveness intent and boundaries

The exact v1 business intent comes from Product Policy v1's meaning of
`deferred`: during the approved interval, keep the exact Opportunity lineage out
of active internal evaluation for the approved governance purpose, without an
evaluation decision or unauthorized downstream action defeating that purpose.
The status transition alone is not a criterion of benefit.

Required invariants:

- execution succeeded != effective;
- execution failed != ineffective;
- COMMITTED != effective;
- compensation executed != ineffective;
- Recommendation confidence has no effectiveness threshold;
- no outcome changes execution/governance history;
- no outcome automatically compensates/resumes or starts a new action;
- no outcome automatically learns, retrains, tunes, changes ModelPolicy,
  Recommendation or Knowledge Layer; and
- no outcome changes certifiability or normative interpretation.

## 7. Operational readiness runbook

`docs/operations/CONTROLLED_EXECUTION_RUNBOOK_V1.md` defines:

- role categories: Platform operator, Security operator, QMS authorized
  reviewer, Release authority and Incident commander;
- exact first response and protected idempotency handling;
- no raw-SQL repair and immutable-history prohibitions;
- additive/versioned repair authority with separation of duties;
- disable and multi-authority enable conditions;
- forward-only retained-history release markers;
- observability fields and conceptual alerts; and
- numeric SLO/SLA as a future release blocker.

### COMMITTED

Return the exact existing Receipt as replayed after matching Authorization,
Plan/hash, action/policy, boundaries, target revisions, trace and exactly-one
artifact counts. Never retry, compensate or claim effectiveness. Any later
mismatch escalates and may disable the capability.

### NOT_COMMITTED

Prove no durable claim/Receipt, exact unique unchanged target leaf/fingerprint,
active tenant/Organization, effective human Approval, valid Authorization,
exact Plan hash/policy/preconditions and enabled capability. Then allow one
normal recoverable invocation. New ambiguity returns to reconciliation.

### INCONSISTENT

No retry or automatic repair. Open incident, assign owners, disable if further
execution could compound damage, preserve execution/receipt/revision/event/
outbox/audit and governance evidence, classify cause, and use only a separately
approved additive forward repair. If none exists, freeze capability.

### Repair, disable and enable authority

QMS reviewer authorizes business meaning, Security operator integrity/security,
and Release authority the forward change. Immutable business/governance/event/
audit history is never rewritten. Disable on INCONSISTENT, RLS/ACL/security
breach, artifact mismatch, ambiguous ownership, systemic conflicts, invalid
release boundary or unexpected capability state. Re-enable only after root
cause, reconciliation/quarantine, full regression, security clearance, QMS
acceptance, release approval and enablement audit. No self-enable.

### Forward-only deployment policy

Read-only pre-release checks mark `NO_CONTROLLED_HISTORY` or
`CONTROLLED_HISTORY_EXISTS`, and `CAPABILITY_DISABLED` or
`CAPABILITY_ENABLED`. Any controlled history makes downgrade below 0015
forbidden. Operational rollback is disable → preserve/read → reconcile →
forward fix, never delete history or weaken RLS.

### Observability and alerts

Stable fields: tenant, Organization, trace, Execution, Plan/hash,
Authorization, hashed idempotency, action/policy, target lineage, before/after
revisions, reconciliation outcome/reason, Receipt, artifact counts, capability
state, release/migration identity and timestamp. No raw key, secret, token,
prompt or Evidence content.

Conceptual alerts cover INCONSISTENT, intervention-required execution,
Receipt/event/outbox/audit mismatch, RLS/ACL/search-path failure, repeated
unexpected idempotency conflicts, unexpected capability state, downgrade attempt
and audit/reconciliation failure. No monitoring stack or SLA number was added.

## 8. Complete Phase 16/17 behavioral evidence

Final isolated PostgreSQL lifecycle used official PostgreSQL 18.6 through Podman
at a run-scoped endpoint/database. The harness first executes the complete Phase
16 matrix, then Phase 17 hardening.

| Matrix | Result | Evidence |
|---|---|---|
| controlled forward | PASS | exact under_evaluation → deferred |
| compensation | PASS | separate success + stale denial; distinct wrapper/governance |
| public-command golden parity | PASS | shared primitive semantics |
| autocommit rejection | PASS | transaction guard, zero mutation |
| SECURITY DEFINER / hostile search_path / ACL | PASS | fixed path, exact grants, direct DML denied |
| RLS and tenant/Organization boundary | PASS | ENABLE+FORCE, A/none/B, cross-boundary deny |
| concurrency/idempotency/lost response | PASS | one winner, exact replay/conflict |
| forced rollback | **13/13 PASS** | no partial business/execution artifacts |
| protocol ambiguous COMMIT | PASS | server COMMIT + lost acknowledgment → COMMITTED exact replay |
| pre-COMMIT disconnect | PASS | NOT_COMMITTED then one safe retry |
| INCONSISTENT | PASS | fail closed, no manufactured success |
| claim race/provenance | PASS | one creator/waiter; distinct provenance conflict |
| abandoned/running claim | PASS | no stealing; explicit intervention |
| owner privilege minimization | PASS | exact role/ownership/membership/table/sequence/function assertions |
| capability disable | PASS | new controlled execution denied; public command/history retained |
| retained history | PASS / FORWARD-ONLY | 0016 reverse safe; 0015 reverse intentionally blocked without loss |
| Effectiveness schema | ABSENT | design gate only |

The complete Phase 16 and Phase 17 matrices passed, including the inherited
Phase 15.2 24/24 acceptance coverage. No second controlled forward action,
generic QMS adapter or arbitrary status transition capability exists.

## 9. Backend, foundation and Django integrity

| Gate | Result | Delta from Phase 17 baseline |
|---|---|---|
| backend (`authentication core integration leadership foundation`) | **165 PASS / 0 FAIL / 0 SKIP** | 0 |
| foundation isolated | **67 PASS / 0 FAIL / 0 SKIP** | 0 |
| `manage.py check` | PASS, zero issues | 0 |
| `makemigrations --check --dry-run` | PASS, no changes | no 0017 |
| Python compilation | PASS | 0 |

Expected negative endpoint warnings occurred. The pre-existing Chroma/PostHog
telemetry attempted DNS during the legacy suite and failed closed; it is not
imported or invoked by controlled execution/Phase 18 paths.

## 10. Frozen hashes and schema absence

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

`makemigrations` detected no changes; there is no 0017 and no EffectivenessCheck
runtime class/table/API.

### Authoritative source hashes

| Artifact | SHA-256 | Result |
|---|---|---|
| DOCX | `8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c` | MATCH |
| Draw.io | `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa` | MATCH |
| Mermaid | `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3` | MATCH |
| XLSX | `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5` | MATCH |
| Nodes CSV | `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3` | MATCH |
| Edges CSV | `30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6` | MATCH |
| DDL | `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e` | MATCH |
| OpenAPI | `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8` | MATCH |
| JSON | `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb` | MATCH |
| LEEME | `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db` | MATCH |

Result: **10/10 MATCH**.

## 11. Zero side effect and teardown

Phase 18 performed no production/staging/shared DEV/QA connection, deployment,
AdminApps/MedSupplier write, network business action, broker/provider call,
notification, external mutation or controlled QMS mutation outside regression
fixtures in isolated PostgreSQL.

The initial sandboxed PostgreSQL attempt could not start Podman and nevertheless
reported teardown PASS with container/volume/temp absent. The authorized final
run used the official image and removed its run-scoped database, eleven roles,
container, volume and temp directory. Finalizer result:

```text
container_absent = true
volume_absent = true
temp_absent = true
teardown = PASS
```

No persistent proxy/fault-injection resource remained; the protocol proxy is
process-local and its socket/thread finalizer passed inside the matrix.

## 12. Git hygiene

Entry status contained unrelated user changes and the known Sidebar trailing
whitespace. Phase 18 did not modify Sidebar, other workspaces, source artifacts,
migrations or application runtime. Scoped Phase 18 artifacts pass whitespace
validation. Repository-wide `git diff --check` continues to identify only the
pre-existing Sidebar issue and is not attributed to this phase.

## 13. Residual risks and release blockers

1. AdminApps must implement/map the two exact permission decisions before a
   runtime command can pass authority; v1 fails closed until then.
2. Evidence capable of proving active-evaluation behavior must exist as exact
   governed revisions; an assessment becomes `unknown`/`inconclusive`, never a
   fabricated binary result, when it does not.
3. Independent system assessment remains prohibited and requires v2 plus an
   observation/authority/security gate.
4. Numeric operational SLO/SLA, alert routing and paging targets remain a
   production release blocker; none was invented in this design gate.
5. The next implementation must prove atomic Evidence-link/event/outbox/audit,
   RLS, no-fork lineage and retained history on PostgreSQL 18.6 before any API or
   environment enablement.

There are **0 P0** and **0 P1** defects blocking the Phase 19 EffectivenessCheck
foundation implementation gate. The residual items are fail-closed release or
future-policy boundaries.

## 14. Promotion verdict

**PHASE 18 — EFFECTIVENESSCHECK SOURCE/POLICY BLOCKER CLOSURE + CONTROLLED EXECUTION OPERATIONAL READINESS DESIGN GATE: PROMOTED**

| Blocker/component | State | Evidence | Risk/next action |
|---|---|---|---|
| Outcome semantics | CLOSED | policy v1 §3, four non-overlapping outcomes | preserve uncertainty/reasons in schema |
| Actor authority | CLOSED | human-only + exact AdminApps permissions/scope | implement fail-closed mapping |
| Timing/due | CLOSED | trusted frozen observation interval/due instant | bind exact planning provenance |
| Evidence | CLOSED | 1..N exact immutable revisions; strict boundary/hash rules | junction + atomic validation in Phase 19 |
| MeasurementDefinition | CLOSED | conditional exact single revision; no observation model invention | implement nullable conditional FK/rules |
| Correction lineage | CLOSED | immutable linear supersession | prove leaf/no-fork/cycle constraints |
| Event/audit | CLOSED | one recorded v1 event + Outbox/Audit atomic contract | implement and rollback-test |
| Execution/effectiveness | SEPARATE / PASS | policy invariants + schema absent | never infer from Receipt/reconciliation |
| Compensation | SEPARATE / PASS | Phase 16 distinct governance regression | no automatic resume |
| Learning/normative | PROHIBITED AUTOMATION / PASS | policy boundaries | future separately governed workflow only |
| Operational runbook | APPROVED DESIGN | COMMITTED/NOT_COMMITTED/INCONSISTENT procedures | operational adoption before release |
| Repair governance | CLOSED | multi-authority additive procedure; immutable exclusions | no raw SQL |
| Capability disable/enable | CLOSED | exact triggers, multi-party re-enable | audit environment marker |
| Forward-only release | CLOSED | retained-history markers; Phase 17 regression | block downgrade below 0015 |
| Observability/alerts | CLOSED DESIGN | stable sanitized fields/conditions | SLO/routing future release blocker |
| No second action | PASS | source/runtime scan + Phase 16/17 harness | preserve single forward wrapper |
| Phase 16 matrix | PASS | full inherited run; 13/13 rollback | none |
| Phase 17 matrix | PASS | ambiguity/reconciliation/claim/history/disable | none |
| Backend/foundation | 165/165; 67/67 PASS | executed 2026-08-24 | baseline delta 0 |
| Django integrity | PASS | check/drift/compile | no migration 0017 |
| Frozen migrations | 16/16 MATCH | SHA-256 | remain frozen |
| Source artifacts | 10/10 MATCH | direct read + SHA-256 | preserve byte-for-byte |
| External effects | ZERO | isolated regression only | no deployment |
| Teardown | PASS | finalizer resource absence | none |
| Promotion | **PROMOTED** | 7/7 closed; 0 P0/P1 blocking implementation gate | Phase 19 only |

## NEXT_CODEX_PROMPT

Implement PHASE 19 — EFFECTIVENESSCHECK FOUNDATION IMPLEMENTATION exclusively in `/home/felipe/proyectos/isosmart` under approved non-normative `effectiveness-check-policy/v1`, without deploying, enabling production/staging/shared DEV/QA, adding a second QMS action, broadening `opportunity.defer_evaluation` or `opportunity.resume_evaluation`, creating external effects, automatic compensation or automatic learning. Preserve migrations 0001–0016, all ten authoritative source artifacts, `CONTROLLED_QMS_ACTION_POLICY_V1`, ADR-0007–ADR-0011 and the Phase 18 operational runbook. Implement only EffectivenessCheck, exact EffectivenessEvidence revision links, conditionally required exact single MeasurementDefinition revision, trusted AdminApps human actor/authority provenance, frozen due_at planning semantics, exact ActionExecution/Receipt/Plan/Authorization/Decision/Recommendation and Opportunity before/resulting provenance, immutable linear supersession with no fork/self/cycle/cross-boundary lineage, `effectiveness_check.recorded` schema v1, TransactionalOutbox, ImmutableAuditLog, ENABLE+FORCE RLS and one atomic command. Use PostgreSQL 18.6 ephemeral first; prove outcome/authority/timing/evidence/measurement constraints, cross-tenant and cross-Organization denial, append-only history, event/outbox/audit rollback at every failure point, no execution-history mutation, no confidence mapping, no certifiability contamination, no automatic resume/learning and zero external effects. Add migration 0017 only if the complete approved contract is implemented, rerun complete Phase 16/17 matrices, backend/foundation regression, Django integrity, frozen hashes, source hashes, git hygiene and mandatory teardown, and fail closed rather than weaken the Phase 18 policy.
