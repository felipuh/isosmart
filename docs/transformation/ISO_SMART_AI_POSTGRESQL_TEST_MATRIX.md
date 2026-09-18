# ISO Smart AI — matriz ejecutable PostgreSQL/RLS

## Entorno gate

PostgreSQL 18.6 efímero, migrations desde cero, roles reales (`owner`, `migrator`, `app`, `worker`, `readonly`), dos TenantProjection A/B y fixtures sintéticas. La suite conecta como runtime role; una conexión owner separada sólo prepara/inspecciona. Se ejecuta en CI y local aislado, no sobre DB compartida.

El reporte debe identificar `SELECT version()`/`server_version`, rol efectivo, tablas POC inspeccionadas y resultados de cada escenario. Ninguna aserción catalogal puede sustituirse por inspección de migration/setup SQL. La suite no obtiene PASS si se omite, marca skip o ejecuta en SQLite cualquiera de RLS-07, RLS-08, RLS-14, RLS-15, RLS-19 o RLS-21.

### Regla de base efímera dedicada

La instancia pertenece exclusivamente a esta slice y su destrucción es parte esperada del ciclo de prueba. Orden de selección: (1) mecanismo efímero seguro y nativo del repositorio; (2) contenedor Docker/Podman nuevo, con nombre único de corrida, creado sólo para esta prueba; (3) cluster PostgreSQL local aislado con directorio de datos y puerto exclusivos, únicamente si no puede interactuar con clusters existentes. La inspección actual del repositorio no encontró un harness nativo, por lo que la implementación debe usar la opción 2 salvo que se añada antes uno equivalente y verificable.

Está prohibido apuntar a producción, staging, una base persistente de desarrollo ISO Smart, PostgreSQL de AdminApps o cualquier base compartida del ecosistema. Antes de migrations, el harness comprueba allow-list de nombre/recurso, host local/aislado y marcador único de la corrida; ante duda aborta. No acepta una `DATABASE_URL` general como sustituto. Los nombres de contenedor/cluster, base y recursos temporales incluyen un `run_id` no vacío. Teardown usa esos nombres exactos: no usa globs, `prune`, rutas amplias ni elimina volúmenes ajenos.

El test debe registrar sin secretos:

| Campo | Evidencia obligatoria |
|---|---|
| Engine | Mecanismo repo-native, Docker, Podman o cluster local aislado; incluir versión del engine cuando esté disponible |
| PostgreSQL exacto | Salida sanitizada de `SHOW server_version` y confirmación de `18.6`; el tag de imagen por sí solo no basta |
| Port | Puerto host/endpoint dedicado asignado a esta corrida |
| Database | Nombre único de la base POC |
| Roles | Nombres de owner, migrator, app, worker y readonly usados; nunca credenciales |
| Creation command | Comando reproducible sanitizado; reemplazar cualquier secreto por `<redacted>` y no registrar valores de variables secretas |
| Destruction command | Comando exacto y acotado al contenedor/cluster/volumen/directorio únicos de la corrida |
| Lifecycle result | Timestamp/resultado de creación, readiness, ejecución y destrucción; demostrar que el recurso ya no existe al finalizar |

El registro nunca imprime passwords, DSN completos, tokens ni variables de entorno secretas. Incluso en fallo, el teardown se ejecuta mediante cleanup/finalizer. Si la creación, validación de aislamiento o destrucción no queda demostrada, la slice es **NO PASS**.

SQLite puede conservar unit tests puros/serializers sin semantics PostgreSQL. No valida RLS, roles/grants, UUIDv7 DB, partial/concurrent indexes, JSONB, constraints diferibles, locking, `SKIP LOCKED`, pool behavior ni migrations PostgreSQL.

## Convención de resultados

Para cada tabla CRUD crítica se ejecutan cuatro operaciones. `A→A allow`; `A→B` y `B→A` deben ser invisible para SELECT/UPDATE/DELETE y rechazados por INSERT/relación; `No tenant` devuelve cero en SELECT y error/0 rows en writes según statement, nunca acceso. UPDATE incluye intento de cambiar `tenant_id`. DELETE sólo se prueba si el rol tiene permiso funcional; tablas append-only deben negar incluso same-tenant.

