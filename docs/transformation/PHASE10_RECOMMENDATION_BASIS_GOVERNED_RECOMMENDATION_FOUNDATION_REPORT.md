# Phase 10 — Recommendation Basis + Governed Recommendation Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 10 — RECOMMENDATION BASIS + GOVERNED RECOMMENDATION FOUNDATION`

**Veredicto provisional:** **NOT PROMOTED** hasta completar todos los gates.

## Source reconciliation gate

Se leyeron directamente DOCX (XML interno), las hojas XLSX, JSON, DDL,
OpenAPI, Mermaid, Draw.io, ambos CSV y LEEME. El DOCX es autoridad funcional;
XLSX/JSON son autoridad estructurada y el DDL/OpenAPI son referencias parciales.

| SOURCE | ENTITY | FIELD / RELATION | SEMANTICS | IMPLEMENT? | RATIONALE |
|---|---|---|---|---:|---|
| DOCX | Recommendation | resultado/recomendación explicable | propuesta visible en lenguaje de negocio | Sí | salida canónica del paso RECOMENDAR; no equivale a ejecución |
| XLSX/JSON/DDL | Recommendation | UUID, tenant, title, body, confidence, impact, status | registro tenant de recomendación | Sí | contrato estructurado coincidente |
| DDL | Recommendation | `agent_run_id` | origen runtime | No en Phase 10 | AgentRun es una slice posterior; no se crea FK falsa |
| Data Architecture | Recommendation | Organization y tenant boundary | pertenencia inequívoca al QMS | Sí | control tenant/Organization aprobado para objetos tenant |
| Data Architecture | Recommendation | body immutable/history | cambios materiales preservan historia | Sí | fila completa append-only; cambio material crea nueva Recommendation |
| DDL | Recommendation | status=`proposed` | lifecycle mínimo conocido | Sí | único valor concreto source-backed; no se inventan estados de Approval |
| DOCX/DDL | confidence | `numeric(5,4)`, nivel visible | indicador normalizado, no probabilidad estadística | Sí | misma representación que Coverage; `[0,1]` fuerte y semántica explícita |
| DOCX | assumptions | confianza, supuestos y límites visibles | supuestos activos reconstruibles | Sí | snapshot JSON estructurado y validado como lista no vacía de textos |
| XLSX/JSON/DDL | RecommendationBasis | UUID, Recommendation, RequirementControl, Rule, Evidence, rationale | fundamento explicable | Sí | relación source-backed directa |
| Data Architecture | RecommendationBasis | tenant directo | provenance tenant-safe | Sí | corrige la omisión parcial del DDL |
| Data Architecture | RecommendationBasis | frozen/append-only | no reinterpretar historia | Sí | exact FKs + guard UPDATE/DELETE |
| Phase 8 + source DDL | Basis→RequirementControl | Requirement exacto | unidad normativa evaluada | Sí | no se sustituye por guidance |
| Data Architecture | Basis→StandardEdition | edition congelada | consistencia normativa histórica | Sí | FK compuesta impide RC/Edition mismatch |
| DOCX/XLSX/JSON/DDL | Basis→KnowledgeLayerRule | Rule/version aplicada | revisión exacta de guidance | Sí | sólo Rule publicada; no current pointer |
| DOCX/XLSX/JSON/DDL | Basis→Evidence | Evidence usada | revisión tenant exacta | Sí | cada fila Evidence Phase 7 es una revisión inmutable |
| DDL/JSON | Basis→EvidenceCoverage | no aparece | Coverage es assessment Evidence→RC | No | Basis fuente referencia Evidence directamente; no se duplica Coverage |
| DOCX/DDL | model/rule metadata | provider/name/version, prompt, rule bundle, trace | provenance de generación | Sí, snapshot | metadata sintética permitida; no crea inferencia ni AgentRun |
| DOCX | dataset/embedding namespace | versión/namespace por run | provenance de recuperación | Sí, nullable | se persiste sólo cuando existe; no crea vector store/RAG |
| DOCX/ADR-0005 | autonomy | A0–A4 | metadata de gobierno | Sí, intended level | CHECK A0–A4; nunca autoriza ejecución en esta fase |
| XLSX/JSON | Approval/AgentDecision | entidades separadas | decisión humana/runtime futuro | No | no crear tablas falsas ni referencias sin filas reales |
| DOCX/OpenAPI | Human Decision Gate | requerido según impacto | boundary futuro | Documentar | Recommendation no representa aprobación humana |
| DOCX/Data Architecture | provenance | requisito, layers, evidencia, modelo/regla, trace, confianza, supuestos | explicación congelada | Sí | Basis completa obligatoria en command atómico |

