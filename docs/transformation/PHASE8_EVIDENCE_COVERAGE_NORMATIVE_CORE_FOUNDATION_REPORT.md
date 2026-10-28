# Phase 8 — Evidence Coverage + Normative Core Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 8 — EVIDENCE COVERAGE + NORMATIVE CORE FOUNDATION`

**PostgreSQL final:** 18.6 (`server_version_num=180006`)

**Run-id final:** `20260817T185810Z_5141a3`

**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó únicamente `foundation/0008_evidence_coverage_normative_core_foundation`. La migration es aditiva, reversible y condicionada a PostgreSQL mediante `SeparateDatabaseAndState`. Crea el schema global `normative`, cuatro tablas de catálogo, el ledger auxiliar `normative.curation_audit` y la tabla tenant-scoped `qms.evidence_coverage`.

| Migration | SHA-256 | Estado |
|---|---|---|
| `0001_foundation_tenant_projection` | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` | frozen/intacta |
| `0002_projection_organization_user_foundation` | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` | frozen/intacta |
| `0003_eventing_immutable_audit_foundation` | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` | frozen/intacta |
| `0004_qms_harmonized_context_foundation` | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` | frozen/intacta |
| `0005_risk_opportunity_objective_foundation` | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` | frozen/intacta |
| `0006_change_performance_measurement_foundation` | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` | frozen/intacta |
| `0007_document_evidence_foundation` | `c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec` | frozen/intacta |
| `0008_evidence_coverage_normative_core_foundation` | `285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032` | nueva |

PostgreSQL ejecutó `0001 → … → 0008 → 0007 → 0008`. Después de la reversa, Document/Evidence y sus commands siguieron funcionales; el segundo forward recreó exclusivamente Phase 8.

## 2. Source reconciliation

Se leyeron directamente los diez artefactos: DOCX, XLSX (11 hojas, incluida `DB_Entities`), JSON, DDL, OpenAPI, Mermaid, Draw.io, ambos CSV y LEEME. DDL/OpenAPI se trataron como referencias parciales, no como autoridad superior.

| SOURCE | ENTITY | FIELD / RELATION | SEMANTICS | IMPLEMENT? | RATIONALE |
|---|---|---|---|---:|---|
| XLSX/JSON `DB_Entities` | Standard | id, code, title, publisher | identidad normativa lógica | Sí | contrato estructurado coincidente |
| XLSX/JSON/DDL | StandardEdition | Standard, edition, status, effective dates, source hash | edición concreta/versionada | Sí | coincide con arquitectura de historia |
| DOCX/Event Catalog | StandardEdition | `standard.edition.published` | publicación material | Sí, como command/audit | DomainEvent global se difiere por tenancy actual |
| XLSX/JSON/DDL | Clause | edition, code, title, parent | cláusula edition-safe | Sí | estructura coincidente |
| DOCX/XLSX/JSON/DDL | RequirementControl | Clause, paraphrase, applicability rule, control type, validity | unidad normativa evaluable | Sí | separada de StakeholderRequirement |
| Data Architecture + prompt | RequirementControl | StandardEdition explícita | defensa de consistencia Edition/Clause/Control | Sí | FK compuesta evita combinaciones ambiguas |
| XLSX/JSON/DDL | EvidenceCoverage | Evidence, RequirementControl, confidence, validator/status/time | cobertura normativa | Sí | contrato coincidente; tenant/Organization se añaden por boundary aprobado |
| Phase 7 Evidence | EvidenceCoverage | fila Evidence exacta | revisión histórica exacta | Sí | cada Evidence row ya es una revisión inmutable |
| Data Architecture | EvidenceCoverage | StandardEdition congelada | historia normativa explícita | Sí | evita relación insuficiente sólo a Standard |
| DDL | EvidenceCoverage | unique Evidence + Requirement | assessment no ambiguo | Sí, ampliado por tenant/Organization | no colapsa tenants; repetir exige nueva Evidence revision |
| Mermaid/Draw.io | Coverage graph | RequirementControl `covered by` Evidence | Compliance Evidence Graph inicial | Sí, como relación tipada | no se crea edge genérica/traversal engine |
| OpenAPI | cláusula como filtro ilustrativo | operación pública | contrato incompleto | No | no autoriza endpoints Phase 8 |
| Nodes/Edges CSV | requisitos/capas | `INFORMS`, `CONTAINS`, etc. | Knowledge Layer graph | No | Phase 9; no contaminar normative core |

