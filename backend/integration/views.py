"""
Integration endpoints for Admin Apps connectivity
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from django.conf import settings
from django.db import transaction

import json
import re
import httpx

from .client import admin_apps_client
from .models import AssistantConversation, AssistantMessage, AssistantMemoryItem, AssistantOrgProfile
from .services.vector_store import AssistantVectorSearchService
from .tasks import index_text_as_chunks
from ai_modules.integration.services.aims_governance_engine import AIMSGovernanceService


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aims_overview(request):
    """ISO/IEC 42001 AIMS overview and baseline maturity."""
    service = AIMSGovernanceService()
    payload = {
        'operation': 'aims_overview',
        'models': request.data.get('models') or [],
        'risks': request.data.get('risks') or [],
        'controls': request.data.get('controls') or [],
    }
    return Response(service.process(payload))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aims_model_lifecycle_check(request):
    service = AIMSGovernanceService()
    payload = {
        'operation': 'model_lifecycle_check',
        'models': request.data.get('models') or [],
    }
    return Response(service.process(payload))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aims_risk_register(request):
    service = AIMSGovernanceService()
    payload = {
        'operation': 'risk_register',
        'risks': request.data.get('risks') or [],
    }
    return Response(service.process(payload))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aims_audit_digest(request):
    service = AIMSGovernanceService()
    payload = {
        'operation': 'audit_log_digest',
        'events': request.data.get('events') or [],
    }
    return Response(service.process(payload))


def _sse(event, payload):
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _fallback_message(question, module_name='general'):
    base = (
        f"No tengo conexión al proveedor de IA en este momento. "
        f"Puedo ayudarte con orientación del módulo {module_name}."
    )
    return f"{base} Consulta recibida: {question[:220]}"


MODULE_GUIDANCE = {
    'general': 'Usa una mirada transversal del sistema de gestion y conecta la consulta con la clausula aplicable y el siguiente modulo a revisar.',
    'context': 'Enfoca tus respuestas en contexto de la organizacion, partes interesadas, alcance y riesgos externos/internos.',
    'stakeholders': 'Enfoca tus respuestas en identificacion, seguimiento y necesidades de partes interesadas.',
    'scope': 'Enfoca tus respuestas en limites, exclusiones justificadas, procesos incluidos y criterios de alcance.',
    'processes': 'Enfoca tus respuestas en enfoque a procesos, entradas, salidas, responsables, interacciones e indicadores.',
    'leadership': 'Enfoca tus respuestas en liderazgo, politica, roles, responsabilidades, compromiso y direccion estrategica.',
    'planning': 'Enfoca tus respuestas en riesgos, oportunidades, objetivos, planes de accion y gestion del cambio.',
    'resources': 'Enfoca tus respuestas en competencias, recursos, toma de conciencia, comunicacion e informacion documentada.',
    'operations': 'Enfoca tus respuestas en control operacional, requisitos, diseno, proveedores, produccion y liberacion.',
    'performance': 'Enfoca tus respuestas en seguimiento, medicion, auditoria interna, revision por la direccion y analisis.',
    'improvement': 'Enfoca tus respuestas en no conformidades, correccion, accion correctiva, verificacion de eficacia y mejora continua.',
    'settings': 'Enfoca tus respuestas en configuracion funcional del sistema y en como parametrizar el cumplimiento.',
}

STANDARD_PATTERNS = {
    'ISO 9001': [r'iso\s*9001', r'9001'],
    'ISO 14001': [r'iso\s*14001', r'14001'],
    'ISO 45001': [r'iso\s*45001', r'45001'],
    'ISO 27001': [r'iso\s*27001', r'27001', r'sgsi', r'seguridad de la informacion'],
    'ISO 42001': [r'iso\s*42001', r'42001', r'sistema de ia', r'inteligencia artificial'],
}


def _normalize_route_context(route_context):
    if not isinstance(route_context, dict):
        return {}
    return {
        'module': str(route_context.get('module') or '').strip(),
        'submodule': str(route_context.get('submodule') or '').strip(),
        'pageLabel': str(route_context.get('pageLabel') or '').strip(),
        'clauseHints': [str(item).strip() for item in (route_context.get('clauseHints') or []) if str(item).strip()],
        'primaryStandards': [str(item).strip() for item in (route_context.get('primaryStandards') or []) if str(item).strip()],
    }


def _detect_standards(question, route_context):
    normalized = question.lower()
    detected = []
    for standard, patterns in STANDARD_PATTERNS.items():
        if any(re.search(pattern, normalized) for pattern in patterns):
            detected.append(standard)

    if detected:
        return detected

    hinted = route_context.get('primaryStandards') or []
    return hinted[:2] if hinted else ['ISO 9001']


def _detect_clause_focus(question, route_context):
    clauses = re.findall(r'(?<!\d)([4-9]|10)(?:\.(\d+))?(?:\.(\d+))?(?!\d)', question)
    normalized = []
    for base, sub1, sub2 in clauses:
        value = base
        if sub1:
            value += f'.{sub1}'
        if sub2:
            value += f'.{sub2}'
        normalized.append(value)

    if normalized:
        seen = []
        for value in normalized:
            if value not in seen:
                seen.append(value)
        return seen[:4]

    return (route_context.get('clauseHints') or [])[:4]


def _build_assistant_prompt(
    base_prompt,
    module_name,
    route,
    route_context,
    question,
    org_id,
    profile_role,
    rag_chunks=None,
    org_profile=None,
    memory_items=None,
):
    effective_module = route_context.get('module') or module_name or 'general'
    module_guidance = MODULE_GUIDANCE.get(effective_module, MODULE_GUIDANCE['general'])
    standards = _detect_standards(question, route_context)
    clauses = _detect_clause_focus(question, route_context)
    page_label = route_context.get('pageLabel') or route or 'pantalla actual'
    submodule = route_context.get('submodule') or 'general_guidance'

    standards_text = ', '.join(standards)
    clauses_text = ', '.join(clauses) if clauses else 'sin clausula explicita'

    prompt = (
        f'{base_prompt} '
        'Responde con criterio tecnico y evita generalidades vacias. '
        'Si el usuario pide ayuda normativa, estructura la respuesta en: interpretacion, evidencia esperada y siguiente paso practico. '
        'Cuando cites una clausula, hazlo solo si estas razonablemente seguro; si no, indica que es una referencia probable. '
        'Prioriza la pantalla actual antes que una explicacion generica del sistema. '
        f'Normas objetivo para esta consulta: {standards_text}. '
        f'Clausulas prioritarias para esta consulta: {clauses_text}. '
        f'Modulo actual: {effective_module}. Submodulo actual: {submodule}. Pantalla actual: {page_label}. '
        f'Guia del modulo: {module_guidance} '
        f'Contexto sesion: organization_id={org_id}, role={profile_role}, route={route}.'
    )

    if org_profile:
        profile_lines = ['\n\nContexto persistente de la organizacion:']
        summary = (org_profile.organization_summary or '').strip()
        if summary:
            profile_lines.append(f'- Resumen organizacional: {summary}')
        if org_profile.industry:
            profile_lines.append(f'- Industria: {org_profile.industry}')
        if org_profile.risk_tolerance:
            profile_lines.append(f'- Tolerancia al riesgo: {org_profile.risk_tolerance}')
        if org_profile.primary_standards:
            profile_lines.append(f"- Normas primarias: {', '.join(org_profile.primary_standards)}")
        if org_profile.preferred_response_style:
            profile_lines.append(f'- Estilo preferido: {org_profile.preferred_response_style}')
        if org_profile.forbidden_topics:
            profile_lines.append(f"- Temas a evitar: {', '.join(org_profile.forbidden_topics)}")
        prompt += '\n'.join(profile_lines)

    if memory_items:
        memory_lines = [
            '\n\nMemoria estructurada relevante de la organizacion (usa cuando aplique y cita el titulo entre corchetes):'
        ]
        for i, item in enumerate(memory_items, start=1):
            parts = []
            if item.get('module'):
                parts.append(f"modulo={item.get('module')}")
            if item.get('standard_code'):
                parts.append(f"norma={item.get('standard_code')}")
            if item.get('clause_reference'):
                parts.append(f"clausula={item.get('clause_reference')}")
            tag = f" ({', '.join(parts)})" if parts else ''
            memory_lines.append(
                f"[{i}] {item.get('title', 'Memoria interna')}{tag}: {str(item.get('content') or '').strip()}"
            )
        prompt += '\n'.join(memory_lines)

    if rag_chunks:
        lines = ['\n\nEvidencia documental de la organizacion (usa estas fuentes si son relevantes; cita el titulo entre corchetes):']
        for i, chunk in enumerate(rag_chunks, start=1):
            title = chunk.get('source_title') or chunk.get('document_id') or 'Documento interno'
            text = chunk.get('chunk_text', '').strip()
            lines.append(f'[{i}] ({title}): {text}')
        prompt += '\n'.join(lines)

    return prompt


def _parse_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _load_recent_db_messages(conversation_obj, org_id, limit=8):
    if not conversation_obj or not org_id:
        return []

    rows = list(
        AssistantMessage.objects.filter(
            conversation=conversation_obj,
            organization_id=org_id,
            role__in=['user', 'assistant'],
        )
        .order_by('-created_at')[:limit]
        .values('role', 'content')
    )
    rows.reverse()
    return rows


def _get_org_profile(org_id):
    if not org_id:
        return None
    return AssistantOrgProfile.objects.filter(organization_id=org_id).first()


def _get_memory_items_for_prompt(org_id, module_name, standards, limit=5):
    if not org_id:
        return []

    queryset = AssistantMemoryItem.objects.filter(
        organization_id=org_id,
        is_active=True,
    )

    if module_name:
        queryset = queryset.filter(module__in=[module_name, ''])

    if standards:
        queryset = queryset.filter(standard_code__in=list(standards) + [''])

    return list(
        queryset.order_by('-confidence_score', '-updated_at')[:limit].values(
            'title',
            'content',
            'module',
            'standard_code',
            'clause_reference',
            'confidence_score',
        )
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assistant_stream(request):
    question = (request.data.get('question') or '').strip()
    route = (request.data.get('route') or '').strip()
    module_name = (request.data.get('module') or 'general').strip()
    route_context = _normalize_route_context(request.data.get('routeContext') or {})
    conversation_id = _parse_int(request.data.get('conversationId'))
    conversation = request.data.get('conversation') or []

    org_id = getattr(request, 'organization_id', None)
    profile_role = getattr(request, 'role', None)

    if not question:
        return Response({'detail': 'La pregunta es obligatoria.'}, status=status.HTTP_400_BAD_REQUEST)

    api_url = getattr(settings, 'AI_ASSISTANT_API_URL', None) or 'https://api.openai.com/v1/chat/completions'
    api_key = getattr(settings, 'AI_ASSISTANT_API_KEY', None)
    model = getattr(settings, 'AI_ASSISTANT_MODEL', None) or 'gpt-4o-mini'
    configured_prompt = getattr(settings, 'AI_ASSISTANT_SYSTEM_PROMPT', '').strip()

    conversation_obj = None
    db_recent_messages = []
    org_profile = _get_org_profile(org_id)
    if org_id:
        if conversation_id:
            conversation_obj = AssistantConversation.objects.filter(
                id=conversation_id,
                organization_id=org_id,
            ).first()

        if not conversation_obj:
            with transaction.atomic():
                conversation_obj = AssistantConversation.objects.create(
                    organization_id=org_id,
                    user=request.user,
                    title=question[:80] or 'Nueva conversación',
                    current_route=route,
                    current_module=route_context.get('module') or module_name,
                    current_submodule=route_context.get('submodule') or '',
                    last_standard_focus=(_detect_standards(question, route_context) or ['ISO 9001'])[0],
                    last_clause_focus=(_detect_clause_focus(question, route_context) or [''])[0],
                )

        AssistantMessage.objects.create(
            conversation=conversation_obj,
            organization_id=org_id,
            role='user',
            content=question,
            content_type='text',
        )

        AssistantConversation.objects.filter(id=conversation_obj.id).update(
            current_route=route,
            current_module=route_context.get('module') or module_name,
            current_submodule=route_context.get('submodule') or '',
            last_standard_focus=(_detect_standards(question, route_context) or ['ISO 9001'])[0],
            last_clause_focus=(_detect_clause_focus(question, route_context) or [''])[0],
        )
        db_recent_messages = _load_recent_db_messages(conversation_obj, org_id, limit=8)

    def event_stream():
        assistant_chunks = []
        base_prompt = configured_prompt or (
            'Eres un asistente para ISO Smart. Responde en español de forma breve, precisa y accionable. '
            'Prioriza orientación sobre módulos, cláusulas ISO y próximos pasos. '
            'Si falta información, dilo explícitamente y sugiere cómo obtenerla.'
        )

        standards = _detect_standards(question, route_context)
        effective_module = route_context.get('module') or module_name or 'general'
        memory_items = _get_memory_items_for_prompt(org_id, effective_module, standards, limit=5)

        # RAG: retrieve relevant chunks from organization's vector store
        rag_chunks = []
        if org_id:
            try:
                rag_chunks = AssistantVectorSearchService.search(
                    org_id=org_id,
                    query_text=question,
                    n_results=3,
                    module=effective_module,
                )
            except Exception:
                rag_chunks = []

        system_prompt = _build_assistant_prompt(
            base_prompt,
            module_name,
            route,
            route_context,
            question,
            org_id,
            profile_role,
            rag_chunks=rag_chunks,
            org_profile=org_profile,
            memory_items=memory_items,
        )

        messages = [{'role': 'system', 'content': system_prompt}]
        history_source = conversation[-8:] if conversation else db_recent_messages
        for item in history_source:
            role = item.get('role')
            content = item.get('content')
            if role in ['user', 'assistant'] and content:
                messages.append({'role': role, 'content': content})
        messages.append({'role': 'user', 'content': question})

        if not api_key:
            fallback = _fallback_message(question, module_name)
            assistant_chunks.append(fallback)
            yield _sse('chunk', {'text': fallback})
            if conversation_obj and org_id:
                AssistantMessage.objects.create(
                    conversation=conversation_obj,
                    organization_id=org_id,
                    role='assistant',
                    content=fallback,
                    content_type='text',
                    model_name='fallback',
                )
            yield _sse('done', {
                'ok': True,
                'provider': 'fallback',
                'conversation_id': conversation_obj.id if conversation_obj else None,
            })
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
                    assistant_chunks.append(fallback)
                    yield _sse('chunk', {'text': fallback})
                    if conversation_obj and org_id:
                        AssistantMessage.objects.create(
                            conversation=conversation_obj,
                            organization_id=org_id,
                            role='assistant',
                            content=fallback,
                            content_type='text',
                            model_name='fallback',
                        )
                    yield _sse('done', {
                        'ok': True,
                        'provider': 'fallback',
                        'error': f'provider_status_{response.status_code}',
                        'conversation_id': conversation_obj.id if conversation_obj else None,
                    })
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

                    choices = chunk.get('choices') or []
                    if not choices:
                        continue

                    delta = (
                        choices[0]
                        .get('delta', {})
                        .get('content', '')
                    )
                    if delta:
                        assistant_chunks.append(delta)
                        yield _sse('chunk', {'text': delta})

            final_text = ''.join(assistant_chunks).strip()
            if conversation_obj and org_id and final_text:
                AssistantMessage.objects.create(
                    conversation=conversation_obj,
                    organization_id=org_id,
                    role='assistant',
                    content=final_text,
                    content_type='text',
                    model_name=model,
                )

            yield _sse('done', {
                'ok': True,
                'provider': 'remote',
                'conversation_id': conversation_obj.id if conversation_obj else None,
            })
        except Exception as exc:
            fallback = _fallback_message(question, module_name)
            assistant_chunks.append(fallback)
            yield _sse('chunk', {'text': fallback})
            if conversation_obj and org_id:
                AssistantMessage.objects.create(
                    conversation=conversation_obj,
                    organization_id=org_id,
                    role='assistant',
                    content=fallback,
                    content_type='text',
                    model_name='fallback',
                )
            yield _sse('done', {
                'ok': True,
                'provider': 'fallback',
                'error': str(exc)[:180],
                'conversation_id': conversation_obj.id if conversation_obj else None,
            })

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assistant_state(request):
    org_id = getattr(request, 'organization_id', None)
    if not org_id:
        return Response({'detail': 'organization_id no disponible en la sesión.'}, status=status.HTTP_400_BAD_REQUEST)

    requested_id = _parse_int(request.query_params.get('conversation_id'))
    conversation_obj = None
    if requested_id:
        conversation_obj = AssistantConversation.objects.filter(
            id=requested_id,
            organization_id=org_id,
            user=request.user,
        ).first()

    if not conversation_obj:
        conversation_obj = (
            AssistantConversation.objects.filter(
                organization_id=org_id,
                user=request.user,
                status='active',
            )
            .order_by('-updated_at')
            .first()
        )

    if not conversation_obj:
        return Response({'ok': True, 'conversation_id': None, 'messages': []})

    db_messages = _load_recent_db_messages(conversation_obj, org_id, limit=30)
    return Response({
        'ok': True,
        'conversation_id': conversation_obj.id,
        'title': conversation_obj.title,
        'messages': db_messages,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def index_document(request):
    org_id = getattr(request, 'organization_id', None)
    if not org_id:
        return Response({'detail': 'organization_id no disponible en la sesión.'}, status=status.HTTP_400_BAD_REQUEST)

    document_id = str(request.data.get('document_id') or '').strip()
    text = str(request.data.get('text') or '').strip()
    source_title = str(request.data.get('source_title') or '').strip()
    module = str(request.data.get('module') or '').strip()
    standard_code = str(request.data.get('standard_code') or '').strip()
    clause_reference = str(request.data.get('clause_reference') or '').strip()

    if not document_id or not text:
        return Response(
            {'detail': 'document_id y text son obligatorios.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    task = index_text_as_chunks.delay(
        org_id=org_id,
        document_id=document_id,
        text=text,
        source_title=source_title,
        module=module,
        standard_code=standard_code,
        clause_reference=clause_reference,
        version=1,
    )
    return Response({
        'ok': True,
        'queued': True,
        'task_id': task.id,
        'organization_id': org_id,
        'document_id': document_id,
    }, status=status.HTTP_202_ACCEPTED)
