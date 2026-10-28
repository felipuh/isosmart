# Phase 15 — Controlled Domain Adapter Design Gate

**Fecha:** 2026-08-24

**Gate:** `PHASE 15 — CONTROLLED DOMAIN ADAPTER DESIGN GATE`

**Naturaleza:** diseño únicamente; cero mutación QMS/efecto externo

**Veredicto:** **NOT PROMOTED**

## 1. Resultado ejecutivo

No existe evidencia suficiente para seleccionar exactamente una primera
mutación QMS controlada que cumpla todos los criterios obligatorios. La
foundation tiene comandos tenant-safe, versionado, Event/Outbox/Audit y locks,
pero las fuentes no definen para ninguna acción candidata simultáneamente:

- una transición concreta y cerrada;
- clasificación inequívoca de impacto `standard`/bajo;
- reversibilidad empresarial o compensación determinística;
- semántica de idempotencia cuando el estado deseado ya existe.

Por la regla de un solo FAIL, no se selecciona acción. No se creó adapter,
interface, test-double, executor, migration ni registro en el allowlist.
`SyntheticNoOpExecutor` permanece como única implementación ejecutable.

## 2. Estado de entrada y alcance

Se leyó `AGENTS.md` antes de cambios y se ejecutó `git status`. El worktree ya
contenía cambios y archivos no rastreados de fases previas y trabajo ajeno; se
preservaron. No se tocó `/home/felipe/proyectos/adminapps`,
`/home/felipe/proyectos/ISO_Smart_MedSupplier` ni
`/home/felipe/proyectos/design-system`.

Se leyeron completos los reportes Phase 10-14, Data Architecture, Tenant Model,
Eventing Design, Immutable Audit Design, PostgreSQL RLS Design, Threat Model y
ADR-0001 a ADR-0006. Se inspeccionaron los comandos promovidos de QMS Context,
Risk/Opportunity/Objective, Change/Measurement, Document/Evidence y
Recommendation.

## 3. Reconciliación directa de fuentes

Los diez artifacts se leyeron directamente: XML interno DOCX; workbook OOXML
XLSX y sus hojas de catálogo relevantes; JSON; DDL; OpenAPI; Mermaid; Draw.io;
ambos CSV; y LEEME.

Jerarquía aplicada: DOCX como autoridad funcional; XLSX/JSON como autoridad
estructurada; DDL/OpenAPI como referencias parciales; diagramas/CSV como
topología y relaciones.

