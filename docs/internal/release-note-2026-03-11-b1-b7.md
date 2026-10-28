# Release Note - Cierre B1-B7

Fecha: 2026-03-11
Rama: development

## Resultado
Se completaron y validaron todas las brechas B1-B7 detectadas en la auditoria de comparacion entre documentacion e implementacion.

## Cambios clave
- B1: `planning` y `resources` estandarizados con `OrganizationScopedViewSetMixin`.
- B2: `sca` protegido con autenticacion y aislamiento por `organization_id`.
- B3: `sie` migrado a `organization_id` con backfill y filtros tenant en sus 4 viewsets.
- B4: carga de documentos alineada a `POST /documents/`.
- B5: acceso a Operaciones agregado en la navegacion principal.
- B6: `asb/spm` endurecidos con `organization_id`, mixin y migraciones de backfill.
- B7: Settings alineado a endpoints reales; historial de backups implementado y persistido via `AuditLog`.

## Settings (detalle B7)
- Endpoint nuevo: `GET /api/settings/backups/`.
- Endpoint existente reforzado: `POST /api/settings/trigger_backup/` con trazabilidad en `AuditLog`.
- Frontend:
  - `getBackupHistory(organizationId, limit)` contra `/settings/backups/`.
  - `createBackup(organizationId)` usa alias de `triggerBackup`.
  - UI de historial en panel de Settings con `data-testid="settings-backup-history"`.

## Validacion ejecutada
- `./venv_ai/bin/python manage.py check`
- `./venv_ai/bin/python manage.py test core --settings=backend.settings_test`
- `npm run build`
- `npx playwright test tests/e2e/scope-process-runtime.spec.js`
- `npx playwright test tests/e2e/settings-backup-runtime.spec.js`

## Commits de referencia
- `d6324df`
- `9d7925b`
- `eb3359b`
- `bef1e80`
- `31a92a0`
- `fe3fe1b`
- `4a41833`

## Nota operativa
El backup manual mantiene trazabilidad completa en base de datos mediante `AuditLog`; no genera un artefacto externo versionado fuera del sistema.
