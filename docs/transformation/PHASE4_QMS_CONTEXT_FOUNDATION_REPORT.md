# Phase 4 — QMS Harmonized Core Context Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 4 — QMS HARMONIZED CORE CONTEXT FOUNDATION`

**PostgreSQL run-id final:** `20260817T172555Z_32e9c1`
**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó únicamente `foundation/0004_qms_harmonized_context_foundation`. Es aditiva, reversible y condiciona el DDL específico a PostgreSQL para conservar la suite SQLite. Crea seis tablas tenant-scoped: `qms.stakeholder`, `qms.process`, `qms.stakeholder_requirement`, `qms.context_item`, `qms.qms_scope` y `qms.qms_scope_process`.

Las migrations promovidas no cambiaron. Hashes: `0001=0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51`, `0002=1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537`, `0003=dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc`. Hash Phase 4: `0004=045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125`.

PostgreSQL real verificó `0001 → 0002 → 0003 → 0004 → 0003 → 0004`. La reversa eliminó sólo las seis tablas y tres funciones Phase 4; `TenantProjection`, `Organization`, `UserProjection`, `DomainEvent`, `TransactionalOutbox`, `ConsumerReceipt` e `ImmutableAuditLog` permanecieron.

## 2. Stakeholder

`Stakeholder` es el único objeto empresarial, sin clones por norma. Campos respaldados: UUID interno, `tenant_id`, `organization_id`, `stakeholder_type`, `name`, `relevance_score`, `created_at`, `updated_at`. `relevance_score`, cuando existe, está limitado a `[0,1]`; nombre y tipo no pueden estar vacíos. No se inventó lifecycle no presente en las fuentes.

La FK compuesta `(tenant_id,organization_id) → Organization(tenant_id,id)` rechaza una Organization de otro tenant. Trigger DB impide cambiar `tenant_id` u `organization_id`. App carece de DELETE grant para preservar el objeto permanente.

## 3. StakeholderRequirement y versionado

`StakeholderRequirement` representa el requisito empresarial y permanece separado de `RequirementControl`. Cada fila es una revisión append-only con `id`, `tenant_id`, `organization_id`, `stakeholder_id`, `lineage_id`, `revision`, `previous_revision_id`, `requirement_text`, `qms_addressed`, `owner_process_id`, `change_reason` y `created_at`.

La primera revisión exige `lineage_id=id`, `revision=1` y predecessor nulo. Revisiones posteriores exigen predecessor del mismo tenant, Organization y lineage, y exactamente `prior.revision+1`. `UNIQUE(tenant_id,organization_id,previous_revision_id)` impide bifurcación; constraints impiden self-supersession; la progresión estricta impide ciclos. UPDATE/DELETE son rechazados por trigger y no tienen grants runtime.

## 4. Requirement supersession

El gate creó `R v1 → R v2 → R v3`. Conservó las tres filas, predecessors `NULL → v1 → v2`, mismo stakeholder/tenant/Organization/lineage, revisión actual v3, tres eventos y audit stream válido. Intentos de overwrite, self-supersession, predecessor cross-tenant y stakeholder cross-tenant fueron rechazados por PostgreSQL.

La concurrencia no necesita UPDATE lock sobre filas append-only: las uniques de predecessor y `(tenant,organization,lineage,revision)` garantizan un único ganador; una bifurcación concurrente falla y hace rollback.

## 5. Process foundation

`Process` contiene UUID, tenant, Organization, `name`, `owner_id` opcional hacia `UserProjection`, `process_type`, `status` y timestamps. Las fuentes respaldan esos campos. No se agregaron KPI, resources, Risk, Objective, Evidence ni clause mapping. FKs compuestas protegen Organization y owner tenant. Trigger impide reasignar tenant/Organization y app no tiene DELETE grant.

## 6. Context foundation e historia

