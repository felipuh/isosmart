# Phase 1.1 — Foundation Promotion & Full Regression Gate

**Fecha:** 2026-08-13

**PostgreSQL run-id final:** `20260813T204323Z`

**Gate:** `ENTERPRISE FOUNDATION BASELINE`

**Veredicto:** **PROMOTED WITH RESTRICTIONS**

Phase 1 conserva su veredicto histórico **PASS**. Phase 1.1 es un gate independiente: detectó y corrigió dos regresiones reales de promoción, repitió la suite backend completa y revalidó el POC en PostgreSQL 18.6 desde una base vacía. No autoriza production, staging, una base compartida ni la introducción de objetos empresariales nuevos.

## 1. Full backend regression

Comando final:

```text
./.venv/bin/python manage.py test --settings=backend.settings_test --noinput --verbosity 1
```

| Ejecución | Descubiertos | PASS | FAIL | SKIP | Duración de tests | Duración de pared | Resultado |
|---|---:|---:|---:|---:|---:|---:|---|
| Inicial | 98 | 0 | 0 casos ejecutados | 0 | N/A | 7.38 s | FAIL durante creación de DB: `0001_tenant_rls_poc` enviaba `DO ...` de PostgreSQL a SQLite |
| Final | 98 | 98 | 0 | 0 | 5.637 s | 30.57 s | PASS |

Clasificación del fallo inicial: **regresión introducida por foundation**. No era preexistente ni de entorno. Se corrigió reemplazando el `RunSQL` incondicional por una operación de migración vendor-aware: ejecuta el DDL únicamente en PostgreSQL y es no-op en el perfil SQLite legado, sin pretender validar RLS en SQLite.

La diferencia entre 5.637 s y 30.57 s provino de reintentos asíncronos de telemetría Chroma/PostHog hacia `us.i.posthog.com`; los 98 tests ya habían terminado en PASS. Persisten warnings preexistentes de paginación sin ordering y telemetría de test, sin fallos ni skips.

La suite se ejecutó sin labels, por lo que incluyó todos los tests Django descubiertos en `authentication`, `core`, `integration`, `leadership` y cualquier otra app con tests disponibles. Las apps legacy restantes no contienen módulos de test descubiertos en el repositorio.

## 2. Django integrity

| Validación | Resultado | Evidencia |
|---|---|---|
| `manage.py check --settings=backend.settings_test` | PASS | `System check identified no issues (0 silenced)` |
| `makemigrations --check --dry-run --settings=backend.settings_test` | PASS | `No changes detected` |
| Compilación Python de `foundation` | PASS | `python -m compileall -q foundation`, exit 0 |
| Models ↔ migration | PASS | Sin drift después de la evolución controlada de `0001` |
| Tablas legacy | PASS | La migration sólo opera sobre schema `qms` en PostgreSQL; no altera tablas legacy |
| SQLite accidental | PASS WITH BOUNDARY | La migration es no-op en SQLite y la suite legacy pasa; ninguna semántica RLS se declara validada allí |

## 3. PostgreSQL 18.6 harness repeat

La imagen oficial `docker.io/library/postgres:18.6` se intentó una vez y respondió `manifest unknown`. Se usó exclusivamente el source oficial por HTTPS:

- source: `postgresql-18.6.tar.gz`;
- SHA-256 oficial y calculado: `983ee554ec53dbeb9b70797bef9fcf4e67e117e7e48ca1463cc80b3ff8e8ff3f`;
- engine: Podman 5.8.2;
- run-id final: `20260813T204323Z`, distinto de Phase 1 (`20260813T192432Z`) y de los intentos de diagnóstico de esta corrida;
- imagen local no publicada: `localhost/isosmart-postgres-18.6-promotion:20260813T204323Z`;
- image ID: `14cfd62f79c4e1063ecfe2a8548aff2563902c9105ef66755f1c0816766d2b3f`;
- contenedor: `isosmart-pg18.6-promotion-20260813T204323Z`;
- volumen: `isosmart-pgdata-18.6-promotion-20260813T204323Z`;
- endpoint exclusivo: `127.0.0.1:44513`;
- base: `isosmart_rls_promotion_20260813_204323`;
- `SHOW server_version`: `18.6`;
- `SELECT version()`: PostgreSQL 18.6, gcc 12.2.0, 64-bit;
- harness final: PASS en 1.31 s de pared.

