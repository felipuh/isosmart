# ISO SMART AI — Phase31.5 E-07 AdminApps Development Runtime Bootstrap

Date: 2026-10-05 (America/Costa_Rica)  
Scope: local AdminApps development runtime bootstrap assessment only.

## A. Governance Integrity

Evidence 39 at commit `644258c9` was verified as the predecessor. AdminApps is at `8b9c5684997baaa590b34af241a173e1a9c41143` on `hardening/p0-p1-enterprise-readiness`; ISO Smart remains on the same branch. Existing unrelated working-tree changes in both repositories were preserved. This slice did not access staging or production.

## B. Starting State

The effective AdminApps profile was derived without disclosing environment values: `development`, `IS_DEVELOPMENT = true`, and `IS_PRODUCTION = false`. Evidence 39's starting gate state was confirmed: `D2 = DEV_DATABASE_UNAVAILABLE`, `D3 = DEV_DATABASE_UNAVAILABLE`, `D4 = DEV_DATABASE_UNAVAILABLE`, and `Phase31.5 = EXECUTION_HELD`.

## C. Python Runtime Contract

`PYTHON_RUNTIME_CONTRACT_BOUND`.

The active controlled-local documentation uses `backend/.venv312/bin/python`. The existing ignored venv at `adminapps/backend/.venv312` identifies CPython 3.12.13 and provides Django 4.2.22, matching `Django==4.2.22` in `backend/requirements.txt`. A historical README references Python 3.9 and `venv_admin`; that legacy instruction was not used to choose a runtime. No venv was created or changed.

## D. Dependency Reproducibility

`DEPENDENCIES_SUFFICIENTLY_PINNED`.

`backend/requirements.txt` is the dependency source. Every declared direct package has an exact version; there is no separate resolver/hash lock file. This is sufficiently deterministic to reuse the existing matching local venv without inventing package selections. No packages were installed. The venv does not include `pip`, so `pip check` was unavailable; Django itself imported at 4.2.22.

## E. Python Development Runtime

`PYTHON_VENV_PATH = /home/felipe/proyectos/adminapps/backend/.venv312`  
`PYTHON_VERSION = 3.12.13`  
`DJANGO_VERSION = 4.2.22`  
`DEPENDENCY_INSTALL_SOURCE = NOT_APPLICABLE (existing venv reused; no installation)`

The local Python/Django runtime was usable for safe development checks. No global Python, dependency manifest, source file, or settings file was changed.

## F. PostgreSQL Runtime Contract

`POSTGRES_VERSION_CONTRACT_UNRESOLVED`.

The checked-out AdminApps sources establish PostgreSQL as the database engine and pin `psycopg2-binary==2.9.10`, but define neither a PostgreSQL major version nor a compatibility interval. They also contain no PostgreSQL image tag, Compose service, project-scoped container definition, or local-start contract. Selecting a version or image would invent a material input, so provisioning stopped under `REPRODUCIBLE_OR_STOP`.

## G. Database Isolation Assessment

The non-secret development endpoint remains `127.0.0.1:5432`, database name `adminapps_db`. A narrow PostgreSQL readiness probe returned no response, preserving `DEV_DB_CONNECTION_REFUSED`. Direct listener inventory was unavailable in the restricted environment, so port 5432 is not affirmatively established as unused. No existing reachable `adminapps_db` was found; no ownership of any possible endpoint process was assumed.

## H. PostgreSQL Bootstrap Action

No PostgreSQL runtime was created or started. No Podman container, image, volume, or service was selected or reused. `ADMINAPPS-DEV-LOCAL-POSTGRES` was not created, because its required PostgreSQL version is not repository-bound. No privilege escalation occurred.

## I. Database Creation Result

No database was created. No existing database was overwritten, dropped, reset, initialized, imported, or seeded. No development database credential was generated, read, printed, or stored.

## J. Migration Bootstrap

The migration plan and migration chain were not executed because no authorized, isolated, contract-bound development database exists. Source inspection confirms that `integration.0006_integration_api_key_lifecycle` is present, but its applied state remains unverified. No schema was patched and no migration ledger was modified.

## K. Django Development Verification

`DJANGO_SYSTEM_CHECK_PASS`.

Running the safe bounded check with `DJANGO_ENV=development` reported no issues (0 silenced). `showmigrations integration` was not run because it would require the unreachable PostgreSQL database; this slice does not manufacture a database merely to make the Python check pass.

## L. D2 — Runtime Readiness

`D2 = DEV_DATABASE_UNAVAILABLE`.

The Python runtime, migration source, lifecycle implementation, and rotation command source are present, but the required PostgreSQL runtime has neither a repository-bound version nor a reachable database. Schema presence, migration `0006`, and revision/schema compatibility cannot be authenticated.

## M. D3 — Integration Target Metadata

`D3 = DEV_DATABASE_UNAVAILABLE`.

No integration metadata was queried and no integration record was created. Key values, verifiers, hashes, and credentials were not selected or inspected.

## N. D4 — Active Staff Operator Metadata

`D4 = DEV_DATABASE_UNAVAILABLE`.

No user metadata was queried and no operator was created or changed. Account, password, MFA, token, session, and recovery information were not accessed.

## O. Preserved D1 / D5–D9 Gates

`D1 = DEV_TARGET_IDENTITY_PASS` and `D7 = DEV_INTERRUPTION_MODEL_DEFINED` are preserved. The independent unresolved gates remain `D5 = DEV_SECRET_RECEIVER_UNRESOLVED`, `D6 = DEV_WEB_WORKLOAD_NOT_RUNNING_OR_UNIDENTIFIED`, `D8 = DEV_FORWARD_RECOVERY_UNRESOLVED`, and `D9 = DEV_SECRET_LEAKAGE_PATHS_UNRESOLVED`.

## P. Development Rotation Eligibility

`DEVELOPMENT_ROTATION_AUTHORIZATION_ELIGIBLE = NO`.

This is expected: D2–D4 remain unavailable and D5, D6, D8, and D9 independently remain unresolved. No rotation was performed.

## Q. Secret Leakage Assurance

No database password, Django secret, API key, token, verifier/hash, authenticated connection string, or full `.env` was printed or persisted. `SECRET_MATERIAL_EXPOSURE_AVOIDED = YES`.

## R. E-08 Preservation

`E-08_BASELINE_PRESERVED = YES`  
`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`

E-08 was not retested or reopened.

## S. Runtime / Database Mutation Audit

No runtime, container, volume, database, schema, migration, fixture, integration, user, credential, ISO Smart receiver, or web workload mutation occurred. Reusing the pre-existing ignored Python venv for inspection was the only runtime interaction.

## T. Repository Mutation Audit

AdminApps product/source code, manifests, migrations, settings, `.env`, and ignored runtime state were not changed. The only intended ISO Smart additions are Evidence 40 and this report. No push occurred.

## U. Runtime Bootstrap Verdict

`POSTGRES_VERSION_CONTRACT_UNRESOLVED`

## V. Remaining Development Blockers

1. No repository-defined PostgreSQL major version or compatibility interval for a project-scoped local runtime.
2. Port 5432 is not affirmatively proven available for a new isolated runtime in the restricted environment.
3. No reachable AdminApps development database, so the migration ledger, ISO Smart integration metadata, and active-staff operator metadata cannot be inspected.
4. `D5`, `D6`, `D8`, and `D9` remain independently unresolved.

## W. Phase31.5 Status

`Phase31.5 = EXECUTION_HELD`

No credential rotation, ISO Smart receiver mutation, web restart, staging/production action, push, or Phase31.5 promotion was performed.
