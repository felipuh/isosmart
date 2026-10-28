"""
Backend de Autenticación personalizado para ISO Smart
Permite autenticación con email en lugar de username
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import DatabaseError

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend de autenticación que usa email como identificador
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        # También aceptar username como email (compatibilidad)
        if email is None:
            email = kwargs.get('username')
        
        if email is None:
            return None
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Ejecutar el hash de contraseña de todas formas
            # para evitar timing attacks
            User().set_password(password)
            return None
        except DatabaseError:
            # If DB schema is not up to date, avoid bubbling errors as HTTP 500.
            return None
        except Exception:
            return None
        
        try:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except Exception:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
