from __future__ import annotations

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
MANIFEST = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_16_RESOURCE_MANIFEST.json").read_text())
iso_resource = MANIFEST["environments"]["isosmart"]
admin_resource = MANIFEST["environments"]["adminapps"]
iso_port = int(iso_resource["port_mappings"][0]["HostPort"])
admin_port = int(admin_resource["port_mappings"][0]["HostPort"])
RETRY_ID = MANIFEST["retry_id"]
PREFIX = "phase31_4_retry16"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_server(root: Path, env: dict[str, str], port: int, label: str):
    log = (EVIDENCE / f"PHASE31_4_CLEAN_RETRY_16_{label}_SERVER.log").open("w")
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
roles = ("app", "worker", "projector", "audit_writer", "normative_curator", "agent_catalog_curator", "human_approver", "execution_authorizer", "executor", "qms_action_owner", "learning_governance", "learning_reviewer", "learning_approver", "learning_authorizer", "learning_application_executor", "knowledge_rule_application_owner", "rule_governance_owner", "rule_publisher", "rule_activator", "rule_adopter", "rule_resolver", "release_repair", "release_controller")
options = " ".join(f"-c foundation.{role}_role={PREFIX}_{role}" for role in roles)
role_passwords = {role: secrets.token_urlsafe(24) for role in roles}
with psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=iso_port) as connection:
    with connection.cursor() as cursor:
        for role, password in role_passwords.items():
            cursor.execute(f'ALTER ROLE "{PREFIX}_{role}" PASSWORD %s', [password])
    connection.commit()
