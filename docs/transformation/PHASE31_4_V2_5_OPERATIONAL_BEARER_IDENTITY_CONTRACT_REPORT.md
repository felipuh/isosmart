# Phase 31.4 V2.5 Operational Bearer Identity Contract

## Verdict

`SAFE_PROGRAMMATIC_BEARER_ISSUANCE_AVAILABLE`

The blocker `AUTHENTICATED_READINESS_IDENTITY_CONTRACT_UNRESOLVED` is closed at source and offline-test level. Live validation requires a new, independent successor diagnostic authorization.

## Contract

The existing run-scoped AdminApps user is created active with an unusable password, `viewer` role, and no staff or superuser privilege. Its enabled trial entitlement is valid under the existing billing policy without fabricating a subscription. AdminApps issues one 15-minute SimpleJWT access token with the existing shared SSO signing subsystem. The raw token crosses the process boundary only through an anonymous inherited pipe, remains in a mutable in-memory buffer, authenticates `GET /health`, and is overwritten during teardown. Evidence contains only token presence, type, subject UUID, source, lifetime and SHA-256 fingerprint.

AdminApps readiness uses the persisted `IntegrationAPIKey` at `GET /api/integration/health/`. ISO Smart readiness retains its production `IsAuthenticated` contract at `GET /health`. No endpoint, permission, global JWT lifetime, password, refresh token or authentication bypass was added.

## Verification

- Focused bearer, readiness, redaction, lifecycle and integrity tests: `43/43 PASS`.
- Operational action boundary tests: `2/2 PASS`.
- ISO Smart regression on Python 3.12: `568/568 PASS`.
- AdminApps regression on Python 3.12: `180/180 PASS`.
- Python compilation, JSON validation, diff validation and credential scan: `PASS`.
- Raw credential leaks: `0`.
- Successor integrity V11: `PASS`, 29 protected sources.
- SQLite custody: unchanged and ignored; no database bytes enter Git.

## Governance

The previous V8 diagnostic cycle remains exhausted and Attempt 4 remains unauthorized. Historical Retry 20 remains superseded and unconsumed; current Retry 20 authorization is `NONE`, Retry 20 execution is `NO`, and Phase 31.5 remains `EXECUTION_HELD`.
