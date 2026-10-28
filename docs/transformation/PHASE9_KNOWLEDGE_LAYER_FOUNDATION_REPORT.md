# Phase 9 — Knowledge Layer Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 9 — KNOWLEDGE LAYER FOUNDATION`

**PostgreSQL final:** 18.6 (`server_version_num=180006`)

**Run-id final:** `20260817T204611Z_340d49`
**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó únicamente `foundation/0009_knowledge_layer_foundation`. Es aditiva,
reversible y condicionada a PostgreSQL mediante `SeparateDatabaseAndState`.
Crea tres tablas globales, una vista de clasificación explícita, constraints,
índices, guards de publicación y grants. No crea tablas tenant, RLS artificial,
eventos globales, recommendations ni runtime IA.

| Migration | SHA-256 | Estado |
|---|---|---|
| `0001_foundation_tenant_projection` | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` | frozen/intacta |
| `0002_projection_organization_user_foundation` | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` | frozen/intacta |
| `0003_eventing_immutable_audit_foundation` | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` | frozen/intacta |
| `0004_qms_harmonized_context_foundation` | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` | frozen/intacta |
| `0005_risk_opportunity_objective_foundation` | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` | frozen/intacta |
| `0006_change_performance_measurement_foundation` | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` | frozen/intacta |
| `0007_document_evidence_foundation` | `c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec` | frozen/intacta |
| `0008_evidence_coverage_normative_core_foundation` | `285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032` | frozen/intacta |
| `0009_knowledge_layer_foundation` | `412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc` | nueva/promovida |

La secuencia real fue `0001 → … → 0009 → 0008 → 0009`. Durante la reversa,
Standard/Edition/Clause/RequirementControl, EvidenceCoverage y el command de
curación Phase 8 siguieron disponibles.

## 2. Source reconciliation gate

Se leyeron directamente los diez artefactos, incluidos XML interno del DOCX,
las once hojas XLSX, JSON completo, DDL, OpenAPI, Mermaid, Draw.io, ambos CSV y
LEEME. El DDL parcial no se elevó sobre DOCX/XLSX/JSON ni sobre las relaciones
canónicas CSV.

| SOURCE | ENTITY | FIELD / RELATION | SEMANTICS | IMPLEMENT? | RATIONALE |
|---|---|---|---|---:|---|
| DOCX | Knowledge Layer | normas complementarias metodológicas | enriquece el core; no es requisito certificable | Sí | principio funcional primario |
| DOCX | ISO/DIS 9002 | guía de aplicación; no añade requisitos | guidance explícita | Sí, como semántica; sin contenido oficial | evidencia negativa de certificabilidad |
| DOCX/XLSX/JSON | ISO 9000/9004/19011/31000 | fundamentos, desempeño, auditoría y riesgo | capas Quality Intelligence | Sí, schema genérico | no se cargó dataset normativo |
| DOCX/XLSX/JSON | ISO/IEC 42001 y capas IA | `AI Governance Core` | guidance/gobierno aplicable al core | Sí, `layer_type` abierto source-backed | no se implementó runtime IA |
| XLSX/JSON `DB_Entities` | KnowledgeLayer | id, StandardEdition, layer type, certifiability metadata | identidad global de capa | Sí | exact edition provenance; clasificación no ambigua |
| XLSX/JSON/DDL | KnowledgeLayerRule | layer, rule key, version, logic JSON, evidence expectation | unidad versionada de metodología | Sí | sin duplicar RequirementControl |
| Data Architecture | KnowledgeLayerRule | published append-only | historia normativa reconstruible | Sí | `draft/published`; no se inventó `superseded` |
| Prompt + source architecture | KnowledgeLayerRule | source/version/reference/publication | provenance explicable | Sí | edition/hash vía Layer + source reference + timestamps |
| XLSX/JSON/DDL | KnowledgeLayerBinding | RequirementControl, Rule, priority, rationale | relación guidance-control | Sí | referencias exactas, no nombres ambiguos |
| CSV/XLSX Graph Edges | Binding | `INFORMS` | guidance informa a un requirement | Sí | único relationship type implementado |
| XLSX `Knowledge_Bindings` | Binding | cláusulas, prioridad, propósito | applicability catalogal | Parcial | priority/rationale; listas masivas y contenido quedan fuera |
| CSV/JSON graph | Layer→Requirement | 488 `INFORMS` | mapa de aplicabilidad | Schema sí; datos no | no importar contenido/licencia de producción |
| DDL | KnowledgeLayer | `certifiable_if_pack_active` boolean | señal parcial/ambigua | No literal | StandardPack está fuera; Rule nunca se vuelve requisito |
| DDL | Binding uniqueness | exact Rule + exact Requirement | evita duplicado ambiguo | Sí, ampliado con relationship type | permite futuros tipos sólo mediante migration reconciliada |
| DDL/Data Architecture | historia | no destructive UPDATE de Rule; bindings nuevos | preserve prior versions | Sí | triggers, predecessor y exact FK |
| Mermaid/Draw.io | Quality/AI layers→Core | alimenta/gobierna | capas separadas del core | Sí conceptualmente | no traversal engine |
| OpenAPI | Recommendation basis drawer | explicación futura | consumidor futuro | No | API/UI/Recommendation fuera de scope |
| LEEME | Knowledge Layers | invisibles por defecto, explicables | futura presentación | Documentado | UI no implementada |

