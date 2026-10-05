# Phase31.5 E-07 Source-Artifact Conformance & External Authority Binding

Date: 2026-10-05 (America/Costa_Rica)
Scope: repository-local source/governance conformance analysis only. No authentic metadata was collected.

## A. Governance Integrity

The governing precedence is `SOURCE_ARTIFACTS → APPROVED TRANSFORMATION / GOVERNANCE PLAN → FROZEN IMPLEMENTATION EVIDENCE → OPERATIONAL / EXTERNAL AUTHORITY DECISIONS`. The source package is `10/10 VALID`; the source reconciliation defines the DOCX as primary product authority, the XLSX/JSON maps as structured authority, and DDL/OpenAPI as non-final implementation references. Pre-existing unrelated working-tree changes were preserved.

## B. Starting State

Repository: `/home/felipe/proyectos/isosmart`; branch: `hardening/p0-p1-enterprise-readiness`. Evidence 28–32 exist. Evidence 31 says `EXTERNAL_AUTHORITY_PACKAGE_COMPLETE`; Evidence 32 says `NO_SUPPLIED_EXTERNAL_EVIDENCE` and `BLOCKED_BY_EXTERNAL_AUTHORITY`.

`E-07 = BLOCKED_BY_EXTERNAL_AUTHORITY`

`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`

`Phase31.5 = EXECUTION_HELD`

## C. Relevant Source-Artifact Baseline

| Artifact | Authority/relevance | Exact reference | Interpretation? |
|---|---|---|---|
| `ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx` | Primary product authority for provenance, security, integrations, audit, and tenancy | §§10, 11, 14 | Yes |
| `ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx` + `ISO_SMART_AI_Mapa_Maestro_Datos.json` | Structured entity/event/onboarding authority | DB_Entities, Event_Catalog, Onboarding | Yes |
| `ISO_SMART_AI_Arquitectura_Completa.mmd` | Architectural representation of secure verification, tenant provisioning, MFA/RBAC, and human gates | lines 33–43 | No |
| `ISO_SMART_AI_DDL_PostgreSQL.sql` | Initial data-model reference only | lines 1–28 | No |
| `ISO_SMART_AI_OpenAPI.yaml` | Initial illustrative API contract only | `/v1/evidence` | No |
| Network CSVs, LEEME, manifest | Architectural catalog and package integrity inputs, not credential authority | source package | No |

The authoritative subset requires tenant isolation, MFA/RBAC, rotation of sessions/tokens, immutable/auditable evidence, authorized integration ingress, cryptographic webhook verification, and no cross-tenant API disclosure. It contains no reference to AdminApps, `IntegrationAPIKey`, `ADMIN_APPS_API_KEY`, a concrete secret receiver, or a deployment restart procedure.

## D. E-07 Provenance Matrix

| Concept | Classification | Binding |
|---|---|---|
| AdminApps identity/tenant authority | `GOVERNANCE_DEFINED` | Reconciliation’s Smart3AI system-of-record specialization; source does not name AdminApps. |
| `IntegrationAPIKey`; `rotate_integration_api_key`; migration `integration.0006_integration_api_key_lifecycle` | `IMPLEMENTATION_DEFINED` | Frozen Evidence 29 local implementation findings. |
| `ADMIN_APPS_API_KEY`; `web` consumer; process-lifetime loading; reload requirement | `IMPLEMENTATION_DEFINED` | ISO Smart settings/client/Compose topology. |
| Active staff operator role | `IMPLEMENTATION_DEFINED` | Required by the local lifecycle; actual identity is external. |
| Authentic target identity; real receiver/injector; deployment/restart owner | `EXTERNAL_AUTHORITY_REQUIRED` | These are live operational facts that source/repository cannot supply. |
| Non-recording handoff; interruption approval; leakage controls; forward recovery rule | `GOVERNANCE_DEFINED` | Safety constraints that do not add product behavior. |
| No dual-key grace and non-atomic cross-system cutover | `IMPLEMENTATION_DEFINED` | Frozen lifecycle/consumer consequence. |

## E. Governance Non-Expansion Assessment

`GOVERNANCE_EXPANSION_DETECTED = NO`

