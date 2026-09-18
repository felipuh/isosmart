"""Native, authorized QMS organization creation independent of Phase 31.4."""

import json
from dataclasses import dataclass
from uuid import UUID, uuid4

from django.conf import settings
from django.db import connections
from django.utils import timezone

from integration.client import admin_apps_client

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash
from .models import DomainEvent, Organization, TenantProjection, TransactionalOutbox
from .tenant_context import TrustedTenantIdentity, trusted_tenant_context


class OrganizationAuthorizationError(PermissionError):
    pass


class OrganizationRequestConflict(ValueError):
    pass


@dataclass(frozen=True)
class OrganizationCreationResult:
    organization_id: UUID
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID
    trace_id: UUID
    replay: bool = False


class QmsOrganizationCommandService:
    """Create one local QMS aggregate per request key; many per tenant are allowed."""

    ALLOWED_ROLES = frozenset({'superadmin', 'admin', 'org_admin', 'iso_manager'})

    def __init__(self, *, using='app', authority=None):
        self.using = using
        self.authority = authority or admin_apps_client

    def create_organization(self, *, identity, display_name, actor_id, trace_id,
                            request_key, legal_name=None, correlation_id=None,
                            fail_before_commit=False):
        if not isinstance(identity, TrustedTenantIdentity):
            raise TypeError('trusted tenant identity is required')
        actor_id = UUID(str(actor_id))
        trace_id = UUID(str(trace_id))
        request_key = UUID(str(request_key))
        correlation_id = UUID(str(correlation_id)) if correlation_id else None
        display_name = str(display_name or '').strip()
        legal_name = str(legal_name or '').strip() or None
        if not display_name or len(display_name) > 255 or (legal_name and len(legal_name) > 255):
            raise ValueError('valid organization display name and legal name are required')
        request_hash = canonical_hash({'tenant_id': str(identity.tenant_id),
                                       'actor_id': str(actor_id), 'display_name': display_name,
                                       'legal_name': legal_name})
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            try:
                tenant = TenantProjection.objects.using(self.using).get(pk=identity.tenant_id)
            except TenantProjection.DoesNotExist as exc:
                raise OrganizationAuthorizationError('tenant projection not found') from exc
            if tenant.lifecycle_status != 'active':
                raise OrganizationAuthorizationError('tenant is not active')
            external_id = str(tenant.adminapps_tenant_id)
            access = self.authority.validate_product_access(
                external_id, settings.ISO_SMART_PRODUCT_CODE, use_cache=False,
                allow_local_fallback=False,
            )
            if access.get('allowed') is not True or access.get('source') != 'adminapps' or access.get('fallback'):
                raise OrganizationAuthorizationError('AdminApps product entitlement denied')
            actor = self.authority.get_user(str(actor_id), organization_id=external_id)
            if str(actor.get('id')) != str(actor_id) or actor.get('is_active') is not True:
                raise OrganizationAuthorizationError('AdminApps actor is not active')
            memberships = actor.get('organizations') or []
            if not any(str(m.get('id')) == external_id and m.get('role') in self.ALLOWED_ROLES
                       for m in memberships):
                raise OrganizationAuthorizationError('actor lacks QMS organization creation scope')
            with connections[self.using].cursor() as cursor:
                cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',
                               [f'qms-organization-create:{identity.tenant_id}:{request_key}'])
                cursor.execute(
                    'SELECT request_hash,result FROM qms.organization_create_request '
                    'WHERE tenant_id=%s AND request_key=%s',
                    [str(identity.tenant_id), str(request_key)],
                )
                prior = cursor.fetchone()
            if prior:
                if prior[0] != request_hash:
                    raise OrganizationRequestConflict('request key was used with different inputs')
                result = json.loads(prior[1]) if isinstance(prior[1], str) else prior[1]
                return OrganizationCreationResult(
                    UUID(result['organization_id']), UUID(result['event_id']),
                    UUID(result['outbox_id']), UUID(result['audit_id']),
                    UUID(result['trace_id']), True,
                )
            occurred_at = timezone.now()
            organization = Organization.objects.using(self.using).create(
                tenant_id=identity.tenant_id, display_name=display_name, legal_name=legal_name,
            )
            event_id = uuid4()
            payload = {'organization_id': str(organization.id), 'tenant_id': str(identity.tenant_id),
                       'display_name': display_name, 'legal_name': legal_name,
                       'actor_id': str(actor_id), 'request_key': str(request_key)}
            DomainEvent.objects.using(self.using).create(
                event_id=event_id, tenant_id=identity.tenant_id,
                event_type='organization.created', schema_version=1,
                aggregate_type='organization', aggregate_id=organization.id,
                aggregate_version=1, occurred_at=occurred_at, trace_id=trace_id,
                correlation_id=correlation_id, source='iso-smart-qms',
                payload=payload, payload_hash=canonical_hash(payload),
            )
            outbox = TransactionalOutbox.objects.using(self.using).create(
                tenant_id=identity.tenant_id, domain_event_id=event_id,
                status=TransactionalOutbox.Status.PENDING, publish_attempts=0,
                available_at=occurred_at,
            )
            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=identity.tenant_id, stream_type='organization',
                stream_id=organization.id, actor_type='user', actor_id=str(actor_id),
                action='organization.created', entity_type='organization',
                entity_id=organization.id, trace_id=trace_id, occurred_at=occurred_at,
                after_hash=canonical_hash(payload),
                metadata={'event_id': str(event_id), 'request_key': str(request_key),
                          'correlation_id': str(correlation_id) if correlation_id else None},
            ))
            result = OrganizationCreationResult(organization.id, event_id, outbox.id, audit_id, trace_id)
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    'INSERT INTO qms.organization_create_request (tenant_id,request_key,request_hash,result) '
                    'VALUES (%s,%s,%s,%s::jsonb)',
                    [str(identity.tenant_id), str(request_key), request_hash,
                     json.dumps({key: str(getattr(result, key)) for key in
                                 ('organization_id', 'event_id', 'outbox_id', 'audit_id', 'trace_id')})],
                )
            if fail_before_commit:
                raise RuntimeError('organization creation rollback requested')
            return result
