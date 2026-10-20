# ADMINAPPS AI Financial Authority Contract V1

**Status:** `ADMINAPPS_AI_FINANCIAL_CONTRACT_V1_READY_FOR_APPROVAL` — proposed only; no endpoint, database migration, credential, provider call, or production authority is created by this document.

## 1. Decision and source grounding

AdminApps is the future central authority for AI entitlement and financial
exposure. This follows its existing product-neutral control plane:

| Existing source | Current authority retained | V1 use |
| --- | --- | --- |
| `apps.organizations.Organization` | Canonical global organization/tenant UUID and active status | `authoritative_tenant_id` |
| `apps.products.ProductSystem` | Product registry | canonical product ID/code, including `ISO_SMART` |
| `apps.products.OrganizationProductEntitlement` | Per-organization product access | live entitlement gate, plan/scopes/effective access |
| `apps.subscriptions.Subscription` | Commercial status | an input to entitlement, not a reservation ledger |
| `apps.integration.IntegrationAPIKey` | Service-principal verifier, lifecycle and audit evidence | authenticated producer identity |
| `apps.integration.AIUsageProjection` | Cross-product cost observability | immutable-ish usage projection only; it is **not** a tariff, invoice, entitlement, or reservation authority |
| `apps.billing.AIUsageDashboardView` | Admin-only usage dashboard | read-only operational visibility; no tenant-facing financial decision |

The existing `GET /api/integration/organizations/{organization_id}/products/{product_code}/validate/`
endpoint is an entitlement/access decision, not a financial reservation. It
must not be relabelled as one. ISO Smart's tenant projection continues to map
its local tenant ID to AdminApps' canonical organization UUID; no request body,
JWT claim, or local QMS organization ID may substitute for that mapping.

`PHASE31_5 = EXECUTION_HELD`. `REAL_OPENAI_INFERENCE`, production delivery,
deployment, and provider spending remain unauthorized.

## 2. Authority boundary

AdminApps owns centrally shared budget, approved product/provider/model scope,
verified tariffs, admission, reservation state, settlement, and audited manual
reconciliation. ISO Smart owns local QMS work, trusted mapping from an
authenticated actor to its projected tenant, the provider dispatch boundary,
and usage evidence/outbox delivery. ISO Smart never calculates a final central
authorization from its local policy and never treats a dashboard projection as
permission to spend.

Product-specific limits and centrally shared limits are separate policy scopes
under one reservation transaction. A successful product limit check does not
claim a global cap; only a future AdminApps transaction that locks/evaluates
all applicable central budget rows may make that claim.

## 3. Producer authentication and entitlement decision

### Proposed operation

`POST /api/integration/ai-financial/v1/admission-decisions/`

The route is proposed, not implemented. It requires a mutually authenticated,
allow-listed service principal. Initial compatible authentication may use a
dedicated, active `IntegrationAPIKey` record with a distinct service name,
hashed verifier, revocation/rotation lifecycle, and audit event; an approved
workload identity or mTLS binding may replace it only through a versioned
credential contract. Raw credentials, prompts, completions, and provider keys
are never logged or stored in the financial records.

AdminApps maps the authenticated principal to exactly one producer registration
(`producer_id`, product allowlist, environment, credential state). It rejects a
caller that asserts another producer. ISO Smart proves its identity by that
principal, not by a client-provided `product_id`. It supplies the canonical
AdminApps organization UUID only after resolving the authenticated request to
its own `TenantProjection.adminapps_tenant_id`; AdminApps independently loads
`Organization` and `OrganizationProductEntitlement`. A tenant value supplied
by an end user is neither sufficient nor authoritative.

Required request fields:

```json
{
  "schema_version": 1,
  "invocation_id": "stable producer-scoped opaque id",
  "authoritative_tenant_id": "AdminApps organization UUID",
  "product_id": "ISO_SMART",
  "provider": "approved provider identifier",
  "model_identifier": "approved exact model identifier",
  "max_input_tokens": 0,
  "max_output_tokens": 0,
  "correlation_id": "opaque UUID"
}
```

`invocation_id` is stable across retries and unique per `(producer_id,
authoritative_tenant_id, product_id, invocation_id)`. Token maxima must be
integers and represent enforceable bounds. Client-supplied price, currency,
tariff version, budget period, or reservation amount are ignored/rejected:
AdminApps selects and returns them only after server-side validation.

An allowed response contains `reservation_id`, `reservation_state=reserved`,
`policy_version`, `budget_period`, `verified_tariff_version`, currency,
server-calculated maximum amount, and expiry/recovery metadata. A denial
contains a stable code and correlation ID but no cross-tenant existence or
budget detail. A duplicate, semantically identical request returns the prior
decision; changed material fields return `IDEMPOTENCY_CONFLICT`.

Admission requires all of: valid producer; active organization; product exists
and is in the producer allowlist; live `OrganizationProductEntitlement` allows
the product; allowed provider/model; effective policy; effective verified
tariff with currency/rates/units; supported bounded request; and all applicable
budgets. Missing or unavailable authority fails closed; ISO Smart must not
dispatch a paid provider request after an ambiguous network failure.

## 4. Central atomic reservation

AdminApps persists an append-only audit decision plus mutable reservation
accounting records. The proposed reservation record has immutable identity,
producer, tenant, product, provider/model, request bounds, tariff version,
currency, server-calculated amount, policy/budget-period versions, correlation
ID, timestamps, and state. It does not store prompts, outputs, raw keys, or
unbounded provider metadata.

Within one database transaction, AdminApps:

1. authenticates/authorizes the producer and resolves the canonical tenant;
2. locks the idempotency identity and every applicable shared/product budget
   row in a deterministic order;