| SOURCE | CANDIDATE ACTION | SOURCE EVIDENCE | AFFECTED ENTITY | MUTATION | REVERSIBILITY | IMPLEMENTATION JUSTIFIED? | RATIONALE |
|---|---|---|---|---|---|---|---|
| DOCX §1, §7-8 | cualquier acción material | objeto empresarial único; A2 prepara; A3 ejecuta tras aprobación; A4 sólo guardrails preaprobados/reversibles/monitorizados | todos | no concreta | sólo regla general | No | no identifica una transición de bajo impacto ni su inverso |
| DOCX/JSON/XLSX §4.2 | actualizar Stakeholder/Requirement | determinar y monitorear cambios; HDG para cambios de registro | Stakeholder, StakeholderRequirement | cambio de registro | no definida | No | soporte al objeto, no a un delta bajo/reversible concreto |
| DOCX/JSON/XLSX §4.4 | actualizar Process | mantener procesos, interacciones, responsabilidades, riesgos y evidencia | Process | actualización material | no definida | No | puede afectar operación y responsabilidad; A1-A3 |
| DOCX/JSON/XLSX §4.1/4.3 | revisar Context/Scope | monitorear contexto; definir alcance/aplicabilidad | ContextItem, QmsScope | nueva revisión | no definida | No | alcance/aplicabilidad no es presumiblemente bajo impacto |
| DOCX/JSON/XLSX §6.1 | revisar Risk/Opportunity | evaluar riesgos/oportunidades y decidir acciones | Risk, Opportunity | revisión/status | no definida | No | aceptación/tratamiento puede ser material; estados no enumerados |
| DOCX/JSON/XLSX §6.2 | cambiar Objective | objetivos, responsables, plazos y evaluación | Objective | revisión/status | no definida | No | puede alterar compromisos; estados/transiciones ausentes |
| DOCX/JSON/XLSX §6.3/8.5.6 | cambiar Change | planificar y controlar cambios | Change | revisión/status | no definida | No | cambio explícitamente gobernado; A2-A3/high-impact gate |
| DOCX/JSON/XLSX §9.1.1 | revisar MeasurementDefinition | definir qué/método/momento de medición | MeasurementDefinition | nueva revisión | no definida | No | puede cambiar criterio de desempeño; impacto no clasificado |
| DOCX/JSON/XLSX §7.5 | revisar Document metadata | crear, actualizar y controlar información documentada | Document | owner/type update | no definida | No | owner/type pueden afectar control/acceso; A4 es sólo regla genérica |
| DOCX/JSON/XLSX/DDL | superseder Evidence | Evidence con hash/origen/trust; preservar historia | Evidence | nueva revisión | no definida | No | evidencia histórica no se destruye; una revisión no neutraliza su uso previo |
| DOCX/JSON/XLSX/DDL | cambiar Recommendation | Recommendation tiene status y provenance | Recommendation | desconocida | no definida | No | foundation promovida sólo permite create inmutable; no command reusable |
| Mermaid/Draw.io | cualquier Execute | Human Gate/A4 guardrail precede Execute y Effectiveness sigue después | ActionExecution | etapa conceptual | sólo etiqueta general | No | confirma arquitectura, no el primer delta de dominio |
| CSV nodes/edges | objetos y dependencias | módulos/agentes por cláusula; Process/Risk/Objective/Change/Document conectados | varios | topología | no definida | No | no contiene contratos de transición o compensación |
| OpenAPI | ninguna | Recommendation/basis read, Approval decision, Evidence create | varios | no endpoint de mutación candidata | no definida | No | no autoriza inventar un adapter ni endpoint |
| LEEME | ninguna | objeto único y Compliance Evidence Graph | varios | ninguna | ninguna | No | orientación de importación, no contrato de acción |

### Hallazgo fuente determinante

La frase fuente de A4 es una condición necesaria para una automatización futura,
no una lista de tareas reversibles. Ningún artifact nombra una acción concreta
como “low impact” ni declara un par semántico `A -> B / B -> A`. Los campos
`status` aparecen sin vocabulario cerrado. Por tanto, convertir un status en la
primera acción exigiría inventar semántica.

## 4. Descubrimiento de candidatos y commands promovidos

| Candidate | Promoted target | Existing command boundary | Historical strategy | Gate result |
|---|---:|---|---|---|
| Stakeholder metadata update | Sí | `update_stakeholder` | UPDATE auditado | FAIL |
| StakeholderRequirement supersede | Sí | `supersede_stakeholder_requirement` | nueva revisión | FAIL |
| Process update | Sí | `update_process` | UPDATE auditado | FAIL |
| ContextItem supersede | Sí | `supersede_context_item` | nueva revisión | FAIL |
| QmsScope revise | Sí | `revise_scope` | nueva revisión | FAIL |
| Risk revise | Sí | `revise_risk` | nueva revisión | FAIL |
| Opportunity status change | Sí | `change_opportunity_status` | nueva revisión | FAIL |
| Objective status change | Sí | `change_objective_status` | nueva revisión | FAIL |
| Change status change | Sí | `change_change_status` | nueva revisión | FAIL |
| MeasurementDefinition revise | Sí | `revise_measurement_definition` | nueva revisión | FAIL |
| Document metadata revise | Sí | `revise_document_metadata` | UPDATE auditado | FAIL |
| Evidence supersede | Sí | `supersede_evidence` | nueva revisión | FAIL |
| Recommendation evolution | Sí | ninguno | fila/Basis inmutables | FAIL |

Creation commands were not selected because creation has no deterministic
business inverse in the promoted foundations: DELETE is not an acceptable undo,
and no source-backed withdraw/tombstone command exists for these aggregates.

## 5. Candidate safety matrix

`PASS WITH RESTRICTIONS` means the current foundation supports the property but
the candidate still fails another mandatory property. No numeric score is used.

