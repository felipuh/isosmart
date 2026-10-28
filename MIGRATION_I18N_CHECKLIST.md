# Lista de Migración a i18n - Sistema Multilenguaje

## Estado: Sistema Multilenguaje 30% Completado

✅ **Completado:**
- Diccionario MESSAGES expandido de 117 a 2000+ líneas
- 3 idiomas completos: Español, English, Português
- Onboarding ya usa useI18n
- ThemeSettings.jsx actualizado con selector de idioma
- I18nContext funcional en todos los idiomas

⏳ **Pendiente:**
- Migración de ~40+ componentes a useI18n
- Backend message localization

---

## PRIORIDAD 1: CRITICOS (Usar hoy)

Estos componentes se ven en TODOS los flujos. **Deben migrarse primero.**

### 1. Layout Components

#### [src/components/Layout/Header.jsx](src/components/Layout/Header.jsx)
- **Strings hardcodeados:** "ISO Smart" (app title), "Notificaciones", "Configuración", "Cerrar sesión"
- **Cambio:** Importar useI18n, reemplazar strings con `t('header...')`

```jsx
// ANTES:
<h1 className="text-xl font-bold">ISO Smart</h1>
<p className="text-xs">Notificaciones</p>
<p className="text-xs">Configuración</p>

// DESPUÉS:
const { t } = useI18n();
<h1 className="text-xl font-bold">{t('header.appTitle')}</h1>
<p className="text-xs">{t('header.notifications')}</p>
<p className="text-xs">{t('header.settings')}</p>
```

#### [src/components/Layout/Layout.jsx](src/components/Layout/Layout.jsx)
- **Strings:** Menu labels (Dashboard, Contexto, Stakeholders, etc.)
- **Cambio:** Usar `t('navigation.dashboard')`, `t('navigation.context')`, etc.

#### [src/components/Auth/ProtectedRoute.jsx](src/components/Auth/ProtectedRoute.jsx)
- **Strings:** "Verificando autenticación...", "Acceso denegado"
- **Cambio:** useI18n para mensajes de carga y error

### 2. Dashboard

#### [src/components/Dashboard/Dashboard.jsx](src/components/Dashboard/Dashboard.jsx)
- **Strings críticos:** 
  - "Bienvenido"
  - "Smart Context Analyzer", "Smart Stakeholder Mapper", etc. (7 módulos)
  - "Analizar Contexto", "Gestionar Stakeholders", etc. (quick actions)
  - "Procesos", "Documentos", "Riesgos" (stats)
- **Cambio:** Usar `t('dashboard.greeting')`, `t('dashboard.modules.sca')`, etc.

### 3. Settings

#### [src/components/Settings/ThemeSettings.jsx](src/components/Settings/ThemeSettings.jsx) ✅ PARTIALLY DONE
- Falta: Traducir descripciones de temas visuales
- Tarea: Completar traducción

#### [src/components/Settings/ISOClausesSettings.jsx](src/components/Settings/ISOClausesSettings.jsx)
- **Strings:** "Parámetros ISO", "Selecciona un estándar", "Inicializar Cláusulas"
- **Cambio:** useI18n

#### [src/components/Settings/BackupExportSettings.jsx](src/components/Settings/BackupExportSettings.jsx)
- **Strings:** "Exportar Datos", "Descripción", "Respaldo", etc.

---

## PRIORIDAD 2: FRECUENTES (Usar regularmente)

### 4. Leadership Module

#### [src/features/leadership/pages/PoliciesPage.jsx](src/features/leadership/pages/PoliciesPage.jsx)
- **Strings:** "Políticas de Calidad", "Gestión y aprobación...", "Nueva política", "Guardar", "Aprobar", "Publicar", "Obsoleta", "Eliminar"
- **Lógica:** 50+ strings

