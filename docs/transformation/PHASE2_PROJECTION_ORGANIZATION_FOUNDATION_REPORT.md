# Phase 2 — Projection + Organization Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 2 — PROJECTION + ORGANIZATION FOUNDATION`

**PostgreSQL run-id final:** `20260817T162942Z_cd2b68`

**Veredicto:** **PROMOTED**

## Alcance y evolución de migrations

Se agregó únicamente `foundation/0002_projection_organization_user_foundation`. La migration congelada `0001_foundation_tenant_projection` conserva SHA-256 `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51`, idéntico antes y después de esta corrida. `0002` es aditiva, vendor-aware, sin backfill, dual-write, alteración legacy ni `DROP` destructivo de datos preexistentes. Su reversa elimina sólo los objetos vacíos de Phase 2 y conserva `qms.tenant_projection` y la foundation `0001`.

Evidencia real: `0001 → 0002 → 0001 → 0002` PASS; reversa final `0002 → 0001` PASS. PostgreSQL confirmó `tenant_projection` presente y `organization/user_projection` ausentes después de cada reversa de esta slice.

## Projection event contract y fixtures

El envelope interno versionado exige `event_id`, `event_type`, `schema_version`, `source`, `source_version`, `occurred_at`, `trace_id`, `aggregate_type`, `aggregate_id`, `adminapps_tenant_id`, `payload` y `correlation_id` opcional. Sólo acepta schema `1`, source `adminapps`, UUIDs válidos y timestamps timezone-aware. Valida la correspondencia tipo/agregado y el payload antes de escribir.

Vocabulario mínimo provisional: `tenant.provisioned`, `tenant.updated`, `tenant.suspended`, `user.updated`, `user.revoked`. No se declara contrato compartido final ni transporte real. Los fixtures internos cubren evento válido tenant/user, replay, avance, conflicto misma versión, versión inferior, payload malformado, schema incorrecto y tipo desconocido.

## Boundary AdminApps y failure semantics

`ContractOnlyAdminAppsAdapter` implementa `envelope → validation/DTO → ProjectionWriterService` sin HTTP, secrets, consulta o DB AdminApps. AdminApps permanece como SoR de tenant, identidad, MFA, roles globales, plan, entitlement, subscription, billing y provisioning authority. ISO Smart sólo materializa projections trazables; `Organization` es dominio QMS.

Semántica interna explícita y testeada: 401 authentication invalid, 403 authorization/entitlement denied, 409 projection/version/immutability conflict, 422 contract invalid y 503 authority unavailable/drift fail-closed. No se expusieron endpoints nuevos.

## Projection writer y principal

El harness creó cuatro LOGIN únicos: migrator, app, worker y `foundation_projector_<runid>`. Todos fueron `LOGIN`, `NOSUPERUSER`, `NOBYPASSRLS`; app/worker/projector no fueron owners. El projector recibe `USAGE qms` y únicamente `SELECT/INSERT/UPDATE` sobre `TenantProjection` y `UserProjection`; no recibe `DELETE` ni DML sobre `Organization`.

Las policies del projector requieren además `app.projection_source = adminapps` con scope local de transacción. Una escritura conectada como projector sin esa operación confiable fue denegada por RLS. App y worker conservaron `SELECT` solamente en ambas projections y los seis intentos de `INSERT/UPDATE/DELETE` por tabla/rol fueron denegados.

## Idempotencia, versiones y transacción

El writer acepta exclusivamente un `ProjectionEvent` validado. Cada evento abre una transacción propia, fija source/trace local, adquiere locks transaccionales por `event_id` y aggregate, interpreta y aplica. Esto serializa replay/conflicto concurrente y evita convertir la semántica normal en un `IntegrityError` opaco.

Resultados TenantProjection y UserProjection:

- evento E versión N: `applied`;
- E/N repetido: `idempotent_replay`, sin mutación;
- evento distinto en N: 409 `source_version_conflict`;
- versión inferior: 409 `source_version_regression`;
- versión superior: valida transición y aplica atómicamente;
- reutilización conflictiva de event identity: conflicto explícito.