## 3. KnowledgeLayer

`normative.knowledge_layer` es global y no contiene `tenant_id`. Sus campos son
UUID, `standard_edition_id` exacta, `layer_type`, clasificación fija
`non_certifiable_guidance` y `created_at`. Una unique por StandardEdition evita
identidades paralelas ambiguas. La identidad es append-only; cualquier
UPDATE/DELETE es rechazado por trigger, incluso para el curator.

La edition exacta conserva provenance hacia Standard, edition, fechas y
`source_hash`. Nueva edición necesita una nueva identidad de Layer; no existe
re-point silencioso.

## 4. KnowledgeLayerRule, versionado y provenance

Cada fila es una revisión exacta con UUID, Layer, `lineage_id`, `rule_key`,
`version`, predecessor exacto, `logic_json`, `evidence_expectation`,
`source_reference`, estado, clasificación fija, `created_at` y `published_at`.

Defensas de historia:

- un único root por `(knowledge_layer_id, rule_key)`;
- root exige `lineage_id=id`;
- predecessor único impide forks;
- FK compuesta exige mismo Layer y `rule_key`;
- trigger exige predecessor publicado y mismo lineage;
- self-reference/cycle y cambio destructivo son rechazados;
- unique `(lineage_id, version)` y `(Layer, rule_key, version)`;
- current revision se deriva como leaf publicada sin successor.

La provenance reconstruible es `Rule revision → KnowledgeLayer → exact
StandardEdition → Standard/source_hash`, más `source_reference`, rule key,
version y timestamps. No se almacenó texto ISO oficial.

## 5. Publicación e inmutabilidad

Los únicos estados source-backed son `draft` y `published`. Publicación es una
transición atómica `draft → published`; exige source edition publicada. Una
Rule publicada rechaza UPDATE/DELETE de contenido, parent, lineage, identity,
version y estado. Nueva guidance usa `revise_knowledge_layer_rule`.

El gate inyectó fallos antes del commit para Rule y Binding: status y entrada
de curation audit quedaron intactos. No se incorporó un estado `superseded` no
definido; v1/v2 continúan publicadas y la leaf v3 es current.

## 6. KnowledgeLayerBinding y semántica

`normative.knowledge_layer_binding` contiene UUID, Rule revision exacta,
StandardEdition objetivo exacta, RequirementControl exacto, relationship type,
priority, rationale, estado, `semantic_effect` y timestamps. La FK compuesta
`(standard_edition_id, requirement_control_id)` impide edition/control mismatch.

Sólo se admite el tipo source-backed `informs`. `semantic_effect` tiene CHECK
fijo `guidance_only`. La clave lógica es `(knowledge_layer_rule_id,
requirement_control_id, relationship_type)`: elimina duplicados del mismo
binding y deja abierta una futura relación distinta sólo mediante nueva
reconciliación/migration.

Crear un binding exige Rule exacta publicada y edition objetivo publicada. Una
vez publicado, no puede re-point a otra Rule, RequirementControl o edition, ni
alterar priority/rationale, ni borrarse.

