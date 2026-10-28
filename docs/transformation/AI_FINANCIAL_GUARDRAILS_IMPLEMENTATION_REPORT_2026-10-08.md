# AI Financial Guardrails Implementation Report

**Date:** 2026-10-08  
**Verdict:** `AI_FINANCIAL_GUARDRAILS_BLOCKED_BY_AUTHORITY_CONTRACT`

## Executive verdict

ISO Smart now has a server-side, fail-closed paid-provider execution boundary:
every Value Discovery call reaches `run_metered_capability`, which rejects a
`REAL_AI` provider before a usage record is created or provider I/O begins.
The default remains `AI_REAL_INFERENCE_AUTHORIZED=False`. Setting it to true
does not permit execution; it continues to reject with
`AI_FINANCIAL_AUTHORITY_CONTRACT_MISSING` because no authenticated AdminApps
contract currently supplies a valid entitlement decision and central budget
reservation.

This batch deliberately does **not** claim a global budget cap or authorize
real OpenAI inference. `PHASE31_5 = EXECUTION_HELD` is unchanged.

## Discovery and gap classification

| Item | Classification | Evidence / boundary |
| --- | --- | --- |
| Tenant identity and local RLS | IMPLEMENTED_AND_TESTED | `TenantProjection`, trusted tenant context and existing PostgreSQL harnesses. |
| Product entitlement authority | PARTIAL | AdminApps owns `OrganizationProductEntitlement`; ISO Smart has no authenticated, pre-request entitlement decision contract. |
| AI usage record and durable outbox | IMPLEMENTED_AND_TESTED | `AIUsageRecord`, stable event IDs and the accepted cross-product HTTP E2E baseline. |
| Versioned model pricing | IMPLEMENTED_UNTESTED_FOR_PILOT | Effective-dated verified tariff lookup exists; no approved tariff for a real model was found. |
| Strict provider adapter | IMPLEMENTED_AND_TESTED | Schema-strict Chat Completions adapter has fixed request `max_tokens`; no mathematically guaranteed input-token bound is available. |
| Pre-request paid admission | IMPLEMENTED_AND_TESTED | Common execution edge blocks every `REAL_AI` request before I/O. |
| Cross-product budget reservation | BLOCKED_BY_AUTHORITY_CONTRACT | No AdminApps authenticated reservation API/contract exists; none was invented. |
| Product-scoped reservation mechanics | IMPLEMENTED_UNTESTED | Migration `0042` adds auditable, tenant-RLS-protected reservations for **controlled_test only**. It is not reachable from real inference. |
| Unknown/unpriced reconciliation stop | PARTIAL | The reservation service leaves unpriced/unknown use `unresolved`; live provider execution remains blocked. |

## Narrow implementation

- `AI_REAL_INFERENCE_AUTHORIZED` is default-disabled and does not itself grant
  execution authority.
- The metered execution choke point rejects real providers prior to network I/O.
  There is no alternate Value Discovery provider invocation path.
- `AIFinancialGuardrailPolicy` and `AIFinancialReservation` are tenant-scoped
  PostgreSQL tables with `ENABLE` + `FORCE` RLS, a policy-row lock, a
  `(tenant_id, invocation_id)` uniqueness constraint, Decimal money values,
  verified/effective tariff selection and an immutable product identifier.
- These tables only accept `policy_scope='controlled_test'`. They exist to
  prove the reservation design with synthetic inputs, not to displace
  AdminApps as the financial authority.
- Reservation settlement preserves the full worst-case exposure for missing,
  unpriced or out-of-bound usage. Only a separately explicit proven
  pre-dispatch failure can release a reservation.

## Transaction boundaries

For a controlled synthetic policy, admission locks the one applicable policy,
checks its period, model, input/output bounds, request count, verified tariff,
currency and Decimal worst-case exposure, then inserts the reservation in the
same transaction. The unique invocation identity makes retries idempotent.
The lock serializes concurrent admissions for the same policy. Settlement also
locks its reservation. No provider call is part of either transaction.

For paid execution, the boundary stops earlier because the required central
authority contract is absent.

## Validation performed

Focused isolated tests passed locally:

```text
./.venv/bin/python manage.py test foundation.test_ai_usage \
  foundation.test_ai_financial_guardrails foundation.test_value_discovery \
  --settings=backend.settings_test --noinput --verbosity 2

16 tests passed
```

Covered by the added focused tests: Decimal worst-case arithmetic, invalid
input-bound rejection without persistence, rejection in the common execution
path before either ledger or provider invocation, default paid-provider denial,
and continued failure after the operational switch when the central authority
is missing. Existing strict-adapter and usage/outbox-focused tests also passed.

No disposable PostgreSQL test was run in this batch. Therefore RLS metadata,
real concurrent locking, and migration application are intentionally not
claimed as validated evidence. No provider request, credential use, delivery,
deployment, commit, merge or push occurred.

## Remaining blockers and governed next batch

1. Define an authenticated AdminApps contract for a point-in-time product
   entitlement decision and atomic central reservation/settlement keyed by a
   stable idempotency identity.
2. Approve a specific provider/model and register a reviewed, source-linked,
   effective verified tariff including precise billing semantics.
3. Add a guaranteed input-token bounding mechanism for the exact provider API
   rather than an estimate.
4. Run the migration and controlled concurrency/RLS matrix on a fresh,
   disposable PostgreSQL environment, including same-budget races, settlement,
   unknown usage, duplicate identity and tenant isolation.
5. Only after those controls and separate operating authorization are accepted
   may the real-provider execution boundary be revisited. That would still not
   constitute authorization to make a real OpenAI request.