| Tabla/grupo crítico | CREATE A→A | SELECT A/B/none | UPDATE A→A / cross / tenant move | DELETE A→A / cross / none | Nota específica |
|---|---|---|---|---|---|
| TenantProjection | provisioning role only | own / hidden / none | allowed fields / hidden / ID move denied | runtime denied | external ID immutable |
| Organization, Site | allow | own / hidden / none | allow / 0 / tenant move denied | policy-specific / 0 / denied | composite FK Site→Org |
| Process, Stakeholder, StakeholderRequirement | allow | own / hidden / none | allow / 0 / move denied | allow/soft-delete policy / 0 / denied | child relation A→B rejected |
| Risk, Opportunity, Objective, Change | allow | own / hidden / none | allow / 0 / move denied | lifecycle policy / 0 / denied | Approval A/B mismatch rejected |
| Document | allow | own / hidden / none | allow / 0 / move denied | soft lifecycle / 0 / denied | current version same tenant |
| DocumentVersion | allow | own / hidden / none | **deny after insert/publish** | **deny** | append-only; indirect-parent policy test if no direct ID |
| Evidence | allow | own / hidden / none | metadata state only / cross denied | **deny or retention workflow only** | hash/source immutable |
| EvidenceCoverage | allow | own / hidden / none | validation transition / cross denied | **deny; supersede** | evidence tenant + global edition/control/rule frozen |
| EvidenceGraphEdge | allow only A→A | own / hidden / none | A→A / cross endpoints denied | allow/supersede / hidden / denied | both endpoints composite constrained |
| Recommendation | allow via runtime | own / hidden / none | state only / cross denied | deny | body/basis publication immutable |
| RecommendationBasis | allow A parent/refs | own / hidden / none | deny | deny | evidence A + global rule; child relation test |
| AgentRun, AgentDecision | allow | own / hidden / none | completion-only / cross denied | deny | trace/event tenant match |
| Approval | allow | own / hidden / none | single transition / cross/replay denied | deny | actor/role/expiry tests |
| ActionExecution, EffectivenessCheck | allow if approved A | own / hidden / none | state/result / cross denied | deny | approval/recommendation/evidence A only |
| Audit, Finding | allow | own / hidden / none | workflow/supersede / cross denied | deny | requirement global, evidence tenant A |
| Nonconformity, CorrectiveAction | allow | own / hidden / none | workflow / cross denied | deny | NC/CA/effectiveness same tenant |
| QuizAttempt, ConceptMastery | allow | own / hidden / none | attempt immutable; mastery projection scoped | deny/history policy | UserProjection A + global learning release |
| DomainEvent | service insert | own/dispatcher policy / hidden / none | deny | deny | system events use distinct role/policy |
| TransactionalOutbox | service insert same tx | dispatcher sees authorized rows only | lease/publish fields only | deny | event/outbox tenant match |
| EventInbox/ConsumerReceipt | consumer insert | own/consumer scope | status transition only | deny | unique consumer+event, hash mismatch quarantine |
| ImmutableAuditLog | append function only | own/redacted / hidden / none | **deny** | **deny** | TRUNCATE denied; chain verification |
| StandardPack | allow if entitled | own / hidden / none | workflow / cross denied | deny/history | global edition FK allowed |
| OnboardingWorkflowInstance/Transition | service insert | own / hidden / none | allowed transition only | deny | 17-step state machine |

Global Standard/Edition/Clause/RequirementControl/KnowledgeLayer/Rule/Binding, IndustryProfile, LearningPath, QuestionBank, AgentDefinition and ModelPolicy get a separate grants suite: runtime SELECT allowed, INSERT/UPDATE/DELETE denied; curator release path enforces published append-only/version rules.

## Required scenario matrix

