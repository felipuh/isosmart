# Phase 3 — Eventing + Immutable Audit Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 3 — EVENTING + IMMUTABLE AUDIT FOUNDATION`

**PostgreSQL run-id final:** `20260817T165135Z_13cfae`

**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó únicamente `foundation/0003_eventing_immutable_audit_foundation`. Las migrations `0001_foundation_tenant_projection` y `0002_projection_organization_user_foundation` no fueron editadas. Hashes finales: `0001=0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51`, `0002=1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537`, `0003=dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc`. `0003` es aditiva, vendor-aware, sin backfill, dual-write, cambios legacy ni despliegue. Su reversa elimina sólo objetos Phase 3 y conserva las tablas y el estado promovido de `0001 + 0002`.

PostgreSQL 18.6 real verificó desde DB vacía: `0001 → 0002 → 0003 → 0002 → 0003` PASS. La reversa final `0003 → 0002` dejó presentes `qms.tenant_projection`, `qms.organization` y `qms.user_projection`, y ausentes los schemas/tablas Phase 3 creados por la migration.

## 2. DomainEvent

`eventing.domain_event` es tenant-scoped y append-only: `event_id UUID PK`, `tenant_id UUID NOT NULL FK RESTRICT`, tipo/schema, agregado/id/versión, `occurred_at`, `recorded_at`, `trace_id`, correlation/causation opcionales, source, payload JSONB y `payload_hash` SHA-256. El payload JSONB está justificado como envelope de contrato versionado; identidad, routing, versiones, timestamps y hashes permanecen en columnas tipadas.

La tabla incluye índices tenant/recorded y tenant/aggregate, constraint de hash lowercase hexadecimal y `UNIQUE(tenant_id,event_id)` para soportar la FK compuesta del outbox. App recibe `SELECT/INSERT`; worker sólo `SELECT`; projector y audit writer no reciben DML. Runtime no recibe UPDATE/DELETE y un trigger defensivo rechaza ambas operaciones incluso por el owner ordinario de migrations.

## 3. TransactionalOutbox

`eventing.transactional_outbox` guarda UUID, tenant, `domain_event_id UNIQUE`, status, attempts, available time, lease owner/expiry, publish/error timestamps y timestamps de fila. No duplica payload. La FK compuesta `(tenant_id,domain_event_id) → DomainEvent(tenant_id,event_id)` impide ambigüedad y cruce tenant/evento.

State machine DB: `pending|failed → processing → published|failed`; un lease `processing` expirado puede reclamarse como `processing → processing`. Cada claim incrementa attempts exactamente una vez; completion no altera attempts. Published/failed preservan la fila e historial. Worker sólo puede actualizar columnas de delivery; no puede cambiar identidad/tenant/evento.

El dispatcher tenant-scoped usa `SELECT FOR UPDATE SKIP LOCKED`, lease de cinco minutos por defecto y recuperación de lease expirado. Entrega baseline: **AT LEAST ONCE**. No se introdujo broker.

## 4. Atomic write service

`OrganizationEventingService.rename` es el boundary reusable de esta slice. Abre el contexto tenant transaccional exterior y ejecuta, sin APIs públicas opcionales separadas:

1. lock y mutación de Organization;
2. insert de DomainEvent con versión de agregado;
3. insert de TransactionalOutbox para ese evento;
4. append audit mediante función controlada;
5. commit único.

Tenant, trace, agregado/entidad y event identity se propagan de forma consistente. Correlation y causation se preservan cuando existen. No se cambió el CRUD/endpoint legacy de Organization ni se expuso un event injection endpoint.

## 5. ConsumerReceipt / Inbox e idempotencia

`eventing.consumer_receipt` persiste UUID, tenant, consumer, event, payload hash, timestamps, status, attempts, error y trace. `UNIQUE(consumer_name,event_id)` es la defensa durable de deduplicación; tenant, event identity, consumer, trace y payload hash son inmutables.

Semántica probada:

- first `E/H1`: receipt durable, handler ejecutado una vez y status `processed`;
- replay `E/H1`: `idempotent_duplicate`, handler no ejecutado;
- substitution `E/H2`: conflicto interno 409 `PayloadIntegrityConflict`; receipt no cambia y no hay efecto.

## 6. Canonicalización y payload hashing

`iso-smart-canonical-json-v1` normaliza recursivamente valores admitidos, exige timestamps aware normalizados a UTC, rechaza floats/decimales no finitos y tipos/keys no soportados, y serializa UTF-8 con keys ordenadas, separators compactos y `allow_nan=False`. SHA-256 se calcula sobre ese texto. Un test demostró el mismo hash para objetos equivalentes con distinto orden de keys y hash distinto ante sustitución.

## 7. Replay

