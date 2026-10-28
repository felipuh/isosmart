# Phase 7 — Document + Document Version + Evidence Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 7 — EVIDENCE + DOCUMENT FOUNDATION`

**PostgreSQL run-id final:** `20260817T183319Z_323963`
**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó únicamente `foundation/0007_document_evidence_foundation`. Es aditiva, reversible y condiciona el DDL a PostgreSQL mediante `SeparateDatabaseAndState`. Crea `qms.document`, `qms.document_version` y `qms.evidence`; no crea EvidenceCoverage ni catálogo normativo.

| Migration | SHA-256 | Estado |
|---|---|---|
| `0001_foundation_tenant_projection` | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` | frozen/intacta |
| `0002_projection_organization_user_foundation` | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` | frozen/intacta |
| `0003_eventing_immutable_audit_foundation` | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` | frozen/intacta |
| `0004_qms_harmonized_context_foundation` | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` | frozen/intacta |
| `0005_risk_opportunity_objective_foundation` | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` | frozen/intacta |
| `0006_change_performance_measurement_foundation` | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` | frozen/intacta |
| `0007_document_evidence_foundation` | `c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec` | nueva |

PostgreSQL verificó `0001 → … → 0007 → 0006 → 0007`. La reversa eliminó exclusivamente las tres tablas y cinco funciones Phase 7; `Change` y `MeasurementDefinition` permanecieron funcionales.

## 2. Source reconciliation

Se leyeron directamente DOCX, XLSX (`DB_Entities`, `Event_Catalog`, mapas), JSON, DDL, OpenAPI, Mermaid, Draw.io y CSV relevantes, además de los diseños/ADRs aprobados.

| SOURCE | ENTITY | FIELD/RELATION | SEMANTICS | IMPLEMENT? | RATIONALE |
|---|---|---|---|---:|---|
| XLSX/JSON `DB_Entities` | Document | `document_id`, `tenant_id`, `doc_type`, `current_version_id`, `owner_id` | identidad lógica y versión vigente | Sí | contrato estructurado coincidente |
| Data Architecture/Tenant model | Document | Organization directa, timestamps | boundary QMS e historia operacional | Sí | control aprobado para todo tenant domain object |
| XLSX/JSON `DB_Entities` | DocumentVersion | id, Document, version, content hash, approver, effective time | versión material concreta | Sí | contrato estructurado coincidente |
| Data Architecture | DocumentVersion | object-storage content reference | boundary de contenido externo | Sí, referencia abstracta | no introduce storage productivo ni secretos |
| Phase 7/history architecture | DocumentVersion | predecessor lineal | reconstrucción y current leaf | Sí | `current_version_id` fuente exige una sucesión no ambigua; branching no aparece en fuentes |
| DDL/XLSX/JSON | Evidence | id, tenant, source type/URI, content hash, captured time, trust score | evidencia canónica y provenance | Sí | mismos campos en las tres fuentes estructuradas |
| Data Architecture | Evidence | append/supersede | conservar cambio material sin overwrite | Sí | mutabilidad aprobada explícitamente |
| Ingestion/provenance design | Evidence | exact DocumentVersion | evidencia originada en versión documental | Sí, nullable | preserva fuente/hash exactos; FK tipada, no UUID genérico |
| Evidence Graph artifacts | EvidenceCoverage/Requirement | cobertura normativa | cobertura futura | No | fuera de alcance; requiere normative core congelado |
| Requirement cards/graph | Evidence→Process/Risk/etc. | menciones funcionales de grafo | contexto/cobertura, no FK de instancia | No | no se inventan relaciones bilaterales sin campos canónicos |

No se agregaron title/name, lifecycle/status, MIME, tamaño, hash algorithm column, metadata JSON, originating-system field ni actor duplicado porque no tienen contrato de entidad suficiente. Actor, trace y origen del command quedan en event/audit.

## 3. Document logical identity

`Document` contiene UUID, tenant, Organization, `doc_type`, owner nullable, `current_version_id` nullable y timestamps. No contiene bytes ni content hash. La creación precede a la primera versión; el puntero se establece atómicamente al crearla. `revise_document_metadata` permite únicamente `doc_type` y owner.

Tenant y Organization son inmutables por trigger. Las FKs compuestas protegen Organization, owner y current version. El current pointer sólo puede avanzar a un sucesor directo; no puede retroceder, saltar o apuntar a otro Document/tenant/Organization.

## 4. DocumentVersion, hashing y storage boundary

`DocumentVersion` contiene UUID, tenant, Organization, Document, version identifier, predecessor nullable, `content_reference`, SHA-256 `content_hash`, approver nullable, effective time nullable y created time. Version identity es única por Document. Una unique sobre predecessor impide forks; la primera versión exige predecessor nulo y toda versión posterior exige predecessor existente del mismo Document/boundary.

UPDATE y DELETE de una versión existente son rechazados por trigger incluso para SQL del migrator; runtime recibe sólo SELECT/INSERT. Esto protege tenant, Organization, parent, version, predecessor, reference y hash contra sustitución in-place. Self predecessor, cycles, cross-document, cross-tenant y cross-Organization fallan por checks/FKs/orden append-only.

