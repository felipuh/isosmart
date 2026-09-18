# Phase 11 — Agent Definition + Agent Run Provenance Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 11 — AGENT DEFINITION + AGENT RUN PROVENANCE FOUNDATION`

**PostgreSQL final:** 18.6 (`server_version_num=180006`)

**Run-id final:** `20260817T213923Z_4abd95`

**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó únicamente `foundation/0011_agent_definition_run_provenance_foundation`.
Es aditiva, reversible y condicionada a PostgreSQL mediante
`SeparateDatabaseAndState`. Crea los catálogos globales `AgentDefinition` y
`ModelPolicy`, su ledger global, y las tablas tenant `AgentRun`,
`AgentRunInput` y `AgentRunRecommendation`. No crea AgentDecision, Approval,
ActionExecution, EffectivenessCheck, proveedor IA, RAG ni vector store.

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
| `0010_governed_recommendation_foundation` | `c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79` | frozen/intacta |
| `0011_agent_definition_run_provenance_foundation` | `cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2` | nueva/promovida |

Secuencia verificada: `0001 → … → 0011 → 0010 → 0011`. Durante la reversa,
Recommendation/Basis y el command Phase 10 siguieron funcionales. La reversa
restauró además los permisos de worker Phase 10.

## 2. Source reconciliation gate

Se leyeron directamente los diez artifacts: XML interno DOCX, las once hojas
XLSX, JSON, DDL, OpenAPI, Mermaid, Draw.io, ambos CSV y LEEME. DOCX es autoridad
funcional; XLSX/JSON son autoridad estructurada; DDL/OpenAPI son parciales.

| SOURCE | ENTITY | FIELD / RELATION | SEMANTICS | IMPLEMENT? | RATIONALE |
|---|---|---|---|---:|---|
| DOCX runtime §7 + Mermaid | Agent runtime | Observe→Contextualize→Retrieve→Validate→Analyze→Simulate→Recommend→Autonomy | lifecycle conceptual | Sí, como boundaries/provenance; no engine | permite trazabilidad sin simular orchestration |
| XLSX/JSON Agent Catalog | AgentDefinition | name, module/capability, responsibility/purpose, autonomy range | catálogo lógico de capacidades | Sí | fuente estructurada y catálogo global en Data Architecture |
| XLSX/JSON DB_Entities | AgentDefinition | agent id, name, purpose, ModelPolicy, autonomy max | definición de agente | Sí | exactos más versionado exigido por arquitectura |
| Data Architecture | AgentDefinition | global, versioned/released | catálogo platform-curated | Sí | sin tenant falso; published append-only |
| XLSX/JSON DB_Entities | ModelPolicy | approved models, data classes, guardrails, human gate rules | policy separada del agente | Sí | no se colapsa en AgentDefinition ni JSON genérico |
| Data Architecture | ModelPolicy | global, published append-only | governance versionada | Sí | AgentRun congela versión exacta |
| DDL/XLSX/JSON | AgentRun | tenant, AgentDefinition, model/prompt versions, start/end, trace | ejecución concreta | Sí | Organization y status se añaden por boundary aprobado |
| DDL | AgentRun | event id | causal trigger | Sí, como `causation_id` UUID | evita FK a un único tipo de evento y conserva causalidad |
| DOCX §11 | AgentRun | model, prompt, Rule, dataset/embedding namespace, trace | provenance por run | Sí | columnas/FKs, no blob |
| DOCX Drawer | provenance | Evidence IDs/hashes, Knowledge Layers, model/rule version | explicación reconstruible | Sí | exact Evidence revision y Rule revision |
| Data Architecture | Evidence history | edición/regla vigentes nunca se pierden | frozen historical link | Sí | Edition+Requirement+Rule+Evidence exactos |
| XLSX/JSON graph objects | AgentRun→Recommendation | advisory output linked to run | Recommendation aggregate propio | Sí | tabla link; no body/confidence duplication |
| DDL | Recommendation.agent_run_id | output origin | run→Recommendation | Sí, equivalente normalizado | tabla link evita alterar 0010 o reescribir aggregate histórico |
| XLSX/JSON | RecommendationBasis | Requirement, Rule, Evidence | output basis | Sí, reutilizada | consistency exacta service + DB |
| DDL/Data Architecture | EvidenceCoverage | Evidence→Requirement assessment | coverage separada | No en AgentRunInput | sources de AgentRun/Recommendation usan Evidence; añadir ambos duplicaría semántica |
| DOCX/XLSX | autonomy | A0–A4 maxima/guardrails | governance metadata | Sí | nunca implica ejecución |
| XLSX/JSON | AgentDecision/Approval/ActionExecution | entidades posteriores separadas | decisión/human gate/acción | No | fuera de scope y no se mezclan con AgentRun |
| OpenAPI | Recommendation read/basis | futura presentación | consumidor | No | no autoriza endpoint Phase 11 |

