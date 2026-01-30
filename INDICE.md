# 📑 ÍNDICE DE DOCUMENTACIÓN - ISOSMART

## 🎯 ¿POR DÓNDE EMPIEZO?

Depende de lo que necesites:

### Si eres el **Usuario Final** (accedes desde un navegador)
1. Lee: [INSTRUCCIONES_USUARIO.md](INSTRUCCIONES_USUARIO.md)
2. Ejecuta: `sudo bash setup_domain.sh`
3. Accede a: `http://isosmart.local`

### Si eres un **Desarrollador** (trabajas con el código)
1. Lee: [README.md](README.md)
2. Lee: [SETUP_GUIDE.md](SETUP_GUIDE.md)
3. Lee: [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)

### Si eres un **DevOps/SysAdmin** (administras la infraestructura)
1. Lee: [CAMBIOS_REALIZADOS.md](CAMBIOS_REALIZADOS.md)
2. Revisa: [nginx_isosmart.conf](nginx_isosmart.conf)
3. Ejecuta: [setup_domain.sh](setup_domain.sh)

---

## 📚 ARCHIVOS DE DOCUMENTACIÓN

### 📄 README.md
**Bienvenida principal del proyecto**
- Descripción general del sistema
- Estado actual de servicios
- URLs de acceso rápido
- Credenciales de prueba
- Troubleshooting básico

**Lectura:** 5-10 minutos  
**Nivel:** Todos

---

### 📄 INSTRUCCIONES_USUARIO.md
**Guía práctica paso a paso para usuarios finales**
- Cómo activar acceso vía dominio
- Instrucciones para otra PC en la red
- Solución de problemas comunes
- Testing rápido
- Credenciales

**Lectura:** 10-15 minutos  
**Nivel:** Usuarios finales ⭐ EMPIEZA AQUÍ

---

### 📄 SETUP_GUIDE.md
**Documentación técnica completa del sistema**
- Descripción de servicios
- Requisitos y dependencias
- Arquitectura del sistema
- Endpoints de API disponibles
- Desarrollo local vs producción
- Logs y monitoreo

**Lectura:** 20-30 minutos  
**Nivel:** Desarrolladores/DevOps

---

### 📄 CAMBIOS_REALIZADOS.md
**Resumen técnico detallado de todo lo implementado**
- Problemas identificados y resueltos
- Archivos modificados y creados
- Verificación final (test suite)
- Servicios activos
- Próximos pasos
- Estadísticas de cambios

**Lectura:** 15-20 minutos  
**Nivel:** Desarrolladores/DevOps

---

### 📄 IMPLEMENTATION_CHECKLIST.md
**Checklist detallado y comandos de testing**
- Estado de cada componente
- Tabla de endpoints con status
- Comandos de testing
- Arquitectura del sistema
- Logs disponibles

**Lectura:** 15-20 minutos  
**Nivel:** Desarrolladores/DevOps

---

### 📄 STATUS.txt
**Resumen visual en formato texto del estado actual**
- Estado de servicios con emojis
- Módulos operacionales
- Cambios realizados
- Instrucciones rápidas
- Estadísticas

**Lectura:** 3-5 minutos  
**Nivel:** Todos (referencia rápida)

---

## ⚙️ ARCHIVOS DE CONFIGURACIÓN

### 🔧 nginx_isosmart.conf
**Configuración del servidor reverse proxy Nginx**

```nginx
upstream isosmart_backend {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name isosmart.local localhost;
    
    location /api/ {
        proxy_pass http://isosmart_backend;
        # ... headers y configuración
    }
    
    location / {
        proxy_pass http://127.0.0.1:3002;  # Frontend Vite
    }
}
```

**Propósito:**
- Sirve frontend en http://isosmart.local
- Proxifica API a http://isosmart.local/api/
- Soporte para WebSocket (Vite HMR)
- Serve archivos estáticos

**Instalación:** Copiar a `/etc/nginx/conf.d/` (automático con setup_domain.sh)

---

### 🔧 setup_domain.sh
**Script automático de instalación**

```bash
#!/bin/bash
# 1. Agrega isosmart.local a /etc/hosts
# 2. Copia nginx_isosmart.conf a /etc/nginx/conf.d/
# 3. Valida configuración de Nginx
# 4. Recarga Nginx
```

**Uso:**
```bash
sudo bash setup_domain.sh
```

**Requisitos:**
- Permisos de sudo
- Nginx instalado
- Acceso a /etc/hosts y /etc/nginx/

**Tiempo:** ~10-15 segundos

---

## 🔄 ARCHIVOS MODIFICADOS EN EL CÓDIGO

### 📝 backend/backend/urls.py
**Archivo principal de rutas Django**

**Cambios realizados:**
```python
# Se agregaron 4 rutas alias:
path('api/stakeholders/', include('ai_modules.sie.urls')),
path('api/change-logs/', include('ai_modules.sie.urls')),
path('api/scopes/', include('ai_modules.asb.urls')),
path('api/maps/', include('ai_modules.spm.urls')),
```

**Propósito:** Permitir que frontend acceda con rutas esperadas

**Antes:** `/api/sie/stakeholders/`  
**Después:** `/api/stakeholders/` (alias agregado)

---

### 📝 frontend/.env
**Variables de entorno para desarrollo**

**Cambios:**
```
VITE_API_URL=http://localhost:8001/api
```

**Antes:** `http://192.168.100.100/api` (IP antigua, no disponible)  
**Propósito:** Conectar frontend con backend correcto

---

### 📝 frontend/.env.production
**Variables de entorno para producción**

**Creado nuevo:**
```
VITE_API_URL=http://isosmart.local/api
```

