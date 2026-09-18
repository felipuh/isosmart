# Phase 15.1 — Controlled QMS Action Product Policy + Blocker Closure Gate

**Fecha:** 2026-08-24

**Naturaleza:** design/product-policy gate; docs-only

**Veredicto:** **NOT PROMOTED**

## 1. Resultado ejecutivo y blockers previos

Phase 15 quedó `NOT PROMOTED` porque ninguna acción probó simultáneamente una
transición legal, impacto estándar/bajo inequívoco, reversibilidad empresarial,
compensación exacta, replay ya-en-destino y token stale compatible. No creó
adapter, executor o migration.

Phase 15.1 crea Product Policy v1 y cierra esos blockers semánticos para un solo
candidato propuesto: diferir temporalmente la evaluación interna de una
Opportunity. La reevaluación completa encuentra un blocker técnico obligatorio
que la policy no puede falsear: el command promovido no compone dentro de la
transacción única requerida con ActionExecution/receipt. También falta una
frontera de privilegio estrecha para que EXECUTOR invoque sólo esa acción sin
DML genérico. Por un FAIL, no hay selección y Phase 15.1 permanece
`NOT PROMOTED`.

## 2. Fuente versus Product Policy

| Categoría | Hecho/decisión |
|---|---|
| AUTHORITATIVE SOURCE FACT | Opportunity existe, pertenece a Process y contiene hypothesis, benefit, feasibility y status. |
| AUTHORITATIVE SOURCE FACT | A2 prepara sin ejecutar; A3 ejecuta tras aprobación; cambios de registro/materiales requieren aprobación. |
| AUTHORITATIVE SOURCE FACT | Las fuentes preservan evidencia/provenance y separan Approval, ActionExecution y Effectiveness. |
| AUSENCIA DE FUENTE | No hay valores de status, grafo de transición, impacto por transición, inverso, replay o token stale. |
| ISO SMART PRODUCT POLICY | `under_evaluation -> deferred`, su significado limitado, impacto `standard`, compensación inversa y A3 obligatorio. |

**Invariante:** la policy define comportamiento de ISO Smart; no define,
modifica, interpreta ni añade un requisito ISO certificable. No toca
`RequirementControl`, `KnowledgeLayerRule`, catálogos ni conteos normativos.

## 3. Reconciliación directa de las diez fuentes

Se inspeccionaron directamente XML DOCX; las hojas XML del XLSX; JSON; DDL;
OpenAPI; Mermaid; Draw.io; ambos CSV y LEEME. DOCX aporta el pipeline y A0-A4;
XLSX/JSON aportan entidades/campos; DDL confirma `Opportunity.status` como texto;
diagramas/CSV aportan topología; OpenAPI no expone esta mutación; LEEME preserva
el principio de objeto empresarial único. Ninguna fuente enumera estados ni
autoriza la transición propuesta como requisito ISO.

## 4. Product Policy v1

- Artifact: `docs/governance/CONTROLLED_QMS_ACTION_POLICY_V1.md`
- Version: v1
- Status: `PROPOSED — NOT APPROVED FOR CONTROLLED POC`
- Authority: ISO Smart Product Governance
- Candidate action: `opportunity.defer_evaluation`
- Target: `Opportunity`
- Legal transition: `under_evaluation -> deferred`
- Compensation: `opportunity.resume_evaluation`,
  `deferred -> under_evaluation`
- Impact: `standard` under every listed precondition
- Human Approval: required
- Autonomy ceiling: A3

Future semantic changes require v2+; historical policy identities may not be
silently overwritten.

## 5. Candidate matrix after Product Policy v1

