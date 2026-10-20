# AdminApps AI Financial Authority Contract V1.1

**Status:** `ADMINAPPS_AI_FINANCIAL_CONTRACT_V1_1_READY_FOR_HUMAN_APPROVAL` — a technical recommendation only. This is a proposed contract, not an implementation or an operating authorization.

## 1. Scope, authority, and retained gates

AdminApps is the sole central authority for admission, centrally governed budgets, tariff selection, reservations, settlement, liability, financial reconciliation, and financial audit. ISO Smart is the authenticated producer, local QMS executor, provider-dispatch boundary, and usage-evidence producer. `AIUsageProjection` is observational and never authorizes, prices, reserves, settles, or releases funds.

This contract supersedes V1 only as a proposal; V1 remains historical evidence. It creates no endpoint, role, credential, table, migration, provider call, transaction, deployment, or authority.

The following gates remain independently closed:

* `REAL_OPENAI_INFERENCE = NOT_AUTHORIZED`
* `PRODUCTION_DELIVERY = NOT_AUTHORIZED`; `DEPLOYMENT = NOT_AUTHORIZED`; `GIT_PUSH = NOT_AUTHORIZED`; `CREDENTIAL_ROTATION = NOT_AUTHORIZED`
* `PHASE31_5 = EXECUTION_HELD`
* exact provider/model approval, effective source-linked verified tariff, approved rounding/billing semantics, defensible exact-model input-token upper bound, and separate operating authorization.

`max_tokens=2000` constrains output only. V1.1 does not solve or waive the input-token bound.

## 2. Source-grounded control plane

| Existing source | Authority retained in V1.1 |
| --- | --- |
| `organizations.Organization` | canonical AdminApps tenant UUID and active status |
| `products.ProductSystem` | canonical product registry and status |
| `OrganizationProductEntitlement` | live organization-product access decision |
| `subscriptions.Subscription` | commercial input to entitlement; not a ledger |
| `integration.IntegrationAPIKey` and lifecycle audit | existing service-credential verifier/lifecycle foundation |
| ISO Smart `TenantProjection` | local, immutable mapping of local tenant to `adminapps_tenant_id`; never financial authority |
| `integration.AIUsageProjection` | idempotent administrative observation only |

AdminApps must independently load `Organization`, `ProductSystem`, `OrganizationProductEntitlement`, and its own future financial records inside admission. An arbitrary request UUID, end-user claim, ISO Smart local organization ID, or dashboard value is not authorization.

## 3. ProducerRegistration and selected V1.1 authentication

### 3.1 Authoritative registration

`ProducerRegistration` is a future AdminApps-owned immutable-registration record. Its immutable `producer_registration_id` is the producer identity used in all financial records and idempotency keys. A registration contains: `producer_code` (for example `ISO_SMART`), bound `credential_id`/credential fingerprint, `environment` (`controlled_test`, `staging`, or `production`), permitted product IDs, permitted operations (`admit_reserve`, `settle`, `status_read`, optionally `submit_evidence`), lifecycle state, creation/revocation evidence, and audit owner.

Permitted lifecycle states are `pending`, `active`, `suspended`, `revoked`, and `retired`. Only `active` registrations may operate. Revocation/suspension takes effect before any admission or settlement authorization; existing reservations remain recoverable only through their recorded ownership and a permitted reconciliation path. Registration and credential history are append-only financial audit evidence. A registration is separate from ordinary integration credentials, customer credentials, and user sessions.

### 3.2 Chosen mechanism

**V1.1 chooses a dedicated AdminApps `IntegrationAPIKey`-backed financial service credential over TLS, bound one-to-one to `ProducerRegistration`.** It uses the existing hashed credential format, credential ID/fingerprint, active/revoked/rotated lifecycle, and secret-free lifecycle audit as implementation foundations. The credential must be named/scoped exclusively for the financial producer and may not be a legacy plaintext credential or a general-purpose integration key.

This is authenticated producer-to-server application authentication; it is **not mutual TLS** and the contract makes no mTLS claim. A future workload-identity/mTLS mechanism requires a new approved credential contract and registration migration. A generic API-key fallback is forbidden: a credential with no active matching financial registration has no financial authority.

## 4. Trusted tenant assertion