## 1. Evolución de migrations

Se agregó únicamente `foundation/0010_governed_recommendation_foundation`.
Es aditiva, reversible y condicionada a PostgreSQL mediante
`SeparateDatabaseAndState`. Crea `qms.recommendation` y
`qms.recommendation_basis`, constraints, triggers, RLS, policies, índices y
grants. No crea runtime de agentes, Approval ni ActionExecution.

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
| `0009_knowledge_layer_foundation` | `412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc` | frozen/intacta |
| `0010_governed_recommendation_foundation` | `c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79` | nueva/promovida |

La secuencia real verificada fue `0001 → … → 0010 → 0009 → 0010`. La
reversa eliminó sólo las dos tablas y cinco funciones Phase 10; los commands y
objetos Phase 9 continuaron funcionales.

## 2. Recommendation model e historia

`qms.recommendation` contiene UUID, tenant, Organization, title, body,
confidence, assumptions, impact nullable, status, intended autonomy y
`created_at`. No contiene execution status/result, rollback, tool calls,
external actions ni AgentRun falso.

La estrategia source-backed es **fila inmutable completa**. El DDL fuente
define una identidad `recommendation_id` y no define lineage/revision. Por ello
UPDATE y DELETE son rechazados por trigger incluso para SQL privilegiado; un
cambio material crea una nueva Recommendation. No se agregó `updated_at`: la
fuente sólo define `created_at` y la fila no cambia.

El lifecycle mínimo es `proposed`, único valor concreto encontrado en fuentes.
No se inventaron `approved`, `rejected`, `executed` ni una tabla Approval. Un
constraint deferred exige al menos una Basis antes de commit, de modo que no
puede persistir una Recommendation gobernada incompleta.

## 3. RecommendationBasis y referencias exactas

`qms.recommendation_basis` tiene tenant y Organization directos, parent
Recommendation exacta, StandardEdition, RequirementControl,
KnowledgeLayerRule, Evidence, rationale, snapshot de metadata y `created_at`.
No usa current pointers.

Defensas fuertes:

- FK compuesta `(tenant, Organization, Recommendation)`;
- FK compuesta `(StandardEdition, RequirementControl)`;
- FK compuesta `(tenant, Organization, Evidence)`;
- FK exacta a `KnowledgeLayerRule` más trigger que exige `published`;
- trigger que exige StandardEdition publicada;
- unique por Recommendation + control + Rule + Evidence;
- UPDATE/DELETE siempre rechazados; no cascade destructivo.

La prueba histórica creó Edition1/RC1, Rule v1 y Evidence revision 1, luego
Edition2/RC2, Rule v2 y Evidence revision 2. R1 siguió resolviendo exactamente
Edition1/RC1/Rule v1/Evidence rev1.

## 4. Decisión EvidenceCoverage

Se implementó Evidence directa y no EvidenceCoverage. XLSX/JSON/DDL definen
`RecommendationBasis.evidence_id`; EvidenceCoverage es un assessment separado
Evidence revision → RequirementControl. Agregar ambas FKs duplicaría esa
semántica y haría obligatoria una Coverage que las fuentes no exigen para toda
Recommendation. La Basis ya congela Evidence + RC y puede coexistir con una
Coverage independiente sin re-point.