| Candidate | Source support | Mutation type | Tenant boundary | Organization boundary | Reversibility | Compensation | Idempotency | Concurrency | Stale-state | Human approval | Autonomy ceiling | Business impact | Audit/event | Dependencies | Rollback | Fail-closed | Overall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Stakeholder metadata | PASS WITH RESTRICTIONS | in-place fields | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS (`select_for_update`) | FAIL (no version contract) | mandatory conservatively | A3 | FAIL | PASS | downstream requirements | FAIL | PASS | FAIL |
| StakeholderRequirement supersede | PASS | append revision | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS (exact current revision possible) | mandatory | A3 | FAIL | PASS | Stakeholder/Process | FAIL | PASS | FAIL |
| Process update | PASS | in-place fields | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS (`select_for_update`) | FAIL (no version) | mandatory | A3 | FAIL | PASS | graph/risks/KPIs | FAIL | PASS | FAIL |
| ContextItem supersede | PASS | append revision | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS | mandatory | A3 | FAIL | PASS | risk/scope | FAIL | PASS | FAIL |
| QmsScope revise | PASS | append revision | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS | mandatory | A3 | FAIL | PASS | applicability/processes | FAIL | PASS | FAIL |
| Risk revise | PASS | append assessment | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS | mandatory | A3 | FAIL | PASS | Process/decisions | FAIL | PASS | FAIL |
| Opportunity status | PASS WITH RESTRICTIONS | append revision | PASS | PASS | FAIL | FAIL | FAIL (desired-state semantics absent) | PASS WITH RESTRICTIONS | PASS | mandatory | A3 | FAIL | PASS | Process/improvement | FAIL | PASS | FAIL |
| Objective status | PASS WITH RESTRICTIONS | append revision | PASS | PASS | FAIL | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS | mandatory | A3 | FAIL | PASS | owner/metric/due date | FAIL | PASS | FAIL |
| Change status | PASS WITH RESTRICTIONS | append revision | PASS | PASS | FAIL | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS | mandatory | A3 | FAIL | PASS | Approval/processes | FAIL | PASS | FAIL |
| MeasurementDefinition revise | PASS | append revision | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS | mandatory | A3 | FAIL | PASS | Process/KPI interpretation | FAIL | PASS | FAIL |
| Document metadata | PASS | in-place owner/type | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS (`select_for_update`) | FAIL (no version) | mandatory | A3 | FAIL | PASS | access/control | FAIL | PASS | FAIL |
| Evidence supersede | PASS | append revision | PASS | PASS | FAIL | FAIL | PASS WITH RESTRICTIONS | PASS WITH RESTRICTIONS | PASS | mandatory | A3 | FAIL | PASS | coverage/basis/history | FAIL | PASS | FAIL |
| Recommendation evolution | FAIL | unavailable | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | mandatory | A3 | FAIL | FAIL | frozen provenance | FAIL | PASS | FAIL |

All candidates are internal-only and have no necessary external dependency;
that property passes but cannot cure the mandatory reversibility/impact failures.

## 6. Fail-closed no-selection

**Selected candidate: none.**

The closest technical candidates are the append-revision status commands for
Opportunity and Objective, because they target one aggregate and preserve
history. They still fail because:

1. source fields do not enumerate statuses or transitions;
2. the promoted services validate only non-empty text;
3. no source says any transition is standard/low impact;
4. copying a previous status into a later revision is not proven to undo
   decisions or dependent actions;
5. the correct already-desired result (`idempotent success` versus
   `stale/conflict`) cannot be derived.

No acceptance criterion is relaxed to force a selection.

## 7. Typed adapter contract status

No candidate-specific typed contract is defined or shipped. Doing so would
preselect an action that failed the gate. The following is only the mandatory
shape that the missing source decision must make concrete; it is not an
executable payload or interface:

| Contract element | Required future binding | Current state |
|---|---|---|
| `action_type` | one literal, not free text | BLOCKED |
| `target_type` | one literal aggregate type | BLOCKED |
| `target_id` | exact UUID | structurally possible |
| tenant | derived from trusted execution context | PASS |
| Organization | derived from target and matched to plan/auth | PASS |
| expected state/version | closed typed value + exact revision/version | BLOCKED per candidate |
| desired delta | one closed change | BLOCKED |
| preconditions | complete typed read-only list | BLOCKED |
| idempotency identity | tenant+auth+plan hash+target+expected state | designable after selection |
| trace | exact Phase 14 trace linkage | PASS |