La DB sigue siendo última defensa: triggers rechazaron downgrade de `source_version` en TenantProjection y UserProjection. Un evento de transición inválida versión 3 falló; una lectura posterior confirmó versión 2 y snapshot anterior intactos. Rollback completo PASS.

## Organization foundation

Schema greenfield: UUID interno PK, `tenant_id uuid NOT NULL` FK `RESTRICT` a TenantProjection, `display_name`, `legal_name` nullable y timestamps. No contiene `adminapps_tenant_id`, billing, subscription, MFA, global permissions, plan ni metadata control-plane. No se impuso `UNIQUE(tenant_id)`, por lo que la baseline puede crear una organización principal sin bloquear una cardinalidad futura aprobada.

El trigger DB `foundation_organization_tenant_immutable` rechaza cambios de UUID interno y `tenant_id` con SQLSTATE `23514`, incluso ejecutado por migrator bajo una policy permisiva; por tanto la prueba es independiente de RLS.

Organization usa `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` y policies separadas. App tiene SELECT/INSERT/UPDATE/DELETE scoped; worker SELECT/INSERT/UPDATE scoped y no DELETE; projector no tiene acceso de negocio.

| Matriz Organization | Resultado |
|---|---|
| App A crea/lee/actualiza/elimina A | PASS |
| App A lee B | invisible |
| App A actualiza/elimina B | 0 rows |
| App A inserta con tenant B | RLS denied |
| App sin tenant SELECT/UPDATE/DELETE | cero filas |
| App sin tenant INSERT | RLS denied |
| Worker A/B/none | PASS scoped; DELETE denied por grant |
| `tenant_id A → B` | trigger denied independientemente de RLS |
| Raw SQL/pool reuse/rollback | PASS |

## UserProjection skeleton

Schema: UUID interno PK, `adminapps_user_id UUID UNIQUE NOT NULL` inmutable, `tenant_id UUID NOT NULL` FK `RESTRICT`, `source_version`, `source_event_id UNIQUE NOT NULL`, lifecycle mínimo (`active/suspended/revoked/deleted_tombstone`), `last_synced_at` y timestamps. El contrato actual mantiene una asociación tenant inmutable; una identidad multi-tenant futura requerirá una association projection dedicada y migration posterior, no una transferencia inventada.

No contiene password/hash usable, MFA secret, tokens, global role, entitlement ni billing. No es `AUTH_USER_MODEL`, no autentica credenciales y su existencia no concede autorización. Tests de modelo y contrato cubren estas aserciones negativas.

UserProjection usa ENABLE+FORCE RLS. App/worker son read-only y A/B/none resultó A-only/B-only/zero. Projector tiene write mínimo condicionado por source transaccional. Triggers rechazaron cambio de `adminapps_user_id`, cambio de tenant y downgrade de versión.

## PostgreSQL 18.6 y catálogos

Run final `20260817T162942Z_cd2b68`, imagen oficial PostgreSQL `18.6 (Debian 18.6-1.pgdg13+2)`, `server_version_num=180006`. Catálogo:

- `organization`, `tenant_projection`, `user_projection`: `relrowsecurity=true`, `relforcerowsecurity=true`;
- owner de las tres: migrator efímero;
- cuatro principals LOGIN reales;
- app/worker/projector: non-superuser, no BYPASSRLS, non-owner;
- 15 policies explícitas de Phase 1 + Phase 2;
- projector sin DELETE de projections y sin INSERT/UPDATE/DELETE de Organization.

TenantProjection, Organization, UserProjection, raw SQL, worker, A/B/none, misma conexión A→none→B y reuse tras rollback: PASS. Tenant context público continúa sin parámetros `tenant_id/body/query/header` y el contexto desapareció al commit/rollback.

## Regresión, Django e integridad

