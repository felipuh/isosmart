# ADR-0007: primera acción QMS para un adapter de dominio controlado

- Estado: Aceptado
- Fecha: 2026-08-24
- Decisión de gate: no seleccionar una acción todavía

## Contexto

Phase 14 promovió `ActionExecution` y `ActionExecutionReceipt` con
`SyntheticNoOpExecutor` como única implementación ejecutable. Phase 15 debe
decidir, sólo por diseño y sin mutar el QMS, si existe exactamente una acción
interna, de bajo impacto, reversible, idempotente, tenant/Organization-safe y
autorizable de forma exacta que pueda convertirse posteriormente en el primer
adapter real.

Las fuentes originales definen los objetos empresariales, el orden
`Human Decision Gate -> Execute -> Effectiveness`, la separación de A0-A4 y la
regla general de que A4 sólo aplica dentro de guardrails preaprobados,
reversibles y monitorizados. No definen, para ninguno de los objetos promovidos,
una transición concreta clasificada como de bajo impacto, su conjunto cerrado
de estados, sus precondiciones de negocio ni un inverso/compensación
semánticamente válido.

## Candidatos considerados

Se revisaron todos los objetos empresariales promovidos permitidos por el gate:

- actualización de Stakeholder;
- supersesión de StakeholderRequirement;
- actualización de Process;
- supersesión de ContextItem;
- revisión de QmsScope;
- revisión de Risk;
- cambio de estado de Opportunity;
- cambio de estado de Objective;
- cambio de estado de Change;
- revisión de MeasurementDefinition;
- revisión de metadata de Document;
- supersesión de Evidence;
- evolución de Recommendation.

Recommendation no tiene un command de evolución material promovido: su fila y
sus Basis son inmutables. Los demás candidatos tienen algún command promovido,
pero ninguno tiene a la vez una clasificación de bajo impacto y un inverso de
negocio respaldados inequívocamente por las fuentes.

## Decisión

No se selecciona candidato y Phase 15 queda **NOT PROMOTED**.

No se define ni registra un `ControlledDomainAdapter`, no se crea migration
`0015`, no se cambia el allowlist y no se añade un executor. El
`SyntheticNoOpExecutor` continúa como única implementación capaz de completar.

La ausencia de selección es una decisión fail-closed, no una preferencia de
implementación. Un campo actualizable por SQL o un command que crea una nueva
revisión no demuestra reversibilidad empresarial. Tampoco se puede clasificar
como `standard` una mutación concreta usando únicamente la regla genérica
“A4 sólo para tareas reversibles y preautorizadas”.

## Alternativas rechazadas

### Cambiar un estado de Opportunity, Objective o Change

Se rechazó porque las fuentes enumeran el campo `status` pero no sus valores,
transiciones, terminalidad ni inversos. Los commands promovidos aceptan texto no
vacío; por tanto, no ofrecen todavía un dominio cerrado que permita autorización
exacta o compensación determinística. Change además puede afectar procesos y
approval, por lo que no se puede asumir impacto bajo.

### Actualizar Process

Se rechazó porque el command permite cambiar nombre, owner, tipo y estado en una
misma frontera. La fuente no identifica un subconjunto bajo impacto ni define la
semántica de restaurar ownership/status. El diagrama incluso relaciona Approval
con cambios de Process, confirmando que no puede considerarse trivial.

### Actualizar Stakeholder

Se rechazó porque nombre, tipo y relevance score pueden afectar el análisis de
partes interesadas y requisitos dependientes. No existe clasificación de impacto
ni semántica fuente para revertir relevance score sin reinterpretrar decisiones
intermedias.

### Crear una revisión que copie el estado anterior

Se rechazó para StakeholderRequirement, ContextItem, QmsScope, Risk, Opportunity,
Objective, Change, MeasurementDefinition y Evidence. Conserva la historia y
puede ser una futura compensación técnica, pero la fuente no declara que la
revisión restaurada neutralice el efecto empresarial. QmsScope, Change, Risk,
Objective y Evidence pueden tener efectos interpretativos o de gobierno aun
cuando la fila previa se copie.

