import multiprocessing

# Configuración del servidor
bind = "127.0.0.1:8001"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Logging
accesslog = "/home/aplicacion/projects/isosmart/logs/ai/gunicorn_access.log"
errorlog = "/home/aplicacion/projects/isosmart/logs/ai/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Proceso
daemon = False
pidfile = None
user = "aplicacion"
group = "aplicacion"

# Seguridad
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Directorio de trabajo
chdir = "/home/aplicacion/projects/isosmart/backend"

# Recargar automáticamente en cambios (solo desarrollo)
reload = False

# Variables de entorno
raw_env = [
    "DJANGO_SETTINGS_MODULE=backend.settings",
    "PYTHONPATH=/home/aplicacion/projects/isosmart/backend",
]