ISO Smart may form `tenant_assertion` only after the authenticated execution is bound to one local `TenantProjection` with: immutable `adminapps_tenant_id`; `lifecycle_status=active`; `provisioning_status=complete`; `reconciliation_status=in_sync`; non-null source version/event; and current reconciliation evidence. It sends:

```json
{
  "adminapps_tenant_id": "uuid",
  "tenant_projection_id": "uuid",
  "tenant_projection_source_version": 42,
  "tenant_projection_source_event_id": "uuid"
}
```

The canonical tenant assertion is the AdminApps UUID, but it is merely a claim with projection evidence. ISO Smart binds it to its trusted server-side identity/context, never to a user-supplied body field or claim. Missing, inactive, stale, incomplete, conflicting, unknown, or authority-unavailable projections fail closed before paid dispatch (`TENANT_PROJECTION_UNTRUSTED`).

AdminApps validates: authenticated registration permits the product/environment/operation; the organization UUID exists and is active; its product entitlement currently allows access; and the assertion is structurally valid. The V1.1 request records projection evidence for audit, but AdminApps does not trust the projection as a replacement for its authoritative identity/authorization data. A mismatch, duplicate/conflicting assertion, or tenant no longer eligible is denied without cross-tenant disclosure.

## 5. Budget, tariff, and concurrency semantics

### 5.1 Scope and exposure

Every admission evaluates the global tenant scope and tenant-product scope where active; future scopes are permitted only when explicitly approved and assigned a canonical `scope_type` rank. The current rank is `tenant_global` then `tenant_product`; ties sort by immutable scope UUID. This exact `(scope_rank, scope_id)` order is the required lock order for **all** admission and reconciliation paths.

A budget policy is versioned and identifies currency (ISO 4217), period boundary/timezone, amount precision, rounding rule, count limits, allowed provider/model, and effective state. Monetary amounts use PostgreSQL `numeric(20,10)` and server-side decimal arithmetic; no binary float. V1.1 does not introduce FX: all applicable policies and verified tariff must share a currency, otherwise admission is denied `FX_POLICY_REQUIRED`.

For each scope and period, the authority maintains: limit; `reserved_exposure`; `settled_exposure`; `unresolved_exposure`; and liabilities from validated overage. Available exposure is limit minus all active reserved, unresolved, settled-to-period exposure, and approved liability as specified by policy. An unresolved outcome retains its original worst-case reservation. A validated actual amount above reservation creates explicit `overage_liability`; it is never silently clipped or funded by an unrelated product.

Periods use an approved, versioned calendar and explicit rollover rule. At period close, open/unresolved exposure remains linked to its originating period until settlement/resolution; it does not disappear through rollover. Carry-forward, expiry, or credit treatment requires an approved policy version and an append-only event.

### 5.2 Atomic reservation

Admission runs in one AdminApps PostgreSQL transaction under `SERIALIZABLE` isolation, with retry of serialization failures using the same idempotency identity. It locks the idempotency record and all applicable budget rows in the canonical order; rechecks producer, tenant, entitlement, policy, tariff, bounds and periods; calculates maximum exposure server-side; checks every scope; then persists one decision, reservation, budget movements, and audit event before commit. Equivalent explicit row-locking is acceptable only if tests prove the same invariant. A failed/unknown transaction grants nothing. No product may allocate centrally governed funds independently.

## 6. Immutable idempotency and records

Admission identity is immutable:

`(producer_registration_id, organization_id, product_id, invocation_id)`.

The producer supplies a stable opaque `invocation_id` and `material_request_hash`, calculated from canonical JSON of all financially material request fields: schema version, tenant assertion, product, provider/model, requested bounded units, request class, and applicable producer-declared evidence IDs. The server recomputes and stores the canonical hash. A unique constraint covers the full identity. Same identity/hash returns the original immutable decision; a different hash returns `IDEMPOTENCY_CONFLICT`; concurrent duplicates result in exactly one persisted decision/reservation.

Settlement identity is `(reservation_id, settlement_id)` with a canonical `settlement_payload_hash`, unique constraint, and transaction that locks the reservation plus relevant budgets. Identical replay returns the original outcome without another financial effect. A changed payload for the same identity is `IDEMPOTENCY_CONFLICT`.