No se inventaron token counts, latency, temperature, cost, retry, tool-call o
framework telemetry fields.

## 3. Límite semántico del runtime

- `AgentDefinition`: versión de una capacidad lógica global.
- `AgentRun`: un registro de ejecución gobernada tenant/Organization.
- `Recommendation`: propuesta advisory inmutable y agregado propio.
- `AgentDecision`: objeto futuro; no existe en Phase 11.
- `ActionExecution`: objeto futuro; no existe en Phase 11.

Un run A4 no ejecuta. `SYNTHETIC MODEL OUTPUT` es fixture persistido como body
de Recommendation; no ocurrió inferencia ni llamada externa.

## 4. AgentDefinition y versionado

`governance.agent_definition` contiene UUID, lineage, `agent_key`, name,
version, predecessor, purpose, capability, autonomy max, ModelPolicy exacta,
status, published/created timestamps. No contiene tenant.

Estados: `draft`, `published`. El único UPDATE permitido es publicación
`draft→published` sin cambio material. Una revisión usa una nueva fila,
predecessor publicada, mismo lineage/key y version única. Forks, overwrite y
DELETE son rechazados. La matriz creó y conservó Definition v1→v2.

## 5. ModelPolicy y versionado

`governance.model_policy` es separado y contiene UUID, lineage, policy key,
version, predecessor, approved models, data classes, guardrails, human gate
rules, status y timestamps. Los arrays/objetos tienen shape DB/service; modelos
aprobados son strings no vacíos.

Published es inmutable. Policy v2 crea una fila nueva. AgentRun R1 siguió
apuntando a Policy v1 después de publicar v2.

## 6. AgentRun

`qms.agent_run` contiene tenant y Organization directos, Definition y Policy
exactas, capability, `running/completed/failed`, requested autonomy, effective
ceiling, provider/model/prompt/rule bundle/dataset/embedding metadata,
trace/correlation/causation y timestamps. No contiene estado de acción.

DB y service exigen Definition/Policy publicadas, capability exacta,
Definition→Policy exacta y ceiling no mayor al Definition. Sólo se permite
`running→completed|failed`; material provenance y tenant/Organization nunca se
actualizan. Completed exige link Recommendation existente.

## 7. Input provenance y referencias exactas

`qms.agent_run_input` es el bundle mínimo tipado, no un generic graph:

- exact StandardEdition publicada;
- exact RequirementControl de esa Edition;
- exact KnowledgeLayerRule publicada;
- exact tenant/Organization Evidence revision.

La FK compuesta Edition/Requirement rechaza current-edition reinterpretation y
la FK compuesta tenant/Organization/Evidence rechaza attachment cruzado. La
tabla es append-only y un deferred constraint impide commit de un run sin input.

### Decisión EvidenceCoverage

Se usa Evidence directa, igual que RecommendationBasis y los graph objects
fuente. EvidenceCoverage sigue siendo el assessment Evidence→Requirement. No se
duplica como segunda provenance obligatoria.

## 8. Separación rules / retrieval / inference / policy

| Boundary | Provenance concreta |
|---|---|
| deterministic rules | exact KnowledgeLayerRule + `rule_bundle_version` |
| retrieval/context | exact Edition/Requirement/Evidence + dataset version/embedding namespace opcionales |
| model inference | provider/model identifier/version + prompt version; fixture sintético solamente |
| governance policy | exact ModelPolicy version + requested/effective autonomy |

El payload event/audit conserva estas cuatro secciones por nombre. No existe
`agent_config` ni `retrieved_context` de texto gigante.

## 9. Recommendation linkage y Basis consistency

`qms.agent_run_recommendation` es one-to-one, tenant/Organization-safe y
append-only. Recommendation no se modifica ni se duplica dentro de AgentRun.

Completion compone el command Phase 10 dentro de la misma transacción confiable.
La metadata model/prompt/rule/dataset/embedding se toma del run, no del caller.
Service compara igualdad exacta de conjuntos y un trigger DB repite un
`EXCEPT` bilateral entre AgentRunInput y RecommendationBasis. RC2, Rule v2 o
Evidence v2 son rechazados contra R1.

## 10. ModelPolicy enforcement y autonomy

Antes de persistir un run válido se comprueban:

- capability = Definition capability;
- Policy = Policy exacta de Definition;
- capability incluida en `guardrails.allowed_capabilities` cuando se declara;
- model identifier incluido en `approved_models`;
- requested autonomy ≤ min(Definition max, Policy guardrail max).

