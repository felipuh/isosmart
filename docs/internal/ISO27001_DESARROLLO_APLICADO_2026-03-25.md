# ISO 27001 (Desarrollo) - Controles aplicados

Fecha: 2026-03-25
Alcance: IsoSmart, AdminApps, Landing
Exclusion solicitada: TLS/certificados en esta etapa

## 1) Controles aplicados en codigo y configuracion

### 1.1 Gestion de secretos y configuracion segura
- Se eliminaron secretos hardcodeados y se parametrizaron via variables de entorno en settings Django.
- Se agregaron plantillas de entorno para estandarizar configuracion segura:
  - IsoSmart: `backend/.env.example`
  - AdminApps: `backend/.env.example`
  - Landing: `.env.example`
- Se reforzaron reglas de exclusion para evitar fuga de secretos en Git:
  - AdminApps: `.gitignore`
  - Landing: `.gitignore`

Relacion ISO 27001: gestion de informacion sensible, prevencion de divulgacion no autorizada, control de configuraciones de seguridad.

### 1.2 Hardening de aplicacion web (backend)
- IsoSmart (`backend/backend/settings.py`):
  - `ALLOWED_HOSTS` por entorno (se elimino wildcard global).
  - Permisos DRF por defecto a `IsAuthenticated`.
  - Eliminacion de middleware duplicado.
  - Cookies y politicas de seguridad activas (`HttpOnly`, `SameSite`, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `COOP`).
  - CORS y CSRF por variables de entorno.
  - Throttling API (`AnonRateThrottle`, `UserRateThrottle`) con tasas configurables.

- AdminApps (`backend/config/settings.py`):
  - Fortalecimiento de parsing de entorno para booleanos/listas.
  - Eliminacion de fallback inseguro para password de base de datos.
  - CORS/CSRF confiables por entorno.
  - Hardening de cookies/headers de seguridad.
  - Throttling API y reduccion de nivel de logs por defecto para apps.

- AdminApps legacy (`backend/adminapps/settings.py`):
  - Eliminacion de defaults inseguros de `SECRET_KEY` y DB password.

Relacion ISO 27001: control de acceso logico, reduccion de superficie de ataque, proteccion contra abuso y enumeracion, configuracion segura por defecto.

### 1.3 Hardening de frontend/static servers
- AdminApps frontend (`frontend/server.js`):
  - Desactivacion de fingerprinting por `X-Powered-By`.
  - Headers de seguridad base en respuestas HTTP.

- Landing:
  - Se reemplazo servidor de desarrollo inseguro por servidor Node controlado (`server.mjs`).
  - Se agregaron headers de seguridad y CSP pragmatica compatible con fuentes externas necesarias.
  - Scripts de arranque actualizados en `package.json`.

Relacion ISO 27001: reduccion de exposicion en capa web, controles preventivos en entrega de contenido, defensa en profundidad.

### 1.4 Scripts operativos y pruebas
- AdminApps `test_integration.sh`:
  - Se eliminaron credenciales/API key hardcodeadas.
  - Se exige provision por variables de entorno y validacion de presencia.

Relacion ISO 27001: operaciones seguras, minimizacion de datos sensibles en scripts, trazabilidad de ejecucion.

## 2) Controles ISO 27001 soportados (mapeo practico)

- Configuracion segura por defecto y hardening tecnico.
- Gestion de secretos en entorno de desarrollo.
- Control de acceso API por autenticacion y permisos por defecto.
- Protecciones contra abuso (throttling/rate limiting).
- Protecciones de navegador y cabeceras de seguridad.
- Separacion de configuracion por entorno.
- Evidencia documental de medidas tecnicas implementadas.

## 3) Pendientes recomendados (siguiente iteracion)

1. Integrar escaneo de dependencias en CI (`pip-audit`, `npm audit`, SCA) con politica de severidad.
2. Definir pipeline SAST (Bandit/semgrep para Python y escaneo JS).
3. Implementar centralizacion de logs de seguridad y alertas automatas.
4. Aplicar principio de minimo privilegio en roles/permissions endpoint por endpoint.
5. Registrar y revisar formalmente excepciones de seguridad de desarrollo.

## 4) Validacion

- Verificacion de errores de sintaxis/lint sobre archivos modificados: sin errores detectados.
- Cambios aplicados sin TLS/certificados, conforme solicitud de alcance.
