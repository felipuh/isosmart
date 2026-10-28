# ADR-0001: monolito modular y transformación incremental

- Estado: Propuesto
- Fecha: 2026-08-13

## Contexto

El sistema es un monolito Django/React con capacidades valiosas y duplicación de entidades entre apps. Un rewrite o microservicios tempranos aumentarían riesgo de datos, contratos y operación.

## Decisión

Mantener un monolito modular, organizado por bounded contexts, y aplicar strangler/expand-contract. Consolidar identidades de dominio mediante servicios y mappings antes de retirar modelos legados. Las cláusulas y normas son datos versionados, no apps Django.

## Consecuencias

Se conserva despliegue simple y se habilitan migraciones graduales. Temporalmente existirán adaptadores de compatibilidad y deuda explícita. Cualquier extracción futura necesita evidencia de escala, ownership y SLO.
