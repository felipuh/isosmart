# ADR-0009: transactional domain command composition and least-privilege executor boundary

- Estado: Aceptado para POC efímero controlado
- Fecha: 2026-08-24
- Sucede a: ADR-0008 sin reescribir ADR-0007 ni ADR-0008
- Alcance: diseño/contrato; ninguna capacidad runtime se concede aquí

## Contexto

Product Policy `controlled-qms-action-policy/v1` propone exclusivamente
`opportunity.defer_evaluation`, `under_evaluation -> deferred`, impacto
`standard`, compensación separada `opportunity.resume_evaluation`, Approval
humana obligatoria y techo A3. La policy es una decisión de producto no
normativa y no modifica requisitos ISO.

El command promovido `change_opportunity_status` conserva historia y escribe la
revisión, `DomainEvent`, `TransactionalOutbox` y audit en una transacción. Sin
embargo, `trusted_tenant_context` exige poseer el bloque atómico externo. Phase
14 también confirma el patrón de dos transacciones alrededor del executor. Por
ello el command actual no puede formar el commit único requerido con
ActionExecution y Receipt. Además, EXECUTOR no tiene ni debe recibir INSERT,
UPDATE o DELETE genérico sobre Opportunity.

## Problema

Se necesita una operación de dominio reutilizable que pueda ejecutarse dentro
de una transacción ya abierta, sin duplicar lógica entre el command normal y el
adapter controlado. A la vez, la credencial EXECUTOR debe poder efectuar sólo
el defer exacto autorizado, sin poder crear, revisar libremente, borrar o
cambiar cualquier campo/estado de Opportunity.

## Alternativas

1. Convención Python/service con DML de Opportunity para EXECUTOR: rechazada;
   la credencial podría omitir la convención.
2. Función `SECURITY DEFINER` genérica `model/field/value` o status arbitrario:
   rechazada por escalamiento de privilegio y duplicación de autoridad.
3. Función action-specific que reimplementa toda la mutación separadamente:
   rechazada porque divergiría del command público.
4. Primicia de dominio privada compartida más wrapper action-specific
   `SECURITY DEFINER`: seleccionada.

## Decisión

Phase 16 deberá extraer la semántica actualmente distribuida entre `_revise`,
`_emit` y `change_opportunity_status` a una primitiva privada de dominio
transaccional, conceptualmente
`apply_opportunity_status_transition_in_transaction`. La primitiva:

- exige que el caller ya esté dentro de `transaction.atomic()` en el alias
  correcto;
- no abre/posee otra transacción, no crea savepoint y nunca hace commit;
- bloquea y valida la revisión actual exacta;
- copia Process/hypothesis/benefit/feasibility, crea la revisión siguiente y
  conserva lineage/predecessor;
- crea exactamente el contrato existente `opportunity.status_changed` v1,
  Outbox y audit;
- retorna IDs/estado deterministas para el caller;
- propaga toda excepción para rollback del bloque exterior.

El public command conservará su firma, validaciones y ownership externo:

```text
change_opportunity_status
  -> trusted_tenant_context (outer atomic + SET LOCAL)
  -> shared in-transaction primitive
  -> commit
```

El futuro path controlado usará el mismo alias/conexión y una sola transacción:

```text
atomic + trusted SET LOCAL
  -> lock ActionExecution/idempotency
  -> revalidate immutable authorization/plan/Approval
  -> narrow defer wrapper
       -> shared Opportunity primitive
       -> revision + Opportunity Event/Outbox/Audit
  -> terminal ActionExecution + Receipt
  -> execution Event/Outbox/Audit
  -> one commit
```

La primitiva compartida se materializará como función DB privada de dominio
`SECURITY INVOKER` (nombre final versionado en 0015) para que tanto el command
APP como el wrapper controlado ejecuten exactamente el mismo algoritmo. APP,
que ya posee el boundary de command promovido, podrá invocarla. EXECUTOR no
recibirá EXECUTE sobre ella.

## Transaction ownership

El caller es dueño del único `atomic`. La nueva primitiva comprueba
`connection.in_atomic_block`; fuera de una transacción falla antes de escribir.
No usa `atomic(durable=True)`, commit, rollback, `on_commit` ni side effects. No
crea savepoint: todo fallo debe abortar la unidad completa, no permitir que el
caller continúe y complete ActionExecution. La operación puede anidarse bajo un
outer atomic precisamente porque no administra el boundary.

