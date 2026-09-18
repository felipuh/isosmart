# Phase 1 — First Foundation Vertical Slice

**Run ID:** `20260813T192432Z`  
**Fecha:** 2026-08-13  
**Veredicto:** **PASS**

El gate de esta slice pasó: se compiló PostgreSQL 18.6 desde el release source oficial cuyo SHA-256 fue verificado, el servidor confirmó exactamente 18.6 y todas las aserciones RLS bloqueantes pasaron en una base efímera dedicada. La slice continúa siendo un POC de testing; no es una imagen, configuración ni autorización de despliegue productivo.

## Resultados

1. **Docker Official Image retry:** el único reintento de `docker.io/library/postgres:18.6` devolvió `manifest unknown`. Clasificación: `DOCKER OFFICIAL IMAGE PUBLICATION LAG`.
2. **Source oficial:** descargado exclusivamente por HTTPS desde `https://ftp.postgresql.org/pub/source/v18.6/postgresql-18.6.tar.gz`, junto con su `.sha256` oficial.
3. **SHA-256:** esperado `983ee554ec53dbeb9b70797bef9fcf4e67e117e7e48ca1463cc80b3ff8e8ff3f`; calculado y publicado oficialmente: el mismo valor. El build volvió a ejecutar `sha256sum --check` antes de extraer.
4. **Build local:** PASS. Imagen no publicada `localhost/isosmart-postgres-18.6-poc:20260813T192432Z`; image ID `2d705eb74f491f5abf1883e0f24ab657864f93ed881b25e77a0468f132527bbb`; digest local `sha256:dc36e387a30277645df4e18eda626b0d43c179591930407bce67283439d48690`.
5. **Versión del servidor:** `SHOW server_version` → `18.6`; `SELECT version()` → `PostgreSQL 18.6 on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit`.
6. **Entorno efímero:** Podman `5.8.2`; contenedor `isosmart-pg18.6-poc-20260813T192432Z`; puerto host `127.0.0.1:46027`; base `isosmart_rls_poc_20260813`; volumen `isosmart-pgdata-18.6-20260813T192432Z`. Base oficial: `debian:bookworm-slim`, fijada a `sha256:362e64223cc0da95422b3b13c045186fc0a81250e765d31c025fbddf257f6143`.
7. **Models/migrations:** se añadió `foundation` con `TenantProjection`, `SyntheticTenantChild`, contexto confiable y migración `0001_tenant_rls_poc`. No se alteró ni eliminó ninguna tabla legada.
8. **Roles:** `isosmart_owner`, `isosmart_app`, `isosmart_worker`; todos NOLOGIN en este POC. Catálogo: app y worker `rolsuper=false`, `rolbypassrls=false`; ambas tablas pertenecen a `isosmart_owner`, nunca al runtime.
9. **RLS:** ambas tablas reportaron `relrowsecurity=true` y `relforcerowsecurity=true`. Existe exactamente una policy explícita SELECT, INSERT, UPDATE y DELETE por tabla (ocho en total).
10. **A/B/No Tenant:** A ve sólo `A only`; B ve sólo `B only`; sin contexto devuelve cero filas. Las direcciones A→B y B→A quedan invisibles.
11. **Pool reuse:** misma conexión física: A → commit → sin contexto (`[]`) → B (`B only`). PASS.
12. **Rollback:** A → excepción → rollback → sin contexto (`[]`) → B (`B only`). PASS.
13. **Worker:** A sólo A; B sólo B; sin tenant cero acceso. PASS.
14. **Raw SQL:** SELECT/INSERT/UPDATE/DELETE se ejecutaron con el rol runtime real mediante SQL directo y RLS permaneció activa. PASS.
15. **Identidad AdminApps:** cambio ordinario de `adminapps_tenant_id` rechazado por trigger server-side con SQLSTATE `23514`. PASS.
16. **Inmutabilidad tenant:** cambio `tenant_id A → B` rechazado por trigger independiente de RLS con SQLSTATE `23514`. PASS.
17. **Migraciones:** base vacía → forward → seed POC → matriz completa → reverse. La reversa eliminó schema, tablas, funciones, triggers, policies, grants y roles POC. `makemigrations --check --dry-run` reportó `No changes detected`.
18. **Regresiones existentes:** no se ejecutó la suite legada completa porque esta corrida instaló sólo Django y el driver en un entorno temporal aislado y el workspace ya contenía cambios ajenos. Sí pasaron compilación Python, consistencia models/migration, `git diff --check` sobre `foundation` y el harness PostgreSQL bloqueante. Esta limitación no reduce el gate RLS definido para la slice.
19. **Integridad de artefactos:** 10/10 hashes recalculados y coincidentes con `SOURCE_ARTIFACT_MANIFEST.md`.
20. **Teardown:** PASS. Se eliminaron el contenedor, volumen, imagen POC y directorio temporal exactos de esta corrida. La verificación posterior no encontró ninguno de los tres recursos Podman y confirmó `TEMP_REMOVED`. La base desapareció con el volumen/contenedor.
21. **Riesgos residuales:** es un POC, no una imagen productiva; los roles NOLOGIN fueron activados con `SET ROLE` desde el migrador efímero; no se midió rendimiento ni se ejecutó la suite legada completa; la integración real AdminApps, login runtime, pooler y despliegue siguen fuera de scope.
22. **Slice verdict:** **PASS — PHASE 1 FIRST FOUNDATION VERTICAL SLICE**.

## Comandos sanitizados

