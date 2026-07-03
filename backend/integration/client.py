"""
Cliente de Integración con Admin Apps para ISO Smart
Permite a ISO Smart comunicarse con Admin Apps para:
- Validar usuarios
- Obtener organizaciones
- Verificar módulos activos

Fallback local: solo si ALLOW_LOCAL_AUTH_FALLBACK=true en desarrollo.
"""
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# Importar modelos locales para fallback
try:
    from core.models import Organization
except ImportError:
    Organization = None


class AdminAppsClient:
    """
    Cliente para comunicación con Admin Apps
    
    Configuración en settings.py:
    
    ADMIN_APPS_INTEGRATION = {
        'BASE_URL': 'http://localhost:8000/api/integration',
        'API_KEY': 'your-secret-api-key',
        'TIMEOUT': 10,
        'CACHE_TTL': 300,  # 5 minutos
    }
    """
    
    def __init__(self):
        config = getattr(settings, 'ADMIN_APPS_INTEGRATION', {})
        self.base_url = config.get('BASE_URL', 'http://localhost:8000/api/integration')
        self.api_key = config.get('API_KEY', '')
        self.timeout = config.get('TIMEOUT', 10)
        self.cache_ttl = config.get('CACHE_TTL', 300)
    
    def _get_headers(self):
        """Headers para las peticiones"""
        return {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
        }
    
    def _make_request(self, method, endpoint, data=None, use_cache=False, cache_key=None):
        """Realiza una petición a Admin Apps"""
        url = f"{self.base_url}{endpoint}"
        
        # Verificar caché si aplica
        if use_cache and cache_key:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
        
        try:
            if method == 'GET':
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
            else:
                response = requests.post(
                    url,
                    json=data,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Guardar en caché si aplica
            if use_cache and cache_key:
                cache.set(cache_key, result, self.cache_ttl)
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout conectando a Admin Apps: {url}")
            return {'error': 'Timeout', 'code': 'timeout'}
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión a Admin Apps: {url}")
            return {'error': 'No se puede conectar a Admin Apps', 'code': 'connection_error'}
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP de Admin Apps: {e}")
            try:
                return response.json()
            except:
                return {'error': str(e), 'code': 'http_error'}
        
        except Exception as e:
            logger.exception(f"Error inesperado con Admin Apps: {e}")
            return {'error': str(e), 'code': 'unknown_error'}

    def _local_fallback_allowed(self):
        return bool(getattr(settings, 'ALLOW_LOCAL_AUTH_FALLBACK', False))

    def _fallback_disabled_response(self, result):
        logger.error(
            "Admin Apps unavailable and local fallback disabled. code=%s error=%s",
            result.get('code'),
            result.get('error'),
        )
        return {
            **result,
            'fallback': 'disabled',
            'source': 'adminapps',
        }
    
    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================
    
    def health_check(self):
        """Verifica que Admin Apps esté disponible"""
        return self._make_request('GET', '/health/')
    
    def get_organizations(self, use_cache=True):
        """Obtiene lista de organizaciones activas (con fallback a BD local)"""
        cache_key = 'adminapps:organizations' if use_cache else None
        result = self._make_request(
            'GET',
            '/organizations/',
            use_cache=use_cache,
            cache_key=cache_key
        )
        
        # Si hay error, intentar fallback a BD local
        if 'error' in result and Organization:
            if not self._local_fallback_allowed():
                return self._fallback_disabled_response(result)
            logger.warning(f"Admin Apps falló ({result.get('error')}), usando fallback de BD local")
            return self._get_organizations_local()
        
        return result
    
    def _get_organizations_local(self):
        """Fallback: obtener organizaciones de BD local"""
        try:
            orgs = Organization.objects.filter(is_active=True)
            return {
                'organizations': [
                    {
                        'id': org.id,
                        'name': org.name,
                        'slug': org.slug,
                        'email': org.email,
                        'external_id': org.external_id,
                    }
                    for org in orgs
                ],
                'source': 'local_database',
                'count': orgs.count(),
            }
        except Exception as e:
            logger.exception(f"Error al obtener organizaciones locales: {e}")
            return {'error': str(e), 'code': 'local_error'}
    
    def get_organization(self, org_id, use_cache=True):
        """Obtiene detalle de una organización (con fallback a BD local)"""
        cache_key = f'adminapps:organization:{org_id}' if use_cache else None
        result = self._make_request(
            'GET',
            f'/organizations/{org_id}/',
            use_cache=use_cache,
            cache_key=cache_key
        )
        
        # Si hay error, intentar fallback a BD local
        if 'error' in result and Organization:
            if not self._local_fallback_allowed():
                return self._fallback_disabled_response(result)
            logger.warning(f"Admin Apps falló ({result.get('error')}), usando fallback de BD local para org {org_id}")
            return self._get_organization_local(org_id)
        
        return result
    
    def _get_organization_local(self, org_id):
        """Fallback: obtener organización de BD local"""
        try:
            org = Organization.objects.get(id=org_id)
            return {
                'organization': {
                    'id': org.id,
                    'name': org.name,
                    'slug': org.slug,
                    'email': org.email,
                    'phone': org.phone,
                    'address': org.address,
                    'website': org.website,
                    'tax_id': org.tax_id,
                    'legal_name': org.legal_name,
                    'is_active': org.is_active,
                    'plan_type': org.plan_type,
                    'external_id': org.external_id,
                },
                'source': 'local_database',
            }
        except Organization.DoesNotExist:
            logger.warning(f"Organización {org_id} no encontrada en BD local")
            return {'error': 'Organización no encontrada', 'code': 'not_found'}
        except Exception as e:
            logger.exception(f"Error al obtener organización local {org_id}: {e}")
            return {'error': str(e), 'code': 'local_error'}
    
    def get_organization_users(self, org_id, use_cache=True):
        """Obtiene usuarios de una organización (con fallback)"""
        cache_key = f'adminapps:organization:{org_id}:users' if use_cache else None
        result = self._make_request(
            'GET',
            f'/organizations/{org_id}/users/',
            use_cache=use_cache,
            cache_key=cache_key
        )
        
        # Si hay error, fallback: retornar admin local
        if 'error' in result:
            if not self._local_fallback_allowed():
                return self._fallback_disabled_response(result)
            logger.warning(f"Admin Apps falló ({result.get('error')}), retornando usuarios locales para org {org_id}")
            return self._get_organization_users_local(org_id)
        
        return result
    
    def _get_organization_users_local(self, org_id):
        """Fallback: obtener usuarios locales de organización"""
        try:
            from authentication.models import UserProfile
            profiles = UserProfile.objects.filter(organization_id=org_id, is_active=True)
            return {
                'organization_id': org_id,
                'users': [
                    {
                        'id': p.user.id,
                        'email': p.user.email,
                        'first_name': p.user.first_name,
                        'last_name': p.user.last_name,
                        'role': p.role,
                        'is_active': p.user.is_active,
                    }
                    for p in profiles
                ],
                'source': 'local_database',
                'count': profiles.count(),
            }
        except Exception as e:
            logger.exception(f"Error al obtener usuarios locales para org {org_id}: {e}")
            return {
                'organization_id': org_id,
                'users': [],
                'error': str(e),
                'code': 'local_error'
            }
    
    def get_organization_modules(self, org_id, use_cache=True):
        """Obtiene módulos habilitados de una organización (con fallback)"""
        cache_key = f'adminapps:organization:{org_id}:modules' if use_cache else None
        result = self._make_request(
            'GET',
            f'/organizations/{org_id}/modules/',
            use_cache=use_cache,
            cache_key=cache_key
        )
        
        # Si hay error, fallback a BD local
        if 'error' in result:
            if not self._local_fallback_allowed():
                return self._fallback_disabled_response(result)
            logger.warning(f"Admin Apps falló ({result.get('error')}), retornando módulos locales para org {org_id}")
            return self._get_organization_modules_local(org_id)
        
        return result
    
    def _get_organization_modules_local(self, org_id):
        """Fallback: obtener módulos habilitados de organización local"""
        try:
            org = Organization.objects.get(id=org_id)
            
            # Intentar obtener los settings, pero con fallback a valores por defecto
            try:
                settings = org.settings
                ai_sca_enabled = settings.ai_sca_enabled
                ai_sie_enabled = settings.ai_sie_enabled
                ai_asb_enabled = settings.ai_asb_enabled
                ai_spm_enabled = settings.ai_spm_enabled
            except:
                # Si no existe settings o hay error, asumir todos habilitados
                ai_sca_enabled = True
                ai_sie_enabled = True
                ai_asb_enabled = True
                ai_spm_enabled = True
            
            modules = [
                {
                    'code': 'SCA',
                    'name': 'Context Analyzer',
                    'enabled': ai_sca_enabled,
                },
                {
                    'code': 'SIE',
                    'name': 'Stakeholder Intelligence',
                    'enabled': ai_sie_enabled,
                },
                {
                    'code': 'ASB',
                    'name': 'Scope Builder',
                    'enabled': ai_asb_enabled,
                },
                {
                    'code': 'SPM',
                    'name': 'Process Mapper',
                    'enabled': ai_spm_enabled,
                },
            ]
            
            return {
                'organization_id': org_id,
                'modules': modules,
                'source': 'local_database',
                'count': sum(1 for m in modules if m['enabled']),
            }
        except Organization.DoesNotExist:
            logger.warning(f"Organización {org_id} no encontrada para módulos locales")
            return {'error': 'Organización no encontrada', 'code': 'not_found'}
        except Exception as e:
            logger.exception(f"Error al obtener módulos locales para org {org_id}: {e}")
            return {'error': str(e), 'code': 'local_error'}
    
    def validate_credentials(self, email, password, organization_id=None):
        """
        Valida credenciales de un usuario
        
        Returns:
        {
            'valid': True/False,
            'user': {...},
            'organizations': [...],
            'current_organization': {...},
            'current_role': '...'
        }
        """
        data = {
            'email': email,
            'password': password,
        }
        if organization_id:
            data['organization_id'] = organization_id
        
        return self._make_request('POST', '/validate-credentials/', data=data)
    
    def get_user(self, user_id, organization_id=None):
        """Obtiene información de un usuario por ID"""
        data = {'user_id': user_id}
        if organization_id:
            data['organization_id'] = organization_id
        
        return self._make_request('POST', '/user/', data=data)
    
    def is_module_enabled(self, org_id, module_code):
        """Verifica si un módulo está habilitado para una organización"""
        result = self.get_organization_modules(org_id)
        
        if 'error' in result:
            return False
        
        modules = result.get('modules', [])
        return any(m['code'] == module_code for m in modules)
    
    def clear_cache(self, org_id=None):
        """Limpia la caché de integración"""
        if org_id:
            cache.delete(f'adminapps:organization:{org_id}')
            cache.delete(f'adminapps:organization:{org_id}:users')
            cache.delete(f'adminapps:organization:{org_id}:modules')
        else:
            # Limpiar toda la caché de adminapps (requiere patrón de eliminación)
            cache.delete('adminapps:organizations')


# Instancia singleton del cliente
admin_apps_client = AdminAppsClient()
