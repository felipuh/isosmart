# Plan Integral: Sistema Multilenguaje 100% 

**Objetivo:** Hacer que TODO el sistema (backend + frontend) sea multilenguaje en 3 idiomas: Español, English, Português

**Estado Actual:** 
- ✅ I18n Context en React existe pero con traduciones limitadas (solo onboarding)
- ✅ Endpoints nuevos para cambiar idioma funcionan
- ❌ 90% de los textos del sistema aún están hardcodeados en español
- ❌ Mensajes de error del backend no tienen i18n
- ❌ Componentes frontend NO usan useI18n

---

## PARTE 1: AUDITORÍA COMPLETA DE STRINGS HARDCODEADOS

### Frontend - Componentes que necesitan i18n

Basado en búsqueda semántica de "hardcoded text messages":

#### Dashboard & Navegación
- [ ] `Dashboard.jsx` - Títulos de módulos (Smart Context Analyzer, Smart Stakeholder Mapper, etc.)
- [ ] `Header.jsx` - Labels (Notificaciones, Configuración, etc.)
- [ ] `Layout.jsx` - Menú sidebar completo
- [ ] `ProtectedRoute.jsx` - Mensajes de carga y acceso denegado

#### Settings
- [ ] `ThemeSettings.jsx` - Descripciones de temas visuales
- [ ] `ISOClausesSettings.jsx` - Títulos de cláusulas
- [ ] `BackupExportSettings.jsx` - "Exportar Datos", "Descargar"
- [ ] Todos los Settings subcomponentes

#### Módulos de Negocio (Leadership, Resources, Improvement, Planning, Performance)
- [ ] `PoliciesPage.jsx` - "Políticas de Calidad", "Nueva política"
- [ ] `RolesPage.jsx` - Labels (Nivel, Reporta a, etc.)
- [ ] `CommitmentsPage.jsx` - Types, statuses, labels
- [ ] `ChangeControlPage.jsx` - Change types, reasons
- [ ] `InfrastructurePage.jsx` - Form labels  
- [ ] `RiskForm.jsx` - Probability/Impact options (Muy Baja, Baja, Media, Alta, etc.)
- [ ] `ImprovementContinualPage.jsx` - Statuses, action types
- [ ] `ImprovementCorrectiveActionsPage.jsx` - Labels
- [ ] `ImprovementDashboard.jsx` - Card titles
- [ ] `ResourcesDashboard.jsx` - Card descriptions

#### Otros Componentes
- [ ] `DocumentDashboard.jsx` - Document types (Actas, Reportes, Políticas, Procedimientos)
- [ ] `RiskMatrixVisual.jsx` - "Leyenda de Niveles de Riesgo"
- [ ] `Recommendations.jsx` - Priority labels

#### Cross-Cutting
- [ ] Botones comunes: "Guardar", "Cancelar", "Agregar", "Editar", "Eliminar", "Crear", "Actualizar", "Limpiar"
- [ ] Estados: "Guardando...", "Cargando...", "En progreso"
- [ ] Mensajes de error genéricos

### Backend - Mensajes que necesitan i18n

#### core/views.py y serializers.py
- [ ] `complete_onboarding()` - Mensajes de respuesta
- [ ] `update_standards()` - Mensajes de validación y éxito
- [ ] `update_language()` - Mensajes de respuesta
- [ ] Mensajes de error de validación (400)

#### authentication/views.py
- [ ] Login error messages
- [ ] Permission denied messages
- [ ] Token validation errors

#### integration/client.py  
- [ ] Mensajes de fallback cuando Admin Apps falla
- [ ] Warning logs

#### Otros módulos
- [ ] Error messages genéricos
- [ ] Validación messages
- [ ] Business logic messages

---

## PARTE 2: ESTRATEGIA DE IMPLEMENTACIÓN

### Fase 1: Crear Diccionario I18n Completo (2h)

Expandir `frontend/src/context/I18nContext.jsx` con estructura jerárquica:

```javascript
MESSAGES = {
  'es-LATAM': {
    header: {...},
    navigation: {...},
    dashboard: {...},
    modules: {
      leadership: {...},
      resources: {...},
      improvement: {...},
      planning: {...},
      performance: {...},
    },
    settings: {...},
    common: {
      buttons: {
        save: 'Guardar',
        cancel: 'Cancelar',
        ...
      },
      messages: {
        saving: 'Guardando...',
        loading: 'Cargando...',
        ...
      },
      errors: {...},
    },
  },
  en: {...},
  pt: {...},
}
```

### Fase 2: Migrar Componentes Frontend (3h)

Patrón para cada componente:
```javascript
import { useI18n } from '../context/I18nContext';

const Component = () => {
  const { t } = useI18n();
  
  return (
    <>
      <h1>{t('modules.leadership.title')}</h1>
      <button>{t('common.buttons.save')}</button>
    </>
  );
}
```

**Componentes por prioridad:**
1. **Alta** (críticos): Dashboard, Header, Layout, Login, Onboarding
2. **Media** (frecuentemente usados): Settings, Leadership, Resources, Improvement
3. **Baja** (menos frecuentes): Performance, Planning

### Fase 3: Backend i18n (2h)

Crear sistema de mensajes traducibles en Django:

**Opción A: Usar package `django-rosetta` o similar**
```python
from django.utils.translation import gettext_lazy as _

# En views.py
response = {'message': _('onboarding_complete')}
```