`create_document_version` exige `bytes`, calcula SHA-256 sobre los octetos exactos sin decodificar, normalizar texto ni canonicalizar JSON, persiste el digest y no guarda el blob. El fixture `b"ISO Smart Phase 7 fixture\x00vN\n"` fue recalculado para v1/v2/v3 y coincidió. Content hash, audit entry hash y DomainEvent payload hash usan dominios y propósitos separados.

`content_reference` es un identificador abstracto respaldado por el diseño object-storage key/version/hash. Phase 7 no valida existencia remota ni implementa S3/MinIO. Boundary futuro: `DocumentVersion → content_reference → object storage`; no hay secrets ni blobs grandes en PostgreSQL.

## 5. Version lineage e historia

El gate creó Document D con `v1 → v2 → v3`. Las tres versiones y hashes permanecieron, los predecessors fueron `NULL → v1 → v2` y `Document.current_version_id=v3`. Cuatro eventos del aggregate Document (`document.created` y tres `document.version_created`) y la chain audit completa fueron verificados. Intentos de cambiar hash/reference, retroceder current, usar predecessor B o parent B fueron rechazados.

La decisión es lineage lineal: las fuentes publican `current_version_id` singular y no describen branching. Concurrencia por command toma lock del Document; las uniques de version y predecessor mantienen un solo ganador incluso ante insert SQL concurrente.

## 6. Evidence model, provenance y revision strategy

`Evidence` es un único objeto empresarial, no se duplica por norma. Cada fila es una revisión append-only con UUID, tenant, Organization, lineage, revision, predecessor, source type, source URI nullable, content hash, captured time, trust score `[0,1]` nullable, DocumentVersion nullable, reason y created time.

La estrategia seleccionada es identidad lógica + supersession lineal: `E v1 → v2 → v3`. Las tres revisiones se conservaron, current leaf fue único, no hubo fork/cycle y UPDATE/DELETE fueron rechazados. `create_evidence` y `supersede_evidence` son los únicos commands materiales expuestos; no se implementó retire porque las fuentes no definen lifecycle de Evidence.

Cuando la fuente es documental, Evidence referencia la DocumentVersion exacta. El command hereda su `content_reference` como source URI si no se suministra uno y su `content_hash`; un trigger exige igualdad del hash. Así se reconstruyó Evidence → DocumentVersion exacta → hash → reference/source type → captured time → tenant/Organization → trace → DomainEvent → audit. El Evidence hash prueba igualdad con el contenido identificado por su source; no prueba disponibilidad del objeto ni autenticidad externa por sí solo.

## 7. Evidence relations y Evidence Graph boundary

Se implementó únicamente `Evidence.document_version_id`, tipada y tenant/Organization-safe. Se difirieron Process, Risk, Opportunity, Objective, Change, StakeholderRequirement, ContextItem y toda cobertura normativa: las fichas funcionales los muestran en el futuro Compliance Evidence Graph pero `DB_Entities` no define FKs de instancia.

No existe edge genérica, traversal CTE, EvidenceCoverage, Standard, Edition, Clause, RequirementControl, KnowledgeLayer ni Recommendation. La FK tipada actual es compatible con el futuro grafo sin permitir UUIDs arbitrarios.

## 8. RLS, constraints y principals

Las tres tablas tienen `tenant_id NOT NULL`, `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY` y cinco policies cada una: SELECT/INSERT/UPDATE/DELETE explícitas y ALL migrator. Policies no amplían grants.

| Tabla | App A / none / B | Worker A / none / B | App grants |
|---|---:|---:|---|
| Document | `1 / 0 / 1` | `1 / 0 / 1` | SELECT, INSERT, UPDATE |
| DocumentVersion | `3 / 0 / 1` | `3 / 0 / 1` | SELECT, INSERT |
| Evidence | `3 / 0 / 1` | `3 / 0 / 1` | SELECT, INSERT |

Los cinco LOGIN efímeros (migrator, app, worker, projector, audit writer) fueron non-superuser, `NOBYPASSRLS` y non-owner. Worker es read-only Phase 7; por tanto no existe captura worker ni selección arbitraria de tenant. Projector y audit writer tienen cero permisos business Phase 7.

Composite FKs o triggers rechazaron Document→Organization B, Version→Document B, predecessor B, Evidence→DocumentVersion B, Evidence/hash mismatch, tenant reassignment y Organization reassignment independientemente de RLS.

## 9. Commands, events, atomicidad y audit

Commands explícitos: `create_document`, `revise_document_metadata`, `create_document_version`, `create_evidence`, `supersede_evidence`. No existe update de DocumentVersion, generic Evidence writer ni event/audit injection.

Eventos schema v1: `document.created`, `document.metadata_revised`, `document.version_created`, `evidence.created`, `evidence.superseded`. Payloads usan canonical JSON v1 y payload hash; envelopes conservan tenant, trace, aggregate identity/version y source.

