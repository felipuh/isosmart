# Phase 14 — Action Execution Foundation — Synthetic / No External Effect

**Fecha:** 2026-08-24

**Gate:** `PHASE 14 — ACTION EXECUTION FOUNDATION — SYNTHETIC / NO-EXTERNAL-EFFECT`

**PostgreSQL:** 18.6

**Run final:** `20260824T180835Z_5d96bc`

**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó exclusivamente
`foundation/0014_action_execution_synthetic_foundation`. Es aditiva,
reversible y condicionada a PostgreSQL mediante `SeparateDatabaseAndState`.
Crea `qms.action_execution`, `qms.action_execution_receipt`, constraints,
triggers, RLS y dos funciones estrechas de inicio/finalización. Su SHA-256 es
`ee0e42a7d45803f633ca40d9b0ca20987a20acfdaf3452ee81d721cec29ada33`.

Las migrations `0001–0013` permanecen byte-for-byte intactas y conservaron
exactamente sus hashes promovidos: `0d72f2…`, `1f538c…`, `dadfad…`, `045043…`,
`96ab33…`, `033242…`, `c7f6a2…`, `285aec…`, `412c64…`, `c4f37a…`, `cdb23e…`,
`7f280e…`, `06177f…`. La secuencia real `0001 → … → 0014 → 0013 → 0014`
pasó; durante la reversa Phase 13 quedó íntegra y funcional.

## 2. Source reconciliation

Se inspeccionaron directamente los diez artifacts: XML interno DOCX, las once
hojas XLSX, JSON, DDL, OpenAPI, Mermaid, Draw.io, ambos CSV y LEEME. La fuente
define una entidad `ActionExecution` separada, executor, timestamps,
reversibilidad, `rollback_ref` y result; ubica Execute después de Autonomy/Human
Gate y antes de effectiveness; A3 exige aprobación y A4 sólo permite acciones
preautorizadas, reversibles y monitorizadas. No define attempt/receipt, estados,
retry algorithm, TTL, revocation, idempotency field, provider/tool framework ni
orchestrator concreto. Mission/ADRs justifican la mínima persistencia adicional
de intento, recibo e idempotencia sin reinterpretar la fuente.

| SOURCE | ENTITY / CONCEPT | FIELD / RELATION | SEMANTICS | IMPLEMENT? | RATIONALE |
|---|---|---|---|---:|---|
| DOCX §7/Mermaid/Draw.io | lifecycle | Human Gate/guardrail → Execute → Effectiveness | etapas distintas | Sí, sólo Execute | Effectiveness queda fuera |
| DOCX/XLSX/JSON DB_Entities | ActionExecution | execution, Recommendation, executor, start/end, reversible, rollback ref | registro de acción | Sí, enlazado al contrato Phase 13 más exacto | evita saltar Plan/Authorization |
| DDL | ActionExecution | `executor_type`, `started_at`, `completed_at`, `reversible`, `rollback_ref`, `result` | mínimo estructurado | Sí, salvo rollback action | reversibilidad vive en plan congelado; no rollback real |
| Data Architecture | ActionExecution | tenant-scoped, append/status/result | historia legal | Sí | RLS + estado mínimo |
| DOCX | A3 | execute después de aprobación humana | gate obligatorio | Sí | Approval efectivo exacto se revalida |
| DOCX/XLSX/JSON | A4 | preauthorized, reversible, monitored | no permiso general | Sí | standard+reversible; sigue synthetic no-op |
| sources | A0/A1/A2 | no execution; A2 prepara | techo | Sí | A2 denegado antes de start |
| sources | rollback | reversible + `rollback_ref` | capacidad/metadato | Parcial | retry lineage y plan reversibility; no fake rollback |
| sources | effectiveness | etapa posterior separada | execution ≠ effectiveness | No | prohibida en Phase 14 |
| source insuficiente | retry | no lifecycle/algorithm | indefinido | Mínimo | nuevo attempt row, nunca overwrite |
| source insuficiente + ADR outbox | receipt/result | terminal result durable | trazabilidad/idempotencia | Sí | receipt append-only por intento |
| source insuficiente + misión | idempotency | same logical command dedupe | durable replay/conflict | Sí | `(tenant,idempotency_key)` + exact auth/hash |
| source insuficiente | authorization expiry/revocation | no TTL | indefinido | No | no se inventó TTL |

