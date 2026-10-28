# ISO Smart AI — reglas operativas

- Evolucionar incrementalmente; no hacer big-bang rewrite ni borrar historia normativa.
- AdminApps es system of record de identidad, acceso de producto, entitlements, tenant global y billing cuando aplique. Las copias locales son proyecciones trazables por `external_id`.
- Toda autorización crítica de AdminApps falla cerrada. El fallback local solo puede existir en test/demo, explícito, observable y prohibido en producción.
- Un objeto empresarial sirve a muchas normas. No duplicar Organization, Stakeholder, Process, Risk, Opportunity, Objective, Change, Evidence, Nonconformity ni CorrectiveAction por edición o cláusula.
- PostgreSQL es la fuente transaccional. Toda tabla tenant-scoped debe tener defensa de aplicación y RLS; probar aislamiento. Documentar tablas globales.
- Preservar ediciones, reglas, provenance y auditoría histórica. Migraciones expand/contract, reversibles, con backfill verificable y rollback; nunca migraciones destructivas directas.
- Trabajar contract-first. Actualizar OpenAPI, errores, permisos, tenant scope, idempotencia y efectos de auditoría/eventos junto con cada caso de uso. Derivar el cliente TypeScript cuando sea posible.
- Eventos críticos usan transacción + outbox; consumers idempotentes, retry-safe y con `trace_id`.
- Ninguna recomendación IA material sin evidencia, versiones, regla/prompt/modelo, confianza, supuestos, decisión humana y resultado. A4 solo con guardrails reversibles y preautorizados.
- Reutilizar el design system compartido antes de crear componentes paralelos. UX accesible, i18n, timezone-aware, con estados loading/empty/degraded/error.
- Cada cambio exige pruebas proporcionales: dominio, constraints/RLS, permisos/AdminApps, contratos, migraciones, frontend/a11y y seguridad. Separar reglas, retrieval, inferencia, policy y aprobación.
- No tocar producción, DNS, certificados, secretos ni datos reales; no desplegar salvo autorización explícita. No introducir datos falsos en producción.
- Mantener `docs/transformation/` y ADRs sincronizados con decisiones estructurales. Registrar comandos y resultados; no declarar verificado lo no ejecutado.
- Preservar cambios locales no relacionados. Antes de modificar integración, esquema o componentes compartidos, inspeccionar consumidores AdminApps, MedSupplier y design-system.
