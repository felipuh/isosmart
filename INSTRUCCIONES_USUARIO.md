# 👤 INSTRUCCIONES PARA ACCESO POR ISOSMART.LOCAL

## 🎯 Objetivo

Permitir que accedas a IsoSmart desde tu PC normal escribiendo simplemente:
```
http://isosmart.local
```

---

## ✅ QUÉ YA ESTÁ HECHO

- ✓ Backend API completamente funcional en puerto 8001
- ✓ Frontend React corriendo en puerto 3002
- ✓ Autenticación (login) funcionando
- ✓ Todos los módulos operacionales
- ✓ Archivos de configuración preparados

**Lo único que falta es ejecutar UN script en el servidor.**

---

## 🚀 CÓMO ACTIVARLO

### Paso 1: En el Servidor Linux

Ejecuta este comando UNA SOLA VEZ:

```bash
sudo bash /home/aplicacion/projects/isosmart/setup_domain.sh
```

Este script hará automáticamente:
1. Agregar `127.0.0.1 isosmart.local` a `/etc/hosts`
2. Configurar Nginx como reverse proxy
3. Validar y activar la nueva configuración

**Tiempo esperado:** 10-15 segundos

---

### Paso 2: En Tu Navegador

Una vez completado el script, abre tu navegador y accede a:

```
http://isosmart.local
```

---

## 🔐 Login

Usa estas credenciales:

```
Email:    admin@isosmart.local
Password: Admin123!
```

---

## 📱 Acceso desde Otra PC en la Red

Si quieres acceder desde otra computadora en la misma red (ej: otra laptop, tablet):

### 1. Obtén la IP del servidor:
```bash
# En el servidor Linux
hostname -I
# Ejemplo: 192.168.1.100
```

### 2. Edita el archivo hosts de tu PC:

**En Windows:**
- Abre: `C:\Windows\System32\drivers\etc\hosts`
- Agrega al final:
  ```
  192.168.1.100    isosmart.local
  ```
- Guarda el archivo (necesita permisos de admin)

**En Mac/Linux:**
- Terminal:
  ```bash
  sudo nano /etc/hosts
  ```
- Agrega:
  ```
  192.168.1.100    isosmart.local
  ```
- Guarda (Ctrl+O, Enter, Ctrl+X)

### 3. En tu navegador:
```
http://isosmart.local
```

---

## 🧪 Testing Rápido

### 1. Verificar que todo funciona:
```bash
curl http://localhost:8001/api/auth/login/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@isosmart.local","password":"Admin123!"}'
```

**Debes ver un JSON con `access_token` y `refresh_token`**

### 2. Verificar endpoints:
```bash
# Con autenticación
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8001/api/stakeholders/
```

---

## ⚠️ Si Algo Falla

### Error: "Connection refused"
```bash
# Verifica que Django está corriendo
ps aux | grep runserver

# Si no está, inicia manualmente:
cd /home/aplicacion/projects/isosmart/backend
source venv_ai/bin/activate
python manage.py runserver 127.0.0.1:8001 &
```

### Error: "502 Bad Gateway"
```bash
# Nginx no puede conectar con Django
# Verifica que Puerto 8001 está escuchando:
netstat -tulpn | grep 8001

# Si no aparece, reinicia Django
```

### Error: "Cannot resolve host"
```bash
# El navegador no reconoce isosmart.local
# En Linux, verifica /etc/hosts:
cat /etc/hosts | grep isosmart

# Debe mostrar:
# 127.0.0.1    isosmart.local
```

---

## 📊 Estado del Sistema

Para verificar que todo está bien, ejecuta:

```bash
# 1. Ver servicios corriendo
ps aux | grep -E "runserver|npm|nginx" | grep -v grep

# 2. Ver puertos abiertos
netstat -tulpn | grep -E "(8001|3002|80|3306|6379)"

# 3. Ver logs de Django
tail -f /home/aplicacion/projects/isosmart/logs/ai/gunicorn_access.log
```

---

## 📝 URL de Acceso

| Uso | URL |
|---|---|
| Desarrollo Local | http://localhost:3002 |
| API Direct | http://localhost:8001 |
| Producción | http://isosmart.local |
| Admin Django | http://localhost:8001/admin |

---

## 🎓 Endpoints Disponibles

Todos estos endpoints están disponibles DESPUÉS de loguearte:

```
GET  /api/stakeholders/          # Ver stakeholders
GET  /api/scopes/                # Ver alcances
GET  /api/change-logs/           # Ver historial de cambios
GET  /api/maps/                  # Ver mapas de procesos
GET  /api/auth/user/profile/     # Tu perfil
POST /api/auth/logout/           # Cerrar sesión
```

---

## 💾 Archivos Importantes

Si necesitas revisar la configuración:

```
/home/aplicacion/projects/isosmart/
├── nginx_isosmart.conf          # Config de Nginx
├── setup_domain.sh              # Script de instalación
├── SETUP_GUIDE.md               # Guía completa
├── IMPLEMENTATION_CHECKLIST.md  # Checklist
└── CAMBIOS_REALIZADOS.md        # Resumen de cambios
```

---

## ✨ Características Incluidas

- ✓ SSL/HTTPS ready (puede agregarse fácilmente)
- ✓ WebSocket support (para Vite HMR)
- ✓ Cache headers configurados
- ✓ Gzip compression enabled
- ✓ Proxy timeouts configurados
- ✓ Logging automático

---

## 🔄 Reiniciar Servicios

Si necesitas reiniciar:

```bash
# Reiniciar Django
pkill -f "runserver" && sleep 2
cd /home/aplicacion/projects/isosmart/backend
source venv_ai/bin/activate
python manage.py runserver 127.0.0.1:8001 &

# Reiniciar Nginx
sudo systemctl reload nginx

# Reiniciar Frontend
pkill -f "vite" && sleep 2
cd /home/aplicacion/projects/isosmart/frontend
npm run dev &
```

---

## 📞 Contacto/Soporte

Si hay problemas, revisa:

1. Logs de error:
   ```bash
   tail -f /home/aplicacion/projects/isosmart/logs/ai/gunicorn_error.log
   tail -f /var/log/nginx/error.log
   ```

2. Estado de servicios:
   ```bash
   ps aux | grep -E "python|node" | grep -v grep
   ```

3. Conectividad:
   ```bash
   curl -v http://localhost:8001/api/auth/login/
   ```

---

## ✅ CHECKLIST FINAL

Antes de usar, verifica que:

- [ ] Ejecutaste `sudo bash setup_domain.sh`
- [ ] Tu archivo /etc/hosts contiene `127.0.0.1 isosmart.local`
- [ ] Puedes acceder a `http://isosmart.local`
- [ ] El login funciona con admin@isosmart.local / Admin123!
- [ ] Ves los módulos en el dashboard

---

**¡Listo para usar!** 🎉

Si aún tienes dudas, revisa los archivos de documentación en el directorio del proyecto.

*Última actualización: 29 de Enero, 2026*
