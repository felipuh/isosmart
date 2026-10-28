# Checklist QA Preproduccion - ISO Smart

Fecha base: 2026-03-17
Objetivo: validar estabilidad funcional, tecnica y operativa antes de habilitar trabajo final en AdminApps y landing de pago para salida a produccion.

## 1) Frontend (React/Vite)

- [x] Dependencias instaladas sin errores (`npm ci` o `npm install`)
- [x] Lint sin errores ni warnings (`npm run lint`)
- [x] Build de produccion exitoso (`npm run build`)
- [x] E2E completo en verde (`npm run test:e2e`)
- [x] Smoke i18n en verde (`npm run test:i18n:smoke`)

## 2) Backend (Django)

- [x] Health check de Django (`./venv_ai/bin/python manage.py check --settings=backend.settings_test`)
- [x] Migraciones consistentes (`./venv_ai/bin/python manage.py makemigrations --check --dry-run --settings=backend.settings_test`)
- [x] Tests de backend en verde (`./venv_ai/bin/python manage.py test --settings=backend.settings_test`)
- [x] Verificacion focalizada modulo core (`./venv_ai/bin/python manage.py test core --settings=backend.settings_test`)

## 3) Integracion y ejecucion

- [x] API y frontend levantan sin errores criticos en logs
- [x] Login y rutas protegidas funcionan con sesion valida
- [x] Flujo onboarding estable en 3 idiomas (es-LATAM, en, pt)
- [x] Export/backup y dashboards con proteccion tenant estables

## 4) Operacion y observabilidad

- [x] Celery worker inicia sin errores de pidfile/ruta
- [x] Redis accesible para broker/result backend
- [x] Nginx/proxy sin 5xx en rutas criticas
- [x] Logs rotan y no se versionan archivos temporales

## 5) Criterio de salida a produccion

Se considera aprobado cuando:

- Todos los checks automatizados del punto 1 y 2 estan en verde.
- No existen errores criticos/altos abiertos en flujos de login, onboarding, dashboard y settings.
- Hay evidencia de smoke de integracion estable (frontend + API + worker).

## 6) Evidencia de ejecucion (esta corrida)

Estado global: APROBADO CON RESERVA (actualizado 2026-04-11)

- Frontend build: PASS (`npm run build`) el 2026-03-17.
- Frontend lint: PASS LIMPIO (`npm run lint`) el 2026-03-17, sin errores ni warnings.
- Frontend E2E completo: PASS (8/8) el 2026-03-17.
- Frontend i18n runtime: PASS (6/6) el 2026-03-17.
- Django check: PASS (`manage.py check --settings=backend.settings_test`).
- Django migrations check: PASS (`manage.py makemigrations --check --dry-run --settings=backend.settings_test`).
- Django test suite: PASS (55 tests).
- Django core test suite: PASS (55 tests).
- Redis broker/result: PASS (`db1: True`, `db2: True`).
- Celery inspect ping: PASS (`1 node online`).
- Runtime ports detectados: 3001 frontend, 6379 Redis, 8001 ISO Smart backend, 8000 AdminApps backend.
- Proxy API desde frontend: PASS (`/api/auth/login/` responde `405`, consistente con endpoint existente que requiere POST).

### Actualizacion de cierre (2026-04-11)

- IsoSmart frontend build: PASS (`npm run build`).
- AdminApps frontend build: PASS (`npm run build`).
- Landing runtime: PASS (`GET http://127.0.0.1:4180/` => `200`).
- Barrido dialogs frontend: PASS (sin usos nativos de `alert(` o `confirm(` en `frontend/src`).
- Smoke login ISO Smart directo (`POST http://127.0.0.1:8001/api/auth/login/`): FAIL (`400`).
- Smoke login via proxy frontend (`POST http://127.0.0.1:3001/api/auth/login/`): FAIL (`400`).

Detalle de error observado en ambos login smoke:

- `{"non_field_errors":["No fue posible validar tu acceso contra AdminApps. Contacta al administrador."]}`

Implicacion para certificacion:

- El requerimiento de UI/UX y build tecnico esta cumplido.
- La certificacion end-to-end queda pendiente por integracion de autenticacion con AdminApps.
- Para declarar 100% cerrado, ambos endpoints de login (`8001` y `3001`) deben responder `200` con credenciales validas.

## 7) Hallazgos y correcciones

Registrar aqui cada hallazgo con severidad, causa y fix aplicado.

- H-001 | Severidad: Media | Frontend lint fallaba por errores reales.
	Causa: hooks/imports sin uso en componentes y specs Playwright sin globals de Node en ESLint.
	Correccion: se removieron imports/variables no usados en `OnboardingGuard.jsx` y `Layout.jsx`, se corrigio dependencia de `useMemo` en `ProcessDiagram.jsx` y se agrego override de globals Node para `frontend/tests/**` en `frontend/eslint.config.js`.

- H-002 | Severidad: Media | Warnings de hooks en frontend.
	Causa: dependencias faltantes en `useEffect`/`useCallback` en multiples pantallas (principalmente `t` y loaders memoizados).
	Correccion: se memoizaron loaders inline y se completaron dependencias de hooks en modulos de leadership, operations, planning, resources y componentes compartidos.
	Estado: resuelto en esta corrida; `npm run lint` quedo limpio.

- H-003 | Severidad: Baja-Media | Ambiguedad operativa entre `8001` y `8000`.
	Causa: coexisten dos backends locales y la evidencia previa mezclaba puertos sin mapear servicio.
	Correccion: se verifico con health y auth que `127.0.0.1:8001` es ISO Smart y `127.0.0.1:8000` corresponde a AdminApps (URLconf `config.urls`).
	Estado: resuelto en checklist con topologia explicita.

- H-004 | Severidad: Media | Archivos de runtime seguian versionados y ensuciaban cada corrida de QA.
	Causa: `logs/ai/celery_worker.log`, `logs/ai/frontend-out-0.log` y `data/chromadb/chroma.sqlite3` estaban trackeados aunque `.gitignore` ya los ignora.
	Correccion: se desindexaron con `git rm --cached` para que el cambio final deje de registrar artefactos locales de ejecucion.

- H-005 | Severidad: Alta | 7 vulnerabilidades npm en frontend (2 moderate, 5 high).
	Causa: paquetes desactualizados: axios 1.x (DoS via __proto__), react-router 7.x (CSRF/XSS), rollup 4.x (path traversal), flatted (prototype pollution), minimatch/ajv (ReDoS).
	Correccion: `npm audit fix` actualizo 9 paquetes a versiones seguras. Build y lint verificados post-update: PASS.
	Estado: 0 vulnerabilidades tras correccion.

- H-006 | Severidad: Media | Nuevo error de lint en VirtualAssistantPanel.jsx tras actualizacion de eslint-plugin-react-hooks a v7.
	Causa: regla `react-hooks/set-state-in-effect` marcaba `setConversationId` llamado sincronamente dentro de `useEffect` para recuperar estado de localStorage.
	Correccion: se reemplazo el `useEffect` de hidratacion por inicializador lazy de `useState(() => localStorage.getItem(...))`, eliminando el ciclo de renderizado innecesario.
	Estado: `npm run lint` queda limpio; `npm run build` PASS.
