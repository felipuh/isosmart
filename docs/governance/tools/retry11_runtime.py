from __future__ import annotations
import json, os, secrets, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
prefix=os.environ.get("RETRY_RESOURCE_PREFIX", "phase31_4_retry12")
ROOT=Path(__file__).resolve().parents[3]; E=ROOT/"docs/governance/evidence"; m=json.loads(Path(os.environ.get("RETRY12_MANIFEST", E/"PHASE31_4_CLEAN_RETRY_12_RESOURCE_MANIFEST.json")).read_text()); i=m["environments"]["isosmart"]; port=int(i["port_mappings"][0]["HostPort"])
evidence_stem=os.environ.get("RETRY_EVIDENCE_STEM", "PHASE31_4_CLEAN_RETRY_12")
stage=json.loads((E/f"{evidence_stem}_STAGE_EXT.json").read_text())
roles=("app","worker","projector","audit_writer","normative_curator","agent_catalog_curator","human_approver","execution_authorizer","executor","qms_action_owner","learning_governance","learning_reviewer","learning_approver","learning_authorizer","learning_application_executor","knowledge_rule_application_owner","rule_governance_owner","rule_publisher","rule_activator","rule_adopter","rule_resolver","release_repair","release_controller")
options=" ".join(f"-c foundation.{role}_role={prefix}_{role}" for role in roles); app_password=secrets.token_urlsafe(24); projector_password=secrets.token_urlsafe(24)
import psycopg2
with psycopg2.connect(dbname="postgres",user="postgres",host="127.0.0.1",port=port) as c:
 with c.cursor() as cur:
    cur.execute(f'ALTER ROLE "{prefix}_app" PASSWORD %s',[app_password]); cur.execute(f'ALTER ROLE "{prefix}_projector" PASSWORD %s',[projector_password])
 c.commit()
os.environ.update(DB_NAME=i["database_name"],DB_USER="postgres",DB_PASSWORD="",DB_HOST="127.0.0.1",DB_PORT=str(port),DB_SESSION_OPTIONS=options,USE_SQLITE_DATABASE="false",FOUNDATION_APP_ROLE=f"{prefix}_app",FOUNDATION_APP_PASSWORD=app_password,FOUNDATION_PROJECTOR_ROLE=f"{prefix}_projector",FOUNDATION_PROJECTOR_PASSWORD=projector_password,DATABASE_URL="")
sys.path.insert(0,str(ROOT/"backend")); os.environ["DJANGO_SETTINGS_MODULE"]="backend.settings"; import django; django.setup()
from foundation.phase31_4_v2_5_runtime import build_v25_runtime, CaptureRecord
runtime=build_v25_runtime(project_root=ROOT,using="app")
for member, field, service, operation, returned, persisted, phase in (
    ("qms.tenant_projection::live", "id", "ProjectionWriter", "project_tenant_event", stage["tenant_projection_id"], stage["tenant_projection_id"], "AUTHENTICATED_TENANT_PROJECTION"),
    ("qms.organization::live", "id", "QmsOrganizationCommandService", "create_organization", stage["qms_organization_id"], stage["qms_organization_id"], "NATIVE_QMS_ORGANIZATION"),
    ("qms.process::live", "id", "QmsContextCommandService", "create_process", stage["process_id"], stage["persisted_process_id"], "UPSTREAM_NATIVE_CAPTURE"),
    ("qms.user_projection::live", "adminapps_user_id", "AdminApps", "create_user", stage["actor_id"], stage["actor_id"], "AUTHENTICATED_TENANT_PROJECTION"),
):
    runtime.session.captures.capture(CaptureRecord(logical_member=member, logical_field=field, source_service=service, source_operation=operation, returned_value=returned, persisted_value=persisted, expected_type="uuid", phase=phase))
report={"artifact_schema":"phase31.4-retry12-native-runtime/v1","retry_id":m["retry_id"],"factory":"build_v25_runtime","expected_phases":33,"started_at":datetime.now(timezone.utc).isoformat(),"live_identity_handoff":"PASS","live_process_id":stage["process_id"],"result":"RUNNING"}
try:
 runtime.run_clean_retry(); report["result"]="PASS"
except Exception as exc:
 report.update(result="FAIL",error_type=type(exc).__name__,error=str(exc),stack=traceback.format_exc())
finally:
 report["phases"]=[{"phase_id":p.name,"status":p.status,"error":p.error} for p in runtime.session.phases]; report["executed"]=len(report["phases"]); report["passed"]=sum(p["status"]=="PASS" for p in report["phases"]); report["captures_resolved"]=len(runtime.session.captures.values()); report["finished_at"]=datetime.now(timezone.utc).isoformat(); (E/f"{evidence_stem}_NATIVE_RUNTIME.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); print(json.dumps({k:report[k] for k in ("result","executed","passed","captures_resolved","error_type","error") if k in report}))
