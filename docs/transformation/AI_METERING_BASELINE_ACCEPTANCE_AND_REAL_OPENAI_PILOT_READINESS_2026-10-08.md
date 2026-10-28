# SMART3AI AI Metering Baseline Acceptance and Real OpenAI Pilot Readiness

**Review date:** 2026-10-08  
**Scope:** read-only review of ISO Smart and AdminApps, plus this acceptance record. No inference, credential access, deployment, push, merge, or production delivery was performed.

## A. Executive verdict

`AI_REAL_INFERENCE_PILOT_BLOCKED_BY_GUARDRAILS`

The accepted cross-product metering path is a sound observability baseline, but it is not yet a safe spending-control boundary. In particular, ISO Smart has no pre-request server-side budget, request-count, per-tenant cost, or output-token enforcement. The configured `max_tokens=2000` is a request parameter, not a validated pilot allowance or aggregate budget control. A retry-exhaustion defect also labels retryable delivery exhaustion as a permanent rejection, removing it from ordinary worker recovery.

A later approval does not authorize execution until the prerequisites in section M are satisfied. `PHASE31_5 = EXECUTION_HELD`, `GIT_PUSH = NOT_AUTHORIZED`, `DEPLOYMENT = NOT_AUTHORIZED`, `REAL_OPENAI_INFERENCE = NOT_AUTHORIZED`, `PRODUCTION_DELIVERY = NOT_AUTHORIZED`, and `CREDENTIAL_ROTATION = NOT_AUTHORIZED` remain in force.

## B. Validated integration baseline

### Accepted evidence (not re-run in this review)

The accepted verdict is `AI_USAGE_CROSS_PRODUCT_HTTP_E2E_PASS`. The untracked, reusable harness at `backend/foundation/ai_usage_cross_product_e2e.py` documents a disposable loopback-only PostgreSQL 18.6 run and asserts:

| Control / outcome | Accepted evidence |
| --- | --- |
| Runtime and health | Python 3.12.13; ISO Smart health success (the brief records HTTP 204); AdminApps health HTTP 200 |
| Usage path | Three accepted projections; 412 reconciled tokens; real HTTP dispatcher and AdminApps ingestion |
| Transient delivery | HTTP `503 -> 201`, published after two attempts |
| Exhaustion | HTTP `503 -> 503`, retained as failed after two attempts |
| Permanent rejection | HTTP `404`, retained as failed after one attempt |
| Reconciliation and access | Central dashboard PASS; organization-admin dashboard access denied (`403, 403`); ISO Smart RLS PASS |
| Disposal | Harness `finally` stops processes and removes the temporary cluster |

The harness uses an explicit loopback endpoint, API key, enabled delivery flag, and retry count only inside its disposable environment. It does not establish a deployed delivery configuration.

### Contracts and authority boundaries

- ISO Smart creates an immutable, tenant-scoped `AIUsageRecord`; retains no prompt, response, or credential; normalizes provider-supplied token metadata only; prices only against a verified, effective-dated `AIModelPricingVersion`; and creates a stable-ID domain event plus transactional-outbox row.
- AdminApps authenticates the producer, checks the authoritative organization ID, validates token arithmetic/cost consistency, preserves idempotency by both event and source-record identity, and presents a central-admin-only aggregate dashboard. The projection explicitly is not an invoice, tariff, or entitlement decision.
- AdminApps remains authoritative for tenant identity, product entitlement, and central financial observability/aggregation. ISO Smart remains responsible for domain inference, tenant-scoped source persistence, source usage metering, and transactional-outbox production. No tenant-facing usage dashboard is introduced or implied.
- The ISO Smart delivery configuration is default-disabled: empty endpoint/key, `AI_USAGE_ADMINAPPS_DELIVERY_ENABLED=False`, timeout 5 seconds, and max attempts 3. Endpoint/key are required when delivery is enabled.

## C. Git state and preserved worktree

| Repository | Branch and HEAD | Worktree observed |
| --- | --- | --- |
| ISO Smart | `hardening/p0-p1-enterprise-readiness`, `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` (`feat: deliver AI usage through durable AdminApps outbox`), two commits ahead of origin | Modified `backend/backend/settings.py`; untracked `backend/foundation/ai_usage_cross_product_e2e.py`; both preserved |
| AdminApps | `hardening/p0-p1-enterprise-readiness`, `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c` (`fix: harden AI usage ingestion replay and producer checks`), two commits ahead of origin | Clean |

Related committed baseline changes are ISO Smart `f19fbd38` (metering and estimated costs) and `0ce01dff` (durable AdminApps outbox), plus AdminApps `1e7f1d93` (usage/cost dashboard) and `42f007d1` (producer and replay hardening). The existing settings change is limited to the explicit disabled-by-default delivery configuration. The harness is not tracked and should remain preserved as evidence until separately reviewed for inclusion. No commit was created by this review.

## D. Outbox recovery semantics

**Finding: genuine recoverability defect — High.**