## 3. Cadena semántica y modelo

Invariante persistido y revalidado:

`Recommendation → AgentDecision → Approval → ActionPlan → ExecutionAuthorization → ActionExecution`.

`ActionExecution` conserva tenant, Organization, exact Authorization, exact
ActionPlan/hash, único executor `synthetic_noop`, status, attempt number,
`retry_of_execution_id`, snapshot de preconditions, idempotency key, trace y
timestamps. No contiene payload arbitrario, provider, endpoint, credential,
tool, EffectivenessCheck o mutación QMS.

`ActionExecutionReceipt` es uno-a-uno y append-only: execution, executor,
synthetic outcome, bounded result JSON, result hash, plan hash, trace y tiempos.
El result obliga las marcas `NON-PRODUCTION`, `SYNTHETIC`, `NO-OP` y
`business_state_changed=false`.

## 4. State machine, attempts, retry y recovery

Estados mínimos: `running → succeeded|failed`. `succeeded` y `failed` son
terminales; UPDATE posterior y DELETE son rechazados. No existe transición
terminal → running.

Cada `ActionExecution` es un intento histórico. Retry explícito crea otro
ActionExecution con idempotency identity nueva, `retry_of` al failed exacto y
`attempt_number=N+1`; revalida toda la autorización/hash/preconditions y no
altera el failed anterior. La fuente no define expiry; por tanto retry no aplica
TTL arbitrario. Una completion abortada deja el intent `running`, sin receipt ni
evento/audit terminal; queda disponible para una futura recovery policy
source-backed, no para mutación manual.

No se ejecuta rollback. Para el no-op, no hubo efecto que compensar. Reversibility
se reconstruye desde el plan/autorización exactos y retry lineage conserva
historia; no se afirma `rollback succeeded`.

## 5. Revalidación de autorización, hash, policy y preconditions

Antes de start y nuevamente antes de completion se verifica:

- trusted tenant context y mismo Organization;
- outcome `authorized` exacto;
- Authorization.ActionPlan = Execution.ActionPlan;
- hash canónico recalculado = Plan hash = Authorization hash;
- exact Decision/Recommendation/Run/Definition/ModelPolicy;
- Policy publicada exacta y Definition→Policy exacta, sin latest pointer;
- Approval efectivo actual, no ambiguo, approved, exacto y actor projection activa;
- required autonomy ≥ A3 y dentro de Decision/Run/Authorization ceilings;
- A4 sólo standard/reversible; siempre synthetic no-op;
- dry-run passed para exact plan ID+hash;
- evaluación server-side inmediata y completa de todas las preconditions; required
  `not_satisfied`/`unknown` falla cerrado;
- idempotency state antes de invocar el executor.

La DB repite tenant/Organization/FK exactos, auth outcome, Plan/Auth hash,
Decision/Recommendation, classification, autonomy/A4, exact dry-run, Approval
efectivo no ambiguo, preconditions, retry lineage y allowlist.

## 6. Idempotencia y command

Único command: `execute_authorized_action`. Recibe sólo
`ExecutionPrincipalContext`, `authorization_id`, `idempotency_key`, `trace_id`
y flags internos de fault injection en tests. No acepta tenant, payload de
acción, executor, autonomy, approved, role, header/query/browser authority ni
cross-tenant choice.

Same tenant + key + exact authorization/hash retorna el mismo execution/receipt
sin nueva invocación. Same key + distinta authorization o plan hash produce
conflicto equivalente a 409. Retry requiere una key nueva y un failed exacto.

## 7. Executor interface, allowlist y ausencia de efectos

`ExecutorInvocation` contiene sólo execution/plan IDs, exact hash y target
descriptivo congelado. `ExecutorRegistry` exige exactamente una entrada:
`synthetic_noop`; `http`, `shell`, `database`, `tool` y unknown se rechazan.

`SyntheticNoOpExecutor` valida invocation y devuelve result determinista. No
importa ni llama HTTP clients, sockets, subprocess, shell, filesystem, provider,
tool o adapter; no importa modelos Process/Risk/Opportunity/Objective/Change/
Evidence. Repository scan y contract tests verificaron esas ausencias. El gate
capturó conteos de esos seis agregados antes/después de success: iguales.

