# Solución: Error 400 en Login - Puerto Frontend Correcto

## 🔴 Problema Reportado

```
POST http://isosmart.local/api/auth/login/ 400 (Bad Request)
Error de login: se {message: 'Request failed with status code 400', ...}
```

**Causa:** El navegador estaba intentando acceder a `isosmart.local` **sin puerto**, lo que lo llevaba a puerto **80** por defecto (HTTP). Pero Vite está escuchando en puerto **3001**.

---

## 🔧 Root Cause Analysis

1. **DNS/Hosts Configurado:**
   ```bash
   # /etc/hosts
   127.0.0.1       isosmart.local
   ```

2. **Vite Ejecutándose en:**
   - Puerto: **3001**
   - Host: 0.0.0.0

3. **Problema:**
   - Usuario accedía a: `http://isosmart.local` (sin puerto)
   - Browser interpretaba como: `http://isosmart.local:80`
   - Pero no hay servidor en puerto 80
   - Resultado: **Timeout o error de conexión**

---

## ✅ Solución

### Opción 1: Usar localhost con puerto (RECOMENDADO)
```
http://localhost:3001
```
- Siempre funciona
- No requiere configuración DNS

### Opción 2: Usar isosmart.local con puerto
```
http://isosmart.local:3001
```
- Requiere puerto explícito `:3001`
- DNS ya está configurado en `/etc/hosts`

### Opción 3: Configurar Nginx como proxy (PRODUCCIÓN)
```nginx
server {
  listen 80;
  server_name isosmart.local;
  location / {
    proxy_pass http://127.0.0.1:3001;
  }
}
```

---

## 📋 URLs Correctas para Pruebas

| Página | URL Correcta |
|--------|------------|
| Login | `http://localhost:3001/login` |
| Onboarding | `http://localhost:3001/onboarding` |
| Dashboard | `http://localhost:3001/` |
| Settings | `http://localhost:3001/settings` |

---

## 🔍 Verificación del Proxy

### Test 1: Verificar que Vite está en el puerto correcto
```bash
curl -s -w "%{http_code}\n" http://localhost:3001 | tail -1
# Debe retornar 200
```

### Test 2: Verificar que el proxy de Vite funciona
```bash
curl -s -X POST http://localhost:3001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@isosmart.local","password":"Admin@123456"}' | jq .access
# Debe retornar un token JWT
```

### Test 3: Verificar backend directamente
```bash
curl -s -X POST http://127.0.0.1:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@isosmart.local","password":"Admin@123456"}' | jq .access
# Debe retornar un token JWT
```

---

## 🚀 Próximos Pasos

1. Abre **http://localhost:3001** en tu navegador
2. Login con:
   - Email: `admin@isosmart.local`
   - Password: `Admin@123456`
3. Se redirecciona a `/onboarding` (primera vez que inicia sesión)
4. Completa el wizard y empieza a usar la plataforma

---

## Para Producción

Si quieres que `isosmart.local:80` funcione sin puerto:

1. **Instala Nginx:**
   ```bash
   sudo apt install nginx
   ```

2. **Crea configuración:**
   ```bash
   sudo tee /etc/nginx/sites-available/isosmart.local << 'EOF'
   server {
     listen 80;
     server_name isosmart.local;
   
     location / {
       proxy_pass http://127.0.0.1:3001;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
     }
   
     location /api {
       proxy_pass http://127.0.0.1:8001;
       proxy_set_header Host $host;
     }
   }
   EOF
   ```

3. **Habilita el sitio:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/isosmart.local /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

4. Ahora funciona: `http://isosmart.local` (sin puerto)

---

**Fecha de Resolución:** 24 de febrero de 2026  
**Estado:** ✅ RESUELTO - Frontend compatible con localhost:3001
