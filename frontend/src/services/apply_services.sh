#!/bin/bash
# =============================================================================
# Script para corregir servicios del frontend de ISO Smart
# Ejecutar desde: /home/aplicacion/projects/isosmart
# =============================================================================

echo "============================================="
echo "Corrigiendo servicios del frontend ISO Smart"
echo "============================================="

FRONTEND_DIR="/home/aplicacion/projects/isosmart/frontend"
SERVICES_DIR="$FRONTEND_DIR/src/services"
FIXES_DIR="/home/claude/isosmart_services"

cd $FRONTEND_DIR

# 1. Backup de archivos actuales
echo ""
echo "1. Creando backups..."
mkdir -p $SERVICES_DIR/backup
cp $SERVICES_DIR/*.js $SERVICES_DIR/backup/ 2>/dev/null || echo "   No hay archivos previos"
echo "   Backups creados en $SERVICES_DIR/backup/"

# 2. Eliminar o renombrar archivos .env problemáticos
echo ""
echo "2. Verificando variables de entorno..."
if [ -f "$FRONTEND_DIR/.env" ]; then
    echo "   Encontrado .env - renombrando a .env.bak"
    mv $FRONTEND_DIR/.env $FRONTEND_DIR/.env.bak
fi
if [ -f "$FRONTEND_DIR/.env.local" ]; then
    echo "   Encontrado .env.local - renombrando a .env.local.bak"
    mv $FRONTEND_DIR/.env.local $FRONTEND_DIR/.env.local.bak
fi
if [ -f "$FRONTEND_DIR/.env.development" ]; then
    echo "   Encontrado .env.development - renombrando a .env.development.bak"
    mv $FRONTEND_DIR/.env.development $FRONTEND_DIR/.env.development.bak
fi

# 3. Copiar servicios corregidos
echo ""
echo "3. Copiando servicios corregidos..."
if [ -d "$FIXES_DIR" ]; then
    cp $FIXES_DIR/*.js $SERVICES_DIR/
    echo "   ✅ Servicios copiados desde $FIXES_DIR"
else
    echo "   ⚠️  Directorio de correcciones no encontrado: $FIXES_DIR"
    echo "   Descarga isosmart_services.zip y descomprime en /home/claude/"
fi

# 4. Verificar que no queden URLs hardcodeadas
echo ""
echo "4. Verificando URLs hardcodeadas..."
HARDCODED=$(grep -rn "localhost:8001\|192.168.100.100" $SERVICES_DIR/*.js 2>/dev/null | grep -v ".bak" | grep -v "backup")
if [ -z "$HARDCODED" ]; then
    echo "   ✅ No se encontraron URLs hardcodeadas"
else
    echo "   ⚠️  Se encontraron URLs hardcodeadas:"
    echo "$HARDCODED"
fi

# 5. Reiniciar frontend
echo ""
echo "5. Reiniciando frontend..."
pm2 restart isosmart-frontend
sleep 2
pm2 status isosmart-frontend

echo ""
echo "============================================="
echo "Correcciones aplicadas"
echo "============================================="
echo ""
echo "Ahora:"
echo "  1. Limpia la caché del navegador (Ctrl+Shift+R)"
echo "  2. Abre http://isosmart.local"
echo "  3. Inicia sesión"
echo ""
