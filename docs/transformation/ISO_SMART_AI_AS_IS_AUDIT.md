# ISO Smart AI — auditoría AS-IS

Fecha: 2026-08-13. Alcance: commit `fc2a670f`, rama `hardening/p0-p1-enterprise-readiness`, incluyendo cambios locales preexistentes. La auditoría no modificó código, datos ni infraestructura.

## Dictamen ejecutivo

ISO Smart es un monolito Django/DRF + React con capacidades QMS amplias, integración AdminApps endurecida recientemente, y pruebas útiles. No es todavía una plataforma multi-tenant Enterprise ni un runtime IA gobernado: el tenant es un entero de organización filtrado principalmente en aplicación, no hay RLS, hay modelos de negocio duplicados, el contrato API no está formalizado y la provenance IA es parcial.

La base se debe conservar y modularizar. No se justifica un rewrite.

## Inventario

### Backend

- Django 4.2.22, DRF 3.15.2, SimpleJWT, Celery/Redis, Gunicorn, PostgreSQL por defecto y SQLite opt-in/test.
- Apps: `authentication`, `core`, `integration`, `leadership`, `planning`, `operations`, `performance`, `improvement`, `resources` y módulos IA `sca`, `sie`, `asb`, `spm`, `sla`.
- APIs DRF con ViewSets y endpoints IA funcionales. Paginación global y throttling básico.
- Tres conexiones configuradas (`default`, `ai_db`, `audit_db`), sin routers de base visibles ni estrategia transaccional cross-DB documentada.
- Health endpoint existe; no se separan claramente liveness y readiness.

### Dominio y datos

- Activos reutilizables: Organization con `external_id`, documentos, contexto, procesos, stakeholders, riesgos/oportunidades, objetivos, cambios, auditorías, hallazgos, no conformidades, acciones correctivas, aprobaciones y evidencia genérica.
- Duplicaciones materiales: `ProcessMap`, `StakeholderProfile`, `QualityObjective`, `ManagementReview` y `Nonconformity` aparecen en más de un contexto. Esto contradice “un objeto empresarial, muchas relaciones normativas”.
- PKs principales son enteras; la organización/tenant también. No existe estrategia UUID uniforme.
- Tenant isolation se apoya en middleware, serializers/ViewSets y `organization_id`; no hay políticas PostgreSQL RLS.
- Hay escapes concretos P0: varios Assistant ViewSets aceptan `organization_id` writable al sobrescribir el guard de scoping; EvidenceEdge valida el tenant del source pero no el target.
- `ISOClauseConfig` y listas JSON de estándares no modelan Standard → Edition → Clause → RequirementControl versionado.
- `EvidenceNode`/`EvidenceEdge` son una base de grafo, pero no preservan cobertura normativa tipada ni edición/regla histórica.
- `AuditLog`, `AIAuditLog` y logs de gobernanza están fragmentados; no hay garantía criptográfica/inmutabilidad demostrada.

### AdminApps y autenticación

- `AdminAppsAuthBackend` valida credenciales y sincroniza User/Organization/UserProfile; las identidades sincronizadas quedan con password local inutilizable.
- Login valida entitlement de producto antes de emitir acceso. `validate_product_access` falla cerrado por defecto y hay tests de allow/deny.
- El fallback local está limitado por configuración de desarrollo, pero persisten backends locales en la cadena. Deben separarse nítidamente cuentas break-glass/test de usuarios federados.
- `Organization.external_id` es mapping útil; la sincronización no tiene cursor/version/event id ni estado de reconciliación durable.
- `BillingSubscription` y `BillingPayment` locales pueden contradecir el control plane. Requieren reclasificación como proyección/deprecación, no borrado inmediato.

### IA

- Existen motores por capacidad, asistente streaming, vector store/Chroma y logs con `model_version`, prompt/hash en algunos contextos.
- El asistente puede responder con fallback determinista cuando el proveedor falla; esto es aceptable solo si se etiqueta como degradado y no se presenta como recomendación normativa material.
- No hay `AgentDefinition`, `AgentRun`, `AgentDecision`, `RecommendationBasis`, autonomía A0–A4 ni reconstrucción end-to-end uniforme.
- Los human-approval flags y approval records son semillas reutilizables, no un Human Decision Gate común.

### Frontend

- React 19.2, React Router 7.10, Vite 8, Axios, D3/Recharts, Tailwind y contexto i18n propio.
- Cobertura de módulos empresariales amplia y lazy loading en el shell. Servicios API están duplicados por feature y por `services/`.
- No hay TypeScript ni cliente generado de OpenAPI; contratos se duplican en JavaScript.
- Onboarding es una página grande y el servidor conserva un orquestador, pero el flujo visible implementa seis macro-pasos, no la máquina de 17 pasos ni Foundation Gate versionado.
- No existe `NormativeIntelligenceDrawer`. `EvidenceGraphPage` es un activo conceptual reutilizable.
- `OnboardingGuard` desbloquea ante error y usa bypass de sesión; el asistente incorpora conocimiento local hardcoded sin provenance. Ambos son P0 antes de un gate o recomendación real.
- Playwright existe; no se encontró stack unit/component explícito (Vitest/Jest/RTL) ni axe automatizado.

