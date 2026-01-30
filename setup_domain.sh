#!/bin/bash
# Setup script para IsoSmart en isosmart.local
# Este script configura el dominio local y Nginx

set -e

echo "========================================="
echo "Configurando IsoSmart en isosmart.local"
echo "========================================="

PROJECT_DIR="/home/aplicacion/projects/isosmart"
NGINX_CONF="/etc/nginx/conf.d/isosmart-all.conf"

# 1. Agregar entrada a /etc/hosts si no existe
echo ""
echo "[1/3] Configurando /etc/hosts..."
if ! grep -q "isosmart.local" /etc/hosts; then
    echo "127.0.0.1       isosmart.local" | sudo tee -a /etc/hosts > /dev/null
    echo "✓ Entrada isosmart.local agregada a /etc/hosts"
else
    echo "✓ isosmart.local ya está en /etc/hosts"
fi

# 2. Copiar configuración de Nginx
echo ""
echo "[2/3] Configurando Nginx..."
if sudo test -f "$NGINX_CONF"; then
    echo "⚠ Haciendo backup de configuración anterior..."
    sudo cp "$NGINX_CONF" "${NGINX_CONF}.bak.$(date +%s)"
fi

sudo cp "$PROJECT_DIR/nginx_isosmart.conf" "$NGINX_CONF"
echo "✓ Configuración de Nginx copiada"

# 3. Validar y recargar Nginx
echo ""
echo "[3/3] Validando y reiniciando Nginx..."
if sudo nginx -t; then
    sudo systemctl reload nginx || sudo service nginx reload
    echo "✓ Nginx recargado exitosamente"
else
    echo "✗ Error en validación de Nginx. Restaurando backup..."
    sudo cp "${NGINX_CONF}.bak" "$NGINX_CONF"
    sudo nginx -s reload
    exit 1
fi

echo ""
echo "========================================="
echo "✓ Configuración completada"
echo "========================================="
echo ""
echo "Puedes acceder a IsoSmart en:"
echo "  → http://isosmart.local"
echo ""
echo "Endpoints de API disponibles:"
echo "  → http://isosmart.local/api/stakeholders/"
echo "  → http://isosmart.local/api/scopes/"
echo "  → http://isosmart.local/api/change-logs/"
echo "  → http://isosmart.local/api/maps/"
echo ""
