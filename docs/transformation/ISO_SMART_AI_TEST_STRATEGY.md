# ISO Smart AI — estrategia de pruebas y quality gates

## Portfolio

| Capa | Objetivo | Herramienta/entorno | Gate mínimo |
|---|---|---|---|
| Unit | Value objects, transitions, policies | pytest/Django test o baseline acordada | Rápido, determinista |
| Domain/service | Casos de uso y invariantes | DB test aislada | Happy/negative/idempotent |
| Model constraints | unique/check/FK/versioning | PostgreSQL real | Violaciones rechazadas |
| RLS/tenant | select/insert/update/delete/joins/tasks/raw SQL | PostgreSQL con runtime role | Cero escape cross-tenant |
| Permissions | RBAC/ABAC/mass assignment/IDOR | API tests | Default deny |
| API contract | OpenAPI request/response/error/backward compatibility | schema validation + diff | Sin breaking no aprobado |
| AdminApps | identity/entitlement/sync/outage/replay | consumer/provider contract fakes | Fail-closed demostrado |
| Events/outbox | commit ordering, duplicate, retry, DLQ | DB + worker integration | Efecto exactamente una vez lógico |
| Agents | pipeline/provenance/autonomy | provider/retriever stubs | Run reconstruible |
| Deterministic rules | edición/rule bundle | fixtures versionadas | Golden vectors exactos |
| Human Gate | A0–A4, expiry, rejection, tamper | domain/API | Sin ejecución no autorizada |
| Migrations | forward/backward/backfill/reconcile | snapshot anonimizado/sintético | Rollback y conteos válidos |
| Frontend component | states/forms/drawer/dialog | Vitest/RTL o baseline común | Interacciones y errores |
| Accessibility | keyboard/focus/name/contrast | axe + Playwright/manual | Cero critical/serious acordado |
| E2E | journeys críticos | Playwright + Postgres + AdminApps sandbox | Login→gate→evidence→approval |
| Performance | traversal, API, DB pool, queue | k6/Locust + EXPLAIN | SLO aprobado, no inventado |
| Security regression | uploads, SSRF/XSS/CSRF/CORS/replay/secrets | SAST/SCA/DAST/tests | Cero P0/P1 abierto para release |

## IA: separación obligatoria

1. Rule evaluator: entradas/versiones y salida exacta; sin modelo.
2. Retrieval: dataset/namespace, autorización tenant, recall fixtures y no cross-tenant.
3. Inference: contract/schema, timeout, redaction; proveedor simulado en CI.
4. Policy/autonomy: tabla de decisión A0–A4 determinista.
5. Human approval: actor, scope, expiry, single-use/replay.
6. Action execution: allow-list, idempotency, rollback.
7. Effectiveness: métrica/ventana/baseline; no “parece buena”.

Evaluaciones de calidad de modelo son adicionales y versionadas; nunca reemplazan invariantes deterministas o revisión humana material.

## Pruebas prioritarias de seguridad

- Assistant create/update ignora organization del payload y valida conversation/message tenant.
- EvidenceEdge rechaza source/target de tenants distintos.
- AdminApps deny, timeout, malformed response, stale cache y revoked entitlement no conceden acceso.
- Onboarding status error no desbloquea; transitions no permitidas retornan conflicto/forbidden.
- RLS con runtime role, superuser separado y pool reuse.
- Upload MIME spoof, oversized, path traversal, malicious scanner result y unauthorized download.
- Audit/DocumentVersion/Rule publicada no admiten update/delete por runtime.

## CI stages

1. Format/lint/type/unit + secret scan.
2. OpenAPI generate/diff y frontend generated-client freshness.
3. PostgreSQL migrations + constraints + RLS + domain/API tests.
4. Frontend component/a11y/build.
5. Integration AdminApps/outbox/workers/AI stubs.
6. Playwright critical paths.
7. SCA/SAST/SBOM; performance/security suites según release.

No usar SQLite como único gate. Deshabilitar telemetría de Chroma/PostHog en test. DBs, object store y queues de CI son efímeros y no contienen datos reales.