There will be no `model`, `field`, `value`, arbitrary selector or
client-controlled authority.

## 8. Target and expected-state contract

The target must ultimately be one exact tenant/Organization aggregate. Broad
selectors are forbidden. For a revisioned target the expected contract should
include exact `lineage_id`, exact current `revision_id`, and revision number or
canonical state hash. For an in-place target it needs a promoted optimistic
version/hash not currently present, or a command-specific state fingerprint
whose semantics are formally adopted.

Because no target passed, no exact expected-state choice is approved. A missing,
ambiguous or changed version/state is `stale_target` and causes zero mutation.

## 9. Preconditions and TOCTOU

Minimum future preconditions, all evaluated server-side and again inside the
execution transaction:

- active trusted TenantProjection and entitlement;
- exact Organization in tenant;
- exact target identity and current revision/version;
- target state equals the authorized expected state;
- exact ActionPlan canonical hash and exact ExecutionAuthorization;
- exact Decision, effective non-ambiguous Approval and exact ModelPolicy;
- action classification remains `standard` and `reversible`;
- all candidate-specific invariants are known and satisfied;
- no conflicting terminal execution/idempotency result.

The QMS object can change after dry-run or authorization. Therefore execution
must lock/re-read the target and revalidate the plan immediately before use.
Any delta between time of check and time of use fails closed; the executor may
not regenerate or broaden the plan.

## 10. Dry-run contract

No candidate dry-run implementation is added. A future action-specific dry-run
must return, without writes:

- exact action/target/tenant/Organization;
- current target revision/version and canonical state hash;
- authorized expected state and desired delta;
- each typed precondition with `satisfied|not_satisfied|unknown`;
- source/policy evidence for `standard` and `reversible`;
- exact compensation preview;
- ActionPlan ID and canonical hash;
- `business_state_changed=false`.

Required `not_satisfied` or `unknown` means denial. Execution must prove the
same plan hash and same expected target state as dry-run/authorization.

## 11. Authorization linkage and autonomy

The future invocation must resolve the exact chain:

`ActionExecution -> ExecutionAuthorization -> ActionPlan/hash -> target +`
`expected state -> Approval -> AgentDecision -> Recommendation -> AgentRun ->`
`AgentDefinition/ModelPolicy`.

No broader permission, latest policy pointer or request-provided authority is
accepted. Because no action-specific policy proves a different safe ceiling,
human Approval is mandatory and A3 is the maximum proposed ceiling for a first
real adapter. A4 remains unavailable for real mutation.

## 12. Idempotency

Future identity:

`tenant + authorization_id + plan_hash + action_type + target_type + target_id +`
`expected_state/version + idempotency_key`.

Exact replay returns the same execution/receipt and performs no second domain
command. Same key with any material difference is conflict. The gate does not
decide the “already desired” case, because that answer depends on the missing
business transition semantics; until specified, it fails as stale/conflict.

## 13. Concurrency

Preferred future strategy for a revisioned aggregate:

1. lock the execution/idempotency identity;
2. lock or command-guard the exact current target revision;
3. require that no successor/current-state conflict exists;
4. revalidate exact expected state/hash;
5. invoke the promoted command once.

For in-place aggregates, `SELECT FOR UPDATE` alone serializes writers but does
not prove the caller authorized the current version; a version/fingerprint is
also required. E1 and E2 against the same expected state cannot both create a
business effect. The loser receives `stale_target`/conflict and zero mutation.

## 14. Transaction boundary and lock ordering

For a purely internal PostgreSQL adapter, ActionExecution completion and the
QMS command should share one transaction:

`revalidate governance -> claim idempotency -> lock target -> domain command ->`
`domain event/outbox/audit -> execution terminal state/receipt -> execution`
`event/outbox/audit -> commit`.

This differs intentionally from Phase 14's two-transaction pattern designed for
future external calls. There is no external call here, so a single transaction
avoids a successful domain mutation with a failed receipt or the inverse.

