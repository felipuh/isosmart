# Cierre B1-B7

Fecha: 2026-03-11

## Alcance
- Cierre de las brechas B1-B7 identificadas en la auditoria comparativa entre documentacion e implementacion.
- Normalizacion de multitenancy en modulos historicos, alineacion frontend/backend y cobertura de validacion.

## Entregables cerrados
- B1: `planning` y `resources` migrados a `OrganizationScopedViewSetMixin`.
- B2: `sca` protegido con autenticacion y filtro por `organization_id`.
- B3: `sie` migrado de organizacion textual a `organization_id` con backfill y filtros en sus 4 viewsets.
- B4: carga de documentos alineada a `POST /documents/`.
- B5: acceso a Operaciones agregado en la UI principal.
- B6: `asb/spm` endurecidos con `organization_id`, mixin y migraciones de backfill.
- B7: `settingsService` alineado a endpoints reales; historial de backups implementado con `GET /settings/backups/` y persistencia en `AuditLog`.

## Validacion ejecutada
- `./venv_ai/bin/python manage.py check`
- `./venv_ai/bin/python manage.py test core --settings=backend.settings_test`
- `npm run build`
- Playwright runtime smoke para scope/processes
- Playwright runtime para settings backup/export

## Commits relevantes
- `d6324df` multitenancy ASB/SPM
- `9d7925b` smoke E2E scope/processes
- `eb3359b` SIE `organization_id` + fixes de settings
- `bef1e80` endpoint `GET /settings/backups/` + auditoria de export/backup
- `31a92a0` UI de historial de backups + prueba runtime de settings
- `fe3fe1b` alineacion final del documento comparativo

## Nota operativa
- El disparo de backup manual sigue siendo un evento de aplicacion con trazabilidad completa en `AuditLog`; no genera todavia un artefacto externo versionado fuera del sistema.