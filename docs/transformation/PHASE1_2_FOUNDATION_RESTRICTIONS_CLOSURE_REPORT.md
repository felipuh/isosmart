# Phase 1.2 — Foundation Restrictions Closure & Permanent Baseline

**Fecha:** 2026-08-17

**Gate:** `ENTERPRISE FOUNDATION BASELINE`

**PostgreSQL run-id final:** `20260817T160458Z_ac48c0`
**Veredicto:** **PROMOTED**

Esta fase cerró exclusivamente las restricciones de foundation. No introdujo Organization, UserProjection, EntitlementProjection, billing, QMS business objects, adapters/event consumers AdminApps, backfill, dual-write ni deployment.

## 1. Migration replacement y evidencia Option B

| Elemento | Resultado |
|---|---|
| OLD | `0001_tenant_rls_poc` |
| NEW | `0001_foundation_tenant_projection` |
| Decisión | Option B: replacement pre-release controlado |
| Motivo | La migration POC creaba/destruía roles cluster-scoped, contenía `SyntheticTenantChild` y usaba cleanup global no apto para una DB compartida |

La condición habilitante no se asumió silenciosamente. Los reportes Phase 1 y 1.1 registran que la migration anterior se aplicó sólo en bases PostgreSQL efímeras cuyos contenedores, volúmenes, imágenes POC y temporales fueron destruidos y cuya ausencia se verificó. Phase 1.1 declara explícitamente que no existía production, staging ni shared DB con esa migration. La 0001 permanecía además en un árbol pre-release sin baseline publicada. No se contactó ni inspeccionó ninguna DB compartida para esta decisión.

La nueva migration es vendor-aware para preservar SQLite legacy, aditiva sobre una DB vacía, no altera tablas legacy, no hace backfill ni dual-write y no depende de datos reales. Su reversa elimina por nombre sólo `qms.tenant_projection`, su trigger/función y el marker de ownership de la migration. `DROP SCHEMA qms` se ejecuta sin `CASCADE` únicamente si la propia migration creó el schema y éste quedó vacío. No crea, revoca ni elimina roles o extensiones.

## 2. FOUNDATION MIGRATION FREEZE POINT

**FOUNDATION MIGRATION FREEZE POINT: ACTIVO desde el PASS final de este reporte.**

`0001_foundation_tenant_projection` queda congelada. No se reescribe después de este punto. Cualquier evolución futura se implementará exclusivamente como `0002+`, `0003+`, etc., con estrategia expand/contract. Esta regla entra en vigor antes de introducir Organization.

## 3. TenantProjection permanente

Schema permanente:

- `id uuid` PK interno;
- `adminapps_tenant_id uuid NOT NULL UNIQUE`, externo e inmutable;
- `source_version bigint NOT NULL`, no negativo y monotónico no decreciente;
- `source_event_id uuid UNIQUE NULL`;
- `display_name_snapshot varchar(255) NOT NULL`;
- `lifecycle_status varchar(32) NOT NULL`;
- `provisioning_status varchar(32) NOT NULL`;
- `reconciliation_status varchar(32) NOT NULL`;
- `reconciliation_error_code varchar(64) NULL`;
- `last_synced_at timestamptz NOT NULL`;
- `last_reconciled_at`, `suspended_at`, `deletion_requested_at` como `timestamptz NULL`;
- `created_at`, `updated_at` como `timestamptz NOT NULL`.

No se agregó `Organization`, `UserProjection`, `EntitlementProjection`, campos de billing ni campos QMS. `entitlement_status` POC se retiró porque la autoridad de entitlements tendrá una proyección separada futura y no debe quedar duplicada en TenantProjection.

## 4. Estados y constraints

Los valores se formalizaron como `TextChoices` en aplicación y `CHECK` equivalentes en PostgreSQL:

- lifecycle: `pending`, `active`, `suspended`, `deprovisioning`, `deleted_tombstone`, `drifted`, `unknown`;
- provisioning: `pending`, `partial`, `complete`, `failed`, derivados de la saga/checkpoint aprobada (pendiente, parcial no activa, resultado completo o fallido);
- reconciliation: `in_sync`, `stale`, `missing_local`, `unexpected_local`, `version_conflict`, `authority_unavailable`.

La matriz ejecutó updates negativos con `invalid` para los tres campos y PostgreSQL rechazó cada uno por check constraint. `source_version >= 0` tiene constraint independiente.

## 5. Inmutabilidad y monotonicidad

El trigger `foundation_tenant_projection_protected_change` usa `BEFORE UPDATE`, `search_path` fijo y SQLSTATE `23514` para:

