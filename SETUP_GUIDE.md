# IsoSmart - Setup Completo

## Estado Actual ✓

Todos los módulos están funcionales y listos para ser accedidos.

### Servicios en Ejecución

- **Backend (Django)**: Puerto 8001 (http://localhost:8001)
- **Frontend (Vite)**: Puerto 3002 (http://localhost:3002)  
- **Nginx**: Puerto 80 (reverse proxy)

### Endpoints Disponibles

Todos los endpoints de API ahora están disponibles con alias:

```
GET  /api/stakeholders/      - Lista de stakeholders (SIE)
POST /api/stakeholders/      - Crear stakeholder
GET  /api/scopes/            - Lista de scopes (ASB)
POST /api/scopes/            - Crear scope
GET  /api/change-logs/       - Histórico de cambios
GET  /api/maps/              - Mapas de procesos (SPM)
POST /api/maps/              - Crear mapa
```

## Acceso Vía Dominio Local (isosmart.local)

### Requisitos

- Acceso de `sudo` en el servidor
- Nginx instalado y configurado
- Permisos de lectura en `/home/aplicacion/projects/isosmart`

### Instalación

Ejecuta el script de setup:

```bash
bash /home/aplicacion/projects/isosmart/setup_domain.sh
```

Este script:
1. ✓ Agrega `127.0.0.1 isosmart.local` a `/etc/hosts`
2. ✓ Copia configuración de Nginx
3. ✓ Valida y recarga Nginx

### Acceso

Una vez completado, accede desde el navegador:

```
http://isosmart.local
```

### Credenciales de Prueba

```
Email:    admin@isosmart.local
Password: Admin123!
```

## Desarrollo Local (Sin Dominio)

Si prefieres acceder sin Nginx:

### Frontend
```bash
cd /home/aplicacion/projects/isosmart/frontend
npm run dev
# Accede a http://localhost:3002
```

### Backend
```bash
cd /home/aplicacion/projects/isosmart/backend
source venv_ai/bin/activate
python manage.py runserver 127.0.0.1:8001
# API en http://localhost:8001
```

## Troubleshooting

### No puedo acceder a isosmart.local

1. Verifica que `/etc/hosts` contenga:
   ```
   127.0.0.1       isosmart.local
   ```

2. Verifica que Nginx esté corriendo:
   ```bash
   sudo systemctl status nginx
   sudo ps aux | grep nginx
   ```

3. Verifica la configuración de Nginx:
   ```bash
   sudo nginx -t
   ```

### 502 Bad Gateway

Significa que Django no está corriendo. Inicia el servidor:

```bash
cd /home/aplicacion/projects/isosmart/backend
source venv_ai/bin/activate
python manage.py runserver 127.0.0.1:8001 &
```

### 404 en algún endpoint

Los endpoints ahora funcionan con alias. Verifica:
- Estás autenticado (accede primero a `/api/auth/login/`)
- Incluyes el header: `Authorization: Bearer {token}`

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│  Navegador (http://isosmart.local)                  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Nginx (Puerto 80)   │
         │   isosmart.local      │
         └────────┬─────────┬────┘
                  │         │
        ┌─────────▼─┐    ┌──▼──────────┐
        │Frontend   │    │Backend API  │
        │Vite Port  │    │Port 8001    │
        │3002       │    │(Django)     │
        └───────────┘    └──────┬──────┘
                                │
                        ┌───────▼────────┐
                        │   MariaDB      │
                        │   Redis        │
                        │   ChromaDB     │
                        └────────────────┘
```

## API Response Format

Todos los endpoints retornan JSON:

**Login (POST /api/auth/login/)**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {...},
  "profile": {...},
  "organizations": [...]
}
```

**Stakeholders (GET /api/stakeholders/)**
```json
[
  {
    "id": 1,
    "name": "Stakeholder Name",
    "description": "...",
    ...
  }
]
```

## Logs

- **Django**: `/home/aplicacion/projects/isosmart/logs/ai/`
- **Nginx**: `/var/log/nginx/`
- **MariaDB**: `/var/log/mysql/`

## Soporte

Para cualquier problema, revisa los logs:

```bash
# Django
tail -f /home/aplicacion/projects/isosmart/logs/ai/gunicorn_access.log
tail -f /home/aplicacion/projects/isosmart/logs/ai/gunicorn_error.log

# Nginx  
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```
