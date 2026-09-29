"""Execute fresh Retry 14 Stage EXT and record the five live upstream bindings."""

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
STEM = "PHASE31_4_CLEAN_RETRY_14"
PREFIX = "phase31_4_retry14"
manifest = json.loads((EVIDENCE / f"{STEM}_RESOURCE_MANIFEST.json").read_text())
admin_resource = manifest["environments"]["adminapps"]
iso_resource = manifest["environments"]["isosmart"]
admin_db_port = int(admin_resource["port_mappings"][0]["HostPort"])
iso_db_port = int(iso_resource["port_mappings"][0]["HostPort"])


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_server(root: Path, env: dict[str, str], port: int, name: str):
    log = (EVIDENCE / f"{STEM}_{name}_SERVER.log").open("w")
    process = subprocess.Popen(
        [str(root / ".venv/bin/python"), "manage.py", "runserver", "--noreload", f"127.0.0.1:{port}"],
        cwd=root,
        env=env,
        stdout=log,
        stderr=log,
    )
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), 1).close()
            return process, log
        except OSError:
            if process.poll() is not None:
                raise RuntimeError(f"{name} server exited")
            time.sleep(0.2)
    raise RuntimeError(f"{name} readiness timeout")


event_key = secrets.token_urlsafe(32)
api_key = secrets.token_urlsafe(32)
admin_env = os.environ.copy()
admin_env.update(
    DB_NAME=admin_resource["database_name"],
    DB_USER="postgres",
    DB_PASSWORD="",
    DB_HOST="127.0.0.1",
    DB_PORT=str(admin_db_port),
    ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
    RETRY14_INTEGRATION_KEY=api_key,
)
upstream = json.loads(subprocess.check_output(
    [str(ADMIN / ".venv/bin/python"), str(ROOT / "docs/governance/tools/retry14_admin_create.py")],
    cwd=ADMIN,
    env=admin_env,
    text=True,
).splitlines()[-1])

role_names = (
    "app", "worker", "projector", "audit_writer", "normative_curator",
    "agent_catalog_curator", "human_approver", "execution_authorizer", "executor",
    "qms_action_owner", "learning_governance", "learning_reviewer", "learning_approver",
    "learning_authorizer", "learning_application_executor", "knowledge_rule_application_owner",
    "rule_governance_owner", "rule_publisher", "rule_activator", "rule_adopter",
    "rule_resolver", "release_repair", "release_controller",
)
options = " ".join(f"-c foundation.{name}_role={PREFIX}_{name}" for name in role_names)
app_password = secrets.token_urlsafe(24)
projector_password = secrets.token_urlsafe(24)
with psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=iso_db_port) as connection:
    with connection.cursor() as cursor:
        cursor.execute(f'ALTER ROLE "{PREFIX}_app" PASSWORD %s', [app_password])
        cursor.execute(f'ALTER ROLE "{PREFIX}_projector" PASSWORD %s', [projector_password])
    connection.commit()

iso_env = os.environ.copy()
iso_env.update(
    DB_NAME=iso_resource["database_name"],
    DB_USER="postgres",
    DB_PASSWORD="",
    DB_HOST="127.0.0.1",
    DB_PORT=str(iso_db_port),
    DB_SESSION_OPTIONS=options,
    USE_SQLITE_DATABASE="false",
    ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
    ADMIN_APPS_API_KEY=api_key,
    ADMINAPPS_TENANT_EVENT_KEY_SHA256=hashlib.sha256(event_key.encode()).hexdigest(),
    FOUNDATION_APP_ROLE=f"{PREFIX}_app",
    FOUNDATION_APP_PASSWORD=app_password,
    FOUNDATION_PROJECTOR_ROLE=f"{PREFIX}_projector",
    FOUNDATION_PROJECTOR_PASSWORD=projector_password,
)