Financial decisions, settlement evidence, financial audit events, and manual-resolution history are append-only. Reservation/accounting state may change only through governed transitions accompanied by immutable events; it is not itself historical evidence replacement.

## 7. Evidence, settlement, and reconciliation

Each evidence item has immutable `evidence_id`, producer registration, reservation/invocation correlation, provider request ID when known, capture time, source owner, payload hash, and retention classification. Raw prompts, completions, provider keys, and credential secrets are excluded. `AIUsageProjection` may be linked by `source`, `usage_event_id`, `usage_record_id`, and `correlation_id`; it remains corroborating observation, not authority.

| Class | Minimum admissible evidence / source owner | Financial consequence |
| --- | --- | --- |
| A. proven non-dispatch | ISO Smart durable pre-dispatch failure/outbox evidence proving no provider request was issued; correlation and attempted-dispatch state | authorized release only after validation |
| B. successful execution, verified usage | provider request ID plus provider usage metadata, ISO Smart signed/durable delivery record, applicable verified tariff | server-priced settlement; release proven difference only |
| C. partial execution, verified usage | same as B with a partial/outcome classification and bounded verified usage | settle verified amount; release proven unused difference only |
| D. timeout/uncertain consumption | durable timeout/connection-loss evidence and correlation; absence of usage is not proof | `unresolved`; retain full reserved exposure |
| E. missing provider usage | dispatch evidence with absent/incomplete provider metadata | `unresolved`; retain exposure |
| F. actual exposure above reservation | verified usage and effective tariff demonstrating excess | settle reserved amount plus append explicit `overage_liability`; no silent release |

No elapsed time releases funds. Manual resolution requires `financial.reconcile`, a reason, referenced immutable evidence, before/after state and amounts, dual-control policy where configured, and an immutable audit event. It can release only class-A-equivalent proof; otherwise it settles, retains unresolved exposure, or records liability.

## 8. PostgreSQL protection, RLS, and roles

Future AdminApps schema must enforce append-only behavior in PostgreSQL, not application convention. Dedicated migration owner, runtime authority role, read-only financial-audit role, and narrowly scoped reconciliation role must be separate NOINHERIT roles; runtime roles must not be table owners, superusers, or `BYPASSRLS`.

Runtime authority receives only required `SELECT`/`INSERT` on immutable decision/evidence/audit/history tables. `UPDATE`, `DELETE`, `TRUNCATE`, and ownership alteration are forbidden to runtime and reconciliation roles. Database triggers reject update/delete for immutable tables; RLS is `ENABLE` + `FORCE`, with tenant predicates and a separate centrally governed admin/auditor policy. Controlled transition procedures may update only mutable reservation/accounting rows and must insert the related immutable event in the same transaction. Direct writes bypassing procedures are denied.

Migration owner access is for reviewed migration windows only; break-glass/recovery requires explicit governance approval, an immutable recovery record, post-action review, and no ordinary runtime grant. Migration exceptions never authorize retroactive silent alteration of financial evidence. Tests must prove RLS A/B isolation, no-context denial, runtime inability to update/delete/forge audit, and role separation.

## 9. Financial RBAC and separation of duties

Introduce an AdminApps central permission family, separate from `IsAdmin`, `IsOrgAdmin`, generic users, and producer identities:

| Permission | Authority |
| --- | --- |
| `financial.policy.admin` | create/activate/supersede budget policies |
| `financial.tariff.approve` | approve effective, source-linked tariffs |
| `financial.reconcile` | restricted evidence-backed reservation resolution |
| `financial.audit.read` | central financial decision/evidence/audit access |
| `financial.admin` | assign the above central roles, subject to governance |

Customer users and organization admins have none of these rights. A producer may call only registered internal operations and cannot administer policy, tariff, evidence resolution, or audit. Separation of duties requires a financial administrator distinct from the actor approving a tariff or originating a manual reconciliation where staffing permits; exceptional overlap needs explicit reason and audit. Every privileged read/write is audited with actor, permission, tenant scope, correlation ID, and result.

## 10. Versioned internal HTTP contract (proposal only)

Base path: `/api/integration/ai-financial/v1`. TLS is mandatory. All routes require the dedicated registered producer credential except restricted resolution, which requires an authenticated human/service principal with `financial.reconcile`; no route accepts generic integration credentials as authority.

