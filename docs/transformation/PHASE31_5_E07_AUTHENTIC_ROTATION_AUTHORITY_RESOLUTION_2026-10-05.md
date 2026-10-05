# Phase31.5 E-07 Authentic Rotation Authority Resolution

Date: 2026-10-05

Scope: repository-local source and governance inspection only. No authentic
credential, environment value, database, AdminApps runtime, external service,
deployment, restart, or customer workflow was accessed or changed.

## A. Governance Integrity

`Phase31.5 = EXECUTION_HELD`

This document does not authorize credential creation, rotation, transfer,
receiver update, restart, deployment, validation against an authentic service,
or publication. Evidence 28 and the prior final-closure report were inspected
and left unchanged.

## B. Starting Git State

| Repository | Branch | HEAD | Required commit |
|---|---|---|---|
| ISO Smart | `hardening/p0-p1-enterprise-readiness` | `1882596f25d7dcd70ad8a3ce9f285f8075b8c717` | `1882596f` exists locally and is HEAD |

The worktree had 21 pre-existing changed paths. They were preserved. The two
artifacts cited in the mutation audit did not exist at the start.

## C. E-07 Secret Consumer Matrix

The source-defined credential is `ADMIN_APPS_API_KEY`, read into
`ADMIN_APPS_INTEGRATION` by `backend/backend/settings.py` and sent as
`X-API-Key` by `AdminAppsClient`.

| Consumer | Variable/source | Startup dependency | Restart required | Evidence |
|---|---|---|---|---|
| `web` | `.env.production.web` receiver name; Django settings and module singleton | Yes | Yes—recreate/restart web after an authorized receiver update | settings, client, Compose, Dockerfile |
| `outbox-worker` | Distinct worker environment-file name, but no client import/call | No direct API-key consumer; settings can read any supplied variable | No for this secret from source | `run_outbox_worker.py` |
| `foundation-bootstrap`, `migrate` | Separate uninspected environment-file names | No direct client use found | N/A for one-shot jobs | Compose and foundation entry points |
| `check_isosmart_adminapps`, `sync_organizations` | Import the shared client | Yes, when invoked | N/A—each invocation is a fresh process | integration commands |
| Authentication, integration, middleware, QMS organization flows in web | Shared client | Covered by web singleton | Yes, through web restart | repository-local import trace |

Configuration is not dynamically refreshed. `AdminAppsClient` copies the
settings value during construction and the module constructs its singleton at
import time. The repository does not define an authentic restart command:
`RESTART_REQUIREMENT_SOURCE_INSUFFICIENT`.

## D. Secret Injection Authority Matrix

| Contract item | Classification | Repository-local finding |
|---|---|---|
| Authoritative secret source | `PARTIAL` | AdminApps defines the lifecycle; authentic deployment/database is not identified. |
| Authorized changer | `PARTIAL` | An active staff AdminApps operator is required; the actual operator is external. |
| ISO Smart receiver | `PARTIAL` | Compose names web’s environment-file input, not the authentic injector or deployed receiver. |
| Secure transfer | `NOT_DEFINED` | No approved non-recording one-time transfer mechanism is defined. |
| Persistence | `PARTIAL` | AdminApps hashes new credentials; the authentic secret-manager/persistence owner is unspecified. |
| Deployment/restart | `PARTIAL` | Web restart is required, but no authorized operational command is present. |
| Rollback | `PARTIAL` | Database work is transactional before commit; no post-commit receiver rollback or old-key reactivation protocol exists. |
| Audit/evidence | `PARTIAL` | AdminApps has secret-free lifecycle audit events; external injection/restart audit is not defined. |

## E. AdminApps Authority Boundary

The active AdminApps route is `apps.integration`. The source-defined target is
an `IntegrationAPIKey` row, selected for rotation by its database primary key.
The authentic row identity remains:

`AUTHENTIC_ADMINAPPS_TARGET_UNRESOLVED`

The lifecycle service locks the selected active row, creates a new hashed
credential and safe fingerprint, deactivates and links the old row, and writes
a secret-free audit event in one database transaction. It requires an
authenticated, active staff AdminApps operator. The management command accepts
only record and actor identifiers and emits the generated replacement once on
stdout. There is no rotation HTTP endpoint and no source requirement for
direct database mutation.

Migration `integration.0006_integration_api_key_lifecycle` is required for
this model and audit contract, but its application to the authentic authority
was not observed. A configured hash fallback is another acceptance path; its
authentic configuration was not inspected.

