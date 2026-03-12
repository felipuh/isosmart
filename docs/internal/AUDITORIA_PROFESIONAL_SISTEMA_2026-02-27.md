# Auditoría profesional del sistema ISO Smart

Fecha: 2026-02-27

## Resumen ejecutivo
Se realizó revisión de profesionalización y simplicidad con foco en seguridad multi-organización, consistencia i18n, y mantenibilidad frontend/backend.

### Estado actual
- Billing: sólido funcionalmente (suscripción, pagos, evidencia, notificaciones, timeline).
- i18n: mejora considerable; aún hay deuda en módulos con `literals.*` en lugar de claves semánticas.
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

### P1 — i18n semántico al 100%
Problema:
- Aún existen vistas que usan `literals.*` como fallback principal o textos heredados no estructurados por módulo.

Recomendación:
- Migrar progresivamente a claves semánticas:
  - `modules.performance.*`
  - `modules.improvement.*`
  - mantener `common.*` para botones/errores genéricos.

### P1 — Consistencia de mensajes de error frontend
Problema:
- Varias vistas capturan error con `console.error` sin feedback uniforme al usuario.

Recomendación:
- Estandarizar patrón:
  - `setError(t('common.messages.errorTryAgain'))`
  - banner reusable por módulo.

### P2 — Endpoints legacy con `@csrf_exempt` y lógica sin scope fuerte
Problema:
- Existen funciones API legacy en `core/views.py` (summary/risk/context) que no siguen patrón DRF moderno por organización.

Recomendación:
- Migrarlas a ViewSet/APIView con `IsAuthenticated` y filtro por organización.

### P2 — Estandarización visual de CRUDs
Problema:
- Distintas pantallas usan modal/tabla con variaciones de etiquetas y estructura.

Recomendación:
- Definir un mini-kit CRUD reutilizable para:
  - Header + CTA
  - Tabla
  - Modal form
  - Empty state
  - Confirmación de delete

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
4. Unificación de manejo de errores visuales en CRUD frontend. (pendiente)
5. Implementar mini-kit CRUD reutilizable (Header+CTA, Tabla, Modal form, Empty state, Confirmación delete). (pendiente)
