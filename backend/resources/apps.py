from django.apps import AppConfig


class ResourcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resources'
    verbose_name = 'Resources & Support (ISO 9001 Clause 7)'
    
    def ready(self):
        try:
            import resources.signals
        except ImportError:
            pass
