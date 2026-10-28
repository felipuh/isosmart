"""Standalone opt-in HTTP settings; each runtime loads only its SQL credential."""
import json
import os
from pathlib import Path
import socket

ROOT = Path(os.environ['ISO_LAB_ROOT']).resolve()
if ROOT.parent != Path('/tmp') or not ROOT.name.startswith('iso-c1-r2-'):
    raise RuntimeError('Only a private disposable laboratory root is accepted')
role = os.environ['ISO_LAB_ROLE']
if role not in ('iso_runtime_a', 'iso_runtime_b'):
    raise RuntimeError('HTTP requires an unprivileged tenant principal')
r3 = json.loads((ROOT / 'http-config.json').read_text())
instance = json.loads((ROOT / ('instance-' + role + '.json')).read_text())
SECRET_KEY = r3['secret']
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
    'USER': role, 'PASSWORD': instance['sql_password'],
    'HOST': str(ROOT / 'socket'), 'PORT': '56439', 'CONN_MAX_AGE': 0,
}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
LOGGING_CONFIG = None
DEBUG = True  # Existing central contract permits HTTP only in explicit debug labs.
ALLOWED_HOSTS = ['127.0.0.1']
ROOT_URLCONF = 'lab05_c1_r3.urls'
MIDDLEWARE = ['lab05_c1_r3.authority.TenantPrincipalMiddleware',
              'django.middleware.csrf.CsrfViewMiddleware']
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['authentication.cookie_auth.CookieJWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
SSO_CENTRAL_TRUST = r3['central_trust']
assert 'PRIVATE_KEY' not in SSO_CENTRAL_TRUST
SSO_LOCAL_TRUST = r3['local_trust']
ADMIN_APPS_SSO = r3['sso']
ADMIN_APPS_INTEGRATION = {'API_KEY': r3['credential'], 'TIMEOUT': 2, 'ENABLED': True}
OWNER_ORGANIZATION_ONLY_ACCESS = True
OWNER_ORGANIZATION_EXTERNAL_ID = instance['tenant']
ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS = False
ALLOW_LOCAL_AUTH_FALLBACK = False
AUTH_COOKIE_SECURE = False  # Loopback only; production cookie settings are untouched.
AUTH_COOKIE_SAMESITE = 'Lax'
AUTH_ACCESS_COOKIE_AGE = AUTH_REFRESH_COOKIE_AGE = 300
PASSWORD_HASHERS = ['django.contrib.auth.hashers.PBKDF2PasswordHasher']
_connect = socket.socket.connect


def loopback_connect(self, address):
    if self.family == socket.AF_UNIX:
        return _connect(self, address)
    if self.family != socket.AF_INET or address != ('127.0.0.1', r3['central_port']):
        raise RuntimeError('Undeclared network destination outside the R3 laboratory')
    return _connect(self, address)


socket.socket.connect = loopback_connect
