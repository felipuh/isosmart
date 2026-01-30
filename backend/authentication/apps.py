"""
Configuración de la app de autenticación
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Autenticación'
    
    def ready(self):
        # Importar señales si las hay
        pass
