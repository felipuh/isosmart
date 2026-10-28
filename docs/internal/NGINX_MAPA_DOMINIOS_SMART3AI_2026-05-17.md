# Mapa Operativo Nginx Smart3AI (2026-05-17)

## Objetivo
Este documento centraliza el enrutamiento de dominios de Smart3AI para evitar conflictos de `server_name`, errores `502` y fallos de WebSocket (HMR) en desarrollo.

## Archivo de configuracion activo
- `/etc/nginx/conf.d/smart3ai_portfolio.conf`

## Reglas clave (estado validado)
- `isosmart.smart3ai.local` se atiende en un bloque dedicado y **sin** alias `isosmart.local`.
- `isosmart.local` queda atendido por el bloque legacy de `isosmart-all.conf`.
- En `isosmart.smart3ai.local`, el `location /` tiene soporte WebSocket:
  - `proxy_set_header Upgrade $http_upgrade;`
  - `proxy_set_header Connection $connection_upgrade;`
  - `proxy_http_version 1.1;`
- Frontend de IsoSmart via proxy en `127.0.0.1:5173`.
- Backend API de IsoSmart via proxy en `127.0.0.1:8001`.

## Mapa de dominios y upstreams

### AdminApps / SSO
- Dominios:
  - `sso.smart3ai.local`
  - `adminapps.smart3ai.local`
- Frontend upstream:
  - `smart3ai_adminapps_frontend` -> `127.0.0.1:3000`
- API upstream:
  - `smart3ai_adminapps_backend` -> `127.0.0.1:8000`

### IsoSmart (smart3ai)
- Dominio:
  - `isosmart.smart3ai.local`
- Frontend upstream:
  - `smart3ai_isosmart_frontend` -> `127.0.0.1:5173`
- API upstream:
  - `smart3ai_isosmart_backend` -> `127.0.0.1:8001`
- Requisito importante:
  - Mantener headers de upgrade WS en `location /` para HMR de Vite.

### VulnGuard IA
- Dominio:
  - `vulnguard.smart3ai.local`
- Frontend upstream:
  - `smart3ai_vulnguard_frontend` -> `127.0.0.1:5174`
- API upstream:
  - `smart3ai_vulnguard_backend` -> `127.0.0.1:8002`

### Control Horas Desarrollo
- Dominio:
  - `horas.smart3ai.local`
- Frontend upstream:
  - `smart3ai_control_horas_frontend` -> `127.0.0.1:5175`
- API upstream:
  - `smart3ai_control_horas_backend` -> `127.0.0.1:3002`

### Sistema Control Condominios
- Dominio:
  - `condominios.smart3ai.local`
- Frontend upstream:
  - `smart3ai_condominios_frontend` -> `127.0.0.1:5176`
- API upstream:
  - `smart3ai_condominios_backend` -> `127.0.0.1:3003`

### BOT Cryptp
- Dominios:
  - `cryptp.smart3ai.local`
  - `bot.smart3ai.local`
- Upstream principal:
  - `smart3ai_bot_cryptp_backend` -> `127.0.0.1:8100`

### Landing / Portfolio
- Dominios:
  - `smart3ai.local`
  - `landing.smart3ai.local`
- Frontend upstream:
  - `smart3ai_landing_frontend` -> `127.0.0.1:4173`

## Checklist rapido de cambios Nginx
1. Editar `/etc/nginx/conf.d/smart3ai_portfolio.conf`.
2. Validar sintaxis:
   - `sudo nginx -t`
3. Recargar:
   - `sudo nginx -s reload`
4. Verificar conflictos y server_name efectivos:
   - `sudo nginx -T 2>&1 | grep -i "conflicting server name\|server_name .*isosmart"`
5. Verificar puertos esperados:
   - `ss -lptn | grep -E '(:3000|:5173|:8000|:8001)'`

## Diagnostico express
- Si aparece `502` en `isosmart.smart3ai.local`:
  - Confirmar `5173` y `8001` activos.
  - Confirmar `proxy_pass` correcto en bloque `isosmart.smart3ai.local`.
- Si aparece error de Vite HMR WebSocket:
  - Revisar headers de upgrade WS en `location /` del bloque `isosmart.smart3ai.local`.
  - Confirmar que Vite este levantado en `5173`.

## Nota de gobierno de configuracion
- Evitar duplicar `server_name` entre archivos activos de `/etc/nginx/conf.d/*.conf`.
- Si se requiere alias compartido (`isosmart.local`), definir un unico bloque propietario para ese host.
