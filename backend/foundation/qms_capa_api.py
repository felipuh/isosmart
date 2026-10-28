"""HTTP application services for the source-defined Audit → Finding →
Nonconformity → CorrectiveAction slice.

The source catalogs define fields and the events ``audit.finding.created`` and
``nonconformity.detected``; they define no audit/NC/CAPA workflow states, so
statuses are recorded as supplied and no transitions are inferred. Tenant is
always derived from the validated principal.
"""

from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .models import (
    Evidence, Finding, Organization, QmsAudit, QmsCorrectiveAction,
    QmsNonconformity, RequirementControl, UserProjection,
)
from .qms_audit import QmsAuditCommandService
from .source_artifact_api import SourceArtifactAPIError, foundation_database_alias
from .tenant_context import trusted_tenant_context


def write_roles():
    """Deployment-configured AdminApps role claims allowed to mutate QMS records.

    The source artifacts define no QMS write-role policy (QMS_WRITE_POLICY_SEMANTICS_INSUFFICIENT),
    so writes fail closed until an operator supplies an explicit allow-list.
    """
    return frozenset(r for r in (str(x).strip() for x in getattr(settings, "QMS_WRITE_ROLES", ())) if r)


def capa_create_enabled():
    return bool(getattr(settings, "QMS_CAPA_CREATE_ENABLED", False))


def authorize_write(principal):
    roles = write_roles()
    if not roles:
        raise SourceArtifactAPIError(
            "QMS_WRITE_POLICY_NOT_ESTABLISHED",
            "QMS mutations are disabled until an authoritative write-role policy is configured", 403)
    if principal.role_code not in roles:
        raise SourceArtifactAPIError(
            "QMS_WRITE_ROLE_REQUIRED", "the authenticated role is not authorized to mutate QMS records", 403)


def capabilities(principal):
    can_write = bool(write_roles()) and principal.role_code in write_roles()
    return {
        "can_write": can_write,
        "write_policy_configured": bool(write_roles()),
        "capa_create_enabled": can_write and capa_create_enabled(),
        "capa_create_blocker": None if capa_create_enabled() else "CAUSE_REFERENCE_SEMANTICS_INSUFFICIENT",
    }


def list_owners(principal, *, using="app"):
    authorize_write(principal)
    using = foundation_database_alias(using)
    with _ctx(principal, using):
        qs = UserProjection.objects.using(using).filter(
            tenant_id=principal.tenant_id, lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
        ).order_by("email", "id")[:200]
        return {"results": [{"id": str(u.adminapps_user_id), "email": u.email or "", "role": u.role or ""} for u in qs]}


def _ctx(principal, using):
    return trusted_tenant_context(
        principal.identity, actor_id=principal.actor_id, trace_id=uuid4(), using=using,
    )


def _result(result):
    return {
        "id": str(result.entity_id),
        "event_id": str(result.event_id) if result.event_id else None,
        "outbox_id": str(result.outbox_id) if result.outbox_id else None,
        "audit_log_id": str(result.audit_id),
        "trace_id": str(result.trace_id),
    }


def _run(principal, using, label, call):
    using = foundation_database_alias(using)
    try:
        return call(QmsAuditCommandService(using=using), using)
    except ObjectDoesNotExist as exc:
        raise SourceArtifactAPIError(
            "REFERENCE_NOT_FOUND", f"{label} reference is not available in the authenticated tenant", 404,
        ) from exc
    except ValueError as exc:
        raise SourceArtifactAPIError("QMS_REQUEST_INVALID", str(exc), 422) from exc


def _audit_row(r):
    return {"id": str(r.id), "organization_id": str(r.organization_id), "scope": r.scope,
            "criteria": r.criteria, "status": r.status, "lead_auditor": r.lead_auditor,
            "created_at": r.created_at.isoformat()}


def _finding_row(r):
    return {"id": str(r.id), "organization_id": str(r.organization_id), "audit_id": str(r.audit_id),
            "requirement_id": str(r.requirement_id), "type": r.finding_type, "statement": r.statement,
            "evidence_id": str(r.evidence_id), "created_at": r.created_at.isoformat()}


def _nc_row(r):
    return {"id": str(r.id), "organization_id": str(r.organization_id), "source_type": r.source_type,
            "source_id": str(r.source_id), "description": r.description, "severity": r.severity,
            "status": r.status, "created_at": r.created_at.isoformat()}


def _capa_row(r):
    return {"id": str(r.id), "organization_id": str(r.organization_id), "nc_id": str(r.nonconformity_id),
            "cause_id": str(r.cause_id), "action": r.action, "owner_id": str(r.owner_id),
            "due_date": r.due_date.isoformat(),
            "effectiveness_check_id": str(r.effectiveness_check_id) if r.effectiveness_check_id else None,
            "created_at": r.created_at.isoformat()}