- rechazar cambios de `id`;
- rechazar `adminapps_tenant_id X → Y`;
- rechazar `NEW.source_version < OLD.source_version`.

La matriz sembró versión 5 y confirmó que versión 4 fue rechazada. La semántica de replay/conflict para igual versión y la aceptación funcional de versiones mayores quedan deliberadamente en el futuro projector; no se implementó un writer AdminApps en esta fase.

## 6. Roles, bootstrap y permisos

La responsabilidad quedó separada:

- **cluster/test bootstrap:** crea LOGIN roles únicos por run y una DB exclusiva;
- **Django migration:** crea tabla, constraints, trigger, ENABLE+FORCE RLS, policies y grants sobre sus propios objetos.

Principals finales:

- `foundation_migrator_20260817t160458zac48c0`;
- `foundation_app_20260817t160458zac48c0`;
- `foundation_worker_20260817t160458zac48c0`.

Los tres fueron `rolcanlogin=true`; app y worker fueron `rolsuper=false`, `rolbypassrls=false` y no owners. La tabla perteneció al migrator. No se usó `SET ROLE`: cada superficie abrió conexión propia con su principal LOGIN. App/worker recibieron únicamente `USAGE` de schema + `SELECT` de TenantProjection; `INSERT`, `UPDATE` y `DELETE` resultaron falsos en `has_table_privilege` y fallaron por permisos. El migrator efímero tuvo una policy explícita controlada para migrations/fixtures. No se creó integration role productivo.

El teardown hizo `DROP DATABASE` y `DROP ROLE` sólo sobre los nombres exactos del run-id. No usa `DROP OWNED`, globs, `prune`, `DROP SCHEMA CASCADE` ni roles genéricos.

## 7. RLS y matriz de seguridad

PostgreSQL oficial reportó:

- `SHOW server_version`: `18.6 (Debian 18.6-1.pgdg13+2)`;
- `SHOW server_version_num`: `180006`;
- `SELECT version()`: PostgreSQL 18.6, 64-bit;
- `relrowsecurity=true` y `relforcerowsecurity=true`;
- owner: migrator efímero, distinto de app/worker;
- policy SELECT: app + worker;
- policy ALL: sólo migrator efímero controlado.

| Assertion | Resultado |
|---|---|
| TenantProjection A ve A / no B | PASS |
| TenantProjection B ve B / no A | PASS |
| TenantProjection sin contexto | PASS, cero filas |
| App/worker INSERT/UPDATE/DELETE projection | PASS, denegado |
| Synthetic child A/B/none | PASS simétrico |
| Wrong-tenant child INSERT | PASS, RLS denial |
| Child `tenant_id` mutation | PASS, trigger denial |
| Raw SQL | PASS bajo RLS |
| Misma conexión A → none → B | PASS: `[[A only], [], [B only]]` |
| Rollback A → none → B | PASS: `[[], [B only]]` |
| Worker A/B/none | PASS |
| External ID mutation | PASS, trigger denial |
| Source version decrease | PASS, trigger denial |
| Invalid lifecycle/provisioning/reconciliation | PASS, constraints |

## 8. Contexto permanente y spoof boundary

`trusted_tenant_context` permanece como boundary transaccional outermost:

- rechaza ejecución dentro de otro atomic block;
- abre `transaction.atomic()`;
- llama al setter privado `_set_transaction_context`;
- usa parámetros y `set_config(..., true)` para tenant/actor/trace;
- verifica inmediatamente el tenant establecido;
- desaparece al commit y rollback.

El resolver sintético fue eliminado del módulo runtime. Las pruebas de boundary verifican que no existe `SyntheticTrustedTenantResolver`, que no existe API pública `set_tenant_context` y que la firma pública no acepta `tenant_id`, `body`, `query` o `header`. No se creó endpoint HTTP sólo para el test. Alcance exacto: prueba de import/callability + servicio + ejecución PostgreSQL del contexto con una `TrustedTenantIdentity` ya resuelta.

Boundary documentado:

`AUTHENTICATED IDENTITY → AUTHORIZED ADMINAPPS/LOCAL PROJECTION CONTEXT → TrustedTenantIdentity → trusted_tenant_context → PostgreSQL transaction context`.

Body, query y headers nunca alimentan el setter.

## 9. Componentes sintéticos

`SyntheticTenantChild` fue eliminado de models y migrations permanentes. El harness crea `qms.foundation_test_tenant_child`, instala FK, trigger, ENABLE+FORCE RLS, cuatro policies y grants; luego la elimina antes de la reversa final. El catálogo final confirmó que no existía. El resolver sintético fue removido por completo; el harness usa UUIDs internos fijos sólo como fixtures, no un resolver runtime.