## Estado actual verificado en esta corrida

- Django check: PASS, 0 issues.
- Migration drift: PASS, no changes detected.
- Backend `authentication core integration`: 89 tests PASS en 7.468 s con settings SQLite; warnings de paginación y telemetría Chroma/PostHog.
- Frontend ESLint: PASS.
- Build frontend a `/tmp/isosmart-ai-discovery-dist`: PASS, 2,410 módulos, 18.29 s; los chunks mayores observados fueron i18n 348.74 kB y vendor-misc 336.89 kB sin gzip.
- No se ejecutaron E2E ni pruebas PostgreSQL/RLS porque requieren servicios externos/una topología no disponible y no deben tocar datos locales.

Los tests actuales no cubren de forma dedicada leadership/planning/operations/performance/improvement/resources, RLS, contratos, a11y, onboarding 17 pasos ni runtime gobernado.

## Evidencia de contención P0 — 2026-08-13

Cobertura añadida:

- Assistant: tenant del payload ignorado en create/update; list/retrieve/patch/delete cross-tenant; querysets de prompt/feedback/audit; conversation/message de feedback cross-tenant e inexistentes con error indistinguible; audit log GET y bloqueo POST/PUT/PATCH/DELETE; emisión interna ORM preservada.
- Evidence Graph: A→A permitido; A→B, B→A y B→B desde actor A rechazados; referencias externas/inexistentes genéricas; edge B no visible ni mutable/eliminable; update de edge A no puede apuntar a B.
- Onboarding: loading no concede acceso; outage y respuesta inválida quedan degraded/fail-closed; `sessionStorage` forjado no concede acceso; retry consulta otra vez el backend.
- Assistant UI/runtime: fallo HTTP no presenta knowledge base local; proveedor 401 emite y persiste únicamente degradación explícita, con `provider=unavailable`, `degraded=true` y sin eco de consulta ni recomendación normativa.

Comandos y resultados exactos:

```text
backend/.venv/bin/python backend/manage.py check --settings=backend.settings_test
PASS: System check identified no issues (0 silenced).

backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run --settings=backend.settings_test
PASS: No changes detected.

backend/.venv/bin/python backend/manage.py test authentication core integration leadership --settings=backend.settings_test --noinput --verbosity 1
PASS final: 98 tests in 6.043s.
Observaciones no bloqueantes: warnings esperados 400/403/404/405, paginación sin ordering y telemetría Chroma/PostHog intentando DNS al finalizar.

npm run lint
PASS.

npm run build -- --outDir /tmp/isosmart-ai-p0-build --emptyOutDir
PASS final: Vite 8.0.16, 2,410 módulos, 11.14s.

npx playwright test tests/e2e/onboarding-guard-runtime.spec.js tests/e2e/assistant-runtime.spec.js --config=playwright.config.cjs --reporter=line
RESULTADO INICIAL: 4 PASS; 1 FAIL por mock de retry sensible al doble efecto de React dev (no por producto).

npx playwright test tests/e2e/onboarding-guard-runtime.spec.js --config=playwright.config.cjs --reporter=line --grep "retry queries"
PASS: 1 test en 20.7s después de hacer que el mock permanezca caído hasta el retry explícito.

npx playwright test tests/e2e/onboarding-guard-runtime.spec.js tests/e2e/assistant-runtime.spec.js --config=playwright.config.cjs --reporter=line
PASS final consolidado: 5 tests en 1.1m.
```

Playwright usó exclusivamente Vite efímero en `127.0.0.1:3001` y routes simuladas para auth, onboarding y assistant. No inició Django, no abrió `backend/test_default.sqlite3`, no usó servicios compartidos ni datos persistentes. El primer intento sandboxed no pudo bindear el puerto (`EPERM`); se repitió con autorización para el listener local efímero.

No se ejecutaron PostgreSQL/RLS, deploy, producción, datos reales, runtime completo de agentes ni onboarding de 17 pasos; permanecen fuera del alcance de esta contención.
