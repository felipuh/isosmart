#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 INSTALADOR AUTOMÁTICO - MÓDULO SIE
# Stakeholder Intelligence Engine para ISO Smart
# Rocky Linux 9
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Detener en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🚀 Instalador Módulo SIE - ISO Smart${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Variables de configuración
PROJECT_BASE="/home/aplicacion/projects/isosmart"
BACKEND="$PROJECT_BASE/backend"
VENV="$BACKEND/venv_ai"
SIE_MODULE="$BACKEND/ai_modules/sie"

# Función para imprimir mensajes
print_step() {
    echo -e "${GREEN}[PASO $1/$2]${NC} $3"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ADVERTENCIA]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Verificar que el proyecto existe
if [ ! -d "$PROJECT_BASE" ]; then
    print_error "No se encontró el proyecto en $PROJECT_BASE"
    exit 1
fi

print_success "Proyecto encontrado en $PROJECT_BASE"

# ═══════════════════════════════════════════════════════════════════════════
# PASO 1: Verificar entorno virtual
# ═══════════════════════════════════════════════════════════════════════════
print_step 1 7 "Verificando entorno virtual..."

if [ ! -d "$VENV" ]; then
    print_error "No se encontró el entorno virtual en $VENV"
    print_warning "Créalo con: python3 -m venv $VENV"
    exit 1
fi

print_success "Entorno virtual encontrado"

# ═══════════════════════════════════════════════════════════════════════════
# PASO 2: Activar entorno virtual e instalar dependencias
# ═══════════════════════════════════════════════════════════════════════════
print_step 2 7 "Instalando dependencias de Python..."

source "$VENV/bin/activate"

pip install --quiet --upgrade pip

echo "  📦 Instalando networkx..."
pip install --quiet networkx==3.2.1

echo "  📦 Instalando numpy..."
pip install --quiet numpy==1.26.2

echo "  📦 Instalando pandas..."
pip install --quiet pandas==2.1.3

echo "  📦 Instalando scikit-learn..."
pip install --quiet scikit-learn==1.3.2

echo "  📦 Instalando nltk..."
pip install --quiet nltk==3.8.1

echo "  📦 Instalando spacy..."
pip install --quiet spacy==3.7.2

echo "  📦 Descargando modelo de español para spaCy..."
python -m spacy download es_core_news_sm --quiet 2>/dev/null || echo "  Modelo ya instalado"

print_success "Dependencias instaladas correctamente"

# ═══════════════════════════════════════════════════════════════════════════
# PASO 3: Verificar estructura de directorios
# ═══════════════════════════════════════════════════════════════════════════
print_step 3 7 "Verificando estructura de directorios..."

# Crear directorios si no existen
mkdir -p "$SIE_MODULE/services"
mkdir -p "$SIE_MODULE/tasks"
mkdir -p "$SIE_MODULE/models"
mkdir -p "$SIE_MODULE/utils"

# Crear __init__.py si no existen
touch "$SIE_MODULE/__init__.py"
touch "$SIE_MODULE/services/__init__.py"
touch "$SIE_MODULE/tasks/__init__.py"
touch "$SIE_MODULE/models/__init__.py"
touch "$SIE_MODULE/utils/__init__.py"

print_success "Estructura de directorios lista"

# ═══════════════════════════════════════════════════════════════════════════
# PASO 4: Verificar archivos del módulo
# ═══════════════════════════════════════════════════════════════════════════
print_step 4 7 "Verificando archivos del módulo SIE..."

REQUIRED_FILES=(
    "$SIE_MODULE/services/stakeholder_intelligence.py"
    "$SIE_MODULE/services/stakeholder_analyzer.py"
    "$SIE_MODULE/models/stakeholder.py"
    "$SIE_MODULE/serializers.py"
    "$SIE_MODULE/views.py"
    "$SIE_MODULE/urls.py"
    "$SIE_MODULE/tasks/stakeholder_tasks.py"
)

MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_warning "Archivo faltante: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    print_error "Faltan $MISSING_FILES archivos. Por favor, súbelos al servidor."
    print_warning "Consulta el archivo INSTALACION_SIE_ROCKY_LINUX.md para más detalles"
    exit 1
fi

print_success "Todos los archivos están presentes"

# ═══════════════════════════════════════════════════════════════════════════
# PASO 5: Crear migraciones
# ═══════════════════════════════════════════════════════════════════════════
print_step 5 7 "Creando migraciones de base de datos..."

cd "$BACKEND"
python manage.py makemigrations sie

print_success "Migraciones creadas"

# ═══════════════════════════════════════════════════════════════════════════
# PASO 6: Aplicar migraciones
# ═══════════════════════════════════════════════════════════════════════════
print_step 6 7 "Aplicando migraciones a la base de datos..."

python manage.py migrate

print_success "Base de datos actualizada"

# ═══════════════════════════════════════════════════════════════════════════
# PASO 7: Verificar instalación
# ═══════════════════════════════════════════════════════════════════════════
print_step 7 7 "Verificando instalación..."

echo "  🔍 Verificando dependencias..."
python -c "import networkx, numpy, pandas, sklearn, nltk, spacy; print('  ✓ Todas las dependencias importadas correctamente')"

echo "  🔍 Verificando modelos de Django..."
python manage.py check sie

print_success "Verificación completada"

# ═══════════════════════════════════════════════════════════════════════════
# FINALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ INSTALACIÓN COMPLETADA EXITOSAMENTE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Próximos pasos:${NC}"
echo "  1. Reiniciar Gunicorn:"
echo "     sudo systemctl restart isosmart-backend"
echo ""
echo "  2. Probar el módulo:"
echo "     curl http://localhost:8000/api/sie/stakeholders/"
echo ""
echo "  3. Ejecutar análisis de IA:"
echo "     curl -X POST http://localhost:8000/api/sie/stakeholders/run_analysis/"
echo ""
echo "  4. Crear stakeholders de prueba:"
echo "     python manage.py shell"
echo "     >>> from ai_modules.sie.models.stakeholder import StakeholderProfile"
echo "     >>> StakeholderProfile.objects.create(name='Test', stakeholder_type='cliente', power='alto', interest='alto')"
echo ""
echo -e "${YELLOW}📖 Documentación completa:${NC} INSTALACION_SIE_ROCKY_LINUX.md"
echo ""
