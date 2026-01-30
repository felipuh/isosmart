# Ajustes de API - ISO Smart
## 29 de Enero de 2026

### Resumen
Se han aplicado ajustes en la arquitectura de API del frontend para sincronizarse correctamente con los endpoints del backend. Los cambios incluyen:

1. **Corrección de rutas de endpoints** - Usar prefijos correctos de módulos (`/spm/`, `/asb/`, `/sca/`, `/sie/`)
2. **Extracción de arrays paginados** - Manejar respuestas paginadas de DRF correctamente
3. **Creación de aliases de endpoints** - Para compatibilidad del frontend

---

## Cambios Realizados

### 1. Backend (`/backend/backend/urls.py`)
**Agregados aliases para endpoints del frontend:**

```python
# Explicit aliases for frontend endpoints without duplicated prefixes
path('api/stakeholders/critical/', sie_views.StakeholderProfileViewSet.as_view({'get': 'critical'}), name='stakeholders-critical'),
path('api/stakeholders/matrix/', sie_views.StakeholderProfileViewSet.as_view({'get': 'matrix'}), name='stakeholders-matrix'),
path('api/change-logs/recent/', sie_views.StakeholderChangeLogViewSet.as_view({'get': 'recent'}), name='change-logs-recent'),
```

**Razón:** Los endpoints `/api/stakeholders/` y `/api/change-logs/` son aliases para `/api/sie/` que activan los routers del mismo módulo. Los acciones custom (`critical`, `matrix`, `recent`) no estaban disponibles directamente desde los alias.

---

### 2. Frontend Services

#### **stakeholderService.js**
- `getAll()`: `/stakeholders/` → `/sie/stakeholders/` + extrae `results`
- `getCritical()`: `/stakeholders/critical/` → `/stakeholders/critical/` (funciona con alias)
- `getMatrix()`: `/stakeholders/matrix/` → `/stakeholders/matrix/` (funciona con alias)
- `getRecentChanges()`: `/change-logs/recent/` → `/change-logs/recent/` (funciona con alias)

#### **processService.js (SPM - Sistema de Mapeo de Procesos)**
- Todos los endpoints ahora usan `/spm/` en lugar de raíz
- Ejemplos:
  - `/maps/` → `/spm/maps/`
  - `/processes/` → `/spm/processes/`
  - `/interactions/` → `/spm/interactions/`
  - `/activities/` → `/spm/activities/`
- Endpoints paginados extraen `results` array

#### **scopeService.js (ASB - Definición del Alcance)**
- Todos los endpoints ahora usan `/asb/` en lugar de raíz
- Ejemplos:
  - `/scopes/` → `/asb/scopes/`
  - `/processes/` → `/asb/processes/`
  - `/locations/` → `/asb/locations/`
- Endpoints paginados extraen `results` array

#### **contextService.js (SCA - Análisis del Contexto)**
- Endpoints ahora usan `/sca/` en lugar de `/context/`
- `/context/latest/` → `/sca/latest/`
- `/context/analyze/` → `/sca/analyze/`
- `getRiskMatrix()`: extrae `results` array

#### **objectiveService.js, documentService.js, riskService.js**
- Agregada extracción de `results` array para manejar respuestas paginadas de DRF
- Patrón: `response.data.results || response.data`

---

## Estructura de Endpoints

### Core (sin cambios)
```
/api/
  ├── documents/          → core.urls (DocumentViewSet)
  ├── risks/              → core.urls (RiskMatrixViewSet)
  ├── objectives/         → core.urls (QualityObjectiveViewSet)
  ├── organizations/      → core.urls (OrganizationViewSet)
  ├── users/              → core.urls (UserManagementViewSet)
  ├── settings/           → core.urls (SettingsViewSet)
  ├── iso-clauses/        → core.urls (ISOClauseConfigViewSet)
  └── audit-logs/         → core.urls (AuditLogViewSet)
```

### AI Modules (con prefijos)
```
/api/
  ├── sie/                → SIE (Stakeholder Intelligence Engine)
  │   ├── stakeholders/
  │   ├── change-logs/
  │   ├── relationships/
  │   └── engagement-plans/
  │
  ├── spm/                → SPM (System Process Mapping)
  │   ├── maps/
  │   ├── processes/
  │   ├── interactions/
  │   └── activities/
  │
  ├── asb/                → ASB (Activity Scope Boundaries)
  │   ├── scopes/
  │   ├── processes/
  │   └── locations/
  │
  └── sca/                → SCA (Strategic Context Analysis)
      └── (endpoints variados)

```

### Aliases (para compatibilidad)
```
/api/
  ├── stakeholders/       → sie.urls (alias)
  ├── change-logs/        → sie.urls (alias)
  ├── scopes/             → asb.urls (alias)
  ├── context/            → sca.urls (alias)
  └── maps/               → spm.urls (alias)
```

---

## Patrón de Paginación

**Respuesta paginada de DRF:**
```json
{
  "count": 10,
  "next": "...",
  "previous": null,
  "results": [...]
}
```

**En servicios:**
```javascript
// Extrae automáticamente el array si es paginated, sino retorna tal cual
return response.data.results || response.data;
```

---

## Verificación

✅ Endpoints probados:
- `http://127.0.0.1:8001/api/stakeholders/critical/` → 200
- `http://127.0.0.1:8001/api/stakeholders/matrix/` → 200
- `http://127.0.0.1:8001/api/change-logs/recent/` → 200

---

## Próximos Pasos (si es necesario)

1. **Verificar en producción**: Si está usando gunicorn/supervisor, reiniciar servicios
2. **Logs**: Revisar `logs/ai/runserver.log` para cualquier error
3. **Frontend**: Limpiar cache del navegador (Ctrl+Shift+R)

---

