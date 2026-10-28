"""Fresh Retry 10 AdminApps API → outbox delivery → ISO Smart native chain."""

import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[3]
ADMIN = ROOT.parent / "adminapps/backend"
EVIDENCE = ROOT / "docs/governance/evidence"
TOOLS = ROOT / "docs/governance/tools"
manifest = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_RESOURCE_MANIFEST.json").read_text())
ports = {key: str(value["port_mappings"][0]["HostPort"]) for key, value in manifest["environments"].items()}
def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
iso_http, admin_http = free_port(), free_port()
event_key, integration_key = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
admin_env = os.environ.copy()
admin_env.update(DB_NAME=manifest["environments"]["adminapps"]["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=ports["adminapps"],
                 RETRY10_INTEGRATION_KEY=integration_key, ALLOWED_HOSTS="127.0.0.1,localhost,testserver")
names = {key: f"phase31_4_retry10_{key}" for key in ("migrator", "app", "worker", "projector", "audit_writer", "normative_curator", "agent_catalog_curator", "human_approver", "execution_authorizer", "executor", "qms_action_owner", "learning_governance", "learning_reviewer", "learning_approver", "learning_authorizer", "learning_application_executor", "knowledge_rule_application_owner", "rule_governance_owner", "rule_publisher", "rule_activator", "rule_adopter", "rule_resolver", "release_repair", "release_controller")}
settings = {key: key + "_role" for key in names if key != "migrator"}
options = " ".join(f"-c foundation.{setting}={names[key]}" for key, setting in settings.items())
role_passwords = {key: secrets.token_urlsafe(32) for key in ("migrator", "app", "projector")}
with psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=ports["isosmart"]) as connection:
    with connection.cursor() as cursor:
        for key, password in role_passwords.items():
            cursor.execute(sql.SQL("ALTER ROLE {} PASSWORD %s").format(sql.Identifier(names[key])), [password])
iso_env = os.environ.copy()
iso_env.update(USE_SQLITE_DATABASE="false", DB_NAME=manifest["environments"]["isosmart"]["database_name"], DB_USER=names["migrator"], DB_PASSWORD=role_passwords["migrator"], DB_HOST="127.0.0.1", DB_PORT=ports["isosmart"], DB_SESSION_OPTIONS=options,
               FOUNDATION_APP_ROLE=names["app"], FOUNDATION_APP_PASSWORD=role_passwords["app"], FOUNDATION_PROJECTOR_ROLE=names["projector"], FOUNDATION_PROJECTOR_PASSWORD=role_passwords["projector"],
               ADMINAPPS_TENANT_EVENT_KEY_SHA256=hashlib.sha256(event_key.encode()).hexdigest(),
               ADMIN_APPS_API_KEY=integration_key, ADMIN_APPS_BASE_URL=f"http://127.0.0.1:{admin_http}/api/integration", ALLOWED_HOSTS="127.0.0.1,localhost,testserver")
servers = []
logs = []
result = {"result": "FAIL", "retry_id": manifest["retry_id"]}
def run(args, cwd, env, include_stderr=False):
    completed = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        raise RuntimeError(f"{Path(args[0]).name} {args[1:3]} failed: {completed.stderr[-1000:]}")
    return completed.stdout + completed.stderr if include_stderr else completed.stdout
def wait_port(port, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("Django server exited before readiness")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Django server readiness timed out")
try:
    upstream = json.loads(run([str(ADMIN / ".venv/bin/python"), str(TOOLS / "retry10_admin_create.py")], ADMIN, admin_env).splitlines()[-1])
    result["adminapps_native_api"] = {"result": "PASS", **upstream}
    for root, env, port in ((ROOT / "backend", iso_env, iso_http), (ADMIN, admin_env, admin_http)):
        python = root / ".venv/bin/python"
        log = open(EVIDENCE / f"PHASE31_4_CLEAN_RETRY_10_{'ISOSMART' if root == ROOT / 'backend' else 'ADMINAPPS'}_SERVER.log", "w")
        logs.append(log)
        process = subprocess.Popen([str(python), "manage.py", "runserver", "--noreload", f"127.0.0.1:{port}"], cwd=root, env=env, stdout=log, stderr=log)
        servers.append(process)
        wait_port(port, process)
    delivery_env = {**admin_env, "ISO_SMART_TENANT_EVENT_URL": f"http://127.0.0.1:{iso_http}/api/integration/adminapps/tenant-events/",
                    "ISO_SMART_TENANT_EVENT_KEY": event_key, "ISO_SMART_TENANT_EVENT_ALLOW_LOOPBACK_HTTP": "true"}
    delivery = run([str(ADMIN / ".venv/bin/python"), "manage.py", "deliver_tenant_events", "--limit", "2"], ADMIN, delivery_env, include_stderr=True)
    with psycopg2.connect(dbname=admin_env["DB_NAME"], user="postgres", host="127.0.0.1", port=ports["adminapps"]) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT status FROM tenant_integration_outbox WHERE id=%s", [upstream["event_id"]])
            delivery_status = cursor.fetchone()
    if delivery_status != ("delivered",):
        raise RuntimeError(f"authenticated AdminApps outbox delivery did not complete: {delivery.strip()}")
    result["authenticated_delivery"] = {"result": "PASS", "event_id": upstream["event_id"],
                                         "dispatched_this_invocation": f"Delivered event {upstream['event_id']}" in delivery}
    native = json.loads(run([str(ROOT / "backend/.venv/bin/python"), str(TOOLS / "retry10_iso_native.py")], ROOT / "backend", {**iso_env, "RETRY10_UPSTREAM_JSON": json.dumps(upstream)}).splitlines()[-1])
    result["iso_smart_native"] = native
    result["result"] = "PASS"
except Exception as exc:
    result["error"] = str(exc)
finally:
    for process in servers:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    for log in logs:
        log.close()
    (EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_STAGE_EXT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