### Infraestructura y repositorio

- Nginx y Gunicorn están configurados; Celery/Redis se asumen locales. No hay artefactos de contenedor propios en ISO Smart.
- Dos workflows GitHub cubren subconjuntos; uno fija Python 3.9 aunque el entorno y evidencia local usan 3.12. CI usa el `requirements.txt` raíz masivo, mientras el backend documenta un requirements mínimo distinto.
- No hay pipeline de migrations, SAST/SCA, secret scanning, contract tests, a11y o RLS.
- 13,473 archivos de `backend/.venv` están versionados (de 14,132 archivos totales). Es deuda P1 de supply-chain/reproducibilidad; retirarlos requiere cambio aislado y revisión.
- `backend/.env` no está versionado, pero debe confirmarse historial de secretos. El SQLite de prueba sí está versionado y tenía cambios locales antes de esta corrida.
- En el ecosistema, AdminApps tiene `.env`/SQLite tracked y MedSupplier una API key default conocida sin guard productivo. No se inspeccionaron secretos; requieren rotación y limpieza autorizadas.

## Reutilización y acción

| Componente | Estado | Acción | Razón | Riesgo |
|---|---|---|---|---|
| Monolito Django/DRF | KEEP + HARDEN | Modularizar por bounded contexts | Reduce riesgo de migración | Medio |
| React shell/routing | KEEP + HARDEN | Adoptar shared design system y contratos tipados | Buena cobertura funcional | Medio |
| AdminApps auth/entitlement | KEEP + HARDEN | Formalizar contrato, errores y reconciliación | Ya falla cerrado | Alto |
| Organization + external_id | MIGRATE | Convertir en Tenant/OrganizationProjection UUID trazable | Semilla de mapping existente | Alto |
| Billing local | DEPRECATE | Proyección read-only hasta reconciliar AdminApps | Doble autoridad potencial | Crítico |
| Process/Stakeholder/Objective/NC duplicados | REFACTOR | Modelo canónico + adaptadores/backfill | Riesgo de divergencia | Alto |
| Document | KEEP + HARDEN | Añadir DocumentVersion, upload security y evidence links | Dominio útil sin versionado completo | Alto |
| EvidenceNode/Edge | REFACTOR | Grafo tipado y versionado en PostgreSQL | Base útil, semántica insuficiente | Alto |
| Audit/Finding/CorrectiveAction | KEEP + HARDEN | Unificar tenant, lifecycle, evidence y effectiveness | Mayor cobertura TO-BE | Medio |
| Motores IA | REFACTOR | Envolver en runtime gobernado común | Lógica reutilizable sin provenance uniforme | Alto |
| Asistente fallback | KEEP + HARDEN | Etiqueta degraded/non-authoritative; bloquear material advice | UX resiliente, riesgo de confianza | Alto |
| Onboarding orchestrator | REFACTOR | State machine backend de 17 pasos | Dirección correcta, cobertura parcial | Alto |
| I18n context | KEEP + HARDEN | Completar cobertura y considerar librería compartida | Base funcional | Medio |
| Servicios API JavaScript | MIGRATE | Cliente TypeScript generado desde OpenAPI | Drift actual | Medio |
| Entornos virtuales versionados | DELETE | Retiro en PR dedicado tras lock reproducible | Bloat/supply chain | Alto |
| SQLite de test versionado | REPLACE | DB efímera/fixtures | Tests mutan artefacto local | Medio |
| Aliases de URL | DEPRECATE | Medir, documentar sunset, retirar por contrato | Compatibilidad actual | Medio |

## Deuda y código temporal

- Comentarios de “fallback”, aliases y workarounds de índices legacy indican migraciones incompletas.
- Documentación histórica contradice a veces el hardening actual; debe marcarse superseded.
- `apply_services.sh`, PIDs y archivos de prueba raíz requieren clasificación antes de retirar.
- No se encontró evidencia de dead-code analysis; por seguridad, nada se etiqueta DELETE excepto artefactos de entorno, y aun ellos requieren PR dedicado.

## Limitaciones

Los diez artefactos TO-BE no estaban disponibles. Este AS-IS sí es válido; la validación final de campos/cardinalidades y de los 17 pasos queda condicionada al intake documentado en `source-artifacts/README.md`.

**Addendum 2026-08-13:** esta limitación histórica se cerró después de la auditoría: 10/10 artefactos fueron incorporados, validados y reconciliados en `SOURCE_ARTIFACT_MANIFEST.md` e `ISO_SMART_AI_SOURCE_RECONCILIATION.md`. Los hallazgos AS-IS de código no cambian por ese intake.
