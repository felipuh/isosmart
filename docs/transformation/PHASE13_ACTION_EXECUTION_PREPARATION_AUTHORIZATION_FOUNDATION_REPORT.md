# Phase 13 — Action Execution Preparation + Authorization Contract Foundation

**Fecha:** 2026-08-24  
**Gate:** `PHASE 13 — ACTION EXECUTION PREPARATION + AUTHORIZATION CONTRACT FOUNDATION`  
**PostgreSQL:** 18.6  
**Run final:** `20260824T172357Z_d6f6c2`  
**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó exclusivamente `foundation/0013_action_execution_preparation_authorization_foundation`.
Es aditiva y reversible: crea `qms.action_plan`, `qms.action_plan_dry_run` y
`qms.execution_authorization`, sus constraints, triggers, RLS y el narrow
function del evaluador. La secuencia real `0001 → … → 0013 → 0012 → 0013`
pasó y dejó Phase 12 funcional. `0001–0012` conservaron sus hashes promovidos:
`0d72f2…`, `1f538c…`, `dadfad…`, `045043…`, `96ab33…`, `033242…`,
`c7f6a2…`, `285aec…`, `412c64…`, `c4f37a…`, `cdb23e…`, `7f280e…`.
El SHA-256 final de `0013` es
`06177fde1c25d884602a41d03df6d2625e8d15df18d7c66bffdb047348abf34b`.

## 2. Source reconciliation

Se inspeccionaron directamente DOCX, las 11 hojas XLSX, JSON, DDL, OpenAPI,
Mermaid, Draw.io, ambos CSV y LEEME. El contrato funcional fuente establece:
A2 prepara sin ejecutar; A3 ejecutaría sólo después de aprobación; A4 sólo
dentro de guardrails preaprobados, reversibles y monitorizados; alto impacto
entra al Human Decision Gate; `Approval` y `ActionExecution` son entidades
distintas; la simulación precede a recomendación/decisión. No existe en las
fuentes un engine de orquestación, TTL, revocación, bearer token, taxonomía
numérica de impacto ni `ActionPlan` detallado.

| SOURCE | ENTITY / CONCEPT | FIELD / RELATION | SEMANTICS | IMPLEMENT? | RATIONALE |
|---|---|---|---|---:|---|
| DOCX §7 + XLSX/JSON | prepared action | A2 | preparar artefacto/acción sin ejecutar | Sí, `ActionPlan` | separación fuente explícita |
| DOCX/Mermaid/Draw.io | Human Gate | A3/high impact → human decision | aprobación antes de futura ejecución | Sí | no se interpreta Approval como ejecución |
| DOCX/XLSX/JSON | A4/reversibility | reversible + preauthorized + monitored | A4 no es permiso general | Sí, clasificación mínima | bloquea bypass irreversible |
| DDL/XLSX/JSON | Approval | exact governance outcome | humano, separado de ejecución | Sí, Phase 12 exacta | resolución append-only |
| OpenAPI | Approval outcomes | approve/reject/request_changes | outcomes concretos únicos | Sí | no se inventan estados |
| DDL/XLSX/JSON | ActionExecution | reversible/rollback/result | futuro efecto | No | prohibido en Phase 13 |
| DOCX/Mermaid | simulation | Analyze/Simulate antes de Recommend/Execute | preview sin efecto | Sí, dry-run inmutable | no provider/tool call |
| source package | impact | standard/material vs high-impact gate | categoría cualitativa | Sí: `standard/high` | escala mínima segura |
| source package | reversibility | reversible vs irreversible boundary | gobernanza A4 | Sí | no se inventó conditional state |
| misión + ADR eventing | idempotency | exact repeated command | no duplicar intent | Sí | tenant + operation/table + key |
| fuente insuficiente | expiry/revocation | no TTL/precedencia de revocación | indefinido | No | diferido, sin defaults arbitrarios |

## 3. Separación semántica y Approval efectivo

`Recommendation` es consejo; `AgentDecision`, decisión gobernada; `Approval`,
outcome humano; `ActionPlan`, contrato exacto; `ExecutionAuthorization`, permiso
para ese contrato; `ActionExecution`, futuro efecto ausente.

La resolución efectiva ordena la historia append-only por
`decided_at, created_at, id`. El último instante sólo es efectivo si todos los
outcomes empatados coinciden; outcomes contradictorios en el mismo instante
son ambiguos y fallan cerrados. La matriz PostgreSQL probó
`request_changes → approve = approve`, `reject = denied`,
`request_changes = denied` y empate `approve/reject = ambiguous/denied`. No se
creó un puntero mutable `current`.

## 4. ActionPlan y hash canónico

