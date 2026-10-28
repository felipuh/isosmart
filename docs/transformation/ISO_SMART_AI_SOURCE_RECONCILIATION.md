# ISO Smart AI — reconciliación de fuentes oficiales

Fecha: 2026-08-13. Gate de intake: **10/10 VALID**. Los hashes y pruebas de formato están en `source-artifacts/SOURCE_ARTIFACT_MANIFEST.md`. Ningún artefacto fuente se corrige en esta reconciliación.

## Jerarquía de autoridad

1. **Especificación Integrada (DOCX):** autoridad funcional y de producto primaria: principios, experiencia, 17 etapas, 63 fichas de requisito, runtime, seguridad y roadmap.
2. **Mapa Maestro Arquitectura (XLSX) + Mapa Maestro Datos (JSON):** autoridad estructurada de entidades, campos candidatos, requisitos, agentes, eventos, onboarding y relaciones. Si difieren entre sí, se bloquea el objeto hasta decisión; en este paquete las tablas principales coinciden.
3. **Mermaid + Draw.io + Nodes/Edges CSV:** representaciones arquitectónicas y relacionales. Una omisión visual no elimina una entidad o etapa declarada en A/B.
4. **DDL PostgreSQL:** implementación inicial de referencia. No define por sí solo schema final, ownership, tenancy, RLS ni completitud.
5. **OpenAPI:** contrato inicial ilustrativo. No representa cobertura definitiva ni autoriza operaciones públicas.
6. **LEEME:** metadata e instrucciones del paquete.
7. **Decisiones de integración Smart3AI:** AdminApps es el system of record físico de identity, tenant global, product entitlement, plan/subscription/billing y provisioning global. Esta especialización del ecosistema transforma `Tenant`/`User` del modelo lógico en proyecciones locales sin alterar las fuentes.

## Resultado cuantitativo

- DOCX: 63 fichas de requisito, 17 etapas, 31 normas/capas, 43 entidades, 14 eventos y 33 agentes/capacidades.
- XLSX: 11 hojas. `DB_Entities` 43/43, `Event_Catalog` 14/14, `Agent_Catalog` 33/33, `Onboarding` 17/17, `Industry_Routes` 6/6, `Graph_Nodes` 153/153 y `Graph_Edges` 731/731 coinciden exactamente con JSON.
- JSON ↔ Nodes/Edges CSV: igualdad exacta de filas y orden; 153 IDs únicos; 731 aristas sin extremos colgantes.
- Red: 4 capas, 31 Knowledge Layers, 63 requirements, 27 modules y 28 agentes de cláusula; relaciones principales: 488 `INFORMS`, 94 `CONTAINS`, 63 `IMPLEMENTED_BY`, 63 `ORCHESTRATED_BY` y 23 dependencias inter-requisito.
- DDL: 24 tablas de las 43 entidades estructuradas; 19 entidades ausentes; cero `CREATE POLICY`, `ENABLE RLS` o `FORCE RLS`.
- OpenAPI: 7 paths/7 operaciones, sin schemas de respuesta, auth, errores, tenant scope, idempotencia ni efectos de audit/eventing.
- Mermaid/Draw.io: consistentes como vistas resumidas; ambos muestran 15 etapas de onboarding, no las 17 canónicas.

## Matriz de discrepancias

