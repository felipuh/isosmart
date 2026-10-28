"""Browser transport with explicit signed-cookie size and lifetime budgets."""
import time
from django.conf import settings
from rest_framework.exceptions import APIException

ACCESS_COOKIE = 'isosmart_access'
REFRESH_COOKIE = 'isosmart_refresh'
MAX_SET_COOKIE_BYTES = 4096
MAX_AUTH_COOKIE_HEADER_BYTES = 7000  # Reserve room for CSRF/other cookies in 8 KiB transports.


def set_auth_cookies(response, *, access, refresh):
    common = {'httponly': True, 'secure': settings.AUTH_COOKIE_SECURE,
              'samesite': settings.AUTH_COOKIE_SAMESITE, 'path': '/'}
    now = int(time.time())
    for name, token, age in ((ACCESS_COOKIE, access, settings.AUTH_ACCESS_COOKIE_AGE),
                             (REFRESH_COOKIE, refresh, settings.AUTH_REFRESH_COOKIE_AGE)):
        response.set_cookie(name, str(token), max_age=max(0, min(age, token['exp'] - now)), **common)
    sizes = [len(response.cookies[name].OutputString().encode('utf-8')) for name in (ACCESS_COOKIE, REFRESH_COOKIE)]
    header = '; '.join(name + '=' + response.cookies[name].value for name in (ACCESS_COOKIE, REFRESH_COOKIE))
    if max(sizes) > MAX_SET_COOKIE_BYTES or len(header.encode('utf-8')) > MAX_AUTH_COOKIE_HEADER_BYTES:
        # No token values in errors/logs. Reject rather than emit truncated authentication.
        clear_auth_cookies(response)
        raise APIException('La sesión excede el límite de transporte del navegador.')
    return response


def clear_auth_cookies(response):
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(name, path='/', samesite=settings.AUTH_COOKIE_SAMESITE)
    return response
