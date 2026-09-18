# ISO Smart AI — diseño PostgreSQL RLS

## Invariante

**NO TENANT CONTEXT = NO ACCESS.** La aplicación ordinaria y workers no son owner, superuser ni `BYPASSRLS`. Cada tabla tenant-scoped usa defensa ORM/servicio, constraints de grafo y RLS. SQLite no valida este control.

PostgreSQL aplica default deny cuando RLS está habilitada y no existe una policy aplicable; owners normalmente bypass, por eso las tablas usan `ENABLE ROW LEVEL SECURITY` y `FORCE ROW LEVEL SECURITY`. Véase la [documentación oficial de RLS](https://www.postgresql.org/docs/18/ddl-rowsecurity.html).

## Contexto transaccional

Dentro de `transaction.atomic()` y antes de cualquier query tenant:

```sql
SELECT set_config('app.tenant_id', :tenant_uuid, true);
SELECT set_config('app.actor_id', :actor_external_or_local_id, true);
SELECT set_config('app.trace_id', :trace_uuid, true);
```

El tercer argumento `true` equivale a scope local de transacción. El tenant proviene únicamente del resolver confiable del servidor: identidad ya autenticada + claim/contrato autorizado + TenantProjection activa + entitlement. Body, query string y headers arbitrarios del cliente no son fuentes aceptables y nunca se pasan directamente a `set_config`. Para el POC se permite un resolver sintético inyectado por fixture, pero su API recibe una identidad autorizada y devuelve una TenantProjection precreada; no recibe un tenant libre controlado por el request. El código comprueba inmediatamente el valor; cualquier query previa al set debe ser sólo de autenticación/projection con policy apropiada. Autocommit queda prohibido en repositorios tenant. Al commit/rollback el contexto desaparece, lo que permite transaction pooling y evita bleed.

Expresión canónica fail-closed:

```sql
tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
```

Missing/empty produce NULL y la comparación no autoriza. Una función helper `app_current_tenant()` sólo se acepta si es `STABLE`, tiene `search_path` fijo, owner no-runtime y tests de tamper; no puede aceptar fallback.

## Policies por operación

Para una tabla directa `qms.risk`:

```sql
ALTER TABLE qms.risk ENABLE ROW LEVEL SECURITY;
ALTER TABLE qms.risk FORCE ROW LEVEL SECURITY;

CREATE POLICY risk_select ON qms.risk FOR SELECT TO isosmart_app, isosmart_worker, isosmart_readonly
USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

CREATE POLICY risk_insert ON qms.risk FOR INSERT TO isosmart_app, isosmart_worker
WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

CREATE POLICY risk_update ON qms.risk FOR UPDATE TO isosmart_app, isosmart_worker
USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

CREATE POLICY risk_delete ON qms.risk FOR DELETE TO isosmart_app
USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
```

UPDATE necesita `USING` para fila vieja y `WITH CHECK` para fila nueva. Policy no reemplaza permisos: `GRANT` se limita por rol; tablas append-only no reciben UPDATE/DELETE aunque una policy pudiera formularse. No usar una policy `FOR ALL` cuando los roles/semantics difieren.

`TenantProjection` usa `id = current tenant`; global normative tables no usan tenant RLS y son read-only por grants para runtime. Cross-tenant platform reporting se implementa mediante export/job privilegiado específico, no una policy permisiva compartida.

## Relaciones e hijos

Baseline: `tenant_id` directo incluso en child records críticos y FK compuesta `(tenant_id, parent_id) → parent(tenant_id,id)`. Esto bloquea cross-tenant attachment antes de RLS.

Si una child table no puede tener tenant directo, su policy usa `EXISTS` contra padre RLS-safe, por ejemplo:

```sql
USING (EXISTS (
  SELECT 1 FROM qms.document d
  WHERE d.id = document_version.document_id
    AND d.tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
))
```

Se prueban SELECT/INSERT/UPDATE/DELETE y planes de joins/nested queries. No se permite `SECURITY DEFINER` para “simplificar” joins salvo API DB mínima, search_path fijo, ownership seguro y security review.

## Inmutabilidad de tenant independiente de RLS

Cada tabla POC protegida con `tenant_id` usa además un trigger `BEFORE UPDATE` propiedad de un rol no-runtime. La función compara `OLD.tenant_id` y `NEW.tenant_id` con `IS DISTINCT FROM` y lanza una excepción con código SQLSTATE estable ante cualquier cambio. El runtime no tiene permiso para deshabilitar triggers ni alterar la tabla o función. Esta defensa es independiente de `USING`/`WITH CHECK`: el test establece contexto A, intenta por SQL u ORM `tenant_id A → B` sobre una fila A visible y debe observar la excepción del trigger y rollback. Una transferencia futura requiere el protocolo privilegiado definido en el modelo de tenant; no se implementa en este POC.

## Matriz de superficies

| Superficie | Control obligatorio | Failure behavior |
|---|---|---|
| HTTP request | Identity→projection→entitlement→atomic→SET LOCAL | Sin tenant: deny/503 antes de dominio |
| Connection pool reuse | Context sólo transaccional; rollback en excepción; test A→none→B | Nunca RESET como control primario |
| Celery/background | Envelope lleva tenant; resolver projection activa; atomic+SET LOCAL | Missing/mismatch: task failed/quarantine, no retry ciego |
| Scheduled tenant fan-out | Enumerador privilegiado produce una tarea por tenant; task ordinaria scoped | Nunca loop cross-tenant con una sesión contextual |
| Management command | `--tenant-external-id` obligatorio o modo platform explícito con dual approval | No tenant: no-op/deny |
| Migration/backfill | migrator separado; lotes tenant por tenant, checkpoint/audit | Stop on mismatch; no app BYPASSRLS |
| Admin UI/API | Misma RLS; platform action separada y audited | Staff flag no implica cross-tenant access |
| Raw SQL | Repository allow-list + SET LOCAL + tests | Sin tenant devuelve cero/deniega writes |
| Bulk create/update | Inyectar tenant server-side; composite FK; RLS checks | Batch completo rollback en mismatch |
| Joins/subqueries | tenant predicates + RLS en cada tabla | No confiar en sólo tabla raíz |
| Async callbacks/webhooks | Signature+Inbox→projection→transaction | Unknown tenant/event: quarantine/409/503 |

## Ownership y bypass

- `isosmart_owner` no tiene LOGIN; migrations controladas pueden `SET ROLE` sólo durante DDL.
- `isosmart_app`, `isosmart_worker`, `isosmart_readonly` carecen de ownership y BYPASSRLS.
- No usar superuser en Django settings, CI de aplicación o pool.
- Los tests consultan PostgreSQL después de migrations: `pg_roles` debe devolver `rolsuper=false` y `rolbypassrls=false` para el rol runtime; el join `pg_class`/`pg_namespace`/`pg_roles` debe demostrar que ninguna tabla protegida pertenece a ese rol.
- Por cada tabla POC protegida, la inspección de `pg_class` debe devolver simultáneamente `relrowsecurity=true` y `relforcerowsecurity=true`; además se comprueban las policies por operación. Inspeccionar solamente SQL/migrations no constituye evidencia.
- `row_security=off` no forma parte de runtime. Break-glass se ejecuta con ticket, límite temporal, dual control, log externo y reconcile posterior.

## Deploy incremental

1. Crear una instancia PostgreSQL 18.6 efímera, dedicada y con identificador único para la slice; validar aislamiento y preparar teardown exacto antes de migrations.
2. Crear roles/schemas/helpers y tablas nuevas sin datos productivos.
3. Crear policies; habilitar + forzar RLS antes de conceder DML runtime.
4. Ejecutar matriz PostgreSQL con roles reales y registrar engine, versión exacta, puerto, base, roles y comandos sanitizados de creación/destrucción.
5. Destruir el recurso efímero aun si falla la suite y comprobar que dejó de existir. No reutilizar producción, staging, desarrollo persistente, AdminApps ni bases compartidas.
6. Para tablas legadas futuras: expand tenant FK, backfill/reconcile, FK compuesta, policies shadow con rol de prueba, canary, luego cambiar runtime role.
7. Validar `NOT VALID` constraints, activar FORCE, observar denials/latency y conservar rollback por role/feature flag. Nunca deshabilitar RLS como rollback de datos; volver al read path legado aislado.

## Criterio de aceptación

El diseño sólo se considera implementado cuando el test matrix demuestra en una instancia PostgreSQL 18.6 real, efímera y exclusiva: A→A, B→B, A↛B, B↛A, no-tenant deny después de commit y rollback sobre la misma conexión, pool/worker isolation, joins/raw SQL/bulk seguros, resolver server-side no falsificable, tenant inmutable por trigger y catálogos que prueban runtime sin superuser/owner/BYPASSRLS y RLS habilitada+forzada. El reporte debe demostrar creación y destrucción segura sin revelar secretos. Evidencia basada sólo en código fuente, SQL de setup, SQLite o una base persistente/compartida no permite PASS.
