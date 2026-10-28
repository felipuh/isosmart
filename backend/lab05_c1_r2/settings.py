"""Synthetic settings; deliberately never import normal settings or dotenv."""
import json
import os
from pathlib import Path
import socket

ROOT = Path(os.environ['ISO_LAB_ROOT']).resolve()
if ROOT.parent != Path('/tmp') or not ROOT.name.startswith('iso-c1-r2-'):
    raise RuntimeError('Only a private disposable laboratory root is accepted')
config = json.loads((ROOT / 'runtime.json').read_text())
role = os.environ.get('ISO_LAB_ROLE', 'iso_owner')
if role not in ('iso_owner', 'iso_runtime_a', 'iso_runtime_b'):
    raise RuntimeError('Unknown laboratory principal')
SECRET_KEY = config['secret']
DEBUG = False
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'authentication.User'
INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'rest_framework', 'authentication', 'core', 'integration', 'foundation',
    'leadership', 'resources', 'planning', 'operations', 'performance', 'improvement',
    'ai_modules.common', 'ai_modules.sca', 'ai_modules.sie', 'ai_modules.asb', 'ai_modules.spm',
]
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql', 'NAME': 'iso_lab',
    'USER': role, 'PASSWORD': config['passwords'][role],
    'HOST': str(ROOT / 'socket'), 'PORT': '56439', 'CONN_MAX_AGE': 0,
}}
ROOT_URLCONF = 'lab05_c1_r2.urls'
MIDDLEWARE = []
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
LOGGING_CONFIG = None
ADMIN_APPS_INTEGRATION = {}
ALLOW_LOCAL_AUTH_FALLBACK = False
# No external calls are part of schema acceptance, including accidental clients.
_connect = socket.socket.connect

def isolated_connect(self, address):
    if self.family != socket.AF_UNIX:
        raise RuntimeError('Network access is outside this schema laboratory')
    return _connect(self, address)

socket.socket.connect = isolated_connect
