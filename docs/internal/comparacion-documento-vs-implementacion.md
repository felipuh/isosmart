# Comparacion documento vs implementacion

Fecha: 2026-03-16
Base documental comparada:
- `docs/internal/manual-operacion-por-roles.md`
- `docs/internal/arquitectura-integraciones-multitenancy.md`
- `docs/internal/mapeo-modulos-actuales-clave.md`

## Resumen ejecutivo
- Cobertura funcional por modulo: alta.
- Riesgo principal actual: deuda tecnica acotada en endpoints legacy de settings (sin brecha critica activa).
- Estado tras correcciones de esta iteracion: brechas B1-B7 cerradas, onboarding dashboard estabilizado en primer uso (sin 404 por ausencia de snapshot), comercializacion inicial acotada a ISO 9001 y superficie activa frontend/backend sin rutas API huerfanas en servicios vigentes.

## Matriz de brechas

### B1 - Multitenancy estricto en modulos de negocio
- Referencia documental: `arquitectura-integraciones-multitenancy.md` seccion 3.
- Evidencia previa: `planning/views.py` y `resources/views.py` sin `OrganizationScopedViewSetMixin`.
- Riesgo: filtros manuales parciales, mayor probabilidad de desalineacion entre endpoints.
- Accion aplicada: estandarizacion a `OrganizationScopedViewSetMixin` y uso de `self.get_queryset()` en acciones custom.
- Estado: resuelta.

### B2 - Seguridad tenant en Contexto (SCA)
- Referencia documental: validacion 400/403 por organizacion activa.
- Evidencia previa: `backend/ai_modules/sca/views.py` sin `IsAuthenticated` ni filtro por organizacion.
- Riesgo: lectura cruzada de analisis historicos.
- Accion aplicada: auth obligatoria + resolucion de organizacion activa + filtros por `organization_id`.
- Estado: resuelta.

### B3 - Seguridad tenant en Stakeholders (SIE)
- Referencia documental: checklist multitenancy operativo.
- Evidencia previa: `permission_classes` comentado en viewsets y querysets sin aislamiento por organizacion.
- Riesgo: exposicion de registros entre organizaciones.
- Accion aplicada: `IsAuthenticated` activo + migracion a `organization_id` en `StakeholderProfile` con backfill + filtrado por `organization_id` en los 4 viewsets SIE + escritura forzada de `organization_id` en create/update.
- Estado: resuelta.

### B4 - Contrato frontend/backend en carga de documentos
- Referencia documental: operacion diaria de modulo Documentos.
- Evidencia previa: frontend enviaba `POST /documents/upload/` sin endpoint backend correspondiente.
- Riesgo: error de subida en runtime.
- Accion aplicada: frontend alineado a `POST /documents/`.
- Estado: resuelta.

### B5 - Acceso operativo a modulo Operaciones desde UI
- Referencia documental: flujo 8.7 en manual por roles.
- Evidencia previa: rutas de operaciones existentes en `App.jsx`, pero sin entrada en sidebar.
- Riesgo: modulo funcional oculto en navegacion principal.
- Accion aplicada: item `operations` agregado en `Sidebar.jsx`.
- Estado: resuelta.

### B6 - Estandar multitenancy en ASB/SPM
- Referencia documental: regla general de aislamiento por organizacion.
- Evidencia previa: modelos `asb/spm` no tenian `organization_id` directo; aislamiento no estandarizado con mixin.
- Accion aplicada: `organization_id` IntegerField + `OrganizationScopedViewSetMixin` + migraciones con backfill aplicadas en commit d6324df.
- Estado: resuelta.

### B7 - Endpoints inexistentes referenciados desde settingsService.js
- Referencia documental: N/A (brecha detectada en revision de codigo).
- Evidencia: `exportData` llamaba `GET /settings/export/` (sin endpoint); `createBackup` llamaba `POST /settings/backup/` (sin endpoint); `getBackupHistory` llamaba `GET /settings/backups/` (sin endpoint).
- Endpoints reales: `POST /settings/trigger_backup/` (action detail=False en SettingsViewSet); `GET /export/` (FBV en core/urls.py); `GET /settings/backups/` implementado sobre `AuditLog`.
- Accion aplicada: `exportData` alineada a `/export/` con contrato `type`; `createBackup` redirigida a `/settings/trigger_backup/`; `getBackupHistory` conectado a historial real y visible en UI.
- Estado: resuelta.

## Validacion de flujos documentados (impacto)
- Flujo 8.7 -> 10.2: conservado (no se altero sincronizacion en `operations`/`improvement`).
- Flujo 9.2 -> 10.2: conservado (no se altero sync de hallazgos).
- Flujo 9.3 -> 10.3: conservado (no se altero sync de revisiones).
- Dashboard principal y modulos core: sin cambios de contrato de salida.

## Conclusion
- Se cerraron todas las brechas operativas y de seguridad identificadas en la auditoria inicial.
- B3 (SIE tenant), B6 (ASB/SPM tenant) y B7 (settings endpoints) completadas en sesiones posteriores.
- Todos los modulos usan `organization_id` estandar con `OrganizationScopedViewSetMixin` o patron equivalente.
- Auditoria adicional de contratos frontend/backend sobre `frontend/src/services` y `frontend/src/features/*/api` sin rutas irresueltas tras eliminar 3 helpers legacy no utilizados.

## Brechas residuales no bloqueantes
1. Documentacion: algunos textos historicos aun mencionan estados tenant antiguos en documentos no operativos.
2. Operacion local: archivos de logs y backups locales pueden ensuciar `git status` durante pruebas manuales.
3. Settings legacy: existen acciones fuera del mixin estandar, aunque actualmente con validaciones de scope y permisos.

## Politica comercial vigente (marzo 2026)
1. Alcance de comercializacion inicial: ISO 9001:2015 unicamente.
2. Enforcement aplicado en backend y frontend para evitar activacion accidental de otras normas.
3. Preparacion para expansion: habilitacion de normas configurable por entorno y por organizacion sin requerir recodificacion de UI.
4. Variables de configuracion operativa:
- `COMMERCIAL_ENABLED_STANDARDS` (global)
- `COMMERCIAL_ENABLED_STANDARDS_BY_ORG` (override por organizacion)

## Propuesta de implementacion incremental (sin romper)
1. Lote documental: normalizar wording restante en docs internas para eliminar estados ya resueltos.
2. Lote de higiene operativa: formalizar exclusiones de artefactos locales (logs/backups temporales) para mantener arbol limpio en validaciones.
3. Lote de hardening settings: converger acciones legacy de settings al patron comun de scoping para reducir variabilidad futura.
