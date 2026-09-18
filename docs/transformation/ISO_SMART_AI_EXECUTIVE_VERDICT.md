# ISO Smart AI — dictamen ejecutivo de discovery

## 1. Estado actual

- Arquitectura: monolito Django/React amplio y reutilizable, pero con bounded contexts difusos y entidades duplicadas.
- Stack: Django 4.2/DRF 3.15/Python 3.12 local; React 19/Vite 8; PostgreSQL configurado, Celery/Redis/Chroma. CI y locks no están alineados.
- Tests: 89 backend seleccionados pasan en SQLite; lint y build frontend pasan. No hay gate PostgreSQL/RLS, contract, a11y ni cobertura suficiente de módulos de negocio.
- Seguridad: hardening AdminApps fail-closed útil, pero existen escapes cross-tenant concretos, onboarding fail-open, JWT en browser storage, upload débil y secretos/higiene de repos en el ecosistema.
- Data: modelos QMS útiles; sin RLS, UUID uniforme, versionado normativo, outbox o audit inmutable. Tres DB configuradas sin routers.
- Frontend: shell/routing/i18n/Playwright reutilizables; falta TypeScript/OpenAPI client/shared DS extendido, drawer normativo y onboarding authoritative.
- Infraestructura: Nginx/Gunicorn y CI parciales; readiness/telemetry/PITR/restore/DR insuficientes.
- AdminApps: boundary real y entitlement gate sano; billing local/sync incompleto deben alinearse.
- Deuda: duplicación, mega-files, fallbacks/aliases, 13,473 archivos de venv tracked y requirements divergentes.

## 2. Reutilización

La tabla exhaustiva está en `ISO_SMART_AI_AS_IS_AUDIT.md`. Se conserva/hardena el monolito modular, shell React, auth/entitlement AdminApps, scoping mixin, request IDs, dominios QMS, Evidence Graph seed, motores/logs IA, i18n, Playwright y design system. Se migran proyecciones tenant, duplicados, documentos/evidencia y contratos. Se depreca autoridad billing local. Se incorporan normative core, RLS, outbox, runtime gobernado, learning gate e immutable audit.

## 3. Gap analysis

Baseline histórico provisional: 42 capacidades, 3 implementadas, 18 parciales, 21 ausentes, `(3 + 18 × 0.5) / 42 = 28.57%`. Tras intake 10/10, el catálogo oficial XLSX/JSON añade `User`; baseline verificado: 43 capacidades, 3 implementadas, 19 parciales, 21 ausentes, `(3 + 19 × 0.5) / 43 = 29.07%`. Es cobertura funcional ponderada, no compliance/readiness. El detalle reproducible está en Gap Matrix.

## 4. Technology alignment

Baseline inicial conservadora: Rocky/RHEL9, Python 3.12, Node 20, Django 4.2.22, DRF 3.15.2, React 19.2/Vite 8, npm lock v3, Nginx/Gunicorn. PostgreSQL major queda pendiente de inventario real; no se infiere del cliente 18. Primero locks/CI/contracts/security, después patches coordinados, y solo luego majors.

## 5. Arquitectura objetivo

Monolito modular por control-plane projection, Harmonized Core, Normative Knowledge, Evidence & Assurance, Quality Intelligence, AI Governance, Learning/Onboarding e Integration/Eventing. PostgreSQL RLS y graph relacional/CTE primero. DomainEvent + outbox. Frontend contract-first con cliente TypeScript y NormativeIntelligenceDrawer.

## 6. Migration strategy

Orden obligatorio: intake/contención → contracts/tenant/RLS/outbox/audit → normative/evidence spine → canónicos de negocio → onboarding/learning → governed agents → SRE/hardening/retiro. Cada agregado usa expand/backfill/reconcile/switch/observe/contract y rollback por feature flag; no borrado en la misma fase.

## 7. Riesgos

Baseline histórico de discovery (varios cerrados posteriormente): P0 incluía artefactos ausentes, dos escapes tenant, onboarding fail-open, fallback IA sin provenance, ausencia RLS/versionado/outbox/runtime, autoridad billing conflictiva y semantics AdminApps no diferenciadas.
- P1: duplicados, documentos/upload/audit, unique constraints globales, métricas cliente, token storage, a11y, OpenAPI/CI/repo hygiene/3-DB ambiguity.
- P2/P3: i18n/timezone/performance/operación refinada.

## 8. Verificación ejecutada

Comandos/resultado relevante (los inventarios `find`/`rg` están además en el historial de la corrida):