- Build: `podman build --pull=never --tag localhost/isosmart-postgres-18.6-poc:<RUN_ID> <TEMP_CONTEXT>`
- Run: `podman run --detach --name <CONTAINER> --publish 127.0.0.1::5432 --volume <VOLUME>:/var/lib/postgresql/data <IMAGE>`
- Harness: `POC_DB_*=<EPHEMERAL_VALUES> python backend/foundation/postgres_poc_harness.py`
- Teardown: `podman rm --force <CONTAINER>`; `podman volume rm <VOLUME>`; `podman image rm <IMAGE>`; eliminar `<TEMP_CONTEXT>`.

| Archivo/artefacto | Cambio | Test/evidencia | Riesgo/gate |
|---|---|---|---|
| `backend/backend/settings.py` | Registra app `foundation` | Carga del app y harness | Archivo tenía cambios locales previos; se añadió sólo una entrada |
| `backend/foundation/models.py` | Skeleton de projection e hijo sintético | Estado de migración sincronizado | POC, `managed=False`; DDL controlado por RunSQL PostgreSQL |
| `backend/foundation/tenant_context.py` | Resolver fixture fail-closed + SET LOCAL verificado | Contexto existe dentro de transacción y queda vacío al commit | Resolver real AdminApps fuera de scope |
| `backend/foundation/migrations/0001_tenant_rls_poc.py` | Roles, schema, tablas, triggers, FORCE RLS, 8 policies y reversa | Catálogos, DML y reverse migration reales | Sólo PostgreSQL; no SQLite |
| `backend/foundation/postgres_poc_harness.py` | Matriz bloqueante ejecutable | PASS contra PostgreSQL 18.6 real | Requiere base efímera dedicada y migrador privilegiado |
| `postgresql-18.6.tar.gz` temporal | Source oficial verificado y compilado | SHA esperado = actual = oficial | Se elimina tras la corrida |
| Imagen POC local | Runtime PostgreSQL 18.6 | SHOW/version + suite RLS | Se elimina tras la corrida; no publicar |
| 10 source artifacts | Sin cambios | 10/10 SHA-256 coinciden | Gate de integridad PASS |

## NEXT_CODEX_PROMPT

```text
# ISO SMART AI — PHASE 1 NEXT INCREMENT AFTER VERIFIED RLS FOUNDATION

WORKSPACE EXCLUSIVO: /home/felipe/proyectos/isosmart

NO modificar /home/felipe/proyectos/adminapps, /home/felipe/proyectos/ISO_Smart_MedSupplier ni /home/felipe/proyectos/design-system.

Estado verificado de partida (2026-08-13):
- PostgreSQL 18.6 fue compilado para testing desde el source oficial postgresql-18.6.tar.gz.
- SHA-256 esperado, oficial y calculado: 983ee554ec53dbeb9b70797bef9fcf4e67e117e7e48ca1463cc80b3ff8e8ff3f.
- SHOW server_version confirmó 18.6.
- La slice foundation implementa TenantProjection, SyntheticTenantChild, roles NOLOGIN POC, contexto transaccional SET LOCAL, ENABLE+FORCE RLS, policies explícitas por operación, triggers de inmutabilidad y harness PostgreSQL.
- Pasaron A/B/No Tenant, wrong-tenant INSERT, tenant_id y adminapps_tenant_id inmutables, pool reuse, rollback, worker, raw SQL, catálogos y forward/reverse migration.
- La imagen, contenedor, volumen y temporales POC fueron destruidos al terminar.
- No asumir que postgres:18.6 ya existe: reintentar el tag oficial una sola vez y, si aún falta, repetir exclusivamente el build verificado desde source oficial con el mismo SHA.

Misión: convertir esta fundación POC en una integración de aplicación mínima, todavía no productiva, sin expandir el dominio. Mantener únicamente TenantProjection + SyntheticTenantChild. Añadir un boundary de conexión runtime separado del migrador, probar el contexto confiable mediante el ORM y una ruta/servicio interno de test no expuesto en producción, y ejecutar la suite legada relevante más la matriz PostgreSQL 18.6 completa.

Requisitos bloqueantes:
1. Preservar AdminApps como única autoridad de tenant; el request nunca elige tenant libremente.
2. Runtime debe conectarse como un principal no-superuser, no-owner y sin BYPASSRLS; no basta SET ROLE desde superuser para el nuevo gate.
3. Migrador/owner separado; secretos sólo efímeros y nunca escritos al repositorio o al reporte.
4. Toda operación tenant usa transaction.atomic + set_config(..., true) antes de queries de dominio.
5. Probar ORM y raw SQL: A→A, B→B, cross-tenant invisible, no tenant fail-closed, wrong insert denied, identidad y tenant_id inmutables.
6. Probar misma conexión tras commit y rollback, worker y al menos una ejecución con pooling real o un sustituto explícitamente documentado si no está disponible.
7. Ejecutar forward/reverse sobre base PostgreSQL 18.6 vacía; no tocar tablas legadas ni datos persistentes.
8. Recalcular los diez hashes de SOURCE_ARTIFACT_MANIFEST.md; cualquier diferencia es FAIL.
9. Ejecutar regresiones relevantes del backend y reportar cualquier test no ejecutado; no declarar PASS sobre evidencia no ejecutada.
10. Destruir sólo los recursos efímeros creados por la corrida y verificar ausencia.

No implementar Organization productiva, UserProjection sync, Site, Process, Risk, Evidence Graph, outbox, audit log, onboarding, billing, cambios AdminApps ni despliegue.

Entregar veredicto PASS / PASS WITH RESTRICTIONS / FAIL, evidencia sanitizada, riesgos residuales, tabla Archivo/artefacto | Cambio | Test/evidencia | Riesgo/gate, y exactamente un NEXT_CODEX_PROMPT autocontenido derivado de los resultados reales.
```