Lock order must be uniform: execution/idempotency row first, target current
revision second, then aggregate event/audit stream locks in existing command
order. Deadlock/serialization failures roll back and may be retried only as a
new attempt under Phase 14 rules; they never imply success.

This design is provisional until one command is selected and its internal lock
order is inspected end-to-end.

## 15. Domain command reuse

Direct ORM `save()` and raw SQL are prohibited. The future adapter must call one
existing promoted material command. Current candidate mappings are documented
in section 4, but none is approved for adapter use. The adapter must not emit a
substitute business event or bypass RLS/invariants.

## 16. Event semantics

The domain command remains the sole producer of the business event (for
example, an eventual selected status command would emit its existing typed
domain event). ActionExecution separately emits lifecycle events describing
attempt/success/failure. The execution event links the domain event ID but does
not restate the business mutation as a second domain event.

No event contract was added in Phase 15.

## 17. Audit semantics

Two linked streams remain distinct:

- execution governance audit: authorization, plan/hash, attempt, adapter,
  receipt and outcome;
- domain audit: before/after or prior/new revision recorded by the promoted
  command.

They link by tenant, trace, ActionExecution ID, target aggregate identity and
domain event ID. The execution audit must not claim Effectiveness. No audit
entry was written during this docs-only gate.

## 18. Receipt contract

No new receipt schema is implemented. A future action-specific Receipt must
prove:

- execution/attempt and action type;
- exact target aggregate/lineage and expected starting revision/version/hash;
- exact Authorization and ActionPlan hash;
- domain command and domain event ID;
- result and resulting revision/version/hash on success;
- idempotent replay identity;
- compensation action type and expected compensation starting state;
- trace and timestamps;
- `effectiveness_claimed=false`.

Failure receipts must not claim a resulting business state unless the
transaction committed and it was re-read/proven.

## 19. Compensation design status

No compensation action is selected or implemented. For the future candidate,
compensation must itself be a new authorized ActionPlan/ExecutionAuthorization
and invoke a promoted domain command. It must be tenant/Organization-safe,
expected-state guarded, idempotent, evented and audited.

Raw SQL restore and DELETE are prohibited. “Create a new revision copying the
old fields” is not accepted until the sources/policy state that it is the
business inverse for the exact transition.

Compensation failure is a separate governed failure requiring audit and human
attention; it must never rewrite the original successful receipt.

## 20. EffectivenessCheck boundary

Execution success proves only that the authorized domain command committed.
Compensation proves only that a defined neutralization committed.
EffectivenessCheck would later require an action-specific method, due point,
expected observation and Evidence linkage to determine whether the intended QMS
outcome occurred. It is not implemented and does not gate transactional success.

## 21. Principal/security matrix

| Actor / Principal | Prepare? | Authorize? | Execute synthetic? | Execute future real adapter? | Mutate target directly? | Approve? | Compensate? |
|---|---:|---:|---:|---:|---:|---:|---:|
| APP | according to Phase 13 command boundary | No | No | No | existing app commands only; no adapter escalation | No | No |
| WORKER | Yes, Phase 13 scope | No | No | No | no new privilege | No | No |
| EXECUTOR | read exact provenance | No | Yes, synthetic only | No | No | No | No |
| HUMAN APPROVER | No | human outcome only, not ExecutionAuthorization | No | No | No | Yes through narrow gate | No |
| PROJECTOR | No | No | No | No | projection-only existing grants | No | No |
| AUDIT WRITER | No | No | No | No | audit append function only | No | No |
| NORMATIVE CURATOR | No | No | No | No | global normative catalog only | No | No |
| AGENT CURATOR | No | No | No | No | agent/policy catalog only | No | No |

Target state never becomes directly writable because an executor exists. A
future executor should receive execute on one narrow function/service boundary,
not generic UPDATE on the target table. Phase 15 grants nothing.

## 22. Threat and failure matrix

