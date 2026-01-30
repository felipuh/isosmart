"""
Middleware de Autenticación para ISO Smart
Extrae información de organización del token JWT y la agrega al request
"""

from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import UserProfile


class OrganizationMiddleware(MiddlewareMixin):
    """
    Middleware que extrae organization_id del token JWT
    y lo agrega al request para filtrado automático
    """
    
    def process_request(self, request):
        # Inicializar atributos
        request.organization_id = None
        request.user_role = None
        request.user_profile = None
        
        # Obtener token del header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        try:
            # Autenticar con JWT
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(
                auth_header.split(' ')[1]
            )
            
            # Extraer claims personalizados
            request.organization_id = validated_token.get('organization_id')
            request.user_role = validated_token.get('role')
            profile_id = validated_token.get('profile_id')
            
            # Cargar perfil si es necesario
            if profile_id:
                try:
                    request.user_profile = UserProfile.objects.select_related(
                        'organization'
                    ).get(id=profile_id)
                except UserProfile.DoesNotExist:
                    pass
                    
        except (InvalidToken, TokenError):
            # Token inválido, dejar valores en None
            pass
        
        return None


class OrganizationFilterMixin:
    """
    Mixin para filtrar querysets automáticamente por organización
    
    Uso en ViewSets:
        class MyViewSet(OrganizationFilterMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            ...
    """
    
    organization_field = 'organization_id'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization_id = getattr(self.request, 'organization_id', None)
        
        if organization_id:
            filter_kwargs = {self.organization_field: organization_id}
            queryset = queryset.filter(**filter_kwargs)
        
        return queryset
    
    def perform_create(self, serializer):
        """Agrega organization_id automáticamente al crear"""
        organization_id = getattr(self.request, 'organization_id', None)
        if organization_id and self.organization_field:
            serializer.save(**{self.organization_field.replace('_id', ''): organization_id})
        else:
            serializer.save()


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware opcional para logging de auditoría
    Registra acciones importantes del usuario
    """
    
    # Métodos que generan logs
    AUDITED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Paths que no se auditan
    EXCLUDED_PATHS = [
        '/api/auth/refresh/',
        '/api/health/',
    ]
    
    def process_response(self, request, response):
        # Solo auditar métodos de escritura
        if request.method not in self.AUDITED_METHODS:
            return response
        
        # Excluir ciertos paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response
        
        # Solo auditar si hay usuario autenticado
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response
        
        # Solo auditar respuestas exitosas
        if response.status_code >= 400:
            return response
        
        # Aquí podrías agregar lógica para guardar en base de datos
        # Por ahora solo logging
        import logging
        logger = logging.getLogger('audit')
        
        logger.info(
            f"AUDIT: {request.method} {request.path} | "
            f"User: {request.user.email} | "
            f"Org: {getattr(request, 'organization_id', 'N/A')} | "
            f"Status: {response.status_code}"
        )
        
        return response