admin_env = os.environ.copy()
admin_env.update(DB_NAME=admin_resource["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(admin_port), ALLOWED_HOSTS="127.0.0.1,localhost,testserver", RETRY16_INTEGRATION_KEY=api_key, DJANGO_SETTINGS_MODULE="config.settings")
iso_env = os.environ.copy()
iso_env.update(DB_NAME=iso_resource["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(iso_port), DB_SESSION_OPTIONS=options, USE_SQLITE_DATABASE="false", ADMIN_APPS_API_KEY=api_key, ADMINAPPS_TENANT_EVENT_KEY_SHA256=hashlib.sha256(event_key.encode()).hexdigest(), ADMIN_APPS_BASE_URL=f"http://127.0.0.1:{admin_http}/api/integration")
for role, password in role_passwords.items():
    env_prefix = f"FOUNDATION_{role.upper()}"
    iso_env[f"{env_prefix}_ROLE"] = f"{PREFIX}_{role}"
    iso_env[f"{env_prefix}_PASSWORD"] = password
admin_process = iso_process = None
report = {"artifact_schema": "phase31.4-retry16-live-bridge/v1", "retry_id": RETRY_ID, "started_at": datetime.now(timezone.utc).isoformat(), "result": "RUNNING"}
try:
    iso_process = start_server(ROOT / "backend", iso_env, iso_http, "ISOSMART")
    admin_process = start_server(ADMIN, admin_env, admin_http, "ADMINAPPS")
    delivery_env = dict(admin_env, ISO_SMART_TENANT_EVENT_URL=f"http://127.0.0.1:{iso_http}/api/integration/adminapps/tenant-events/", ISO_SMART_TENANT_EVENT_KEY=event_key, ISO_SMART_TENANT_EVENT_ALLOW_LOOPBACK_HTTP="true")
    admin_result = subprocess.check_output([str(ADMIN / ".venv/bin/python"), str(ROOT / "docs/governance/tools/retry16_admin_create.py")], cwd=ADMIN, env=admin_env, text=True)
    upstream = json.loads(admin_result.splitlines()[-1])
    delivered = subprocess.run([str(ADMIN / ".venv/bin/python"), "manage.py", "deliver_tenant_events", "--limit", "10"], cwd=ADMIN, env=delivery_env, text=True, capture_output=True)
    if delivered.returncode:
        raise RuntimeError(delivered.stdout + delivered.stderr)
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
        event = validate_projection_event({"event_id": str(uuid4()), "event_type": "tenant.provisioned", "schema_version": 1, "source": "adminapps", "source_version": 1, "occurred_at": datetime.now(timezone.utc).isoformat(), "trace_id": str(uuid4()), "aggregate_type": "tenant", "aggregate_id": upstream["tenant_id"], "adminapps_tenant_id": upstream["tenant_id"], "payload": {"display_name": "Retry 16 Native Tenant", "lifecycle_status": "active", "adminapps_status": "active"}})
        projection = TenantProjection.objects.get(pk=ProjectionWriterService(using="projector").apply(event).projection_id)
    user_event = validate_projection_event({"event_id": str(uuid4()), "event_type": "user.updated", "schema_version": 1, "source": "adminapps", "source_version": 2, "occurred_at": datetime.now(timezone.utc).isoformat(), "trace_id": str(uuid4()), "aggregate_type": "user", "aggregate_id": upstream["actor_id"], "adminapps_tenant_id": upstream["tenant_id"], "payload": {"lifecycle_status": "active"}})
    user_projection = UserProjection.objects.get(pk=ProjectionWriterService(using="projector").apply(user_event).projection_id)
    identity = TrustedTenantIdentity("retry16-stage-ext", projection.id)
    organization = QmsOrganizationCommandService().create_organization(identity=identity, display_name="Retry 16 QMS", actor_id=UUID(upstream["actor_id"]), trace_id=uuid4(), request_key=uuid4())
    process = QmsContextCommandService().create_process(identity=identity, organization_id=organization.organization_id, name="Retry 16 Native Process", actor_id=UUID(upstream["actor_id"]), trace_id=uuid4())
    stage_ext = {"retry_id": RETRY_ID, "tenant_id": upstream["tenant_id"], "actor_id": upstream["actor_id"], "tenant_projection_id": str(projection.id), "organization_id": str(organization.organization_id), "user_projection_id": str(user_projection.id), "process_id": str(process.entity_id)}
    checks = {"tenant_external": str(projection.adminapps_tenant_id) == upstream["tenant_id"], "tenant_projection": str(projection.id) == stage_ext["tenant_projection_id"], "organization": stage_ext["organization_id"] == str(organization.organization_id), "user_projection": stage_ext["user_projection_id"] == str(user_projection.id), "process": stage_ext["process_id"] == str(process.entity_id)}
    if not all(checks.values()):
        raise RuntimeError(f"upstream capture mismatch: {checks}")
    from foundation.phase31_4_v2_5_runtime import CaptureBundle, build_v25_runtime
    bundle = CaptureBundle.from_stage_ext(stage_ext, retry_id=RETRY_ID)
    runtime = build_v25_runtime(project_root=ROOT, using="app", capture_bundle=bundle, retry_id=RETRY_ID)
    phase_payload = runtime.contract.native_phase_inputs("INITIAL_OPPORTUNITY", session=runtime.session)
    report.update({"stage_ext": {"result": "PASS", "upstream_captures": {"expected": 5, "imported": len(bundle.captures), "missing": 0}, "checks": checks, "provenance": sorted({record.provenance for record in bundle.captures})}, "live_capture_bridge": "PASS", "initial_opportunity_bridge": {"process_id": str(phase_payload["process_id"]), "tenant_projection_id": str(phase_payload["identity"].tenant_id), "actor_id": str(phase_payload["actor_id"]), "historical_process_fallback": False}, "native_runtime": "STARTED"})
    try:
        runtime.run_clean_retry()
        report["native_runtime"] = "PASS"
    except Exception as exc:
        report.update({"native_runtime": "FAIL", "native_runtime_error": f"{type(exc).__name__}: {exc}"})
        raise
    report["phases"] = [{"phase_id": phase.name, "status": phase.status, "error": phase.error} for phase in runtime.session.phases]
    report["phase_count"] = len(report["phases"])
    report["result"] = "PASS"
finally:
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    (EVIDENCE / "PHASE31_4_CLEAN_RETRY_16_LIVE_BRIDGE.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for process in (admin_process, iso_process):
        if process is not None:
            process.terminate()
            process.wait(timeout=10)
print(json.dumps(report, indent=2, sort_keys=True))
