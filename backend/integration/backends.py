"""
Backend de Autenticación para ISO Smart
Valida credenciales contra Admin Apps
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import IntegrityError
from .client import admin_apps_client
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

ROLE_MAP = {
    'superadmin': 'org_admin',
    'admin': 'org_admin',
    'org_admin': 'org_admin',
    'iso_manager': 'iso_manager',
    'auditor': 'auditor',
    'user': 'user',
    'viewer': 'viewer',
}


class AdminAppsAuthBackend(BaseBackend):
    """
    Backend de autenticación que valida credenciales contra Admin Apps
    
    Flujo:
    1. Usuario intenta login en ISO Smart
    2. ISO Smart envía credenciales a Admin Apps
    3. Admin Apps valida y retorna información del usuario
    4. ISO Smart crea/actualiza usuario local con los datos
    5. Usuario queda autenticado en ISO Smart
    
    Configuración en settings.py:
    
    AUTHENTICATION_BACKENDS = [
        'integration.backends.AdminAppsAuthBackend',
        'django.contrib.auth.backends.ModelBackend',  # Fallback local
    ]
    
    ADMIN_APPS_INTEGRATION = {
        'BASE_URL': 'http://adminapps.isosmart.local/api/integration',
        'API_KEY': 'your-secret-api-key',
        'SYNC_USERS': True,  # Crear/actualizar usuarios locales
    }
    """
    
    def authenticate(self, request, email=None, password=None, organization_id=None, **kwargs):
        from django.core.exceptions import PermissionDenied
        # LoginSerializer uses the central challenge protocol. A password-only
        # backend cannot attest completion and must stop all local fallbacks.
        raise PermissionDenied('Use central SSO authentication')

    def get_user(self, user_id):
        # Old Django password sessions carry no central MFA proof. Product
        # sessions use the validated JWT/cookie adapter, never this backend.
        return None


class AdminAppsTokenBackend:
    """
    Utilidad para validar tokens JWT contra Admin Apps
    (Para uso con SimpleJWT si se necesita validación remota)
    """
    
    @staticmethod
    def validate_user(user_id, organization_id=None):
        """
        Valida que un usuario siga activo en Admin Apps
        Útil para verificaciones periódicas de tokens
        """
        result = admin_apps_client.get_user(user_id, organization_id)
        
        if 'error' in result:
            return False, result.get('error')
        
        return True, result.get('user')
