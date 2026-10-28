# ADR-0010: controlled execution recovery and retained-history migration policy

- Estado: Aceptado para el POC efímero endurecido
- Fecha: 2026-08-24
- Sucede a: ADR-0009 sin reescribir 0007–0009
- Alcance: una sola acción forward `opportunity.defer_evaluation`; compensation separada

## Contexto

Phase 16 probó una transacción atómica y replay después de perder la respuesta de
aplicación, pero no el caso real en que el cliente envía `COMMIT` y pierde la
conexión antes de conocer el resultado. También dejó dos límites explícitos: dos
primeros callers podían llegar simultáneamente al INSERT del claim y la reversa
0015 sólo estaba probada antes de crear historia controlada.

Execution success significa que la transición autorizada hizo commit. No prueba
que la decisión produjo beneficio empresarial. `EffectivenessCheck` continúa
siendo una etapa posterior y separada.

## Decisión de recuperación de COMMIT

Después de una pérdida de transporte durante COMMIT no se reejecuta a ciegas.
El caller reconecta bajo tenant confiable y consulta una capability exacta de
reconciliación. La identidad incluye tenant, idempotency key hash, Authorization,
ActionPlan/hash, action, target lineage/revision y Organization.

Resultados cerrados:

- `COMMITTED`: existe una sola ActionExecution terminal y un Receipt exacto; la
  revisión resultante, event/outbox/audit de Opportunity y event/outbox/audit de
  execution existen una vez y coinciden en IDs, hash, target, trace y provenance.
  Se devuelve el Receipt existente con `replayed=true`.
- `NOT_COMMITTED`: no existe claim y el target continúa siendo exactamente la
  revisión/estado/fingerprint autorizado sin successor. Sólo entonces puede
  ejecutarse una vez.
- `INCONSISTENT`: cualquier claim running/abandonado, Receipt ausente, artifact
  faltante/duplicado, provenance diferente o target inseguro falla cerrado y
  requiere intervención operativa.

Cada reconciliación agrega una señal operativa a un stream de audit separado,
con hash de idempotencia y conteos observados; no crea `DomainEvent` empresarial
ni registra la key raw, prompt, token o secreto.

## Claim ownership y crash recovery

`qms.action_execution` sigue siendo el owner durable del claim, protegido por
`UNIQUE(tenant_id,idempotency_key)`. 0016 añade un advisory transaction lock
determinista antes del lookup/insert para cerrar exclusivamente la ventana en
que todavía no existe fila. Esta combinación se eligió porque el lock solo
serializa la creación; no reemplaza el owner durable ni su constraint.

El primer caller crea el row. Un caller exacto concurrente espera y reconstruye
el mismo Receipt. Distinta Authorization/Plan/target/action bajo la misma key es
conflict y el claim nunca se reasigna.

La capability controlada crea claim, mutación y terminalización dentro de una
sola transacción. Un crash antes del commit revierte también el claim; por tanto,
el path actual no produce un claim abandonado durable. Si se observa uno por
historia legada, corrupción o intervención privilegiada, no hay lease, timeout
ni stealing: `INCONSISTENT` y reconciliación humana/operativa explícita. Una
política futura de lease requiere nueva evidencia/policy.

## Política de historia retenida

Se adopta la opción **C**: después de la primera ejecución controlada, 0015 es
una frontera forward-only para deployment. `0016 -> 0015` es reversible sin
pérdida porque sólo retira recovery/ACL evolution. `0015 -> 0014` no es un
rollback de negocio y queda intencionalmente bloqueado cuando existen rows
`controlled_opportunity`; no se borran ni reescriben ActionExecution, Receipt,
Opportunity revisions, events, outbox, audit o compensation para hacer pasar
constraints antiguas.

El rollback operativo es expand/contract:

1. revocar la capability recoverable para impedir nuevos defer;
2. preservar lectura, provenance e historia;
3. mantener el public Opportunity command independiente;
4. observar/reconciliar executions y outbox;
5. corregir o reemplazar código mediante una migration forward;
6. contraer sólo tras aprobación, backup/restore y evidencia de cero uso.

Schema rollback no equivale a compensation. Resume sigue exigiendo otro Plan,
Approval, Authorization, idempotency y execution. Revocar forward no autoriza,
ejecuta ni borra compensation.

## Least privilege y observabilidad

El function owner continúa NOLOGIN, NOSUPERUSER, NOINHERIT, NOCREATEDB,
NOCREATEROLE, NOREPLICATION, NOBYPASSRLS, sin ownership de tablas/sequences ni
CREATE de schema. 0016 retira SELECT no usado sobre Organization,
UserProjection y Recommendation; añade sólo SELECT tenant-scoped sobre immutable
audit para verificar artifacts. EXECUTOR pierde los wrappers 0015 y recibe sólo
los wrappers recoverable y reconciliation exactos. PUBLIC mantiene cero EXECUTE.

Campos operativos estables: tenant, Organization, ActionExecution, ActionPlan ID/
hash, governance artifact, target lineage/revisions, trace, hashed idempotency,
reconciliation outcome/reason, execution outcome, replay/retry classification y
compensation lineage. El repo no posee una foundation de métricas runtime; se
documentan nombres conceptuales (`controlled_execution_reconciled`,
`controlled_execution_inconsistent`, `controlled_execution_replay`) sin añadir
Prometheus u OpenTelemetry.

## Boundary de EffectivenessCheck

Las fuentes nombran `EffectivenessCheck` y los campos mínimos `subject_type`,
`subject_id`, `method`, `due_at`, `result`, `evidence_id`, además del orden
Execute → Effectiveness y el requisito de medir/revisar eficacia. No fijan una FK
exacta a ActionExecution, outcome cerrado, actor/authority, regla para `due_at`,
cardinalidad de Evidence, relación con MeasurementDefinition ni versionado.

Por ello Phase 17 define sólo el modelo candidato: record histórico separado,
append-only, enlazado al exacto Execution/Plan/Decision/Recommendation, target y
revisiones before/resulting, con Evidence explícita y MeasurementDefinition sólo
cuando el método la respalde. No se congela schema, actor, timing ni outcomes
hasta cerrar esos blockers mediante Product Policy. No modifica execution,
Receipt, Approval, Authorization, Plan ni Recommendation; ineffective nunca
dispara compensation o aprendizaje automático.

## Consecuencias

Se añadió migration 0016 porque serialization, recovery functions, audit read y
privilege minimization son cambios persistentes reales. No se añadió segunda
acción, EffectivenessCheck, telemetry externa, learning, deployment o efecto
externo. Operaciones deben tratar `INCONSISTENT` como incidente, conservar el
audit ID y no resolverlo con SQL/DML ad hoc.

