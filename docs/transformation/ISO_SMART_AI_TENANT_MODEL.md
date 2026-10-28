# ISO Smart AI — modelo objetivo de tenant

## Decisión

`Tenant` es un concepto lógico de las fuentes TO-BE, no una autorización para duplicar el control plane.

```text
AdminApps tenant/identity/entitlement/subscription authority
                  |
          immutable external IDs + source version/event
                  v
ISO Smart TenantProjection / UserProjection / EntitlementProjection
                  |
                  v
ISO Smart Organization / Site / QMS domain
```

`TenantProjection.id` es el UUID interno estable usado por FKs y RLS. `adminapps_tenant_id` es el identificador externo opaco e inmutable, `UNIQUE NOT NULL`. No se usa el ID externo directamente como PK para desacoplar lifecycle y permitir reconciliación sin reinterpretar identidad.

## TenantProjection

Campos mínimos de diseño: `id uuid`, `adminapps_tenant_id uuid/text`, `source_version bigint/text`, `source_event_id uuid`, `display_name_snapshot`, `lifecycle_status`, `entitlement_status`, `provisioning_status`, `last_synced_at`, `last_reconciled_at`, `reconciliation_status`, `reconciliation_error_code`, `suspended_at`, `deletion_requested_at`, `created_at`, `updated_at`. Los snapshots no son autoridad.

Constraints:

- `UNIQUE(adminapps_tenant_id)` y `UNIQUE(source_event_id)` cuando no nulo.
- source version sólo avanza; eventos viejos se reconocen sin revertir estado.
- `id` y `adminapps_tenant_id` son inmutables después de insert.
- toda Organization pertenece a exactamente un TenantProjection; una projection puede tener una o más Organization QMS sólo si producto lo aprueba explícitamente. Baseline: una principal.
- toda reasignación de `tenant_id` queda prohibida por el CRUD y por trigger/servicio defensivo.

## Lifecycle y comportamiento

| Estado local | Lectura QMS | Escritura QMS | Workers | Regla |
|---|---|---|---|---|
| `pending` | No | Sólo provisioning interno mínimo | Sólo provisioning idempotente | No emitir sesión de producto |
| `active` | Sí, sujeto a entitlement | Sí | Sí | Revalidación por riesgo/TTL |
| `suspended` | Default no; export autorizado separado | No | No, salvo reconcile/audit | Fail-closed |
| `deprovisioning` | Sólo export/retention autorizados | No | Sólo workflow de deprovisioning | No hard delete inmediato |
| `deleted_tombstone` | No | No | Reconcile/tombstone | Conservar mapping mínimo según policy |
| `drifted`/`unknown` | No para operaciones críticas | No | Sólo reconcile | 503 o 409 según causa |

Provisioning es una saga idempotente iniciada por evento AdminApps validado. Cada paso tiene checkpoint y no marca `active` hasta que projection, Organization base, roles QMS mínimos y policy estén consistentes. Suspensión revoca nuevas operaciones inmediatamente; no cambia ownership de filas existentes. Deletion es workflow legal/retention, no `CASCADE` genérico.

## Scope de entidades críticas

Todos estos agregados contienen `tenant_id NOT NULL` directo: Organization, Site, Process, Stakeholder, StakeholderRequirement, Risk, Opportunity, Objective, Change, Document, DocumentVersion, Evidence, EvidenceCoverage, Recommendation, RecommendationBasis, AgentRun, AgentDecision, DomainEvent, TransactionalOutbox, EventInbox, Approval, ActionExecution, EffectivenessCheck, Audit, Finding, Nonconformity, CorrectiveAction, StandardPack, QuizAttempt, ConceptMastery, onboarding instances y ImmutableAuditLog.

Las FKs compuestas `(tenant_id, referenced_id)` impiden grafos cruzados. Para catálogos globales se referencia el ID global y se registra la versión aplicable. Child tables que permanezcan sin tenant directo requieren una justificación y policy `EXISTS` contra el padre; son la excepción, no el baseline.

## Transferencia y reasignación

