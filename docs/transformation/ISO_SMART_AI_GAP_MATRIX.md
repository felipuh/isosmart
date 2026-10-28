# ISO Smart AI — gap matrix verificable

## Método de cobertura

### Baseline histórico provisional

Antes del intake oficial: 42 capacidades, 3 implementadas, 18 parciales, 21 ausentes. Fórmula: `(3 × 1 + 18 × 0.5 + 21 × 0) / 42 = 12 / 42 = 28.57%`. Se conserva para trazabilidad y no se reescribe.

### Baseline verificado — source gate 10/10

Universo: las **43 entidades** de `Mapa_Maestro_Datos.json` y la hoja `DB_Entities` del XLSX, que coinciden exactamente. La lista oficial añade `User`, omitida en las 42 filas provisionales. Para el ecosistema Smart3AI se evalúa como capacidad `UserProjection`; no cambia el ownership AdminApps.

Puntuación reproducible por fila: Implementado = 1, Parcial = 0.5, Ausente = 0. Resultado: **3 implementadas, 19 parciales, 21 ausentes**. Fórmula: `(3 × 1 + 19 × 0.5 + 21 × 0) / 43 = 12.5 / 43 = 29.07%` (redondeo a dos decimales).

Cambio exacto: denominador `42→43`, parciales `18→19`, numerador `12→12.5`, porcentaje `28.57%→29.07%`. La única fila nueva es `User/UserProjection`, clasificada Parcial por `auth.User`, UserProfile y sync AdminApps existentes, pero sin projection version/event/reconcile ni RLS. Ninguna de las 42 filas históricas cambia de clasificación a causa del intake; los artefactos confirman el universo/semántica, no nueva implementación en código.

Esto no es readiness Enterprise ni cumplimiento normativo. “Parcial” exige coincidencia semántica demostrable en código; nombres similares no bastan.