## 5. Confidence y assumptions

Confidence es `numeric(5,4) NOT NULL` con CHECK `[0,1]`. La decisión usa la
misma representación fuente que EvidenceCoverage y la convención normalizada
ya promovida en Phase 8. Su contrato explícito es
`normalized_indicator_not_statistical_probability`: no se presenta como
probabilidad calibrada. Service y DB rechazaron `-0.1`, `1.0001`, `1.1`,
non-numeric y non-finite.

Assumptions es un array JSONB estructurado. DB exige array y el trigger exige
strings no vacíos; el command preserva orden y no descarta entradas. Se
reconstruyeron exactamente A1/A2. Un array vacío representa explícitamente
“sin supuestos declarados”; no se oculta en body.

## 6. Metadata de modelo/regla y provenance

Cada Basis congela los campos soportados por DOCX/DDL:

- model provider nullable;
- model identifier y model version;
- prompt version;
- rule bundle version;
- dataset version reference nullable;
- embedding namespace nullable;
- trace UUID.

Los tests usan fixtures `synthetic` y no realizan AI inference, LLM calls,
retrieval ni RAG. La Rule real referenciada sigue siendo la revisión publicada
exacta; `rule_bundle_version` describe el snapshot de generación y no reemplaza
esa FK.

## 7. Invariantes semánticos

El contract y las pruebas mantienen cuatro categorías distintas:

| Object | Clasificación | Efecto |
|---|---|---|
| RequirementControl | certifiable normative requirement | obligación normativa evaluable |
| KnowledgeLayerRule | non-certifiable guidance | metodología que informa; no crea requisito |
| Evidence | observed/supporting evidence | observación/provenance; no es decisión |
| Recommendation | derived advisory proposal | propuesta; no aprobación ni ejecución |

Crear Recommendation no cambió counts ni filas de RequirementControl,
KnowledgeLayerRule, Evidence o EvidenceCoverage.

## 8. Human Decision Gate y autonomy boundary

Approval, AgentDecision y Human Decision Gate completo se difieren. Una
Recommendation `proposed` no constituye aprobación humana. La linkage futura
debe añadir referencias tipadas sin reinterpretar Basis existente.

`intended_autonomy` acepta A0–A4 mediante smallint CHECK 0–4. Es metadata de
gobierno solamente. Una Recommendation A4 no mutó Process, Risk, Objective ni
Change, no produjo acción externa y `qms.action_execution` no existe.

## 9. RLS, Organization y principals

Ambas tablas tienen `tenant_id NOT NULL`, `ENABLE ROW LEVEL SECURITY`, `FORCE
ROW LEVEL SECURITY` y policies explícitas SELECT/INSERT/UPDATE/DELETE/ALL.
Policies no amplían grants.

| Principal | Recommendation | Basis | Resultado |
|---|---|---|---|
| APP | SELECT + INSERT | SELECT + INSERT | A=1 / none=0 / B=1 |
| WORKER | SELECT | SELECT | A=1 / none=0 / B=1; write denied |
| PROJECTOR | none | none | no Recommendation write/read |
| AUDIT WRITER | none | none | sólo append API de audit promovida |
| NORMATIVE CURATOR | none | none | catálogo global únicamente |
| MIGRATOR | DDL/policy propia | DDL/policy propia | non-superuser/NOBYPASSRLS en gate |

Los seis principals fueron LOGIN reales, non-superuser, `NOBYPASSRLS` y
non-owner de runtime tables. FKs compuestas rechazaron parent/Evidence de otro
tenant u Organization. El trigger append-only rechazó tenant reassignment.

## 10. Command, evento, outbox y audit

El único command material es `create_recommendation`. Recibe todas las Basis y
ejecuta en un único `trusted_tenant_context`/`transaction.atomic()`:

