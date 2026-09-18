# ISO Smart AI — migration roadmap

No se asignan fechas sin capacidad de equipo. El orden es por dependencias y gates.

## Fase 0 — intake y contención

1. Ingresar los diez artefactos, registrar hashes y reconciliar la matriz/ADRs.
2. Corregir aisladamente tenant escape en Assistant y EvidenceEdge; hacer audit de endpoints análogos.
3. Hacer onboarding y assistant fallback fail-closed/degraded.
4. Congelar nueva autoridad local de billing y documentar AdminApps contract tests.
5. Alinear Python/Node/requirements en CI sin upgrades funcionales; desactivar telemetría test.

Gate: P0 locales cerrados, artifacts accepted, tests existentes verdes. Rollback: revertir feature flags/adapters; no schema destructivo.

**Estado verificado 2026-08-13:** gate cumplido para pasar a una foundation limitada: 10/10 artifacts VALID/reconciliados; cuatro P0 locales mitigados; 98 tests backend, lint/build y Playwright P0 reportados PASS. Permanecen restricciones Enterprise (RLS no ejecutada, contratos AdminApps y PostgreSQL productivo pendientes).

## Fase 1 — foundations

Primera vertical slice autorizable, sin migrar dominio existente:

1. PostgreSQL 18.6 efímero reproducible, desechable y dedicado exclusivamente a la corrida + roles owner/migrator/app/worker/read-only. Preferir harness nativo; si no existe, crear contenedor Docker/Podman único; nunca reutilizar bases persistentes o compartidas. Registrar sin secretos engine, versión exacta, puerto, base, roles y comandos de creación/destrucción, y probar teardown.
2. `TenantProjection` skeleton y como máximo una tabla hija sintética/no destructiva, con external ID/source version/event/reconcile fields.
3. Tenant context transaction-scoped desde resolver server-side confiable y RLS `ENABLE+FORCE` con policies SELECT/INSERT/UPDATE/DELETE; pruebas A/B/no tenant, spoofing, commit/rollback sobre conexión reutilizada, worker y raw SQL.
4. Trigger DB independiente para inmutabilidad de `tenant_id`; forward/backward migration tests y assertions reales de `pg_roles`/`pg_class` para superuser, ownership, BYPASSRLS y ambos flags RLS. No backfill, dual-write, AdminApps write ni cambio productivo.

Slices posteriores, sólo tras el POC: baseline OpenAPI de comportamiento actual; source mapping compatible; DomainEvent/Outbox/ConsumerReceipt sin consumidores críticos; ImmutableAuditLog append-only y trace propagation.

Gate: contract diff limpio, migration forward/backward, entorno efímero exclusivo creado y destruido con evidencia sanitizada, los seis security assertions bloqueantes de la matriz ejecutados sin skips en PostgreSQL 18.6 real, RLS negative tests y outbox duplicate/retry tests. Rollback: reads legados + detener dispatcher; conservar filas nuevas.

## Fase 2 — normative and evidence spine

1. Standard/Edition/Clause/RequirementControl.
2. KnowledgeLayer/Rule/Binding y StandardPack.
3. DocumentVersion/Evidence/EvidenceCoverage.
4. Typed graph views/traversals y explanations API.
5. NormativeIntelligenceDrawer con progressive disclosure.

Gate: edición/regla/evidencia histórica inmutable; traversal SLO medido; no graph DB. Rollback: feature flag a UI/reads legados, sin borrar spine.

## Fase 3 — canonical Harmonized Core

Orden de agregado: TenantProjection/Organization/Site → Process/StakeholderRequirement → Risk/Opportunity/Objective/Change → NC/CA/Audit/Finding. Para cada uno: expand, source mapping, dual read, backfill, reconciliation, switch, stop legacy writes, deprecate posterior.

Gate por agregado: 100% de source rows clasificadas (migrada/conflicto explícito), constraints tenant, API parity, rollback probado. Nunca dedupe por texto solamente.

## Fase 4 — onboarding y learning

1. Workflow definitions/instances/transitions backend-authoritative con 17 pasos exactos del artefacto.
2. LearningPath/QuestionBank/QuizAttempt/ConceptMastery versionados por edición.
3. Foundation Gate, score/retries/adaptación role/industry y delta learning.
4. Frontend como renderer de estado/acciones.

Gate: transitions/property tests, fail-closed, edition delta fixtures, E2E baseline publication. Rollback: mantener workflow previo read-only; no marcar gates completos automáticamente.

## Fase 5 — governed intelligence

1. ModelPolicy + AgentDefinition/Run/Decision + Recommendation/Basis.
2. Adaptar motores existentes a pipeline común.
3. Human Decision Gate/ActionExecution/EffectivenessCheck.
4. A0/A1, luego A2/A3. A4 solo en caso separado con guardrails aprobados.

Gate: provenance completeness 100% para recomendaciones materiales, policy tests, approvals/replay, action rollback. Kill switch por agent/policy/tenant.

## Fase 6 — hardening y retiro

1. Completar shared design system, TypeScript, query/cache, a11y y timezone.
2. Upload/object storage security, observabilidad, backup/PITR/restore/DR drills.
3. Retirar `.venv`/SQLite del repo mediante PR dedicado con lock/SBOM reproducible.
4. Retirar aliases/modelos/tablas solo tras telemetry cero, retention y backup aprobado.

Gate: staging production-like, restore/migration rollback drill, SLO/alerts y security regression. Deployment sigue fuera del alcance hasta autorización.

## Secuencia segura de upgrades

1. Inventario/lock reproducible y CI matrix en versiones actuales.
2. Unificar Python 3.12 y Node 20 LTS (o baseline ecosistema aprobada) antes de framework upgrades.
3. Patch/minor compatibles por familia, un cambio por PR con AdminApps/MedSupplier contracts.
4. PostgreSQL driver (`psycopg` 3) en adaptación separada.
5. Django 4.2 LTS → LTS común aprobada solo tras deprecation audit; DRF después.
6. React/Vite/router/design system como conjunto ecosistémico, nunca ISO Smart aislado.

Cada upgrade mantiene rollback por lockfile/image anterior y no se mezcla con migración de dominio.
