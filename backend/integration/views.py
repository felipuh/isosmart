"""
Integration endpoints for Admin Apps connectivity
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .client import admin_apps_client


def _bool_param(value, default=True):
    if value is None:
        return default
    return str(value).lower() in ['1', 'true', 'yes', 'y']


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_apps_health(request):
    """Proxy health check to Admin Apps"""
    result = admin_apps_client.health_check()
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_502_BAD_GATEWAY
    return Response(result, status=status_code)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organizations(request):
    """List organizations from Admin Apps"""
    use_cache = _bool_param(request.query_params.get('use_cache'), default=True)
    result = admin_apps_client.get_organizations(use_cache=use_cache)
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_502_BAD_GATEWAY
    return Response(result, status=status_code)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organization_detail(request, org_id):
    """Organization detail from Admin Apps"""
    use_cache = _bool_param(request.query_params.get('use_cache'), default=True)
    result = admin_apps_client.get_organization(org_id, use_cache=use_cache)
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_502_BAD_GATEWAY
    return Response(result, status=status_code)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organization_users(request, org_id):
    """Organization users from Admin Apps"""
    use_cache = _bool_param(request.query_params.get('use_cache'), default=True)
    result = admin_apps_client.get_organization_users(org_id, use_cache=use_cache)
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_502_BAD_GATEWAY
    return Response(result, status=status_code)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organization_modules(request, org_id):
    """Organization modules from Admin Apps"""
    use_cache = _bool_param(request.query_params.get('use_cache'), default=True)
    result = admin_apps_client.get_organization_modules(org_id, use_cache=use_cache)
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_502_BAD_GATEWAY
    return Response(result, status=status_code)
