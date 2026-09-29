# Phase 31.4 V2.5 AdminApps Endpoint Remediation

## Verdict

`ADMINAPPS_ENDPOINT_REMEDIATION_CODE_PASS / INTEGRITY_RECONCILIATION_REQUIRED`

The endpoint binding remediation and focused mocked tests pass. P1 is not live-closed.

## Retry 18 blocker and root cause

Retry 18 reached `STAGE_EXT` and failed at `QmsOrganizationCommandService.create_organization` because entitlement validation used `http://127.0.0.1:8000/api/integration`. The run allocation had isolated AdminApps HTTP port `41491`, but `ADMIN_APPS_BASE_URL` was not injected before Django settings initialization. The settings fallback then selected localhost. The client also contained an independent localhost fallback when the settings mapping was absent.

## Authoritative configuration

The authoritative key is `ADMIN_APPS_BASE_URL`. The corrected path is:

`resource allocation -> ADMIN_APPS_BASE_URL injected before Django startup -> settings.ADMIN_APPS_INTEGRATION[BASE_URL] -> AdminAppsClient -> entitlement validation and other AdminApps calls`

A future disposable allocation supplies its own dynamic endpoint, for example `http://127.0.0.1:<allocated-adminapps-port>/api/integration`. No Retry 18 port is hard-coded.

## Fallback and authorization behavior

The settings and client localhost defaults were removed. Missing or malformed configuration is rejected before a request. Unreachable, incorrect, unauthorized, or denied AdminApps responses remain denied. `QmsOrganizationCommandService` continues to call entitlement validation with `allow_local_fallback=False` and preserves `AdminApps product entitlement denied`.

## Files changed

- `backend/backend/settings.py`
- `backend/integration/client.py`
- `backend/integration/test_adminapps_endpoint_remediation.py`
- this JSON evidence artifact
- this report

## Tests

Focused command:

```text
cd backend && .venv/bin/python manage.py test integration.test_adminapps_endpoint_remediation --verbosity 1
```

Result: 8 tests passed. Coverage includes dynamic/non-8000 endpoint selection, localhost override, missing and malformed endpoint, unreachable endpoint, entitlement denied, entitlement allowed, and QMS organization creation after allowed entitlement. Tests use mocks only; no PostgreSQL, containers, live AdminApps, Retry 19, or live Stage EXT were run.

The root `.venv` was also checked but lacks Django; no tests ran under that interpreter. The repository `backend/.venv` produced the passing result above.

## Integrity impact

`backend/backend/settings.py` is listed as a protected source in `PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V3.json`. V3 was not modified. A normal successor current-integrity reconciliation is required for the protected-source hash changes before any future live authorization. V2.4 and all historical Retry 18 artifacts remain unchanged.

## Disposition

- Phase 31.5: `EXECUTION_HELD`
- Live retry executed: `NO`
- P1: code remediation passes, pending successor integrity reconciliation and later disposable live revalidation
- Required sequence: configuration remediation -> integrity reconciliation -> authorization -> next disposable run
