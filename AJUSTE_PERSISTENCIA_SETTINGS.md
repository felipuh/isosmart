# Ajustes del Sistema - Persistencia de Cambios en Settings

## ✅ Problema Identificado

Los cambios realizados en el onboarding y settings **no se reflejaban** al intentar modificarlos posteriormente. Causas:

1. **Faltaba campo `preferred_language`** en modelo `OrganizationSettings`
2. **No había endpoints para actualizar** estándares e idioma después del onboarding
3. **Frontend no llamaba** a métodos de persistencia   
4. **Cambios de idioma no se sincronizaban** entre OrganizationSettings y UserProfile

---

## 🔧 Cambios Realizados

### Backend

#### 1. Agregado Campo `preferred_language` en modelo
**Archivo:** `backend/core/models.py`
```python
# Nuevo campo en OrganizationSettings
preferred_language = models.CharField(
    max_length=20, 
    default='es-LATAM', 
    choices=[
        ('es-LATAM', 'Español (LATAM)'),
        ('en', 'English'),
        ('pt', 'Português'),
    ]
)
```

**Migración:** `core/migrations/0007_add_preferred_language_to_settings.py` ✅ Aplicada

#### 2. Nuevos Endpoints de Actualización
**Archivo:** `backend/core/views.py` → `SettingsViewSet`

```python
# POST /api/settings/update_standards/
# Actualizar estándares ISO habilitados
{
  "organization_id": 1,
  "enabled_standards": ["ISO9001_2015", "ISO42001_2023"]
}
```

```python
# POST /api/settings/update_language/
# Actualizar idioma preferido
{
  "organization_id": 1,
  "preferred_language": "es-LATAM"
}
```

#### 3. Mejorado `complete_onboarding`
**Archivo:** `backend/core/views.py`

Antes: Solo guardaba estándares, ignoraba idioma
```python
# ❌ ANTES
settings.enabled_standards = enabled_standards
```

Ahora: Guarda estándares, idioma Y sincroniza con UserProfile
```python
# ✅ DESPUÉS
settings.enabled_standards = enabled_standards
settings.preferred_language = preferred_language
# Sincronizar también en UserProfile
user_profile.language = language_map.get(preferred_language, 'es')
user_profile.save()
```

### Frontend

#### 1. Nuevos Métodos en `settingsService`
**Archivo:** `frontend/src/services/settingsService.js`

```javascript
updateStandards: async (organizationId, standards) => {
  // POST /api/settings/update_standards/
}

updateLanguage: async (organizationId, language) => {
  // POST /api/settings/update_language/
}
```

#### 2. Actualizado `ISOClausesSettings.jsx`
**Cambio:** Al inicializar cláusulas, ahora también guarda los estándares
```javascript
// Antes: Solo inicializa cláusulas
// Ahora:
await settingsService.initializeStandards(organizationId, [selectedStandard]);
await settingsService.updateStandards(organizationId, [selectedStandard]); // ← NUEVO
```

#### 3. Agregada Sección de Idioma en `ThemeSettings.jsx`
**Archivo:** `frontend/src/components/Settings/ThemeSettings.jsx`

**Nueva funcionalidad:**
- Selector de 3 idiomas (Español, English, Português)
- Botón para cada idioma con indicador visual
- Guarda automáticamente en backend y actualiza UI
- Mensajes de éxito/error

```jsx
onClick={async () => {
  await settingsService.updateLanguage(currentOrganization?.id, lang.code);
  setLanguage(lang.code);  // Actualiza UI inmediatamente
}}
```

---

## 📊 Flujo de Persistencia Actualizado

### Onboarding
```
Usuario completa wizard
    ↓
POST /api/settings/complete_onboarding/
    ├── Guarda enabled_standards
    ├── Guarda preferred_language  ← NUEVO
    ├── Sincroniza UserProfile.language  ← NUEVO
    └── Marca onboarding_completed = true
```

### Settings - Cambiar Estándares
```
Usuario abre Settings → Parámetros ISO
Selecciona estándar e inicializa cláusulas
    ↓
POST /api/iso-clauses/initialize_standards/  (carga cláusulas)
    ↓
POST /api/settings/update_standards/  (guarda en BD)  ← NUEVO
    ↓
ISOClausesSettings.jsx se actualiza
```