Replay es una operación explícita foundation-only, sin endpoint: requiere actor, event ID, consumer, trace y reason no vacío. Agrega `event.replay.requested` al audit mediante el writer controlado. Nunca borra ni sobrescribe ConsumerReceipt y no ejecuta automáticamente side effects externos.

## 8. ImmutableAuditLog y hash chain

`audit.immutable_audit_log` contiene UUID, tenant, stream type/id, sequence, actor, action, entity, trace, occurred time, before/after/payload/previous/entry hashes y metadata canónica mínima. `UNIQUE(tenant_id,stream_type,stream_id,sequence_number)` evita secuencias duplicadas.

`audit.append_immutable_audit` es `SECURITY DEFINER`, tiene `search_path` fijo, valida tenant contra `app.tenant_id`, campos obligatorios, formato de hashes, tamaño máximo y claves/patrones sensibles. El caller no proporciona sequence, previous hash, payload hash ni entry hash. La función toma un advisory transaction lock por tenant/stream, obtiene el tail, asigna la siguiente secuencia y calcula hashes con SHA-256 core de PostgreSQL 18.

Canonicalización chain `iso-smart-audit-chain-v1`: campos textuales length-prefixed UTF-8, null con marcador distinto, timestamp UTC con seis decimales y orden fijo: version, tenant, stream, sequence, previous, actor, action, entity, trace, timestamp, before/after/payload hash. Genesis usa `previous_entry_hash=NULL`.

Tres entries de Organization verificaron secuencias `1,2,3` y enlaces. Una copia con metadata modificada falló recomputación. Dos conexiones audit-writer concurrentes sobre el mismo stream produjeron exactamente secuencias `1,2` y cadena válida.

## 9. Append-only y permisos

App/worker/audit writer no tienen INSERT directo sobre audit ni UPDATE/DELETE/TRUNCATE. Sólo ejecutan el append function controlado. Un trigger defensivo rechaza UPDATE/DELETE y otro TRUNCATE. Intentos runtime de update, delete, truncate y forge directo de sequence/hash fueron denegados.

| Principal | Permisos Phase 3 |
|---|---|
| migrator | owner efímero/migration policy; no superuser/BYPASSRLS |
| app | DomainEvent SELECT/INSERT; Outbox SELECT/INSERT; Receipt/Audit SELECT tenant-scoped; audit append function |
| worker | DomainEvent SELECT; Outbox SELECT + delivery columns; Receipt SELECT/INSERT + transition columns; Audit SELECT + append function |
| projector | conserva sólo projection permissions Phase 2; cero permisos Phase 3 |
| audit_writer | `USAGE audit` + `EXECUTE append_immutable_audit`; cero DML directo |

Los cinco principals fueron LOGIN reales, non-superuser, `NOBYPASSRLS`, non-owner para runtime.

## 10. RLS, raw SQL, pool y worker

Las siete tablas foundation inspeccionadas (`TenantProjection`, `Organization`, `UserProjection` y las cuatro Phase 3) devolvieron simultáneamente `relrowsecurity=true` y `relforcerowsecurity=true`. Se inspeccionaron 28 policies totales. Cada tabla Phase 3 tuvo fixtures A/B visibles sólo bajo su tenant; app y worker sin tenant obtuvieron cero filas. Writes sin tenant fueron denegados.

Matriz Phase 3 final:

| Tabla | A con A | A con B | B con B | no tenant |
|---|---:|---:|---:|---:|
| DomainEvent | 3 | 0 | 1 | 0 |
| TransactionalOutbox | 3 | 0 | 1 | 0 |
| ConsumerReceipt | 1 | 0 | 1 | 0 |
| ImmutableAuditLog | 7 | 0 | 1 | 0 |

Raw SQL, conexión reutilizada `A → none → B`, rollback y worker `A/B/none` pasaron. Los GUC transaccionales desaparecieron tras commit y rollback. Cambios de tenant en las cuatro tablas fueron rechazados por triggers DB independientemente de RLS.

## 11. Pruebas bloqueantes

| Gate | Resultado |
|---|---|
| Atomic success | Organization + DomainEvent + Outbox + Audit commit; tenant/trace compartidos |
| Atomic deliberate failure | nombre original y conteos Event/Outbox/Audit intactos; cero persistencia parcial |
| Outbox retry | failure/reclaim/publish; attempts=2; row conservada |
| Outbox crash recovery | lease expirado reclamado por otro worker; attempts incrementado |
| Duplicate receipt | un solo business effect |
| Payload substitution | 409 interno; no overwrite/effect |
| Audit chain | 1→2→3 MATCH; tampered copy FAIL |
| Audit concurrency | dos conexiones; secuencias 1,2; chain MATCH |
| Audit tamper runtime | UPDATE/DELETE/TRUNCATE/direct forge DENIED |
| Tenant reassignment | cuatro tablas REJECTED por trigger DB |
| Projector restrictions | cero DML Phase 3 y cero nuevas business writes |

