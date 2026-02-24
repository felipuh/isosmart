"""
Integration endpoints for Admin Apps connectivity
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from django.conf import settings

import json
import httpx

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


def _sse(event, payload):
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _fallback_message(question, module_name='general'):
    base = (
        f"No tengo conexión al proveedor de IA en este momento. "
        f"Puedo ayudarte con orientación del módulo {module_name}."
    )
    return f"{base} Consulta recibida: {question[:220]}"


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assistant_stream(request):
    question = (request.data.get('question') or '').strip()
    route = (request.data.get('route') or '').strip()
    module_name = (request.data.get('module') or 'general').strip()
    conversation = request.data.get('conversation') or []

    org_id = getattr(request, 'organization_id', None)
    profile_role = getattr(request, 'role', None)

    if not question:
        return Response({'detail': 'La pregunta es obligatoria.'}, status=status.HTTP_400_BAD_REQUEST)

    api_url = getattr(settings, 'AI_ASSISTANT_API_URL', None) or 'https://api.openai.com/v1/chat/completions'
    api_key = getattr(settings, 'AI_ASSISTANT_API_KEY', None)
    model = getattr(settings, 'AI_ASSISTANT_MODEL', None) or 'gpt-4o-mini'

    def event_stream():
        system_prompt = (
            'Eres un asistente para ISO Smart. Responde en español de forma breve, precisa y accionable. '
            'Prioriza orientación sobre módulos, cláusulas ISO y próximos pasos. '
            f'Contexto sesión: organization_id={org_id}, role={profile_role}, module={module_name}, route={route}. '
            'Si falta información, dilo explícitamente y sugiere cómo obtenerla.'
        )

        messages = [{'role': 'system', 'content': system_prompt}]
        for item in conversation[-8:]:
            role = item.get('role')
            content = item.get('content')
            if role in ['user', 'assistant'] and content:
                messages.append({'role': role, 'content': content})
        messages.append({'role': 'user', 'content': question})

        if not api_key:
            fallback = _fallback_message(question, module_name)
            yield _sse('chunk', {'text': fallback})
            yield _sse('done', {'ok': True, 'provider': 'fallback'})
            return

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        }
        payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.2,
            'stream': True,
        }

        try:
            with httpx.stream('POST', api_url, headers=headers, json=payload, timeout=60.0) as response:
                if response.status_code >= 400:
                    fallback = _fallback_message(question, module_name)
                    yield _sse('chunk', {'text': fallback})
                    yield _sse('done', {'ok': True, 'provider': 'fallback', 'error': f'provider_status_{response.status_code}'})
                    return

                for line in response.iter_lines():
                    if not line:
                        continue
                    if not line.startswith('data:'):
                        continue

                    data_str = line[len('data:'):].strip()
                    if data_str == '[DONE]':
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    delta = (
                        chunk.get('choices', [{}])[0]
                        .get('delta', {})
                        .get('content', '')
                    )
                    if delta:
                        yield _sse('chunk', {'text': delta})

            yield _sse('done', {'ok': True, 'provider': 'remote'})
        except Exception as exc:
            fallback = _fallback_message(question, module_name)
            yield _sse('chunk', {'text': fallback})
            yield _sse('done', {'ok': True, 'provider': 'fallback', 'error': str(exc)[:180]})

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
