"""DRF adapters for the QMS Audit → Finding → NC → CorrectiveAction slice."""

from rest_framework import serializers
from rest_framework.response import Response

from . import qms_capa_api as api
from .api_views import SourceArtifactAPIView
from .source_artifact_api import request_trace_id


class _Text(serializers.CharField):
    def __init__(self, **kw):
        kw.setdefault("max_length", 4000)
        super().__init__(**kw)


class AuditIn(serializers.Serializer):
    organization_id = serializers.UUIDField()
    scope = _Text()
    criteria = _Text()
    status = _Text(max_length=80)
    lead_auditor = _Text(max_length=255)


class FindingIn(serializers.Serializer):
    audit_id = serializers.UUIDField()
    requirement_id = serializers.UUIDField()
    type = _Text(max_length=80)
    statement = _Text()
    evidence_id = serializers.UUIDField()


class NonconformityIn(serializers.Serializer):
    description = _Text()
    severity = _Text(max_length=80)
    status = _Text(max_length=80)


class CorrectiveActionIn(serializers.Serializer):
    cause_id = serializers.UUIDField()
    action = _Text()
    owner_id = serializers.UUIDField()
    due_date = serializers.DateField()


def _uuid_param(request, name):
    value = request.query_params.get(name)
    if not value:
        return None
    field = serializers.UUIDField()
    try:
        return field.run_validation(value)
    except serializers.ValidationError:
        raise serializers.ValidationError({name: "must be a UUID"})


class _WriteView(SourceArtifactAPIView):
    """Resolves the principal and enforces the QMS write policy before any parsing."""

    def write_principal(self, request):
        principal = self.get_principal(request)
        api.authorize_write(principal)
        return principal


class _ListView(_WriteView):
    def get(self, request):
        return Response(self.fetch(self.get_principal(request), request))


class AuditsView(_ListView):
    def fetch(self, p, request):
        return api.list_audits(p)

    def post(self, request):
        principal = self.write_principal(request)
        s = AuditIn(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(api.create_audit(principal, s.validated_data,
                                         trace_id=request_trace_id(request)), status=201)


class FindingsView(_ListView):
    def fetch(self, p, request):
        return api.list_findings(p, audit_id=_uuid_param(request, "audit_id"))

    def post(self, request):
        principal = self.write_principal(request)
        s = FindingIn(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(api.create_finding(principal, s.validated_data,
                                           trace_id=request_trace_id(request)), status=201)


class NonconformitiesView(_ListView):
    def fetch(self, p, request):
        return api.list_nonconformities(p)


class FindingNonconformityView(_WriteView):
    def post(self, request, finding_id):
        principal = self.write_principal(request)
        s = NonconformityIn(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(api.create_nonconformity(principal, finding_id, s.validated_data,
                                                 trace_id=request_trace_id(request)), status=201)


class CorrectiveActionsView(_ListView):
    def fetch(self, p, request):
        return api.list_corrective_actions(p, nc_id=_uuid_param(request, "nc_id"))


class NonconformityCorrectiveActionView(_WriteView):
    def post(self, request, nc_id):
        principal = self.write_principal(request)
        s = CorrectiveActionIn(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(api.create_corrective_action(principal, nc_id, s.validated_data,
                                                     trace_id=request_trace_id(request)), status=201)


class QmsEvidenceView(_ListView):
    def fetch(self, p, request):
        return api.list_evidence(p, organization_id=_uuid_param(request, "organization_id"))


class QmsRequirementsView(_ListView):
    def fetch(self, p, request):
        return api.list_requirements(p)


class QmsOrganizationsView(_ListView):
    def fetch(self, p, request):
        return api.list_organizations(p)


class QmsCapabilitiesView(SourceArtifactAPIView):
    def get(self, request):
        return Response(api.capabilities(self.get_principal(request)))


class QmsOwnersView(_ListView):
    def fetch(self, p, request):
        return api.list_owners(p)
