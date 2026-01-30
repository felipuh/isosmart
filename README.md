# 🎉 ISOSMART - COMPLETAMENTE FUNCIONAL

## ✅ Estado: LISTO PARA USAR

Todos los módulos están operacionales y pueden ser accedidos.

---

## 🚀 INICIO RÁPIDO

### Para Desarrollo Local (3 minutos)
```bash
# Terminal 1: Backend
cd backend && source venv_ai/bin/activate && python manage.py runserver 127.0.0.1:8001

# Terminal 2: Frontend
cd frontend && npm run dev

# Accede a: http://localhost:3002
```

### Para Producción con Dominio (5 minutos)
```bash
# En el servidor:
sudo bash setup_domain.sh

# Luego accede a: http://isosmart.local
```

---

## 📚 DOCUMENTACIÓN

Lee estos archivos EN ORDEN:

1. **[INSTRUCCIONES_USUARIO.md](INSTRUCCIONES_USUARIO.md)** ← EMPIEZA AQUÍ
   - Instrucciones paso a paso
   - Cómo activar isosmart.local
   - Solución de problemas comunes

2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)**
   - Guía completa del sistema
   - Descripción de servicios
   - Endpoints disponibles

3. **[CAMBIOS_REALIZADOS.md](CAMBIOS_REALIZADOS.md)**
   - Resumen técnico de cambios
   - Problemas resueltos
   - Verificación final

4. **[IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)**
   - Checklist detallado
   - Testing comandos
   - Arquitectura del sistema

---

## 🔐 Credenciales

```
Email:    admin@isosmart.local
Password: Admin123!
```

---

## 🌐 URLs de Acceso

| Opción | URL | Uso |
|---|---|---|
| **Desarrollo** | http://localhost:3002 | Frontend en tiempo real |
| **API Direct** | http://localhost:8001 | Backend API |
| **Dominio Local** | http://isosmart.local | Después de ejecutar setup_domain.sh |
| **Admin Django** | http://localhost:8001/admin | Panel de administración |

---

## ✨ Módulos Operacionales

- ✅ **SIE** (Stakeholder Intelligence) - Gestión de stakeholders
- ✅ **ASB** (Activity Scope Breakdown) - Definición de alcances
- ✅ **SPM** (Scope & Process Management) - Mapeo de procesos
- ✅ **SCA** (Strategic Context Analysis) - Análisis de contexto
- ✅ **Integration** - Integraciones entre módulos

---

## 📊 Servicios

| Servicio | Puerto | Status |
|---|---|---|
| **Backend (Django)** | 8001 | ✅ Corriendo |
| **Frontend (Vite)** | 3002 | ✅ Corriendo |
| **Nginx** | 80 | ⏳ Listo (await setup) |
| **MariaDB** | 3306 | ✅ Accesible |
| **Redis** | 6379 | ✅ Accesible |
| **ChromaDB** | 8002 | ✅ Accesible |

---

## 🔄 Endpoints API Principales

```
POST   /api/auth/login/              # Autenticación
GET    /api/stakeholders/             # Listar stakeholders
POST   /api/stakeholders/             # Crear stakeholder
GET    /api/scopes/                   # Listar alcances
GET    /api/change-logs/              # Ver historial
GET    /api/maps/                     # Procesos
```

---

## 🛠️ Scripts Útiles

### Activar Dominio Local (IMPORTANTE)
```bash
sudo bash setup_domain.sh
```

### Ver Estado de Servicios
```bash
ps aux | grep -E "runserver|vite" | grep -v grep
```

### Ver Logs en Tiempo Real
```bash
tail -f logs/ai/gunicorn_access.log
```

### Testing de API
```bash
# Login
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@isosmart.local","password":"Admin123!"}'

# Obtener stakeholders (requiere token JWT)
TOKEN="<paste_access_token_here>"
curl http://localhost:8001/api/stakeholders/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📁 Archivos de Configuración

```
isosmart/
├── nginx_isosmart.conf              # Config de Nginx
├── setup_domain.sh                  # Script de instalación
├── INSTRUCCIONES_USUARIO.md         # Este archivo (LEE PRIMERO!)
├── SETUP_GUIDE.md                   # Guía completa
├── CAMBIOS_REALIZADOS.md            # Resumen técnico
├── IMPLEMENTATION_CHECKLIST.md      # Checklist y testing
│
├── backend/
│   ├── manage.py
│   ├── gunicorn_config.py
│   ├── backend/urls.py              # ← Modificado con URL aliases
│   ├── requirements.txt
│   └── ai_modules/                  # Todos los módulos
│
├── frontend/
│   ├── .env                         # ← Actualizado
│   ├── .env.production              # ← Creado para dominio
│   ├── src/
│   └── package.json
│
└── logs/
    └── ai/
        ├── gunicorn_access.log
        └── gunicorn_error.log
```

---

## ⚡ Solución Rápida de Problemas

### No puedo acceder a isosmart.local
1. Verifica que ejecutaste: `sudo bash setup_domain.sh`
2. Verifica `/etc/hosts` contiene: `127.0.0.1 isosmart.local`
3. Reinicia Nginx: `sudo systemctl reload nginx`

### 502 Bad Gateway
1. Verifica que Django corre: `ps aux | grep runserver`
2. Reinicia: `pkill -f runserver` luego inicia manualmente

### Login retorna 404
1. Verifica puerto 8001: `netstat -tulpn | grep 8001`
2. Verifica logs: `tail -f logs/ai/gunicorn_error.log`

### Vite no se conecta
1. Verifica puerto 3002: `netstat -tulpn | grep 3002`
2. Reinicia: `pkill -f vite` luego `cd frontend && npm run dev`

---

## 📞 Contacto y Soporte

Para diagnosticar problemas:

```bash
# Ver todos los servicios activos
ps aux | grep -E "python|node|nginx" | grep -v grep

# Ver puertos en escucha
netstat -tulpn | grep LISTEN

# Ver logs de error
tail -50 /home/aplicacion/projects/isosmart/logs/ai/gunicorn_error.log
sudo tail -50 /var/log/nginx/error.log

# Testear conectividad
curl -v http://localhost:8001/health
curl -v http://localhost:3002
```

---

## 🎯 Siguiente Paso

**Ejecuta esto EN EL SERVIDOR si quieres acceder desde otro PC vía isosmart.local:**

```bash
sudo bash setup_domain.sh
```

Luego abre tu navegador en:
```
http://isosmart.local
```

---

## ✅ Verificación Final

Todos los tests pasaron:
- ✓ Login funciona (status 200)
- ✓ Stakeholders endpoint (status 200)
- ✓ Scopes endpoint (status 200)
- ✓ Change-logs endpoint (status 200)
- ✓ Maps endpoint (status 200)
- ✓ Django corriendo en puerto 8001
- ✓ Vite corriendo en puerto 3002
- ✓ Redis accesible
- ✓ Base de datos sincronizada

---

**¿Preguntas? Revisa los archivos .md en este directorio 📚**

*Sistema completamente funcional desde 29 de Enero, 2026*
