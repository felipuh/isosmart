# ISO Smart AI — registro de riesgos

Escala: P0 bloquea datos/IA reales o rompe boundary; P1 debe resolverse antes de piloto Enterprise; P2 antes de escala; P3 mejora planificada.

| ID | Pri. | Riesgo/evidencia | Impacto | Mitigación / owner sugerido | Gate |
|---|---|---|---|---|---|
| R-001 | P0 | **CERRADO 2026-08-13:** 10/10 artefactos presentes, parseables, hashes registrados y reconciliados | Riesgo de fuente de paquete mitigado | Mantener hashes y originals read-only; Product/Architecture | PASS para design; recheck antes de implementation |
| R-002 | P0 | Assistant ViewSets aceptan organization_id writable y omiten mixin al guardar | Tenant escape/IDOR | Forzar tenant server-side, validar relaciones, tests negativos; Backend/Security | Hotfix aislado |
| R-003 | P0 | EvidenceEdge valida source pero no target tenant | Grafo cross-tenant | Validación bilateral + constraint/service + tests; Backend/Data | Hotfix aislado |
| R-004 | P0 | OnboardingGuard hace fail-open ante error y bypass por sesión | Gate evadible | Backend authoritative, deny/degraded, remover bypass; Frontend/Security | Antes de baseline gate |
| R-005 | P0 | Fallback local del asistente se presenta como respuesta normativa | Consejo sin provenance | Estado degraded/non-authoritative; bloquear material recommendation; AI/UX | Antes de usuarios reales |
| R-006 | P0 | Sin PostgreSQL RLS; tenant = filtros ORM/int suelto | Exposición masiva cross-tenant | Tenant UUID/context/FORCE RLS/tests Postgres; Data/Security | Antes de multi-tenant Enterprise |
| R-007 | P0 | Doble autoridad billing AdminApps/local | Acceso/cobro contradictorio | Reconcile y convertir a proyección; AdminApps/Product | Antes de billing real |
| R-008 | P0 | AdminApps sync permite continuar en outage para checks no diferenciados | Acceso potencialmente stale | Separar sync informativo de authorization; 403/503 fail-closed; Integration | Contract gate |
| R-009 | P0 | Sin versionado normativo/evidence coverage | Destruir/reinterpretar historia | Edition/rule/evidence snapshots append-only; Data/Compliance | Antes de migrar evidencia |
| R-010 | P0 | IA sin AgentRun/Basis/ModelPolicy común | No reconstruible/auditable | Runtime gobernado + Human Gate; AI Governance | Antes de recomendación material |
| R-011 | P0 | Sin outbox; indexing borra antes de reconstruir | Evento perdido/índice inconsistente | Outbox, version staging/activate, idempotencia; Platform | Antes de workflows críticos |
| R-012 | P1 | Objetos empresariales duplicados | Divergencia y doble conteo | Canónicos + source mappings + backfill reconcile; Domain/Data | Antes de nuevos módulos |
| R-013 | P1 | Document delete físico y upload sin MIME/malware/hashes | Pérdida histórica/malware | DocumentVersion, retention/quarantine/scanner; Security/Data | Antes de evidencia productiva |
| R-014 | P1 | Audit logs mutables y API CRUD | Tampering | Append-only DB grants/hash chain; API read-only; Security | Antes de auditoría externa |
| R-015 | P1 | Códigos unique globales sin tenant | Colisiones/DoS entre tenants | Audit/backfill → composite unique; Data | Migration gate |
| R-016 | P1 | Métricas ISO calculadas en navegador y fallos convertidos a cero | Indicadores engañosos | Backend EvidenceCoverage; degraded states; Product | Antes de executive dashboard |
| R-017 | P1 | JWT access/refresh en localStorage | XSS token theft | Alinear BFF/HttpOnly con AdminApps + CSP; Security | Antes de producción |
| R-018 | P1 | Modal común sin semántica/focus/Escape | WCAG/operabilidad | Migrar a shared dialog y axe tests; UX | Accessibility gate |
| R-019 | P1 | No OpenAPI/TypeScript generated client | Drift/breaking changes | ADR-0006 + contract diff; API/Frontend | Antes de ampliar API |
| R-020 | P1 | CI Python 3.9 vs runtime 3.12 y requirements divergentes | Builds no reproducibles | Baseline/lock único, matrix temporal; Platform | Antes de upgrade |
| R-021 | P1 | 13,473 archivos `.venv` versionados | Supply chain/bloat | PR dedicado, SBOM/lock y limpieza no destructiva | Antes de release pipeline |
| R-022 | P1 | Tests SQLite; Chroma intenta telemetría externa | No prueba RLS y fuga/flake CI | Postgres CI + disable telemetry; QA/Platform | Test foundation |
| R-023 | P1 | Tres DB configuradas sin routers | Supuesta separación inexistente | Consolidar inicialmente o justificar/operar routers | Architecture gate |
| R-024 | P2 | i18n catálogo monolítico y timezone inconsistente | UX/traducciones erróneas | Namespaces + org timezone formatter | UX quality gate |
| R-025 | P2 | Sin DR/PITR/restore evidence local | Recuperación desconocida | Definir RPO/RTO y restore drills | Production readiness |
| R-026 | P0 | LEEME/DOCX refieren un FDIS normativo “adjunto”, pero no forma parte de los 10 artefactos del paquete | Publicar controles normativos desde paráfrasis o fuente no licenciada/incorrecta | Obtener fuente controlada/licenciada, registrar edition/hash y curator approval | Antes de cargar/publicar normative data real |
| R-027 | P0 | DDL cubre 24/43 entidades y contiene cero políticas RLS | Falsa sensación de schema Enterprise | Tratar DDL como referencia; primera slice PostgreSQL efímera + TenantProjection + RLS POC | Antes de models/migrations de dominio |
| R-028 | P0 | Mermaid/Draw.io omiten 2/17 etapas (`Subscription Activation`, `Value Discovery`) | Implementar onboarding visual incompleto | DOCX/XLSX/JSON son autoridad; contract/state machine usa 17 | Antes de onboarding implementation |
| R-029 | P0 | Contratos/eventos AdminApps de tenant/user/entitlement/subscription no están acordados entre repos | Projection drift o fail-open | Provider/consumer contract, source version/event, reconcile, 401/403/409/503 | Antes de activar projection productiva |
| R-030 | P1 | PostgreSQL server productivo no inventariado; Design Gate evaluó target 18.4 y la revalidación pre-implementación corrigió el patch target a 18.6 | Incompatibilidad driver/pool/backup/platform | Efímero 18.6; inventario/certificación/restore antes de prod | Foundation restriction |

