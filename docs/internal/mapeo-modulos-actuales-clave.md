# Mapeo de modulos actuales clave

Fecha: 2026-03-12
Objetivo: Inventariar el flujo real `ruta UI -> servicio frontend -> endpoint backend` y clasificar el estado de scoping multitenant por modulo.

## Fuentes revisadas
- `frontend/src/App.jsx`
- `frontend/src/components/Layout/Sidebar.jsx`
- `frontend/src/services/*.js`
- `frontend/src/features/*/api/*.js`
- `backend/backend/urls.py`
- `backend/*/urls.py`
- `backend/*/views.py`
- `backend/ai_modules/*/urls.py`
- `backend/ai_modules/*/views.py`
- `backend/core/organization_scoping.py`

## Mapa global de enrutamiento
- Base frontend API: `frontend/src/services/api.js` usa `baseURL: '/api'`.
- Composicion backend central: `backend/backend/urls.py` agrega modulos en prefijos:
  - `/api/` (core)
  - `/api/auth/`
  - `/api/leadership/`
  - `/api/resources/`
  - `/api/planning/`
  - `/api/operations/`
  - `/api/performance/`
  - `/api/improvement/`
  - `/api/sca/`, `/api/sie/`, `/api/scope/`, `/api/processes/`
- Existen aliases de compatibilidad en backend:
  - `/api/stakeholders/` -> SIE
  - `/api/change-logs/` -> SIE
  - `/api/scopes/` -> ASB
  - `/api/maps/` -> SPM

## Matriz por modulo

### 1) Auth y sesion
- Rutas UI: `/login`, ruta protegida global con `ProtectedRoute` en `frontend/src/App.jsx`.
- Servicio frontend: `frontend/src/services/authService.js`.
- Backend: `/api/auth/*` en `backend/authentication/urls.py`.
- Estado tenant: fuerte en capa token (JWT incluye `organization_id`), cambio de organizacion via `/auth/switch-organization/`.

### 2) Dashboard core
- Rutas UI: `/`.
- Servicio frontend: `frontend/src/services/contextService.js` (`/dashboard/`).
- Backend: `dashboard_summary` en `backend/core/views.py` expuesto por `backend/core/urls.py`.
- Estado tenant: estricto (requiere auth y valida org con `_resolve_scoped_org_id`).

### 3) Contexto (SCA)
- Rutas UI: `/context`.
- Servicio frontend: `frontend/src/services/contextService.js` (`/sca/latest`, `/sca/analyze`, `/sca/history`).
- Backend: `backend/ai_modules/sca/urls.py` + `backend/ai_modules/sca/views.py`.
- Estado tenant: fuerte. Endpoints con `IsAuthenticated` y resolucion de organizacion activa para filtrar historial/ultimo analisis y ejecucion.

### 4) Stakeholders (SIE)
- Rutas UI: `/stakeholders`.
- Servicio frontend: `frontend/src/services/stakeholderService.js` (`/sie/stakeholders/*` y aliases `/stakeholders/*`, `/change-logs/*`).
- Backend: `backend/ai_modules/sie/urls.py`, `backend/ai_modules/sie/views.py`.
- Estado tenant: fuerte. `IsAuthenticated` activo, `organization_id` estandar en `StakeholderProfile`, filtrado por organizacion activa en todos los viewsets y escritura forzada de `organization_id` en create/update.

### 5) Alcance (ASB)
- Rutas UI: `/scope`.
- Servicio frontend: `frontend/src/services/scopeService.js` (`/scope/scopes/*`, `/scope/generate`, `/scope/statement`, `/scope/audit`).
- Backend: `backend/ai_modules/asb/urls.py`, `backend/ai_modules/asb/views.py`.
- Estado tenant: fuerte. ViewSets con `OrganizationScopedViewSetMixin`, modelo con `organization_id`, y FBVs con `_resolve_scoped_org_id()` y validaciones 400/403 por consistencia de token/organizacion.

### 6) Procesos (SPM)
- Rutas UI: `/processes`.
- Servicio frontend: `frontend/src/services/processService.js` (`/processes/maps/*`, `/processes/analyze`, `/processes/interactions`).
- Backend: `backend/ai_modules/spm/urls.py`, `backend/ai_modules/spm/views.py`.
- Estado tenant: fuerte. ViewSets con `OrganizationScopedViewSetMixin`, modelo con `organization_id`, y enforcement de organizacion activa en endpoints de analisis e interacciones.

### 7) Documentos (core)
- Rutas UI: `/documents`.
- Servicio frontend: `frontend/src/services/documentService.js`.
- Backend: `DocumentViewSet` en `backend/core/views.py` (router `backend/core/urls.py`).
- Estado tenant: fuerte. Usa `OrganizationScopedViewSetMixin`.
- Nota de compatibilidad: alineado en esta iteracion a `POST /documents/`.

