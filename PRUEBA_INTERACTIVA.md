# Guía de Prueba Interactiva - ISO Smart v2026

## Estado Actual del Ambiente

- **Frontend**: http://localhost:3001/ o http://isosmart.local:3001/
  - ⚠️ IMPORTANTE: Accede con **:`3001` (puerto incluido)**
- **Backend API**: http://127.0.0.1:8001/
- **Base de datos**: Limpia (1 org, 1 usuario)
- **Componentes nuevos**: Onboarding, Configuración Multi-Org, ISOes Multiestándar, Asistente IA

---

## Paso 1: Login (1 min)

**URL**: http://localhost:3001/login  
**O alternativa:** http://isosmart.local:3001/login  (⚠️ incluir puerto `:3001`)

### Credenciales por defecto:
- **Email**: `admin@isosmart.local`
- **Contraseña**: `Admin@123456`

**Qué validar:**
- ✅ Página de login carga correctamente
- ✅ Auth token se almacena en localStorage
- ✅ Se redirige a /onboarding (no al dashboard, porque onboarding aún no está completado)

---

## Paso 2: Onboarding (3 min)

**URL**: http://localhost:3001/onboarding  
**O alternativa:** http://isosmart.local:3001/onboarding  (⚠️ incluir puerto `:3001`)

**Qué hacer:**
1. Verás una pantalla con 3 secciones:
   - **Sección 1 (Bienvenido)**: Muestra "Organización Principal" (única org del sistema)
   - **Sección 2 (Idioma)**: Selector con Español, English, Português
   - **Sección 3 (Estándares ISO)**: Checkboxes para seleccionar estándares
     - ✅ ISO 9001:2015 (obligatorio, no se puede desmarcar)
     - ☐ ISO/IEC 42001:2023
     - ☐ ISO 27001:2022
     - ☐ ISO 14001:2015
     - ☐ ISO 45001:2018

2. **Prueba el selector de idioma:**
   - Haz clic en **"English"** → Toda la interfaz cambia a inglés
   - Haz clic en **"Português"** → Cambia a portugués
   - Haz clic en **"Español (LATAM)"** → Vuelve al español

3. **Selecciona** algunos estándares adicionales (ej: ISO 42001 + ISO 27001)

4. **Haz clic en** "Finalizar onboarding" (o en inglés: "Finish Onboarding")

**Qué validar:**
- ✅ Selector de idioma funciona (cambia textos EN TIEMPO REAL)
- ✅ Todos los textos se traducen (título, subtítulo, botones, etc.)
- ✅ Checkbox ISO 9001 está marcado y deshabilitado
- ✅ Mensaje actual al finalizar está en el idioma seleccionado
- ✅ El idioma se guarda (irá con ese idioma a Dashboard)
- ✅ Otros checkboxes se pueden seleccionar/desmarcar
- ✅ Botón "Finalizar" está activo
- ✅ Se redirige al dashboard (/) tras completar
- ✅ No vuelve a aparecer el wizard de onboarding si refrescas la página

---

## Paso 3: Settings - Configuración Multi-Org (2 min)

**URL**: http://localhost:3001/settings  
**O alternativa:** http://isosmart.local:3001/settings  (⚠️ incluir puerto `:3001`)

**Encontrarás un panel con 7 secciones en sidebar:**
1. **Organización** - Datos de la empresa
2. **Usuarios** - Gestión de perfiles
3. **Módulos IA** - Activar/desactivar SCA, SIE, ASB, SPM
4. **Notificaciones** - Alertas por riesgos, objetivos, etc.
5. **Backup y Exportación** - Respaldos manuales, descarga de datos
6. **Parámetros ISO** ⭐ **AQUÍ ESTÁ LO NUEVO**
7. **Apariencia** - Tema visual

### Validar ISO 9001:2015 (tab "Parámetros ISO")

1. Haz clic en **"Parámetros ISO"** en el sidebar izquierdo
2. Verás un **selector de estándares** en la esquina superior derecha
3. El estándar por defecto es "ISO 9001:2015"
4. **Si las cláusulas ya están cargadas:**
   - Verás un resumen: "27 de 27 aplicables"
   - Una lista de 10 secciones (4, 5, 6, 7, 8, 9, 10)
   - Cada sección se puede expandir/contraer
5. **Si NO están cargadas:**
   - Verás botón "Inicializar Cláusulas"
   - Haz clic para cargar las 27 cláusulas de ISO 9001:2015

**Qué validar:**
- ✅ Selector de estándares funciona
- ✅ Cláusulas se cargan o se inicializa correctamente
- ✅ Se pueden expandir secciones
- ✅ Cada cláusula muestra: número, nombre, responsable (si aplica), estado (Aplicable/Excluida)

### Cambiar a ISO 42001:2023

1. Abre el **selector de estándares**
2. Selecciona **"ISO/IEC 42001:2023"**
3. Haz clic en **"Inicializar Cláusulas"** (si no están pre-cargadas)

