# ADR-0006: contrato OpenAPI como frontera backend/frontend

- Estado: Propuesto
- Fecha: 2026-08-13

## Decisión

Introducir un OpenAPI versionado y ampliarlo por casos de uso. Cada operación declara request/response/error, paginación/filtros, permisos, tenant scope, idempotencia y efectos de auditoría/eventos. Generar cliente y tipos frontend; mantener aliases actuales solo como compatibilidad temporal con métricas de uso y fecha de retiro.

## Consecuencias

Se elimina drift manual y se habilitan contract tests. No se crearán endpoints por conveniencia de pantalla sin modelo y caso de uso.
