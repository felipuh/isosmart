# ADR-0011: effectiveness assessment governance and controlled execution operational readiness

- Estado: Aceptado para gate de implementación posterior; sin schema ni deployment
- Fecha: 2026-08-24
- Sucede a: ADR-0010 sin reescribir ADR-0007–ADR-0010
- Policy: `effectiveness-check-policy/v1`, no normativa

## Contexto

Phase 17 promovió COMMIT ambiguo real, reconciliación cerrada
`COMMITTED|NOT_COMMITTED|INCONSISTENT`, claim durable serializado, least
privilege, historia retenida y disablement de capability. También confirmó que
las diez fuentes separan Execute de Effectiveness y nombran
`EffectivenessCheck(method,due_at,result,evidence_id)`, pero no fijan outcome,
actor, derivación temporal, cardinalidad de evidencia, relación exacta con
MeasurementDefinition, correcciones ni contrato de evento.

Inventar esas decisiones como requisitos ISO sería semantic laundering. ISO
Smart puede cerrarlas mediante Product Policy explícita, versionada y no
normativa sin tocar fuentes, historia normativa o certifiability.

## Decisión de EffectivenessCheck

Se adopta `docs/governance/EFFECTIVENESS_CHECK_POLICY_V1.md` con estado
`APPROVED FOR IMPLEMENTATION GATE`. No crea schema, migration, API ni runtime.

La evaluación v1 aplica únicamente a la ejecución exacta de
`opportunity.defer_evaluation`. Su intención medible es comprobar, durante el
intervalo aprobado, que la Opportunity quedó fuera de evaluación activa para el
propósito de gobernanza y que ninguna decisión/acción downstream no autorizada
frustró ese propósito. El cambio de status por sí solo sigue siendo ejecución,
no eficacia.

Outcomes cerrados:

- `effective`: todos los criterios obligatorios soportados;
- `ineffective`: al menos un criterio de objetivo refutado;
- `inconclusive`: evaluación realizada sin conclusión positiva/negativa fiable;
- `unknown`: evaluación no realizable por evidencia ausente/inválida u otro
  bloqueo registrado.

Ninguno dispara compensation, resume, recomendación, policy/model change,
learning o efecto externo.

## Autoridad y AdminApps

Sólo un humano con categoría `QMS authorized reviewer`, permiso AdminApps
`qms.effectiveness_check.record` (y
`qms.effectiveness_check.supersede` para corrección), identidad/acceso/MFA y
scope vigentes para tenant/Organization puede atestar/crear v1. UserProjection
no concede autoridad. ISO Smart conserva provenance de actor/contexto, pero
AdminApps sigue siendo autoridad de identidad, roles globales, MFA y acceso.

System/measurement pueden producir evidencia/propuesta; no pueden atestar un
outcome v1. Execution succeeded o COMMITTED jamás actúa como assessor.

## Timing, evidencia y MeasurementDefinition

`due_at` es el fin exacto del intervalo observado y momento en que la evaluación
queda due. Debe venir de contexto de planificación de eficacia gobernado,
congelado, aprobado y enlazado server-side; es posterior al commit de la revisión
resultante. No hay ventanas globales 7/30/90 ni timestamp arbitrario de cliente.

Cardinalidad de Evidence: conjunto finito 1..N, sin máximo semántico numérico,
sin truncamiento. Cada referencia es una revisión exacta con hash/provenance;
no latest/current, duplicados exactos, cross-tenant ni cross-Organization.
Revisiones distintas del mismo lineage sólo se permiten para comparación
cronológica exigida por criterios.

MeasurementDefinition es condicionalmente obligatoria: exacta y única si un
criterio/due usa qué/método/momento; ausente en revisión puramente gobernada por
evidencia. No se crea MeasurementRecord ni campos de observación inventados.

## Historia, evento y audit

Cada assessment es inmutable. Corrección crea otro record completo que
supersede el leaf actual, con revisión +1, misma execution/tenant/Organization/
target y razón/actor/time propios. Se prohíben fork, cycle, self-reference,
reuso de predecessor y edición/destrucción del original.

Se elige un único DomainEvent `effectiveness_check.recorded` v1 para original y
corrección. Revision y `supersedes_check_id` expresan lineage; no se duplica la
taxonomía con un evento superseded separado. El evento contiene IDs, outcome,
actor, timing y provenance, no blobs. Check, Evidence links, event, outbox y
ImmutableAuditLog forman una transacción futura atómica.

Audit reconstruye autoridad, execution/receipt/plan/authorization, target
before/resulting, criteria hash, outcome/reason, Evidence IDs/hashes,
MeasurementDefinition, due/assessed time, trace, event/outbox y lineage.

## Decisión operacional

Se adopta `docs/operations/CONTROLLED_EXECUTION_RUNBOOK_V1.md`:

- COMMITTED devuelve Receipt exacto replayed y jamás reintenta;
- NOT_COMMITTED revalida leaf, Approval, Authorization y Plan hash antes de una
  única invocación normal;
- INCONSISTENT abre incidente, preserva artifacts, deshabilita si procede y no
  reintenta/repara automáticamente;
- repair requiere QMS reviewer + Security operator + Release authority y sólo
  procedimiento aditivo/versionado; nunca raw SQL ni rewrite de historia;
- disable y enable son gobernados/auditados; no hay self-enable;
- 0015 queda forward-only tras primera historia controlada;
- observability usa IDs/hashes/provenance sanitizados, sin secretos/prompts;
- SLA/SLO numérico permanece bloqueante para release productivo, no para este
  design gate.

## Alternativas rechazadas

1. Tres outcomes sin `unknown`: pierde diferencia entre evaluación imposible y
   evaluación realizada no concluyente.
2. System assessor directo: fuentes no fijan autoridad ni observation model.
3. MeasurementDefinition siempre obligatoria: las fuentes también admiten
   revisión/evaluación con evidencia y Phase 6 no tiene MeasurementRecord.
4. Evidence única como DDL fuente: insuficiente para criterios múltiples y
   provenance exacta.
5. UPDATE de result o revisions mutables: destruye historia legal/audit.
6. Eventos recorded+superseded: taxonomía innecesaria; lineage en recorded es
   suficiente.
7. Auto-resume al ser ineffective: mezcla effectiveness y compensation y omite
   nuevo Human Decision Gate.
8. Reparación SQL/claim stealing: oculta inconsistencia y rompe historia.

## Consecuencias y restricciones

Los siete blockers quedan cerrados por separación explícita de fuente y Product
Policy. El próximo gate puede diseñar la foundation exacta, pero debe fallar
cerrado si no materializa la authority context, planificación due, Evidence
junction, conditional MeasurementDefinition, lineage, RLS, atomic event/outbox/
audit y no-automation.

Phase 18 no añade migration 0017, modelo, endpoint, segundo QMS action,
telemetría externa, compensation automática, learning, production/staging/shared
enablement ni deployment. Migrations 0001–0016 y los diez sources permanecen
frozen.
