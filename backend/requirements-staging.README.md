# Isolated dependency candidate — 2026-10-29

Separate objective: Linux x86_64 / CPython 3.12.13, Django 5.2.18 LTS. This candidate does not change operational `requirements.txt`, services or existing environments. The old requirements remain unsuitable for a new supported deployment. Promotion is pending PostgreSQL migration/schema/HTTP regression on an accredited isolated target.

Changes from backend requirements: Django 4.2.22 → 5.2.18; DRF 3.15.2 → 3.17.1; SimpleJWT 5.4.0 → 5.5.1. ISO Smart additionally changes django-celery-beat 2.5.0 → 2.8.1 to remove its Django<5 bound. All other direct pins are retained. The lock records the resolved transitive graph and artifact SHA256s; it is scoped to this OS/Python target, not a universal lock.

Django 4.2 ended extended support on 2026-04-07. Django 6.0 removes `CheckConstraint(check=...)`, used by ISO's models/migrations, and the observed 6.0.6 environment violates installed celery-beat/timezone-field requirements. Django 5.2 keeps the deprecated keyword and avoids rewriting historical migrations during this P0 objective. Follow-up must replace deprecated calls in a separately reviewed compatibility change and validate migration state on disposable PostgreSQL.

Official sources consulted 2026-10-29:
- https://www.djangoproject.com/download/ (5.2.18; extended support through April 2028)
- https://docs.djangoproject.com/en/5.2/faq/install/ (Python support)
- https://docs.djangoproject.com/en/6.0/releases/6.0/ (removed check argument)
- https://github.com/celery/django-celery-beat/releases (Django 5.2 support)

Reproduction, using pre-existing uv and Python (substitute a NEW writable dedicated path):

```sh
uv --no-config pip compile backend/requirements-staging.in --python python3.12 --generate-hashes --only-binary :all: -o backend/requirements-staging.lock
uv --no-config venv --python python3.12 /DEDICATED/isosmart/venv
uv --no-config pip sync --python /DEDICATED/isosmart/venv/bin/python --require-hashes --only-binary :all: --link-mode copy backend/requirements-staging.lock
```

Set `UV_CACHE_DIR` to an isolated volume and bound download/install concurrency. Do not use a product's active virtualenv, `--system-site-packages`, editable links or shared package directories. Do not overwrite an existing environment. Each product needs its own venv even with identical versions; sharing the immutable base interpreter is acceptable.

Executed candidate: `/tmp/smart3ai-p0-20261029/venvs/isosmart`; independent prefix, package paths and inodes; no operational site-packages on sys.path. Dependency metadata audit: zero conflicts and zero direct manifest mismatches. 452 offline test executions PASS for this consumer; real models/views/JWT with simulated persistence and central transport, zero DB/network attempts. Existing SSO B/D/session suites and new P0 tests included. No PostgreSQL migration or HTTP end-to-end execution is claimed. A dependency resolution is not a full transitive vulnerability assessment.

Run suites from backend, using this candidate's Python with `-B`: integration/tests_staging_p0_offline.py, tests_b_offline.py, tests_d_offline.py and tests_d_session_offline.py (each under integration/). ISO additionally runs tests_recovery_p0_offline.py and tests_me_p0_offline.py. Evidence is consolidated in the AdminApps isolated worktree, `docs/evidence/p0-remediation-2026-10-29/`.
