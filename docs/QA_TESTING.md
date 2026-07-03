# QA Testing Gate - ISO Smart

Date: 2026-07-03

## Official Local Gate

Run from `/home/felipe/proyectos/isosmart/backend`:

```bash
. .venv/bin/activate
python manage.py check
DJANGO_ENV=production \
SECRET_KEY=test-secure-key-for-check-only-2026-07-03-not-a-real-secret-value \
ALLOWED_HOSTS=example.com \
CSRF_TRUSTED_ORIGINS=https://example.com \
CORS_ALLOWED_ORIGINS=https://example.com \
SECURE_SSL_REDIRECT=true \
SESSION_COOKIE_SECURE=true \
CSRF_COOKIE_SECURE=true \
SECURE_HSTS_SECONDS=31536000 \
SECURE_HSTS_PRELOAD=true \
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py showmigrations --plan
DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test
```

Run from `/home/felipe/proyectos/isosmart/frontend`:

```bash
npm run lint
npm run build
```

## Why The Default Test Command Can Fail

The default `backend.settings` configuration uses PostgreSQL databases for `default`, `ai_db`, and `audit_db`. Django creates test databases when running the default test command. If the configured database role does not have `CREATEDB`, the default command fails before the suite can run.

For this release candidate, the official local gate is `DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test`. `settings_test` uses isolated SQLite databases and keeps the suite independent from local PostgreSQL privileges.

## CI/Staging Database Permission Fix

If CI/staging must run the default PostgreSQL-backed test command, grant test database creation only to the CI/staging DB role:

```sql
ALTER ROLE isosmart_user CREATEDB;
```

Use the real CI/staging role name. Do not grant test database creation to a production runtime role.
