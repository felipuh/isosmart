# LAB05-C1-R2: isolated authentication schema

Requires PostgreSQL `initdb`/`pg_ctl` on PATH and Python 3.12. Run as an
unprivileged OS user. No existing database, role, connection URL or env file is
accepted. The runner creates and removes its own `/tmp/iso-c1-r2-*` cluster.

```sh
python3.12 -m venv /tmp/iso-r2-venv
/tmp/iso-r2-venv/bin/pip install -r backend/lab05_c1_r2/requirements.txt
/tmp/iso-r2-venv/bin/python backend/lab05_c1_r2/run.py --evidence /tmp/iso-r2-result.json
```

The executable creates a new database, projects explicitly selected **real**
Django models with `schema_editor`, checks the authentication URLs/models, and
runs ORM/SQL acceptance through two SCRAM-authenticated, non-owner principals.
It does not invoke migrate, MigrationExecutor or MigrationRecorder. The normal
settings and migration graph are unchanged; this database is **not migratable
production state** and must never be upgraded or reused as a normal database.

`evidence.json` contains the actual MigrationLoader plan/edges; table columns,
indexes, FK/unique/check definitions, sequences, policies and SQL grants; and
positive/negative acceptance results. Failure aborts acceptance and cleanup
still runs. Keep assertions enabled (optimized Python is rejected).

Tenant authority is fixed by database `session_user` in this lab. There is no
application SET ROLE or tenant-GUC trust. Runtime A/B are a lab-specific topology,
not an implementation of HTTP tenant routing. No network calls are permitted.

User identities are global, as are the Django authorization catalogs (the latter
have no runtime grants). Organizations, profiles and audit rows have forced RLS.
Reset/blacklist records are user-scoped by the real models: membership gates
visibility; a user shared by tenants has user-wide reset/revocation state. This
is not evidence of tenant-specific token ownership. General user administration,
ORM cascade deletion, groups/permissions, sessions, foundation workflows and
HTTP authentication are outside this acceptance.
