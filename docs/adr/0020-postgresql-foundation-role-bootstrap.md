# ADR-0020: PostgreSQL foundation roles before Django migrations

- Status: Accepted for isolated Retry 10 validation
- Date: 2026-09-18

## Decision

The existing `backend/foundation/postgres_foundation_gate.py` owns the cluster bootstrap for foundation roles. Django migrations own schemas, tables, RLS policies, and table grants, but never create cluster roles. An isolated cluster is bootstrapped before `manage.py migrate`; its database is owned by the dedicated migrator. Normal QMS commands connect as the separate app principal, and AdminApps projection ingress connects as the projector principal. Restricted function owner roles have `NOLOGIN` and can be set only by the migrator.

The reusable `bootstrap_idempotent` entry point accepts a fresh cluster and an already matching cluster. It refuses role attribute drift, membership drift, partial role setup, and incorrect database ownership. A missing database with otherwise preexisting roles is treated as partial setup and requires DBA review; a wholly fresh cluster creates its database as part of bootstrap. Role names are run-scoped, and passwords are generated ephemerally for the isolated run. The bootstrap does not grant superuser, database creation, role creation, or RLS bypass to any foundation role.

The Django PostgreSQL connection accepts non-secret `DB_SESSION_OPTIONS` so migrations that assign restricted function ownership see the same `foundation.*_role` settings in `settings_dict['OPTIONS']` and in PostgreSQL. This preserves the frozen migrations and makes the prerequisite explicit in deployment configuration.

## Evidence and limits

Retry 10 demonstrated the missing-role failure before bootstrap, 24 matching roles afterward, successful `foundation.0001`, all 92 ISO Smart migrations, and zero pending migrations. The final catalog audit found 50 protected tables and 250 RLS policies; runtime LOGIN roles owned none of the protected tables. The isolated Retry 10 containers inherited Retry 9's loopback-only `trust` host authentication, so this run verifies role identity and database privileges but is not evidence of password-enforced network authentication. A future production deployment must use its normal authenticated PostgreSQL connection policy.

The native V2.5 run remains blocked at `INITIAL_OPPORTUNITY` by the mismatch between the frozen Process reference and the fresh native Process ID. The bootstrap decision does not alter V2.5 bindings or Stage EXT.