| Failure/threat | Detection/revalidation | Required result |
|---|---|---|
| authorization stale | exact Authorization and effective governance chain re-read | no mutation |
| approval invalid/rejected/request_changes/ambiguous | effective Approval resolver | no mutation |
| plan hash mismatch | canonical v1 recomputation and exact equality | no mutation |
| action/target mismatch | literal action/target contract vs plan/auth | no mutation |
| target missing | tenant-scoped exact lookup | no mutation; non-leaking error |
| target changed | expected revision/version/hash under lock | stale conflict; no mutation |
| cross-tenant target | trusted tenant + RLS + composite FK | deny/no visibility |
| cross-Organization target | exact target-derived Organization vs plan/auth | deny |
| precondition failed/unknown | typed server-side evaluator | deny |
| concurrent mutation | lock/version/current-revision guard | one winner at most |
| duplicate execution | durable exact idempotency identity | return prior receipt, no second effect |
| idempotency key conflict | compare all material identity fields | 409-equivalent conflict |
| domain command rejection | catch classified invariant failure | transaction rollback; failed attempt |
| DB rollback/serialization | transaction outcome only | zero domain/receipt/event/audit partial state |
| domain event/outbox failure | same transaction | rollback business mutation |
| audit failure | same transaction | rollback business mutation |
| execution receipt failure | same transaction | rollback business mutation |
| executor privilege abuse | no generic DML; narrow command/function only | permission denied + security audit |
| compensation stale/fails | own expected-state/auth/idempotency checks | no partial compensation; escalate |
| Effectiveness confused with success | explicit receipt flag and separate aggregate | never claim effectiveness |
| unresolved condition | fail-closed default | no mutation |

## 23. Acceptance criteria

| Criterion | Result | Evidence/blocker |
|---|---|---|
| Direct source support | FAIL for a concrete delta | objects/actions general, no exact first transition |
| Existing promoted target aggregate | PASS | all considered targets promoted |
| Internal only / single target / no external dependency | PASS WITH RESTRICTIONS | achievable after selection |
| Standard/low impact | FAIL | no candidate-specific source/policy classification |
| Reversible / deterministic compensation | FAIL | no business inverse defined |
| Tenant/Organization-safe | PASS | RLS/composite boundaries promoted |
| Exact authorization / expected state | PASS WITH RESTRICTIONS | target version semantics incomplete for in-place objects |
| Idempotency | PASS WITH RESTRICTIONS | already-desired semantics missing |
| Concurrency controllable | PASS WITH RESTRICTIONS | command-specific lock/version design pending |
| Existing domain command reusable | PASS except Recommendation | commands exist but are not approved candidates |
| Domain Event/Audit supportable | PASS | promoted commands emit both atomically |
| Dry-run possible | PASS WITH RESTRICTIONS | evaluator must be candidate-specific |
| No catalog/history/Approval mutation | PASS | enforceable by scope |
| No Effectiveness needed for execution success | PASS | boundary defined |

Mandatory FAIL means no selection and **NOT PROMOTED**.

## 24. Implementation exclusions and no-side-effect evidence

Only two Markdown files were added: this report and ADR-0007. There are no
changes to Python, models, migrations, settings, database, API, executor
registry, allowlist, permissions or tests. No QMS command was invoked in
mutation mode. No database, PostgreSQL harness, production/staging resource,
AdminApps, MedSupplier, external API, provider, HTTP, filesystem business path,
shell adapter, subprocess, broker or deployment was used.

Because no database was opened or command invoked, selected target row
counts/hashes are not applicable; the stronger code/repository evidence is that
there is no selected target and no executable artifact.

## 25. Migration status and frozen integrity

**NO MIGRATION.** There is no `0015`. Migrations `0001-0014` were SHA-256
checked and match their promoted values:

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

## 26. Source hashes

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

**10/10 SHA-256 MATCH.**

## 27. Verification and regression evidence

This is a docs-only gate. Required verification:

- initial and final `git status`: executed;
- `git diff --check`: executed, with only the known pre-existing whitespace in
  `frontend/src/components/Layout/Sidebar.jsx:28` outside Phase 15; Phase 15
  files are clean;
- source hashes: 10/10 MATCH;
- migrations 0001-0014: 14/14 promoted hashes MATCH;
- migration 0015: absent;
- repository scan: no Phase 15 adapter/executor/registration/schema artifact;
- backend regression: not rerun because no code/interface/test/schema changed;
  inherited verified baseline remains 165 PASS / 0 FAIL / 0 SKIP;
