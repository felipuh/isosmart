# Documentación Interna - ISO Smart

Este directorio centraliza documentación técnica interna del sistema.

## Índice

- [Arquitectura, Integraciones y Multitenancy](./arquitectura-integraciones-multitenancy.md)
- [Manual de Operación por Roles](./manual-operacion-por-roles.md)
- [Mapa Operativo Nginx Smart3AI (2026-05-17)](./NGINX_MAPA_DOMINIOS_SMART3AI_2026-05-17.md)

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

## Asistente IA (entorno)

- Para activar proveedor real del asistente IA, crear `backend/.env` desde `backend/.env.example`.
- Definir `AI_ASSISTANT_API_URL`, `AI_ASSISTANT_API_KEY` y `AI_ASSISTANT_MODEL`.
- Si `AI_ASSISTANT_API_KEY` no está definida, el panel usa fallback local automáticamente.
