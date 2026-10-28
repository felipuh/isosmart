# Phase31.5 E-07 AdminApps Rotation Mechanism

Date: 2026-10-05

## A. Governance Integrity

- This implementation adds a local credential lifecycle; it does not authorize or perform authentic credential rotation.
- `E-07 = FAIL_AUTHENTIC_ROTATION_EVIDENCE_REQUIRED`.
- `E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`.
- `Phase31.5 = EXECUTION_HELD`.
- Evidence 27 was not modified. No production/staging endpoint, customer data, environment credential value, or authentic key was accessed.
- Tests use synthetic/local credentials and Django's disposable SQLite test database.

## B. Starting Repository State

| Repository | Branch | Starting HEAD | Pre-existing changes preserved |
|---|---|---|---|
| AdminApps | `hardening/p0-p1-enterprise-readiness` | `836c4433e63f91b13af4dac8fce339d429f154f5` | Modified `backend/apps/organizations/tests_tenant_events.py` and untracked `backend/test_default.sqlite3`. |
| ISO Smart | `hardening/p0-p1-enterprise-readiness` | `db3cae34865991d7a5c4903fc4226ba83ddce681` | Existing tracked edits and untracked governance artifacts were preserved. |

Only task-owned files were changed or published.

## C. Prior Authority Discovery

The prior source diagnostic is `PHASE31_5_E07_ROTATION_AUTHORITY_DISCOVERY_2026-10-05.md`. It found plaintext `IntegrationAPIKey.key` storage, generic Admin CRUD and a create command, no dedicated rotation operation, partial audit evidence, and an ISO Smart consumer using `ADMIN_APPS_API_KEY` as `X-API-Key`. The current work addresses the missing local lifecycle mechanism; it does not change that diagnostic or its authentic-rotation finding.

## D. IntegrationAPIKey Security Model

- New keys use an internally generated 256-bit random token, represented as `iak_<32-hex-id>.<urlsafe-random-token>`.
- The raw value is returned by the service/management command once; secure persistence stores a Django `make_password` verifier, public credential ID, and safe fingerprint. The legacy `key` column is `NULL` for these records.
- `IntegrationAPIKey.save()` hashes any newly assigned raw key before writing it. This preserves compatible ORM callers without persisting their supplied raw value. Unprefixed hashed records are verified through Django's `check_password`.
- Persisted legacy rows are explicitly classified by migration as `legacy_plaintext`; no key value is rewritten by the migration. Inactive historical rows are classified as revoked. No automatic rotation occurs.
- Lifecycle state records `created`, `active`, `revoked`, or `rotated`; timestamps and `replaced_by` link the rotation. The existing model has no tenant/application foreign key or expiry field; service `name` remains its ownership label.
- Revoked or rotated verifier matches also block the settings-hash fallback, so that fallback cannot silently re-enable an old credential.

## E. Legacy Credential Compatibility

Migration `0006_integration_api_key_lifecycle` marks existing rows `legacy_plaintext` and maps `is_active` to active/revoked state without printing, rehashing, or changing their credential values. Active legacy keys continue to authenticate until the governed rotation runs. Rotation fingerprints the old value, stores only its verifier and fingerprint, clears `key`, marks it rotated/revoked, and links the replacement. Tests verify the legacy value then fails authentication, including when a matching configured hash fallback is present.

## F. Rotation Service

`apps.integration.services.rotate_integration_api_key` requires an authenticated, active staff operator. It selects the original row with `select_for_update`, rechecks the active state, generates a replacement internally, saves only the verifier and safe metadata, revokes and links the old row, and writes an audit event inside one `transaction.atomic()` block. The raw replacement is returned to the authorized caller only after the transaction succeeds. Service code does not log or persist it.

## G. Atomicity and Concurrency

- A forced audit-write exception rolls back both replacement creation and original-key revocation: `ROTATION_ATOMICITY = PASS`.
- PostgreSQL row locking is implemented and a focused two-thread concurrency test is present.
- The local test configuration forces SQLite, so that PostgreSQL-only test was skipped. PostgreSQL client utilities are installed, but no isolated disposable PostgreSQL test database was established; no PostgreSQL server/database was contacted. The test result therefore does not claim a live PostgreSQL concurrency run.

## H. Management Authority Surface

- `rotate_integration_key --id <record-id> --actor-id <staff-user-id>` invokes the rotation service.
- `create_integration_key --name <service> --actor-id <staff-user-id>` uses the secure creation service.
- Neither command accepts a raw key argument or environment-sourced replacement. Both print the generated credential only in their direct one-time command output, along with safe metadata and an unrecoverability warning.
- The authentic rotation command was not executed.

