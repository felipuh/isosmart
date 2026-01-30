#!/bin/bash
# Script para reiniciar todos los servicios de IsoSmart

set -e

echo "=========================================="
echo "Reiniciando Servicios de IsoSmart"
echo "=========================================="

PROJECT_DIR="/home/aplicacion/projects/isosmart"

# 1. Matar procesos anteriores
echo "[1/4] Deteniendo servicios anteriores..."
pkill -f "runserver" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 2
echo "✓ Servicios detenidos"

# 2. Iniciar Backend
echo "[2/4] Iniciando Backend Django..."
cd "$PROJECT_DIR/backend"
source venv_ai/bin/activate
nohup python manage.py runserver 127.0.0.1:8001 > "$PROJECT_DIR/logs/ai/runserver.log" 2>&1 &
BACKEND_PID=$!
sleep 3
echo "✓ Backend iniciado (PID: $BACKEND_PID)"

# 3. Iniciar Frontend
echo "[3/4] Iniciando Frontend Vite..."
cd "$PROJECT_DIR/frontend"
nohup npm run dev > "$PROJECT_DIR/logs/frontend_vite.log" 2>&1 &
FRONTEND_PID=$!
sleep 3
echo "✓ Frontend iniciado (PID: $FRONTEND_PID)"

# 4. Verificar servicios
echo "[4/4] Verificando servicios..."
echo ""
echo "Backend (puerto 8001):"
ps aux | grep "runserver" | grep -v grep | head -1 || echo "✗ No corriendo"

echo ""
echo "Frontend (puerto 3002):"
ps aux | grep "vite" | grep -v grep | head -1 || echo "✗ No corriendo"

echo ""
echo "=========================================="
echo "✓ Servicios reiniciados correctamente"
echo "=========================================="
echo ""
echo "Accede a:"
echo "  • Desarrollo: http://localhost:3002"
echo "  • Dominio:    http://isosmart.local"
echo ""
