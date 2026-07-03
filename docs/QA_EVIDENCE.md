# QA Evidence - ISO Smart

Fecha de ejecucion principal: 2026-07-02 America/Costa_Rica.

## Backend

- Python backend validado: Python 3.12 en `backend/.venv`.
- `.venv/bin/python manage.py check`: OK.
- `.venv/bin/python manage.py check --deploy`: OK con warnings esperados si se usan valores locales de `.env`.
- `DJANGO_ENV=production ... .venv/bin/python manage.py check --deploy`: OK, sin issues, usando overrides productivos completos de prueba.
- `.venv/bin/python manage.py makemigrations --check --dry-run`: OK, sin cambios detectados.
- `.venv/bin/python manage.py test core.tests_security_guardrails --settings=backend.settings_test`: OK, 2 tests.
- `.venv/bin/python manage.py test --settings=backend.settings_test`: OK, 84 tests.
- `rg "fields\\s*=\\s*['\\\"]__all__['\\\"]" backend --glob '!**/migrations/**' --glob '!**/staticfiles/**'`: sin resultados.
- `.venv/bin/python manage.py showmigrations --plan`: ejecutado; migraciones mostradas como aplicadas.

## Frontend

- `npm ci`: OK, 0 vulnerabilidades reportadas.
- `npm run lint`: OK.
- `npm run build`: OK.
- `frontend/src/services/api.js` usa `VITE_API_BASE_URL || "/api"`.
- `frontend/.env.example` agregado con `VITE_LOCAL_AUTH_BYPASS=0`.

Build generado:

- `dist/index.html`
- bundles lazy de modulos principales y vendors.

## Observaciones

- La validacion backend usa el nuevo `backend/requirements.txt` porque el freeze raiz no es reproducible en Python 3.9 para este backend.
- Tras habilitar `SECURE_SSL_REDIRECT` por entorno, se ajusto `settings_test.py` y se relanzo la suite completa: 84 tests OK.