`ActionPlan` conserva UUID, tenant, Organization, exact AgentDecision y
Recommendation, action type, target type/identity, parameters JSON object,
impact, reversibility, preconditions estructuradas, dry-run capability,
required autonomy, SHA-256, tenant-scoped idempotency key, trace y timestamp.

La representación `iso-smart-action-plan-v1` incluye Organization, Decision,
Recommendation, action type, target `{type,id}`, parameters, impact,
reversibility, preconditions, dry-run capability y autonomy. Excluye UUID del
plan, timestamp, trace e idempotency key. Se serializa con el canonical JSON
promovido y se calcula SHA-256. Cambiar cualquier campo material produce otro
hash. Triggers rechazan todo UPDATE/DELETE; un cambio requiere un plan nuevo.

## 5. Impacto, reversibilidad y preconditions

Impacto usa sólo `standard/high`; reversibilidad sólo
`reversible/irreversible`. Se omitió una escala numérica y
`conditionally_reversible` por falta de soporte inequívoco. High o irreversible
nunca puede beneficiarse de un supuesto bypass A4.

Cada precondition exige `identity`, `type`, `expected`, `required` boolean y
`source_reference` opcional. El dry-run informa exactamente una evaluación por
identidad: `satisfied`, `not_satisfied` o `unknown`. Required + cualquier valor
distinto de `satisfied` deniega autorización.

## 6. Dry-run

`ActionPlanDryRun` es append-only y enlaza exact plan ID/hash. Guarda objetos
esperados, delta pretendido, validation status, resultados de preconditions,
resumen de impacto y trace. No tiene adapter, provider, tool o command de
ejecución. La prueba sintética capturó conteos de Process, Risk, Opportunity,
Objective, Change y Evidence antes/después: idénticos. Usar dry-run H1 con plan
H2 fue denegado.

## 7. ExecutionAuthorization y provenance congelada

El artifact autorizado conserva exact ActionPlan ID/hash, dry-run, Decision,
Recommendation, effective Approval, AgentRun, AgentDefinition, ModelPolicy,
effective autonomy ceiling, impact, reversibility, request hash, tenant-scoped
idempotency, actor, trace y authorized time. Sólo existe outcome persistido
`authorized`; denials producen ImmutableAuditLog sin fabricar una autorización.

La cadena reconstruible es:

`Authorization → ActionPlan hash → Approval → AgentDecision → Recommendation →`
`RecommendationBasis → AgentRun → AgentRunInput → AgentDefinition/ModelPolicy →`
`RequirementControl/KnowledgeLayerRule/Evidence revision`.

DB y servicio verifican coincidencia tenant/Organization, exact Recommendation,
run/definition/policy, Approval efectivo approved, policy ceiling, exact dry-run
hash y preconditions. No hay current pointers.

## 8. Actor, AdminApps e idempotency

La autorización es una evaluación de `governance_service`, no una segunda
decisión humana. `ExecutionAuthorizerContext` sólo admite trusted backend policy
evaluator. AdminApps conserva identidad, roles y MFA; la authority humana se
revalida contra UserProjection activa y snapshot exacto. Los commands no
aceptan tenant, approver, role o autonomy del cliente.

Preparación y autorización usan uniqueness `(tenant_id,idempotency_key)` en su
operación. Same key + same canonical/request hash retorna la fila previa; same
key + changed plan/request produce conflicto 409. La matriz probó ambos casos.
La futura ActionExecution deberá deduplicar también el efecto externo; aquí no
existe ningún efecto.

## 9. Commands, events y audit

Commands: `prepare_action_plan`, `run_action_plan_dry_run` y
`evaluate_execution_authorization`. No existe `execute_action`.

Eventos schema v1: `action_plan.prepared`,
`action_plan.dry_run_completed`, `execution_authorization.granted` y contrato
reservado `execution_authorization.denied`; en esta slice los denials se
conservan como audit de seguridad, no como business authorization/event.

Cada success material persiste aggregate + DomainEvent + Outbox +
ImmutableAuditLog dentro del transaction-scoped trusted tenant context.
Rollback forzado después de audit dejó cero delta. Audit registra hashes,
lineage exacto, classification, preconditions, dry-run, idempotency hash,
actor/trace y `no_execution`, sin secretos.

## 10. RLS, principals y SQL

Las tres tablas tienen `tenant_id NOT NULL`, composite FKs, `ENABLE` + `FORCE
ROW LEVEL SECURITY` y policies SELECT/INSERT/UPDATE/DELETE/ALL. La matriz
poblada demostró A-only, none-zero y B-only; contexto después de commit y
rollback volvió a none-zero.