`ContextItem` distingue `internal` y `external`; contiene descripción, tenant, Organization y el mismo esquema explícito de lineage/revision/predecessor. No usa JSON blob ni se confunde con KnowledgeLayer. `Context v1 → v2` quedó reconstruible; v1 conservó su texto. UPDATE/DELETE son rechazados y una revisión cross-tenant falla por FK/trigger.

La solución es deliberadamente mínima: registra cuestiones internas/externas versionadas, no implementa Context Twin, signals automáticos, scoring, KnowledgeLayer ni agentes.

## 7. QMS Scope foundation e historia

`QmsScope` versiona los conceptos fuente de 4.3 en columnas explícitas: `boundaries`, `applicability` y `products_services`; además contiene tenant, Organization, lineage, revision, predecessor, reason y timestamp. `QmsScopeProcess` congela por revisión los Processes incluidos mediante dos FKs compuestas tenant+Organization.

El gate reconstruyó `Scope v1 → Scope v2`, conservó límites v1 y los links de Process de ambas revisiones. No se creó Site ni producto/servicio como entidad porque no existen aún en la foundation disponible; tampoco se evaluaron exclusiones normativas.

## 8. Relaciones y constraints cross-tenant

Todas las relaciones críticas usan FKs compuestas o enforcement equivalente: Stakeholder→Organization; Process→Organization/UserProjection; Requirement→Stakeholder/Process/predecessor; Context→Organization/predecessor; Scope→Organization/predecessor; ScopeProcess→Scope/Process. Las tablas parent exponen las uniques compuestas necesarias. El gate ejecutó SQL directo inválido para Organization, Process, Stakeholder, predecessor y Scope graph, y PostgreSQL rechazó cada cruce.

## 9. RLS y principals

Las seis tablas tienen simultáneamente `relrowsecurity=true` y `relforcerowsecurity=true`, inspeccionado en catálogo. Existen 30 policies: SELECT/INSERT/UPDATE/DELETE explícitas más policy migrator por tabla. Una policy no concede permiso: las tablas versionadas sólo dan SELECT/INSERT a app; Stakeholder/Process dan SELECT/INSERT/UPDATE; worker sólo SELECT; projector cero permisos Phase 4.

| Tabla | App A | No tenant | App B | Worker A/none/B |
|---|---:|---:|---:|---|
| Stakeholder | 1 | 0 | 1 | 1/0/1 |
| Process | 1 | 0 | 1 | 1/0/1 |
| StakeholderRequirement | 3 | 0 | 1 | 3/0/1 |
| ContextItem | 2 | 0 | 1 | 2/0/1 |
| QmsScope | 2 | 0 | 1 | 2/0/1 |
| QmsScopeProcess | 2 | 0 | 1 | 2/0/1 |

Los cinco LOGIN fueron reales, non-superuser, `NOBYPASSRLS` y non-owner: migrator, app, worker, projector y audit writer. Projector mantuvo cero business access Phase 4.

## 10. Commands, events y contratos

`QmsContextCommandService` expone: `create_stakeholder`, `update_stakeholder`, `create_stakeholder_requirement`, `supersede_stakeholder_requirement`, `create_process`, `update_process`, `create_context_item`, `supersede_context_item`, `create_scope` y `revise_scope`. No expone event/audit injection.

Eventos schema version 1: `stakeholder.created`, `stakeholder.updated`, `stakeholder_requirement.created`, `stakeholder_requirement.superseded`, `process.created`, `process.updated`, `context_item.created`, `context_item.superseded`, `qms_scope.created`, `qms_scope.revised`. Payload, routing, aggregate identity/version, trace y hash usan la foundation Phase 3 y canonicalización `iso-smart-canonical-json-v1`.

## 11. Atomicidad, outbox y audit

Cada command abre el único `trusted_tenant_context` exterior y persiste business mutation + DomainEvent + TransactionalOutbox + ImmutableAuditLog antes del commit. Éxito se demostró para Stakeholder, Requirement, Process, Context y Scope con tenant, trace y aggregate coincidentes.

Fallos deliberados después del append audit y antes de commit se probaron para Requirement supersession, Process update y Context supersession. No sobrevivió business row, event, outbox ni audit, y el nombre de Process original permaneció.