3. re-evaluates live entitlement, policy version, effective period, tariff and
   request maxima;
4. calculates/validates exposure server-side, checks counts and held exposure;
5. creates exactly one `reserved` record and immutable decision/audit event;
6. commits before ISO Smart may dispatch.

Serializable isolation or row locks plus retry-on-serialization-failure must
provide the same invariant: concurrent admissions cannot exceed an enforced
budget or duplicate a reservation. A transaction failure returns no admission;
ISO Smart must treat it as denied/unknown and make no provider request.

## 5. Settlement, reconciliation, and lifecycle

Proposed settlement operation: `POST /api/integration/ai-financial/v1/reservations/{reservation_id}/settlements/`.
It is producer-authenticated and accepts the stable invocation, provider request
identifier where available, reported usage metadata, outcome classification,
and correlation ID. AdminApps validates tenant/producer/reservation ownership,
deduplicates the settlement identity, selects/validates the applicable tariff,
and computes actual cost itself. Usage/audit records are immutable evidence;
reservation accounting is a separate lifecycle record.

| State | Permitted next state | Evidence / authority |
| --- | --- | --- |
| `reserved` | `settled` | authenticated matching completion with complete, priced, bounded usage |
| `reserved` | `released` | durable proof that provider dispatch never occurred; automated only with proof |
| `reserved` | `unresolved` | timeout after possible execution, missing/unknown usage, missing verified pricing, inconsistent usage, or recovery ambiguity |
| `settled` | none | duplicate identical settlement is an idempotent read; changed replay conflicts |
| `released` | none | terminal audit record; no silent reuse |
| `unresolved` | `settled` or `released` | authorized reconciliation with new evidence; release requires proof of non-execution |

`unresolved` continues to hold the original worst-case exposure. A TTL may flag
or escalate stale reservations but may not automatically release money where a
billable provider execution could have happened. Partial priced usage settles
the actual server-validated amount and releases only the proven difference.
Unknown/unpriced/missing metadata stays unresolved. Manual reconciliation is a
separate privileged AdminApps action requiring reason, supporting evidence,
actor, before/after amounts and state, timestamp, and immutable audit event.

## 6. Deterministic failure contract

| Condition | Result |
| --- | --- |
| absent/revoked producer credential; unknown producer | `401` / `INVALID_PRODUCER` |
| producer not permitted for product | `403` / `PRODUCER_NOT_ALLOWED` |
| unknown/inactive tenant; entitlement missing/blocked | `403` / specific non-enumerating denial code |
| unsupported provider/model | `403` / `MODEL_NOT_ALLOWED` |
| no effective verified tariff | `409` / `PRICING_UNVERIFIED` |
| invalid maxima or request shape | `422` / `REQUEST_BOUND_INVALID` |
| budget/count exhausted | `409` / `BUDGET_EXHAUSTED` |
| exact duplicate invocation | `200` / prior immutable decision |
| materially conflicting replay | `409` / `IDEMPOTENCY_CONFLICT` |
| stale policy decision | re-evaluate within the lock; deny `STALE_POLICY` if it cannot be validly reissued |
| authority/network/transaction unavailable | `503` or transport failure; ISO Smart fails closed and does not infer authorization |
| repeated settlement | prior result for identical payload; conflict for changed material payload |

HTTP status mapping is proposed and must align with the then-current AdminApps
API error envelope. It must never convert an ambiguous timeout into approval,
release, or provider dispatch permission.

## 7. Security and audit requirements

- Least-privilege producer DB/API identities; no provider credential in
  AdminApps reservation data and no AdminApps authority credential in client
  code.
- Producer allowlisting, tenant/product ownership validation, canonical UUID
  lookup, replay keys, correlation IDs, and request hashes.
- Per-tenant API responses omit other tenants' existence, budgets, policies,
  reservations, and usage. Central dashboard access remains AdminApps RBAC only.
- Administrative policy/tariff/budget/reconciliation writes require existing
  AdminApps privileged RBAC plus a future explicit financial-administrator
  permission; ordinary entitlement UI permission is insufficient.
- Audit authentication decisions, denials, reservations, settlement attempts,
  manual overrides, credential lifecycle events, and policy/tariff versions;
  minimize sensitive metadata and retain no prompts/responses.

## 8. Input-token boundary dependency

ISO Smart's selected `ChatCompletionsValueDiscoveryProvider` sends a fixed
`max_tokens=2000`, which bounds generated output only. Its Chat Completions
payload sends `json.dumps(context)` without a provider-supported preflight
input-token count or a validated request byte/token ceiling tied to the exact
model/tokenizer. Response usage is post-execution reporting, not admission
proof. An estimated token count can support conservative rejection only if an
approved tokenizer/model contract, deterministic request-size cap, and safety
margin make the maximum defensible; it is not a mathematical guarantee by
itself. Therefore **guaranteed input financial exposure is a separate blocking
dependency** for real execution under the current API/model contract.

## 9. Approval and implementation sequence

1. Approve this authority boundary, producer enrollment model, policy owner,
   tariff evidence process, and financial administrator RBAC.
2. Design/migrate AdminApps reservation, budget, tariff, idempotency, audit,
   and reconciliation tables with PostgreSQL concurrency/RLS tests.
3. Implement authenticated admission and settlement operations; test fault,
   replay, cross-tenant, and serializable-concurrency matrices.
4. Establish an approved exact-model input-token bounding contract.
5. Integrate ISO Smart only behind the existing fail-closed boundary and a
   separate operating authorization. Real inference remains unauthorized until
   all preceding gates are approved and evidenced.