No se cargó texto ISO oficial, FDIS ni dataset normativo de producción. Los fixtures PostgreSQL se etiquetaron expresamente como sintéticos/no oficiales.

## 3. Catálogo global y modelos

`Standard`, `StandardEdition`, `Clause` y `RequirementControl` no tienen `tenant_id` ni RLS tenant. Son referencia global controlada mediante separación de privilegios.

- **Standard:** UUID, code único, title nullable y publisher. No mezcla edition, fechas ni cláusulas.
- **StandardEdition:** UUID, Standard, edition, status, `effective_from`, `effective_to` y SHA-256 `source_hash` nullable. Única por `(standard, edition)`.
- **Clause:** UUID, StandardEdition, code, title nullable y parent nullable. Única por `(edition, code)`.
- **RequirementControl:** UUID, StandardEdition explícita, Clause, paraphrase, applicability JSON, control type y ventana de validez. No es `StakeholderRequirement`.

Los únicos estados soportados son `draft` y `published`: la arquitectura aprueba draft mutable/published append-only y el catálogo fuente incluye el evento de publicación. No se inventó `superseded` ni un workflow editorial adicional.

## 4. Historia, jerarquía e inmutabilidad

Publicar es una transición atómica `draft → published`. El command bloquea la edition y exige al menos una Clause y un RequirementControl; un trigger repite esta precondición. Una excepción deliberada después de cambiar status y escribir curation audit revirtió ambos.

Una edition publicada rechaza UPDATE/DELETE de sus campos. Clause y RequirementControl rechazan INSERT/UPDATE/DELETE cuando su edition está publicada. Nueva edición implica nuevas filas; N nunca se convierte en N+1.

La jerarquía Clause usa FK compuesta `(standard_edition_id,parent_id)`, self-check y detector recursivo de ciclos. PostgreSQL rechazó parent cross-edition y ciclo `A → B → A`; pertenecer a una edition también impide parent de otro Standard.

La FK compuesta de RequirementControl a Clause exige que ambos declaren la misma StandardEdition. Coverage usa otra FK compuesta `(standard_edition_id,requirement_control_id)`.

## 5. Privilegios y normative curator

El gate creó `foundation_normative_curator_<runid>` como LOGIN real, non-superuser, `NOBYPASSRLS` y non-owner.

| Principal | Catálogo | Curation audit | Coverage/QMS |
|---|---|---|---|
| APP | SELECT | ninguno | Coverage SELECT/INSERT bajo RLS |
| WORKER | SELECT | ninguno | Coverage SELECT bajo RLS |
| PROJECTOR | SELECT | ninguno | ninguno |
| AUDIT WRITER | ninguno | ninguno | permisos Phase 3 existentes solamente |
| NORMATIVE CURATOR | SELECT/INSERT; UPDATE sólo columna Edition.status | SELECT/INSERT | cero DML QMS/Coverage |
| MIGRATOR | ownership técnico de la instancia efímera | DDL controlado | DDL controlado |

El curator no puede UPDATE code/title/edition/source metadata, DELETE catálogo, insertar material en published editions, mutar TenantProjection/Organization/Evidence ni registrar Coverage. Las escrituras materiales se exponen sólo mediante `create_standard`, `create_standard_edition`, `add_clause`, `add_requirement_control` y `publish_standard_edition`.

Cada command de curación crea en la misma transacción una entrada append-only de `normative.curation_audit` con actor, trace, action, entity y payload hash. No se reutilizó migrator como editor runtime.

## 6. EvidenceCoverage y duplicate semantics

`EvidenceCoverage` contiene UUID, tenant, Organization, Evidence exacta, StandardEdition exacta, RequirementControl exacto, confidence, validation status, validator, validation time y creation time. Es append-only: UPDATE/DELETE se deniegan por grants y trigger.

