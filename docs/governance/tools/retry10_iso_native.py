"""Validate fresh authenticated projection and native QMS commands."""

import json
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from django.db import connections
from foundation.models import TenantProjection
from foundation.tenant_context import TrustedTenantIdentity
from foundation.qms_organization import QmsOrganizationCommandService
from foundation.qms_context import QmsContextCommandService
from foundation.risk_objective import RiskOpportunityObjectiveCommandService

upstream = json.loads(os.environ["RETRY10_UPSTREAM_JSON"])
with connections["default"].cursor() as cursor:
    cursor.execute("SELECT event_id, authenticated, status, projection_id, source_version FROM eventing.adminapps_ingress_receipt WHERE event_id=%s", [upstream["event_id"]])
    receipt = cursor.fetchone()
    if not receipt or str(receipt[0]) != upstream["event_id"] or not receipt[1] or receipt[2] != "processed":
        raise RuntimeError("authenticated ingress receipt is missing or incomplete")
projection = TenantProjection.objects.using("default").get(adminapps_tenant_id=UUID(upstream["tenant_id"]))
if projection.id != receipt[3] or projection.source_version != upstream["source_version"]:
    raise RuntimeError("canonical tenant projection differs from upstream event")
identity = TrustedTenantIdentity("retry10-authorized-upstream", projection.id)
actor = UUID(upstream["actor_id"])
trace = uuid4()
organization = QmsOrganizationCommandService().create_organization(
    identity=identity, display_name="Retry 10 QMS", actor_id=actor, trace_id=trace, request_key=uuid4())
process = QmsContextCommandService().create_process(
    identity=identity, organization_id=organization.organization_id, name="Native process",
    actor_id=actor, trace_id=trace)
opportunity = RiskOpportunityObjectiveCommandService().create_opportunity(
    identity=identity, process_id=process.entity_id, hypothesis="Controlled opportunity",
    benefit="Improved quality", feasibility="Feasible", status="identified",
    actor_id=actor, trace_id=trace)
successor = RiskOpportunityObjectiveCommandService().revise_opportunity(
    identity=identity, opportunity_id=opportunity.entity_id, process_id=process.entity_id,
    hypothesis="Controlled opportunity revision", benefit="Improved quality",
    feasibility="Feasible", status="identified", actor_id=actor, trace_id=trace)
with connections["default"].cursor() as cursor:
    cursor.execute("SELECT id,lineage_id,revision,previous_revision_id,process_id FROM qms.opportunity WHERE id IN (%s,%s) ORDER BY revision", [str(opportunity.entity_id), str(successor.entity_id)])
    revisions = cursor.fetchall()
    cursor.execute("SELECT count(*) FROM eventing.domain_event WHERE tenant_id=%s", [str(projection.id)])
    events = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM eventing.transactional_outbox WHERE tenant_id=%s", [str(projection.id)])
    outbox = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM audit.immutable_audit_log WHERE tenant_id=%s", [str(projection.id)])
    audit = cursor.fetchone()[0]
if len(revisions) != 2 or revisions[1][1] != revisions[0][1] or revisions[1][2] != revisions[0][2] + 1 or revisions[1][3] != revisions[0][0] or revisions[1][4] != process.entity_id:
    raise RuntimeError("controlled revision lineage check failed")
print(json.dumps({"result": "PASS", "tenant_id": upstream["tenant_id"], "projection_id": str(projection.id),
                  "ingress_receipt": str(receipt[0]), "organization_id": str(organization.organization_id),
                  "organization_event_id": str(organization.event_id), "organization_audit_id": str(organization.audit_id),
                  "process_id": str(process.entity_id), "opportunity_id": str(opportunity.entity_id),
                  "successor_id": str(successor.entity_id), "revision": revisions[1][2],
                  "event_count": events, "outbox_count": outbox, "audit_count": audit}))
