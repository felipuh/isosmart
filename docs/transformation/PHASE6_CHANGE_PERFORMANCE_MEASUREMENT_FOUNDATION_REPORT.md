# Phase 6 — Change + Performance Measurement Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 6 — CHANGE + PERFORMANCE MEASUREMENT FOUNDATION`

**PostgreSQL run-id final:** `20260817T180743Z_90a38e`
**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó únicamente `foundation/0006_change_performance_measurement_foundation`. La migration es aditiva y reversible: crea `qms.change`, `qms.change_process` y `qms.measurement_definition`, y agrega `qms.objective.metric_id` nullable con FK tenant/Organization-safe a una revisión concreta de `MeasurementDefinition`.

| Migration | SHA-256 | Estado |
|---|---|---|
| `0001_foundation_tenant_projection` | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` | frozen/intacta |
| `0002_projection_organization_user_foundation` | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` | frozen/intacta |
| `0003_eventing_immutable_audit_foundation` | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` | frozen/intacta |
| `0004_qms_harmonized_context_foundation` | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` | frozen/intacta |
| `0005_risk_opportunity_objective_foundation` | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` | frozen/intacta |
| `0006_change_performance_measurement_foundation` | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` | nueva |

PostgreSQL verificó `0001 → 0002 → 0003 → 0004 → 0005 → 0006 → 0005 → 0006`. La reversa elimina sólo las tres tablas Phase 6, la FK/columna `objective.metric_id` y las tres funciones Phase 6. Después de la reversa `Risk` y `Objective` permanecieron disponibles y `metric_id` quedó ausente, exactamente como en Phase 5.

## 2. Source gate de measurement

Se leyeron directamente DOCX, XLSX `DB_Entities`/`Event_Catalog`/mapa maestro, JSON `master`/`entities`/`events`, DDL y CSV relevantes.

| SOURCE | TERM | ENTITY/FIELD | SEMANTICS | IMPLEMENTATION JUSTIFIED? | RATIONALE |
|---|---|---|---|---:|---|
| XLSX/JSON `DB_Entities` | Objective metric | `Objective.metric_id` | referencia de métrica del objetivo | Sí | campo estructurado explícito y coincidente |
| DOCX/XLSX/JSON 9.1.1 | seguimiento/medición | qué medir, método y momento | definición operativa de una medición | Sí | tres responsabilidades explícitas soportan `MeasurementDefinition` |
| DOCX/XLSX/JSON 9.1.x | KPI | entrada del Performance Tracker | concepto/product input | No como entidad | no existe `KPI` en las 43 entidades ni campos canónicos propios |
| JSON/XLSX Event Catalog | Measurement | `measurement.out_of_tolerance` | aggregate/event trigger futuro | No como schema de registro | el catálogo no define identidad, `value` ni timestamp de observación |
| DOCX/XLSX/JSON | mediciones | ejemplos/entradas | observaciones de desempeño | No para `MeasurementRecord` | no hay campos estructurados suficientes para un registro canónico |
| DOCX/XLSX/JSON 9.1.1 | Process | graph object de evaluación | contexto de proceso para definición | Sí, opcional | Process aparece explícitamente en el graph object y ya tiene boundary promovido |

Decisión: **B — `MeasurementDefinition` únicamente**. A queda superado porque 9.1.1 define estructura mínima; C no queda justificado porque faltan `value`, timestamp e identidad canónica de observación; D queda rechazado porque KPI es hoy concepto semántico/producto y no una entidad canónica. No se creó `MeasurementRecord`, `KPI`, dashboard, agregación, fórmula, alert rule, trend engine, scoring, warehouse ni AI analysis.

## 3. Change schema e historia

`Change` es un business object independiente, no una revisión de Process/Risk/Opportunity/Objective. Cada revisión append-only contiene UUID interno, `tenant_id`, `organization_id`, `lineage_id`, `revision`, predecessor, `type`, `purpose`, `impact`, `status`, `approval_id` nullable, reason y timestamp.

El gate creó `Change v1 → v2 → v3`: v1/v2/v3 permanecieron, el leaf único fue v3 y los predecessors quedaron `NULL → v1 → v2`. Uniques de predecessor y `(tenant,organization,lineage,revision)` impiden forks; el trigger exige incremento exacto y mismo boundary/lineage, por lo que self-reference/ciclos y predecessor cross-tenant quedan rechazados. UPDATE/DELETE histórico se rechaza por trigger y grants.

Los artefactos no enumeran valores ni transiciones de status. Por ello Phase 6 no inventa una workflow engine ni un enum artificial: PostgreSQL rechaza NULL, vacío/whitespace y valores fuera de longitud; el command conserva el status fuente como texto material no vacío. No se afirma un transition graph que las fuentes no definen.

## 4. Relaciones Change

