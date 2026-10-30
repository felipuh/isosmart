"""Fail-closed deployment policy. Pure functions: no settings, files or network I/O."""
from urllib.parse import urlsplit

FALSE = frozenset(('0', 'false', 'no', 'off'))
ALIASES = {'dev':'development', 'local':'development', 'prod':'production', 'stage':'staging', 'testing':'test'}
UNSAFE_FLAGS = ('DEBUG', 'ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS', 'ALLOW_LOCAL_AUTH_FALLBACK',
                'ADMIN_APPS_ALLOW_LOCAL_FALLBACK', 'ALLOW_SESSION_AUTH_FOR_DEV',
                'SMART3AI_SSO_ALLOW_2FA_BYPASS', 'USE_SQLITE_DATABASE')


def environment_name(value):
    value = str(value or '').strip().lower()
    return ALIASES.get(value, value)


def validate_startup_environment(env, product):
    """Reject unsafe intent before flags are silently masked by settings."""
    names = [environment_name(env[k]) for k in ('DJANGO_ENV', 'ENVIRONMENT') if k in env]
    name = names[0] if names else 'development'
    if name not in ('development', 'test', 'demo', 'staging', 'production') or any(n != name for n in names):
        raise RuntimeError('Unknown or conflicting deployment environment')
    if name not in ('staging', 'production'):
        return name
    if env.get('DJANGO_SETTINGS_MODULE', '') != 'backend.settings':
        raise RuntimeError('Operational environment requires backend.settings')
    required = ('DEBUG', 'ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS', 'ALLOW_SESSION_AUTH_FOR_DEV',
                'ALLOW_LOCAL_AUTH_FALLBACK' if product == 'ISO_SMART' else 'ADMIN_APPS_ALLOW_LOCAL_FALLBACK')
    for flag in UNSAFE_FLAGS:
        if (flag in required or flag in env) and str(env.get(flag, '')).strip().lower() not in FALSE:
            raise RuntimeError(flag + ' must be explicitly false')
    if product == 'ISO_SMART' and env.get('ISO_SMART_PRODUCT_CODE', 'ISO_SMART') != 'ISO_SMART':
        raise RuntimeError('Incorrect product identity')
    if product == 'MEDSUPPLIER' and str(env.get('ADMIN_APPS_REQUIRE_IDENTITY_SOURCE', 'true')).strip().lower() not in ('true', '1', 'yes', 'on'):
        raise RuntimeError('AdminApps must remain the identity authority')
    try:
        url = urlsplit(env.get('ADMIN_APPS_BASE_URL', ''))
        valid = (url.scheme == 'https' and url.hostname and not url.username and not url.password
                 and not url.query and not url.fragment)
        _ = url.port
    except (ValueError, TypeError):
        valid = False
    if not valid:
        raise RuntimeError('Explicit HTTPS AdminApps authority required')
    if not str(env.get('ADMIN_APPS_API_KEY', '')).strip() or env.get('ADMIN_APPS_API_KEY') == 'isosmart-integration-key-2025':
        raise RuntimeError('Explicit AdminApps integration credential required')
    return name


def local_fallback_allowed(settings, enabled):
    """Only explicit test/demo data fallback; never an authentication grant."""
    return (enabled is True
            and getattr(settings, 'IS_PRODUCTION', False) is False
            and environment_name(getattr(settings, 'ENVIRONMENT', None)) in ('test', 'demo'))
