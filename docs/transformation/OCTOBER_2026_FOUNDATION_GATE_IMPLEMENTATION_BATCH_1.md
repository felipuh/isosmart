# October 2026 — Foundation Gate implementation batch 1

Date: 2026-10-05 (America/Costa_Rica)
Scope: repository-local product implementation. This record does not amend the
frozen WP2 matrix or Phase31.5 evidence.

## Governance boundary

`Phase31.5 = EXECUTION_HELD` is limited to its operational execution and
promotion scope. Its controlling plan explicitly excludes Phase32 and product
code changes. This batch performs no E-07 action, database operation,
migration, deployment, credential operation, or external call.

## Source traceability and selected requirements

| Requirement | Authoritative source reference | Prior state | Missing source-defined behavior | Change and test evidence | Batch disposition |
|---|---|---|---|---|---|
| `REQ-ONBOARDING-09` | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, `onboarding[9]` — “Quiz obligatorio adaptativo por rol/industria; mínimo recomendado 80%; reintentos guiados.” | `PARTIAL` | The existing server-side gate was not exposed in the human onboarding journey. | `OnboardingPage` fetches only server-published paths/questions, submits selections to the existing server evaluator, displays its result, and blocks the legacy finish action until the source gate reports `passed`. Playwright covers the round trip. | `PARTIAL`: licensed/published content and the remaining onboarding steps still have their established independent blockers. |
| `REQ-API-GET-ONBOARDING-STATUS` | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, OpenAPI path `GET /v1/onboarding/status` | `PARTIAL` | Browser client could not reach the existing source-contract status path through its `/api` gateway. | The unchanged `/v1` contract is additionally routed at `/api/v1`; `foundationService` consumes it through the authenticated browser API client. Django route tests and Playwright cover the gateway. | `PARTIAL`: the endpoint now supports the Foundation journey, but its response truthfully retains the incomplete source-defined steps. |
| `REQ-ENTITY-QUESTION-BANK` | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, `entities[QuestionBank]` — `question_id; concept_id; industry_profile_id; difficulty; scenario; options_json; answer_key` | `PARTIAL` | Published questions and options had no functional user-facing consumer in the onboarding journey. | The UI renders only the server-projected question metadata and options. It never receives or derives `answer_key`; server-side evaluation remains authoritative. Playwright asserts the exact submitted selection. | `PARTIAL`: publisher-controlled question content and canonical concept/industry authority are not changed by this batch. |

## Constraints preserved

- No ISO content, question answer key, score, selection rule, or retry policy is
  fabricated in the client.
- The server remains the sole evaluator of a Foundation attempt.
- The frontend sends only the selected option IDs for the currently
  server-published question set.
- No database or migration change is required; tenant/RLS/audit/event behavior
  remains in the existing Foundation command and its PostgreSQL test suite.

## Verification

- `foundation.test_source_artifact_api.SourceArtifactRouteTests`: 7 passing.
- `manage.py check --settings=backend.settings_test`: passing.
- `frontend npm run lint`: passing.
- `frontend npm run build`: passing.
- `frontend Playwright onboarding-guard-runtime.spec.js`: 4 passing.