La ficha 6.3 incluye `Process` en `graph_objects`; se materializó `ChangeProcess` normalizado por revisión. Cada revisión conserva su snapshot de Processes afectados y las FKs compuestas verifican Change revision y Process bajo el mismo tenant/Organization.

Risk aparece como histórico/entrada funcional, no como FK de instancia de Change. Opportunity y Objective tampoco aparecen como relaciones estructuradas de Change. Por tanto no se crearon `ChangeRisk`, `ChangeOpportunity` ni `ChangeObjective`. Change no muta lateralmente ningún agregado; cualquier revisión futura de Risk/Objective debe entrar por su command boundary promovido.

## 5. Approval y Effectiveness

`approval_id` queda como referencia UUID nullable/diferida, sin FK, porque `Approval` es una entidad maestra futura y crear una tabla mínima ahora arriesgaría incompatibilidad con el Human Decision Gate canónico. No se creó Approval ni workflow humano.

La eficacia mencionada en 6.3 se documenta como relación futura con `EffectivenessCheck`. No se agregó pseudo-check, resultado o método dentro de Change, y no se implementó el agregado productivo fuera de alcance.

## 6. MeasurementDefinition y Objective.metric_id

`MeasurementDefinition` es append-only y contiene UUID, tenant, Organization, lineage/revision/predecessor, Process opcional, `what_is_measured`, `method`, `measurement_timing`, reason y timestamp. No contiene unit, target copiado, fórmula ejecutable, thresholds ni registros de valor porque las fuentes no los definen como campos canónicos.

`Objective.metric_id` ahora referencia una revisión específica de `MeasurementDefinition` mediante FK `(tenant_id,organization_id,metric_id)`. Esto satisface el campo fuente y congela la definición aplicable a la revisión de Objective; una revisión posterior de la definición no reinterpreta silenciosamente el Objective histórico. La columna es nullable para conservar filas Phase 5 y permitir adopción incremental.

## 7. Tenancy, RLS y constraints

Las tres tablas nuevas tienen `tenant_id NOT NULL`, Organization directa, `ENABLE ROW LEVEL SECURITY` y `FORCE ROW LEVEL SECURITY`. Se inspeccionaron 15 policies: SELECT/INSERT/UPDATE/DELETE explícitas y ALL migrator por tabla. Policies y grants quedan separados.

| Tabla | App A | No tenant | App B | Worker A/none/B | App grants |
|---|---:|---:|---:|---:|---|
| Change | 3 | 0 | 1 | 3/0/1 | SELECT, INSERT |
| ChangeProcess | 3 | 0 | 1 | 3/0/1 | SELECT, INSERT |
| MeasurementDefinition | 2 | 0 | 1 | 2/0/1 | SELECT, INSERT |

Projector y audit writer tienen cero acceso business Phase 6. Migrator, app, worker, projector y audit writer fueron LOGIN reales, non-superuser, `NOBYPASSRLS` y non-owner de las tablas protegidas.

PostgreSQL rechazó por constraint/trigger, independientemente de RLS: Change A→Process B, MeasurementDefinition A→Process B, Objective A→MeasurementDefinition B, predecessor Change cross-tenant, tenant reassignment y Organization reassignment. Las relaciones Risk/Opportunity/Objective no existentes no tienen un traversal que proteger.

## 8. Commands y eventos

`ChangePerformanceCommandService` expone exclusivamente:

- `create_change`, `revise_change`, `change_change_status`;
- `define_measurement`, `revise_measurement_definition`.

No expone `record_measurement` porque C no pasó el source gate, ni endpoints de event/audit injection.

Contratos schema version 1: `change.created`, `change.revised`, `change.status_changed`, `measurement_definition.created` y `measurement_definition.revised`. Envelopes y payloads son typed, canonicalizados, tenant/trace/aggregate-aware y versionados.

`change.detected` es un trigger de análisis descrito en las fichas, no el hecho de crear el business object; por eso no se emitió al ejecutar `create_change`. El catálogo también define `change.requested`, que describe activación de 6.3; no se reutilizó para confundir request/event ingress con persistencia de Change. `change.created` expresa exclusivamente creación canónica del agregado.

## 9. Atomicidad, outbox y audit

Cada command ejecuta business mutation → DomainEvent → TransactionalOutbox → ImmutableAuditLog dentro del único `trusted_tenant_context`/`transaction.atomic()`.

Éxito quedó demostrado para Change create/revise/status, MeasurementDefinition create/revise y Objective create con `metric_id`: business/event/outbox/audit compartieron tenant, trace y aggregate. Fallos deliberados después del append audit y antes del commit para Change revision y MeasurementDefinition revision conservaron conteos exactos previos: cero business revision, event, outbox o audit parcial.

Las chains de Change v1/v2/v3 y MeasurementDefinition v1/v2 verificaron secuencia, previous hash, payload hash y entry hash. Runtime continúa sin UPDATE/DELETE/TRUNCATE ni forge directo sobre `ImmutableAuditLog`; no se ampliaron privilegios del audit writer.