| SOURCE_A | SOURCE_B | OBJECT | FIELD/RELATION | VALUE_A | VALUE_B | SEVERITY | AUTHORITATIVE_DECISION | RATIONALE |
|---|---|---|---|---|---|---|---|---|
| DOCX/XLSX/JSON | Mermaid/Draw.io | Onboarding | Etapas | 17 | 15 | Alta | Conservar las 17 etapas | A/B son funcional y estructural; las vistas omiten `Subscription Activation` y `Value Discovery`. |
| XLSX/JSON | DDL | Modelo de datos | Entidades | 43 | 24 | Alta | Diseñar desde 43 entidades y añadir foundations explícitas | DDL se autodeclara inicial. |
| XLSX/JSON | DDL | Organization/Site/User | Presencia | Presentes | Ausentes | Alta | Modelar Organization/Site; User como proyección | DDL no cubre control plane ni QMS completo. |
| XLSX/JSON | DDL | Core empresarial | 16 entidades relevantes | Faltan 11 (`Stakeholder`, `Risk`, `Opportunity`, `Objective`, `Change`, `Document`, `DocumentVersion`, `Audit`, `Finding`, `Nonconformity`, `CorrectiveAction`) | Alta | Incorporar gradualmente, sin duplicación por norma | Principio funcional primario. |
| DOCX/XLSX/JSON | DDL | Tenant | `name`, `plan`, `status` locales | Tabla `tenant` autoritativa aparente | Crítica | Renombrar objetivo a `TenantProjection`; AdminApps manda | Integración específica Smart3AI; evita doble autoridad. |
| DOCX/XLSX/JSON | AdminApps boundary | User | Usuario con tenant/role/MFA | Identity/roles globales/MFA en AdminApps | Crítica | `UserProjection` + assignments QMS locales | Separar identidad global de autorización de dominio. |
| DOCX/XLSX/JSON | AdminApps boundary | Plan/subscription/billing | Flujo dentro de onboarding | Control plane ya existente | Crítica | Etapas 1–7 se proyectan/consumen; ISO Smart no confirma cobro | SoR del ecosistema prevalece para integración, sin cambiar la intención funcional. |
| DDL | Requisito Enterprise | RLS | Comentario “preparada para RLS” | Cero políticas/comandos RLS | Crítica | DDL no demuestra aislamiento; diseñar/ensayar RLS real | Un comentario no es un control. |
| DDL | Diseño histórico | EvidenceCoverage | `evidence_id`, `requirement_id` | No fija edition/rule aplicables | Crítica | Añadir referencias congeladas a edition/control/rule/binding version | Evitar reinterpretación histórica. |
| DDL | XLSX/JSON | EffectivenessCheck | Sin `tenant_id` en DDL | Entidad estructurada tampoco lo lista | Alta | `tenant_id NOT NULL` directo | Defensa RLS y consultas operativas. |
| DDL | Modelo tenant | ActionExecution/RecommendationBasis | Sin `tenant_id` directo | Scope inferido por padre | Alta | Preferir `tenant_id` directo + FK compuesta; probar hijos indirectos restantes | Reduce joins frágiles y cross-tenant graphs. |
| DDL | DOCX | DomainEvent | Envelope mínimo | Faltan schema, correlation, causation y source | Alta | Envelope completo y append-only | Requerido para replay/provenance. |
| DDL | ADR-0004 | Event delivery | No outbox/inbox | Outbox + receipt requeridos | Crítica | Añadir `TransactionalOutbox` y `EventInbox/ConsumerReceipt` | Evento persistido no equivale a publicación fiable. |
| DDL | Requisito audit | ImmutableAuditLog | Tabla insertable sin grants/chain/trace | Append-only/tamper evidence requeridos | Crítica | Grants separados, trigger defensivo, chain por tenant y export | El nombre no aporta inmutabilidad. |
| DDL | XLSX/JSON | ModelPolicy/AgentDecision | Ausentes; policy JSON embebida | Entidades explícitas | Alta | Entidades versionadas; definición referencia policy | Governed runtime reconstruible. |
| DDL | Autoridad normativa | `pgcrypto` | Extension obligatoria para UUID | PostgreSQL 18 ofrece UUID nativo | Media | Ninguna extensión obligatoria baseline; UUIDv7 nativo/app | No instalar extensión sin necesidad. |
| OpenAPI | DOCX/XLSX/JSON | API | 7 operaciones | 43 entidades + casos de uso | Alta | Tratar OpenAPI como semilla, contract-first por slice | Se autodeclara inicial. |
| OpenAPI | Seguridad objetivo | `/v1/events` POST | “Publicar evento” genérico | Eventos internos/autorizados | Crítica | No exponer publicación arbitraria; aceptar sólo comandos/webhooks tipados y firmados | Evita forgery e inyección de eventos. |
| OpenAPI | Contrato objetivo | Errores/autenticación | No definidos | 401/403/409/503 requeridos | Alta | Problem Details y semantics explícitas | Fail-closed verificable. |
| Nodes/Edges | XLSX/JSON entities | Evidence Graph | Grafo normativo de 153/731 | No contiene los 43 objetos de instancia | Media | Usarlo como catálogo/bootstrap, no grafo transaccional | La red es arquitectura/conocimiento, no datos tenant. |
| Mermaid/Draw.io | Nodes/Edges | Granularidad | Diagramas resumidos | Red de 153/731 | Baja | Ambas vistas son válidas para sus propósitos | No se exige equivalencia visual uno-a-uno. |
| LEEME | Evidencia del paquete | Baseline normativo | Dice FDIS “adjunto” | No hay FDIS separado entre los 10 archivos | Alta | Tratar la especificación/paráfrasis como fuente de producto; bloquear carga normativa licenciada/publicación final hasta obtener fuente controlada | No inventar texto normativo ni afirmar licencia. |
| DOCX/LEEME | Fecha normativa | ISO 9001:2026/FDIS | Baseline pre-publicación | Edición definitiva futura | Alta | `StandardEdition` con estado `draft/fdis`; re-baseline al publicar | Preserva historia y evita declarar final lo provisional. |

## Reconciliación por dominio

- **Normativa:** `Standard → StandardEdition → Clause → RequirementControl`; metodologías por `KnowledgeLayer → KnowledgeLayerRule → KnowledgeLayerBinding`. `StandardPack` activa aplicabilidad tenant sin clonar objetos empresariales.
- **Core:** una Organization, Site, Process, StakeholderRequirement, Risk, Opportunity, Objective, Change, Document/Evidence y CAPA; las normas se vinculan mediante bindings/coverage, nunca mediante tablas `RiskISO*`.
- **Evidence Graph:** los CSV son catálogo normativo. El grafo operativo se deriva de FKs/edges tipados tenant-scoped, con provenance y vigencia; no es otro system of record.
- **Agentes:** 33 capacidades declaradas; sólo 28 aparecen como nodos de agentes de cláusula. Las cinco transversales (`Normative Intelligence`, `Evidence Verifier`, `AI Governance Guardian`, `Autonomy Policy Engine`, `Learning Optimizer`) siguen siendo canónicas por DOCX/XLSX/JSON aunque la red visual no las incluya.
- **Onboarding:** 17 etapas canónicas. La autoridad de 1–7 es mayormente AdminApps; 8 es compartida; 9–17 pertenecen al producto/QMS, con validaciones de entitlement cuando corresponda.

## Decisiones y bloqueos resultantes

La reconciliación es suficiente para diseñar la foundation. No autoriza migrations masivas ni importar contenido normativo. Quedan como restricciones: obtener/validar la fuente normativa licenciada que el LEEME menciona como adjunta; certificar el servidor PostgreSQL real; acordar contratos/eventos AdminApps; y demostrar RLS en PostgreSQL efímero antes de cualquier dominio productivo.
