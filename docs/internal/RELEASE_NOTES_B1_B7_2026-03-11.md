# Release Notes B1-B7

Fecha: 2026-03-11
Version: estabilizacion multitenancy y contratos API

## Resumen
Se completa el cierre de brechas B1-B7 identificadas en la comparacion documento vs implementacion, con foco en aislamiento tenant, alineacion frontend/backend y validacion runtime.

## Cambios por brecha

### B1 - Multitenancy en modulos de negocio
- Estandarizacion de vistas de `planning` y `resources` con `OrganizationScopedViewSetMixin`.
- Uso consistente de `self.get_queryset()` en acciones custom.

### B2 - Seguridad tenant en SCA
- Activacion de `IsAuthenticated`.
- Filtro por `organization_id` en consultas.
- Validaciones de alcance para evitar lectura cruzada.

### B3 - Seguridad tenant en SIE
- Migracion de modelo a `organization_id` en `StakeholderProfile`.
- Backfill de datos historicos por nombre de organizacion.
- Filtrado por `organization_id` en los 4 viewsets de SIE.

### B4 - Contrato de carga de documentos
- Alineacion de frontend para usar `POST /documents/`.

### B5 - Navegacion a Operaciones
- Incorporacion del acceso a `operations` en sidebar.

### B6 - Estandar multitenancy en ASB/SPM
- Incorporacion de `organization_id` en modelos de ASB/SPM.
- Endurecimiento de aislamiento con mixin de scoping.
- Migraciones con backfill de datos existentes.

### B7 - Endpoints Settings y respaldo/export
- Correccion de endpoints frontend:
  - `exportData` -> `GET /export/`
  - `createBackup` -> `POST /settings/trigger_backup/`
  - `getBackupHistory` -> `GET /settings/backup_history/`
- Implementacion backend de historial real de backups basado en `AuditLog`.
- Registro de auditoria para eventos de backup y export.

## Validacion
- Pruebas backend (`manage.py test core --settings=backend.settings_test`) en verde.
- Build frontend (`npm run build`) en verde.
- Smoke runtime/E2E validado para flujo autenticado.

## Impacto operativo
- Menor riesgo de fuga de datos entre organizaciones.
- Contratos API consistentes para modulo de configuracion.
- Mayor trazabilidad operativa para acciones de respaldo y exportacion.

## Pendientes
- Evaluar almacenamiento fisico de artefactos de backup (si se requiere backup binario ademas de auditoria de ejecucion).