| ID | Setup/action | Expected proof |
|---|---|---|
| RLS-01 | Context A CRUD row A | Allowed according to table lifecycle |
| RLS-02 | Context A reads/updates/deletes row B by exact UUID | 0 rows/404; no attributes leaked |
| RLS-03 | Context A inserts child referencing B parent | constraint/RLS denial; transaction rollback |
| RLS-04 | Context B against A | symmetric denial |
| RLS-05 | No `app.tenant_id` | zero SELECT; INSERT/UPDATE/DELETE denied/0 |
| RLS-06 | Empty/malformed tenant GUC | fail/deny, never fallback |
| RLS-07 | Misma conexión física reutilizada: tx A establece A y lee A → commit → nueva tx sin establecer tenant intenta SELECT y write → establece B en otra tx y consulta | La tx sin contexto devuelve cero y el write se deniega; B ve sólo B; registrar identidad de backend/conexión para probar reuse |
| RLS-08 | Tx atómica establece A, lee A, provoca excepción deliberada y rollback; misma conexión física abre nueva tx sin establecer tenant e intenta SELECT y write; sólo después abre tx con B | Después del rollback, sin contexto devuelve cero y write se deniega; ningún valor A sobrevive; B ve sólo B |
| RLS-09 | Worker event A opens tx/context; next event B | effects isolated; envelope/aggregate mismatch quarantined |
| RLS-10 | Worker missing tenant or inactive projection | no domain query/effect; failed/quarantined task |
| RLS-11 | Join A parent to B child attempt and nested subquery | no B rows; cross FK impossible |
| RLS-12 | Raw SQL repository with A/B/none | same RLS outcomes as ORM |
| RLS-13 | `bulk_create`, bulk update/upsert with mixed A/B | whole batch rejected or rows strictly scoped; specified behavior tested |
| RLS-14 | Consultar rol efectivo y `pg_roles`; unir `pg_class` + `pg_namespace` + `pg_roles` para cada tabla POC protegida | `rolsuper=false`, `rolbypassrls=false` y owner distinto del runtime en todas las tablas; adjuntar filas/resultados de catálogo |
| RLS-15 | Consultar `pg_class` para cada tabla POC protegida después de migrations | Cada fila tiene a la vez `relrowsecurity=true` y `relforcerowsecurity=true`; policies esperadas presentes; adjuntar filas/resultados de catálogo |
| RLS-16 | Admin/staff request without tenant | no cross-tenant access; platform operation uses separate audited path |
| RLS-17 | Management command no `--tenant` | exits safely without data access |
| RLS-18 | Migration/backfill batch A with injected B relation | stop + checkpoint conflict; no partial contamination |
| RLS-19 | Con contexto A y fila A visible, ejecutar por SQL/ORM `UPDATE ... SET tenant_id = B`; repetir por la ruta de escritura aplicable | Trigger DB independiente de RLS lanza SQLSTATE esperado, transacción revierte y la fila conserva A; no basta un 0-row de policy |
| RLS-20 | Delete/suspend TenantProjection | no cascade/reassignment; lifecycle policy enforced |
| RLS-21 | Enviar tenant B falsificado por body, query y header mientras la identidad/fixture autorizada resuelve A; instrumentar el valor entregado al setter | Las entradas B son ignoradas o rechazadas antes del dominio; el setter recibe únicamente A desde el resolver confiable y nunca un valor libre del request |

## Outbox/audit/normative integration

- Domain change + event + outbox commit together; rollback leaves none.
- Dispatcher duplicate/crash/lease expiry and ConsumerReceipt duplicate yield one logical effect.
- Published RequirementControl/Rule/Edition and DocumentVersion reject runtime mutation; N+1 does not alter N coverage.
- Audit append occurs for material command in same business transaction where required; runtime cannot mutate/delete; chain detects tamper fixture.

## Migration and operational gates

Run forward from empty, forward from synthetic legacy snapshot, reverse where safe, idempotent backfill resume, `NOT VALID` then validation, lock-timeout behavior, EXPLAIN/index assertions for tenant-leading queries, backup/restore then RLS/hash verification. A gate fails on entorno no dedicado/no desechable o teardown no demostrado; versión distinta de 18.6; cualquier cross-tenant row; contexto que sobreviva commit/rollback; setter alimentado por input de request no autorizado; reasignación de tenant no rechazada por el trigger independiente; runtime superuser/owner/BYPASSRLS; tabla POC sin ambos flags RLS; policy ausente; escenario obligatorio skipped; count/hash mismatch sin explicar; o mutación del artefacto fuente.
