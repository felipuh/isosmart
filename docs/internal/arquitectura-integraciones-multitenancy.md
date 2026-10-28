# Arquitectura, Integraciones y Multitenancy

Fecha: 24-02-2026

## 1) Objetivo

Documentar el estado actual del sistema tras la corrección de pendientes funcionales en:

- Dashboard principal ISO 9001 (cláusulas 4–10)
- Integración entre módulos 8.7, 9.2, 9.3 y 10.x
- Aislamiento multitenant por organización

---

## 2) Componentes clave

### Backend

- Mixin de escopado por organización:
  - `backend/core/organization_scoping.py`
- Servicios de sincronización cross-módulo:
  - `backend/improvement/services.py`
- ViewSets con multitenancy estricto:
  - `backend/improvement/views.py`
  - `backend/performance/views.py`
  - `backend/operations/views.py`

### Frontend

- Dashboard principal con progreso dinámico por cláusula:
  - `frontend/src/components/Dashboard/Dashboard.jsx`

---

## 3) Multitenancy (estado actual)

## 3.1 Regla general

Todos los endpoints de datos en módulos críticos deben resolverse por organización activa.

Mecanismo:

- Se obtiene `organization_id` desde:
  1. Query param `organization_id`
  2. Claim del JWT (`request.organization_id`)
- Si ambos existen y no coinciden, se rechaza con `403`.
- Si no hay organización resoluble, se rechaza con `400`.

## 3.2 Implementación

El mixin `OrganizationScopedViewSetMixin` aplica:

- `get_queryset()` filtrado por organización
- `perform_create()` validación de tenant y escritura de `organization_id`
- `perform_update()` bloquea cambios de tenant

## 3.3 Resultado esperado

- Sin `organization_id` (y sin claim válido): `400`
- Con `organization_id` de otra organización: `403`
- Con `organization_id` válido: `200`

---

## 4) Integraciones automáticas entre cláusulas

## 4.1 9.2 Hallazgos de auditoría → 10.2 No conformidades de mejora

Disparador:

- Crear o actualizar hallazgos (`AuditFindingViewSet`)

Servicio:

- `sync_finding_to_improvement_nc(finding)`

Comportamiento:

- Solo sincroniza tipos `nc_major` y `nc_minor`.
- Crea/actualiza NC de mejora con clave idempotente:
  - `nc_number = AUD-{finding_number}`
- Mapea severidad y estado de hallazgo a catálogo de Mejora.

## 4.2 9.3 Revisión por la dirección → 10.3 Mejora continua

Disparador:

- Crear o actualizar revisión (`ManagementReviewViewSet`)

Servicio:

- `sync_management_review_to_continual_improvement(review)`

Comportamiento:

- Si hay oportunidades/decisiones de mejora, crea/actualiza iniciativa.
- Clave idempotente:
  - `initiative_number = MR-{review_code}`
- Genera iniciativa de tipo `system` con datos de desempeño y decisiones.

## 4.3 8.7 No conformidades de operaciones → 10.2 Mejora

Disparadores:

- Crear o actualizar NC en `operations` (`NonconformityViewSet`)
- Sync manual puntual o masiva por endpoints

Servicio:

- `sync_operations_nc_to_improvement_nc(operations_nc)`

Comportamiento:

- Crea/actualiza NC en mejora con clave:
  - `nc_number = OPS-{operations_nc.nc_number}`
- Mapea severidad y estado del flujo operativo al flujo de Mejora.

---

## 5) Endpoints relevantes

## 5.1 Operaciones

- Sync puntual de una NC:
  - `POST /api/operations/nonconformities/{id}/sync_to_improvement/?organization_id={org}`
- Sync masiva de abiertas:
  - `POST /api/operations/nonconformities/sync_open_to_improvement/?organization_id={org}`

## 5.2 Performance

- Hallazgos (disparan sync 9.2→10.2):
  - `POST /api/performance/findings/?organization_id={org}`
  - `PUT /api/performance/findings/{id}/?organization_id={org}`
- Revisiones (disparan sync 9.3→10.3):
  - `POST /api/performance/reviews/?organization_id={org}`
  - `PUT /api/performance/reviews/{id}/?organization_id={org}`

## 5.3 Mejora

- NC de mejora:
  - `GET /api/improvement/nonconformities/?organization_id={org}`
- Iniciativas de mejora continua:
  - `GET /api/improvement/continual-improvements/?organization_id={org}`

---

## 6) Dashboard principal (frontend)

Archivo:

- `frontend/src/components/Dashboard/Dashboard.jsx`

Estado:

- Ya no usa progreso estático.
- Calcula progreso por cláusula (4–10) consultando endpoints por módulo.
- Muestra:
  - progreso individual por cláusula
  - promedio ISO 9001 global
  - conteos reales (procesos, stakeholders, etc.)

Criterio de progreso por cláusula:

- Cada cláusula se evalúa con 3 o 4 verificadores (endpoints).
- Si un verificador tiene datos `> 0`, cuenta como completado.
- Progreso = verificadores completados / verificadores totales.

---

## 7) Riesgos y límites conocidos

- La métrica de progreso por cláusula es **operativa** (existencia de datos), no auditoría formal de cumplimiento ISO.
- Si un endpoint cambia su contrato de respuesta (`count/results`), debe actualizarse la normalización del dashboard.
- Para módulos aún en fase inicial, el progreso puede verse bajo aunque el flujo funcional exista.

---

## 8) Checklist de QA recomendado

- Multitenancy:
  - `GET` sin `organization_id` en endpoints críticos → `400`
  - `GET` con organización ajena al token → `403`
- Integración 9.2→10.2:
  - Crear hallazgo `nc_major` y verificar NC `AUD-*` en Mejora
- Integración 9.3→10.3:
  - Crear revisión con decisiones de mejora y verificar iniciativa `MR-*`
- Integración 8.7→10.2:
  - Crear NC operativa y verificar NC `OPS-*` en Mejora
- Dashboard:
  - Verificar variación de % al crear/eliminar datos por módulo

---

## 9) Operación y mantenimiento

- Ante nuevos módulos, añadir su escopado con `OrganizationScopedViewSetMixin`.
- Toda nueva integración cross-módulo debe implementarse en servicios (no lógica en serializers).
- Mantener sincronizaciones idempotentes para evitar duplicidad.

---

## 10) Historial de cambio

- 24-02-2026:
  - Se implementa escopado multitenant estricto.
  - Se habilitan sincronizaciones automáticas 8.7/9.2/9.3 hacia 10.x.
  - Se actualiza dashboard principal a cálculo dinámico por cláusulas.

---

## 12) Documentación operativa complementaria

- Manual por rol y flujos E2E: `docs/internal/manual-operacion-por-roles.md`
