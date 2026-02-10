from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operations'
    verbose_name = 'Operations (ISO 9001 Clause 8)'
    
    def ready(self):
        try:
            import operations.signals
        except ImportError:
            pass