`AIUsageDelivery._retryable` correctly classifies HTTP 503 and transport errors as retryable at first. However, when `publish_attempts >= max_attempts`, it calls `mark_failed(... error_code=PERMANENT_REJECTION)`. `deliver_next` then excludes that error code when claiming future work. Thus an exhausted transient failure is semantically recorded and operationally treated as a permanent rejection even though no recipient made a permanent 4xx decision.

The accepted harness correctly proves source-row retention, but its comment that this follows the recovery contract does not remove the mismatch. A source event remains available in the database, yet it is not eligible for ordinary redelivery because the permanent-rejection exclusion prevents it.

**Minimal remediation recommendation (not implemented):** introduce a distinct terminal/recovery-required code such as `AI_USAGE_RETRY_EXHAUSTED`; preserve the source record, attempt count, last HTTP status/error, and stable event ID; exclude it from automatic delivery; and provide an explicitly authorized, auditable operator replay/reset path that never reclassifies it as a 4xx rejection. Retain `AI_USAGE_PERMANENT_REJECTION` exclusively for authenticated recipient 4xx validation/authorization failures. Add focused tests for status/code/attempt count and authorized replay.

## E. Strict OpenAI adapter readiness

The existing `ChatCompletionsValueDiscoveryProvider` is an OpenAI-compatible Chat Completions adapter, not a proven production OpenAI integration. It requires URL, key, and model configuration; uses `response_format` with `json_schema.strict=true`; uses temperature zero; bounds the request at `max_tokens=2000`; rejects HTTP failures, refusals, unfinished responses, malformed JSON, and invalid domain output. ISO Smart also applies independent bounded domain/schema/provenance validation after provider output.

Metering integration is present: `ValueDiscoveryService` invokes `run_metered_capability` for each of its three capabilities; the ledger reserves one attempt before provider I/O, finalizes it on both success and error, persists provider request ID/status/duration/model/correlation/tenant attribution, and emits a secret-free stable-ID outbox event after finalization. The tenant-level uniqueness key `(tenant_id, invocation_id)` prevents a second provider attempt for the same invocation. AdminApps independently rejects conflicting replay identities.

Limitations that block a real pilot:

- The adapter does not prove that its configured URL is the OpenAI endpoint or that the configured model is approved/available; configuration defaults to an OpenAI URL and `gpt-4o-mini`, but it accepts any compatible endpoint.
- No verified local `AIModelPricingVersion` row, source reference, effective date, or authorization for the intended model was evidenced. The ledger correctly emits `unpriced` rather than inventing cost, but that must stop a financial pilot before further requests.
- On provider failures before a usable response, the source record is retained with unknown usage/unpriced cost. This is appropriate observability, but no policy presently stops subsequent requests or reconciles possibly consumed tokens with provider-side records.
- The adapter's `max_tokens=2000` is not tied to an approval artifact or server-side per-pilot/per-tenant budget reservation. Provider output may be accounted only after the call; it is not a consumption limit.
- Credentials are read from environment only and are not serialized into usage events. This review did not inspect, print, test, rotate, or validate any credential. A specific approved secret-injection target and operator remain required.

## F. Token metering accuracy

Token capture is accurate **when the provider returns complete usage metadata**: `prompt_tokens`/`input_tokens` plus `completion_tokens`/`output_tokens` are required, negative/non-integer values are rejected, and `total_tokens` must equal their sum. Cached-input metadata is retained when supplied. Prompt text is never used to estimate tokens.

## G. Pricing-version and cost reconciliation

Pricing selection is correctly constrained to a verified, effective-dated provider/model tariff with a positive rate unit. The selected rates and pricing-version foreign key are retained with the record; absent/incomplete pricing yields `unpriced` rather than a fabricated cost. AdminApps validates negative costs and estimated/unpriced consistency, then aggregates known cost separately from unknown/unpriced counts.

The current official OpenAI pricing page is an authoritative source for eventual tariff registration, but this repository review did not find an evidenced approved pricing record for the configured model. Pricing verification is therefore **pending in the implementation**, and no numeric pilot cap should be derived or claimed from code/configuration alone. Any approved pricing row must record the current official source, exact model identifier/API, effective period, currency, rate unit, and reviewer verification before execution.

## H. Financial guardrail assessment

| Safeguard | Status | Evidence / limitation |
| --- | --- | --- |
| Maximum budget per controlled test | **Missing** | No pre-request budget reservation or aggregate cap exists. |
| Maximum output tokens | **Configuration only** | Adapter sends `max_tokens=2000`; it is not bound to pilot authorization or independently enforced as a budget. |
| Maximum provider requests | **Missing** | No pilot/request counter or server-side quota was found. |
| Maximum cost per tenant | **Missing** | AdminApps aggregates after ingestion; no source or central spending gate exists. |
| Server-side consumption enforcement | **Missing** | Accounting is persisted after attempted provider I/O. |
| Correct pricing-version selection | **Implemented, not pilot-ready** | Verified/effective-dated lookup and snapshotting exist; no approved verified tariff record was evidenced. |
| Unknown/unpriced usage | **Implemented observability; missing stop policy** | It is classified/aggregated, but does not block future calls. |
| Duplicate billing protection | **Implemented for metering/projection** | Stable event ID, source invocation uniqueness, and dual AdminApps uniqueness constraints. This is not customer billing. |
| Provider failures with consumed tokens | **Partially implemented** | Failed attempts persist unknown/unpriced status; no provider reconciliation or stop condition. |
| Reconciliation stop condition | **Missing** | Dashboard warnings/counts do not prohibit subsequent requests. |