## F. Administrator Password Dependency

`ADMIN_PASSWORD_NOT_REQUIRED_FOR_ROTATION`

`INITIAL_ADMIN_PASSWORD` is read solely by ISO Smart’s bootstrap script to
create or update a local initial administrator. The AdminApps rotation service
instead requires an active staff operator object, and the command takes only
record and actor identifiers. Neither reads or validates the initial ISO Smart
administrator password. Thus its applicable source scope is
`ADMIN_PASSWORD_BOOTSTRAP_ONLY`.

ISO Smart has source-defined email-token recovery and authenticated password
management paths, but they are irrelevant to credential rotation. Whether an
authentic bootstrap account was ever materialized remains unobserved. No
password material was read, reconstructed, tested, reset, or recorded.

## G. Restart / Cutover Contract

The following is symbolic and non-executing; angle-bracket values are never
to be placed in an unapproved command, transcript, ticket, log, or artifact.

1. Obtain separate authority for `<authentic-adminapps-target-id>`,
   `<active-staff-operator>`, `<web-secret-receiver>`, the non-recording
   transfer channel, the restart operator, and an interruption policy.
2. Perform authorized metadata-only preflight: migration 0006, active target
   state, and every authentic acceptance path, including the hash fallback.
3. Invoke the source-defined AdminApps rotation operation through the approved
   operator context, transferring `<one-time-replacement>` directly into the
   approved receiver without recording it.
4. Update the authoritative web receiver for `ADMIN_APPS_API_KEY`, then
   recreate/restart web so its settings and client singleton are rebuilt.
5. Under separate authorization, use the narrow AdminApps health contract to
   evidence `<old-credential>` rejection and `<replacement-credential>`
   acceptance. Account for the successful request’s usage-metadata write.
6. Collect the secret-free lifecycle audit event and the external receiver and
   restart evidence.

No authentic command was run.

## H. Dual-Key / Atomicity Assessment

`dual-key/grace-period = NOT_SUPPORTED_BY_SOURCE`

AdminApps rotation is atomic inside its database transaction only. It is not
atomic across AdminApps, the secret receiver, and ISO Smart web. The old key
is revoked as the replacement becomes active, before the generated
replacement can be injected and web restarted. A bounded authentication
interruption is therefore possible. A future authorization must explicitly
accept that interruption and define forward recovery; source provides neither
post-commit receiver rollback nor old-key reactivation. This is a documented
cutover constraint, not a repository-local rotation design defect by itself.

## I. External Dependencies

1. Authentic AdminApps deployment/database identity and migration-0006 proof.
2. Authorized metadata-only selection of the target key record.
3. Authorized active staff operator identity.
4. Secret receiver, non-recording handoff, and persistence owner.
5. Web restart/recreate operator and environment-specific procedure.
6. Acceptance-path/fallback verification and service-interruption approval.

## J. Tests and Validation

`backend/.venv/bin/python manage.py test apps.integration.tests.SecureIntegrationAPIKeyLifecycleTests --verbosity 1` completed successfully with exit status 0 in the local AdminApps checkout. It uses a synthetic Django test database and validates the lifecycle transaction, revocation, fallback rejection behavior, secret-free audit event, read-only admin, and one-time command semantics.

No authentic infrastructure was contacted.

## K. Repository Mutation Audit

No product/runtime code, environment file, credential, database, deployment,
or external system changed. The only task-owned additions are:

- `docs/governance/evidence/phase31_5/29_e07_authentic_rotation_authority_resolution_2026-10-05.json`
- `docs/transformation/PHASE31_5_E07_AUTHENTIC_ROTATION_AUTHORITY_RESOLUTION_2026-10-05.md`

Unrelated existing worktree changes were preserved.

## L. E-07 Readiness Verdict

`BLOCKED_BY_EXTERNAL_AUTHORITY`

Repository-local source is now sufficient to identify the consumer contract,
rotation mechanism, required operator role class, administrator-password
non-dependency, audit capability, and cutover limitation. It cannot name or
authorize the authentic target/operator, secret receiver, safe handoff,
restart, fallback verification, or service-interruption acceptance. A future
separately authorized rotation is therefore not yet deterministic and auditable.

## M. Phase31.5 Status

`Phase31.5 = EXECUTION_HELD`

`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`

Evidence: `docs/governance/evidence/phase31_5/29_e07_authentic_rotation_authority_resolution_2026-10-05.json`.
