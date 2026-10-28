# ADR-0002: AdminApps como control plane

- Estado: Aceptado para Stage EXT
- Fecha: 2026-08-13

## Decisión

AdminApps conserva autoridad sobre identidad, tenant global, acceso de producto, entitlements y billing/subscription del ecosistema. ISO Smart mantiene proyecciones locales idempotentes, enlazadas por identificadores externos, y datos propios del QMS. Validaciones obligatorias fallan cerradas; no existe fallback silencioso de autorización.

La entidad física local objetivo se denomina `TenantProjection`: UUID interno estable para FK/RLS, `adminapps_tenant_id` externo único e inmutable, source version/event ID, timestamps y estado de reconciliación. `Organization` representa el dominio QMS y no el tenant global. Identity/MFA/global roles usan `UserProjection`; assignments puramente QMS pueden ser locales. `tenant_id` no se reasigna por CRUD; cualquier transferencia futura es una operación administrativa explícita, dualmente autorizada y auditada.

El identificador canónico del tenant es `apps.organizations.Organization.id` de AdminApps. La creación activa lo genera como UUID y el trigger de AdminApps impide su modificación. ISO Smart conserva el mismo valor en `TenantProjection.adminapps_tenant_id`, mientras genera IDs propios para la proyección y para cada QMS `Organization`. La relación tenant → organización QMS admite múltiples organizaciones. El contrato v1 inicia `source_version=1` y preserva cada evento autenticado en el recibo de ingreso.

## Consecuencias

Las tablas locales de billing actuales no pueden seguir como autoridad competidora: se migran a proyección/cache o se deprecan después de reconciliación. Test/demo puede usar fallback explícito, nunca producción. La indisponibilidad del control plane produce `503/403` accionable, no concesión de acceso.

La semántica completa de lifecycle, sync, errores y onboarding está en `docs/transformation/ISO_SMART_AI_TENANT_MODEL.md` y `ISO_SMART_AI_ADMINAPPS_CONTRACT.md`.
