# ISO Smart AI — arquitectura de datos

## Principios

- PostgreSQL es la fuente transaccional; no usar Chroma, Redis ni un grafo externo como autoridad.
- UUID (`uuid7` cuando la biblioteca/baseline lo permita; UUID4 como fallback estable) para nuevas entidades públicas. Las PK enteras legadas se conservan durante compatibilidad.
- `timestamptz`, UTC en persistencia y timezone de organización solo en presentación/reglas de calendario.
- JSONB solo para envelopes/versioned snapshots o atributos extensibles con schema; relaciones y campos consultables son columnas/FK.
- Nunca actualizar en sitio una edición, regla o evidencia histórica; usar vigencias/versiones y referencias congeladas.

## Baseline PostgreSQL verificado

**Target de implementación para la foundation efímera/greenfield: PostgreSQL 18.6**, release de mantenimiento/seguridad vigente al 2026-08-13. El Design Gate original evaluó 18.4; la revalidación oficial previa a implementación corrige sólo el patch target y mantiene intacta la arquitectura PostgreSQL 18 aprobada. PostgreSQL 18 está soportado hasta noviembre de 2030 y ofrece `uuidv7()` nativo. El servidor productivo actual no está inventariado: adoptar 18 en producción queda condicionado a compatibilidad de plataforma, driver, backup/PITR, pooler y restore drill. PostgreSQL 19 beta/desarrollo no es elegible. Fuentes: [release notes 18.6](https://www.postgresql.org/docs/18/release-18-6.html), [versioning policy](https://www.postgresql.org/support/versioning/) y [UUID functions 18](https://www.postgresql.org/docs/18/functions-uuid.html).

- Extensions obligatorias: **ninguna**. El `CREATE EXTENSION pgcrypto` del DDL de referencia no es necesario para UUIDv4/v7 en PostgreSQL 18. `pg_trgm`, vector u otras extensiones sólo entran con caso medido, security review y ADR.
- IDs nuevos: UUIDv7 generado en PostgreSQL 18 o en una única librería RFC 9562 validada; nunca mezclar representaciones. IDs externos AdminApps son opacos y separados.
- Fechas: `timestamptz NOT NULL`, persistencia UTC; `date` sólo para fechas civiles; timezone IANA en Organization/Site para reglas/presentación.
- Convención: `snake_case`, singular para tablas objetivo, PK `<entity>_id` o `id` de forma consistente por slice, FK con nombre de agregado, constraints/índices nombrados (`pk_`, `fk_`, `uq_`, `ck_`, `ix_`, `pol_`).
- Schemas propuestos: `control_plane`, `normative`, `qms`, `eventing`, `governance`, `audit`. Aíslan grants y ownership; la primera slice debe probar compatibilidad Django/migrations/search_path antes de aceptarlos físicamente. Si falla, mantener `public` con prefijos y conservar límites lógicos.
- Pool: PgBouncer transaction pooling es compatible sólo si cada caso de uso abre transacción y usa `set_config(..., true)`/`SET LOCAL`; no usar session state. Presupuestar conexiones web/worker/admin y limitar `idle_in_transaction_session_timeout`.

## Roles y ownership

| Rol | Login | Owner | BYPASSRLS | Función |
|---|---:|---:|---:|---|
| `isosmart_owner` | No | Sí, objetos | No | Ownership técnico; no usado por runtime |
| `isosmart_migrator` | Sí, restringido CI/release | No (puede `SET ROLE owner` controlado) | No por defecto | Migrations/DDL; ventana auditada |
| `isosmart_app` | Sí | No | No | Requests ordinarios; DML mínimo; RLS forzada |
| `isosmart_worker` | Sí | No | No | Workers tenant-scoped; queues allow-listed |
| `isosmart_readonly` | Sí/restringido | No | No | Lectura tenant-scoped; contexto obligatorio |
| `isosmart_audit_writer` | No login o uso mediante función | No | No | Sólo INSERT audit vía función `SECURITY DEFINER` endurecida |
| `isosmart_backup` | Restringido | No | No | Backup físico/lógico según runbook; sin app use |
| `isosmart_breakglass` | Sí, vaulted | No | sólo si operación aprobada | Incidente excepcional, MFA/dual control/audit |

Superuser no se usa para aplicación, migration cotidiana, worker ni soporte. `search_path` se fija a schemas allow-listed + `pg_catalog`; no se concede `CREATE` a runtime.

## Matriz global, tenant y versionado

Retention se expresa como política, no como plazo inventado. `Legal` significa conservar según compliance/contrato; `lifecycle+grace` requiere aprobación de Data Owner.

| Entity | Classification | tenant_id? | RLS? | Why / System of record | Mutability | Retention |
|---|---|---:|---:|---|---|---|
| Tenant (`TenantProjection`) | TENANT PROJECTION | PK scope | Sí, acceso propio; admin separado | AdminApps | Upsert versionado; IDs inmutables | Tombstone + legal |
| User (`UserProjection`) | TENANT PROJECTION | Sí | Sí | AdminApps identity; QMS attrs locales separados | Upsert/tombstone | Identity/legal |
| Organization | TENANT DOMAIN DATA | Sí | Sí | ISO Smart QMS | Mutable, version/audit | Lifecycle+legal |
| Site | TENANT DOMAIN DATA | Sí | Sí | ISO Smart QMS | Mutable | Lifecycle+legal |
| Standard | GLOBAL REFERENCE DATA | No | No; grants | Catálogo curado | Append/versioned | Permanente |
| StandardEdition | NORMATIVE VERSIONED DATA | No | No; grants | Catálogo curado/licenciado | Draft mutable; published append-only | Permanente |
| Clause | NORMATIVE VERSIONED DATA | No | No; grants | Edition | Published append-only | Permanente |
| RequirementControl | NORMATIVE VERSIONED DATA | No | No; grants | Edition/clause | Published append-only | Permanente |
| KnowledgeLayer | GLOBAL REFERENCE DATA | No | No; grants | Catálogo curado | Versionada | Permanente |
| KnowledgeLayerRule | NORMATIVE VERSIONED DATA | No | No; grants | Layer/edition | Published append-only | Permanente |
| KnowledgeLayerBinding | NORMATIVE VERSIONED DATA | No | No; grants | Binding curado | Append-only por release | Permanente |
| StandardPack | TENANT DOMAIN DATA | Sí | Sí | ISO Smart, bounded by entitlement | State machine | Lifecycle+history |
| Process | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Mutable/versioned where material | Lifecycle+legal |
| Stakeholder | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Mutable + audit | Lifecycle/privacy |
| StakeholderRequirement | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Supersede/version | Lifecycle+legal |
| Risk | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Assessment versions, no norm clones | Lifecycle+legal |
| Opportunity | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Version/audit | Lifecycle |
| Objective | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Version/audit | Lifecycle+legal |
| Change | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Workflow append history | Legal |
| Document | TENANT DOMAIN DATA | Sí | Sí | ISO Smart identity/lifecycle | Mutable pointer/status | Lifecycle+legal |
| DocumentVersion | TENANT DOMAIN DATA | Sí | Sí | ISO Smart/object store | Immutable after creation/approval | Legal/records policy |
| Evidence | TENANT DOMAIN DATA | Sí | Sí | ISO Smart/provenanced source | Append/supersede | Legal/evidence policy |
| EvidenceCoverage | TENANT DOMAIN DATA | Sí | Sí | ISO Smart, references frozen normative versions | Append/supersede validation | Same as evidence |
| Recommendation | TENANT DOMAIN DATA | Sí | Sí | ISO Smart governed runtime | State transitions; body immutable after publish | Decision/legal |
| RecommendationBasis | TENANT DOMAIN DATA | Sí | Sí | Frozen provenance | Append-only | Same as recommendation |
| AgentDefinition | GLOBAL REFERENCE DATA | No | No; grants | Platform-curated template | Versioned/released | Permanent versions |
| AgentRun | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Append/status completion only | Governance policy |
| AgentDecision | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Append-only | Governance/legal |
| DomainEvent | EVENTING | Sí (`system` allowed explicitly) | Sí | Producer transaction | Append-only | Replay policy |
| Approval | TENANT DOMAIN DATA | Sí | Sí | ISO Smart Human Gate | Append decision; no rewrite | Legal |
| ActionExecution | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Append/status/result | Legal |
| EffectivenessCheck | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Append/result; corrections supersede | Legal |
| Audit | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Workflow + history | Audit policy |
| Finding | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Append/supersede | Audit policy |
| Nonconformity | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Workflow + history | Quality/legal |
| CorrectiveAction | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Workflow + history | Quality/legal |
| IndustryProfile | GLOBAL REFERENCE DATA | No | No; grants | Platform-curated taxonomy | Versioned | Permanent versions |
| LearningPath | NORMATIVE VERSIONED DATA | No | No; grants | Edition/role/industry template | Published append-only | Permanent versions |
| QuestionBank | NORMATIVE VERSIONED DATA | No | No; grants | Learning release | Published append-only; answers restricted | Permanent versions |
| QuizAttempt | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Append-only | Learning/privacy policy |
| ConceptMastery | TENANT DOMAIN DATA | Sí | Sí | ISO Smart | Append assessments/current projection | Learning/privacy policy |
| ModelPolicy | GLOBAL REFERENCE DATA | No | No; grants | Platform governance; tenant assignment separate | Published append-only | Permanent versions |
| ImmutableAuditLog | AUDIT | Sí/system stream | Sí + append-only grants | ISO Smart audit foundation | INSERT only | Legal/security policy |
| Entitlement/Subscription/ProvisioningProjection | TENANT PROJECTION | Sí | Sí | AdminApps | Versioned upsert/tombstone | Contract/legal |
| TenantRoleAssignment | TENANT DOMAIN DATA | Sí | Sí | ISO Smart for QMS-only scope | Mutable + audit | Security policy |
| TransactionalOutbox | EVENTING | Sí/system | Sí; dispatcher policies | Same DB transaction | Append + delivery state | Event policy |
| EventInbox/ConsumerReceipt | EVENTING | Sí/system | Sí | Consumer dedupe | Append/status | Replay policy |
| EvidenceGraphEdge | TENANT DOMAIN DATA | Sí | Sí | Derived/typed domain relationship | Effective-dated; no silent rewrite | Same as referenced records |
| OnboardingWorkflowInstance/Transition | TENANT DOMAIN DATA | Sí | Sí | ISO Smart for steps 7–17 | State + append transitions | Product/legal |

Global tables are not public-write. Runtime normally gets SELECT only; curator/migrator release paths are audited. A `system` event without tenant uses a distinct nullable scope plus restrictive policy/role, not a fake tenant UUID.

## FK, constraints, indexes and JSONB

- Every tenant parent exposes `UNIQUE(tenant_id, id)`; children use composite FKs so a valid foreign ID from another tenant cannot attach.
- `ON DELETE RESTRICT` is default for normative, evidence, audit and provenance. `CASCADE` is allowed only for private, non-record implementation details after review; never for published RecommendationBasis or audit.
- Ranges/confidence have checks; workflow states use checks/reference tables with transitions enforced in service + DB invariants where feasible.
- B-tree indexes begin with `tenant_id` for tenant query patterns; unique business keys are `(tenant_id, normalized_key)`. Partial indexes cover active records, pending approvals and unpublished outbox. Add GIN only for measured JSONB/FTS predicates.
- JSONB is limited to versioned envelopes/snapshots, rule ASTs, bounded extensible metadata and provider payloads after redaction. IDs, tenant, state, timestamps, confidence, hashes and queried relations remain typed columns. Every JSONB has `schema_version` and application/schema validation.

## Tenancy y RLS

Tablas globales deliberadas, sin `tenant_id`: Standard, StandardEdition, Clause, RequirementControl base, KnowledgeLayer/Rule publicados, ModelProvider catalog y schemas de eventos. Su escritura es solo de curadores/platform roles y queda auditada.

Todas las demás tablas llevan `tenant_id NOT NULL` FK a TenantProjection, incluidos joins, outbox tenant events, audit y agent runs. Excepciones necesitan ADR.

Patrón de request:

1. Validar token y entitlement con AdminApps según criticidad/cache policy.
2. Resolver external tenant UUID a TenantProjection activa.
3. Abrir transacción y ejecutar `SET LOCAL app.tenant_id = ...` y actor/trace.
4. Políticas usan `current_setting('app.tenant_id', true)` y default deny.
5. `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` y `FORCE ROW LEVEL SECURITY`; runtime role no tiene BYPASSRLS ni ownership.
6. QuerySets siguen filtrando tenant como defensa y para mensajes claros.

Workers repiten el mismo patrón desde el event envelope y limpian conexiones. Tests prueban cross-tenant select/insert/update/delete, joins, bulk paths, admin endpoints, tasks y raw SQL.

## Constraints e índices

- Unique: `(tenant_id, business_key)`; normative globals por `(standard_edition_id, clause_code)` y version/rule key.
- FK compuestas o triggers de constraint garantizan que relaciones tenant-scoped no crucen tenants.
- Check constraints para score/confidence [0,1 o 0,100], ventanas de vigencia, autonomy enum y estados.
- Índices comienzan por `tenant_id`; partial indexes para activos/pending/outbox unpublished; GIN solo para JSONB/FTS consultado.
- Evidence content hash + tamaño + media type; uniqueness definida por tenant/version sin colapsar historia legítima.

## Versionado y grafo

- StandardEdition y KnowledgeLayerRule son append-only luego de publicar.
- EvidenceCoverage referencia explícitamente edition, requirement control y rule version efectivas al crear evidencia.
- DocumentVersion es inmutable y apunta a object storage key/version/hash; Document conserva identidad/lifecycle.
- Graph edge tipado es una tabla relacional con constraints por tipo y vigencia. Crear vistas de traversal y materialized summaries solo con invalidación/eventos definidos.
- ImmutableAuditLog es append-only para la app; campos sensibles minimizados. Hash chain por stream/tenant y export WORM opcional permiten detectar manipulación, sin prometer inmutabilidad física solo por nombre.

## Migrations y backfill

Patrón expand/contract:

1. Crear tablas/columnas/índices concurrentes nullable y políticas en modo shadow.
2. Dual-read mediante adapters; dual-write transaccional/outbox solo si está instrumentado.
3. Backfill por lotes con checkpoint, métricas y reconciliación de conteos/hashes.
4. Activar constraints `NOT VALID`, validar, luego `NOT NULL`/RLS.
5. Cambiar reads por feature flag y observar.
6. Detener writes legados; conservar tablas/IDs durante ventana de rollback.
7. Deprecar/eliminar únicamente en release posterior con evidencia de cero uso y backup restaurable.

Rollback revierte flags/read path y detiene consumers; no destruye datos nuevos. Migrations de DDL deben tener reverse seguro o runbook explícito si PostgreSQL no lo permite.

## Mappings legados prioritarios

| Legado | Canónico | Tratamiento |
|---|---|---|
| core.Organization | TenantProjection + Organization | external_id es clave de reconciliación; no asumir equivalencia ciega |
| core/spm ProcessMap | Process/ProcessMap view | seleccionar owner y mapear IDs |
| core/sie StakeholderProfile | Stakeholder | dedupe por tenant/business key con cola de conflictos |
| core/planning QualityObjective | Objective | preservar source IDs y approvals |
| operations/improvement Nonconformity | Nonconformity | merge por provenance, nunca por título solamente |
| EvidenceNode/Edge | Evidence/typed relationships | migrar solo tipos mapeables; cuarentena para desconocidos |
| BillingSubscription/Payment | AdminApps projection | reconciliar; ISO Smart deja de confirmar cobros |

## Backup y recovery

- Backups cifrados, full + WAL/PITR, retención por ambiente/clasificación.
- Restore automático periódico a entorno aislado con checks de integridad, RLS y hashes de evidencia.
- RPO/RTO deben aprobarse antes de producción; no se inventan valores en discovery.
- Object storage y DB se restauran a un punto consistente mediante manifest/version ids.