## Riesgo residual aceptable en discovery

### Estado de la contención P0 local — 2026-08-13

| Riesgo | Estado | Evidencia de mitigación | Riesgo residual |
|---|---|---|---|
| R-002 Assistant mass assignment/IDOR | **Mitigated** | Tenant derivado sólo del JWT/request autorizado; campos de organización y actor read-only; querysets y relaciones tenant-scoped; regresiones create/update/list/retrieve/delete y referencias feedback A/B. | Defensa en aplicación/SQLite; RLS permanece abierto en R-006. |
| R-003 EvidenceEdge cross-tenant | **Mitigated** | Queryset exige source y target del tenant activo; ambos campos relacionales usan queryset tenant-scoped; create/update A/B y retrieve/update/delete de edge B cubiertos. | No existe todavía constraint/RLS de base; queda cubierto por R-006 y la futura foundation PostgreSQL. |
| R-004 Onboarding fail-open | **Mitigated** | Máquina explícita loading/completed/incomplete/degraded; error, timeout y payload inválido bloquean; no se consulta browser storage para autorizar; retry vuelve al servidor. Playwright mockeado cubre estados críticos. | La autoridad sigue siendo el endpoint actual; el onboarding de 17 pasos/Foundation Gate continúa fuera de alcance. |
| R-005 fallback normativo local | **Mitigated** | Se retiró `KNOWLEDGE_BASE` como fallback; backend y frontend emiten degradación explícita sin recomendación/análisis; pruebas backend y Playwright negativas. | El runtime gobernado/provenance material sigue bloqueado por R-010; no se autoriza IA material. |

R-014 queda **partially mitigated**: la API pública de `AssistantAuditLog` es read-only y la escritura interna ORM continúa operativa, pero inmutabilidad de base, grants append-only y hash chain pertenecen a una fase posterior.

La decisión de no-leakage para referencias relacionadas es: `404` para lookup de recursos/edges fuera del queryset tenant-scoped; `400` genérico para FKs de create/update porque DRF valida el payload antes del lookup del recurso. Referencias inexistentes y cross-tenant producen el mismo mensaje por campo y nunca incluyen organización, propietario ni atributos privados.

Los cuatro P0 locales de esta corrida están mitigados con pruebas. Persisten otros P0 Enterprise del registro (RLS ejecutable aún no probado, authority contracts, versionado, runtime y outbox), por lo que no existe autorización para producción/deploy ni para datos/IA materiales.

### Estado posterior al intake y design gate de datos — 2026-08-13

R-001 está cerrado: `SOURCE_ARTIFACT_MANIFEST.md` registra 10/10 VALID y la reconciliación cuantifica las diferencias. El riesgo de fuente normativa licenciada se separa como R-026; no bloquea una foundation sintética/no normativa, sí bloquea publicar controles reales. R-027–R-030 mantienen restricciones para implementación: RLS aún no fue ejecutada, los contratos AdminApps no están acordados y el servidor productivo no está inventariado. Por tanto, una primera slice efímera y no destructiva puede avanzar; migración masiva/productiva no.
