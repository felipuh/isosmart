# Hardening P0/P1 Report - ISO Smart

Fecha de ejecucion principal: 2026-07-02 America/Costa_Rica.
Reporte actualizado: 2026-07-03.
Branch revisado: `hardening/p0-enterprise-readiness-20260702`.

## Alcance

- Backend Django en `backend/`.
- Frontend Vite en `frontend/`.
- No se modificaron archivos `.env` reales.
- No se ejecuto `sudo`.
- No se realizaron commits desde esta documentacion.

## Cambios aplicados

- `DJANGO_ENV` queda como variable canonica, con compatibilidad de lectura para `ENVIRONMENT`.
- Hosts locales y bypass de autenticacion local solo se habilitan en entorno de desarrollo.
- `ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS` requiere desarrollo y flag explicito.
- `.env.example` deja el bypass local en `False` por defecto.
- `SECURE_SSL_REDIRECT`, HSTS y proxy SSL quedan controlados por variables de entorno.
- `settings_test.py` desactiva redirects/cookies secure productivos para evitar falsos 301 en la suite local.
- Se reemplazaron `ModelSerializer.fields = "__all__"` por campos explicitos en serializers de `core`, `integration` y `performance`.
- Se agregaron guardrails de seguridad para serializers y bypass local.
- Se agrego `backend/requirements.txt` minimo para reproducir el backend sin depender del freeze raiz.
- El frontend ahora documenta `VITE_API_BASE_URL=/api` y `VITE_LOCAL_AUTH_BYPASS=0` en `frontend/.env.example`.
- El cliente API frontend usa `VITE_API_BASE_URL` con fallback seguro a `/api`.

## Estado

Resultado: implementacion P0/P1 validada para ISO Smart.

Nota operativa: el `requirements.txt` raiz contiene dependencias incompatibles con Python 3.9 y paquetes no resolubles desde indice estandar. Para backend se valido con Python 3.12 y `backend/requirements.txt`.