`foundation_execution_authorizer_<runid>` fue LOGIN real, non-superuser,
NOBYPASSRLS, non-owner, NOINHERIT. Puede leer únicamente provenance gobernada,
Event/Outbox/Audit y ejecutar el narrow
`foundation_0013_grant_execution_authorization`; no tiene INSERT directo de
Authorization, Approval o Decision, ni writes QMS/catalog. Worker prepara y
simula, pero no lee/crea authorization ni ejecuta el function. Raw SQL rechazó
mutación/re-point de ActionPlan; DB triggers validan exact provenance.

## 11. Evidencia de paths y denials

- authorized path + exact Event/Outbox/Audit: PASS;
- effective approved sequence: PASS;
- reject/request_changes/ambiguous/missing approval: DENIED;
- high/irreversible without approval: DENIED;
- policy A3 request above A3 ceiling: DENIED;
- required precondition unknown: DENIED;
- dry-run H1 with plan H2: DENIED;
- repeated authorization: same row; changed request with same key: 409;
- forced post-audit authorization rollback: zero partial authorization;
- ActionPlan immutable after authorization: raw SQL DENIED;
- worker self-authorization: DENIED;
- ActionExecution relation/model/command: ABSENT.

## 12. Regression, integrity, hashes y teardown

| Gate | Resultado |
|---|---|
| Backend completo | **161 PASS / 0 FAIL / 0 SKIP** |
| Delta vs Phase 12 baseline 156 | **+5** focused Phase 13 contracts |
| Foundation total | 63 tests dentro del backend total |
| Django check | PASS, 0 issues |
| makemigrations check/dry-run | PASS, no changes |
| Python compilation | PASS |
| PostgreSQL 18.6 populated matrix | PASS |
| forward/reverse/forward | PASS |
| source hashes | 10/10 MATCH |
| frozen migrations | 0001–0012 exact hashes MATCH |
| teardown | container/volume/temp absent PASS |

El `git diff --check` final sigue reportando whitespace preexistente en
`frontend/src/components/Layout/Sidebar.jsx:28`; Phase 13 no tocó ese archivo.
No se modificó `.env`, fuente, producción, staging, DB compartida, AdminApps DB,
MedSupplier DB ni repos externos. La telemetría preexistente intentó DNS durante
la suite, falló cerrada y no produjo side effect.

## 13. Riesgos residuales

1. No hay TTL ni revocación: la fuente no define su semántica; una futura slice
   debe usar artifact append-only, nunca `revoked=true` improvisado.
2. `standard/high` y `reversible/irreversible` son el mínimo source-backed; una
   taxonomía más rica necesita policy versionada.
3. Denied idempotent attempts se auditan, pero no tienen ledger de replay propio;
   un futuro authorization-attempt artifact puede deduplicarlos si el source lo
   requiere.
4. El evaluador recibe resultados de simulación gobernados; verificadores reales
   read-only por tipo de precondition siguen futuros.
5. El hash canónico está versionado en código/documentación; futuras versiones
   deben convivir, no reinterpretar hashes históricos.
6. ActionExecution, effect deduplication, monitoring y rollback execution siguen
   deliberadamente ausentes.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 14. Veredicto

**PHASE 13 — ACTION EXECUTION PREPARATION + AUTHORIZATION CONTRACT FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0013_action_execution_preparation_authorization_foundation` | PROMOTED | PostgreSQL 18.6; reverse/forward; RLS catalog | congelar después de promoción |
| `ActionPlan` | PROMOTED | exact provenance/hash; immutable; idempotent | versionar canonicalization si evoluciona |
| `ActionPlanDryRun` | PROMOTED | exact hash; no-side-effect counts | evaluadores read-only tipados futuros |
| effective Approval | PROMOTED | ordered append history; ambiguity denied | no crear mutable current pointer |
| `ExecutionAuthorization` | PROMOTED | exact Plan/Approval/Decision/Run/Policy | expiry/revocation sólo con fuente |
| authorizer principal | PASS | LOGIN, non-owner, NOBYPASSRLS, function-only | mantener privilege regression |
| Event/Outbox/Audit | PASS | atomic success + rollback | denial ledger sólo si se justifica |
| RLS/raw SQL/pool | PASS | populated A/none/B; mutation denied | ampliar joins con futuras tablas |
| No execution | PASS | no model/table/command/provider/QMS mutation | ActionExecution permanece fuera de scope |
| Full regression | PASS | 161/161 | conservar baseline |
| Source/frozen history | PASS | 10/10 + 0001–0012 hashes | no reescribir |
| Teardown | PASS | container/volume/temp absent | ninguno |
