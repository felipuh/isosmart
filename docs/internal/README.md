# Documentación Interna - ISO Smart

Este directorio centraliza documentación técnica interna del sistema.

## Índice

- [Arquitectura, Integraciones y Multitenancy](./arquitectura-integraciones-multitenancy.md)
- [Manual de Operación por Roles](./manual-operacion-por-roles.md)

## Audiencia

- Equipo backend
- Equipo frontend
- QA
- DevOps
- Líder funcional ISO

## Convenciones

- Todas las APIs se exponen bajo prefijo `/api`.
- Todas las consultas de datos multitenant deben incluir `organization_id` o venir respaldadas por JWT con claim de organización.
- Las automatizaciones entre módulos se describen como **sync** y son idempotentes (`update_or_create`).