**Qué validar:**
- ✅ Se cargan las cláusulas de 42001 (aprox. 7 cláusulas totales)
- ✅ El resumen del contador se actualiza
- ✅ Las cláusulas de 9001 siguen disponibles si vuelves al selector

---

## Paso 4: Asistente Virtual IA (2 min)

**Ubicación**: Botón **flotante con icono de chat** en la esquina inferior derecha (visible en cualquier página)

### Sin API Key (Fallback Local)

1. Haz clic en el **botón de chat flotante**
2. Se abrirá un panel con:
   - Historial de conversación
   - 3 sugerencias rápidas (botones pequeños):
     - "¿Dónde registro auditorías?"
     - "¿Cómo inicializo ISO 27001?"
     - "¿Dónde cargo riesgos?"
   - Cuadro de entrada de texto
   - Botón "Enviar"

3. **Haz clic en una sugerencia** o **escribe tu pregunta**
4. El asistente responde en menos de 1 segundo (fallback local)

**Preguntas para probar:**
- "¿Dónde registro auditorías?"
- "¿Cómo inicializo ISO 27001?"
- "¿Dónde cargo riesgos?"
- Cualquier otra pregunta → te dará respuesta genérica de fallback

**Qué validar:**
- ✅ Panel se abre/cierra correctamente
- ✅ Mensajes aparecen con rol usuario/asistente diferenciados
- ✅ Sugerencias rápidas funcionan
- ✅ Respuestas aparecen instantáneamente (fallback local)

### CON API Key (Streaming Real - Opcional)

Si tienes una API key de OpenAI (o compatible):

1. **Crea** `backend/.env` en `/home/aplicacion/projects/isosmart/backend/`:
   ```
   AI_ASSISTANT_API_KEY=sk-proj-xxx...
   AI_ASSISTANT_API_URL=https://api.openai.com/v1/chat/completions
   AI_ASSISTANT_MODEL=gpt-4o-mini
   ```

2. **Reinicia backend**: `Ctrl+C` en terminal backend y levanta nuevamente
3. Prueba el asistente de nuevo → **verás respuestas en streaming** (texto aparecerá letra por letra)

---

## Paso 5: Dashboard Principal (30 seg)

**URL**: http://localhost:3001/  
**O alternativa:** http://isosmart.local:3001/  (⚠️ incluir puerto `:3001`)

Ahora que completaste onboarding, el dashboard debe mostrarte:
- Header con logo + nombre org + selector de idioma
- Sidebar con todos los módulos
- Panel del asistente flotante disponible

**Qué validar:**
- ✅ Dashboard carga sin errores
- ✅ Sidebar navigation funciona
- ✅ Selector de idioma en header está activo
- ✅ Asistente flotante visible en esquina inferior derecha

---

## Paso 6: Cambiar Idioma (1 min)

1. Ve al dashboard (/)
2. Busca el **selector de idioma** en el header superior derecho (junto a campana y settings)
3. Cambia entre:
   - **Español (LATAM)**
   - **English**
   - **Português**

**Qué validar:**
- ✅ El idioma se persiste en localStorage
- ✅ Textos del header, sidebar y panel asistente cambian instantáneamente
- ✅ Idioma se mantiene al navegar entre páginas

---

## Checklist de Validación Final

| Feature | Estado | Notas |
|---------|--------|-------|
| Login con admin@isosmart.local | ✅ | Email/password auth |
| Onboarding Guard (primera vez) | ✅ | Redirige a /onboarding |
| Wizard de Onboarding | ✅ | Selector de idioma, ISO 9001 obligatorio |
| Settings Multi-Org | ✅ | Panel lateral con 7 secciones |
| ISO 9001:2015 Parámetros | ✅ | 27 cláusulas, expandible |
| ISO 42001:2023 Parámetros | ✅ | ~7 cláusulas, inicializable |
| Cambio de Estándares | ✅ | Selector dinámico |
| Asistente Fallback Local | ✅ | Respuestas instantáneas |
| Asistente Streaming Real | ⚠️ | Requiere API key en .env |
| i18n Español/English/Português | ✅ | Selector en header |
| Limpieza de datos realizada | ✅ | 1 org, 1 usuario |

---

## Troubleshooting

### "Puerto 8001 ya está en uso"
```bash
fuser -k 8001/tcp
cd /home/aplicacion/projects/isosmart/backend
./venv_ai/bin/python manage.py runserver 0.0.0.0:8001
```

### "Frontend no carga en 3001"
- Vite cambia automáticamente si el puerto está ocupado
- Verifica con: `curl -s http://localhost:3001 | head -c 50`
- Confirma URL en terminal de npm

### "Onboarding no desaparece"
- Cierra sesión y vuelve a loguear
- El guard verifica el estado en `settings/onboarding_status/`

### "Asistente no responde"
- Verifica que backend esté activo: `curl http://127.0.0.1:8001/health`
- Sin API key, el fallback es automático (respuestas rápidas locales)

---

## Tiempo Total Estimado

⏱️ **5 minutos** para completar todos los pasos

---

**¡Listo para probar!** 🚀