Execution success significa únicamente que el executor no-op autorizado terminó;
no significa que una acción QMS ocurrió ni que fue efectiva.

## 8. Boundary transaccional, events y audit

Inicio: `ActionExecution(running) + action_execution.started + Outbox + Audit`
en una transacción y commit. Sólo después se invoca el no-op. Completion usa otra
transacción para `terminal status + Receipt + succeeded|failed Event + Outbox +
Audit`. Esto preserva el patrón futuro `persist intent → commit → dispatch →
receipt transaction`; nunca establece `open DB transaction → external call →
commit`.

Eventos schema v1: `action_execution.started`,
`action_execution.succeeded`, `action_execution.failed`. Audit reconstruye
execution, governance artifact, Plan/hash, executor, attempt, preconditions,
status, receipt/result hash, trace y no-side-effect/effectiveness flags, sin
secrets. Start rollback dejó cero delta. Completion rollback conservó sólo el
running previamente committed y cero receipt/event/outbox/audit terminal parcial.

## 9. Principal, permisos, RLS y raw SQL

`foundation_executor_<runid>` fue LOGIN real, non-superuser, NOBYPASSRLS,
NOINHERIT y non-owner. Sólo lee provenance tenant-scoped, execution/receipt y
Event/Outbox; escribe Event/Outbox y Audit por función promovida. No tiene DML
directo sobre execution/receipt; inicio/finalización ocurren sólo por
`foundation_0014_start_action_execution` y
`foundation_0014_complete_action_execution`. No puede crear Approval/Decision,
modificar Recommendation/Plan/Authorization, escribir QMS ni catálogos.

Ambas tablas tienen `tenant_id NOT NULL`, composite tenant/Organization FKs,
tenant immutable by transition trigger, ENABLE + FORCE RLS y policies separadas
SELECT/INSERT/UPDATE/DELETE/ALL. A-only, none-zero y B-only pasaron para app y
executor. Raw SQL rechazó direct UPDATE, forged terminal state, executor/hash
mismatch y cross-tenant visibility. Pool `A→commit→none→B` y rollback context
`A→exception→none→B` pasaron.

## 10. Evidencia de pruebas

| Gate | Resultado |
|---|---|
| Synthetic no-op success + exact receipt/event/outbox/audit | PASS |
| Forced synthetic failure | failed durable, zero QMS effect |
| Retry | new attempt 2; failed attempt unchanged |
| Duplicate execution | same execution/receipt; no duplicate invocation |
| Changed authorization/plan with same key | 409 conflict |
| Wrong executor/hash/raw function | rejected before valid execution |
| Effective rejected/request_changes/ambiguous chain | Phase 13 + revalidation PASS |
| A2 | denied, no execution |
| A4 | reversible/standard synthetic-only success; zero QMS effect |
| Preconditions changed to unknown | denied before start |
| Dry-run exact ID/hash | service + DB defensive validation PASS |
| Start rollback | zero execution/event/outbox/audit delta |
| Completion rollback | running coherent; no receipt/terminal artifacts |
| Terminal immutability/no DELETE | PASS |
| RLS/raw SQL/pool/rollback | PASS |

## 11. Verificación ejecutada

- PostgreSQL 18.6 official image matrix: PASS, final run
  `20260824T180835Z_5d96bc`;
- full backend: **165 PASS / 0 FAIL / 0 SKIP**; legitimate delta vs Phase 13
  baseline 161 = **+4** Phase 14 contract tests;
- foundation: **67 PASS / 0 FAIL / 0 SKIP**; delta vs 63 = **+4**;
- `manage.py check`: PASS, 0 issues;
- `makemigrations --check --dry-run`: PASS, no changes;
- Python compilation: PASS;
- `0014 → 0013 → 0014`: PASS;
- `git diff --check` en archivos Phase 14: PASS;
- source SHA-256: **10/10 MATCH**;
- frozen migrations `0001–0013`: **13/13 MATCH**;
- finalizer: database/10 roles/container/volume/temp removed, PASS.