#### [src/features/leadership/pages/RolesPage.jsx](src/features/leadership/pages/RolesPage.jsx)
- **Strings:** "Roles Organizacionales", form labels (Nivel, Reporta a, etc.)
- ~30+ strings

#### [src/features/leadership/pages/CommitmentsPage.jsx](src/features/leadership/pages/CommitmentsPage.jsx)
- **Strings:** "Compromisos de Liderazgo", commitment types, evidence types
- ~25+ strings

#### [src/features/leadership/pages/LeadershipDashboard.jsx](src/features/leadership/pages/LeadershipDashboard.jsx)
- **Strings:** "Liderazgo y Compromiso", stat card titles, descriptions
- ~20+ strings

### 5. Resources Module

#### [src/features/resources/pages/ResourcesDashboard.jsx](src/features/resources/pages/ResourcesDashboard.jsx)
- **Strings:** "Nuevo Recurso", "Nueva Capacitación", "Nueva Competencia", descriptions
- ~15+ strings

#### [src/features/resources/pages/InfrastructurePage.jsx](src/features/resources/pages/InfrastructurePage.jsx)
- Form labels: "Ubicación", "Descripción", buttons
- ~15+ strings

### 6. Improvement Module

#### [src/features/improvement/pages/ImprovementDashboard.jsx](src/features/improvement/pages/ImprovementDashboard.jsx)
- **Strings:** "Mejora", stat card titles
- ~10+ strings

#### [src/features/improvement/pages/ImprovementContinualPage.jsx](src/features/improvement/pages/ImprovementContinualPage.jsx)
- **Strings:** "Mejora Continua", status options (Propuesta, En evaluación, Aprobada, etc.)
- ~15+ strings

#### [src/features/improvement/pages/ImprovementCorrectiveActionsPage.jsx](src/features/improvement/pages/ImprovementCorrectiveActionsPage.jsx)
- **Strings:** action types, status labels
- ~15+ strings

### 7. Planning Module

#### [src/features/planning/pages/ChangeControlPage.jsx](src/features/planning/pages/ChangeControlPage.jsx)
- **Strings:** "Control de Cambios", change types, reasons, statuses
- ~20+ strings

### 8. Performance Module

#### [src/features/performance/pages/DashboardPage.jsx](src/features/performance/pages/DashboardPage.jsx)
- **Strings:** "Desempeño", stat titles
- ~10+ strings

---

## PRIORIDAD 3: MENORES (Less Frequent)

### 9. Context & Scope Components

#### [src/components/Context/ContextDashboard.jsx](src/components/Context/ContextDashboard.jsx)
- ~15+ strings

#### [src/components/Scope/ScopeDashboard.jsx](src/components/Scope/ScopeDashboard.jsx)
- ~10+ strings

#### [src/components/Context/Recommendations.jsx](src/components/Context/Recommendations.jsx)
- **Strings:** Priority labels (Alta, Media, Baja)
- ~5+ strings

### 10. Risk Components

#### [src/components/Risks/RiskForm.jsx](src/components/Risks/RiskForm.jsx)
- **Strings:** Probability/Impact options (Muy Baja, Baja, Media, Alta, Muy Alta)
- ~12+ strings

#### [src/components/Risks/RiskMatrixVisual.jsx](src/components/Risks/RiskMatrixVisual.jsx)
- ~10+ strings

#### [src/components/Risks/RiskDashboard.jsx](src/components/Risks/RiskDashboard.jsx)
- ~10+ strings

### 11. Other Components

- Process/Document/Objective Dashboards (~30 strings total)
- Reusable modals and forms
- Error boundaries and loading states
- LoginPage - "Email", "Contraseña", "Iniciar Sesión", "Olvidé mi contraseña"

---

## PATRÓN DE MIGRACIÓN

### Paso 1: Importar useI18n
```jsx
import { useI18n } from '../context/I18nContext';
```

