# AI usage metering v1

ISO Smart records one `AIUsageRecord` for every external inference attempt. It
is a local execution ledger, not a customer invoice and not an AdminApps tenant
master. Tenant attribution is obtained only from the server-resolved
`TrustedTenantIdentity`; the corresponding authoritative identifier is copied
from `TenantProjection.adminapps_tenant_id` at reservation time.

## Lifecycle and failure semantics

Before a Value Discovery capability invokes its provider, ISO Smart commits a
`started` ledger row using a deterministic `event_id:capability` invocation
identity. Each finalization is a separate short tenant transaction from the
onboarding transaction. A later Step 11 validation or persistence rollback
therefore cannot erase a provider attempt.

Provider token metadata is normalized only when the provider reports valid
input, output, and total counts. Missing, malformed, timed-out, or lost
responses become `usage_status=unknown`; no prompt-length estimate and no zero
token substitute is written. Invalid model output with provider usage remains a
`rejected` attempt, while its reported usage is retained.

The unique `(tenant_id, invocation_id)` constraint prevents duplicate payment
accounting on the same replay. A duplicate reservation fails closed before a
second provider call. A deliberate new attempt requires a new invocation/event
identity.

## Cost semantics

`AIModelPricingVersion` is an effective-dated, verified provider tariff. Cost
uses PostgreSQL numeric/`Decimal` and snapshots the matching rates onto the
usage record. No tariff is seeded by this change: without a verified tariff,
`cost_status=unpriced` and `estimated_provider_cost=NULL`. Provider-cost
estimates are never customer billing prices.

## AdminApps contract

`serialize_for_adminapps(record, usage_event_id=...)` produces the secret-free
schema v1 payload accepted by `POST /api/integration/ai-usage/`. It contains
the authoritative AdminApps tenant identifier, stable usage event/record IDs,
dimensions, token counts, and cost state; it never includes prompts, model
responses, authorization headers, or API keys. AdminApps validates the tenant
against its `Organization` authority and has unique source/event and
source/record identities for replay safety.

This cycle intentionally configures no delivery URL, credential, or publisher.
The local ledger is authoritative for ISO Smart execution; external transport
requires separate operational authorization. The AdminApps `AI Usage & Costs`
view is restricted to existing AdminApps administrators and presents provider
observability only.

## Retention and reconciliation

Retain ledger records according to approved financial/audit retention policy.
Reconcile local record IDs against the AdminApps projection IDs and replay
missing payloads using the stable usage event identity. Unpriced and unknown
records must remain visible in every summary rather than being silently folded
into zero cost.
