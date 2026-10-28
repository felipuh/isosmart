# Phase 5 — Risk + Opportunity + Objective Foundation

**Fecha:** 2026-08-17  
**Gate:** `PHASE 5 — RISK + OPPORTUNITY + OBJECTIVE FOUNDATION`  
**PostgreSQL run-id final:** `20260817T175115Z_8ad3e3`  
**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó únicamente `foundation/0005_risk_opportunity_objective_foundation`. Es aditiva, reversible, sin backfill, dual-write, borrado legacy ni cambios de producción. El DDL PostgreSQL crea `qms.risk`, `qms.opportunity` y `qms.objective`; SQLite conserva el estado Django mediante `SeparateDatabaseAndState`.

Las migrations promovidas permanecen byte-for-byte intactas:

| Migration | SHA-256 |
|---|---|
| `0001_foundation_tenant_projection` | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` |
| `0002_projection_organization_user_foundation` | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` |
| `0003_eventing_immutable_audit_foundation` | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` |
| `0004_qms_harmonized_context_foundation` | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` |
| `0005_risk_opportunity_objective_foundation` | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` |

PostgreSQL verificó `0001 → 0002 → 0003 → 0004 → 0005 → 0004 → 0005`. La reversa de 0005 eliminó sólo sus tres tablas y tres funciones; Stakeholder, StakeholderRequirement, Process, ContextItem, QmsScope, DomainEvent y Audit permanecieron.

## 2. Decisiones de fuente

Se leyeron directamente DOCX, XLSX, JSON, DDL, CSV de nodos/aristas y catálogo de eventos. La autoridad estructurada define:

- Risk: `risk_id`, `tenant_id`, `process_id`, `cause`, `event`, `consequence`, `likelihood`, `impact`, `residual`.
- Opportunity: `opportunity_id`, `tenant_id`, `process_id`, `hypothesis`, `benefit`, `feasibility`, `status`.
- Objective: `objective_id`, `tenant_id`, `owner_id`, `metric_id`, `target`, `due_date`, `status`.

La migration añade `organization_id`, lineage, revision, predecessor, reason y timestamps como controles tenant/históricos ya aprobados por la arquitectura. No inventa title, description, Risk status, score, treatment ni relaciones simétricas. `metric_id` queda diferido hasta la foundation de measurement/KPI: persistir ahora un UUID sin entidad/FK crearía una referencia ambigua.

## 3. Risk schema e historia

Risk es un único business object, sin clones por norma. Cada fila es una revisión append-only con UUID, tenant, Organization, Process, lineage, revision, predecessor, los seis campos fuente de evaluación, reason y timestamp. Likelihood, impact y residual se conservan como texto tipado de dominio sin inventar escala/rango numérico ausente de la fuente.

El gate reconstruyó Risk v1→v2→v3. La unique `(tenant,organization,previous_revision_id)` impide forks; `(tenant,organization,lineage,revision)` impide duplicar versión; el trigger exige incremento exacto y mismo tenant/Organization/lineage. El current es el único leaf sin sucesor. UPDATE/DELETE son rechazados por trigger y app sólo tiene SELECT/INSERT.

## 4. Opportunity schema e historia

Opportunity es una entidad y tabla independientes de Risk; no existe `Risk.type`, score negativo, row identity compartida ni conversión silenciosa. Contiene Process, hypothesis, benefit, feasibility y status conforme a fuente, más boundary e historia.

El gate creó Opportunity sin depender de Risk y reconstruyó v1→v2→v3; v3 fue un cambio de status que conservó la definición anterior. Las mismas constraints de lineage bloquean ciclos, forks, predecessor cruzado y overwrite.

## 5. Objective schema e historia

Objective contiene owner opcional tenant-safe, target, due_date y status, más tenant, Organization e historia. No se creó KPI, measurement, Evidence ni performance subsystem. El gate reconstruyó v1→v2→v3 y conservó target/due date/status anteriores; el cambio de status genera revisión.

## 6. Process, Requirement y trazabilidad causal

Risk→Process y Opportunity→Process son relaciones formales respaldadas por `process_id` en XLSX/JSON. Usan FK compuesta `(tenant_id,organization_id,process_id)`, por lo que un Process de otro tenant u Organization es rechazado independientemente de RLS.

Los artefactos describen contexto, stakeholders, procesos, histórico de riesgos y KPI como inputs funcionales, pero no definen campos de instancia Risk/Opportunity/Objective→ContextItem o StakeholderRequirement. Tampoco definen Objective→Risk/Opportunity/Process/Requirement en `DB_Entities`. Por tanto 0005 no inventa esas relaciones. `EXPOSES_RISKS` en el CSV une requisitos normativos del catálogo, no instancias tenant. StakeholderRequirement no se enlaza ni a logical identity ni a revisión en esta Phase; la decisión queda explícitamente diferida hasta que un source binding de instancia la respalde.

Esta ausencia es conservación contract-first, no texto libre sustituto: tampoco se añadieron campos “because of risk XYZ”. Las futuras relaciones normativas pertenecen a Standard/Edition/Clause/RequirementControl/KnowledgeLayerBinding fuera de alcance.

## 7. Cross-tenant, boundary y RLS

Cada tabla tiene `tenant_id NOT NULL`, Organization FK compuesta, predecessor FK compuesta y unique parent keys. Risk/Opportunity añaden Process FK compuesta; Objective owner usa `(tenant_id,owner_id)`. Triggers DB ejecutados antes del rechazo append-only reportan explícitamente `tenant_id is immutable` u `organization_id is immutable`; no existe reasignación CRUD.

Las tres tablas tienen `ENABLE ROW LEVEL SECURITY` y `FORCE ROW LEVEL SECURITY`, inspeccionados en catálogo. Hay 15 policies: SELECT/INSERT/UPDATE/DELETE explícitas y una migrator por tabla. Policies no amplían grants.

| Tabla | App A | No tenant | App B | Worker A/none/B | App grants |
|---|---:|---:|---:|---:|---|
| Risk | 3 | 0 | 1 | 3/0/1 | SELECT, INSERT |
| Opportunity | 3 | 0 | 1 | 3/0/1 | SELECT, INSERT |
| Objective | 3 | 0 | 1 | 3/0/1 | SELECT, INSERT |

Projector y audit writer tienen cero acceso a estas tablas. Los cinco LOGIN fueron non-superuser, `NOBYPASSRLS`, non-owner.

## 8. Commands y eventos

`RiskOpportunityObjectiveCommandService` expone exclusivamente:

- `create_risk`, `revise_risk`;
- `create_opportunity`, `revise_opportunity`, `change_opportunity_status`;
- `create_objective`, `revise_objective`, `change_objective_status`.

Risk no expone status command porque la fuente no define status para Risk. No existe endpoint/event/audit injection.

Contratos schema version 1: `risk.created`, `risk.revised`, `opportunity.created`, `opportunity.revised`, `opportunity.status_changed`, `objective.created`, `objective.revised`, `objective.status_changed`. Payloads pasan por `iso-smart-canonical-json-v1`, contienen lineage/revision IDs y cambios mínimos deterministas, preservan aggregate version/trace/tenant en el envelope y no incluyen secretos ni snapshots masivos.

## 9. Atomic success, rollback y audit

Cada command abre un único `trusted_tenant_context`, que posee una única `transaction.atomic()`: business revision → DomainEvent → TransactionalOutbox → `audit.append_immutable_audit` → commit. Process/Organization lookup y escritura ocurren dentro de ese boundary.

Éxito se verificó para create/revise de Risk, Opportunity y Objective: business row, event, outbox y audit comparten tenant, trace y aggregate. Fallos inyectados después del append audit y antes del commit para las tres revisiones dejaron sin cambio history, DomainEvent, Outbox y Audit.

Las tres cadenas audit v1/v2/v3 validaron sequence, previous hash, metadata payload hash y entry hash. Runtime conserva cero UPDATE/DELETE/TRUNCATE/forge sobre audit.

## 10. Raw SQL, worker, pool y rollback context

SQL directo con roles reales rechazó Risk→Process B, Opportunity→Process B, Objective→Organization B y predecessor cross-tenant. También rechazó tenant/Organization reassignment, UPDATE histórico y DELETE runtime.

Worker obtuvo A only/B only y cero sin tenant; carece de business writes Phase 5. La misma conexión ejecutó `A → commit → none → zero → B → B only`. Otra secuencia ejecutó `A → exception → rollback → none → zero → B → B only`. Projector siguió sin permisos.

## 11. PostgreSQL, regresión e integridad

Corrida final: PostgreSQL `18.6`, `server_version_num=180006`, imagen oficial, endpoint efímero `127.0.0.1:44003`, run-id `20260817T175115Z_8ad3e3`.

| Gate | Resultado |
|---|---|
| Backend completo | **125 PASS / 0 FAIL / 0 SKIP** |
| Delta vs baseline 120 | **+5** contract tests Phase 5 |
| Foundation unit suite | **27 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL Phase 1–5 | PASS |
| Forward/reverse/forward | PASS |

Warnings legacy de paginación y telemetría Chroma/PostHog no produjeron failures ni skips.

## 12. Source integrity y teardown

Los diez SHA-256 recalculados coinciden exactamente con el manifest: `8308bd…`, `e0a59c…`, `11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`, `eb4231…`: **10/10 MATCH**. Ningún artefacto fuente fue modificado.

Teardown final: database y cinco roles eliminados; container, volume y temp dir ausentes. No se usó producción, staging, DB compartida, AdminApps DB ni MedSupplier DB. No hubo deployment, cambios `.env`, secretos ni repos externos.

## 13. Riesgos residuales

1. Metric binding y measurement/KPI permanecen pendientes hasta la siguiente slice; Objective conserva target/due date/status sin referencia huérfana.
2. Relaciones causales de instancia a ContextItem, StakeholderRequirement, Risk u Opportunity no se agregaron porque DB_Entities no las define. Deben entrar sólo con evidencia de fuente y decisión logical identity vs specific revision.
3. Current se deriva como leaf único, no como pointer mutable. Las uniques garantizan linealidad; consumidores futuros deberían encapsular la consulta en repository/view.
4. No existen endpoints/OpenAPI de producto ni broker; commands son foundation interna y transport permanece fuera de alcance.
5. Audit es append-only/tamper-evident para runtime, no indestructible ante DBA; checkpoints WORM siguen pendientes.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 14. Veredicto

**PHASE 5 — RISK + OPPORTUNITY + OBJECTIVE FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001–0004` | FROZEN / INTACTO | hashes promovidos exactos | Evolucionar sólo 0006+ |
| `0005_risk_opportunity_objective_foundation` | PROMOTED | PostgreSQL forward/reverse/forward; hash `96ab33…` | Congelar tras promoción |
| Risk | PROMOTED | v1→v2→v3; Process FK; RLS; atomic/audit | Change integration next |
| Opportunity | PROMOTED | identidad separada; v1→v2→v3; Process FK | Performance integration next |
| Objective | PROMOTED | target/due/status history; owner tenant-safe | Measurement/KPI foundation next |
| Requirement/Context causal links | DEFERRED BY SOURCE | no instance FK in DB_Entities | Añadir sólo con source-backed semantics |
| RLS/principals | PASS | 3 tables, 15 policies, A/B/none, worker | Repetir por nuevas tablas |
| Event/Outbox/Audit | PASS | success + rollback + chain | Transport futuro |
| Backend/Django | PASS | 125/0/0; check/drift/compile | Mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | Preservar byte-for-byte |
| Recursos efímeros | REMOVED | teardown PASS | Ninguna acción |