| Candidate | Source object/property | Narrow promoted command | Policy transition/inverse | Impact/revision | Atomic command composition | Overall |
|---|---|---|---|---|---|---|
| Stakeholder | object/fields | `update_stakeholder` | none | in-place, no version | not analyzed after semantic FAIL | FAIL |
| StakeholderRequirement | object/fields | `supersede_stakeholder_requirement` | none | revision available; inverse absent | command owns transaction | FAIL |
| Process | object/fields | `update_process` | none | in-place, wider graph impact | command owns transaction | FAIL |
| ContextItem | object/fields | `supersede_context_item` | none | revision available; inverse absent | command owns transaction | FAIL |
| QmsScope | object/fields | `revise_scope` | none | applicability is material | command owns transaction | FAIL |
| Risk | no source status | `revise_risk` | none | assessment change material | command owns transaction | FAIL |
| **Opportunity** | **status direct** | **`change_opportunity_status`** | **v1 exact forward/inverse** | **standard; exact revision** | **FAIL: rejects outer atomic; narrow executor boundary absent** | **FAIL** |
| Objective | status direct | `change_objective_status` | none | commitment/metric/date impact | command owns transaction | FAIL |
| Change | status direct | `change_change_status` | none | governed material change | command owns transaction | FAIL |
| MeasurementDefinition | definition fields | `revise_measurement_definition` | none | measurement meaning changes | command owns transaction | FAIL |
| Document | metadata fields | `revise_document_metadata` | none | in-place; access/control risk | command owns transaction | FAIL |
| Evidence | revision fields | `supersede_evidence` | none | use/history not neutralized | command owns transaction | FAIL |
| Recommendation | status exists | no evolution command | none | frozen provenance | unavailable | FAIL |

Creations remain rejected because DELETE is not a business inverse. Exactly one
candidate received policy semantics; it still fails mandatory technical gates.
The tie-break is not reached.

## 6. Candidate contract and business proof

Proposed literals:

```text
action_type = "opportunity.defer_evaluation"
target_type = "Opportunity"
```

The source-supported property is `Opportunity.status`; Process, hypothesis,
benefit, and feasibility are also direct source fields and must remain equal.
Product Policy alone supplies the two values and legal transition.

`impact = standard` is business-level: only evaluation eligibility of one
tenant/Organization Opportunity changes temporarily. It neither accepts nor
rejects it; changes no assessment content or linked Process; communicates
nothing externally; has no financial/security/identity/normative effect; and
does not delete or overwrite history.

Business reversibility is exact only while the forward result remains current:
`opportunity.resume_evaluation` restores eligibility from `deferred` to
`under_evaluation`. It must create a new governed revision through the same
status-command semantics. It is invalid after a successor, substantive change,
unrelated transition, policy withdrawal, or boundary/provenance mismatch.
Compensation requires its own plan, dry-run, authorization, human approval,
execution, idempotency, event, audit, and receipt.

## 7. Existing command and remaining blocker

`RiskOpportunityObjectiveCommandService.change_opportunity_status` accepts
trusted identity, exact current revision, status, actor, trace, reason, and a
test rollback flag. It copies Process/hypothesis/benefit/feasibility, appends a
revision, rejects non-leaf revisions, emits `opportunity.status_changed` v1,
creates outbox/audit atomically, and rolls back all command artifacts on error.

It is not presently safe to call from controlled execution. Its
`trusted_tenant_context` raises whenever the connection already has an outer
atomic block. Phase 14 commits ActionExecution start before invoking the
executor and completes it afterward in another transaction. Consequently there
is no existing transaction that can atomically cover target lock/mutation,
domain event/outbox/audit, execution terminal state, and receipt. This is a
mandatory FAIL, not a semantic detail to waive.

The executor also must not receive generic Opportunity INSERT permission. A
future design gate must prove an action-specific composition seam and narrow
grant/function/service boundary while preserving the promoted command's domain,
event, audit, and RLS semantics. No such seam is implemented here.

## 8. Expected revision, TOCTOU, concurrency, and idempotency

The expected token is the exact Opportunity `lineage_id`, current
`revision_id`, integer `revision`, status, and canonical hash of Process,
hypothesis, benefit, feasibility, status, tenant, Organization, and lineage.
Dry-run, authorization, and execution each revalidate it; execution does so
under `SELECT FOR UPDATE`. Missing, superseded, mismatched, or unknown state
causes zero mutation.

Lock order: execution/idempotency identity, immutable authorization reads,
exact target revision, domain event stream, audit stream, outbox/receipt.
Append unique predecessor constraints provide a second no-fork defense.
Deadlock/serialization failure rolls back and does not imply success.

