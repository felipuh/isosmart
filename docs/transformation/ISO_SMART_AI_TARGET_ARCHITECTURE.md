# ISO Smart AI — arquitectura objetivo

## Forma general

Monolito modular Django/DRF + React, PostgreSQL como sistema transaccional, Celery/Redis inicialmente para trabajo asíncrono, y AdminApps como control plane. La evolución usa expand/contract y adaptadores; ningún bounded context se convierte en microservicio sin necesidad medida.

```text
AdminApps (identity/tenant/entitlement/billing SoR)
          | signed contract + idempotent projections
          v
API / Use cases / Policy enforcement / Tenant context
          |
  +-------+-------------------------+
  | Harmonized Core                 |
  | Normative Knowledge             |
  | Quality Operations              |
  | Evidence & Assurance            |
  | Learning & Onboarding           |
  | AI Runtime & Governance         |
  | Integration & Eventing          |
  +-------+-------------------------+
          | transaction + outbox
          v
PostgreSQL (RLS) -> dispatcher -> consumers/Redis workers
          |
          v
React capability UI + generated client + shared design system
```

## Bounded contexts

1. **Control-plane projection**: TenantProjection, UserProjection, EntitlementProjection, sync ledger. No billing authority.
2. **Harmonized Core**: Organization QMS, Site, Process, Stakeholder/Requirement, Risk, Opportunity, Objective, Change, Document/Version.
3. **Normative Knowledge**: Standard, Edition, Clause, RequirementControl, KnowledgeLayer/Rule/Binding, StandardPack, IndustryProfile.
4. **Evidence & Assurance**: Evidence, EvidenceCoverage, Audit, Finding, Nonconformity, CorrectiveAction, EffectivenessCheck, immutable log.
5. **Quality Intelligence**: Recommendation/Basis, signals, measurements and deterministic evaluation.
6. **AI Runtime & Governance**: AgentDefinition/Run/Decision, ModelPolicy, autonomy, approvals and actions.
7. **Learning & Onboarding**: workflow instance/transition plus LearningPath, QuestionBank, QuizAttempt, ConceptMastery.
8. **Integration & Eventing**: DomainEvent, OutboxMessage, ConsumerReceipt, webhook inbox, trace propagation.

Dependencies point inward to domain/application ports. Cross-context references use stable UUIDs and application services, not direct cyclic imports.

## Compliance Evidence Graph

El grafo es una vista de relaciones del dominio, no un segundo sistema de verdad. Tipos mínimos de enlaces:

- `RequirementControl --governed_by--> KnowledgeLayerRule`
- `RequirementControl --applies_to--> Process|StakeholderRequirement|Risk|Objective`
- `Evidence --covers--> EvidenceCoverage --for--> RequirementControl`
- `Recommendation --based_on--> RecommendationBasis --references--> Evidence|Rule`
- `AgentRun --produced--> Recommendation|AgentDecision`
- `AgentDecision --requires/uses--> Approval`
- `Approval --authorizes--> ActionExecution`
- `ActionExecution --measured_by--> EffectivenessCheck`
- `Audit --creates--> Finding --may_create--> Nonconformity --resolved_by--> CorrectiveAction`

Cada edge material guarda tenant, tipo, timestamps de efectividad, provenance y versiones aplicables. PostgreSQL con FK/índices, vistas y `WITH RECURSIVE` es la primera implementación. Evaluar una graph DB solo si perfiles reales incumplen SLO acordado pese a índices/materialized views.

## Event-driven architecture

`Domain operation → DB transaction(domain rows + DomainEvent + OutboxMessage) → commit → dispatcher → consumer`.

- Event envelope: UUID, type/version, aggregate type/id/version, tenant, occurred_at, trace/correlation/causation IDs, producer, payload/schema version.
- Dispatcher usa leases y backoff; publicar al menos una vez.
- Consumer registra `ConsumerReceipt(event_id, consumer)` con unique constraint antes/atómicamente con efectos.
- Poison messages pasan a estado dead-letter observable; replay es explícito y auditado.
- AdminApps produce `payment.confirmed` y `tenant.provisioned`; ISO Smart no los redefine.

## Agent runtime

Pipeline común de 12 pasos definido en ADR-0005. Los motores existentes se adaptan detrás de puertos:

- deterministic rule evaluator;
- retriever con namespace/dataset versionado;
- model inference adapter;
- policy/autonomy evaluator;
- human decision gate;
- action executor allow-listed;
- effectiveness evaluator.

Una respuesta degradada local debe etiquetarse `non_authoritative`; nunca sustituye consejo material con provenance. A4 exige acción reversible, límites de impacto, kill switch, observabilidad, preautorización vigente y rollback probado.

## API y frontend

- OpenAPI versionado, errores Problem Details, cursor o paginación consistente, filters allow-listed e `Idempotency-Key` en comandos retryables.
- Cliente TypeScript generado; capa query/cache compartida. No duplicar DTOs manualmente.
- Rutas y features por capability. Shell/lazy loading actuales se conservan.
- Shared design system para dialog, drawer, forms, tables, loading y feedback. Migración incremental de componentes locales.
- `NormativeIntelligenceDrawer` consume un endpoint de explanation/provenance; progressive disclosure muestra requisito, layers, evidencia/hashes, agente/modelo/versiones, regla, confianza, supuestos/limitaciones, autonomía, aprobación y cobertura del graph.
- Onboarding UI renderiza estado, razones de bloqueo y comandos permitidos por backend; nunca decide transición ni hace fail-open.

## Seguridad

- AdminApps MFA/identity; ISO Smart valida audience/issuer/signature/lifetime y revalida entitlement en puntos críticos.
- RBAC para roles estables; ABAC para site, ownership, sensitivity, workflow state y autonomy. Default deny.
- RLS + aplicación + object permissions para impedir IDOR/tenant escape.
- Browser auth objetivo: sesión/cookie HttpOnly o BFF coherente con AdminApps; si JWT se mantiene temporalmente, CSP estricta, rotación/revocación y reducción de exposición en storage.
- Upload pipeline: tamaño/extensión, magic-byte MIME, nombre seguro, cuarentena, malware scanner port, object key no predecible, URL firmada y authorization en cada descarga.
- SSRF egress allow-list para retrievers/webhooks; webhook signature + timestamp/nonce; rate limits distribuidos.
- Logs estructurados con redaction; secretos en secret manager; TLS y cifrado de storage/backup según clasificación.

## SRE por ambiente

- Dev: servicios locales aislados, datos sintéticos, fallback visible permitido solo por flag.
- Test/CI: PostgreSQL real para RLS/migrations además de unit SQLite; servicios externos simulados por contrato.
- Staging: topología product-like, AdminApps sandbox, restore/migration/rollback drills.
- Production: HA según SLO, backups + PITR, pools/connections presupuestados, workers autoscaling por queue depth.

Separar `/health/live` (proceso) de `/health/ready` (DB y dependencias obligatorias con política explícita). Métricas mínimas: latencia/error/saturation, DB pool/locks, queue depth/age/retries/DLQ, outbox lag, AdminApps availability/denials, agent latency/cost/confidence/approval/effectiveness. OpenTelemetry preserva `trace_id` API→DB/event→worker→provider.

## Quality gates

No avanzar una fase si fallan: contrato AdminApps fail-closed; OpenAPI diff breaking; migration forward/backward/backfill; RLS escape; provenance completeness; Human Gate; lint/type/build; a11y; security regression; restore drill correspondiente al release.