La suite mostró warnings 400/401/403/404/405 y el intento de telemetría PostHog/
Chroma preexistente falló cerrado por DNS; no pertenece al execution path y no
produjo failures. Los intentos intermedios fallidos también ejecutaron teardown
PASS. No se tocó producción, staging, broker, DB compartida, AdminApps DB,
MedSupplier DB, `.env`, secrets, source artifacts ni repos externos.

## 12. Riesgos residuales

1. La fuente no define authorization expiry/revocation; no existe TTL. Antes de
   dominio real se necesita contrato append-only source-backed.
2. Recovery de un intent `running` tras crash no tiene lease/timeout; añadirlos
   requiere fuente/policy, no un cron arbitrario.
3. `SyntheticPreconditionEvaluator` es un boundary de fixture confiable; cada
   adapter de dominio futuro necesitará evaluadores read-only tipados.
4. No hay actual rollback/compensation ni EffectivenessCheck. Execution outcome
   no prueba cambio real ni eficacia.
5. Result hash es comprometido por el service/audit y receipt inmutable; un
   futuro adapter externo requerirá firma/attestation y receipt verification.
6. APP/worker no pueden ejecutar; una futura dispatcher architecture deberá
   conservar function-only executor y no ampliar DML.
7. Audit sigue tamper-evident para runtime; DBA/WORM externo permanece trust
   boundary.

No quedan P0 ni P1 bloqueando la siguiente slice de diseño. Ningún permiso para
mutación real se deriva de esta promoción.

## 13. Veredicto

**PHASE 14 — ACTION EXECUTION FOUNDATION — SYNTHETIC / NO-EXTERNAL-EFFECT: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0014_action_execution_synthetic_foundation` | PROMOTED | PG 18.6; reverse/forward; hash `ee0e42…` | congelar tras promoción |
| `ActionExecution` | PROMOTED | exact auth/plan/hash; append attempt history | recovery policy source-backed futura |
| `ActionExecutionReceipt` | PROMOTED | append-only deterministic synthetic receipt | signed external receipts futuros |
| Authorization/policy/preconditions | PASS | double service revalidation + DB defense | expiry/revocation no definidos |
| State/retry/idempotency | PASS | terminal immutable; new retry attempt; replay/409 | no arbitrary retry scheduler |
| Synthetic executor/allowlist | PASS | `synthetic_noop` only; no external imports/calls | no production executor autorizado |
| Executor principal | PASS | LOGIN, non-owner, NOBYPASSRLS, function-only | conservar privilege regression |
| Event/Outbox/Audit | PASS | separate atomic start/completion + rollback | future dispatch after commit only |
| RLS/raw SQL/pool | PASS | ENABLE+FORCE; A/none/B; direct forge denied | repetir por adapter futuro |
| No QMS/external effect | PASS | six aggregate counts unchanged; code scan | real mutation requires separate gate |
| Backend/Django | PASS | 165/165; 67 foundation; check/drift/compile | mantener baseline |
| Frozen/source integrity | PASS | 13/13 migrations + 10/10 artifacts | preservar byte-for-byte |
| Teardown | PASS | DB/roles/container/volume/temp absent | ninguno |

## NEXT_CODEX_PROMPT

Implementa exclusivamente el design gate `ACTION EXECUTION CONTROLLED DOMAIN ADAPTER DESIGN GATE` en `/home/felipe/proyectos/isosmart`, preservando byte-for-byte las migrations `0001–0014` y los diez source artifacts. Relee las fuentes originales y selecciona exactamente UNA acción QMS interna, de bajo impacto y reversible, con soporte inequívoco; diseña —sin habilitar todavía mutación real, producción ni efectos externos— su contrato tipado de adapter, target y preconditions read-only, autorización exacta, idempotencia, receipt, límites transaccionales, compensación/rollback y frontera separada de EffectivenessCheck. Mantén `SyntheticNoOpExecutor` como única implementación ejecutable y usa fixtures/dry-runs sin side effects. Produce reconciliación fuente, ADR/design report, threat/security matrix, criterios de aceptación y veredicto PROMOTED/NOT PROMOTED; si ninguna acción cumple el gate, falla cerrado y documenta el bloqueo. No implementes HTTP/tools/providers/shell, QMS writes reales, broker, production, staging ni deployment. Repite full regression, Django integrity, hashes y teardown si el diseño añade cualquier artifact verificable.
