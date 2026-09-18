# ADR-0016: Separate historical fact from rematerialization eligibility and require transitive retention closure

- Estado: Aceptado para gobernanza y futuros gates de retencion
- Fecha: 2026-09-04
- Sucede a: ADR-0015 sin reescribir ADR-0001--ADR-0015
- Policy: `historical-lifecycle-evidence-transitive-retention-closure-policy/v1`
- Alcance: decision arquitectonica; sin migration, database, Activation,
  RuntimeAdoption, runtime, deployment o reconstruccion

## Contexto

Phase 29 demostro una Publication nativa exacta y retuvo su claim, Publication,
event, Outbox y governance Audit antes de destruir el entorno efimero. Phase
31.1 demostro que el paquete no retuvo la fila
`normative.curation_audit.id = 12d811ab-c3b4-4615-8972-75008a36e327`.
Migration 0022 exige esa fila mediante FK `NOT NULL UNIQUE ON DELETE RESTRICT`.

Los hechos no son contradictorios: la Publication ocurrio, pero su paquete no
puede rematerializar fielmente el grafo relacional congelado. Fabricar la fila,
relajar el FK o invalidar retroactivamente Phase 29 falsearia historia.

## Decision 1: estados independientes

Se adoptan capacidades y estados independientes:

```text
historical_fact
evidence_completeness
faithful_rematerialization_eligibility
Activation_eligibility
RuntimeAdoption_eligibility
```

Ninguno implica al siguiente. La verificacion historica de un artefacto no
otorga capacidad de rematerializacion ni autoridad operacional.

## Decision 2: tratamiento de Phase 29

Publication `e97576de-d4ef-520d-8592-d376ed401221` queda clasificada de forma
append-only como `HISTORICALLY_VERIFIED_NON_REMATERIALIZABLE`, con incidente
`RETENTION_CLOSURE_BREACH`.

Su hecho historico y evidencia retenida permanecen validos e inmutables. El
paquete no puede ser input de Activation, RuntimeAdoption, recovery, migration
bootstrap, deployment o live release. La dependencia ausente no se reconstruye.
Phase 31 no se reintenta sobre ese paquete y Phase 32 permanece bloqueada.

## Decision 3: Transitive Retention Closure

Antes del teardown de un POC futuro, cada dependencia relacional o semantica
obligatoria alcanzable desde Publication, Activation o RuntimeAdoption debe
tener exactamente una disposicion gobernada y verificable. La closure se deriva
del snapshot exacto de schema/FKs y de un registro versionado de dependencias
semanticas; un UUID aislado no cuenta como material retenido.

Teardown y promotion requieren `closure_complete=true`. Una omision obligatoria
no clasificada produce `RETENTION_CLOSURE_BREACH`, prohibe reconstruccion y
cierra toda continuation que dependa de rematerializacion.

## Decision 4: continuidad segura

La ruta preferida es un futuro experimento sintetico nuevo, con lineage,
fixture, identidades y cadena de gobernanza nuevas, closure completa antes del
teardown e Application/Publication/Activation independientes. No reutiliza IDs
de Phase 29, no afirma recovery o continuidad y no incluye RuntimeAdoption.
Requiere un gate posterior de diseno/autorizacion; esta ADR no lo ejecuta.

## Alternativas rechazadas

1. Reconstruir la curation audit: fabrica evidencia historica.
2. Relajar/eliminar el FK: debilita el contrato promovido y falsea closure.
3. Declarar rematerializable el paquete: contradice Phase 31.1.
4. Invalidar Phase 29: confunde deficiencia de retencion con ausencia del hecho.
5. Grandfathering operacional: hereda autoridad desde evidencia incompleta.
6. Reintentar Phase 31 o avanzar a Phase 32: depende del grafo ausente.

## Consecuencias

La historia permanece verdadera y consultable, pero el paquete Phase 29 queda
permanentemente no operacional. Futuros manifests son mayores y deben incluir
closure, schema snapshot, semantic registry, disposiciones y digest. El costo
de retencion aumenta; a cambio, teardown deja de destruir silenciosamente
material obligatorio para gates futuros.

Migrations 0001--0023 no cambian y 0024 permanece ausente. Esta decision no
autoriza database, reconstruccion, Activation, RuntimeAdoption, runtime,
produccion, staging, deployment ni efectos externos.