| Gate | Resultado |
|---|---|
| Backend completo | **110 PASS / 0 FAIL / 0 SKIP** |
| Diferencia vs baseline 101 | **+9 tests legítimos** (12 foundation actuales vs 3 baseline) |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation foundation | PASS |
| PostgreSQL forward/reverse/forward | PASS |
| Whitespace de archivos Phase 2 | PASS |
| `git diff --check` global | Hallazgo preexistente: `Sidebar.jsx:28`; preservado por instrucción |

Los warnings legacy de paginación y telemetría PostHog/Chroma no produjeron failures o skips.

## Source artifacts, teardown y límites

Los diez hashes recalculados coincidieron exactamente con el manifest: `8308bd…`, `e0a59c…`, `11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`, `eb4231…`: **10/10 MATCH**.

Teardown final PASS: database y cuatro roles exactos eliminados; container, volumen y temp context ausentes. No se usó DB persistente/compartida, production, staging, AdminApps DB ni MedSupplier DB. No se modificó `.env`, no se agregaron secrets y no hubo deployment ni cambios a repos externos. Los cambios preexistentes, incluido `Sidebar.jsx`, no se atribuyen a Phase 2.

## Riesgos residuales

1. No existe aún transporte autenticado/firmado ni integración real AdminApps; el adapter es contract-only.
2. El vocabulario de eventos es provisional hasta consumer contract testing entre repositorios.
3. No existe historial durable Inbox/ConsumerReceipt ni payload hash; la deduplicación material actual conserva el último `source_event_id` por projection. La siguiente slice debe resolver replay histórico y payload substitution con Inbox/receipt.
4. La asociación tenant de UserProjection refleja el contrato actual; multi-tenancy de identidad requiere modelado explícito posterior.
5. Se probó reuse de conexión Django, no un pooler externo productivo.
6. Roles/credentials productivos y operación/backup/restore siguen fuera de alcance.

No quedan P0 ni P1 bloqueando la progresión. No se implementó EntitlementProjection: TenantProjection existente, UserProjection existente u Organization existente no implican subscription activa, entitlement ni acceso de producto.

## Veredicto

**PHASE 2 — PROJECTION + ORGANIZATION FOUNDATION: PROMOTED**

Todos los gates bloqueantes pasaron: 0001 intacta; evolución 0002+; writer aislado; app/worker read-only en projections; replay/conflict/downgrade/rollback; Organization tenant-scoped, inmutable y FORCE RLS; UserProjection sin autoridad de autenticación y aislada; LOGIN reales; raw SQL/pool/worker; forward/reverse; regresión 110/0/0; drift; hashes 10/10 y teardown.

| Componente/archivo | Estado | Evidencia | Riesgo/acción siguiente |
|---|---|---|---|
| `0001_foundation_tenant_projection` | FROZEN / INTACTO | SHA-256 `0d72f2…` | Evolucionar sólo 0003+ |
| `0002_projection_organization_user_foundation` | PROMOTED | forward/reverse/forward PostgreSQL 18.6 | Conservar reversibilidad |
| Projection contract/fixtures | INTERNAL PROVISIONAL | 12 foundation tests + malformed/unknown gates | Formalizar contrato compartido futuro |
| Projection writer | PROMOTED BOUNDARY | apply/replay/conflict/lower/higher/rollback PASS | Añadir Inbox/receipt y payload hash |
| Projector LOGIN/policies | TESTED FOUNDATION | catálogo/grants/RLS real | Diseñar bootstrap productivo separado |
| Organization | PROMOTED FOUNDATION | A/B/none + CRUD + immutable trigger | Provisioning QMS futuro, sin backfill aún |
| UserProjection | PROMOTED SKELETON | A/B/none + identity/version triggers | Modelar membership multi-tenant si contrato lo exige |
| AdminApps adapter | CONTRACT-ONLY | cero transporte/DB/secrets | Integración autenticada futura |
| Backend/Django | PASS | 110/0/0; check/drift/compile | Mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 | Preservar byte-for-byte |
| Recursos efímeros | REMOVED | teardown PASS | Ninguna acción |