```text
backend/.venv/bin/python backend/manage.py check --settings=backend.settings_test
PASS: System check identified no issues.

backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run --settings=backend.settings_test
PASS: No changes detected.

backend/.venv/bin/python backend/manage.py test authentication core integration --settings=backend.settings_test --noinput --verbosity 1
PASS: 89 tests in 7.468s. Warnings: unordered pagination; Chroma/PostHog telemetry attempted network.

npm run lint
PASS.

npm run build -- --outDir /tmp/isosmart-ai-discovery-dist --emptyOutDir
PASS: Vite 8.0.16, 2,410 modules, 18.29s.

required-file non-empty checks
PASS: 9 required transformation docs + AGENTS.md.

gap matrix state count
PASS: 3 Implementado, 18 Parcial, 21 Ausente.

git diff --check -- docs/transformation docs/adr AGENTS.md
PASS (el diff global conserva un trailing whitespace preexistente en Sidebar.jsx, fuera de esta corrida).
```

No se ejecutaron E2E, PostgreSQL/RLS, deploy, servicios productivos ni pruebas con datos reales.

## 9. Dictamen

**Dictamen histórico de discovery:** **GO WITH RESTRICTIONS** únicamente para la fase 0 y una implementación incremental. **NO-GO** para migración masiva, recomendaciones IA materiales, multi-tenancy Enterprise o deployment hasta cerrar: intake de artefactos, boundary billing/AdminApps, PostgreSQL RLS tests y foundations de contract/provenance/outbox. Los escapes tenant/onboarding/fallback IA locales listados originalmente se actualizaron con evidencia en la sección 10; el gate específico vigente está en la sección 11.

## 10. Resultado Phase 0 P0 containment — 2026-08-13

Los cuatro P0 locales seleccionados quedaron mitigados con regresiones automatizadas:

- Assistant deriva tenant/actor del contexto autorizado, mantiene querysets tenant-scoped y rechaza referencias conversation/message fuera del tenant sin leakage.
- EvidenceEdge exige `source.organization == target.organization == current_tenant`; lookup de edges ajenos retorna 404 y las referencias de payload inválidas/cross-tenant usan 400 genérico indistinguible.
- `AssistantAuditLog` quedó read-only para clientes; su creación interna ORM permanece disponible. La inmutabilidad definitiva sigue pendiente.
- `OnboardingGuard` falla cerrado en loading/error/timeout/payload inválido, eliminó autorización por sesión y ofrece retry al servidor.
- Assistant backend/UI ya no fabrica fallback normativo: declara indisponibilidad y que no se generó análisis ni recomendación.

Evidencia: 98 tests backend PASS, check PASS, migration drift PASS, lint PASS, build PASS y cinco casos Playwright P0 efectivos PASS con APIs simuladas. No se crearon migrations ni se modificó AdminApps.

Al cierre de Phase 0, el dictamen global permanecía **GO WITH RESTRICTIONS**. Ese cierre no habilitaba RLS Enterprise, migración masiva, IA material, runtime completo ni deployment. El intake y design gate posteriores se registran en la sección 11.

## 11. Resultado Phase 1 Enterprise Data design gate — 2026-08-13

Los artefactos TO-BE ya no están ausentes: intake **10/10 VALID**, hashes preservados y reconciliación completa. Se formalizaron TenantProjection/AdminApps, clasificación de tablas, PostgreSQL 18.4 efímero condicionado, RLS `ENABLE+FORCE` con contexto transaccional, outbox/inbox, auditoría append-only/tamper-evident, versionado normativo, migración expand/contract, threat model y matriz PostgreSQL A/B/no-tenant.

**Corrección pre-implementación (2026-08-13):** el párrafo anterior conserva la evidencia histórica del Design Gate, que evaluó 18.4. La revalidación contra la información oficial de releases estableció PostgreSQL **18.6** como target de implementación de esta slice. Es una actualización de mantenimiento dentro de la arquitectura PostgreSQL 18 aprobada; PostgreSQL 19 beta/desarrollo no es elegible.

Dictamen específico para **ENTERPRISE DATA & TENANT FOUNDATION IMPLEMENTATION: GO WITH RESTRICTIONS**, limitado a la primera slice efímera/no destructiva. No autoriza migración masiva, normativa real, RLS productivo, billing/tenant authority local, deployment ni cambios externos. Restricciones: contratos AdminApps aún no acordados, PostgreSQL productivo no inventariado, fuente normativa licenciada/FDIS referida pero no incluida y RLS aún no ejecutada. La slice permanece **NO PASS** hasta crear y destruir con evidencia una instancia PostgreSQL 18.6 desechable y exclusiva —sin reutilizar producción, staging, desarrollo persistente, AdminApps ni recursos compartidos— y ejecutar allí sin skips las pruebas bloqueantes de rol/ownership/BYPASSRLS, ambos flags `relrowsecurity`/`relforcerowsecurity`, reset tras commit, reset tras excepción/rollback, rechazo de tenant falsificado en la frontera de aplicación e inmutabilidad de `tenant_id` mediante trigger DB independiente de RLS.

El dictamen global del producto continúa **GO WITH RESTRICTIONS**.
