# Security Notes - ISO Smart

## Configuracion

- Produccion debe definir `DJANGO_ENV=production`.
- No confiar en `ENVIRONMENT` para nuevos despliegues; queda solo como compatibilidad.
- Los alias locales (`127.0.0.1`, `localhost`, `testserver`) no se agregan automaticamente en produccion.
- `ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS=True` solo tiene efecto en desarrollo.
- `.env.example` documenta `ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS=False` por defecto.
- `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS` y `SECURE_HSTS_PRELOAD` quedan documentados para produccion.
- `settings_test.py` fuerza `SECURE_SSL_REDIRECT=False` para que las pruebas validen endpoints y permisos sin redireccion HTTPS.
- `frontend/.env.example` deja `VITE_LOCAL_AUTH_BYPASS=0` por defecto.
- `VITE_API_BASE_URL` permite configurar el backend en frontend sin hardcodear dominios.

## Serializacion

- Los serializers revisados ya no usan `fields = "__all__"`.
- El guardrail `backend/core/tests_security_guardrails.py` debe mantenerse en CI.

## Dependencias

- `backend/requirements.txt` contiene el set backend reproducible validado.
- El freeze raiz debe tratarse como deuda operativa separada porque mezcla dependencias de multiples runtimes.

## Pendientes recomendados

- Consolidar strategy de dependencias entre root y backend.
- Ejecutar validacion de entorno productivo real con variables finales de deploy.
- Migrar almacenamiento de JWT en `localStorage` hacia cookies HttpOnly/SameSite en una fase coordinada backend/frontend.
