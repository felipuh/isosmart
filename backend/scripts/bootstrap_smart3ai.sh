#!/usr/bin/env bash
set -euo pipefail

# Bootstrap for a fresh ISO Smart setup using Smart3AI baseline.
# Usage:
#   SUPERUSER_PASSWORD='StrongPass!123' ./scripts/bootstrap_smart3ai.sh

EMAIL="${SUPERUSER_EMAIL:-felipe@smart3ai.com}"
PASSWORD="${SUPERUSER_PASSWORD:-}"
FIRST_NAME="${SUPERUSER_FIRST_NAME:-Felipe}"
LAST_NAME="${SUPERUSER_LAST_NAME:-Admin}"
ORG_NAME="${SMART3AI_ORG_NAME:-Smart3AI}"
ORG_SLUG="${SMART3AI_ORG_SLUG:-smart3ai}"
ORG_EMAIL="${SMART3AI_ORG_EMAIL:-felipe@smart3ai.com}"

if [[ -z "${PASSWORD}" ]]; then
  echo "ERROR: define SUPERUSER_PASSWORD before running this script."
  exit 1
fi

python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model
from authentication.models import UserProfile
from core.models import Organization

email = os.getenv('SUPERUSER_EMAIL', 'felipe@smart3ai.com')
password = os.getenv('SUPERUSER_PASSWORD')
first_name = os.getenv('SUPERUSER_FIRST_NAME', 'Felipe')
last_name = os.getenv('SUPERUSER_LAST_NAME', 'Admin')
org_name = os.getenv('SMART3AI_ORG_NAME', 'Smart3AI')
org_slug = os.getenv('SMART3AI_ORG_SLUG', 'smart3ai')
org_email = os.getenv('SMART3AI_ORG_EMAIL', 'felipe@smart3ai.com')

if not password:
    raise SystemExit('SUPERUSER_PASSWORD is required')

User = get_user_model()

org, _ = Organization.objects.get_or_create(
    slug=org_slug,
    defaults={
        'name': org_name,
        'email': org_email,
        'is_active': True,
        'plan_type': 'enterprise',
        'max_users': 50,
    },
)

if org.name != org_name or org.email != org_email:
    org.name = org_name
    org.email = org_email
    org.is_active = True
    org.save(update_fields=['name', 'email', 'is_active', 'updated_at'])

user, _ = User.objects.get_or_create(
    email=email,
    defaults={
        'username': email.split('@')[0],
        'first_name': first_name,
        'last_name': last_name,
        'is_active': True,
        'is_staff': True,
        'is_superuser': True,
    },
)

user.first_name = first_name
user.last_name = last_name
user.is_active = True
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()

UserProfile.objects.update_or_create(
    user=user,
    organization=org,
    defaults={
        'role': 'org_admin',
        'is_active': True,
        'language': 'es',
    },
)

print(f'ISO Smart ready: superuser={email}, organization={org.name}')
PY

echo "Done. You can now log in with ${EMAIL}."