Common request header: `X-Correlation-ID` (UUID, generated by producer and echoed); `Idempotency-Key` is the relevant immutable invocation/settlement ID. Common error envelope:

```json
{"schema_version":1,"code":"IDEMPOTENCY_CONFLICT","message":"safe non-sensitive summary","correlation_id":"uuid","retryable":false,"decision_id":"uuid-or-null"}
```

### 10.1 Admission and reservation

`POST /admission-decisions`

Required body: `schema_version`, `invocation_id`, `material_request_hash`, `tenant_assertion`, `product_id`, `provider`, `model_identifier`, bounded `max_input_tokens`, bounded `max_output_tokens`, `request_class`, and `correlation_id`. Server-authoritative fields are producer registration, organization/entitlement truth, policy/tariff versions, currency, budget period, calculated amount, decision/reservation IDs, and timestamps. Client price/currency/amount/policy/tariff fields are rejected.

`201` creates reserved decision; `200` returns same decision for exact replay; `401`, `403`, `409`, `422`, `429`, and `503` use the common envelope. Success returns `decision_id`, `reservation_id`, `state`, `policy_version`, `tariff_version`, `currency`, `reserved_amount`, `budget_period`, `correlation_id`, and reconciliation link. Commit precedes success; ISO Smart may dispatch only after a received committed `reserved` result.

### 10.2 Settlement

`POST /reservations/{reservation_id}/settlements`

Required: `settlement_id`, `settlement_payload_hash`, `invocation_id`, outcome/evidence class, immutable evidence references, usage fields if known, provider request ID if known, and correlation ID. Server recomputes pricing and ownership. `201` is a new outcome; `200` exact replay; `409` conflict/invalid transition; `422` invalid evidence; `403` ownership denial; `503` unavailable. Successful commit has one and only one budget effect for the settlement identity.

### 10.3 Status lookup

`GET /admission-decisions/{producer_registration_id}/{organization_id}/{product_id}/{invocation_id}`. The authenticated producer can read only its own identity and permitted tenant/product. Response returns the original immutable decision, reservation state, result IDs, policy/tariff metadata, and correlation IDs; no cross-tenant data. This is the mandatory reconciliation procedure after an ambiguous admission response.

### 10.4 Restricted resolution

`POST /reservations/{reservation_id}/resolutions` requires `financial.reconcile`, `resolution_id`, canonical payload hash, reason, evidence references, requested outcome, and correlation ID. Its idempotency identity is `(reservation_id, resolution_id)`; same/different payload behavior matches settlement. Response includes immutable resolution/audit IDs and resulting accounting state. It cannot bypass permitted transitions or release uncertainty without proven non-dispatch.

### 10.5 Ambiguity protocol

`503`, network timeout, connection loss, and a lost response after server commit are **unknown**, not authorization and not proof of non-execution. The producer must not dispatch/repeat blindly. It first calls status lookup using the original admission identity: `reserved` permits one correlated dispatch; a recorded denial prohibits dispatch; absent decision may be safely retried with the exact original material request; unavailable lookup remains fail-closed. Duplicate delivery is handled by immutable identity/hashes. The same rule applies to settlement: status/replay the same identity; do not create a new settlement ID to escape ambiguity.

## 11. Required verification before activation

Before any operational activation, AdminApps must demonstrate PostgreSQL migration/role/RLS validation, cross-tenant and producer spoofing denial, full applicable-scope concurrency race tests, admission/settlement duplicate and crash/retry tests, evidence-class transitions, immutable-record update/delete/forge denial, privileged RBAC/segregation tests, API schema/error compatibility tests, and ISO Smart integration fault injection. These are prerequisites, not claims of current implementation.

## 12. Human approval decisions still required

1. Approve this dedicated IntegrationAPIKey-backed V1.1 producer mechanism, or explicitly choose a stronger replacement before implementation.
2. Approve policy owner, financial-admin membership/governance, retention, and break-glass controls.
3. Approve exact provider/model, tariff source/effective version, pricing/rounding semantics, and any future FX policy.
4. Approve an exact-model defensible input-token bounding method and worst-case reservation formula.
5. Authorize each implementation slice and, separately, any ISO Smart integration/paid execution operation.

