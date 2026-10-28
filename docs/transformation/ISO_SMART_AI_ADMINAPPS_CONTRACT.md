# ISO Smart AI — contrato y boundary AdminApps

## Regla

AdminApps es control plane. ISO Smart no crea una autoridad paralela para identidad, acceso de producto, tenant global, entitlements o billing/subscription. Los datos QMS pertenecen a ISO Smart.

La reconciliación de los artefactos oficiales confirma una entidad lógica `Tenant` y una entidad `User`, pero el DDL de referencia no es autoridad de integración. En Smart3AI se materializan como `TenantProjection` y `UserProjection`; `Organization` continúa como agregado QMS.

## Matriz system-of-record y sincronización

| Concept | System of record | Local representation | External ID | Local ID | Sync direction | Source version/event | Last sync/reconciliation | Failure behavior |
|---|---|---|---|---|---|---|---|---|
| Identity | AdminApps/IdP | auth principal + UserProjection sin password utilizable | subject/User UUID | UUID interno | AdminApps → ISO; claims por sesión | issuer/version + event ID | last sync, status, error | 401 inválido; 503 si validación obligatoria no disponible |
| Tenant | AdminApps | TenantProjection | adminapps tenant UUID | UUID interno RLS | AdminApps → ISO | monotónica + event ID | synced/reconciled timestamps + drift | Unknown/inactive/drift: 503/403 fail-closed |
| Users | AdminApps | UserProjection | adminapps user UUID | UUID interno | AdminApps → ISO | source version/event | active/tombstone/reconcile | Usuario desconocido/revocado: deny |
| Global roles/MFA | AdminApps | claim/RoleProjection snapshot | role/policy ID | opcional local | AdminApps → ISO | policy version | freshness/status | Mapping desconocido/stale crítico: 403/503 |
| QMS roles | ISO Smart | RoleAssignment | user projection ID | assignment UUID | ISO local; nunca eleva rol global | local aggregate version/event | audit timestamp | Default deny; requiere tenant y scope |
| Product entitlement | AdminApps | EntitlementProjection/cache | entitlement ID | UUID interno | AdminApps → ISO + validate | entitlement version/event/expiry | evaluated/expires/reconciled | Deny=403; no validable cuando fresco requerido=503 |
| Plans | AdminApps | Plan snapshot/read model | plan code/version | opcional | AdminApps → ISO | catalog/version | last sync | No habilitar feature desconocida |
| Subscription | AdminApps | SubscriptionProjection | subscription UUID | UUID interno | AdminApps → ISO | version/event | status/freshness | No inferir activación local; stale crítico=503 |
| Billing status | AdminApps/payment authority | mínimo snapshot de estado/referencia | payment/subscription ref | opcional | AdminApps → ISO | signed event ID/version | receipt + reconcile | Nunca confirmar desde redirect/UI; conflicto=409 |
| Provisioning authority | AdminApps inicia | ProvisioningProjection/checkpoints de dominio | provisioning request/event ID | UUID interno | AdminApps → ISO; ISO reporta resultado | event/schema/attempt | step/status/error | Idempotent retry; partial no activa tenant |
| Organization QMS | ISO Smart | Organization/Site | tenant external sólo como vínculo | UUIDs ISO | ISO local | aggregate version/event | local audit | No escribe TenantProjection authority |

`source_version`, `source_event_id`, `last_synced_at`, `last_reconciled_at`, `reconciliation_status` y error code son obligatorios en las proyecciones donde aplique. Nunca se cambia un external ID para “resolver” drift.

| System of Record | Proyección ISO Smart | Ownership local | Sync mechanism objetivo | Failure behavior |
|---|---|---|---|---|
| AdminApps User/Identity | UserProjection + auth user sin password usable | Preferencias/QMS assignments | SSO/JWT + webhook/outbox + reconcile | Token inválido/indisponible crítico: deny |
| AdminApps Tenant | TenantProjection (external UUID, status, version) | Organization/Site QMS | tenant.provisioned + idempotent upsert | Tenant desconocido/inactivo: deny |
| AdminApps Product/Entitlement | EntitlementProjection con expiración/source version | Ninguno | validate endpoint + signed event/cache | Rechazo: 403; no validable: 503; nunca allow |
| AdminApps Billing/Subscription | Read model mínimo | Ninguno | payment.confirmed/subscription events + reconcile | No inferir pago local; conservar último estado solo bajo TTL/policy |
| ISO Smart Organization QMS | N/A | Nombre operativo, sites, QMS config | Comandos ISO Smart ligados a tenant | No altera tenant global |
| ISO Smart roles QMS | Claims/assignment local acotado | Permisos dentro del producto | Mapping explícito y ABAC | Default deny si mapping desconocido |

## AS-IS

`AdminAppsClient`, `AdminAppsAuthBackend`, `Smart3AISSOAuthentication`, `ModuleAccessMiddleware` y `AdminAppsSyncMiddleware` forman una integración real. `Organization.external_id` y passwords inutilizables de usuarios sincronizados son decisiones sanas. `validate_product_access` falla cerrado por defecto y el login tiene pruebas de allow/deny.