**Opción B: Usar diccionario persistente en BD:**
```python
MESSAGES = {
  'es-LATAM': {
    'onboarding_complete': 'Onboarding completado correctamente',
    'standards_updated': 'Estándares actualizados correctamente',
    ...
  },
  'en': {...},
  'pt': {...},
}
```

**Opción C: Usar traducción dinámica desde frontend**
- Backend retorna mensajes en KEY-form
- Frontend resuelve usando useI18n

**Recomendación:** Opción C (más control, menos setup)

```python
# Backend
def update_language():
  return {
    'message_key': 'settings.language_updated',
    'new_language': 'en',
  }

# Frontend
const response = await updateLanguage(orgId, 'en');
const message = t(response.message_key);
```

### Fase 4: Validación y Testing (1h)

- Verificar que cambios de idioma persisten
- Que API retorna message_keys
- Que todos los componentes usan useI18n
- Testing de 3 idiomas en flujos críticos

---

## PARTE 3: STRUCTURE COMPLETA DE TRADUCCIÓN

### Archivo: `frontend/src/context/I18nContext.jsx`

Necesita expanderse de ~117 líneas actuales a ~2000 líneas con:

```
MESSAGES = {
  'es-LATAM': {
    // Navigation & Layout (50 strings)
    navigation: {
      modules: {},
      settings: {},
      menu: {},
    },
    // Dashboard (40 strings)
    dashboard: {
      greeting: 'Bienvenido',
      lastAccess: 'Último acceso',
      moduleDescriptions: {},
      quickActions: {},
    },
    // Settings (80 strings)
    settings: {
      theme: {},
      iso: {},
      backup: {},
      users: {},
    },
    // Leadership Module (120 strings)
    modules: {
      leadership: {
        policies: {}, 
        roles: {},
        raci: {},
        commitments: {},
      },
      resources: {...},
      improvement: {...},
      planning: {...},
      performance: {...},
    },
    // Common UI (100 strings)
    common: {
      buttons: {},
      forms: {},
      messages: {},
      errors: {},
      placeholders: {},
      labels: {},
    },
  },
  'en': {...},
  'pt': {...},
}
```

Total estimado: **~3000 strings** a traducir

---

## PARTE 4: TIMELINE Y PRIORIZACIÓN

### Semana 1: Fundación (8h)
- [x] Verificar endpoints de i18n funcionan (✅ DONE)
- [ ] Expandir diccionario MESSAGES (2h)
- [ ] Migrar componentes críticos: Dashboard, Header, Layout, Login (3h)
- [ ] Validar que funciona (1h)
- [ ] Documentar patrones (1h)

### Semana 2: Bulk Migration (12h)
- [ ] Migrar todos los módulos de negocio (8h)
- [ ] Migrar Settings (2h)
- [ ] Migrar componentes menores (2h)

### Semana 3: Backend + Validación (8h)
- [ ] Sistema de i18n en respuestas backend (3h)
- [ ] Testing de todos los flujos (3h)
- [ ] Documentación de uso (2h)

**Total: 28 horas de desarrollo**

---

## CHECKLIST DE IMPLEMENTACIÓN

### Step 1: Diccionario Completo
- [ ] Crear MESSAGES con 3000+ strings
- [ ] Validar que no hay keys duplicadas
- [ ] Agregar comentarios con contexto

### Step 2: Componentes Core
- [ ] Dashboard → useI18n
- [ ] Header → useI18n
- [ ] Layout/Navigation → useI18n
- [ ] Login → useI18n
- [ ] Onboarding → useI18n (mejorar existente)
- [ ] Settings → useI18n

### Step 3: Módulos
- [ ] Leadership (Policies, Roles, RACI, Commitments)
- [ ] Resources (Infrastructure, Trainings, Competencies)
- [ ] Improvement (Nonconformities, Corrective Actions, Continual)
- [ ] Planning (Change Control, Product Planning)
- [ ] Performance (KPIs, Measurements)
- [ ] Core (Context, Scope, Processes, Documents, Risks, Objectives)

### Step 4: Backend
- [ ] Crear helper para mensajes traducibles
- [ ] Actualizar error responses con message_keys
- [ ] Actualizar success responses con message_keys
- [ ] Documentar en API spec

### Step 5: QA
- [ ] Cambiar a cada idioma y navegar todos los módulos
- [ ] Verificar que se guardan preferencias
- [ ] Verificar que errores muestran en idioma correcto
- [ ] Testing de flujos en 3 idiomas

---

## NOTAS TÉCNICAS

### Naming Convention para Keys
```
modules.{module_name}.{component}.{field}
common.buttons.save
common.errors.required_field
settings.{feature}.{section}
```

### Fallback Strategy
```javascript
const t = (key, fallback = key) => {
  // Path lookup
  const value = getValue(MESSAGES[language], key);
  if (value) return value;
  
  // Try default language
  const defaultValue = getValue(MESSAGES[DEFAULT_LANGUAGE], key);
  return defaultValue || fallback;
}
```

### Testing Traducción
```javascript
// En pruebas
const { t } = useI18n('en');
const text = t('dashboard.title');
expect(text).toBe('Dashboard');
```

---

## PRÓXIMOS PASOS INMEDIATOS

1. ✅ Validar estado actual (endpoints, frontend hot reload)
2. ⏳ **Expandir MESSAGES en I18nContext (Tarea Prioritaria)**
3. ⏳ Migrar 5 componentes core  
4. ⏳ Crear backend message_key system
5. ⏳ Testing end-to-end en 3 idiomas

**¿Empezamos por la expansión del diccionario?**