## 7. Invariante certifiable vs guidance

La distinción no depende de naming:

| Object | Classification | Certifiable customer requirement? | Future presentation |
|---|---|---:|---|
| RequirementControl | `normative_requirement` | YES | `Requirement` |
| KnowledgeLayer | `non_certifiable_guidance` | NO | `Knowledge Layer` |
| KnowledgeLayerRule | `non_certifiable_guidance` | NO | `Guidance` |
| KnowledgeLayerBinding | `semantic_effect=guidance_only` | NO transformation | relationship only |

La vista global `normative.catalog_object_classification` expone la distinción
en schema. `KnowledgeCatalogQueryService.certifiable_requirements()` consulta
exclusivamente RequirementControl. Los modelos y el contract de serialización
futura entregan `is_certifiable_customer_requirement` y presentation kind.

Agregar Layer, tres Rule revisions y bindings no cambió el count certificable.
`qms.evidence_coverage` conserva exclusivamente su FK tipada a
RequirementControl; no tiene FK/columna a Rule o Binding.

## 8. Resultados históricos

Rule sintética `v1 → v2 → v3`:

- tres filas retenidas y publicadas;
- predecessors `NULL → v1 → v2`;
- un solo lineage y v3 como leaf/current;
- source references v1/v2/v3 retenidas;
- self-reference, cycle por re-point y destructive overwrite rechazados.

Binding B1 se publicó con `Rule v1 + Edition1/RC1`. Después de publicar v2 y
v3, B1 siguió resolviendo v1. B2 fue creado explícitamente para v2. Tras crear
Edition2/RC2, B1 siguió en Edition1/RC1/v1 y B3 se creó explícitamente para
Edition2/RC2/v3. No hubo UPDATE histórico.

## 9. Privilegios runtime y curator

| Principal | Layer | Rule | Binding | Classification view | QMS writes |
|---|---|---|---|---|---:|
| APP | SELECT | SELECT | SELECT | SELECT | Phase 9: 0 |
| WORKER | SELECT | SELECT | SELECT | SELECT | Phase 9: 0 |
| PROJECTOR | SELECT | SELECT | SELECT | SELECT | 0 |
| AUDIT WRITER | none | none | none | none | sólo foundation Phase 3 |
| NORMATIVE CURATOR | SELECT/INSERT | SELECT/INSERT + UPDATE status/published_at | igual | SELECT | 0 |

El curator fue LOGIN real, non-superuser, `NOBYPASSRLS`, non-owner. No puede
UPDATE campos materiales, DELETE catálogo, tocar TenantProjection,
Organization, Risk, Evidence o EvidenceCoverage, ni saltar triggers de
publicación. KnowledgeLayer tampoco admite UPDATE.

Commands materiales: `create_knowledge_layer`,
`create_knowledge_layer_rule`, `revise_knowledge_layer_rule`,
`publish_knowledge_layer_rule`, `create_knowledge_layer_binding` y
`publish_knowledge_layer_binding`. No existe generic save material.

## 10. Curation audit y eventos globales

Cada command exitoso agrega en la misma transacción una entrada a
`normative.curation_audit` con actor, trace, acción, entidad y payload hash. Se
reutilizó el ledger append-only promovido en Phase 8; no se forzó
ImmutableAuditLog tenant-scoped con tenant falso.

Se mantiene la decisión Phase 8: no DomainEvent global. DomainEvent Phase 3
requiere tenant real; Phase 9 no cambia `0003`, no usa `GLOBAL` ni UUID fake.
Eventos platform quedan para una foundation backward-compatible específica.

## 11. PostgreSQL/raw SQL/forward-reverse

Gate final en PostgreSQL 18.6 oficial:

- runtime SELECT y DML deny para las tres tablas;
- curator least privilege con LOGIN real;
- Rule material UPDATE/DELETE publicado: rechazado;
- cambio de Layer parent, version, predecessor: rechazado;
- Binding Rule/Requirement/edition re-point y DELETE: rechazado;
- nonexistent/draft Rule, nonexistent/mismatched RequirementControl: rechazado;
- duplicate binding: rechazado;
- publication rollback Rule/Binding: cero estado/audit parcial;
- `0001 → … → 0009 → 0008 → 0009`: PASS;
- Phase 8 command tras reversa: PASS.