Ciclo probado: source/checksum → build → cluster/base vacíos → forward migration → seed sintético → matriz RLS/catalogal → reverse migration → teardown. La reversa comprobó ausencia de tablas y roles POC. Después se eliminaron por nombre exacto contenedor, volumen, imagen y directorio temporal; las consultas posteriores de Podman devolvieron cero recursos.

La revisión encontró y corrigió dos defectos de reproducibilidad antes del PASS final: el harness dependía de un `PYTHONPATH` implícito, y la operación vendor-aware debía pasar `params=None` para no interpretar los `%I` internos de SQL como placeholders. Los intentos fallidos ocurrieron antes de completar migrations y no se cuentan como evidencia PASS.

## 4. Security regression matrix

| Assertion bloqueante | Resultado | Evidencia final |
|---|---|---|
| Runtime non-superuser | PASS | `isosmart_app=false`; `isosmart_worker=false` en `rolsuper` |
| Runtime sin `BYPASSRLS` | PASS | ambos roles `rolbypassrls=false` |
| Runtime non-owner | PASS | ambas tablas protegidas pertenecen a `isosmart_owner` |
| RLS enabled | PASS | `relrowsecurity=true` en 2/2 tablas |
| FORCE RLS | PASS | `relforcerowsecurity=true` en 2/2 tablas |
| Policies catalog | PASS | exactamente SELECT/INSERT/UPDATE/DELETE por tabla; 8 total, sin duplicados |
| Tenant A/B | PASS | A sólo `A only`; B sólo `B only`; simétrico |
| No tenant | PASS | SELECT devuelve cero filas; write incorrecto denegado |
| Connection reuse | PASS | misma conexión A → none → B: `[[A only], [], [B only]]` |
| Rollback contamination | PASS | rollback A → none → B: `[[], [B only]]` |
| Worker isolation | PASS | A sólo A; B sólo B; none vacío |
| Raw SQL protection | PASS | INSERT/SELECT/UPDATE/DELETE directos permanecen bajo RLS |
| `tenant_id` immutable | PASS | trigger independiente, SQLSTATE `23514` |
| `adminapps_tenant_id` immutable | PASS | trigger independiente, SQLSTATE `23514` |
| Runtime provision/delete TenantProjection | PASS | `INSERT` y `DELETE` denegados por grants para app y worker |
| Tenant context cleanup | PASS | `SET LOCAL` verificado y vacío tras commit |
| Nested atomic behavior | PASS | una transacción exterior es rechazada antes de establecer contexto |

El harness aún usa roles `NOLOGIN` mediante `SET ROLE` desde el migrador efímero. La evidencia demuestra propiedades catalogales y comportamiento RLS del rol efectivo, pero no prueba un principal de conexión runtime separado. Esto permanece como restricción para promoción productiva, no como degradación de las assertions Phase 1.

## 5. Foundation code review

### TenantProjection

Cumple: UUID interno estable; identidad externa UUID `UNIQUE NOT NULL`; `source_version`; `source_event_id UNIQUE` nullable; snapshots; lifecycle y entitlement básicos; timestamps; inmutabilidad DB de `id` y `adminapps_tenant_id`; runtime sin provision/delete.

No cumple todavía el modelo objetivo completo: faltan `provisioning_status`, `last_synced_at`, `last_reconciled_at`, `reconciliation_status`, `reconciliation_error_code`, `suspended_at` y `deletion_requested_at`; no existe enforcement monotónico de `source_version`; lifecycle/entitlement no tienen constraints de transición. `managed=False` y el nombre quoted de schema son propios del POC. Clasificación: **PROMOTE WITH REFACTOR**.