Idempotency cases:

1. exact source revision/state: eligible;
2. desired state in the exact receipt-produced revision from the same
   authorization/plan/idempotency identity: return prior receipt, no command;
3. desired state without exact provenance: stale/conflict, not replay success.

## 9. ActionPlan, dry-run, authorization, and trusted execution

The Phase 13 canonical hash can safely represent the contract without a hash
implementation change. Top-level fields contain literal action/target,
Organization, Decision/Recommendation, impact, reversibility, preconditions,
dry-run capability and A3. `parameters` contains only expected revision ID and
number, expected/desired state, expected state hash, policy identity, and
compensation action type. Tenant and Organization authority are server-derived;
there is no arbitrary mutation map.

Dry-run returns target/revision, observed and desired state, legality, every
precondition result, impact, reversibility, compensation availability, policy
identity and plan hash with no mutation. Authorization must bind the exact plan
hash, passed dry-run, effective human Approval, published frozen ModelPolicy,
and A3 ceiling. The future adapter may receive only resolved ActionExecution,
ExecutionAuthorization, and ActionPlan and must derive the target from the
frozen plan.

## 10. Transaction, events, audit, receipt, effectiveness

Required future transaction:

```text
lock/claim ActionExecution identity
-> revalidate authorization/plan/approval/policy
-> lock/revalidate Opportunity
-> invoke governed status command
-> domain event/outbox/audit
-> execution terminal event/outbox/audit + receipt
-> one commit
```

This required transaction is not supported today. Execution events describe
attempt lifecycle; `opportunity.status_changed` describes QMS meaning. Audits
remain separate and linked by trace/execution/target/event IDs.

Receipt fields: Execution/Authorization IDs, plan hash, policy, literal action,
target lineage, before/after revision/state/hash, domain event/outbox/audit
references, outcome, idempotency, compensation eligibility, timestamps, and
`effectiveness_claimed=false`.

Successful execution is not effectiveness. A future EffectivenessCheck would
need the exact receipt, intended queue outcome, measurement time/method, current
revision, and Evidence. It is neither defined nor implemented here.

## 11. Threat matrix

| Threat/failure | Control | Result |
|---|---|---|
| stale target / concurrent transition | exact leaf token + lock + no-fork constraint | no mutation |
| replayed authorization / duplicate execution | exact durable idempotency and prior receipt | replay receipt or conflict |
| wrong target/tenant/Organization | frozen target + trusted tenant + RLS + exact Organization equality | deny/non-leaking error |
| plan hash/policy mismatch | recompute canonical v1 + exact policy identity | deny |
| invalid/ambiguous Approval | effective Approval resolver + active authority | deny |
| compensation after later change | exact forward-result leaf/fingerprint required | compensation denied |
| direct command bypass | service/function allowlist and audit monitoring required | blocker until proven |
| direct DB mutation / executor escalation | no generic DML; RLS; narrow boundary required | blocker until proven |
| audit/event/receipt failure | single transaction required | full rollback; currently blocker |
| unknown condition | fail-closed default | no mutation |

## 12. Security matrix

| Principal | Read target | Prepare | Approve | Authorize | Execute adapter | Direct target mutation | Compensate |
|---|---:|---:|---:|---:|---:|---:|---:|
| APP | tenant-scoped | through existing app boundary | No | No | No | existing commands only, never executor authority | No |
| WORKER | tenant-scoped as granted | Yes | No | No | No | No | prepare only |
| EXECUTOR | exact target/provenance only | No | No | No | future narrow action only | **No** | future separately authorized narrow action |
| HUMAN APPROVER | minimum provenance | No | Yes, narrow gate | No | No | No | approve separate plan only |
| PROJECTOR | projection scope | No | No | No | No | No | No |
| AUDIT WRITER | audit inputs only | No | No | No | No | audit append only | No |
| NORMATIVE CURATOR | no tenant target needed | No | No | No | No | normative catalog only | No |
| AGENT CURATOR | no tenant target needed | policy catalog | No | No | No | agent catalog only | No |

