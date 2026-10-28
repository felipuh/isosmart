from django.apps import AppConfig


class LeadershipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leadership'
    verbose_name = 'Leadership & Commitment (ISO 9001 Clause 5)'
    
    def ready(self):
        # Import signals if any
        try:
            import leadership.signals
        except ImportError:
            pass
