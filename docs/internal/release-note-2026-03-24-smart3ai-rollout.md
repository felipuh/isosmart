# Release Note - Smart3AI Rollout

Fecha: 2026-03-24
Estado: Completado

## Resumen ejecutivo

Se completaron ajustes de infraestructura, estabilidad y diseño para unificar ISO Smart, AdminApps y Landing en un mismo marco de despliegue y branding.

Resultado principal:

- Landing operativo por dominio y por ruta fallback.
- AdminApps sin error 502 en login.
- Paleta visual alineada con ISO Smart en Landing y AdminApps.
- Checklist interno de inicializacion cerrado y actualizado.

## Cambios por repositorio

### 1) AdminApps

Repositorio: https://github.com/felipuh/adminapps.git
Rama: `development`
Commit: `59dafc2f`

Cambios:

- Unificacion de entrypoints para usar settings canonicos.
- Ajustes de tema/paleta a marca ISO Smart (`#004990` family).
- Correccion de tokens legacy de color en dashboard.

Archivos destacados:

- `backend/manage.py`
- `backend/adminapps/wsgi.py`
- `frontend/tailwind.config.js`
- `frontend/src/index.css`
- `frontend/src/pages/DashboardPage.jsx`

### 2) Landing

Repositorio: https://github.com/felipuh/landing.git
Rama: `master`
Commit: `a0dcc2f`

Cambios:

- Rebranding visual completo (paleta, acentos y gradientes) alineado con ISO Smart.
- Consistencia de estilo entre pagina principal y pagina de producto ISO Smart.

Archivos destacados:

- `index.html`
- `isosmart.html`

### 3) ISO Smart

Repositorio: https://github.com/felipuh/isosmart.git
Rama: `development`
Commit: `ddaf387`

Cambios:

- Configuracion Nginx actualizada para incluir host de landing.
- Ruta fallback de landing en `isosmart.local/landing/` para entornos con DNS limitado.
- Titulo del frontend corregido a branding oficial.
- Checklist interno actualizado con evidencia y cierre operativo.

Archivos destacados:

- `nginx_isosmart.conf`
- `frontend/index.html`
- `docs/internal/SMART3AI_INIT_CHECKLIST.md`

## Validaciones ejecutadas

- `http://isosmart.local/` -> 200
- `http://isosmart.local/landing/` -> 200
- `http://landing.isosmart.local/` -> 200
- `http://adminapps.isosmart.local/` -> 200
- `http://adminapps.isosmart.local/health` -> 200
- `POST http://adminapps.isosmart.local/api/auth/login/` con credenciales invalidas -> 401 (esperado)

## Consideraciones operativas

- El error `ERR_NAME_NOT_RESOLVED` corresponde a resolucion DNS/hosts, no a tecnologia del landing (HTML vs React).
- Se normalizo el entorno para evitar procesos redundantes en PM2 que causaban conflicto de puerto en AdminApps.
- HTTPS no se configuro en esta fase; validacion realizada en HTTP.

## Criterio de aceptacion (cumplido)

- Landing accesible por dominio.
- AdminApps accesible sin 502 en login.
- Branding consistente en los tres frentes.
- Repositorios con cambios integrados y publicados en remoto.

## Mensaje sugerido para equipo

Se completaron y publicaron los ajustes de Smart3AI del 24/03/2026.

Incluye:

- estabilizacion de AdminApps (sin 502 en login),
- unificacion de paleta de marca con ISO Smart,
- habilitacion de landing por dominio y ruta fallback,
- cierre del checklist operativo con evidencias de QA.

Favor de validar navegacion en:

- `http://isosmart.local/`
- `http://landing.isosmart.local/`
- `http://adminapps.isosmart.local/`

Si se detecta un problema de resolucion en cliente, usar temporalmente:

- `http://isosmart.local/landing/`