No existe `PATCH tenant_id`. Cada tabla tenant-scoped del POC instala un trigger `BEFORE UPDATE` no controlado por runtime que compara `OLD.tenant_id` y `NEW.tenant_id` con `IS DISTINCT FROM` y rechaza la reasignación con un SQLSTATE estable, independientemente de RLS. Una transferencia futura requiere una operación administrativa fuera del CRUD normal con: autorización dual, motivo, scope cerrado, preflight de grafo completo, snapshot/backup, plan de conflicto, ventana de bloqueo, transacción o saga compensable, hashes antes/después, evento dedicado, ImmutableAuditLog, reconcile y aprobación break-glass. Sin ese protocolo, el trigger rechaza cambios de tenant incluso al migration role fuera de una ventana explícita.

## Resolución de request y fail-closed

1. Validar identidad (firma, issuer, audience, lifetime).
2. Obtener tenant externo sólo de claims/contrato autorizado; nunca de body/query/header arbitrario. El POC puede sustituir AdminApps por un resolver sintético confiable que mapea identidad autorizada a una fixture TenantProjection, pero no acepta un tenant libre del request.
3. Resolver una única TenantProjection activa y coherente.
4. Validar entitlement según criticidad y max-staleness.
5. Abrir transacción, establecer tenant/actor/trace con contexto local a la transacción y ejecutar caso de uso.
6. Cerrar transacción; el pool no conserva contexto.

| Código | Uso |
|---:|---|
| 401 | Identidad ausente, inválida o expirada; no revelar estado tenant. |
| 403 | Identidad válida, pero entitlement/rol/policy niega la operación. |
| 409 | Evento/source version en conflicto, provisioning incompatible, idempotency key con payload diferente o intento de reasignación. |
| 503 | AdminApps requerido no validable, projection drift/unknown o reconciliación obligatoria indisponible; nunca convertir en allow. |

Los lookups de objetos fuera del tenant devuelven 404 cuando evita leakage; errores de FK de payload son 400 genéricos indistinguibles. Los códigos anteriores describen el boundary de autoridad, no la existencia de objetos privados.

## Onboarding y system of record

| # | Etapa | SoR | Representación/evento ISO Smart |
|---:|---|---|---|
| 1 | Plan Selection | AdminApps | Entitlement/plan snapshot; evento/inbox receipt |
| 2 | Account Registration | AdminApps | UserProjection mínima |
| 3 | Billing Contact | AdminApps | Ninguna PII adicional salvo referencia necesaria |
| 4 | Payment | AdminApps/payment provider | Receipt/status proyectado; nunca confirmación local |
| 5 | Payment Verification | AdminApps | Evento firmado y deduplicado |
| 6 | Subscription Activation | AdminApps | SubscriptionProjection/entitlement version |
| 7 | Tenant Provisioning | AdminApps inicia; ISO Smart ejecuta dominio local | TenantProjection + provisioning checkpoints + Organization base |
| 8 | Security Setup | AdminApps identity/MFA/global roles; ISO Smart QMS roles/privacy acceptance local | User/role projections + assignments/policy evidence |
| 9 | Foundation Gate | ISO Smart | LearningPath, QuestionBank, QuizAttempt, ConceptMastery, event |
| 10 | Organizational Profile | ISO Smart | Organization, Site, IndustryProfile binding |
| 11 | Value Discovery | ISO Smart | AgentRun/Recommendation/Basis (A0–A2) |
| 12 | Document/Data Ingestion | ISO Smart | DocumentVersion/Evidence/DomainEvent |
| 13 | Context Twin Baseline | ISO Smart | Context/Stakeholder/Process + evidence graph |
| 14 | Quality Baseline | ISO Smart | Risk/Opportunity/Objective/gaps |
| 15 | Human Validation | ISO Smart | Approval/AgentDecision/audit |
| 16 | Agents Activation | ISO Smart, bounded by AdminApps plan | StandardPack/agent policy assignments |
| 17 | First-Day Value | ISO Smart | Recommendation/Basis/roadmap snapshots |

## Reconciliation

Inbox deduplica `source_event_id`; upsert exige version monotónica. Un job periódico compara AdminApps → projections y clasifica `in_sync`, `stale`, `missing_local`, `unexpected_local`, `version_conflict` o `authority_unavailable`. Nunca “arregla” un conflicto reasignando datos. Métricas: projection lag, stale entitlement, duplicate/out-of-order events, reconcile failures, denied-on-drift y provisioning age.