Cada command abre un único `trusted_tenant_context`/`transaction.atomic()`: business mutation → DomainEvent → TransactionalOutbox → ImmutableAuditLog → commit. Éxito fue probado para Document, DocumentVersion y Evidence con tenant/trace/aggregate coherentes. Fallos inyectados después de audit y antes de commit para DocumentVersion y Evidence supersession dejaron cero business row/event/outbox/audit parcial; current Document tampoco avanzó.

Las audit chains Document y Evidence verificaron sequence, previous entry hash, payload hash y entry hash. Los controles promovidos continúan rechazando UPDATE/DELETE/TRUNCATE/forge runtime.

## 10. Raw SQL, worker, pool y rollback

SQL directo probó aislamiento A/B/none, wrong-tenant Organization/Document/predecessor/provenance, mismatch de hash, sustitución de hash/reference, reasignación boundary, retroceso current y DELETE histórico. Todos fueron rechazados según semántica.

Worker obtuvo A only, none zero y B only en las tres tablas; no recibió writes. La misma conexión ejecutó `A → commit → none → zero → B → B only`. Otra ejecutó `A → exception → rollback → none → zero → B → B only`.

## 11. PostgreSQL, regresión, Django e integridad

Corrida final: PostgreSQL `18.6`, `server_version_num=180006`, imagen oficial, endpoint efímero `127.0.0.1:35097`, run-id `20260817T183319Z_323963`.

| Gate | Resultado |
|---|---|
| Backend completo | **135 PASS / 0 FAIL / 0 SKIP** |
| Delta vs baseline Phase 6 (130) | **+5** contract tests Phase 7 |
| Foundation unit suite | **37 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation (backend, excluyendo virtualenvs) | PASS |
| PostgreSQL Phase 1–7 | PASS |
| Forward/reverse/forward | PASS |

Warnings esperados de endpoints negativos, paginación y telemetría Chroma/PostHog no produjeron failures ni skips. La invocación de regression enumeró explícitamente apps instaladas porque `manage.py test` sin labels devuelve cero en este layout.

Los diez SHA-256 source fueron recalculados: `8308bd…`, `e0a59c…`, `11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`, `eb4231…`: **10/10 MATCH**. Ningún source artifact fue modificado.

## 12. Teardown y final verification

Database y cinco roles fueron eliminados; container, volume y temp dir quedaron ausentes. No se usaron producción, staging, DB compartida, AdminApps DB ni MedSupplier DB. No hubo deployment, cambios `.env`, secretos, broker, object storage ni repos externos.

`git status` conserva los cambios locales preexistentes. `git diff --check` reporta únicamente whitespace preexistente en `frontend/src/components/Layout/Sidebar.jsx:28`, ya presente en el estado de entrada y fuera de Phase 7; los archivos Phase 7 no agregan errores whitespace. 0001–0006 y los diez source artifacts conservan sus hashes promovidos.

## 13. Riesgos residuales

1. `content_reference` no verifica existencia, disponibilidad, firma ni retención del objeto; eso pertenece a la integración futura de storage.
2. La foundation interna aún no expone endpoints/OpenAPI/permissions de producto. Deben añadirse contract-first en una slice autorizada.
3. Runtime app conserva INSERT directo requerido por ORM; la atomicidad material está encapsulada por command service, pero un SQL runtime comprometido podría intentar bypass del service. Constraints preservan historia/boundary; un hardening futuro puede usar funciones DB estrechas si el threat model eleva este riesgo.
4. `Document` metadata es mutable y app tiene UPDATE; current pointer está protegido por sucesión DB, pero la disciplina event/audit depende del command boundary.
5. Audit es tamper-evident/append-only para runtime, no indestructible ante DBA; checkpoints WORM siguen pendientes.
6. No hay MIME/tamaño porque los source contracts no los definen para DocumentVersion en esta slice. Añadirlos requiere reconciliación explícita.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 14. Veredicto

**PHASE 7 — EVIDENCE + DOCUMENT FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001–0006` | FROZEN / INTACTO | hashes promovidos exactos | Evolucionar sólo 0008+ |
| `0007_document_evidence_foundation` | PROMOTED | PostgreSQL forward/reverse/forward; hash `c7f6a2…` | Congelar tras promoción |
| Document | PROMOTED | logical identity, current successor guard, atomic commands | API futura |
| DocumentVersion | PROMOTED | v1→v2→v3, exact-byte SHA-256, overwrite/delete rejected | Storage integration futura |
| Evidence | PROMOTED | v1→v2→v3, structured provenance, exact version/hash | EvidenceCoverage next |
| Evidence relationships | SOURCE-BOUNDED | sólo DocumentVersion FK tipada | Normative coverage en Phase 8 |
| RLS/principals | PASS | 3 tables, 15 policies, A/B/none, worker/projector | Repetir por nuevas tablas |
| Event/Outbox/Audit | PASS | success + rollback + chains | Transport futuro |
| Backend/Django | PASS | 135/0/0; check/drift/compile | Mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | Preservar byte-for-byte |
| Recursos efímeros | REMOVED | teardown PASS | Ninguna acción |
