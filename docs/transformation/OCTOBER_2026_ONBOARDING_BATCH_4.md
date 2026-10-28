# October 2026 — Onboarding completion and document-reference browser flow

Date: 2026-10-05 (America/Costa_Rica)

This record covers repository-local product work. It does not reopen E-07,
E-08, or the Phase31.5 execution hold.

## REQ-ONBOARDING-10 traceability and defect

| Field | Evidence |
| --- | --- |
| Requirement ID | `REQ-ONBOARDING-10` |
| Source artifact | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, `onboarding[10]`, **Organizational Profile** |
| Authority class | `SOURCE_DEFINED`; browser transport and cache coordination are `IMPLEMENTATION_DEFINED_WITHIN_SOURCE_CONSTRAINTS` |
| Source behavior | Record role, expertise, size, sites, country, industry/manufacture-service, and current certification. |
| Existing implementation | `POST /v1/onboarding/organizational-profile` persists the tenant-scoped profile, provenance hash, workflow transition, immutable audit and event effects. |
| Defect | `OnboardingPage` persisted legacy completion and navigated, while each `OnboardingGuard` retained an earlier independent `incomplete` status. The destination guard therefore redirected the user back to `/onboarding`. |
| Correction | `OnboardingStatusProvider` is the sole browser state for the authoritative legacy completion readback. The finish action now waits for a successful `GET /settings/onboarding_status/` result reporting `onboarding_completed=true` before navigation. |

The guard remains fail-closed for unavailable, invalid, or incomplete status;
it was neither removed nor weakened.

## REQ-ONBOARDING-12 traceability

| Field | Evidence |
| --- | --- |
| Requirement ID | `REQ-ONBOARDING-12` |
| Source artifact | `ISO_SMART_AI_Mapa_Maestro_Datos.json`, `onboarding[12]`, **Document/Data Ingestion** |
| Exact source reference | `"Carga/importación de estrategia, procesos, KPIs, auditorías, reclamos, proveedores, documentos."` |
| Authority class | Source categories are `SOURCE_DEFINED`; browser metadata transport is `IMPLEMENTATION_DEFINED_WITHIN_SOURCE_CONSTRAINTS` and follows the approved Batch 2 API contract. |
| Existing backend/API | `POST /v1/onboarding/document-references`; `OnboardingEvidenceIngestionService` persists the existing tenant-scoped evidence/audit/outbox/provenance effects and reports `content_bytes_read=false`. |
| Browser behavior | When server-projected step 12 is `AVAILABLE` or `IN_PROGRESS`, the onboarding screen accepts exactly source category, source URI, lowercase SHA-256, and capture time, then submits one metadata reference with stable batch/item idempotency IDs and refreshes authoritative onboarding status. |
| Explicit boundary | No file control, multipart request, document bytes, parsing, OCR, storage, licensing behavior, or source-content display was added. |

The browser does not unlock step 12 itself; it reflects the server-projected
workflow status and remains locked until its existing prerequisites are met.

## Validation scope

- `foundation.test_source_artifact_api`: transport tests for organizational
  profiles and metadata-only document references.
- `onboarding-guard-runtime.spec.js`: controlled browser coverage for
  authoritative completion readback and document-reference submit/readback.
- Frontend lint and production build validate the consumer bundle.
- The canonical disposable PostgreSQL suite remains the authoritative
  tenant/RLS, provenance, audit, event/outbox, and regression check.