**Propósito:** Usar dominio local en producción

---

## 📊 RESUMEN DE CAMBIOS

| Aspecto | Detalle |
|---|---|
| Archivos Modificados | 2 (urls.py, .env) |
| Archivos Creados | 5 (.env.production, 4 archivos de config) |
| Líneas Agregadas | ~200+ |
| Documentación Creada | 5 archivos .md |
| Problemas Resueltos | 4 |
| Módulos Funcionales | 5/5 (100%) |
| Endpoints Operacionales | 20+ |

---

## 🗺️ MAPA DE NAVEGACIÓN

```
isosmart/
│
├── 📖 DOCUMENTACIÓN
│   ├── README.md                     ← COMIENZA AQUÍ (todos)
│   ├── STATUS.txt                    ← Referencia rápida
│   ├── INSTRUCCIONES_USUARIO.md      ← Usuarios finales ⭐
│   ├── SETUP_GUIDE.md                ← Guía completa
│   ├── CAMBIOS_REALIZADOS.md         ← Resumen técnico
│   └── IMPLEMENTATION_CHECKLIST.md   ← Testing y verificación
│
├── ⚙️ CONFIGURACIÓN
│   ├── nginx_isosmart.conf           ← Config de Nginx
│   ├── setup_domain.sh               ← Instalación automática
│   └── frontend/.env*                ← Variables de entorno
│
├── 💻 CÓDIGO MODIFICADO
│   ├── backend/backend/urls.py       ← URL aliases
│   └── frontend/.env                 ← API URL
│
└── 🚀 SERVICIOS
    ├── Backend (puerto 8001)          ← Django API
    ├── Frontend (puerto 3002)         ← Vite + React
    ├── Nginx (puerto 80)              ← Reverse proxy (await setup)
    ├── MariaDB (puerto 3306)          ← Base de datos
    ├── Redis (puerto 6379)            ← Cache
    └── ChromaDB (puerto 8002)         ← Embeddings
```

---

## ⏱️ TIEMPO DE LECTURA POR PERFIL

| Perfil | Archivos a Leer | Tiempo Total |
|---|---|---|
| **Usuario Final** | STATUS.txt + INSTRUCCIONES_USUARIO.md | 15 min |
| **Desarrollador** | README.md + SETUP_GUIDE.md + IMPLEMENTATION_CHECKLIST.md | 45 min |
| **DevOps/SysAdmin** | CAMBIOS_REALIZADOS.md + nginx_isosmart.conf | 30 min |
| **Auditor** | Todos los archivos .md | 90 min |

---

## 🎯 CASOS DE USO COMUNES

### "Quiero acceder desde mi PC normal vía isosmart.local"
1. Lee: [INSTRUCCIONES_USUARIO.md](INSTRUCCIONES_USUARIO.md)
2. Ejecuta: `sudo bash setup_domain.sh`
3. En tu PC: Agrega a `/etc/hosts`: `<IP_DEL_SERVIDOR> isosmart.local`
4. Accede a: `http://isosmart.local`

### "Necesito desenvolver localmente"
1. Lee: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Sección "Desarrollo Local"
2. Lee: [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) - Testing
3. Inicia: `cd frontend && npm run dev` + `cd backend && python manage.py runserver`

### "Necesito entender qué se cambió"
1. Lee: [CAMBIOS_REALIZADOS.md](CAMBIOS_REALIZADOS.md)
2. Revisa: `backend/backend/urls.py` y `frontend/.env`
3. Lee: [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) - Verificación

### "Hay un error, necesito diagnosticarlo"
1. Lee: [STATUS.txt](STATUS.txt) - Estado actual
2. Lee: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Sección Troubleshooting
3. Ejecuta: Comandos de testing en [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)

---

## ✅ VERIFICACIÓN ANTES DE USAR

- [ ] Leí [README.md](README.md)
- [ ] Leí la documentación apropiada para mi perfil
- [ ] Todos los servicios están corriendo (ver STATUS.txt)
- [ ] Entiendo cómo acceder al sistema (localhost vs isosmart.local)
- [ ] Tengo las credenciales de prueba

---

## 🔗 ENLACES RÁPIDOS

### Acceso
- 🌐 **Desarrollo:** http://localhost:3002
- 🌐 **API:** http://localhost:8001
- 🌐 **Dominio:** http://isosmart.local (después de setup)

### Login
```
Email: admin@isosmart.local
Password: Admin123!
```

### Comandos Útiles
```bash
# Ver estado de servicios
ps aux | grep -E "runserver|vite" | grep -v grep

# Ver logs
tail -f /home/aplicacion/projects/isosmart/logs/ai/gunicorn_access.log

# Activar dominio
sudo bash setup_domain.sh

# Test de API
curl http://localhost:8001/api/auth/login/
```

---

## 📞 SOPORTE

1. **Primero:** Revisa [STATUS.txt](STATUS.txt) para estado general
2. **Luego:** Busca tu problema en [SETUP_GUIDE.md](SETUP_GUIDE.md) - Troubleshooting
3. **Finalmente:** Revisa logs con comandos en [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)

---

## 📝 NOTAS

- ✓ Todos los tests pasaron correctamente
- ✓ Sistema listo para usar inmediatamente
- ✓ Documentación completamente actualizada
- ✓ Archivos de configuración listos para instalar

---

**Última actualización:** 29 de Enero, 2026  
**Versión:** 1.0  
**Estado:** ✅ COMPLETAMENTE FUNCIONAL

*Para comenzar, lee [README.md](README.md) o [INSTRUCCIONES_USUARIO.md](INSTRUCCIONES_USUARIO.md) según tu perfil.*