La clave lógica es `(tenant_id, organization_id, evidence_id, requirement_control_id)`. Como `evidence_id` identifica una revisión concreta, no se permiten dos assessments ambiguos del mismo control contra la misma revisión. Una reevaluación legítima usa una nueva revisión Evidence. Si un futuro source exige assessments repetidos sobre idéntica revisión, deberá introducir una identidad/version de assessment en `0009+`, no debilitar esta unique silenciosamente.

Defensas DB:

- Evidence usa FK compuesta tenant/Organization/id: Coverage A no puede adjuntar Evidence B.
- Organization y validator usan FKs compuestas con tenant.
- StandardEdition/RequirementControl usan FK compuesta para impedir Edition X + Control Y.
- Coverage sólo acepta una StandardEdition publicada/congelada.
- confidence está en `[0,1]`; validator y validated_at aparecen juntos o ambos nulos.

## 7. RLS, raw SQL, worker y pool

`qms.evidence_coverage` tiene `tenant_id NOT NULL`, `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY` y policies explícitas SELECT/INSERT/UPDATE/DELETE/ALL. Grants mantienen semántica append-only.

| Principal/contexto | Tenant A | none | Tenant B | Writes |
|---|---:|---:|---:|---|
| APP | 2 | 0 | 1 | INSERT sólo A propia |
| WORKER | 2 | 0 | 1 | ninguno |

SQL real rechazó Evidence B desde A, Organization mismatch, Edition/Control inconsistente, duplicate assessment, Coverage UPDATE/DELETE, published edits y runtime catalog writes. La conexión reutilizada verificó `A → commit → none → 0 → B → B only`; la ruta con exception/rollback produjo el mismo aislamiento.

## 8. Commands, eventos, atomicidad y audit

`record_evidence_coverage` ejecuta dentro de un único `trusted_tenant_context`/`transaction.atomic()`:

`EvidenceCoverage → DomainEvent → TransactionalOutbox → ImmutableAuditLog → commit`.

El único contrato tenant Phase 8 es `evidence_coverage.recorded`, schema version 1. El payload congela evidence ID, lineage, revision, StandardEdition, RequirementControl, confidence y validation metadata.

El caso exitoso comprobó las cuatro filas con tenant, trace y aggregate coherentes; la hash chain de audit fue válida. Una excepción después de Coverage/Event/Outbox/Audit y antes del commit dejó los cuatro conteos intactos.

Los eventos normativos globales no se emitieron. `DomainEvent` Phase 3 requiere `tenant_id NOT NULL`; no se usó tenant falso `global` ni se relajó silenciosamente la foundation. La curación queda auditada en el ledger global aislado. Una futura extensión de eventos platform deberá ser backward-compatible, allow-listed y diseñada expresamente.

## 9. Pruebas históricas

El gate creó Standard S, Edition 1/Clause/Control R1 y Coverage COV1 con Evidence revision 1. Después creó Edition 2/Control R2 y Evidence revision 2. COV1 siguió apuntando a Edition 1, R1 y Evidence revision 1; COV2 usó Edition 2, R2 y revision 2. No hubo UPDATE histórico.

También se probaron raw SQL published UPDATE de StandardEdition, Clause y RequirementControl, DELETE de edition publicada, inserción tardía de Clause, parent cross-edition y ciclos. Todos fueron rechazados.

## 10. Regresión, Django e integridad

| Gate | Resultado |
|---|---|
| Backend completo | **139 PASS / 0 FAIL / 0 SKIP** |
| Delta vs Phase 7 baseline 135 | **+4** contract tests Phase 8 |
| Foundation unit suite | **41 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL Phase 1–8 | PASS |
| Forward/reverse/forward | PASS |
| Publish rollback | PASS |

Warnings esperados de endpoints negativos, paginación y telemetría PostHog/Chroma no produjeron failures ni skips.

Los diez SHA-256 coinciden con el manifest: `8308bd…`, `e0a59c…`, `11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`, `eb4231…`: **10/10 MATCH**.

## 11. Teardown y límites