## 10. Harness reproducible y lifecycle

`postgres_foundation_gate.py` automatiza:

`official 18.6 pull/fallback source+SHA → container+volume → readiness → LOGIN roles+DB → forward → reverse → forward → fixture+seed → security matrix → fixture drop → final reverse → DB/roles drop → container/volume/temp teardown → absence verification`.

El tag oficial `postgres:18.6` ya estuvo disponible en la corrida final, por lo que se usó la imagen oficial. El fallback permanece fijado a source HTTPS oficial y SHA-256 `983ee554ec53dbeb9b70797bef9fcf4e67e117e7e48ca1463cc80b3ff8e8ff3f`. Cualquier fallo bloqueante retorna non-zero y el `finally` siempre ejecuta teardown.

Intentos no PASS registrados durante desarrollo del harness: readiness por layout de volumen, suffix Debian en `server_version` y seeds inicialmente bloqueados por FORCE RLS. Todos finalizaron con teardown PASS antes del siguiente intento. Sólo run-id `20260817T160458Z_ac48c0` cuenta como evidencia PASS final; reemplazó una corrida PASS previa al añadir DML real completo para app/worker y escritura sin contexto.

## 11. Forward/reverse

Contra DB vacía:

1. forward y catálogo: PASS;
2. reverse: PASS, tabla y schema propios ausentes;
3. forward nuevamente: PASS;
4. suite final: PASS;
5. fixture sintética eliminada;
6. reverse final: PASS.

No se tocó ningún objeto externo, tabla legacy, schema compartido, extensión o rol preexistente.

## 12. Backend y Django integrity

| Gate | Resultado |
|---|---|
| Suite backend completa | **101 PASS / 0 FAIL / 0 SKIP** |
| Diferencia vs baseline 98 | +3 tests legítimos de foundation boundary |
| Duración interna | 3.244 s |
| Duración pared | 14.95 s |
| `manage.py check --settings=backend.settings_test` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation `foundation` | PASS |
| SQLite safety | PASS; migration PostgreSQL es no-op vendor-aware |

Los warnings de paginación sin ordering y los reintentos de telemetría PostHog/Chroma son preexistentes y no produjeron failures/skips. `backend/test_default.sqlite3` no fue modificado manualmente ni se atribuye a Phase 1.2.

## 13. Source integrity

Los diez SHA-256 fueron recalculados en el orden del manifest: `8308bd…`, `e0a59c…`, `11c2b4…`, `952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`, `eb4231…`.

Resultado: **10/10 MATCH**. Ningún source artifact fue modificado.

## 14. Teardown y alcance

Resultado final:

- database efímera eliminada;
- tres roles LOGIN del run eliminados y ausencia comprobada antes de destruir el cluster;
- synthetic table y funciones test-only eliminadas;
- container ausente;
- volume ausente;
- temp build context ausente;
- sin production, staging, shared DB, AdminApps DB ni MedSupplier DB;
- sin `.env`, secretos persistidos ni DSN/password impreso;
- sin cambios a `adminapps`, `ISO_Smart_MedSupplier` o `design-system`;
- sin deployment.

La imagen oficial local es una dependencia cacheable del engine y no contiene estado, DB, roles ni secretos. Los recursos PostgreSQL stateful de la corrida quedaron ausentes.

## 15. Clasificación final

| Componente | Clasificación | Evidencia | Próxima acción |
|---|---|---|---|
| Foundation Django app | PERMANENT | 101 backend tests + check/drift PASS | Evolucionar sólo con migrations 0002+ |
| TenantProjection | PERMANENT | Schema completo, RLS, constraints y triggers PASS | Integrar writer futuro separado |
| Tenant context service | PERMANENT | outermost/SET LOCAL/cleanup/boundary PASS | Conectar al adapter autorizado futuro |
| RLS migration pattern | PERMANENT | ENABLE+FORCE y catalog assertions PASS | Reutilizar en nuevos objetos tenant-scoped |
| Immutability triggers | PERMANENT | ID externo y tenant child mutation denegadas | Extender a tablas futuras |
| Status/version constraints | PERMANENT | invalid states + version regression denegados | Evolucionar mediante 0002+ si contrato cambia |
| Role bootstrap | TEST-ONLY | LOGIN names únicos, scoped cleanup | Reemplazo de deployment futuro requerido |
| PostgreSQL harness | TEST-ONLY | lifecycle + matrix + teardown PASS | Ejecutar como gate CI/local |
| Synthetic resolver | REMOVED | símbolo ausente y test de import PASS | Future replacement: adapter AdminApps real |
| Synthetic child | TEST-ONLY | creado/destruido sólo dentro del harness | Nunca agregar a migration permanente |
| AdminApps projection writer | FUTURE REPLACEMENT REQUIRED | app/worker deliberadamente read-only | Implementar role/adapter mínimo en fase futura |

