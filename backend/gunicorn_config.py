import multiprocessing
import os
from pathlib import Path


def _load_env_file(env_path):
    values = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value

    return values

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
env_file_values = _load_env_file(Path(chdir) / ".env")
env_vars = {
    "DJANGO_SETTINGS_MODULE": "backend.settings",
    "PYTHONPATH": chdir,
}

for key in [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "AI_DB_HOST",
    "AI_DB_PORT",
    "AI_DB_NAME",
    "AI_DB_USER",
    "AI_DB_PASSWORD",
    "AUDIT_DB_HOST",
    "AUDIT_DB_PORT",
    "AUDIT_DB_NAME",
    "AUDIT_DB_USER",
    "AUDIT_DB_PASSWORD",
    "ADMIN_APPS_API_KEY",
    "ADMIN_APPS_BASE_URL",
    "ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS",
    "SECRET_KEY",
]:
    value = os.getenv(key, env_file_values.get(key))
    if value:
        env_vars[key] = value

raw_env = [f"{key}={value}" for key, value in env_vars.items()]