### 8) Riesgos (core)
- Rutas UI: `/risks`.
- Servicio frontend: `frontend/src/services/riskService.js` (`/risks/*`, `/risks/matrix/`, `/risks/stats/`).
- Backend: `RiskMatrixViewSet` + `risk_stats` + `risk_matrix_list` en `backend/core/views.py`.
- Estado tenant: fuerte (mixin + funciones legacy reforzadas con `_resolve_scoped_org_id`).

### 9) Objetivos (core)
- Rutas UI: `/objectives`.
- Servicio frontend: `frontend/src/services/objectiveService.js`.
- Backend: `QualityObjectiveViewSet` en `backend/core/views.py`.
- Estado tenant: fuerte (mixin).

### 10) Liderazgo
- Rutas UI: `/leadership` y subrutas (`policies`, `roles`, `role-assignments`, `raci`, `commitments`, `customer-focus`).
- Servicio frontend: `frontend/src/features/leadership/api/leadershipApi.js`.
- Backend: `backend/leadership/urls.py`, `backend/leadership/views.py`.
- Estado tenant: medio-fuerte. Usa `OrganizationQuerysetMixin` propio con `request.organization_id` y validaciones en `perform_create`.

### 11) Planificacion
- Rutas UI: `/planning` y subrutas (`risks-opportunities`, `objectives`, `actions`, `changes`).
- Servicio frontend: `frontend/src/features/planning/api/planningApi.js`.
- Backend: `backend/planning/urls.py`, `backend/planning/views.py`.
- Estado tenant: fuerte. ViewSets migrados a `OrganizationScopedViewSetMixin` y acciones custom basadas en `self.get_queryset()`.

### 12) Recursos
- Rutas UI: `/resources` y subrutas (`resources`, `infrastructure`, `work-environment`, `competences`, `trainings`, `awareness`, `communications`).
- Servicio frontend: `frontend/src/features/resources/api/resourcesApi.js`.
- Backend: `backend/resources/urls.py`, `backend/resources/views.py`.
- Estado tenant: fuerte. ViewSets migrados a `OrganizationScopedViewSetMixin` y acciones custom basadas en `self.get_queryset()`.

### 13) Operaciones
- Rutas UI: `/operations` y subrutas (`requirements`, `design-projects`, `providers`, `nonconformities`, `releases`, `production`).
- Servicio frontend: `frontend/src/features/operations/api/operationsApi.js`.
- Backend: `backend/operations/urls.py`, `backend/operations/views.py`.
- Estado tenant: fuerte. ViewSets con `OrganizationScopedViewSetMixin`.

### 14) Desempeno
- Rutas UI: `/performance` y subrutas (`indicators`, `measurements`, `analyses`, `audits`, `findings`, `reviews`).
- Servicio frontend: `frontend/src/features/performance/api/performanceApi.js` (y legado parcial en `frontend/src/services/performanceService.js`).
- Backend: `backend/performance/urls.py`, `backend/performance/views.py`.
- Estado tenant: fuerte. ViewSets con `OrganizationScopedViewSetMixin`.

### 15) Mejora
- Rutas UI: `/improvement` y subrutas (`nonconformities`, `corrective-actions`, `continual`).
- Servicio frontend: `frontend/src/features/improvement/api/improvementApi.js`.
- Backend: `backend/improvement/urls.py`, `backend/improvement/views.py`.
- Estado tenant: fuerte. ViewSets con `OrganizationScopedViewSetMixin`.

### 16) Settings y administracion
- Rutas UI: `/settings` (protegida por roles).
- Servicio frontend: `frontend/src/services/settingsService.js`.
- Backend: `OrganizationViewSet`, `UserManagementViewSet`, `SettingsViewSet`, `BillingViewSet`, `ISOClauseConfigViewSet`, `AuditLogViewSet`, `export_data` en `backend/core/views.py`.
- Estado tenant: medio-fuerte. Endpoints sensibles usan resolucion de organizacion activa, validaciones de permisos/roles y filtrado por organizaciones permitidas; persisten acciones legacy fuera del mixin estandar, aunque con enforcement aplicado.

## Hallazgos transversales (priorizados)
1. Alto (resuelto 2026-03-11): `asb/spm` migrados a `organization_id` estandar + `OrganizationScopedViewSetMixin` + migraciones con backfill (commit d6324df).
2. Medio (resuelto): `planning` y `resources` migrados a `OrganizationScopedViewSetMixin`.
3. Medio (resuelto): upload de documentos alineado a `POST /documents/`.
4. Medio (resuelto): navegacion lateral incluye acceso a `/operations`.
5. Bajo (resuelto 2026-03-11): `settingsService` alineado a endpoints reales; historial de backups implementado con `GET /settings/backups/` y persistencia en `AuditLog`.
6. Operativo (sin brecha critica abierta): onboarding dashboard devuelve payload vacio con `200` cuando no hay snapshot, evitando ruido 404 en primer uso.

## Criterio de cierre del hito 1
- Completado el inventario de modulos y conexiones UI/API/backend.
- Reevaluados estados tenant tras remediaciones B1-B7 y actualizada la matriz a estado real 2026-03-12.
- Sin brechas criticas abiertas en scoping multitenant ni contratos frontend/backend prioritarios.