## 16. Riesgos residuales

No quedan P0 ni P1 que bloqueen progresión del dominio. Riesgos no bloqueantes y explícitamente futuros:

1. no existe aún production integration writer/ingestor AdminApps;
2. no se probó pooler externo; sí la misma conexión física tras commit y rollback;
3. roles de deployment/CI productivos deben diseñarse fuera de migrations y no reutilizar nombres/credenciales del harness;
4. PostgreSQL productivo sigue sujeto a inventario, backup/restore, pooler y certificación operativa;
5. la semántica same-version replay/conflict queda en el projector futuro;
6. telemetría Chroma/PostHog añade ruido y latencia a tests legacy.

## 17. Veredicto

**ENTERPRISE FOUNDATION BASELINE: PROMOTED**

La migration legítima queda congelada, TenantProjection queda hardened y read-only para app/worker, el contexto permanente es fail-closed, los sintéticos están removidos/separados, los principals son LOGIN reales, PostgreSQL 18.6 y toda la matriz pasan, forward/reverse pasa, la regresión completa pasa, no hay drift, los hashes son 10/10 y el teardown está demostrado.

## NEXT_CODEX_PROMPT

```text
# ISO SMART AI — NEXT VERTICAL SLICE
# TENANT PROJECTION INTEGRATION BOUNDARY + ORGANIZATION FOUNDATION

WORKSPACE EXCLUSIVO: /home/felipe/proyectos/isosmart

NO modificar /home/felipe/proyectos/adminapps, /home/felipe/proyectos/ISO_Smart_MedSupplier ni /home/felipe/proyectos/design-system.

Estado verificado:
- Phase 1.2 ENTERPRISE FOUNDATION BASELINE = PROMOTED.
- 0001_foundation_tenant_projection está FROZEN; toda evolución debe ser 0002+.
- PostgreSQL oficial 18.6: security matrix, LOGIN principals, RLS ENABLE+FORCE, forward/reverse y teardown PASS.
- Backend: 101 PASS / 0 FAIL / 0 SKIP; check, migration drift, compilation y 10/10 hashes PASS.
- App y worker son read-only sobre TenantProjection; no existe projection writer productivo.

Misión: implementar una vertical slice incremental y no destructiva para TenantProjection production integration boundary + Organization foundation + UserProjection skeleton + AdminApps contract adapter boundary.

Requisitos:
1. Preservar AdminApps como system of record de tenant, identidad, acceso global, entitlements y billing.
2. No reescribir 0001; crear migrations 0002+ únicamente, aditivas y reversibles.
3. Diseñar un AdminApps projection writer/ingestor con principal mínimo independiente; app/worker permanecen read-only sobre TenantProjection.
4. Implementar la semántica del projector: same version + same event = idempotent replay; same version + conflicting event = 409/conflict; higher version = candidate update; lower version sigue bloqueada por DB.
5. Introducir Organization foundation tenant-scoped con tenant_id NOT NULL, FK/constraints, tenant immutability y ENABLE+FORCE RLS, sin migrar datos legacy todavía.
6. Añadir sólo un UserProjection skeleton mínimo contract-first, sin passwords utilizables ni autorización paralela.
7. Definir el adapter boundary AdminApps sin llamar ni modificar una DB AdminApps; usar contract tests/fixtures firmes y fail-closed.
8. Mantener transaction.atomic + trusted_tenant_context; jamás aceptar tenant desde body/query/header.
9. Repetir PostgreSQL 18.6 con LOGIN principals, A/B/none, raw SQL, worker, reuse, rollback, spoof, forward/reverse y teardown.
10. Ejecutar suite backend completa, Django check, migration drift, compilación y 10/10 source hashes.

Seguir SIN integración destructiva, migración masiva, backfill, dual-write, billing local nuevo, datos normativos, Process/Risk/Evidence productivos, las 43 entidades completas, production, staging ni deployment.

Entregar reporte de la slice, evidencia real, riesgos, clasificación de componentes y veredicto PROMOTED o NOT PROMOTED. Si falla un gate bloqueante, el siguiente prompt debe corregir exclusivamente esos blockers.
```