## I. Admin Hardening

Integration API key Admin is view-only. It shows safe identifiers, fingerprint, lifecycle state, usage metadata, and timestamps. It excludes raw key and verifier/hash from forms, list views, and search; adding, changing, and deleting credentials through generic Admin are disabled. HTTP tests verify legacy plaintext does not appear in list or detail output.

## J. Authentication Validation

`require_api_key` delegates to the lifecycle verifier. Active hashed and explicitly classified legacy credentials authenticate; wrong, malformed, revoked, and rotated credentials are rejected. The replacement passes `/api/integration/health/`; the old key receives `401`. Configured digest fallback remains compatible, uses constant-time digest comparison, and checks rotated/revoked verifiers before accepting a match. Cross-tenant ownership does not apply to this source model: keys are service-scoped and the model has no tenant relation.

## K. Fingerprint Contract

Fingerprints are `hmac-sha256-v1:<64 lowercase hex characters>`, computed with HMAC-SHA256 using the application `SECRET_KEY` and a domain/version prefix. They are deterministic while that key remains stable, irreversible for practical evidence correlation, and are not accepted for authentication. Authentication uses the separately stored Django password verifier. Old and replacement fingerprints are recorded separately and tested to differ.

## L. Audit Evidence

`IntegrationAPIKeyAuditEvent` records create/rotation operation, event UUID, old/new credential IDs, old/new fingerprints, service name, actor, timestamp, and safe lifecycle metadata. It does not store the raw key, verifier, password, or JWT. Rotation audit failure is included in the atomic rollback test.

## M. Safe Future Acceptance Probe

Use only the narrow health route:

```text
GET /api/integration/health/
X-API-Key: <credential>
```

Expected old-key rejection: `401`. Expected replacement acceptance: `200` with generic service health only. Synthetic tests exercise both outcomes; no real endpoint was called.

## N. ISO Smart Consumer Compatibility

Read-only source verification confirms `backend/backend/settings.py` reads `ADMIN_APPS_API_KEY`, and `backend/integration/client.py` sends it as `X-API-Key`. The runtime consumer requires only replacement of that injected value and restart/reconstruction of consumers; no ISO Smart runtime source change was needed. No ISO Smart runtime key database/persistence was found. Several historical governance setup scripts do write AdminApps-side `IntegrationAPIKey` rows from process-supplied values; they were not executed or modified. New ORM saves now hash those values before persistence, but such direct setup writes are not a substitute for the audited rotation service.

No `.env` file or live environment value was opened.

## O. Tests

Command:

```text
cd /home/felipe/proyectos/adminapps/backend
./.venv/bin/python manage.py test apps.integration.tests --verbosity 1
```

Result: 29 tests discovered, 28 passed, 1 PostgreSQL-only concurrency test skipped on SQLite. Coverage includes secure service and direct ORM creation, non-persistence, fingerprints, auth outcomes, legacy compatibility and rotation, linkage, forced rollback, audit secrecy, Admin output, command interface, and data migration classification. Django system checks reported no issues.

## P. Secret Leakage Review

`RAW_CREDENTIAL_LEAK_REGRESSION = PASS`. Changes contain only synthetic fixture values. No authentic credential, production key, private key, or raw credential was added to governance evidence. Test command output is captured in memory; only the explicitly required one-time command output contains generated test keys. No application logger records generated values. No `.env` value was accessed.

## Q. Remaining Authentic Rotation Blockers

- E-07 still requires operator-authorized authentic old-key rejection and replacement-key acceptance evidence after the replacement is installed in the approved ISO Smart runtime secret injection and relevant processes are restarted.
- The authentic historical AdminApps key has not been identified or rotated here. Settings-hash acceptance must be checked/configured under the separate runtime authority as appropriate.
- Initial administrator-password status remains the separately adjudicated `INITIAL_ADMINISTRATOR_PASSWORD` blocker; no account was read, authenticated, or reset.
- PostgreSQL concurrency needs execution against a confirmed disposable PostgreSQL test database before claiming database-level race-test evidence.
- Historical governance setup scripts can write/update credentials directly through ORM and do not create rotation audit events; they are not authorized rotation interfaces.

## R. Final Verdict

**`ROTATION_MECHANISM_READY_FOR_AUTHORIZED_USE`** for the source-defined AdminApps service/command path, subject to the PostgreSQL test limitation above. This is local technical evidence only and is not authentic rotation evidence.

`E-07 = FAIL_AUTHENTIC_ROTATION_EVIDENCE_REQUIRED`

`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`

`Phase31.5 = EXECUTION_HELD`

No authentic credential rotation is authorized by this slice.