Se añadirá un binder interno de tenant context que sólo funcione dentro de una
transacción ya abierta y acepte únicamente `TrustedTenantIdentity`; no reemplaza
ni relaja el `trusted_tenant_context` público.

## Privilege model

Se elegirá un rol owner dedicado `isosmart_qms_action_owner` (nombre de
despliegue configurable), `NOLOGIN`, non-superuser, `NOBYPASSRLS`, `NOINHERIT`
y no-owner de las tablas. Recibirá sólo las operaciones de tabla/función que la
primitiva necesita y policies tenant-scoped específicas. No se otorgará su
membresía a EXECUTOR ni a otro principal runtime.

Una función externa exacta, conceptualmente
`defer_opportunity_evaluation(execution_id, authorization_id)`, será
`SECURITY DEFINER`, propiedad de ese rol, con:

- `search_path = pg_catalog, pg_temp` y referencias plenamente calificadas;
- cero SQL dinámico y tipos exactos;
- `REVOKE ALL ... FROM PUBLIC` en la misma migration;
- EXECUTE sólo para EXECUTOR;
- tenant derivado de `current_setting('app.tenant_id', true)` y contexto
  missing/empty fail-closed;
- ActionExecution, Authorization, ActionPlan, hash, Approval, Organization,
  target lineage/revision/status/fingerprint derivados server-side;
- literals internos `opportunity.defer_evaluation`, `Opportunity`,
  `under_evaluation` y `deferred`;
- ninguna entrada de action type, desired status, field, value, tenant u
  Organization libre;
- lock/revalidación del leaf y llamada a la primitiva compartida.

EXECUTOR seguirá siendo LOGIN non-superuser, `NOBYPASSRLS`, `NOINHERIT`,
non-owner, sin Opportunity INSERT/UPDATE/DELETE. `SECURITY DEFINER` eleva sólo
durante la llamada exacta; la función no hace commit y participa en la
transacción del caller.

## RLS

No se usa `BYPASSRLS`. El function owner no será owner de tablas, por lo que
RLS continúa aplicando. Sus policies sólo aceptarán
`tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid` y la
función volverá a verificar tenant/Organization contra Plan/Authorization/
Execution/Opportunity. A-only, B-only y none-deny se deberán probar con roles
reales. FORCE RLS y los triggers de tenant/Organization inmutables permanecen.

## Lock order y concurrencia

Orden global futuro:

1. ActionExecution/idempotency identity;
2. lecturas inmutables Authorization/Plan/Approval (sin lock mutable);
3. Opportunity expected leaf/lineage;
4. Opportunity event stream sequencing;
5. Opportunity audit stream;
6. execution event stream;
7. execution audit stream;
8. Outbox/Receipt inserts asociados.

El public Opportunity command usa el sufijo desde el paso 3. Así no invierte
locks frente al adapter. La primitiva usa `SELECT ... FOR UPDATE` sobre la
revisión esperada y revalida ausencia de successor; la unique de predecessor
sigue como segunda defensa. Deadlock/serialization/unique race abortan todo y
nunca se interpretan como éxito.

## Threats y tradeoffs

La elevación DB aumenta la severidad de un bug de función; se limita mediante
contrato sin parámetros libres, owner no-login/no-bypass, search path seguro,
RLS, full qualification, grants exactos y tests de bypass. Mover el núcleo de
status transition a una función versionada aumenta complejidad de migration,
pero elimina dos riesgos mayores: lógica de negocio duplicada y DML genérico
del executor.

El commit único sólo es apropiado para esta acción PostgreSQL interna. No crea
precedente para mantener transacciones abiertas durante HTTP, provider, shell,
filesystem o cualquier efecto externo.

## Compensation

`opportunity.resume_evaluation` no se incluye ni se concede implícitamente. Un
POC de compensation, si Phase 16 lo exige, tendrá wrapper, Plan, Approval,
Authorization, idempotency y tests separados. Nunca se parametriza el wrapper
forward para aceptar `under_evaluation` como desired status.

## POC restrictions y rollback

Esta decisión autoriza sólo diseñar/implementar un POC efímero PostgreSQL 18.6
en Phase 16. No autoriza producción, staging, DB compartida, adapter registrado,
allowlist runtime ni grants en este gate.

La reversa futura de 0015 revocará EXECUTE, eliminará wrappers/primitiva y
policies/grants del function owner, restaurará constraints Phase 14 y eliminará
el role efímero mediante el bootstrap/finalizer. Los datos de prueba vivirán
sólo en la DB efímera y su teardown será obligatorio.
