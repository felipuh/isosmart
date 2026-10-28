# ADR — Phase31.5 enterprise operations

## Context

Phase31.5 requires deterministic deployment, secure browser authentication, recoverable PostgreSQL backups, and an operable transactional outbox. Existing PostgreSQL/RLS evidence is frozen and remains authoritative.

## Decision

- Browser authentication uses short-lived and refresh JWTs only in `HttpOnly`, `Secure` production cookies. The frontend sends no bearer token and persists no authentication token. Unsafe cookie-authenticated requests require Django CSRF validation.
- Deployment is defined by the version-pinned Compose topology: PostgreSQL, Redis, migrate-once, non-root web process, and the isolated outbox worker. Production environment validation rejects insecure settings and SQLite.
- Backups use `pg_dump` custom archives, `pg_restore --list`, SHA-256 manifests, explicit retention ownership, and platform-supplied encryption/decryption commands in production. Restore verifies checksum and archive before mutation.
- The existing PostgreSQL `SKIP LOCKED` outbox remains the dispatcher. The management command operates one trusted tenant, retries persisted failures, records errors, and only delivers to the existing local Foundation consumer; it makes no external calls.

## Security and operations

Cookie authentication trades header tokens for CSRF enforcement. Production secrets, encryption keys, and backup destinations are injected only through environment/secret systems. Worker lifecycle is supervised by Compose and uses a required trusted tenant UUID.

## Alternatives

Keeping localStorage JWTs was rejected because XSS exposes bearer credentials. Adding Celery/Redis delivery for the Foundation outbox was rejected because a safe database dispatcher and local consumer already exist. A custom backup format was rejected in favor of PostgreSQL tooling.

## Verification

Frontend build passed; Django system check passed; shell and Compose syntax passed. SQLite test setup remains incompatible with existing PostgreSQL-specific migrations and is recorded as an environment limitation, not waived.
