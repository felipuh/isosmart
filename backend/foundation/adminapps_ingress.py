"""Authenticated AdminApps service API with durable provenance before projection."""

import hashlib
import hmac
import json

from django.conf import settings
from django.db import DatabaseError, connections, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .adminapps_adapter import ContractOnlyAdminAppsAdapter
from .projection_contract import ContractValidationError, validate_projection_event
from .projection_writer import ProjectionFailure, ProjectionWriterService


@csrf_exempt
@require_POST
def receive_tenant_event(request):
    expected = settings.ADMINAPPS_TENANT_EVENT_KEY_SHA256
    supplied = request.headers.get('X-API-Key', '')
    if not expected or not supplied or not hmac.compare_digest(
        hashlib.sha256(supplied.encode()).hexdigest(), expected
    ):
        return JsonResponse({'code': 'unauthenticated_adminapps_service'}, status=401)
    if len(request.body) > 65536:
        return JsonResponse({'code': 'event_too_large'}, status=413)
    if 'projector' not in connections.databases:
        return JsonResponse({'code': 'projector_not_configured'}, status=503)
    try:
        envelope = json.loads(request.body)
        event = validate_projection_event(envelope)
        if event.aggregate_type.value != 'tenant':
            raise ContractValidationError('tenant ingress accepts only tenant events')
    except (ValueError, TypeError, ContractValidationError):
        return JsonResponse({'code': 'invalid_tenant_event'}, status=422)
    payload_hash = hashlib.sha256(json.dumps(envelope, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    using = 'projector'
    with transaction.atomic(using=using):
        with connections[using].cursor() as cursor:
            cursor.execute("SELECT set_config('app.projection_source','adminapps',true)")
            cursor.execute(
                "INSERT INTO eventing.adminapps_ingress_receipt "
                "(event_id,adminapps_tenant_id,issuer,authenticated,payload_hash,schema_version,source_version,trace_id,status) "
                "VALUES (%s,%s,'adminapps',true,%s,%s,%s,%s,'received') ON CONFLICT (event_id) DO NOTHING",
                [str(event.event_id), str(event.adminapps_tenant_id), payload_hash,
                 event.schema_version, event.source_version, str(event.trace_id)],
            )
            cursor.execute(
                "SELECT payload_hash,status,projection_id FROM eventing.adminapps_ingress_receipt "
                "WHERE event_id=%s FOR UPDATE", [str(event.event_id)],
            )
            recorded_hash, recorded_status, projection_id = cursor.fetchone()
            if recorded_hash != payload_hash:
                return JsonResponse({'code': 'event_payload_conflict'}, status=409)
            if recorded_status == 'processed':
                cursor.execute(
                    "UPDATE eventing.adminapps_ingress_receipt SET replay_count=replay_count+1 WHERE event_id=%s",
                    [str(event.event_id)],
                )
                return JsonResponse({'result': 'idempotent_replay', 'projection_id': str(projection_id)})
        try:
            result = ContractOnlyAdminAppsAdapter(ProjectionWriterService(using=using)).receive(envelope)
        except (ProjectionFailure, ContractValidationError, DatabaseError) as exc:
            failure_code = getattr(exc, 'failure_code', 'projection_database_error')
            with connections[using].cursor() as cursor:
                cursor.execute(
                    "UPDATE eventing.adminapps_ingress_receipt SET status='failed',failure_code=%s WHERE event_id=%s",
                    [failure_code, str(event.event_id)],
                )
            return JsonResponse({'code': failure_code}, status=503 if isinstance(exc, DatabaseError) else 409)
        with connections[using].cursor() as cursor:
            cursor.execute(
                "UPDATE eventing.adminapps_ingress_receipt SET status='processed',failure_code=NULL,"
                "processed_at=statement_timestamp(),projection_id=%s WHERE event_id=%s",
                [str(result.projection_id), str(event.event_id)],
            )
        return JsonResponse({'result': result.kind.value, 'projection_id': str(result.projection_id)}, status=201)