### Revisar metadata de Document

Se rechazó porque `owner_id` puede afectar responsabilidad/acceso y `doc_type`
puede afectar control documental. La fuente exige creación, actualización y
control de información documentada, pero no clasifica esta operación concreta
como baja ni declara un inverso de negocio.

### Mutar Recommendation

Se rechazó porque la foundation promovida la trata como propuesta advisory
inmutable; un cambio material crea otra Recommendation. No existe command de
estado respaldado por fuente que el adapter pueda reutilizar.

## Contrato y autorización

No se congela un contrato tipado específico sin una acción seleccionada. La
próxima decisión debe proporcionar, como evidencia fuente/policy versionada:

1. un `action_type` único y un `target_type` único;
2. campos de estado inicial y deseado con valores y transiciones cerrados;
3. definición explícita de impacto `standard` para esa transición;
4. inverso/compensación empresarial exacto;
5. precondiciones completas y verificables;
6. command promovido exacto que se reutilizará;
7. límite de autonomía y requisito de Approval.

Después de eso, la autorización deberá enlazar exactamente Authorization, plan
y hash, action/target, expected state, Approval, Decision y Policy. Para el
primer adapter se mantendrá Approval humano obligatorio y techo A3 salvo una
política fuente posterior más restrictiva o inequívoca.

## Modelo transaccional futuro

Si una acción llega a ser seleccionada y continúa siendo sólo PostgreSQL/QMS
interno, la preferencia es una única transacción:

`revalidación + lock de target + command de dominio + DomainEvent + Outbox +`
`Audit de dominio + terminalización/Receipt de ActionExecution`.

La selección deberá fijar orden de locks para evitar deadlocks, comenzando por
el artifact de ejecución/idempotencia y después el aggregate target, o demostrar
el orden opuesto de manera uniforme en todos los paths. Cualquier inconsistencia
o fallo de event/audit debe hacer rollback de todo el efecto.

## Idempotencia y concurrencia futuras

La identidad debe incluir tenant, exact Authorization, plan hash, action type,
target y expected state/version. Replay exacto devuelve el Receipt existente;
misma clave con material distinto es conflicto. Ejecuciones concurrentes deben
serializar mediante lock/version guard del command y fallar cerradas cuando el
target ya no coincide con el estado autorizado. No se decide todavía si un
target ya en estado deseado es éxito idempotente o conflicto: esa semántica debe
venir con la acción elegida.

## Compensación y EffectivenessCheck

La compensación futura será otro command gobernado, autorizado, idempotente,
evented y auditado; nunca SQL directo. No se implementa ni se afirma un inverso
hasta que exista evidencia de negocio. Compensation revierte o neutraliza el
efecto; EffectivenessCheck mide si se logró el resultado y sigue siendo una
etapa separada.

## Seguridad

El executor futuro no recibirá UPDATE genérico sobre tablas QMS. Deberá invocar
una frontera estrecha de servicio/función que preserve RLS ENABLE+FORCE,
composite tenant/Organization checks, invariantes, eventing y audit. APP,
WORKER, PROJECTOR, AUDIT WRITER y curadores no obtienen ejecución real por esta
decisión.

## Riesgos

- Elegir un status por conveniencia convertiría strings abiertos en autoridad de
  negocio inventada.
- Confundir revisionado con reversibilidad podría dejar consecuencias de negocio
  sin neutralizar.
- Clasificar impacto por intuición permitiría bypass de Human Decision Gate.
- Una función genérica model/field/value ampliaría privilegios y el blast radius.
- Separar la mutación y ActionExecution en transacciones distintas podría dejar
  estados inconsistentes para un adapter puramente interno.

## Rollback y criterios de salida

Este ADR no introduce runtime ni schema; su rollback documental es reemplazarlo
por un ADR posterior cuando nueva evidencia controlada resuelva los blockers.
El gate puede reabrirse sólo con una especificación fuente/policy versionada que
fije para una única acción los siete elementos del contrato y permita repetir
la matriz Phase 15 sin ningún FAIL.