## 10. Raw SQL, worker, pool y rollback

La matriz usó SQL directo y roles runtime reales. A no leyó B; sin tenant obtuvo cero; B leyó sólo B. Inserts con Process/metric/predecessor del tenant incorrecto fallaron. UPDATE histórico, tenant/Organization reassignment y DELETE runtime fallaron.

Worker obtuvo A only/B only y cero sin tenant, con SELECT únicamente; no registra mediciones ni selecciona tenants arbitrariamente. La conexión reutilizada pasó `A → commit → none → zero → B → B only`. La ruta con excepción pasó `A → rollback → none → zero → B → B only`.

## 11. PostgreSQL, regresión e integridad Django

Corrida final: PostgreSQL `18.6`, `server_version_num=180006`, imagen oficial, endpoint efímero `127.0.0.1:43531`, run-id `20260817T180743Z_90a38e`.

| Gate | Resultado |
|---|---|
| Backend completo | **130 PASS / 0 FAIL / 0 SKIP** |
| Delta vs baseline 125 | **+5** contract tests Phase 6 |
| Foundation unit suite | **32 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL Phase 1–6 | PASS |
| Forward/reverse/forward | PASS |

Los mensajes esperados de pruebas de autenticación no fueron failures ni skips.

## 12. Source integrity y teardown

Los diez SHA-256 recalculados coinciden exactamente con el manifest: `8308bd…`, `e0a59c…`, `11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`, `eb4231…`: **10/10 MATCH**. Ningún source artifact fue modificado.

La primera invocación de Podman fue denegada por sandbox y aun así verificó teardown. La corrida autorizada final eliminó database y cinco roles; container, volume y temp dir quedaron ausentes. No se usaron producción, staging, DB compartida, AdminApps DB ni MedSupplier DB. No hubo deployment, cambios `.env`, secretos ni repos externos.

## 13. Riesgos residuales

1. Las fuentes no fijan enum/transiciones de Change; Phase 6 sólo puede garantizar status material no vacío y evolución auditada. Un workflow futuro requiere decisión fuente/ADR.
2. `approval_id` no tiene integridad referencial hasta la foundation canónica de Approval; sigue nullable y no autoriza decisiones.
3. No existe MeasurementRecord: el producto aún no puede persistir observaciones canónicas hasta que fuentes/contrato definan identidad, valor, timestamp y corrección.
4. `MeasurementDefinition.process_id` es opcional y `Objective.metric_id` apunta a revisión específica; una futura UX/repository debe mostrar definición current vs frozen sin reinterpretar historia.
5. No hay relaciones Change→Risk/Opportunity/Objective de instancia. Deben agregarse sólo cuando una fuente establezca semántica y cardinalidad.
6. Commands son foundation interna; endpoints/OpenAPI, broker y Performance Tracker completo siguen fuera de alcance.
7. Audit permanece append-only/tamper-evident para runtime, no físicamente indestructible frente a DBA; checkpoints WORM quedan futuros.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 14. Veredicto

**PHASE 6 — CHANGE + PERFORMANCE MEASUREMENT FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001–0005` | FROZEN / INTACTO | hashes promovidos exactos | Evolucionar sólo 0007+ |
| `0006_change_performance_measurement_foundation` | PROMOTED | PostgreSQL forward/reverse/forward; hash `033242…` | Congelar tras promoción |
| Change | PROMOTED | v1→v2→v3, leaf único, no fork/cycle, atomic/audit | Workflow enum sólo con fuente |
| ChangeProcess | PROMOTED | snapshot por revisión; composite FKs | Otras relaciones sólo source-backed |
| Approval | DEFERRED | UUID nullable sin FK; no Human Gate artificial | Foundation canónica futura |
| Effectiveness | DEFERRED | sin pseudo EffectivenessCheck | Agregado futuro separado |
| Measurement source gate | B / PROMOTED | 9.1.1 qué/método/momento; no record fields | Reabrir C sólo con contrato fuente |
| MeasurementDefinition | PROMOTED | v1→v2; Process opcional; atomic/audit | MeasurementRecord futuro |
| Objective.metric_id | PROMOTED | FK compuesta a revisión congelada | Binding UX/repository futuro |
| KPI | SEMANTIC ONLY | input/event terms, no entity schema | No crear tabla sin evidencia |
| RLS/principals | PASS | 3 tables, 15 policies, A/B/none, worker | Repetir por nuevas tablas |
| Event/Outbox/Audit | PASS | typed v1 contracts, success + rollback + chain | Transport futuro |
| Backend/Django | PASS | 130/0/0; check/drift/compile | Mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | Preservar byte-for-byte |
| Recursos efímeros | REMOVED | database/roles/container/volume/temp absent | Ninguna acción |