`Recommendation → Basis[] → DomainEvent → TransactionalOutbox → ImmutableAuditLog → commit`.

No existe generic save, revise/status command no respaldado, execute, approve,
infer, AgentRun ni AgentDecision command.

Contrato de evento: `recommendation.created`, schema version 1, aggregate
`recommendation`, version 1. Payload canónico incluye status, confidence con
semántica, assumptions, intended autonomy, `advisory_only=true` y snapshots de
Basis. Outbox conserva el event ID único.

Audit usa stream Recommendation y registra actor, tenant, trace, identity,
status, event/schema y cada Basis como `{basis_id, hash}`. El `after_hash`
compromete el estado completo, sin secretos ni prompt body sensible. La chain
se recalculó correctamente.

## 11. Pruebas bloqueantes

| Gate | Resultado |
|---|---|
| Minimum Basis deferred constraint | PASS; Recommendation sin Basis rechazada al commit |
| Edition/Requirement mismatch | PASS; FK compuesta rechazó Edition2 + RC1 |
| Draft Rule | PASS; trigger rechazó Rule no publicada |
| Frozen provenance | PASS; R1 conservó Edition1/RC1/Rule v1/Evidence rev1 |
| Basis re-point | PASS; RC, Rule, Evidence, tenant y DELETE rechazados por raw SQL |
| Recommendation overwrite | PASS; body UPDATE rechazado |
| Confidence | PASS service + DB |
| Assumptions reconstruction | PASS; dos entradas exactas |
| Certifiability negative | PASS; control/rule/evidence/coverage invariantes |
| No execution A4 | PASS; Process/Risk/Objective/Change invariantes; no ActionExecution |
| Atomic success | PASS; Recommendation/Basis/Event/Outbox/Audit coherentes |
| Atomic rollback | PASS; fallo post-audit dejó cero delta en las cinco superficies |
| Cross-tenant Basis | PASS; tenant A → Evidence B rechazado |
| Pool reuse | PASS; A → commit → none=0 → B only |
| Rollback context | PASS; A exception → rollback → none=0 → B only |

## 12. PostgreSQL, forward/reverse y teardown

Gate final: PostgreSQL 18.6, `server_version_num=180006`, imagen oficial,
run-id `20260817T210635Z_b33c1a`. Ejecutó principals, migrations 0001–0010,
fixtures sintéticos, matrices histórica/semantic/security/atomic y
`0010 → 0009 → 0010`.

El finalizer eliminó database, seis LOGIN roles, container, volume y temp dir.
`container_absent`, `volume_absent`, `temp_absent`: PASS. No se usaron
production, staging, DB compartida, AdminApps DB, MedSupplier DB, broker,
deployment ni secretos.

## 13. Regresión e integridad Django

| Gate | Resultado |
|---|---|
| Backend completo | **148 PASS / 0 FAIL / 0 SKIP** |
| Delta vs Phase 9 baseline 144 | **+4** contract tests Phase 10 |
| Foundation suite | **50 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL Phase 1–10 | PASS |
| Forward/reverse/forward | PASS |

Warnings esperados 400/401/403/404/405, pagination y telemetría PostHog/Chroma
no produjeron failures ni skips.

## 14. Source integrity y final verification

Los diez SHA-256 coinciden exactamente con el manifest: `8308bd…`, `e0a59c…`,
`11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`,
`eb4231…`: **10/10 MATCH**. No se modificaron source artifacts.

Los hashes promovidos confirman `0001–0009` byte-for-byte intactas. No se
modificó `.env`, no se introdujeron secrets, no se tocó ningún repo externo y
no se creó configuración de production/staging.

## 15. Riesgos residuales

1. Metadata de modelo queda como snapshot de Basis hasta introducir AgentRun;
   la slice siguiente debe evitar duplicación divergente mediante linkage
   tipada y una estrategia de transición explícita.
