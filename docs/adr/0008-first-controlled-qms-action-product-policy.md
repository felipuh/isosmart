# ADR-0008: product policy for the first controlled QMS action

- Estado: Aceptado
- Fecha: 2026-08-24
- Sucede a: ADR-0007 sin reescribir su veredicto histórico

## Contexto

ADR-0007 y Phase 15 fallaron cerrados porque las fuentes establecen objetos y
campos, pero no una transición de estado concreta, clasificación de impacto,
inverso empresarial ni semántica de replay. Inventar esas decisiones como si
fueran ISO habría sido semantic laundering.

ISO Smart sí puede gobernar comportamiento propio de aplicación mediante una
Product Policy explícita, versionada y no normativa, siempre que no cree o
modifique `RequirementControl`, `KnowledgeLayerRule`, conteos certificables ni
historia normativa.

## Decisión

Adoptar `docs/governance/CONTROLLED_QMS_ACTION_POLICY_V1.md` como propuesta de
gobernanza ISO Smart. La policy define únicamente el candidato
`opportunity.defer_evaluation` sobre `Opportunity`, transición
`under_evaluation -> deferred`, compensación gobernada
`opportunity.resume_evaluation`, impacto `standard`, aprobación humana
obligatoria y techo A3.

La policy cierra los blockers semánticos de Phase 15, pero permanece
`PROPOSED — NOT APPROVED FOR CONTROLLED POC`. El command promovido
`change_opportunity_status` posee la transacción externa y rechaza composición
dentro de otra transacción. Phase 14, a su vez, persiste inicio y finalización
alrededor de una invocación separada. No está probado un commit único de target,
DomainEvent/Outbox/Audit y receipt, ni una frontera de privilegio estrecha que
evite DML genérico del executor. Por fail-closed, Phase 15.1 no promueve ningún
adapter ni POC.

## Alternativas consideradas

- Declarar los estados como ISO: rechazado; las fuentes no los definen.
- Seleccionar Objective: rechazado; cambia un compromiso con owner/métrica/
  fecha y tiene mayor impacto que pausar evaluación de una Opportunity.
- Usar Change: rechazado; su propio impacto/approval y procesos afectados hacen
  el delta más material.
- Usar creación/borrado o SQL undo: rechazado; no hay inverso empresarial y se
  destruiría o eludiría historia.
- Aceptar dos transacciones: rechazado; puede quedar mutación sin receipt final
  coherente o receipt sin atomicidad con el evento de dominio.
- Modificar el command en este gate: rechazado; Phase 15.1 es docs-only.

## Consecuencias

ADR-0007 sigue siendo verdad histórica. Hay una policy productiva versionada,
pero no autorización de ejecución. `SyntheticNoOpExecutor` continúa como única
implementación ejecutable; no se cambia allowlist, privilegio, migration, API,
modelo ni command. Un futuro gate de diseño de command/composición debe probar,
sin mutación QMS real, una única transacción y least privilege antes de que otra
fase considere un POC efímero.