Los audit streams extienden la chain promovida. El stream Requirement v1/v2/v3 verificó secuencias, previous hashes, payload hashes y entry hashes. Runtime continúa sin UPDATE/DELETE/TRUNCATE/forge sobre audit.

## 12. Raw SQL, worker, pool y rollback context

Las matrices se ejecutaron con principals runtime y SQL directo; no dependieron de filtros ORM. La misma conexión probó `A → commit → none → B`. Otra secuencia probó `A → exception → rollback → none → B`. Worker obtuvo A only/B only y cero sin tenant en las seis tablas. No hubo traversal cross-tenant.

## 13. PostgreSQL, regresión e integridad

Corrida final: PostgreSQL `18.6`, `server_version_num=180006`, Podman official image, endpoint efímero `127.0.0.1:33607`, run-id `20260817T172555Z_32e9c1`.

| Gate | Resultado |
|---|---|
| Backend completo | **120 PASS / 0 FAIL / 0 SKIP** |
| Delta vs baseline 115 | **+5** contract tests Phase 4 |
| Foundation unit suite | **22 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL Phase 1–4 | PASS |
| Forward/reverse/forward | PASS |

Warnings legacy de paginación y telemetría Chroma/PostHog no produjeron failures ni skips.

## 14. Source integrity y teardown

Los diez hashes recalculados fueron exactamente: `8308bd…`, `e0a59c…`, `11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`, `eb4231…`: **10/10 MATCH**. Ningún source artifact fue modificado.

Teardown final: DB y cinco roles eliminados; container, volume y temp dir ausentes. No se usaron producción, staging, DB compartida, AdminApps DB ni MedSupplier DB. No hubo deployment, cambios `.env`, secretos ni repos externos.

## 15. Riesgos residuales

1. Los command services son foundation interna; endpoints/OpenAPI/permissions de producto quedan para una slice contract-first futura.
2. Scope modela products/services como campo tipado de dominio, no como relación, porque no existe entidad fuente disponible; Site también queda diferido.
3. Stakeholder/Process conservan UPDATE ordinario para sus campos materiales; la disciplina business+event+outbox+audit se aplica mediante el command service. Un futuro hardening puede restringir DML a funciones DB controladas si se exige impedir bypass por SQL comprometido.
4. Audit sigue siendo append-only para runtime y tamper-evident, no indestructible frente a DBA; checkpoints WORM siguen pendientes.
5. No hay transport/broker productivo, endpoints, backfill, dual-write ni integración con modelos legacy. Todos permanecen fuera de alcance.

No quedan P0 ni P1 bloqueando la siguiente domain slice.

## 16. Veredicto

**PHASE 4 — QMS HARMONIZED CORE CONTEXT FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001/0002/0003` | FROZEN / INTACTO | hashes promovidos exactos | Evolucionar sólo 0005+ |
| `0004_qms_harmonized_context_foundation` | PROMOTED | PostgreSQL forward/reverse/forward; hash `045043…` | Congelar tras promoción |
| Stakeholder | PROMOTED | composite Organization FK, RLS, commands/event/outbox/audit | API futura |
| StakeholderRequirement | PROMOTED | v1→v2→v3, append-only, no cycles/forks | Integrar Risk next |
| Process | PROMOTED | tenant/Organization guards; update rollback | Integrar Risk/Objective next |
| ContextItem | PROMOTED | internal/external, v1→v2 | Context Twin posterior |
| QmsScope/QmsScopeProcess | PROMOTED | v1→v2 + structured Process links | Site/product entities futuras |
| RLS/principals | PASS | 6 tables, 30 policies, A/B/none, worker/projector | Repetir por nuevas tablas |
| Event/Outbox/Audit | PASS | success + rollback + chain | Operación/transport futuros |
| Backend/Django | PASS | 120/0/0; check/drift/compile | Mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | Preservar byte-for-byte |
| Recursos efímeros | REMOVED | teardown PASS | Ninguna acción |