def create_audit(principal, data, *, trace_id, using="app"):
    return _result(_run(principal, using, "organization", lambda svc, u: svc.create_audit(
        identity=principal.identity, organization_id=data["organization_id"], scope=data["scope"],
        criteria=data["criteria"], status=data["status"], lead_auditor=data["lead_auditor"],
        actor_id=principal.actor_id, trace_id=trace_id)))


def create_finding(principal, data, *, trace_id, using="app"):
    return _result(_run(principal, using, "audit, requirement or evidence", lambda svc, u: svc.create_finding(
        identity=principal.identity, audit_id=data["audit_id"], requirement_id=data["requirement_id"],
        finding_type=data["type"], statement=data["statement"], evidence_id=data["evidence_id"],
        actor_id=principal.actor_id, trace_id=trace_id)))


def create_nonconformity(principal, finding_id, data, *, trace_id, using="app"):
    def call(svc, u):
        with _ctx(principal, u):
            if QmsNonconformity.objects.using(u).filter(source_type="finding", source_id=finding_id).exists():
                raise SourceArtifactAPIError(
                    "NONCONFORMITY_ALREADY_EXISTS", "a nonconformity already exists for this finding", 409)
        return svc.create_nonconformity_from_finding(
            identity=principal.identity, finding_id=finding_id, description=data["description"],
            severity=data["severity"], status=data["status"], actor_id=principal.actor_id, trace_id=trace_id)
    return _result(_run(principal, using, "finding", call))


def create_corrective_action(principal, nc_id, data, *, trace_id, using="app"):
    if not capa_create_enabled():
        raise SourceArtifactAPIError(
            "CAPA_CAUSE_REFERENCE_UNDEFINED",
            "CorrectiveAction.cause_id has no source-defined Cause contract; creation is blocked", 409)
    def call(svc, u):
        with _ctx(principal, u):
            QmsNonconformity.objects.using(u).get(pk=nc_id)
            if not UserProjection.objects.using(u).filter(
                adminapps_user_id=data["owner_id"], tenant_id=principal.tenant_id,
                lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
            ).exists():
                raise SourceArtifactAPIError(
                    "OWNER_NOT_IN_TENANT", "owner_id must be an active user of the authenticated tenant", 422)
        return svc.create_corrective_action(
            identity=principal.identity, nonconformity_id=nc_id, cause_id=data["cause_id"],
            action=data["action"], owner_id=data["owner_id"], due_date=data["due_date"],
            actor_id=principal.actor_id, trace_id=trace_id)
    return _result(_run(principal, using, "nonconformity", call))


def _list(principal, using, model, row, filters=None, order="-created_at"):
    using = foundation_database_alias(using)
    with _ctx(principal, using):
        qs = model.objects.using(using).filter(tenant_id=principal.tenant_id, **(filters or {}))
        return {"results": [row(r) for r in qs.order_by(order, "id")[:500]]}


def list_audits(principal, *, using="app"):
    return _list(principal, using, QmsAudit, _audit_row)


def list_findings(principal, *, audit_id=None, using="app"):
    return _list(principal, using, Finding, _finding_row, {"audit_id": audit_id} if audit_id else None)


def list_nonconformities(principal, *, using="app"):
    return _list(principal, using, QmsNonconformity, _nc_row)


def list_corrective_actions(principal, *, nc_id=None, using="app"):
    return _list(principal, using, QmsCorrectiveAction, _capa_row, {"nonconformity_id": nc_id} if nc_id else None)


def list_evidence(principal, *, organization_id=None, using="app"):
    return _list(principal, using, Evidence, lambda r: {
        "id": str(r.id), "organization_id": str(r.organization_id), "source_type": r.source_type,
        "source_uri": r.source_uri, "captured_at": r.captured_at.isoformat(),
    }, {"organization_id": organization_id} if organization_id else None)


def list_requirements(principal, *, using="app"):
    using = foundation_database_alias(using)
    with _ctx(principal, using):
        rows = RequirementControl.objects.using(using).select_related("clause").order_by("clause__code", "id")[:500]
        return {"results": [{"id": str(r.id), "clause": r.clause.code, "paraphrase": r.paraphrase} for r in rows]}


def list_organizations(principal, *, using="app"):
    using = foundation_database_alias(using)
    with _ctx(principal, using):
        rows = Organization.objects.using(using).filter(tenant_id=principal.tenant_id).order_by("display_name", "id")
        return {"results": [{"id": str(r.id), "display_name": r.display_name} for r in rows]}
