# LAB05-C1-R3 — real cross-product HTTP SSO

Run from the sanitized AdminApps checkout, using its prepared R1 Python
environment (including Django, DRF, SimpleJWT, django-filter, Pillow, requests,
PyJWT, cryptography and psycopg2). PostgreSQL tools must be on PATH. No dependency
installation, external service or operational env file is needed by the runner.

```sh
/tmp/adminapps-sec02-20261022/.venv-sec02/bin/python backend/lab04/run.py \
  --http-isosmart /home/felipe/proyectos/isosmart-lab05-c1-r2/backend
```

This flag provisions the existing disposable R1 database and invokes `run.py`.
It does **not** run either R1 or R2 acceptance. ISO's R2 bootstrap is reused only
for its real-model schema projection; R3 adds the real `resources.Resource` model
and an immutable principal-to-tenant authority table. No consumer migrations are
executed or faked. Both private clusters are destroyed, including on failure.
The AdminApps runner prints an evidence directory under `/tmp/adminapps-lab04-*`.
Retain only `r3-result.json`, `r3-cleanup.json` and `cleanup.json`; failure logs
are private diagnostics, not publishable evidence.

There are three actual WSGI listeners bound to `127.0.0.1`: AdminApps SSO and ISO
instances A/B. Each ISO instance authenticates directly to PostgreSQL as its own
non-owner, NOBYPASSRLS role; it loads only its own SQL password. Every HTTP request
reconnects PostgreSQL. The middleware verifies `current_user = session_user`,
the owner-maintained authority row, and the configured tenant. Existing
`central_auth.validate_proof` verifies CENTRAL RS256 plus real introspection and
the instance's fixed tenant before `sync_identity` can write. No runtime SET ROLE
or request-selected database connection exists. Forced RLS uses `session_user`.

Central RSA private material stays in AdminApps. ISO receives the public keyring
and has a separate ephemeral LOCAL RSA key for the existing session contract.
The maintenance negative-input generator signs deliberately invalid proofs in
AdminApps; none is accepted as a successful authentication. Observation wrappers
count calls and execute the original functions; they do not substitute transport,
authentication, authorization, ORM or persistence. Database snapshots compare all
consumer table rows around rejected requests, excluding nontransactional sequences.

Existing endpoints: GET `/api/auth/csrf/`; CSRF-protected POST `/api/auth/login/`;
GET `/api/auth/me/`; GET/POST `/api/resources/`; GET `/api/resources/{id}/`.
Login sets HttpOnly `isosmart_access` and `isosmart_refresh` cookies, not response
body tokens. Protected requests use the cookie and live central authority.
The laboratory disables Secure only for its declared loopback HTTP transport.
Scopes are enforced by the existing ResourceViewSet and authorization contract.
Tenant A grants the shared subject `user`; tenant B grants `viewer`.

Revocation tests replay the **exact same** pre-logout cookie and CENTRAL proof,
check durable central revocation/outbox state, and assert that protected handlers
never execute and no ISO table changes. They repeat across fresh SQL connections
and a real central server restart. Scope removal also revokes the existing central
session; restoring scopes does not revive it. Central outage returns 503 and a
matching usable local password cannot enable fallback.

This is not a production topology or a full application schema. Processes run
under one OS account; separate OS/container isolation is not demonstrated. A
foreign cookie whose profile is hidden by RLS returns the existing generic 503
authority error, while a valid foreign-tenant login is rejected with 403 before
projection. Both fail closed. Normal settings, billing, migrations, workers,
Phase31.5, MedSupplier and existing databases are untouched.

`PRODUCTION_READY = FALSE` · `PHASE31_5 = EXECUTION_HELD` ·
`S3_DECISION_02A_NOT_CLOSED` · `NO_DEPLOYMENT` · `NO_SHARED_DB_MUTATION`.
