# October 2026 — Onboarding batch 3 implementation traceability

Date: 2026-10-05 (America/Costa_Rica)

This is a product-development traceability record. It does not reopen Evidence
28–40, E-07, E-08, or the Phase31.5 execution hold.

## Frozen boundary and integration baseline

- `E-07 = BLOCKED_BY_EXTERNAL_AUTHORITY / OPERATIONAL_READINESS` remains frozen.
- `E-08 = CLOSED_LOCAL_TECHNICAL_EVIDENCE` remains frozen.
- `Phase31.5 = EXECUTION_HELD`, with `PHASE31_5_HOLD_SCOPE = PHASE31_5_ONLY`.
- Parallel repository-local product implementation remains permitted.
- `ADMINAPPS_BASIC_INTEGRATION_STATUS = PREVIOUSLY_PROVEN_IN_CONTROLLED_ENVIRONMENT`.

The historical controlled evidence for ISO Smart ↔ AdminApps authentication,
entitlement allow/deny behavior, and fail-closed operation remains distinct from
the pending authentic credential-rotation/runtime validation. The latter is not
used to block ordinary AdminApps-consumer work.

## Batch 3 source traceability

| Requirement | Source artifact and exact reference | Authority | Source-defined behavior | Current disposition |
|---|---|---|---|---|
| `REQ-ONBOARDING-07` | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, `onboarding[7]`, **Tenant Provisioning** | `SOURCE_DEFINED` plus approved AdminApps reconciliation | Create tenant, organization, spaces, keys, roles, and policies. | `PARTIAL`: ISO Smart's existing signed-principal resolver requires an active, complete, in-sync tenant projection before tenant-owned operations. Provisioning and its external authorities remain AdminApps-owned; the source does not define an ISO Smart local provisioning command or UI that can safely recreate them. |
| `REQ-ONBOARDING-08` | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, `onboarding[8]`, **Security Setup** | `SOURCE_DEFINED` plus approved AdminApps reconciliation | MFA, admin principal, RBAC/RLS, terms and privacy acceptance. | `PARTIAL`: ISO Smart retains tenant/RLS enforcement and consumes signed AdminApps identity/projection material. It does not create a competing MFA, terms, or privacy-acceptance authority. Source/governance supplies no local acceptance or status contract for the missing UI/action. Authentic external validation remains pending separately. |
| `REQ-ONBOARDING-10` | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, `onboarding[10]`, **Organizational Profile** | `SOURCE_DEFINED`; browser transport is `IMPLEMENTATION_DEFINED_WITHIN_SOURCE_CONSTRAINTS` | Role, expertise, size, sites, country, industry/manufacture-service, and current certification. | Executable and advanced: the browser now loads a server-published canonical organization, validates the source-listed form fields, uses the canonical tenant API with an idempotency event ID, reloads server state, and displays the saved confirmation. |

## Step 7 and 8 boundary

`STEP_07_SOURCE_BEHAVIOR` is tenant provisioning. Its ISO Smart responsibility
is to reject tenant-owned work until the AdminApps projection is active,
provisioned, and reconciled; this is already enforced by
`resolve_source_artifact_principal`. No local duplicate of tenant, keys, roles,
or policies was added.

`STEP_08_SOURCE_BEHAVIOR` is MFA/admin-principal/RBAC-RLS/terms/privacy
security setup. MFA and global identity remain AdminApps authority. Tenant RLS
and signed principal enforcement remain local protections. No source-backed
contract identifies local authoritative records or a UI action for terms/privacy,
so a new acceptance workflow was not fabricated.

## Step 10 browser journey

1. The authenticated user loads `/v1/onboarding/status` and
   `/v1/onboarding/organizations`.
2. The screen exposes only canonical organizations published for the resolved
   tenant; it never reuses a legacy/AdminApps organization identifier.
3. The user enters the source-listed organizational profile fields.
4. Client validation requires the server-required profile shape before submit;
   the API remains the final validator.
5. The client posts `/v1/onboarding/organizational-profile` with a stable
   per-screen UUID event ID and then reloads server progress.
6. The existing domain command applies tenant/RLS checks, workflow transition,
   provenance hash, immutable transition record, and event effects. The browser
   displays the persisted confirmation.

The browser blocks the submit when the server reports the profile step as
locked, and explains that it cannot replace AdminApps provisioning or security
confirmation. This protects the existing source-defined progression rather than
hard-coding a client transition.

## Tests

- Frontend lint and production build cover the updated UI bundle.
- The Playwright `controlled integration` test intercepts the established
  authenticated contracts, asserts the canonical organization UUID and exact
  source-listed profile payload, returns the persisted profile transition, and
  asserts the resulting browser progression. It is intentionally labelled a
  controlled integration test, not authentic AdminApps runtime evidence.
- Existing PostgreSQL integration coverage for the same command remains in
  `backend/foundation/test_source_artifact_postgres_integration.py::test_organizational_profile_is_validated_persisted_and_replay_safe`; it exercises real domain persistence, tenant isolation, provenance, transition, replay, and cross-tenant rejection.