## I. Tenant and AdminApps authority validation

AdminApps is the authoritative organization directory referenced by the ISO Smart tenant projection; it owns product-entitlement evaluation and is the only reviewed cross-tenant financial-observability surface. The ingestion contract resolves the submitted authoritative tenant ID to an AdminApps organization before writing its projection. The E2E evidence confirms central-admin access and organization-admin denial; it explicitly records that a tenant-scoped AI-usage read contract is not defined.

ISO Smart is correctly limited to domain execution, tenant-scoped source records, provider-usage capture, pricing snapshotting, and outbox production. The AdminApps projection says it is not an invoice, tariff, or entitlement decision. No redundant billing authority or tenant-facing dashboard is created by the accepted baseline or this review.

## J. Credential and security assessment

Security controls observed: tenant context/RLS for source records, authoritative AdminApps tenant mapping, producer-key authentication and allowlist, secret-free usage payload, central-admin dashboard authorization, explicit default-disabled delivery, bounded HTTP timeouts, and idempotent delivery/ingestion.

Security gaps for real inference: no reviewed operational authorization for the specific endpoint/model/credential receiver; no approved credential ownership/injection/revocation procedure; no evidence of production target identity; no per-pilot allowlist or kill switch; and no authorization to enable delivery. The existing Phase31.5 governance holds remain controlling and are not changed by this record.

## K. Missing requirements and blockers

The blocking requirements are: pre-request hard quotas/budget reservation; a verified local tariff for the exact approved model; a stop-on-unknown/unpriced/reconciliation-failure policy; correction of retry-exhausted versus permanent-rejection semantics; an approved non-production credential/target/runbook; and explicit operational authority. The E2E PASS supplies none of these approvals.

## L. Minimal controlled pilot proposal — design only

Proposed, non-executed shape:

1. Create one disposable synthetic tenant in a non-production PostgreSQL environment, with no customer content and one explicitly approved central administrator.
2. Approve one exact OpenAI model identifier after model suitability and current pricing are reviewed; register one verified effective pricing version from the official source.
3. Use one synthetic, pre-reviewed bounded request and one Value Discovery capability with the existing strict JSON schema and independent validation.
4. Enforce before provider I/O: one total request, an explicit small maximum-output-token allowance, and a per-tenant/pilot cost reservation/cap computed from the approved tariff plus a conservative input allowance. Reject if any limit, pricing lookup, entitlement, or correlation/tenant mapping is absent.
5. Capture the provider request ID and complete provider usage metadata; persist the source ledger row and pricing snapshot transactionally. If usage/cost is unknown or cannot reconcile, stop the pilot and issue no further provider request.
6. Keep AdminApps HTTP delivery disabled for the inference run. Reconcile the source ledger directly in the approved non-production environment; enable the existing loopback-only E2E route only in a separately authorized disposable reconciliation exercise.
7. Treat malformed output, refusal, timeout, provider HTTP error, unknown usage, unpriced usage, budget breach, or outbox delivery uncertainty as terminal pilot-stop conditions. Do not retry the inference automatically.

## M. Exact prerequisites for operational authorization

All of the following require explicit, recorded authorization before any real call:

1. Approval of this design's model, endpoint, synthetic prompt/content, one-request limit, output-token allowance, currency, and maximum cost.
2. A current, reviewed official pricing source and an exact verified `AIModelPricingVersion` record for that approved model/API, including effective dates and rate unit.
3. Implemented and tested pre-request server-side quota/budget controls (one request, output-token cap, tenant/pilot cost cap), plus a fail-closed reconciliation stop condition.
4. Remediation and focused tests for retry exhaustion versus permanent 4xx rejection, including authorized manual replay semantics.
5. An approved non-production target identity, credential owner/injection procedure, least-privilege service credential, audit trail, revocation procedure, and no credential disclosure in evidence/logs.
6. Proof that the target environment has applied the reviewed schema/migrations and retains RLS, idempotency, and central-admin authorization behavior.
7. An approved runbook naming operators, start/stop authority, audit evidence, provider failure handling, no-production-delivery rule, and post-run reconciliation/cleanup.
8. Separate authorization if AdminApps HTTP delivery is ever to be enabled; this pilot design does not require it.

## N. Recommended next governed batch

Do not run inference. First, perform a small implementation-and-test batch limited to: (1) distinct retry-exhausted recovery state and authorized replay, (2) fail-closed pre-request pilot/tenant quotas and cost reservation, (3) verified pricing-record administration with review evidence, and (4) a non-production pilot runbook/authorization artifact. Re-review those changes and their focused tests before considering `AI_REAL_INFERENCE_PILOT_READY_FOR_APPROVAL`.
