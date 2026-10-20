# ISO Smart AI Financial Guardrails — PostgreSQL Validation Report

**Date:** 2026-10-08

## Executive verdict

`AI_FINANCIAL_POSTGRESQL_VALIDATION_PASS`

The ISO Smart controlled-test reservation primitives passed the focused,
disposable PostgreSQL 18.6 validation. This verdict applies only to synthetic,
product-scoped reservation mechanics. It does not authorize central financial
authority, real OpenAI inference, live spending, deployment, production
delivery, a Git push, or Phase 31.5 execution.

`REAL_OPENAI_INFERENCE = NOT_AUTHORIZED`

`PHASE31_5 = EXECUTION_HELD`

## Starting state preserved

Both repositories began on `hardening/p0-p1-enterprise-readiness` at
`0ce01dff` (ISO Smart, two commits ahead of origin) and `42f007d1` (AdminApps,
two commits ahead of origin). ISO Smart had pre-existing modified settings,
usage/outbox/eventing/model/test/provider files and untracked financial-guardrail
and governance artifacts. They were preserved. AdminApps had no reported
working-tree changes. No commit, merge, push, deployment, credential access,
provider call, or customer transaction occurred.

## PostgreSQL runtime and cleanup evidence

The established `foundation/postgres_foundation_gate.py` lifecycle ran the
focused `foundation/ai_financial_guardrails_postgres_harness.py` against the
official PostgreSQL 18.6 image. Run ID: `20261009T001336Z_c9e0c7`; endpoint was
loopback-only and credentials were generated in memory. The harness created
dedicated NOLOGIN owners plus independent LOGIN migrator/app/worker roles.

The final lifecycle output reported all of:

- `AI_FINANCIAL_GUARDRAILS_POSTGRES_PASS=4`
- bootstrap initial run `PASS`; repeat bootstrap `PASS_IDEMPOTENT`
- teardown `PASS`
- container absent, volume absent, temporary build context absent

Teardown first dropped the run-scoped database and all run-scoped roles, and
the harness verified no scoped roles remained. No disposable PostgreSQL process,
database role, or generated credential was retained.

## Migration 0042

The suite migrated a fresh database to actual predecessor `0041`, verified the
0042 tables did not yet exist, then migrated to `0042_ai_financial_guardrails`.
It verified both financial tables, RLS `ENABLE` and `FORCE`, tenant policies,
invocation uniqueness, reservation foreign keys, policy index, runtime grants,
and a non-superuser/non-`BYPASSRLS` runtime identity.

The first attempted real migration exposed an actual defect in the untracked
0042 baseline: SQL quoting inside `format()` generated invalid policy SQL. It
was corrected minimally to the repository's established dollar-quoted policy
format. A second runtime defect was found and fixed: the public
`trusted_tenant_context` documented trusted-identity-only input but did not
check the type before setting context. It now fails request-shaped values before
database context mutation. The final rerun passed all four PostgreSQL tests.

## Isolation, admission, arithmetic, and recovery

| Gate | Result |
| --- | --- |
| Tenant A/B reservation and policy visibility | PASS — B could neither read nor update A rows; missing context returned no rows. |
| Trusted identity input | PASS — non-`TrustedTenantIdentity` input fails before context binding. |
| Concurrent budget/request admission | PASS — two independent worker connections and real concurrent transactions admitted one request only; the other was denied by quota/budget. |
| Invocation idempotency | PASS — same identity returned the same reservation; changed bounds were rejected as a conflict. |
| Transaction rollback | PASS — forced outer rollback left no reservation. |
| Decimal/tariff/currency mechanics | PASS — synthetic labeled tariff, exact `Decimal` reservation arithmetic, enforced bounds, and verified effective pricing path exercised. |
| Settlement and recovery | PASS — known settlement is idempotent; unknown usage remains `unresolved`; only proven non-dispatch becomes `released`; cross-tenant settlement is blocked. |

Synthetic rates and models in the harness are explicitly `SYNTHETIC_TEST_TARIFF_ONLY`; they do not assert provider pricing.

## Regression and input-bound assessment

Focused SQLite-safe regressions completed: `16` tests passed across
`foundation.test_ai_usage`, `foundation.test_ai_financial_guardrails`, and
`foundation.test_value_discovery`. Compilation and diff whitespace checks
passed. The existing common execution boundary still rejects `REAL_AI` before
ledger creation or provider I/O; changing the operational switch still fails
closed with `AI_FINANCIAL_AUTHORITY_CONTRACT_MISSING`.

The Chat Completions adapter sends `max_tokens=2000`, which constrains output,
not input. It serializes context without provider-supported exact preflight
input-token counting or an approved exact-model request-size/token bound.
Post-response token metadata is not admission proof. A defensible guaranteed
input-cost bound therefore remains a separate blocker for real execution.

## Authority and remaining blockers

The approval-pending source-grounded central design is in
`ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_2026-10-08.md`. It preserves
AdminApps as the authoritative organization, entitlement, product registry,
integration-principal, and central financial decision owner. It creates no
operational authority.

Remaining blockers:

1. Approve and implement the AdminApps central entitlement/reservation/
   settlement contract with its own concurrency, RLS, and failure testing.
2. Approve exact provider/model scope and effective verified tariff evidence.
3. Establish an enforceable input-token maximum for the selected API/model.
4. Obtain separately governed authorization before changing the paid-provider
   execution boundary.

## Task-owned changes

- `backend/foundation/migrations/0042_ai_financial_guardrails.py` — fixed
  demonstrated PostgreSQL policy-SQL quoting defect.
- `backend/foundation/tenant_context.py` — enforced documented trusted identity
  type at the public context boundary.
- `backend/foundation/ai_financial_guardrails_postgres_harness.py` — focused
  disposable PostgreSQL validation coverage.
- This report and `ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_2026-10-08.md`.

All unrelated existing work remains unmodified. Recommended next step is
approval of the V1 contract, then an AdminApps-only implementation batch; do
not activate ISO Smart real-provider execution in that batch.