La prueba de capability no permitida dejó cero AgentRun parcial. A4 completó
una Recommendation advisory sin Process/Risk/Objective/Change write ni
ActionExecution.

## 11. Commands

Catálogo: `create_model_policy`, `revise_model_policy`,
`publish_model_policy`, `create_agent_definition`,
`revise_agent_definition`, `publish_agent_definition`.

Runtime: `start_agent_run`, `complete_agent_run_with_recommendation`,
`fail_agent_run`. No existen generic save, infer, approve, decide o execute.

## 12. Events, outbox y audit

Eventos tenant schema v1:

- `agent_run.started`;
- `agent_run.completed`;
- `agent_run.failed`.

Start persiste Run + inputs + Event + Outbox + ImmutableAuditLog. Completion
persiste Recommendation + Basis + link + status + Recommendation event/outbox/
audit + AgentRun event/outbox/audit. Trace de Run se conserva en ambos streams.
Audit compromete hashes de Definition, Policy, inputs, metadata, status y output
sin raw prompt ni secrets.

No se emitieron eventos globales de catálogo porque DomainEvent 0003 sigue
requiriendo tenant real. La curación usa `governance.curation_audit` append-only;
no fake tenant y no cambio silencioso de 0003.

## 13. Worker y catalog curator

Worker es LOGIN real, non-superuser, NOBYPASSRLS y non-owner. Phase 11 le
concede sólo:

- SELECT/INSERT AgentRun/Input/Link;
- UPDATE columnas `status,completed_at` de AgentRun;
- INSERT tenant-scoped DomainEvent/Outbox para typed commands;
- INSERT Recommendation/Basis bajo invariantes Phase 10;
- audit sólo mediante función promovida.

No obtiene UPDATE/DELETE de Recommendation/Basis, ni writes a Process, Risk,
Objective, Change, Evidence o catálogo.

Se creó `agent_catalog_curator_<runid>` separado: LOGIN, non-superuser,
NOBYPASSRLS, non-owner, SELECT/INSERT de sus dos catálogos, UPDATE sólo de
status/published_at y ledger propio. Tiene cero writes normativos, QMS, Evidence,
Recommendation o AgentRun. Normative curator tiene cero privilegio en el
catálogo de agentes.

## 14. RLS y matriz de seguridad

Las tres tablas tenant Phase 11 tienen `tenant_id NOT NULL`, ENABLE + FORCE RLS,
policies explícitas SELECT/INSERT/UPDATE/DELETE/ALL y FKs compuestas.

| Table | APP A/none/B | WORKER A/none/B |
|---|---|---|
| AgentRun | `2/0/1` | `2/0/1` |
| AgentRunInput | `2/0/1` | `2/0/1` |
| AgentRunRecommendation | `1/0/1` | `1/0/1` |

Raw SQL rechazó tenant reassignment, model rewrite, input Evidence re-point,
link DELETE y published Definition/Policy overwrite. El worker no pudo UPDATE
Risk. Roles runtime no son owner, superuser ni BYPASSRLS.

## 15. Atomic success, rollback y frozen history

Success fixture:

`Definition v1 + Policy v1 + Edition1/RC1 + Rule v1 + Evidence rev1 → Run →
SYNTHETIC MODEL OUTPUT → Recommendation/Basis → completed`.

Run, input, link, Recommendation, Basis, events, outboxes y audit chains fueron
coherentes. Una excepción deliberada después de preparar Recommendation y audit
dejó Run `running` y cero delta parcial en Recommendation/Basis/link/Event/
Outbox/Audit.

Después se publicaron Definition v2, Policy v2, Edition2/RC2, Rule v2 y Evidence
rev2. R1 reconstruyó exactamente las cinco referencias v1.

## 16. Pool, forward/reverse y teardown

Pool reuse: A→commit→none=0→B only y A→rollback→none=0→B only: PASS.

Forward/reverse/forward: `0001→…→0011→0010→0011`: PASS. Phase 10 command
funcionó durante la reversa. El finalizer eliminó database, siete LOGIN roles,
container, volume y temp dir. `container_absent`, `volume_absent`, `temp_absent`:
PASS.

No se usó production, staging, DB compartida, AdminApps DB, MedSupplier DB,
broker, deployment, API key, secret ni `.env`.

## 17. Regresión, Django e integridad

| Gate | Resultado |
|---|---|
| Backend completo | **152 PASS / 0 FAIL / 0 SKIP** |
| Delta vs Phase 10 baseline 148 | **+4** contract tests Phase 11 |
| Foundation suite | **54 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL Phase 1–11 | PASS |
| Forward/reverse/forward | PASS |