No current principal gains permissions in Phase 15.1.

## 13. Verification and integrity

- initial/final `git status`: executed; pre-existing user changes preserved;
- docs-only files added: policy, successor ADR, this report;
- `git diff --check`: executed; scoped files clean; unrelated pre-existing
  whitespace remains separately identified if reported by whole-tree diff;
- migrations `0001-0014`: **14/14 SHA-256 MATCH**;
- source artifacts: **10/10 SHA-256 MATCH**;
- migration `0015`: absent;
- no adapter/interface/runtime/test/model/API/allowlist/privilege change;
- no QMS command, database harness, provider, external system, production,
  staging, deployment, or side effect;
- `SyntheticNoOpExecutor`: only class with executable executor behavior;
- backend regression/Django/drift/compile: not rerun because no runtime or test
  artifact changed; no unexecuted check is claimed.

### Frozen migration hashes

| Migration | SHA-256 |
|---|---|
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

## 14. Residual blockers and verdict

1. Add/prove a transaction-aware, action-specific composition seam that reuses
   the promoted Opportunity command semantics and permits one atomic commit.
2. Prove a narrow executor privilege boundary with no generic target DML.
3. Only after both pass may Product Governance approve v1 for a controlled,
   ephemeral PostgreSQL POC; this report grants no production authority.

**PHASE 15.1 — FIRST CONTROLLED QMS ACTION PRODUCT POLICY + BLOCKER CLOSURE
GATE: NOT PROMOTED.**

| Candidate/component | State | Evidence | Risk/next action |
|---|---|---|---|
| Opportunity policy candidate | SEMANTICS PROPOSED / NOT SELECTED | exact v1 transition, impact, inverse, replay | command composition and privilege FAIL |
| All other candidates | REJECTED | candidate matrix | no second policy action in v1 |
| Product Policy v1 | PROPOSED | non-normative, versioned artifact | approve only after technical blockers close |
| ADR-0007 | PRESERVED | historical NOT PROMOTED truth | none |
| ADR-0008 | ACCEPTED | records policy and fail-closed result | successor design gate |
| Adapter/real executor | ABSENT | repository scan | do not create yet |
| SyntheticNoOpExecutor | ONLY EXECUTABLE IMPLEMENTATION | code scan | preserve |
| Migrations 0001-0014 | FROZEN / 14/14 MATCH | exact SHA-256 | preserve byte-for-byte |
| Migration 0015 | ABSENT | filesystem check | do not create in design gate |
| Source artifacts | FROZEN / 10/10 MATCH | exact SHA-256 | preserve byte-for-byte |
| QMS/external effects | ZERO | docs-only work | maintain fail-closed |

## NEXT_CODEX_PROMPT

Execute exclusively a docs-and-contract design gate in `/home/felipe/proyectos/isosmart` to close the two remaining Phase 15.1 blockers for the sole proposed action `action_type="opportunity.defer_evaluation"`, `target_type="Opportunity"`, without performing a QMS mutation, registering an adapter, changing the executor allowlist, granting runtime privileges, creating migration `0015`, or modifying any of the ten authoritative source artifacts or frozen migrations `0001-0014`. Preserve Product Policy `controlled-qms-action-policy/v1` as non-normative and preserve ADR-0007/ADR-0008 history. Design and prove, with non-executable contracts or isolated tests only if necessary, (1) a transaction-aware action-specific composition seam that reuses the promoted `change_opportunity_status` domain/event/audit semantics while allowing Opportunity lock/revalidation, domain revision/event/outbox/audit, ActionExecution completion, and receipt to commit atomically, and (2) an executor least-privilege boundary that cannot perform generic Opportunity DML. Revalidate ActionPlan hash compatibility, TOCTOU, idempotency, deadlock ordering, rollback behavior, threat/security matrices, 14/14 migration hashes, 10/10 source hashes, absence of `0015`, synthetic-only execution, zero QMS/external side effects, and emit PROMOTED only if every design criterion is proven; otherwise fail closed with NOT PROMOTED.
