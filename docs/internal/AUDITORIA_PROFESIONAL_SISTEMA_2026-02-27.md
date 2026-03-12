# Auditoría profesional del sistema ISO Smart

Fecha: 2026-03-11 (actualizado)

## Resumen ejecutivo
Se realizó revisión de profesionalización y simplicidad con foco en seguridad multi-organización, consistencia i18n, y mantenibilidad frontend/backend.

### Estado actual
- Billing: sólido funcionalmente (suscripción, pagos, evidencia, notificaciones, timeline).
- i18n: consolidado en módulos críticos; `performance/*` e `improvement/*` ya operan con claves semánticas y `common.*`.
- Seguridad multi-tenant: se cerraron brechas críticas en esta iteración.

## Mejoras aplicadas en esta iteración

### 1) Seguridad multi-organización (CRÍTICO)
- `BillingViewSet`: ahora valida que el usuario solo resuelva organizaciones permitidas por `UserProfile` (excepto superuser).
- `AuditLogViewSet`: ahora restringe queryset por organizaciones permitidas del usuario (excepto superuser).

Archivo:
- `backend/core/views.py`

Impacto:
- Evita acceso cruzado entre organizaciones en endpoints de billing y auditoría.

## Hallazgos prioritarios pendientes

### P1 — i18n semántico al 100% (resuelto en módulos críticos)
Estado:
- `performance/*` e `improvement/*` completaron migración a claves semánticas de módulo.
- Se mantiene `common.*` para mensajes y acciones compartidas.

### P1 — Consistencia de mensajes de error frontend (resuelto en performance/improvement)
Estado:
- Se estandarizó el patrón `setError(t('common.messages.errorTryAgain'))` en CRUDs críticos.
- Se incorporó banner reusable (`CrudErrorBanner`) para feedback visual uniforme.
- Pendiente: extender el mismo patrón al resto de módulos CRUD fuera de performance/improvement.

### P2 — Endpoints legacy sin scope fuerte (resuelto)
Estado:
- Endpoints `dashboard_summary`, `risk_matrix` y `context_latest` usan `IsAuthenticated` + `_resolve_scoped_org_id()` con enforcement tenant.

### P2 — Estandarización visual de CRUDs (parcialmente resuelto)
Estado:
- Se implementó mini-kit reusable en front (`CrudPageHeader`, `CrudErrorBanner`, `CrudEmptyState`) y se aplicó en CRUDs de performance/improvement.
- Pendiente: extender cobertura a otros módulos para uniformidad transversal total.

## Patrón oficial recomendado para nuevas pantallas
1. `useI18n()` obligatorio.
2. No strings visibles hardcoded.
3. Claves semánticas por módulo (`settings.billing.*`, `dashboard.billing.*`, etc.).
4. Permisos y scope organizacional validados en backend.
5. Build/check en cada lote.

## Próxima iteración sugerida (ordenada)
1. ~~Migración i18n semántica completa en `performance/*`.~~ Resuelto: no quedan `literals.*` en uso activo.
2. ~~Migración i18n semántica completa en `improvement/*`.~~ Resuelto: idem.
3. ~~Refactor de endpoints legacy `dashboard_summary/risk_matrix/context_latest` a patrón DRF scoped.~~ Resuelto: ya usan `@permission_classes([IsAuthenticated])` y `_resolve_scoped_org_id()` con enforcement tenant.
4. Extender el patrón de errores visuales unificado (`setError` + banner reusable) al resto de CRUDs fuera de performance/improvement.
5. Extender el mini-kit CRUD reusable al resto de módulos para homogeneidad visual completa.
