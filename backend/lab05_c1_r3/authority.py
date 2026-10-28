"""Bind configured central tenant to immutable SQL authority, never request input."""
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def verify_principal():
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_user, session_user, tenant_id FROM lab_tenant_authority '
                       'WHERE principal = session_user')
        row = cursor.fetchone()
        expected = settings.DATABASES['default']['USER']
        if row != (expected, expected, settings.OWNER_ORGANIZATION_EXTERNAL_ID):
            raise RuntimeError('Central tenant / SQL principal binding mismatch')
        cursor.execute('SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb '
                       'FROM pg_roles WHERE rolname = session_user')
        if cursor.fetchone() != (False,) * 4:
            raise RuntimeError('Privileged SQL principal is forbidden')
    return row


class TenantPrincipalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            verify_principal()
        except Exception:
            return JsonResponse({'detail': 'Laboratory tenant authority unavailable.'}, status=503)
        return self.get_response(request)