## 12. Regresión e integridad Django

| Gate | Resultado |
|---|---|
| Backend completo | **144 PASS / 0 FAIL / 0 SKIP** |
| Delta vs Phase 8 baseline 139 | **+5** contract tests Phase 9 |
| Foundation unit suite | **46 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL Phase 1–9 | PASS |
| Forward/reverse/forward | PASS |
| Raw SQL/history/privileges | PASS |

Los warnings 400/401/403/404/405, pagination y telemetría PostHog/Chroma ya
esperados no produjeron failures ni skips.

## 13. Source integrity, licensing y teardown

Los diez SHA-256 coinciden con el manifest: `8308bd…`, `e0a59c…`, `11c2b4…`,
`952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`,
`eb4231…`: **10/10 MATCH**.

Todos los fixtures dicen `NON-OFFICIAL TEST FIXTURE`; no se cargó texto ISO,
FDIS, producción ni material que aparente ser oficial/licenciado.

El finalizer eliminó database, seis LOGIN roles, container, volume y temp dir.
`container_absent`, `volume_absent` y `temp_absent`: PASS. No se usaron
producción, staging, DB compartida, AdminApps DB, MedSupplier DB, broker,
deployment, secretos ni `.env`.

`git diff --check` sólo reporta el trailing whitespace preexistente en
`frontend/src/components/Layout/Sidebar.jsx:28`, fuera de Phase 9. Los archivos
Phase 9 no agregan errores whitespace.

## 14. Contrato UI/API futuro

Una UI/API futura debe presentar RequirementControl como `Requirement`, Rule
como `Guidance` y Layer como `Knowledge Layer`. El futuro Normative
Intelligence Drawer podrá reconstruir requirement evaluado, layers aplicadas,
Rule version y source/provenance; Phase 9 no implementa Drawer,
Recommendation, Evidence basis ni inferencia.

## 15. Riesgos residuales

1. El ledger global es append-only para curator pero aún no tiene hash chain o
   WORM externo; migrator/DBA continúa como trust boundary.
2. Sólo `informs` está reconciliado. Nuevos relationship types, applicability
   conditions o priorities tipadas requieren source y migration explícitos.
3. Layer se identifica por exact StandardEdition y una edition admite un Layer;
   otra granularidad necesitará evidencia fuente y evolución aditiva.
4. `logic_json`/`evidence_expectation` tienen boundary JSON object en service,
   pero no existe aún schema de regla determinista/versionado por tipo.
5. No existen API/UI ni importador licenciado. El contenido de producción sigue
   bloqueado hasta fuente controlada.
6. No existe evento global asíncrono; curation ledger es el mecanismo vigente.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 16. Veredicto

**PHASE 9 — KNOWLEDGE LAYER FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001–0008` | FROZEN / INTACTO | hashes promovidos exactos | evolucionar sólo 0010+ |
| `0009_knowledge_layer_foundation` | PROMOTED | PostgreSQL 18.6 forward/reverse/forward; raw SQL PASS | congelar tras promoción |
| KnowledgeLayer | PROMOTED | global, exact edition, append-only | contenido licenciado futuro |
| KnowledgeLayerRule | PROMOTED | v1→v2→v3, provenance, published immutable | rule schema determinista futuro |
| KnowledgeLayerBinding | PROMOTED | exact Rule + exact Edition/Control; B1 history PASS | nuevos tipos sólo source-backed |
| Certifiability invariant | PASS | classification view + query/service/tests | mantener en serializers/API |
| Runtime catalog | PASS | APP/WORKER/PROJECTOR SELECT-only | repetir privilege tests |
| Normative curator | PASS | LOGIN least privilege/non-owner | aprobación externa futura |
| Global curation audit | PASS | atomic ledger + rollback tests | hash chain/WORM futuro |
| Global DomainEvent | DEFERRED | no fake tenant; 0003 intacta | diseñar foundation platform event |
| Backend/Django | PASS | 144/0/0; check/drift/compile | mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | preservar byte-for-byte |
| Recursos efímeros | REMOVED | finalizer/teardown PASS | ninguna acción |
