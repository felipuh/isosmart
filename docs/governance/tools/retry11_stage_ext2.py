from __future__ import annotations
import hashlib, json, os, secrets, socket, subprocess, sys, time
from pathlib import Path
from uuid import UUID, uuid4
import psycopg2
ROOT=Path(__file__).resolve().parents[3]; ADMIN=ROOT.parent/"adminapps/backend"; E=ROOT/"docs/governance/evidence"
evidence_stem=os.environ.get("RETRY_EVIDENCE_STEM", "PHASE31_4_CLEAN_RETRY_12")
prefix=os.environ.get("RETRY_RESOURCE_PREFIX", "phase31_4_retry12")
m=json.loads(Path(os.environ.get("RETRY12_MANIFEST", E/"PHASE31_4_CLEAN_RETRY_12_RESOURCE_MANIFEST.json")).read_text()); a=m["environments"]["adminapps"]; i=m["environments"]["isosmart"]; ap=int(a["port_mappings"][0]["HostPort"]); ip=int(i["port_mappings"][0]["HostPort"])
def free():
 with socket.socket() as s: s.bind(("127.0.0.1",0)); return s.getsockname()[1]
def start(root,env,port,name):
 log=open(E/f"{evidence_stem}_{name}_SERVER.log","w"); p=subprocess.Popen([str(root/".venv/bin/python"),"manage.py","runserver","--noreload",f"127.0.0.1:{port}"],cwd=root,env=env,stdout=log,stderr=log)
 for _ in range(100):
  try: socket.create_connection(("127.0.0.1",port),1).close(); return p,log,port
  except OSError:
   if p.poll() is not None: raise RuntimeError(f"{name} server exited")
   time.sleep(0.2)
 raise RuntimeError(f"{name} readiness timeout")
event_key=secrets.token_urlsafe(32); api_key=secrets.token_urlsafe(32)
admin_env=os.environ.copy(); admin_env.update(DB_NAME=a["database_name"],DB_USER="postgres",DB_PASSWORD="",DB_HOST="127.0.0.1",DB_PORT=str(ap),ALLOWED_HOSTS="127.0.0.1,localhost,testserver",RETRY11_INTEGRATION_KEY=api_key)
up=json.loads(subprocess.check_output([str(ADMIN/".venv/bin/python"),str(ROOT/"docs/governance/tools/retry11_admin_create.py")],cwd=ADMIN,env=admin_env,text=True).splitlines()[-1])
role_names = ("app", "worker", "projector", "audit_writer", "normative_curator", "agent_catalog_curator", "human_approver", "execution_authorizer", "executor", "qms_action_owner", "learning_governance", "learning_reviewer", "learning_approver", "learning_authorizer", "learning_application_executor", "knowledge_rule_application_owner", "rule_governance_owner", "rule_publisher", "rule_activator", "rule_adopter", "rule_resolver", "release_repair", "release_controller")
options = " ".join(f"-c foundation.{name}_role={prefix}_{name}" for name in role_names)
app_password = secrets.token_urlsafe(24); projector_password = secrets.token_urlsafe(24)
with psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=ip) as c:
 with c.cursor() as cur:
  cur.execute(f'ALTER ROLE "{prefix}_app" PASSWORD %s', [app_password]); cur.execute(f'ALTER ROLE "{prefix}_projector" PASSWORD %s', [projector_password])
 c.commit()
iso_env=os.environ.copy(); iso_env.update(DB_NAME=i["database_name"],DB_USER="postgres",DB_PASSWORD="",DB_HOST="127.0.0.1",DB_PORT=str(ip),DB_SESSION_OPTIONS=options,USE_SQLITE_DATABASE="false",ALLOWED_HOSTS="127.0.0.1,localhost,testserver",ADMIN_APPS_API_KEY=api_key,ADMINAPPS_TENANT_EVENT_KEY_SHA256=hashlib.sha256(event_key.encode()).hexdigest(),FOUNDATION_APP_ROLE=f"{prefix}_app",FOUNDATION_APP_PASSWORD=app_password,FOUNDATION_PROJECTOR_ROLE=f"{prefix}_projector",FOUNDATION_PROJECTOR_PASSWORD=projector_password)
iproc,ilog,iso_http=start(ROOT/"backend",iso_env,free(),"ISOSMART"); aproc,alog,admin_http=start(ADMIN,admin_env,free(),"ADMINAPPS")
os.environ["ADMIN_APPS_BASE_URL"] = f"http://127.0.0.1:{admin_http}/api/integration"
if True:
 denv=dict(admin_env,ISO_SMART_TENANT_EVENT_URL=f"http://127.0.0.1:{iso_http}/api/integration/adminapps/tenant-events/",ISO_SMART_TENANT_EVENT_KEY=event_key,ISO_SMART_TENANT_EVENT_ALLOW_LOOPBACK_HTTP="true")
 d=subprocess.run([str(ADMIN/".venv/bin/python"),"manage.py","deliver_tenant_events","--limit","2"],cwd=ADMIN,env=denv,text=True,capture_output=True)
 if d.returncode: raise RuntimeError(d.stdout+d.stderr)
os.environ.update(iso_env); os.environ["DJANGO_SETTINGS_MODULE"]="backend.settings"; sys.path.insert(0,str(ROOT/"backend")); import django; django.setup()
from foundation.models import TenantProjection
from foundation.tenant_context import TrustedTenantIdentity
from foundation.qms_organization import QmsOrganizationCommandService
from foundation.qms_context import QmsContextCommandService
projection=TenantProjection.objects.get(adminapps_tenant_id=UUID(up["tenant_id"])); identity=TrustedTenantIdentity("retry12-stage-ext",projection.id); actor=UUID(up["actor_id"]); trace=uuid4()
org=QmsOrganizationCommandService().create_organization(identity=identity,display_name="Retry 12 QMS",actor_id=actor,trace_id=trace,request_key=uuid4()); process=QmsContextCommandService().create_process(identity=identity,organization_id=org.organization_id,name="Retry 12 Native Process",actor_id=actor,trace_id=trace)
with psycopg2.connect(dbname=i["database_name"],user="postgres",host="127.0.0.1",port=ip) as c:
 with c.cursor() as cur:
  cur.execute("SELECT id,tenant_id,organization_id FROM qms.process WHERE id=%s",[str(process.entity_id)]); persisted, process_tenant, process_org=cur.fetchone()
  cur.execute("SELECT id,tenant_id FROM qms.organization WHERE id=%s",[str(org.organization_id)]); org_row=cur.fetchone()
if str(org_row[1]) != str(projection.id) or str(process_tenant) != str(projection.id) or str(process_org) != str(org.organization_id): raise RuntimeError("Retry 12 QMS identity chain mismatch")
out={"result":"PASS","adminapps_tenant_id":up["tenant_id"],"actor_id":up["actor_id"],"tenant_projection_id":str(projection.id),"qms_organization_id":str(org.organization_id),"organization_tenant_id":str(org_row[1]),"process_id":str(process.entity_id),"persisted_process_id":str(persisted),"process_tenant_id":str(process_tenant),"process_organization_id":str(process_org),"provenance":"LIVE_UPSTREAM_NATIVE_CAPTURE","delivery":"PASS"}; (E/f"{evidence_stem}_STAGE_EXT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True))
for p,l in ((aproc,alog),(iproc,ilog)): p.terminate(); p.wait(); l.close()
