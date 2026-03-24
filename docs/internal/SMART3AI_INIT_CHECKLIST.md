# Smart3AI Multi-Project Initialization Checklist

This checklist aligns ISO Smart and AdminApps for a fresh Smart3AI rollout.

## 1) Branding alignment

- ISO Smart login footer now shows: `© 2026 ISO Smart by Smart3AI`.
- AdminApps branding now shows `Smart3AI Control Center` and `© 2026 Smart3AI`.

## 2) Bootstrap order (recommended)

1. AdminApps backend: run migrations and bootstrap script.
2. ISO Smart backend: run migrations and bootstrap script.
3. Frontends: install dependencies and run both apps.
4. Validate login with the same superuser in both systems.

## 3) AdminApps bootstrap

From `adminapps/backend`:

```bash
python manage.py migrate
SUPERUSER_PASSWORD='DefineUnaPasswordFuerte' ./scripts/bootstrap_smart3ai.sh
```

Expected baseline:

- Superuser: `felipe@smart3ai.com`
- Platform admin enabled
- Organization: `Smart3AI` (active, enterprise)
- Membership as `org_admin`

## 4) ISO Smart bootstrap

From `isosmart/backend`:

```bash
python manage.py migrate
SUPERUSER_PASSWORD='DefineUnaPasswordFuerte' ./scripts/bootstrap_smart3ai.sh
```

Expected baseline:

- Superuser: `felipe@smart3ai.com`
- Organization: `Smart3AI`
- User profile in org with role `org_admin`

## 5) Cross-system validation

- Login AdminApps with `felipe@smart3ai.com`.
- Login ISO Smart with `felipe@smart3ai.com`.
- Confirm ISO Smart login footer branding.
- Confirm AdminApps login + sidebar branding.
- Create additional colleagues from AdminApps and validate access in ISO Smart.

## 6) Next commercialization steps

- Keep AdminApps as product control center for all Smart3AI applications.
- Register each upcoming product in AdminApps with lifecycle states.
- Publish landing pages per product (ISO Smart first), with unified lead capture.

## 7) Security hardening rollout (password policy)

Apply these settings in both backends (`.env` or service environment):

```bash
PASSWORD_HISTORY_COUNT=5
TEMP_PASSWORD_MAX_AGE_DAYS=7
TEMP_PASSWORD_WARNING_DAYS=2
```

ISO Smart backend (`isosmart/backend`):

```bash
python manage.py migrate
python manage.py check
```

AdminApps backend (`adminapps/backend`):

```bash
python manage.py check
```

## 8) Functional validation of temporary passwords

- Create or reset a user from admin flow and confirm `must_change_password=true` on first login.
- Login with a temporary password that is close to expiry and confirm `security_alert.reason_code=TEMP_PASSWORD_EXPIRING`.
- Verify warning banner appears in:
	- ISO Smart profile password section.
	- AdminApps security settings section.
- Change password and confirm temporary state is cleared (`must_change_password=false`, no `security_alert`).
- Attempt password reuse in change/reset/create flows and confirm rejection with `reason_code=PASSWORD_REUSE_RECENT`.

## 9) Operational note for local test execution

- If ISO Smart tests fail creating `test_isosmart_main` with MySQL permission error (1044), grant test DB create privileges for the DB user or run tests against an isolated local test database profile.