The receiver, operator, direct non-recording handoff, restart, interruption, R1/R2/R3 decision model, and leakage rules constrain a risky implementation operation. They are not represented as new source-defined ISO Smart functionality. The exact procedure, actual identities, and deployed target remain external decisions.

## F. AdminApps Authority Binding

Source requires tenant/identity security and auditable integration boundaries; it does **not** source-define AdminApps. The reconciliation’s AdminApps system-of-record specialization is a compatible governance binding for global identity, tenant, entitlement, billing, and provisioning. Credential lifecycle ownership (`IntegrationAPIKey`) and rotation are implementation mechanisms for that boundary, not source-defined product semantics. The authentic target is `EXTERNAL_AUTHORITY_REQUIRED`.

## G. ISO Smart Boundary Binding

ISO Smart is source-bound to tenant safety, auditable actions/evidence, and secure integration behavior. `ADMIN_APPS_API_KEY`, `web`, process-lifetime configuration loading, and restart/recreation are implementation/deployment consequences. Narrow health/authentication validation is a governance control; it must not become customer-workflow execution.

## H. External Authority Dependency Adjudication

| Evidence 32 blocker | Adjudication |
|---|---|
| Authentic AdminApps target | `VALID_EXTERNAL_AUTHORITY_DEPENDENCY` |
| Runtime/migration proof | `VALID_EXTERNAL_AUTHORITY_DEPENDENCY` |
| Active staff operator | `VALID_EXTERNAL_AUTHORITY_DEPENDENCY` |
| Secret receiver/injector | `VALID_EXTERNAL_AUTHORITY_DEPENDENCY` |
| Web deployment/restart authority | `VALID_EXTERNAL_AUTHORITY_DEPENDENCY` |
| Interruption approval | `VALID_EXTERNAL_AUTHORITY_DEPENDENCY` |
| Forward-recovery decision | `VALID_EXTERNAL_AUTHORITY_DEPENDENCY` |
| Leakage-prevention controls | `VALID_EXTERNAL_AUTHORITY_DEPENDENCY` |

None is used to conceal a missing source-required product capability.

## I. Authorized Future Metadata Scope

For a separately authorized future stage only, collect minimum non-secret metadata: target environment ID/class; logical ISO Smart integration attribution; key record ID, active state, duplicate disposition; applied migration/revision and lifecycle availability; operator role/status/approval reference; receiver category/injector/control attestation; web workload mapping and restart-authority reference; interruption-window/abort/escalation references; forward-recovery decision reference; and leakage-control/stop-escalation attestation. Evidence 33 contains the per-field justification, authority, and secret classification.

## J. Explicitly Prohibited Collection

Current/future API-key values; passwords; MFA values; tokens; private keys; secret-bearing hashes/verifiers; full environment files; secret-store contents; database dumps; unrelated tenant/customer/integration/user records; broad identity or secret-store enumeration; and replayable secret-bearing command, log, shell, CI, capture, or transcript output are prohibited.

## K. Source / Governance Contradiction Assessment

`NO_MATERIAL_CONTRADICTION`

AdminApps and the lifecycle mechanism are not relabeled source-defined. The proposed metadata stage only identifies external facts necessary to constrain later use of existing implementation behavior.

## L. Authentic Access Audit

`AUTHENTIC_SYSTEMS_INSPECTED = NONE`

## M. E-08 Preservation

`E-08_BASELINE_PRESERVED = YES`

`E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE`

E-08 was neither retested nor reopened.

## N. Repository Mutation Audit

Only this report and Evidence 33 were created. Evidence 28–32, source artifacts, runtime code, migrations, authentication, deployment, and environment files were not changed. Unrelated worktree changes were preserved.

## O. Source-Artifact Conformance Verdict

`SOURCE_ARTIFACT_CONFORMANCE = PASS`

## P. Next-Stage Eligibility Verdict

`AUTHORIZED_NON_SECRET_METADATA_COLLECTION_ELIGIBLE`

This is eligibility to define a separately authorized, field-bounded, non-secret metadata collection stage. It is not collection or execution authority.

## Q. Remaining Blockers

`NONE FOR STAGE DEFINITION — authentic metadata collection still requires separate explicit authorization.`

## R. Phase31.5 Status

`Phase31.5 = EXECUTION_HELD`

No authentic metadata collection, credential rotation, deployment mutation, or Phase31.5 promotion is authorized by this slice.