## 12. PostgreSQL, regresión e integridad Django

Corrida final: PostgreSQL `18.6 (Debian 18.6-1.pgdg13+2)`, `server_version_num=180006`, Podman, base/puerto únicos y cinco roles con sufijo `20260817t165135z13cfae`.

| Gate | Resultado |
|---|---|
| Backend completo | **115 PASS / 0 FAIL / 0 SKIP** |
| Delta vs baseline Phase 2 110 | **+5 tests legítimos** de contrato/canonicalización Phase 3 |
| Foundation unit suite | 17 PASS |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL migration/behavior/security | PASS |

Warnings legacy de paginación y telemetría Chroma/PostHog no produjeron failures ni skips.

## 13. Source integrity y teardown

Los diez SHA-256 recalculados coincidieron exactamente con `SOURCE_ARTIFACT_MANIFEST.md`: `8308bd…`, `e0a59c…`, `11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`, `eb4231…`: **10/10 MATCH**.

Teardown final: database y cinco roles exactos eliminados; container, volumen y directorio temporal ausentes. No se usó DB persistente/compartida, producción, staging, AdminApps DB ni MedSupplier DB. No hubo deployment, cambios `.env`, secrets ni cambios a repos externos.

`git diff --check` global conserva un único hallazgo preexistente en `frontend/src/components/Layout/Sidebar.jsx:28`; fue observado en la entrada Phase 2 y se preservó por instrucción. Los archivos Phase 3 no contienen whitespace terminal.

## 14. Event injection y límites

No existe `POST /v1/events` en esta slice. El artefacto OpenAPI TO-BE que sugiera un endpoint genérico requiere hardening/rediseño como comandos autorizados o webhooks tipados, firmados, rate-limited e idempotentes antes de cualquier exposición. No se implementaron broker, transport AdminApps, Process, Risk, Evidence, normativa, backfill, dual-write ni producción.

## 15. Riesgos residuales

1. La foundation es append-only para runtime y tamper-evident; un DBA privilegiado aún puede alterar historia. Faltan checkpoints firmados/export WORM y verifier operativo.
2. No existe transport/broker real, firma de ingress, publisher scheduling, DLQ/alerting productivo ni SLO/load test. PostgreSQL conserva la durabilidad y leases baseline.
3. Retention, privacy exceptions, backup/restore de event/audit y break-glass productivos requieren aprobación Legal/Security/Operations.
4. El vocabulario implementado cubre sólo `organization.renamed`; cada nuevo evento necesita schema versionado y contract tests.
5. El filtro de secretos reduce riesgo en metadata, pero no sustituye clasificación/DLP ni revisión de todos los futuros payload producers.
6. Roles/credentials/bootstrap productivos siguen fuera de alcance; los principals demostrados fueron efímeros.

No quedan P0 ni P1 bloqueando la siguiente vertical slice.

## 16. Veredicto

**PHASE 3 — EVENTING + IMMUTABLE AUDIT FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001_foundation_tenant_projection` | FROZEN / INTACTO | SHA-256 histórico preservado; no editado | Evolucionar sólo 0004+ |
| `0002_projection_organization_user_foundation` | PROMOTED / INTACTO | reversa 0003 conservó sus tres tablas | No reescribir |
| `0003_eventing_immutable_audit_foundation` | PROMOTED | forward/reverse/forward PostgreSQL 18.6 | Congelar tras promoción |
| DomainEvent | PROMOTED FOUNDATION | append-only + hash + A/B/none | Añadir contratos tipados por dominio |
| TransactionalOutbox | PROMOTED FOUNDATION | SKIP LOCKED + lease/retry/publish | Añadir operación/metrics/DLQ futura |
| ConsumerReceipt | PROMOTED FOUNDATION | duplicate y substitution gates PASS | Añadir consumers reales tipados |
| ReplayService | FOUNDATION-ONLY | request auditado; receipt preservado | Human gate/upcasters futuros |
| ImmutableAuditLog | PROMOTED FOUNDATION | controlled append, chain y concurrency PASS | External checkpoint/WORM futuro |
| Runtime principals | TESTED FOUNDATION | cinco LOGIN; no owner/superuser/BYPASSRLS | Bootstrap productivo separado |
| RLS/tenant immutability | PASS | ENABLE+FORCE, 28 policies, triggers, raw SQL | Repetir por toda entidad nueva |
| Backend/Django | PASS | 115/0/0; check/drift/compile | Mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | Preservar byte-for-byte |
| Recursos efímeros | REMOVED | teardown PASS | Ninguna acción |