### Tenant context

Usa `transaction.atomic`, tres `set_config(..., true)`, parámetros SQL, verificación inmediata y resolver sintético fail-closed. No recibe tenant desde body/query/header y no tiene consumidor HTTP funcional. Se corrigió el caso nested: un `SET LOCAL` dentro de un savepoint sobreviviría hasta el commit exterior, por lo que ahora el servicio exige poseer la transacción outermost y falla antes de establecer contexto si ya existe un atomic exterior.

El mecanismo transaccional es promovible. El resolver y `TrustedTenantIdentity` actuales son fixtures; todavía faltan projection activa, entitlement y boundary AdminApps reales. Clasificación dividida: contexto **PERMANENT FOUNDATION**; resolver **TEMPORARY POC**.

### RLS, ownership, grants y triggers

Las policies son explícitas por operación, con expresión canónica fail-closed, ENABLE+FORCE y owner no-runtime. Los triggers tienen `search_path` fijo y SQLSTATE estable. Se corrigieron grants excesivos sobre TenantProjection. El patrón es sano, pero el setup de roles fijo dentro de la migration y su reversa global no son apropiados para una base compartida.

### SyntheticTenantChild

No hay referencias fuera de `foundation/models.py`, `0001_tenant_rls_poc` y `postgres_poc_harness.py`; ningún endpoint, servicio, worker ni flujo funcional depende de él. Es estrictamente sintético y debe salir del schema de dominio antes de la próxima slice empresarial.

### Hallazgos

- P0 abiertos: **0**.
- P1 abiertos de seguridad/regresión ejecutada: **0** después de las correcciones.
- Restricciones de promoción: migration POC no apta para DB compartida; TenantProjection incompleta; principal runtime real no probado; lifecycle del entorno aún se orquesta fuera del harness Python.

## 6. Component classification

| Componente/archivo | Clasificación | Evidencia | Acción siguiente |
|---|---|---|---|
| `backend/foundation/` Django app | PERMANENT FOUNDATION | Namespace aislado registrado; suite completa PASS | Conservar como app foundation |
| `backend/foundation/models.py` — `TenantProjection` | PROMOTE WITH REFACTOR | Identidades/uniqueness/immutability base PASS; faltan campos y constraints objetivo | Completar projection y estado de migration antes de dominio |
| `SyntheticTenantChild` | TEMPORARY POC | Cero consumidores funcionales; sólo migration/harness | Retirar del schema permanente antes de la próxima slice empresarial |
| `trusted_tenant_context` | PERMANENT FOUNDATION | Atomic outermost, SET LOCAL verificado, commit/rollback limpios, nested fail-closed | Añadir tests de integración con principal runtime y projection real |
| `SyntheticTrustedTenantResolver` | TEMPORARY POC | Map fixture subject→tenant; unknown subject denegado | Sustituir sólo al definir boundary real, sin aceptar tenant del request |
| DB roles setup en `0001` | TEMPORARY POC | Roles NOLOGIN y `SET ROLE`; catálogos PASS | Sacar bootstrap de roles globales de la migration de dominio y probar LOGIN efímero separado |
| RLS policy/migration pattern | PROMOTE WITH REFACTOR | 8 policies, ENABLE+FORCE, grants y reverse PASS | Convertir a migration production-grade, acotada y sin cleanup global |
| Immutability triggers | PERMANENT FOUNDATION | Ambos cambios rechazados con `23514`; `search_path` fijo | Conservar patrón y extender a tablas reales |
| `0001_tenant_rls_poc.py` actual | REMOVE BEFORE NEXT SLICE | Reversa usa `DROP SCHEMA ... CASCADE` y elimina roles nominales; contiene child sintético | Reemplazo controlado opción B antes de cualquier DB compartida |
| `postgres_poc_harness.py` | PROMOTE WITH REFACTOR | Matriz final PASS; import path autocontenido | Automatizar lifecycle completo y conexión como principal runtime real |
| 10 source artifacts | PERMANENT FOUNDATION INPUT | SHA-256 10/10 MATCH | Mantener byte-for-byte inmutables |