| Nueva capacidad | Requisito fuente provisional | Implementación actual | Estado/gap | Acción | Prioridad | Dependencia | Riesgo |
|---|---|---|---|---|---|---|---|
| TenantProjection | Multi-tenancy/AdminApps | Organization.external_id + sync | Parcial | Proyección UUID, sync ledger y RLS | P0 | AdminApps contract | Crítico |
| Organization | Harmonized Core | core.Organization | Parcial: mezcla tenant/QMS/billing | Separar proyección global y organización QMS | P0 | TenantProjection | Alto |
| Site | Harmonized Core | LocationScope no canónico | Ausente | Nuevo agregado Site | P1 | Organization | Alto |
| User / UserProjection | XLSX/JSON `User`; AdminApps boundary | auth.User + UserProfile + sync AdminApps | Parcial: identity local/sync sin projection ledger, source version ni RLS | UserProjection; identity/MFA/global role authority AdminApps; QMS assignments locales | P0 | TenantProjection/AdminApps contract | Crítico |
| Standard | Normative relations | ISOClauseConfig/listas | Parcial | Catálogo global versionado | P0 | Artefactos TO-BE | Alto |
| StandardEdition | Historia normativa | Ninguna | Ausente | Modelo inmutable/efectividad | P0 | Standard | Crítico |
| Clause | Normative relations | ISOClauseConfig | Parcial: sin edición | Migrar a Clause por edición | P0 | StandardEdition | Alto |
| RequirementControl | Harmonized Core | Ninguna | Ausente | Control versionado | P0 | Clause | Crítico |
| KnowledgeLayer | Quality Intelligence | Ninguna | Ausente | Nuevo catálogo/versiones | P0 | RequirementControl | Alto |
| KnowledgeLayerRule | Governance Core | Reglas dispersas en código | Ausente | Regla versionada y determinista | P0 | KnowledgeLayer | Crítico |
| KnowledgeLayerBinding | Normative relations | Ninguna | Ausente | Binding many-to-many efectivo | P0 | Rule/domain | Alto |
| StandardPack | Standard packs | enabled_standards JSON | Ausente: no equivale a un pack | Pack/versión/compatibilidad | P1 | StandardEdition | Alto |
| Process | Business object | core + spm duplicados | Parcial | Canónico + mapping/backfill | P0 | Tenant/RLS | Alto |
| Stakeholder | Business object | core + sie duplicados | Parcial | Canónico + mapping/backfill | P0 | Tenant/RLS | Alto |
| StakeholderRequirement | Harmonized Core | needs/expectations y CustomerRequirement | Parcial | Entidad tipada/versionada | P1 | Stakeholder | Alto |
| Risk | Business object | RiskMatrix/RiskOpportunity | Parcial | Canónico separado del assessment | P0 | Tenant/RLS | Alto |
| Opportunity | Business object | RiskOpportunity combinado | Parcial | Tipo canónico/migración compatible | P1 | Risk model | Medio |
| Objective | Business object | core + planning duplicados | Parcial | Canónico + métricas/evidence | P0 | Tenant/RLS | Alto |
| Change | Business object | ChangeLog/ChangeControl | Parcial | Canónico + workflow | P1 | Approval/Event | Alto |
| Document | Harmonized Core | core.Document | Parcial | Lifecycle, storage auth, links | P0 | Tenant/RLS | Alto |
| DocumentVersion | Historia/evidencia | Ninguna explícita | Ausente | Versiones inmutables + hash | P0 | Document | Crítico |
| Evidence | Evidence graph | EvidenceNode/documents varios | Parcial | Evidence canónica + hash/version | P0 | DocumentVersion | Crítico |
| EvidenceCoverage | Evidence graph | Edges genéricos | Ausente: no hay cobertura normativa | Coverage a control/edición/regla | P0 | Evidence/Requirement | Crítico |
| Recommendation | AI runtime | Respuestas/logs dispersos | Parcial | Registro material común | P0 | AgentRun | Crítico |
| RecommendationBasis | Provenance | Ninguna uniforme | Ausente | Evidencia/reglas/supuestos congelados | P0 | Recommendation | Crítico |
| AgentDefinition | AI runtime | Motores Python | Ausente: no hay entidad gobernada | Definición/version/autonomía | P1 | ModelPolicy | Alto |
| AgentRun | Reconstruction | Logs parciales | Ausente | Run end-to-end con trace | P0 | AgentDefinition | Crítico |
| AgentDecision | Human gate | Flags/logs parciales | Ausente | Decisión/policy/razón | P0 | AgentRun/Approval | Crítico |
| DomainEvent | Event architecture | Notificaciones ad hoc | Ausente | Evento + outbox | P0 | Transaction model | Crítico |
| Approval | Human gate | Múltiples ApprovalRecord | Parcial | Servicio/entidad común | P0 | RBAC/ABAC | Alto |
| ActionExecution | Agent runtime | Acciones de dominio directas | Ausente | Command execution auditado | P0 | Approval/Event | Crítico |
| EffectivenessCheck | Learning loop | Campos CA/improvement | Parcial | Entidad común medible | P1 | ActionExecution | Alto |
| Audit | QMS | InternalAudit | Implementado | Harden tenant/evidence/version | P1 | RLS/Evidence | Medio |
| Finding | QMS | AuditFinding | Implementado | Harden graph links | P1 | Audit/Evidence | Medio |
| Nonconformity | Business object | operations + improvement duplicados | Parcial | Canónico + compatibilidad | P0 | Finding | Alto |
| CorrectiveAction | QMS | improvement.CorrectiveAction | Implementado | Añadir graph/effectiveness | P1 | Nonconformity | Medio |
| IndustryProfile | Industry packs | Ninguna | Ausente | Perfil versionado | P2 | StandardPack | Medio |
| LearningPath | Foundation Gate | Ninguna | Ausente | Nuevo contexto learning | P1 | Edition/Role | Alto |
| QuestionBank | Foundation Gate | Ninguna | Ausente | Banco versionado | P1 | LearningPath | Alto |
| QuizAttempt | Foundation Gate | Ninguna | Ausente | Intento, score, retries | P1 | QuestionBank | Alto |
| ConceptMastery | Foundation Gate | Ninguna | Ausente | Mastery/delta learning | P1 | QuizAttempt | Alto |
| ModelPolicy | AI governance | Config/env + logs | Ausente | Policy versionada/guardrails | P0 | Admin/security | Crítico |
| ImmutableAuditLog | Audit trail | 3+ logs fragmentados | Parcial | Append-only, hash chain/WORM export | P0 | Tenant/Event | Crítico |