La corrida final eliminó database, seis LOGIN roles, container, volume y temp dir; las comprobaciones `container_absent`, `volume_absent` y `temp_absent` pasaron. No se usaron producción, staging, DB compartida, AdminApps DB, MedSupplier DB, broker ni deployment. No hubo cambios `.env`, secretos, repos externos ni source artifacts.

No se implementaron KnowledgeLayer, KnowledgeLayerRule, KnowledgeLayerBinding, StandardPack, Recommendation, RecommendationBasis, Agent runtime, AI analysis, traversal engine ni dataset normativo de producción.

## 12. Riesgos residuales

1. Falta la fuente normativa licenciada/FDIS completa; sólo existe schema y test data sintética no oficial.
2. La curation audit global es append-only para el curator y conserva payload hashes, pero todavía no tiene hash chain/WORM externa; migrator/DBA sigue siendo un trust boundary privilegiado.
3. No existen DomainEvents globales mientras el contrato tenant Phase 3 sea NOT NULL. Esta decisión evita un tenant falso, pero difiere el re-baseline asíncrono global.
4. APP conserva INSERT directo en Coverage para compatibilidad ORM. Constraints/RLS preservan boundary e historia; Event/Outbox/Audit dependen del command service, igual que las slices previas.
5. La unique conservadora no permite assessments repetidos sobre la misma Evidence revision/control; cualquier cambio necesita evidencia source-backed y nueva migration.
6. No hay endpoints/OpenAPI de producto para estas entidades. Deben incorporarse contract-first en una slice autorizada.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 13. Veredicto

**PHASE 8 — EVIDENCE COVERAGE + NORMATIVE CORE FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001–0007` | FROZEN / INTACTO | hashes promovidos exactos | evolucionar sólo 0009+ |
| `0008_evidence_coverage_normative_core_foundation` | PROMOTED | PostgreSQL forward/reverse/forward; hash `285aec…` | congelar tras promoción |
| Standard/Edition | PROMOTED | global, versioned, publish rollback e immutability PASS | licensed import futuro |
| Clause/RequirementControl | PROMOTED | edition-safe, hierarchy/FK/cycle tests PASS | Knowledge Layer bindings next |
| Runtime catalog | PASS | APP/WORKER/PROJECTOR SELECT-only | mantener privilege tests |
| Normative curator | PASS | real LOGIN, least privilege, non-owner | harden external curation approval later |
| EvidenceCoverage | PROMOTED | exact Evidence/Edition/Control; append-only | API futura |
| RLS/raw SQL | PASS | ENABLE+FORCE, A/none/B, cross-tenant defenses | repetir por nuevas tenant tables |
| Event/Outbox/Audit | PASS | success + rollback + chain | global event contract futuro |
| Backend/Django | PASS | 139/0/0; check/drift/compile | mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | preservar byte-for-byte |
| Recursos efímeros | REMOVED | teardown PASS | ninguna acción |

## NEXT_CODEX_PROMPT

Implementa PHASE 9 — KNOWLEDGE LAYER FOUNDATION de forma incremental, aditiva y reversible en `/home/felipe/proyectos/isosmart`, preservando byte-for-byte las migrations `0001–0008` y los diez source artifacts. Añade únicamente `0009+` para `KnowledgeLayer`, `KnowledgeLayerRule` y `KnowledgeLayerBinding`; modela una distinción explícita y comprobable entre `RequirementControl` certificable y guidance metodológica no certificable, conserva edition/rule versions y provenance, usa catálogo global con runtime read-only y normative curator least-privilege, protege published history en DB, evita texto normativo/licenciado inventado y usa sólo fixtures sintéticos identificados como no oficiales. Extiende commands, curation audit, PostgreSQL 18.6 harness, raw SQL, privilege tests, forward/reverse/forward, full backend regression, Django check/drift/compile, source hashes y teardown. No implementes todavía StandardPack, Recommendation, RecommendationBasis, Agent runtime, AI analysis, Human Decision Gate completo, traversal engine, production data, broker ni deployment. Entrega `docs/transformation/PHASE9_KNOWLEDGE_LAYER_FOUNDATION_REPORT.md`, veredicto PROMOTED/NOT PROMOTED y exactamente un siguiente prompt autocontenido.
