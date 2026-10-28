from django.apps import AppConfig


class PlanningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planning'
    verbose_name = 'Planning (ISO 9001 Clause 6)'
    
    def ready(self):
        try:
            import planning.signals
        except ImportError:
            pass