Gaps:

- Backends locales permanecen habilitados globalmente; documentar y aislar break-glass/test.
- Sync por request no guarda source version/event ID, cursor, last_success/error ni reconciliación durable.
- Cache invalidation/TTL y comportamiento ante revocación no tienen contrato versionado.
- Billing local incluye confirmación/evidencia y puede competir con AdminApps.
- El sync completo hace upsert pero no tombstone/revocación de proyecciones ausentes; añadir source version, cursor, last_synced/status/error y reconciliación durable.
- No hay OpenAPI/schema compartido ni consumer contract tests entre repositorios.

## Contrato objetivo mínimo

- Identificadores externos UUID opacos; nunca reinterpretar un ID local como externo salvo adapter legacy auditado.
- Requests llevan trace/correlation ID, product code, organization external ID y versión del contrato.
- Responses de acceso distinguen `allowed`, `reason`, `billing_status`, `entitlement_version`, `evaluated_at`, `expires_at` y source.
- Webhooks/eventos firmados incluyen ID único, timestamp, schema version y replay protection. Inbox deduplica antes de efecto.
- Upserts son idempotentes; cambios de tenant/user no reasignan silenciosamente datos QMS.
- 401 = identidad inválida; 403 = autorización rechazada; 503 = autoridad obligatoria no validable. Todos accionables y sin leakage sensible.
- 409 = source version/idempotency conflict, provisioning incompatible o intento de reasignación; no se usa para ocultar un 403.

## Semántica de errores y freshness

- **401:** autenticación ausente/expirada/firma, issuer o audience inválidos. No informa si el tenant existe.
- **403:** identidad válida, decisión vigente de entitlement/role/policy negativa. Una denegación cacheada nunca se convierte en allow.
- **409:** mismo event/idempotency key con payload distinto, source version concurrente, transition no permitida o external ID ya vinculado a otra projection.
- **503:** control plane obligatorio no alcanzable o response no verificable, projection `drifted`, freshness excedida para la operación o reconciliación requerida. Incluye retry metadata segura.

La freshness se define por caso de uso, no por un TTL global. Lecturas de bajo impacto pueden usar una decisión positiva vigente; cambios de permisos, export, activación de agente, aprobación material y acciones A3/A4 requieren validación fresca o invalidación dirigida. El TTL observado de 300 s permanece no aprobado.

## Eventos y reconciliación

Entradas mínimas: `tenant.provisioned`, `tenant.updated`, `tenant.suspended`, `user.updated/revoked`, `entitlement.changed`, `subscription.changed` y `payment.confirmed`. El contrato tenant v1 usa el endpoint de servicio autenticado por API key sobre HTTPS, `event_id`, `source_version`, `schema_version` y recibo persistente para deduplicación. Los eventos adicionales permanecen trabajo de contrato.

Para tenant v1, `apps.organizations.Organization.id` es el UUID global canónico,
inmutable, recibido como `adminapps_tenant_id`; `TenantProjection.id` y
`qms.Organization.id` son UUID locales distintos. La versión inicial es 1 y
crece una vez por cambio de nombre o estado. `trial|active` se proyecta a
`active`; `inactive|suspended` a `suspended`. El nombre es una instantánea
mutable. Suspender no borra el tenant ni sus organizaciones QMS. El recibo
`eventing.adminapps_ingress_receipt` preserva la historia de eventos aunque
una versión posterior reemplace `TenantProjection.source_event_id`.

Reconcile periódico es un pull de autoridad AdminApps hacia projections, con reportes `in_sync/stale/missing/version_conflict/unavailable`; ISO Smart sólo reporta estado de provisioning y señales de producto permitidas en dirección inversa. No sincroniza datos QMS ni billing authority hacia AdminApps por inferencia.

## Cache y degradación

Una decisión positiva puede cachearse solo por TTL corto definido por riesgo y con versión/revocación; una denegación no se transforma en allow. Operaciones de alto impacto revalidan. Si AdminApps no responde y la policy exige validación fresca, el sistema falla cerrado. Fallback demo/test debe estar deshabilitado por construcción en producción, visible en health/telemetry y cubierto por tests.

El TTL observado es 300 s; no se aprueba como baseline. Definir max-staleness por caso, invalidación dirigida por eventos y bypass de cache para acciones de alto impacto.

## Migración de billing local

1. Congelar nuevas capacidades locales; inventariar consumidores.
2. Reconciliar subscription/payment IDs con AdminApps y producir reporte de conflictos.
3. Convertir UI/endpoints a read model AdminApps detrás de feature flag.
4. Bloquear confirmación local, observar y conservar historial como snapshot de migración.
5. Deprecar tablas/endpoints solo tras ventana de rollback y aprobación de data owner.

No se elimina historial de pagos en esta transformación.
