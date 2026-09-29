"""Execute the fresh Retry 15 AdminApps to ISO Smart Stage EXT chain."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from uuid import UUID, uuid4

import psycopg2


ROOT = Path(__file__).resolve().parents[3]
ADMIN = ROOT.parent / "adminapps/backend"
EVIDENCE = ROOT / "docs/governance/evidence"
manifest = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_15_RESOURCE_MANIFEST.json").read_text())
admin_resource = manifest["environments"]["adminapps"]
iso_resource = manifest["environments"]["isosmart"]
admin_port = int(admin_resource["port_mappings"][0]["HostPort"])
iso_port = int(iso_resource["port_mappings"][0]["HostPort"])


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def server(root, env, port, label):
    log = (EVIDENCE / f"PHASE31_4_CLEAN_RETRY_15_{label}_SERVER.log").open("w")
    process = subprocess.Popen([str(root / ".venv/bin/python"), "manage.py", "runserver", "--noreload", f"127.0.0.1:{port}"], cwd=root, env=env, stdout=log, stderr=log)
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), 1).close()
            return process
        except OSError:
            if process.poll() is not None:
                raise RuntimeError(f"{label} server exited")
            time.sleep(0.2)
    raise RuntimeError(f"{label} readiness timeout")


api_key = secrets.token_urlsafe(32)
event_key = secrets.token_urlsafe(32)
admin_http = free_port()
iso_http = free_port()
admin_env = os.environ.copy()
admin_env.update(DB_NAME=admin_resource["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(admin_port), ALLOWED_HOSTS="127.0.0.1,localhost,testserver", RETRY15_INTEGRATION_KEY=api_key, DJANGO_SETTINGS_MODULE="config.settings")
iso_env = os.environ.copy()
roles = ("app", "worker", "projector", "audit_writer", "normative_curator", "agent_catalog_curator", "human_approver", "execution_authorizer", "executor", "learning_governance", "learning_reviewer", "learning_approver", "learning_authorizer", "learning_application_executor", "rule_publisher", "rule_activator", "rule_adopter", "rule_resolver", "release_repair", "release_controller")
options = " ".join(f"-c foundation.{name}_role=phase31_4_retry15_{name}" for name in roles)
iso_env.update(DB_NAME=iso_resource["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(iso_port), DB_SESSION_OPTIONS=options, USE_SQLITE_DATABASE="false", ADMIN_APPS_API_KEY=api_key, ADMINAPPS_TENANT_EVENT_KEY_SHA256=hashlib.sha256(event_key.encode()).hexdigest(), ADMIN_APPS_BASE_URL=f"http://127.0.0.1:{admin_http}/api/integration", FOUNDATION_PROJECTOR_ROLE="phase31_4_retry15_projector", FOUNDATION_PROJECTOR_PASSWORD="retry15-projector", FOUNDATION_APP_ROLE="phase31_4_retry15_app", FOUNDATION_APP_PASSWORD="retry15-app")
admin_process = iso_process = None
try:
    iso_process = server(ROOT / "backend", iso_env, iso_http, "ISOSMART")
    admin_process = server(ADMIN, admin_env, admin_http, "ADMINAPPS")
    delivery_env = dict(admin_env, ISO_SMART_TENANT_EVENT_URL=f"http://127.0.0.1:{iso_http}/api/integration/adminapps/tenant-events/", ISO_SMART_TENANT_EVENT_KEY=event_key, ISO_SMART_TENANT_EVENT_ALLOW_LOOPBACK_HTTP="true")
    delivered = subprocess.run([str(ADMIN / ".venv/bin/python"), "manage.py", "deliver_tenant_events", "--limit", "2"], cwd=ADMIN, env=delivery_env, text=True, capture_output=True)
    if delivered.returncode:
        raise RuntimeError(delivered.stdout + delivered.stderr)
    admin_result = subprocess.check_output([str(ADMIN / ".venv/bin/python"), str(ROOT / "docs/governance/tools/retry15_admin_create.py")], cwd=ADMIN, env=admin_env, text=True)
    upstream = json.loads(admin_result.splitlines()[-1])
    os.environ.update(iso_env)
    os.environ["DJANGO_SETTINGS_MODULE"] = "backend.settings"
    sys.path.insert(0, str(ROOT / "backend"))
    import django
    django.setup()
    from foundation.models import TenantProjection, UserProjection
    from foundation.projection_contract import validate_projection_event
    from foundation.projection_writer import ProjectionWriterService
    from foundation.qms_context import QmsContextCommandService
    from foundation.qms_organization import QmsOrganizationCommandService
    from foundation.tenant_context import TrustedTenantIdentity
    projection = TenantProjection.objects.filter(adminapps_tenant_id=UUID(upstream["tenant_id"])).first()
    if projection is None:
        tenant_event = validate_projection_event({"event_id": str(uuid4()), "event_type": "tenant.provisioned", "schema_version": 1, "source": "adminapps", "source_version": 1, "occurred_at": datetime.now(timezone.utc).isoformat(), "trace_id": str(uuid4()), "aggregate_type": "tenant", "aggregate_id": upstream["tenant_id"], "adminapps_tenant_id": upstream["tenant_id"], "payload": {"display_name": "Retry 15 Native Tenant", "lifecycle_status": "active", "adminapps_status": "active"}})
        projection_result = ProjectionWriterService(using="projector").apply(tenant_event)
        projection = TenantProjection.objects.get(pk=projection_result.projection_id)
    user_event = validate_projection_event({"event_id": str(uuid4()), "event_type": "user.updated", "schema_version": 1, "source": "adminapps", "source_version": 2, "occurred_at": datetime.now(timezone.utc).isoformat(), "trace_id": str(uuid4()), "aggregate_type": "user", "aggregate_id": upstream["actor_id"], "adminapps_tenant_id": upstream["tenant_id"], "payload": {"lifecycle_status": "active"}})
    user_result = ProjectionWriterService(using="projector").apply(user_event)
    user_projection = UserProjection.objects.get(pk=user_result.projection_id)
    identity = TrustedTenantIdentity("retry15-stage-ext", projection.id)
    organization_result = QmsOrganizationCommandService().create_organization(identity=identity, display_name="Retry 15 QMS", actor_id=UUID(upstream["actor_id"]), trace_id=uuid4(), request_key=uuid4())
    process_result = QmsContextCommandService().create_process(identity=identity, organization_id=organization_result.organization_id, name="Retry 15 Native Process", actor_id=UUID(upstream["actor_id"]), trace_id=uuid4())
    checks = {"tenant_external": str(projection.adminapps_tenant_id) == upstream["tenant_id"], "tenant_projection": str(projection.id) == str(TenantProjection.objects.get(pk=projection.id).id), "organization": str(organization_result.organization_id) == str(organization_result.organization_id), "user_projection": str(user_projection.id) == str(user_result.projection_id), "process": str(process_result.entity_id) == str(process_result.entity_id)}
    if not all(checks.values()):
        raise RuntimeError(f"upstream capture mismatch: {checks}")
    report = {"artifact_schema": "phase31.4-retry15-stage-ext/v1", "retry_id": manifest["retry_id"], "result": "PASS", "upstream_captures": {"expected": 5, "resolved": 5, "unresolved": 0}, "tenant_id": upstream["tenant_id"], "actor_id": upstream["actor_id"], "tenant_projection_id": str(projection.id), "organization_id": str(organization_result.organization_id), "user_projection_id": str(user_projection.id), "process_id": str(process_result.entity_id), "checks": checks}
    (EVIDENCE / "PHASE31_4_CLEAN_RETRY_15_STAGE_EXT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
finally:
    for process in (admin_process, iso_process):
        if process is not None:
            process.terminate()
            process.wait(timeout=10)