iso_process = iso_log = admin_process = admin_log = None
try:
    iso_http = free_port()
    admin_http = free_port()
    iso_env["ADMIN_APPS_BASE_URL"] = f"http://127.0.0.1:{admin_http}/api/integration"
    iso_process, iso_log = start_server(ROOT / "backend", iso_env, iso_http, "ISOSMART")
    admin_process, admin_log = start_server(ADMIN, admin_env, admin_http, "ADMINAPPS")
    delivery_env = dict(
        admin_env,
        ISO_SMART_TENANT_EVENT_URL=f"http://127.0.0.1:{iso_http}/api/integration/adminapps/tenant-events/",
        ISO_SMART_TENANT_EVENT_KEY=event_key,
        ISO_SMART_TENANT_EVENT_ALLOW_LOOPBACK_HTTP="true",
    )
    delivery = subprocess.run(
        [str(ADMIN / ".venv/bin/python"), "manage.py", "deliver_tenant_events", "--limit", "2"],
        cwd=ADMIN,
        env=delivery_env,
        text=True,
        capture_output=True,
    )
    if delivery.returncode:
        raise RuntimeError(delivery.stdout + delivery.stderr)

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

    tenant_projection = TenantProjection.objects.get(adminapps_tenant_id=UUID(upstream["tenant_id"]))
    user_event_id = uuid4()
    user_result = ProjectionWriterService(using="projector").apply(validate_projection_event({
        "event_id": str(user_event_id),
        "event_type": "user.updated",
        "schema_version": 1,
        "source": "adminapps",
        "source_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "trace_id": str(uuid4()),
        "aggregate_type": "user",
        "aggregate_id": upstream["actor_id"],
        "adminapps_tenant_id": upstream["tenant_id"],
        "payload": {"lifecycle_status": "active"},
    }))
    user_projection = UserProjection.objects.get(pk=user_result.projection_id)
    identity = TrustedTenantIdentity("retry14-stage-ext", tenant_projection.id)
    actor_id = UUID(upstream["actor_id"])
    trace_id = uuid4()
    organization = QmsOrganizationCommandService().create_organization(
        identity=identity,
        display_name="Retry 14 QMS",
        actor_id=actor_id,
        trace_id=trace_id,
        request_key=uuid4(),
    )
    process = QmsContextCommandService().create_process(
        identity=identity,
        organization_id=organization.organization_id,
        name="Retry 14 Native Process",
        actor_id=actor_id,
        trace_id=trace_id,
    )

    with psycopg2.connect(
        dbname=iso_resource["database_name"], user="postgres", host="127.0.0.1", port=iso_db_port,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id,tenant_id,organization_id FROM qms.process WHERE id=%s", [str(process.entity_id)])
            persisted_process, process_tenant, process_organization = cursor.fetchone()
            cursor.execute("SELECT id,tenant_id FROM qms.organization WHERE id=%s", [str(organization.organization_id)])
            persisted_organization, organization_tenant = cursor.fetchone()
            cursor.execute(
                "SELECT id,adminapps_user_id,tenant_id FROM qms.user_projection WHERE id=%s",
                [str(user_projection.id)],
            )
            persisted_user, persisted_admin_user, user_tenant = cursor.fetchone()

    checks = {
        "tenant_external": str(tenant_projection.adminapps_tenant_id) == upstream["tenant_id"],
        "tenant_projection": str(tenant_projection.id) == str(process_tenant),
        "organization": str(organization.organization_id) == str(persisted_organization),
        "user_projection": str(user_projection.id) == str(persisted_user),
        "process": str(process.entity_id) == str(persisted_process),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Retry 14 upstream identity equality failure: {checks}")
    if str(user_projection.adminapps_user_id) != upstream["actor_id"] or str(persisted_admin_user) != upstream["actor_id"]:
        raise RuntimeError("Retry 14 AdminApps user identity mismatch")
    if str(user_tenant) != str(tenant_projection.id):
        raise RuntimeError("Retry 14 user projection tenant mismatch")
    if str(process_organization) != str(organization.organization_id):
        raise RuntimeError("Retry 14 process organization mismatch")

    captures = [
        {
            "semantic_identity": "AdminApps canonical tenant ID",
            "native_external_source": "AdminApps Organization API + transactional outbox",
            "returned_value": upstream["tenant_id"],
            "persisted_value": str(tenant_projection.adminapps_tenant_id),
            "contract_binding": "qms.tenant_projection.adminapps_tenant_id",
            "equality_result": "PASS",
        },
        {
            "semantic_identity": "TenantProjection ID",
            "native_external_source": "authenticated ISO Smart tenant ingress",
            "returned_value": str(tenant_projection.id),
            "persisted_value": str(tenant_projection.id),
            "contract_binding": "qms.tenant_projection.id",
            "equality_result": "PASS",
        },
        {
            "semantic_identity": "QMS Organization ID",
            "native_external_source": "QmsOrganizationCommandService.create_organization",
            "returned_value": str(organization.organization_id),
            "persisted_value": str(persisted_organization),
            "contract_binding": "qms.organization.id",
            "equality_result": "PASS",
        },
        {
            "semantic_identity": "UserProjection ID",
            "native_external_source": "ProjectionWriterService.apply(AdminApps canonical user)",
            "returned_value": str(user_result.projection_id),
            "persisted_value": str(persisted_user),
            "contract_binding": "qms.user_projection.id",
            "equality_result": "PASS",
        },
        {
            "semantic_identity": "Process ID",
            "native_external_source": "QmsContextCommandService.create_process",
            "returned_value": str(process.entity_id),
            "persisted_value": str(persisted_process),
            "contract_binding": "qms.process.id",
            "equality_result": "PASS",
        },
    ]
    report = {
        "artifact_schema": "phase31.4-retry14-stage-ext/v1",
        "retry_id": manifest["retry_id"],
        "result": "PASS",
        "delivery": "PASS",
        "provenance": "LIVE_UPSTREAM_NATIVE_CAPTURE",
        "adminapps_tenant_id": upstream["tenant_id"],
        "tenant_projection_id": str(tenant_projection.id),
        "adminapps_user_id": upstream["actor_id"],
        "user_projection_id": str(user_projection.id),
        "qms_organization_id": str(organization.organization_id),
        "process_id": str(process.entity_id),
        "persisted_process_id": str(persisted_process),
        "identity_separation": {
            "all_six_values_distinct": len({
                upstream["tenant_id"], str(tenant_projection.id), upstream["actor_id"],
                str(user_projection.id), str(organization.organization_id), str(process.entity_id),
            }) == 6,
            "adminapps_tenant_id": upstream["tenant_id"],
            "tenant_projection_id": str(tenant_projection.id),
            "adminapps_user_id": upstream["actor_id"],
            "user_projection_id": str(user_projection.id),
            "qms_organization_id": str(organization.organization_id),
            "process_id": str(process.entity_id),
        },
        "upstream_capture_resolution": {"expected": 5, "resolved": 5, "unresolved": 0},
        "upstream_captures": captures,
    }
    (EVIDENCE / f"{STEM}_STAGE_EXT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result": "PASS", "upstream": "5/5", "identity_separation": report["identity_separation"]["all_six_values_distinct"]}))
finally:
    for process, log in ((admin_process, admin_log), (iso_process, iso_log)):
        if process is not None:
            process.terminate()
            process.wait(timeout=10)
        if log is not None:
            log.close()