2. Confidence es un indicador normalizado, no calibración estadística; una
   futura calibración requiere dataset/métrica/version source-backed.
3. No existe workflow de withdraw/approve/reject porque las fuentes no fijan
   estados completos. Debe evolucionar junto al Human Decision Gate, no por
   strings ad hoc.
4. APP conserva INSERT directo por compatibilidad ORM; constraints preservan
   boundary/history/completeness, pero Event/Outbox/Audit siguen dependiendo
   del command service, como en las slices previas.
5. Basis no exige una KnowledgeLayerBinding concreta; las fuentes definen FKs
   directas Requirement/Rule/Evidence. Si un futuro contrato exige demostrar
   applicability mediante Binding exacto, debe añadirse de forma aditiva.
6. Audit es tamper-evident/append-only para runtime; DBA sigue siendo trust
   boundary hasta checkpoint WORM externo.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 16. Veredicto

**PHASE 10 — RECOMMENDATION BASIS + GOVERNED RECOMMENDATION FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001–0009` | FROZEN / INTACTAS | nueve hashes promovidos exactos | evolucionar sólo 0011+ |
| `0010_governed_recommendation_foundation` | PROMOTED | PostgreSQL 18.6; hash `c4f37a…`; reverse/forward PASS | congelar tras promoción |
| Recommendation | PROMOTED | immutable advisory proposal; proposed/A0–A4 metadata | lifecycle con Human Gate futuro |
| RecommendationBasis | PROMOTED | exact Edition/RC/Rule/Evidence; append-only | AgentRun linkage aditiva |
| Confidence/assumptions | PASS | DB/service validation + reconstruction | calibración futura explícita |
| Semantic invariants | PASS | counts/source rows unchanged | mantener en API/serializers |
| No execution | PASS | A4 sin business/external effects | Agent Runtime separado |
| Event/Outbox/Audit | PASS | atomic success + post-audit rollback | dispatcher futuro ya promovido |
| RLS/principals | PASS | ENABLE+FORCE; A/none/B; least privilege | repetir en cada tenant table |
| Backend/Django | PASS | 148/0/0; check/drift/compile | mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | preservar byte-for-byte |
| Recursos efímeros | REMOVED | finalizer PASS | ninguna acción |

## NEXT_CODEX_PROMPT

Implementa PHASE 11 — AGENT DEFINITION + AGENT RUN PROVENANCE FOUNDATION de forma incremental, aditiva y reversible exclusivamente en `/home/felipe/proyectos/isosmart`, preservando byte-for-byte las migrations `0001–0010` y los diez source artifacts. Añade sólo `0011+` para `AgentDefinition`, `AgentRun` y `ModelPolicy`, con versiones publicadas inmutables, tenant/Organization-safe AgentRun, trace/provenance congelada, inputs y referencias exactas a RequirementControl, StandardEdition, KnowledgeLayerRule y Evidence/EvidenceCoverage según reconciliación fuente, y linkage de output a Recommendation sin duplicar o reinterpretar RecommendationBasis histórica. Mantén reglas, retrieval, inferencia y policy como boundaries distinguibles; permite únicamente fixtures sintéticos y no integres proveedor IA real. Incluye DomainEvent, TransactionalOutbox, ImmutableAuditLog y atomic success/rollback, PostgreSQL 18.6 con ENABLE+FORCE RLS, principals reales, worker least-privilege, A/B/none, raw SQL, pool/rollback reuse, forward/reverse/forward, regresión completa, Django check/drift/compile, 10/10 hashes y teardown obligatorio. No implementes todavía AgentDecision, Approval/Human Decision Gate completo, autonomous execution, ActionExecution, EffectivenessCheck, LLM calls, RAG/vector store, external actions, broker, production, staging ni deployment. Entrega el reporte Phase 11, veredicto PROMOTED/NOT PROMOTED y exactamente un siguiente prompt autocontenido.