### Paso 2: Usar en componente
```jsx
const MyComponent = () => {
  const { t } = useI18n();
  
  return (
    <div>
      <h1>{t('modules.leadership.title')}</h1>
      <button>{t('common.buttons.save')}</button>
    </div>
  );
};
```

### Paso 3: Nuevas keys si necesarias
Si algún string NO ESTÁ en MESSAGES, AGREGARLO:
```javascript
// En I18nContext.jsx MESSAGES
modules: {
  leadership: {
    customFeature: {
      'es-LATAM': 'Mi Característica Personalizada',
      'en': 'My Custom Feature',
      'pt': 'Meu Recurso Personalizado',
    }
  }
}
```

---

## TESTING DURANTE MIGRACION

**Cuando migres un componente:**
1. Cambiar idioma en Settings → Apariencia
2. Navegar al componente  
3. Verificar que TODOS los textos están traducidos
4. Cambiar a "English" y "Português"
5. Verificar que se traducen correctamente

**Ejemplo:**
- Ir a /leadership/policies
- Cambiar a English → Debe decir "Quality Policies" (no "Políticas de Calidad")
- Cambiar a Português → Debe decir "Políticas de Qualidade"

---

## PRIORIDAD DE IMPLEMENTACIÓN RECOMENDADA

**Día 1 (4h):**
- Header.jsx
- Layout.jsx  
- ProtectedRoute.jsx
- Dashboard.jsx
- Onboarding check + ThemeSettings completion

**Día 2 (4h):**
- PoliciesPage, RolesPage, CommitmentsPage (Leadership)
- ISOClaus esSettings.jsx
- LeadershipDashboard.jsx

**Día 3 (4h):**
- ResourcesDashboard + InfrastructurePage
- ImprovementDashboard + ImprovementContinualPage
- ChangeControlPage

**Día 4 (4h):**
- RiskForm, RiskMatrixVisual, RiskDashboard
- ContextDashboard, ScopeDashboard
- Otros menores

**Día 5 (2h):**
- Testing integración
- Backend msg localization

---

## CHECKLIST MIGRACIÓN GLOBAL

### Componentes Core
- [ ] Header.jsx
- [ ] Layout.jsx
- [ ] Dashboard.jsx
- [ ] ProtectedRoute.jsx
- [ ] LoginPage.jsx

### Settings
- [ ] ThemeSettings.jsx (completar)
- [ ] ISOClausesSettings.jsx
- [ ] BackupExportSettings.jsx

### Leadership
- [ ] PoliciesPage.jsx
- [ ] RolesPage.jsx
- [ ] CommitmentsPage.jsx
- [ ] LeadershipDashboard.jsx

### Resources
- [ ] ResourcesDashboard.jsx
- [ ] InfrastructurePage.jsx
- [ ] Otros (Trainings, Competencies, Awareness, Communications)

### Improvement
- [ ] ImprovementDashboard.jsx
- [ ] ImprovementContinualPage.jsx
- [ ] ImprovementCorrectiveActionsPage.jsx

### Planning & Performance
- [ ] ChangeControlPage.jsx
- [ ] PerformanceDashboard.jsx

### Other Modules
- [ ] Context, Scope, Processes, Documents
- [ ] Risks (Form, Matrix, Dashboard)
- [ ] Objectives & Stakeholders

---

## NOTAS

- **No necesitas** tocar cada archivo manualmente para agregar imports - son idénticos
- **Puedes** copiar/pegar el import: `import { useI18n } from '../../context/I18nContext';`
- **Ajusta** la ruta relativa según dónde esté el componente
- **Cuando tengas duda** sobre la key, busca en MESSAGES (I18nContext.jsx)

---

## PRÓXIMO PASO

1. **Empezar con Header.jsx** (es el más visible)
2. Luego **Layout.jsx y Dashboard.jsx** (usados en todas partes)
3. Luego **Settings components**
4. Finalmente **módulos de negocio**

**¿Empezamos?**

---