## 7. Migration evolution decision

**Decisión: opción B.** `0001_tenant_rls_poc` debe reemplazarse de forma controlada antes de que exista cualquier base compartida.

Justificación:

1. Phase 1 y Phase 1.1 sólo la aplicaron a bases efímeras destruidas; no existe production, staging ni shared DB con esta migration.
2. El archivo continúa sin formar parte de una baseline publicada y contiene deliberadamente el child sintético.
3. Su reversa `DROP SCHEMA IF EXISTS qms CASCADE` y `DROP ROLE IF EXISTS ...` podría borrar objetos/roles no creados por esa ejecución en una base evolucionada.
4. `TenantProjection` aún no representa todos los campos/constraints obligatorios del diseño aprobado.

Consecuencias:

- la edición realizada en este gate es un reemplazo pre-release explícito, no una reescritura silenciosa de historia compartida;
- no se debe aplicar la `0001` actual en ninguna DB persistente;
- la siguiente corrida debe producir una `0001` legítima y final de foundation, separar bootstrap de roles, retirar el child sintético del estado de dominio y repetir forward/reverse/regresión;
- una vez publicada/aplicada esa baseline, toda evolución será mediante migrations nuevas expand/contract; no se reescribirá de nuevo `0001`.

## 8. Source artifact integrity

Resultado: **10/10 MATCH** contra `SOURCE_ARTIFACT_MANIFEST.md`.

| # | SHA-256 recalculado | Resultado |
|---:|---|---|
| 1 | `8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c` | MATCH |
| 2 | `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa` | MATCH |
| 3 | `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3` | MATCH |
| 4 | `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5` | MATCH |
| 5 | `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3` | MATCH |
| 6 | `30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6` | MATCH |
| 7 | `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e` | MATCH |
| 8 | `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8` | MATCH |
| 9 | `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb` | MATCH |
| 10 | `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db` | MATCH |

Ningún source artifact fue modificado.

## 9. Residual risks and final verification

Riesgos residuales:

1. La migration actual sólo es segura en el entorno efímero POC y debe reemplazarse antes de DB compartida.
2. `TenantProjection` no está production-hardened ni completa respecto del contrato de reconciliación.
3. Los roles runtime son `NOLOGIN`; falta probar conexión directa con credenciales efímeras separadas del migrador.
4. No se probó un pooler externo real; sí la misma conexión física tras commit y rollback.
5. El harness Python no crea/compila/destruye por sí solo todo el entorno; la corrida es reproducible mediante comandos sanitizados, pero falta automatización con finalizer.
6. La suite intenta telemetría externa durante tests; no afecta el PASS, pero añade ruido y duración.

Verificación de alcance:

- no production, staging ni shared DB;
- no AdminApps DB ni MedSupplier DB;
- no `.env`, secretos o DSN persistidos;
- no cambios en `adminapps`, `ISO_Smart_MedSupplier` ni `design-system`;
- no Organization, Site, UserProjection, EntitlementProjection ni dominio nuevo;
- PostgreSQL efímero destruido y ausencia verificada;
- `backend/test_default.sqlite3` y `frontend/src/components/Layout/Sidebar.jsx:28` eran cambios preexistentes y no se atribuyen a Phase 1.1.

## 10. Promotion verdict

**ENTERPRISE FOUNDATION BASELINE: PROMOTED WITH RESTRICTIONS**

La regresión completa, Django integrity, PostgreSQL 18.6, assertions de seguridad y hashes pasan. No se otorga `PROMOTED` pleno porque la migration POC no puede promoverse a una DB compartida, TenantProjection requiere hardening contractual y falta una conexión runtime real separada. No se permite avanzar todavía a Organization, UserProjection ni adapter AdminApps; primero deben cerrarse estas restricciones y repetir el gate.

