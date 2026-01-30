"""
Permisos personalizados para ISO Smart
Basados en roles de usuario en la organización
"""

from rest_framework import permissions


class IsOrgAdmin(permissions.BasePermission):
    """
    Permiso que solo permite acceso a administradores de organización
    """
    message = 'Solo los administradores pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        role = getattr(request, 'user_role', None)
        return role == 'org_admin'


class IsOrgManager(permissions.BasePermission):
    """
    Permiso que permite acceso a administradores y responsables SGC
    """
    message = 'Solo los administradores y responsables SGC pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        role = getattr(request, 'user_role', None)
        return role in ['org_admin', 'iso_manager']


class CanEdit(permissions.BasePermission):
    """
    Permiso que permite edición a admin, manager y usuarios normales
    Los auditores y viewers solo tienen lectura
    """
    message = 'No tienes permisos para editar.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Métodos seguros (lectura) permitidos para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        role = getattr(request, 'user_role', None)
        return role in ['org_admin', 'iso_manager', 'user']


class IsAuditor(permissions.BasePermission):
    """
    Permiso específico para auditores
    Tienen acceso de lectura a todos los módulos
    """
    message = 'Acceso restringido a auditores.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        role = getattr(request, 'user_role', None)
        
        # Auditores y superiores pueden acceder
        if role in ['org_admin', 'iso_manager', 'auditor']:
            return True
        
        return False


class OrganizationPermission(permissions.BasePermission):
    """
    Permiso base que verifica que el usuario pertenece a la organización
    """
    message = 'No tienes acceso a esta organización.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        organization_id = getattr(request, 'organization_id', None)
        return organization_id is not None
    
    def has_object_permission(self, request, view, obj):
        organization_id = getattr(request, 'organization_id', None)
        
        # Verificar si el objeto tiene organization_id
        if hasattr(obj, 'organization_id'):
            return obj.organization_id == organization_id
        
        # Verificar si el objeto tiene organization
        if hasattr(obj, 'organization'):
            return obj.organization.id == organization_id
        
        return True


class RoleBasedPermission(permissions.BasePermission):
    """
    Permiso dinámico basado en roles
    Puede configurarse por vista
    """
    
    # Mapeo de métodos HTTP a roles mínimos requeridos
    role_hierarchy = {
        'org_admin': 5,
        'iso_manager': 4,
        'auditor': 3,
        'user': 2,
        'viewer': 1,
    }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user_role = getattr(request, 'user_role', None)
        if not user_role:
            return False
        
        user_level = self.role_hierarchy.get(user_role, 0)
        
        # Obtener rol mínimo requerido de la vista
        required_role = getattr(view, 'required_role', 'viewer')
        required_level = self.role_hierarchy.get(required_role, 0)
        
        # Para métodos de escritura, puede requerirse un rol mayor
        if request.method not in permissions.SAFE_METHODS:
            write_role = getattr(view, 'write_required_role', required_role)
            required_level = self.role_hierarchy.get(write_role, required_level)
        
        return user_level >= required_level


# Decorador helper para vistas basadas en función
def role_required(roles):
    """
    Decorador para verificar roles en vistas basadas en función
    
    Uso:
        @api_view(['GET'])
        @role_required(['org_admin', 'iso_manager'])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_role = getattr(request, 'user_role', None)
            if user_role not in roles:
                from rest_framework.response import Response
                from rest_framework import status
                return Response(
                    {'detail': 'No tienes permisos para realizar esta acción.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
