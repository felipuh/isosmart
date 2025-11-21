import os
from celery import Celery

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Crear aplicación Celery
app = Celery('isosmart')

# Cargar configuración desde Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en múltiples ubicaciones
app.autodiscover_tasks(['backend', 'tasks'])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')