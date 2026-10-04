#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${ROOT_DIR}/.venv/bin/python}"
TEST_SETTINGS="backend.settings_postgres_integration"
HARNESS="${FOUNDATION_HARNESS:-foundation/postgres_wp2_harness.py}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Supported Django 4.2 interpreter not found: ${PYTHON_BIN}" >&2
  exit 2
fi

export DJANGO_SETTINGS_MODULE="${TEST_SETTINGS}"
export ISO_SMART_POSTGRES_INTEGRATION=1
export USE_SQLITE_DATABASE=0

cd "${ROOT_DIR}"
engine="$(${PYTHON_BIN} manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])")"
if [[ "${engine}" != "django.db.backends.postgresql" ]]; then
  echo "Refusing integration tests with database engine: ${engine}" >&2
  exit 3
fi

FOUNDATION_HARNESS="${HARNESS}" exec "${PYTHON_BIN}" foundation/postgres_foundation_gate.py "$@"