## NEXT_CODEX_PROMPT

```text
# ISO SMART AI — PHASE 1.2
# CLOSE FOUNDATION PROMOTION RESTRICTIONS

WORKSPACE EXCLUSIVO: /home/felipe/proyectos/isosmart

NO modificar /home/felipe/proyectos/adminapps, /home/felipe/proyectos/ISO_Smart_MedSupplier ni /home/felipe/proyectos/design-system.

Estado verificado:
- Phase 1 = PASS.
- Phase 1.1 = PROMOTED WITH RESTRICTIONS.
- Suite backend completa: 98/98 PASS, 0 FAIL, 0 SKIP.
- Django check y migration drift: PASS.
- PostgreSQL 18.6 run-id final 20260813T204323Z: PASS; SHOW server_version=18.6; 8 policies; ENABLE+FORCE; A/B/none, reuse, rollback, worker, raw SQL y triggers PASS.
- Source artifacts: 10/10 SHA-256 MATCH.
- Recursos efímeros destruidos.

Misión: cerrar exclusivamente las restricciones de foundation antes de introducir cualquier objeto empresarial.

Requisitos bloqueantes:
1. Ejecutar git status antes de modificar y preservar todos los cambios preexistentes.
2. Aplicar la decisión de migration evolution opción B: reemplazar de forma controlada la 0001 POC, permitido únicamente porque nunca fue aplicada a una DB compartida. Documentar el punto tras el cual 0001 queda congelada.
3. Crear una primera migration legítima de foundation que no use DROP SCHEMA CASCADE ni elimine roles preexistentes, y separar el bootstrap de roles globales del schema de dominio.
4. Retirar SyntheticTenantChild del estado permanente de models/migrations; si se necesita para pruebas RLS, crearlo y destruirlo como fixture estrictamente temporal del harness.
5. Completar TenantProjection con provisioning_status, last_synced_at, last_reconciled_at, reconciliation_status, reconciliation_error_code, suspended_at y deletion_requested_at; añadir constraints/trigger para source_version monotónica y estados válidos, sin Organization ni UserProjection.
6. Conservar UUID interno, adminapps_tenant_id externo UNIQUE NOT NULL e inmutable, source_event_id UNIQUE nullable, timestamps e inmutabilidad DB.
7. Mantener trusted_tenant_context como outermost transaction boundary fail-closed; separar el resolver sintético del API permanente y probar que ningún valor de body/query/header puede llegar al setter.
8. Probar con principales LOGIN efímeros separados para migrator, app y worker; app/worker deben ser non-superuser, non-owner, sin BYPASSRLS y sin INSERT/DELETE de TenantProjection. No usar SET ROLE desde superuser como única evidencia.
9. Automatizar create→18.6→migrate→security matrix→reverse→cleanup con finalizer; no usar production, staging, shared DB, AdminApps DB ni MedSupplier DB.
10. Repetir la suite backend completa, check, makemigrations --check --dry-run, forward/reverse desde DB vacía, blocking security assertions y 10/10 hashes. Registrar PASS/FAIL/SKIP/duración y no ocultar intentos fallidos.
11. No implementar Organization, Site, UserProjection, EntitlementProjection, integración AdminApps nueva, billing, Process, Risk, Evidence, outbox, audit productivo, onboarding, agentes, backfill ni deployment.

Entregar docs/transformation/PHASE1_2_FOUNDATION_RESTRICTIONS_CLOSURE_REPORT.md, clasificación final de componentes, decisión explícita PROMOTED o NOT PROMOTED para ENTERPRISE FOUNDATION BASELINE y exactamente un NEXT_CODEX_PROMPT derivado de evidencia real. Sólo si queda PROMOTED podrá el prompt siguiente avanzar incrementalmente a TenantProjection production hardening + Organization foundation + UserProjection skeleton + AdminApps contract adapter boundary.
```
