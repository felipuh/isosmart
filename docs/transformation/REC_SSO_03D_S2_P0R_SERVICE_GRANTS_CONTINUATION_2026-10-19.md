# Service grant consumer amendment — 2026-10-19 continuation

Both adapters now fail closed on every central HTTP 4xx, including missing/disabled tenant 404.
They return allowed=false and authorization_denied=true; existing local fallback cannot bypass this.
Server HTTP error bodies are discarded: allowed/valid/modules inside a 5xx are not authority. Existing
explicit test/demo transport fallback policy remains, and IS_PRODUCTION=true disables it.

No active settings, credentials or grants were changed. The seven service grants, authenticated
credential_id, tenant/product lists and independence from SSOClient retain the preceding contract.
No additional permission or fallback is implied. Actual adapter/central-handler tests use synthetic
credentials and simulated ORM/HTTP. Real provisioning, projection persistence and HTTP E2E remain open.

Evidence and full contract delta:
`/home/felipe/proyectos/adminapps/docs/security/REC-SSO-03D-S2-P0R/continuation-20261019/REPORT.md`.

PRODUCTION_READY = FALSE · NO_DEPLOYMENT · NO_COMMIT · NO_PUSH · GOVERNANCE_PRESERVED.
