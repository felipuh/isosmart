"""Decision D: live, product-bound operation and object authorization.

This is an additional intersection with existing permissions. A missing policy
never falls back to IsAuthenticated, a role name, a query parameter, or a JWT.
"""
from rest_framework.exceptions import PermissionDenied, NotFound
from integration import central_auth
from integration.authorization_contract import CONTRACT, ACTIONS, role_scopes, valid_scopes


def deny():
    raise PermissionDenied('Operación no autorizada.')


def validate_evidence(data, required):
    evidence = data.get('authorization')
    product = central_auth.PRODUCT
    if not isinstance(evidence, dict) or data.get('active') is not True:
        deny()
    if (evidence.get('contract') != CONTRACT or evidence.get('state') != 'active'
            or evidence.get('principal_type') != 'user' or evidence.get('product') != product
            or any(evidence.get(k) != data.get(k) for k in
                   ('sub', 'tenant_id', 'client_id', 'product', 'role', 'sid', 'sg', 'av'))
            or not valid_scopes(evidence.get('scopes'), product)
            or evidence['scopes'] != role_scopes(evidence['scopes'], product, data.get('role'))
            or required not in evidence['scopes']):
        deny()
    return evidence


def resource_for(view):
    model = getattr(getattr(view, 'queryset', None), 'model', None)
    if model is None:
        deny()
    return model._meta.label_lower


# Writes are enabled only after field/relationship review. Other resources still
# receive read/object enforcement and fail closed for unreviewed mutations.
REVIEWED_WRITES = {'resources.resource', 'medsupplier.suppliercontact'}
STANDARD_ACTIONS = {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'}
# These actions only read the same scoped queryset. Composite responses (audit
# findings, versions, traceability, AI output) require separate resource grants
# and a domain policy before they can be enabled.
REVIEWED_READ_ACTIONS = {
    'resources.resource': {'by_type'},
    'resources.infrastructure': {'maintenance_due'},
    'resources.competence': {'gaps', 'by_user'},
    'resources.training': {'upcoming'},
    'resources.communication': {'pending'},
    'core.document': {'stats'},
    'performance.measurement': {'dashboard_stats'},
}


def action_enabled(resource, action, operation):
    if resource.startswith('integration.') or operation is None:
        return False
    if operation == 'read':
        return action in {'list', 'retrieve'} or action in REVIEWED_READ_ACTIONS.get(resource, ())
    return resource in REVIEWED_WRITES and action in STANDARD_ACTIONS
SENSITIVE_FIELDS = {'role', 'scopes', 'authorization', 'tenant_id', 'product', 'client_id',
                    'is_staff', 'is_superuser', 'permissions', 'created_by', 'updated_by',
                    'uploaded_by', 'approved_by', 'approved_at', 'is_approved', 'status',
                    'state', 'is_processed', 'processed_at', 'visibility', 'metadata', 'documentation'}


def authorize_request(request, view):
    if not getattr(request.user, 'is_authenticated', False) or not request.auth:
        deny()
    resource = resource_for(view)
    action = getattr(view, 'action', None)
    operation = ACTIONS.get(central_auth.PRODUCT, {}).get(resource, {}).get(action)
    if not action_enabled(resource, action, operation):
        deny()
    # A GET action can enqueue work. The action policy, never the HTTP method,
    # determines whether a call may reach business logic.
    data = central_auth.validate_session(request.auth, request.user)
    evidence = validate_evidence(data, f'{central_auth.PRODUCT}:{resource}:{operation}')
    organization_id = request.auth.get('organization_id')
    if type(organization_id) is not int or organization_id <= 0:
        deny()
    previous = getattr(request, 'organization_id', None)
    if previous is not None and str(previous) != str(organization_id):
        deny()
    for payload in (request.query_params, request.data):
        if not hasattr(payload, 'get'):
            deny()
        for key in ('organization', 'organization_id'):
            value = payload.get(key)
            if value is not None and str(value) != str(organization_id):
                deny()
        forbidden = SENSITIVE_FIELDS if payload is request.data else {'role', 'scopes', 'authorization', 'tenant_id', 'product', 'client_id', 'is_superuser', 'is_staff'}
        if any(key in payload for key in forbidden):
            deny()
    request.organization_id = organization_id
    # Only this request-local evidence is retained; never a cache across requests.
    request.functional_authorization = evidence
    return evidence


def object_tenant(obj, lookup):
    value = obj
    try:
        for part in lookup.split('__'):
            value = getattr(value, part)
        return value
    except (AttributeError, TypeError):
        return None


def authorize_object(request, view, obj):
    tenant = object_tenant(obj, view.organization_lookup_field)
    if tenant is None or str(tenant) != str(request.organization_id):
        raise NotFound('No encontrado.')
    if central_auth.PRODUCT == 'MEDSUPPLIER' and resource_for(view).startswith('medsupplier.'):
        from medsupplier.permissions import assert_object_allowed
        assert_object_allowed(obj, view.get_medsupplier_context())


class AuthorizedSerializerMixin:
    def get_fields(self):
        fields = super().get_fields()
        # Tenant identity is supplied by the authenticated context, never required
        # from input. Raw conflicting values were already rejected by the gate.
        for name in ('organization', 'organization_id'):
            if name in fields:
                fields[name].read_only = True
                fields[name].required = False
        return fields

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        view = self.context.get('view')
        if request is None or view is None or not getattr(request, 'functional_authorization', None):
            deny()
        for key, value in attrs.items():
            if key in SENSITIVE_FIELDS:
                deny()
            if value is None and self.instance is not None and hasattr(getattr(self.instance, key, None), '_meta'):
                deny()
            if isinstance(value, dict):
                deny()  # Nested mutation requires an explicit policy.
            values = value if isinstance(value, (tuple, list)) else [value]
            for related in values:
                if not hasattr(related, '_meta'):
                    continue
                # Reparenting is not an ordinary update, even inside one tenant.
                old = getattr(self.instance, key, None) if self.instance is not None else None
                if self.instance is not None and getattr(old, 'pk', old) != related.pk:
                    deny()
                from django.contrib.auth import get_user_model
                if isinstance(related, get_user_model()):
                    from authentication.models import UserProfile
                    if not UserProfile.objects.filter(user=related, organization_id=request.organization_id,
                                                      is_active=True).exists():
                        deny()
                else:
                    tenant = getattr(related, 'organization_id', None)
                    if tenant is None or str(tenant) != str(request.organization_id):
                        deny()
                    if central_auth.PRODUCT == 'MEDSUPPLIER' and resource_for(view).startswith('medsupplier.'):
                        from medsupplier.permissions import assert_object_allowed
                        assert_object_allowed(related, view.get_medsupplier_context())
        return attrs


def authorize_resources(request, resources):
    """Aggregate reads need every resource scope; one scope is never universal."""
    from types import SimpleNamespace as NS
    if not resources:
        deny()
    view = NS(queryset=NS(model=NS(_meta=NS(label_lower=resources[0]))), action='list')
    evidence = authorize_request(request, view)
    if any(f'{central_auth.PRODUCT}:{resource}:read' not in evidence['scopes'] for resource in resources):
        deny()
    return evidence
