"""
=============================================================================
CONFIGURACIÓN DE SETTINGS.PY PARA ISO SMART AUTHENTICATION
=============================================================================

Agrega las siguientes configuraciones a tu archivo settings.py:
"""

# =============================================================================
# 1. INSTALLED_APPS - Agregar al final de la lista
# =============================================================================
"""
INSTALLED_APPS = [
    # ... apps existentes ...
    
    # Django REST Framework
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    
    # App de autenticación
    'authentication',
]
"""

# =============================================================================
# 2. MIDDLEWARE - Agregar después de AuthenticationMiddleware
# =============================================================================
"""
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Debe ser primero
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'authentication.middleware.OrganizationMiddleware',  # <-- Agregar aquí
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
"""

# =============================================================================
# 3. AUTH_USER_MODEL - Modelo de usuario personalizado
# =============================================================================
"""
AUTH_USER_MODEL = 'authentication.User'
"""

# =============================================================================
# 4. AUTHENTICATION_BACKENDS
# =============================================================================
"""
AUTHENTICATION_BACKENDS = [
    'authentication.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]
"""

# =============================================================================
# 5. REST_FRAMEWORK Configuration
# =============================================================================
"""
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}
"""

# =============================================================================
# 6. SIMPLE_JWT Configuration
# =============================================================================
"""
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'TOKEN_OBTAIN_SERIALIZER': 'authentication.serializers.LoginSerializer',
}
"""

# =============================================================================
# 7. CORS Configuration
# =============================================================================
"""
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://isosmart.local",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
"""

# =============================================================================
# 8. URLs - Agregar en urls.py principal
# =============================================================================
"""
# En backend/urls.py

from django.urls import path, include

urlpatterns = [
    # ... otras urls ...
    path('api/auth/', include('authentication.urls')),
]
"""

# =============================================================================
# 9. Requisitos de pip (requirements.txt)
# =============================================================================
"""
# Agregar a requirements.txt:
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
django-cors-headers>=4.3.0
"""

# =============================================================================
# 10. Comandos de migración
# =============================================================================
"""
# Después de configurar todo, ejecutar:

cd /home/aplicacion/projects/isosmart/backend
source venv_ai/bin/activate

# Crear migraciones
python manage.py makemigrations authentication

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Reiniciar servicio
sudo systemctl restart gunicorn-isosmart
"""
