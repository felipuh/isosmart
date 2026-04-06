import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('isosmart')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en backend, integration y ai_modules
app.autodiscover_tasks(['backend', 'integration', 'ai_modules.sca', 'ai_modules.sie', 'tasks'])

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    # Tarea de prueba cada minuto
    'test-task-every-minute': {
        'task': 'backend.tasks.test_task',
        'schedule': crontab(minute='*/1'),
    },
    # Análisis de contexto diario a las 2 AM
    'analyze-context-daily': {
        'task': 'ai_modules.sca.tasks.analyze_context_periodic',
        'schedule': crontab(hour=2, minute=0),
    },
    # Sincronización de señales externas (ONU/IPCC/ISO) a las 6 AM
    'sync-external-context-signals-daily': {
        'task': 'ai_modules.sca.tasks.sync_external_context_signals',
        'schedule': crontab(hour=6, minute=0),
    },
    # Análisis de stakeholders diario a las 2:30 AM
    'analyze-stakeholders-daily': {
        'task': 'ai_modules.sie.tasks.analyze_stakeholders_periodic',
        'schedule': crontab(hour=2, minute=30),
    },
    # Evaluación de estado de facturación diaria a las 3 AM
    'evaluate-billing-status-daily': {
        'task': 'backend.tasks.evaluate_billing_statuses_task',
        'schedule': crontab(hour=3, minute=0),
    },
}

# Configuración adicional
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Costa_Rica',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')