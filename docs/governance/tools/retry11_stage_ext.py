"""Fresh Retry 11 AdminApps tenant chain and native Process capture."""
from __future__ import annotations
import json, os, secrets, socket, subprocess, sys
from pathlib import Path
from uuid import UUID, uuid4
import psycopg2

ROOT = Path(__file__).resolve().parents[3]; ADMIN = ROOT.parent / "adminapps/backend"; EVIDENCE = ROOT / "docs/governance/evidence"
manifest = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_11_RESOURCE_MANIFEST.json").read_text())
admin = manifest["environments"]["adminapps"]; iso = manifest["environments"]["isosmart"]
ap = int(admin["port_mappings"][0]["HostPort"]); ip = int(iso["port_mappings"][0]["HostPort"])
def free():
    with socket.socket() as s: s.bind(("127.0.0.1", 0)); return s.getsockname()[1]
def start(root, env, port, name):
    log = open(EVIDENCE / f"PHASE31_4_CLEAN_RETRY_11_{name}_SERVER.log", "w")
    p = subprocess.Popen([str(root / ".venv/bin/python"), "manage.py", "runserver", "--noreload", f"127.0.0.1:{port}"], cwd=root, env=env, stdout=log, stderr=log)
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1): return p, log
        except OSError:
            if p.poll() is not None: raise RuntimeError(f"{name} server exited")
    raise RuntimeError(f"{name} server readiness timeout")

event_key = secrets.token_urlsafe(32); api_key = secrets.token_urlsafe(32); admin_env = os.environ.copy()
admin_env.update(DB_NAME=admin["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(ap), ALLOWED_HOSTS="127.0.0.1,localhost,testserver", RETRY11_INTEGRATION_KEY=api_key)
os.environ.update(DB_NAME=iso["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(ip), USE_SQLITE_DATABASE="false", ALLOWED_HOSTS="127.0.0.1,localhost,testserver", ADMIN_APPS_API_KEY=api_key, ADMINAPPS_TENANT_EVENT_KEY_SHA256=__import__('hashlib').sha256(event_key.encode()).hexdigest())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
sys.path.insert(0, str(ADMIN)); os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"; import django as admin_django; admin_django.setup()
from rest_framework.test import APIClient
from apps.users.models import User
from apps.organizations.models import Organization, TenantIntegrationOutbox
from apps.integration.models import IntegrationAPIKey
actor = User.objects.create_superuser(email="retry11-owner@example.test", password=secrets.token_urlsafe(32)); client = APIClient(); client.force_authenticate(user=actor)
r = client.post("/api/organizations/", {"name": "Retry 11 Native Tenant", "email": "retry11-tenant@example.test"})
if r.status_code != 201: raise RuntimeError(f"tenant create failed: {r.status_code} {r.data}")
organization = Organization.objects.get(pk=r.data["id"]); IntegrationAPIKey.objects.update_or_create(name="isosmart", defaults={"key": api_key, "is_active": True})
r = client.post(f"/api/organizations/{organization.id}/activate/")
if r.status_code != 200: raise RuntimeError(f"tenant activation failed: {r.status_code} {r.data}")
event = TenantIntegrationOutbox.objects.filter(organization=organization).order_by("-source_version").first()
iso_env = os.environ.copy(); iso_env.update(DB_NAME=iso["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(ip), USE_SQLITE_DATABASE="false", FOUNDATION_APP_ROLE="phase31_4_retry11_app", FOUNDATION_PROJECTOR_ROLE="phase31_4_retry11_projector", ADMIN_APPS_API_KEY=api_key, ADMINAPPS_TENANT_EVENT_KEY_SHA256=__import__('hashlib').sha256(event_key.encode()).hexdigest())
iproc, ilog = start(ROOT / "backend", iso_env, free(), "ISOSMART")
admin_proc, alog = start(ADMIN, admin_env, free(), "ADMINAPPS")
try:
    delivery_env = dict(admin_env, ISO_SMART_TENANT_EVENT_URL=f"http://127.0.0.1:{iproc.args[-1].split(':')[-1]}/api/integration/adminapps/tenant-events/", ISO_SMART_TENANT_EVENT_KEY=event_key, ISO_SMART_TENANT_EVENT_ALLOW_LOOPBACK_HTTP="true")
    delivery = subprocess.run([str(ADMIN / ".venv/bin/python"), "manage.py", "deliver_tenant_events", "--limit", "2"], cwd=ADMIN, env=delivery_env, text=True, capture_output=True)
    if delivery.returncode: raise RuntimeError(delivery.stdout + delivery.stderr)
finally:
    admin_proc.terminate(); iproc.terminate(); admin_proc.wait(); iproc.wait(); alog.close(); ilog.close()
# Re-enter ISO Django and create the native QMS chain from the authenticated projection.
os.environ["DJANGO_SETTINGS_MODULE"] = "backend.settings"; sys.path.insert(0, str(ROOT / "backend")); import django; django.setup()
from foundation.models import TenantProjection
from foundation.tenant_context import TrustedTenantIdentity
from foundation.qms_organization import QmsOrganizationCommandService
from foundation.qms_context import QmsContextCommandService
projection = TenantProjection.objects.get(adminapps_tenant_id=UUID(str(organization.id))); identity = TrustedTenantIdentity("retry11-stage-ext", projection.id); trace = uuid4(); actor_id = UUID(str(actor.id))
qms_org = QmsOrganizationCommandService().create_organization(identity=identity, display_name="Retry 11 QMS", actor_id=actor_id, trace_id=trace, request_key=uuid4())
process = QmsContextCommandService().create_process(identity=identity, organization_id=qms_org.organization_id, name="Retry 11 Native Process", actor_id=actor_id, trace_id=trace)
with psycopg2.connect(dbname=iso["database_name"], user="postgres", host="127.0.0.1", port=ip) as c:
    with c.cursor() as cur:
        cur.execute("SELECT id FROM qms.process WHERE id=%s", [str(process.entity_id)]); persisted = cur.fetchone()[0]
if str(process.entity_id) != str(persisted): raise RuntimeError("Process capture/persistence mismatch")
out = {"result":"PASS", "tenant_id":str(organization.id), "projection_id":str(projection.id), "organization_id":str(qms_org.organization_id), "process_id":str(process.entity_id), "persisted_process_id":str(persisted), "provenance":"LIVE_UPSTREAM_NATIVE_CAPTURE", "delivery":"PASS"}
(EVIDENCE / "PHASE31_4_CLEAN_RETRY_11_STAGE_EXT.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n"); print(json.dumps(out, sort_keys=True))
