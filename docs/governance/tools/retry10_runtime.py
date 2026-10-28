"""Execute the production V2.5 runtime against Retry 10 PostgreSQL."""

import json
import os
from pathlib import Path
import secrets
import sys
import traceback
from datetime import datetime, timezone

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/governance/evidence"
manifest = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_RESOURCE_MANIFEST.json").read_text())
resource = manifest["environments"]["isosmart"]
port = int(resource["port_mappings"][0]["HostPort"])
names = {key: f"phase31_4_retry10_{key}" for key in (
    "migrator", "app", "worker", "projector", "audit_writer", "normative_curator",
    "agent_catalog_curator", "human_approver", "execution_authorizer", "executor",
    "qms_action_owner", "learning_governance", "learning_reviewer", "learning_approver",
    "learning_authorizer", "learning_application_executor", "knowledge_rule_application_owner",
    "rule_governance_owner", "rule_publisher", "rule_activator", "rule_adopter",
    "rule_resolver", "release_repair", "release_controller")}
options = " ".join(f"-c foundation.{key}_role={name}" for key, name in names.items() if key != "migrator")
passwords = {key: secrets.token_urlsafe(32) for key in ("migrator", "app", "projector")}
connection = psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=port)
try:
    with connection.cursor() as cursor:
        for key, password in passwords.items():
            cursor.execute(sql.SQL("ALTER ROLE {} PASSWORD %s").format(sql.Identifier(names[key])), [password])
    connection.commit()
finally:
    connection.close()
os.environ.update(USE_SQLITE_DATABASE="false", DB_NAME=resource["database_name"], DB_USER=names["migrator"], DB_PASSWORD=passwords["migrator"], DB_HOST="127.0.0.1", DB_PORT=str(port), DB_SESSION_OPTIONS=options,
                  FOUNDATION_APP_ROLE=names["app"], FOUNDATION_APP_PASSWORD=passwords["app"],
                  FOUNDATION_PROJECTOR_ROLE=names["projector"], FOUNDATION_PROJECTOR_PASSWORD=passwords["projector"])
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()
from foundation.phase31_4_v2_5_runtime import build_v25_runtime

runtime = build_v25_runtime(project_root=ROOT, using="app")
report = {"artifact_schema": "phase31.4-retry10-native-runtime/v1", "retry_id": manifest["retry_id"],
          "started_at": datetime.now(timezone.utc).isoformat(), "factory": "build_v25_runtime", "connection_role": names["app"],
          "expected_phases": 33, "result": "RUNNING"}
try:
    runtime.run_clean_retry()
    report["result"] = "PASS"
except Exception as exc:
    report["result"] = "FAIL"
    report["error_type"] = type(exc).__name__
    report["error"] = str(exc)
    report["stack"] = traceback.format_exc()
finally:
    report["phases"] = [{"phase_id": phase.name, "status": phase.status, "error": phase.error} for phase in runtime.session.phases]
    report["executed"] = len(report["phases"])
    report["passed"] = sum(phase["status"] == "PASS" for phase in report["phases"])
    report["captures_resolved"] = len(runtime.session.captures.values())
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    (EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_NATIVE_RUNTIME.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("result", "executed", "passed", "captures_resolved", "error_type", "error") if key in report}))
