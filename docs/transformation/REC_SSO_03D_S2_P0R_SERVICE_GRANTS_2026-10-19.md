# REC-SSO-03D-S2-P0R — adaptador de grants (ISO_SMART)

2026-10-19. Cambio local, sin provisión ni despliegue. PRODUCTION_READY = FALSE.

`backend/integration/client.py` consulta AdminApps en cada lectura `/organizations/...` y `/user/`,
aun si el caller solicita caché. Un HTTP 401/403 conserva la denegación (`allowed=false`,
`authorization_denied=true`) sin fallback local. El helper de módulos rechaza datos de una respuesta
denegada. No se ampliaron permisos ni grants. El fallback de transporte también se bloquea cuando
IS_PRODUCTION=true, aun si ALLOW_LOCAL_AUTH_FALLBACK está habilitado.

El servidor requiere una credencial hashed_v1 autenticable y activa, y
`INTEGRATION_API_GRANTS[credential_id]` con listas explícitas de operaciones, UUID centrales de tenant
y `product_codes: ["ISO_SMART"]`. No se provisionó ninguna clave, tenant o grant real.
El caller de `get_user` debe aportar organization_id. SSOClient no concede este acceso de datos.
Los módulos legacy sin mapping de producto adjudicado permanecen omitidos/denegados.

Se ejecutó este adaptador real hacia los siete handlers Django de AdminApps con transporte/ORM
simulados y autenticación de hash real para valores sintéticos. ALLOW propio y DENY por credencial,
grant, tenant y producto; ninguna DB/red real. El lookup de external_id fue simulado. No se declara
E2E, compatibilidad de todos los callers ni provisión de producción. Las suites D/B/sesión pasan;
A/C/H originales conservan los fallos de fixtures anteriores al contrato B.

Contrato y evidencia central: `/home/felipe/proyectos/adminapps/docs/security/REC-SSO-03D-S2-P0R/`:
`REPORT.md`, `CONTRACT.md`, `p0r-contract.openapi.json`, `p0r.log`, `test-summary.json`.

Se preservan S3-IMP-01, S3_DECISION_02A_NOT_CLOSED, PHASE31_5 = EXECUTION_HELD, REC-2FA-04,
REC-SSO-02, REC-SSO-03A, REC-SSO-03B-CH y
DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED. Sin migraciones, commit ni push.