Warnings esperados 400/401/403/404/405, pagination y telemetría PostHog/Chroma
no produjeron failures ni skips. No hubo llamadas IA; el intento de telemetría
preexistente falló cerrado por DNS y no forma parte de Phase 11.

## 18. Source integrity y final verification

Los diez SHA-256 coinciden con el manifest: `8308bd…`, `e0a59c…`, `11c2b4…`,
`952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`,
`eb4231…`: **10/10 MATCH**.

`0001–0010` coinciden byte-for-byte con sus hashes promovidos. Source artifacts,
`.env` y repos externos no se modificaron. El único `git diff --check` ajeno al
slice sigue siendo el whitespace preexistente de `Sidebar.jsx:28`; los archivos
Phase 11 quedan clean.

## 19. Riesgos residuales

1. `approved_models`, data classes y guardrails son contracts JSON source-backed;
   schemas de policy más ricos requieren una futura migration, no claves ad hoc.
2. APP/worker conservan INSERT directo compatible con ORM en varias tablas; DB
   preserva RLS/history/consistency, pero Event/Outbox/Audit completos dependen
   del command service promovido.
3. No hay hash de raw prompt: se conserva versión y no secretos. Un futuro
   registry de prompt controlado podría añadir content hash source-backed.
4. No hay provider/model registry separado ni calibración de confidence.
5. Global catalog events siguen diferidos hasta una foundation platform-event
   sin tenant falso.
6. Audit es tamper-evident para runtime; DBA/WORM externo sigue trust boundary.
7. Human Decision Gate, AgentDecision y Approval todavía no existen; una
   Recommendation completada sigue siendo únicamente advisory.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 20. Veredicto

**PHASE 11 — AGENT DEFINITION + AGENT RUN PROVENANCE FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001–0010` | FROZEN / INTACTAS | hashes promovidos exactos | evolucionar sólo 0012+ |
| `0011_agent_definition_run_provenance_foundation` | PROMOTED | PostgreSQL 18.6; hash `cdb23e…`; reverse/forward PASS | congelar tras promoción |
| AgentDefinition | PROMOTED | global v1→v2, published immutable | assignments futuros separados |
| ModelPolicy | PROMOTED | global v1→v2, enforcement/rollback PASS | schema policy futuro versionado |
| AgentRun/Input | PROMOTED | exact frozen provenance; A/none/B | API/UI futura contract-first |
| Recommendation linkage | PROMOTED | one-to-one link + bilateral DB consistency | AgentDecision next |
| Rules/retrieval/inference/policy | PASS | payload/columns/FKs separados | motores reales fuera de scope |
| Worker/curator | PASS | seven real least-privilege LOGIN roles | mantener privilege regression |
| Event/Outbox/Audit | PASS | atomic start/completion + rollback | dispatcher futuro ya promovido |
| No execution | PASS | A4 sin ActionExecution/business writes | Human Gate before any action |
| Backend/Django | PASS | 152/0/0; check/drift/compile | mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | preservar byte-for-byte |
| Recursos efímeros | REMOVED | finalizer PASS | ninguna acción |

## NEXT_CODEX_PROMPT

Implementa PHASE 12 — AGENT DECISION + HUMAN DECISION GATE FOUNDATION de forma incremental, aditiva y reversible exclusivamente en `/home/felipe/proyectos/isosmart`, preservando byte-for-byte las migrations `0001–0011` y los diez source artifacts. Añade sólo `0012+` para `AgentDecision` y `Approval`, con lifecycle humano explícito, separación estricta entre Recommendation advisory, AgentDecision y Approval, linkage exacta a AgentRun/Recommendation, A0–A4 como ceilings de autorización y ninguna equivalencia entre A4 y permiso de ejecutar. Conserva Definition/Policy/Run/Basis frozen provenance; exige que toda decisión y aprobación sea tenant/Organization-safe, actor/role/time/reason source-backed, append-only o versionada según sources, y coherente con la Recommendation exacta. Incluye commands tipados, DomainEvent/TransactionalOutbox/ImmutableAuditLog atómicos, success/rollback, rechazo de auto-aprobación o principal no autorizado, RLS ENABLE+FORCE, A/B/none, raw SQL, worker/human-approver least privilege, pool/rollback reuse, forward/reverse/forward, full backend regression, Django check/drift/compile, 10/10 hashes y teardown obligatorio. No implementes todavía ActionExecution, EffectivenessCheck, llamadas LLM/provider, RAG/vector store, tool calling, external actions, autonomous execution, broker, production, staging ni deployment. Entrega `docs/transformation/PHASE12_AGENT_DECISION_HUMAN_DECISION_GATE_FOUNDATION_REPORT.md`, veredicto PROMOTED/NOT PROMOTED y exactamente un siguiente prompt autocontenido.