### Settings - Cambiar Idioma
```
Usuario abre Settings → Apariencia
Hace clic en un idioma
    ↓
POST /api/settings/update_language/  ← NUEVO
    ├── Actualiza OrganizationSettings.preferred_language
    ├── Actualiza UserProfile.language
    └── Responde con confirmación
    ↓
useI18n(setLanguage) → UI se reactualiza instantáneamente
```

---

## ✅ Validación

### Endpoints Verificados
```bash
# 1. Login (sigue funcionando)
curl -X POST http://127.0.0.1:8001/api/auth/login/ \
  -d '{"email":"admin@isosmart.local","password":"Admin@123456"}'
# Status: 200 OK ✅

# 2. Complete Onboarding (ahora guarda idioma)
curl -X POST http://127.0.0.1:8001/api/settings/complete_onboarding/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{"organization_id":1,"enabled_standards":["ISO9001_2015","ISO42001_2023"],"preferred_language":"es-LATAM"}'
# Status: 200 OK ✅

# 3. Update Standards (NUEVO)
curl -X POST http://127.0.0.1:8001/api/settings/update_standards/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{"organization_id":1,"enabled_standards":["ISO9001_2015","ISO27001_2022"]}'
# Status: 200 OK ✅

# 4. Update Language (NUEVO)
curl -X POST http://127.0.0.1:8001/api/settings/update_language/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{"organization_id":1,"preferred_language":"en"}'
# Status: 200 OK ✅
```

### Migraciones
```bash
cd backend
./venv_ai/bin/python manage.py migrate
# Applying core.0007_add_preferred_language_to_settings... OK ✅
```

### Sintaxis
```bash
./venv_ai/bin/python -m py_compile core/views.py core/models.py
# ✅ Sin errores
```

---

## 🎯 Comportamiento Esperado Ahora

### Escenario 1: Completar Onboarding
1. Usuario selecciona idioma (Español) + estándares (9001, 42001)
2. Se presiona "Finalizar"
3. **Resultado:** 
   - ✅ Estándares guardados en `organization_settings.enabled_standards`
   - ✅ Idioma guardado en `organization_settings.preferred_language`
   - ✅ Idioma sincronizado en `user_profile.language`
   - ✅ Interfaz cambia inmediatamente al idioma seleccionado

### Escenario 2: Cambiar Idioma en Settings
1. Usuario accede a Settings → Apariencia
2. Selecciona un idioma diferente (English)
3. **Resultado:**
   - ✅ Se envía POST a `/api/settings/update_language/`
   - ✅ Se actualiza en BD (organization_settings + user_profile)
   - ✅ Interfaz cambia inmediatamente
   - ✅ Se muestra mensaje de confirmación "Idioma cambiado a English"

### Escenario 3: Cambiar Estándares en Settings
1. Usuario accede a Settings → Parámetros ISO
2. Cambia el selector a ISO 42001:2023
3. Hace clic en "Inicializar Cláusulas"
4. **Resultado:**
   - ✅ Se cargan las cláusulas de ISO 42001
   - ✅ Se guarda en BD (PostPOST a `/api/settings/update_standards/`
   - ✅ Cambio persiste al recargar la página

---

## 📝 Notas Técnicas

1. **Sincronización de Idioma:** Se guarda en dos lugares para compatibilidad
   - `OrganizationSettings.preferred_language` (nivel org)
   - `UserProfile.language` (nivel usuario)

2. **Validación de Estándares:** Se asegura que ISO 9001 siempre esté incluido
   ```python
   if 'ISO9001_2015' not in enabled_standards:
       enabled_standards = ['ISO9001_2015'] + list(enabled_standards)
   ```

3. **Manejo de Errores:** Ambos endpoints retornan status 400 si falta algo requerido

4. **Cambios Persistentes:** Usa `update_fields` cuando es posible para evitar queries innecesarios

---

**Status:** ✅ COMPLETADO - Sistema de persistencia fully functional

Fecha: 24 de febrero de 2026