- foundation baseline: inherited verified 67 PASS / 0 FAIL / 0 SKIP;
- PostgreSQL harness: not started; no resource to tear down.

No unexecuted check is claimed as executed.

## 28. Open risks and required blockers

P0/P1 blocking controlled implementation:

1. **P0 — action-specific impact:** adopt a controlled source/policy artifact
   classifying one exact transition as `standard`/low impact.
2. **P0 — state machine:** enumerate allowed current/desired states and legal
   transitions for that exact target.
3. **P0 — business inverse:** define exact compensation and conditions under
   which it neutralizes the business effect.
4. **P0 — already-desired idempotency:** define success versus stale/conflict.
5. **P1 — expected-state token:** select revision/version/hash semantics and
   prove TOCTOU guard compatibility with the promoted command.
6. **P1 — command narrowing:** if using an in-place multi-field command, add or
   approve a one-action command boundary without generic fields.
7. **P1 — policy binding:** bind exact Approval requirement and A3 ceiling to
   the action type in a versioned policy/source artifact.

These blockers are design/source work only. They do not justify schema or
executor implementation.

## 29. Next design/source gate

The next phase must not implement a real adapter. It must choose one proposed
transition at the source/policy level and resolve only the seven blockers above.
The leading candidates may be compared again, but none is preselected by this
report.

## 30. Promotion verdict

**PHASE 15 — CONTROLLED DOMAIN ADAPTER DESIGN GATE: NOT PROMOTED**

No candidate passed every mandatory criterion. There are zero Phase 15 P0/P1
implementation defects because no implementation was added, but seven
source/design blockers prevent controlled implementation. This is the required
fail-closed result.

| Candidate/component | State | Evidence | Risk/next action |
|---|---|---|---|
| Candidate selection | NOT SELECTED | all candidates fail impact and/or business reversibility | resolve source/policy blockers only |
| Typed adapter | NOT CREATED | no candidate passed | do not scaffold prematurely |
| Real executor/allowlist | ABSENT / UNCHANGED | repository design scope | keep synthetic-only |
| SyntheticNoOpExecutor | ONLY EXECUTABLE IMPLEMENTATION | Phase 14 foundation unchanged | preserve |
| Domain commands | PROMOTED BUT NOT APPROVED FOR ADAPTER | Phase 4-10 command inspection | narrow only after source decision |
| Authorization/plan/hash | PROMOTED / UNCHANGED | Phase 13-14 | action-specific exactness pending |
| EffectivenessCheck | OUT OF SCOPE | separate lifecycle stage | do not implement |
| Migrations 0001-0014 | FROZEN / 14/14 MATCH | exact SHA-256 | preserve byte-for-byte |
| Migration 0015 | ABSENT | docs-only gate | do not create |
| Source artifacts | INTACT / 10/10 MATCH | exact SHA-256 | preserve byte-for-byte |
| QMS/external effects | ZERO | no code/DB/external action | maintain fail-closed |

## NEXT_CODEX_PROMPT

Ejecuta exclusivamente un gate de cierre de blockers de diseño/fuente para la primera acción QMS controlada en `/home/felipe/proyectos/isosmart`, sin implementar adapter, executor, migration, API ni mutación. Preserva byte-for-byte las migrations `0001-0014`, los diez source artifacts y `SyntheticNoOpExecutor` como única implementación ejecutable. Para exactamente una transición candidata propuesta —sin preseleccionarla por conveniencia— exige y documenta en un artifact fuente/policy versionado: `action_type` y `target_type` literales; estados actuales/deseados enumerados y transiciones legales; clasificación inequívoca `standard`/low impact; inverso o compensación empresarial exacta con sus precondiciones; semántica idempotente cuando el target ya está en el estado deseado; expected revision/version/hash y control TOCTOU compatible con el command promovido; command boundary estrecho reutilizable; Human Approval obligatorio y techo A3. Compara nuevamente todos los candidatos promovidos permitidos y selecciona exactamente uno sólo si esa evidencia resuelve cada criterio; si alguno falla, mantén `NOT PROMOTED`. Entrega ADR/reporte actualizados, matrices de source/safety/security/threat, 10/10 hashes, 14/14 migrations, `git diff --check`, cero side effects y exactamente un siguiente prompt autocontenido.
