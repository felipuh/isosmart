"""Centralized browser authentication cookie policy."""

from django.conf import settings

ACCESS_COOKIE = 'isosmart_access'
REFRESH_COOKIE = 'isosmart_refresh'


def set_auth_cookies(response, *, access, refresh):
    common = {'httponly': True, 'secure': settings.AUTH_COOKIE_SECURE,
              'samesite': settings.AUTH_COOKIE_SAMESITE, 'path': '/'}
    response.set_cookie(ACCESS_COOKIE, str(access), max_age=settings.AUTH_ACCESS_COOKIE_AGE, **common)
    response.set_cookie(REFRESH_COOKIE, str(refresh), max_age=settings.AUTH_REFRESH_COOKIE_AGE, **common)
    return response


def clear_auth_cookies(response):
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(name, path='/', samesite=settings.AUTH_COOKIE_SAMESITE)
    return response
