# ISO Smart canonical reconciliation baseline — 2026-10-05

## Canonical source under test

- Canonical integration base: `bcfb1360005c43ca3229d0b72079b10c0ff84ec4`
- Reconciliation source commits: `ef47ff60` (tracked internal-context metadata wiring) and `86cd8ee9` (Phase 31.4 authority-tenant correction).
- E-07 remains `BLOCKED_BY_EXTERNAL_AUTHORITY / OPERATIONAL_READINESS`.
- E-08 remains `CLOSED_LOCAL_TECHNICAL_EVIDENCE`.
- Phase31.5 remains `EXECUTION_HELD`.

## Backend PostgreSQL result

Authoritative command: `FULL_REPOSITORY_TESTS=1 bash backend/scripts/run_postgres_integration.sh`.

| Total | Pass | Fail | Error | Skip |
| ---: | ---: | ---: | ---: | ---: |
| 664 | 630 | 9 | 24 | 1 |

The disposable PostgreSQL lifecycle and teardown passed. The count is six higher than the previously cited 658 baseline, reflecting the current canonical suite rather than a substituted harness.

Failure/error families:

- 16 errors: frozen Phase 31.4 runtime/V2.4 support-package integrity and executable-wiring expectations.
- 8 errors: integration assistant API tests.
- 1 failure: ISO Smart product-access login expectation.
- 2 failures: Phase 31.4 supporting-contract census and authoritative-producer source-hash reachability.
- 1 failure: Phase 8 normative tenant-event contract expectation.
- 5 failures: leadership evidence-edge tenant-containment expectations.

## Focused QMS result

`bash backend/scripts/run_postgres_integration.sh` passed `38/38` focused PostgreSQL tests, followed by `18/18` ActionExecution rollback acceptance assertions. Controlled QMS browser E2E passed `2/2`.

The controlled browser run uses a disposable PostgreSQL database and controlled principal. It is not an authentic AdminApps E2E. Its validated defaults remain fail-closed: `QMS_WRITE_POLICY = SEMANTICS_INSUFFICIENT`, `QMS_CAPA_CREATE_ENABLED = FALSE BY DEFAULT`, and `CAUSE_REFERENCE_SEMANTICS_INSUFFICIENT`.

## Frontend result

- `npm run lint`: pass.
- `npm run build -- --outDir /tmp/isosmart-ai-reconciliation-build --emptyOutDir`: pass.
- Controlled onboarding E2E: `4/5` pass.

The organizational-profile request persists successfully, but the final browser assertion remains on `/onboarding` rather than reaching `/`. This is classified as `CURRENT_PRODUCT_DEFECT`: `OnboardingPage` calls `navigate('/')`, but the surrounding onboarding guard retains its earlier incomplete state and returns the user to `/onboarding`. No product behavior was changed during reconciliation.

## Next normal development batch

1. Resolve the organizational-profile completion redirect defect and its browser assertion, because it directly affects November functional testing.
2. Implement the source-traceable browser consumer for `REQ-ONBOARDING-12`.
3. Select the next remaining source-executable onboarding/QMS P0 item only after the full PostgreSQL baseline failures are triaged.