## Crosswalk transversal

| Capacidad | Fuente | AS-IS | Gap/acción | Prioridad | Dependencia/riesgo |
|---|---|---|---|---|---|
| 17-step onboarding | DOCX + XLSX/JSON (17 exactos) | 6 macro-pasos y orchestrator | Modelar estados/transiciones backend-authoritative; etapas 1–7 AdminApps/control plane | P0 | AdminApps contracts + learning; crítico |
| Foundation Gate 2026 | Solicitud §Onboarding | Quiz local en UI, sin entidades | Backend-authoritative learning context | P0 | Edition + learning; crítico |
| Compliance Evidence Graph | Solicitud §Graph | EvidenceNode/Edge genérico | Relaciones tipadas/versionadas y CTE | P0 | Data migration; crítico |
| Transactional outbox | Solicitud §Events | No existe | Outbox en misma transacción | P0 | Dispatcher/idempotencia; crítico |
| Governed agent runtime | Solicitud §Agent runtime | Motores y logs parciales | Runtime común + provenance | P0 | ModelPolicy/Human gate; crítico |
| NormativeIntelligenceDrawer | Solicitud §Frontend | No existe | Componente compartido sobre graph API | P1 | Graph/OpenAPI; alto |
| Contract-first API | Solicitud §Contract | DRF ad hoc, sin OpenAPI | Baseline + cliente generado | P0 | ADR-0006; alto |
| PostgreSQL RLS | Solicitud §Data | Filtros de aplicación | Tenant context + FORCE RLS + tests | P0 | AdminApps mapping; crítico |

## Verificación de conteo

La tabla principal contiene 43 filas: 3 `Implementado` (`Audit`, `Finding`, `CorrectiveAction`), 19 `Parcial` (incluida la nueva `User/UserProjection`) y 21 `Ausente`. El rebase no puntúa los foundations adicionales `TransactionalOutbox`/`EventInbox` como entidades separadas porque no figuran en el catálogo oficial de 43; permanecen gaps transversales y gates obligatorios, evitando alterar el denominador por diseño derivado.

## Eventos y ownership

| Evento | Owner primario | Consumidor |
|---|---|---|
| payment.confirmed | AdminApps | ISO Smart provision/read-model |
| tenant.provisioned | AdminApps | ISO Smart projection/onboarding |
| iso9000.foundation.completed | ISO Smart | AdminApps opcional para entitlement/product telemetry |
| context.signal.detected | ISO Smart | Quality Intelligence |
| stakeholder.requirement.changed | ISO Smart | Risk/objective agents |
| kpi.threshold.breached | ISO Smart | Recommendation/audit |
| supplier.performance.degraded | ISO Smart | Risk/nonconformity |
| customer.complaint.received | ISO Smart | Nonconformity |
| change.requested | ISO Smart | Approval/runtime |
| document.updated | ISO Smart | Evidence/retrieval indexing |
| measurement.out_of_tolerance | ISO Smart | Nonconformity |
| audit.finding.created | ISO Smart | Corrective action |
| nonconformity.detected | ISO Smart | Corrective action/runtime |
| standard.edition.published | ISO Smart normative catalog (o proveedor curado futuro) | Delta learning/rule evaluation |
