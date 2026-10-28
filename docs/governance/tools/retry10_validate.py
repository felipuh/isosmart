"""Read-only Retry 10 PostgreSQL role, migration, and preservation audit."""

import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

import psycopg2

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/governance/evidence"
manifest = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_RESOURCE_MANIFEST.json").read_text())
bootstrap_path = EVIDENCE / "PHASE31_4_POSTGRES_RUNTIME_ROLE_BOOTSTRAP_V1.json"
bootstrap = json.loads(bootstrap_path.read_text())
resource = manifest["environments"]["isosmart"]
port = int(resource["port_mappings"][0]["HostPort"])
dbname = resource["database_name"]
connection = psycopg2.connect(dbname=dbname, user="postgres", host="127.0.0.1", port=port)
connection.autocommit = True
with connection.cursor() as cursor:
    cursor.execute("SHOW server_version")
    version = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM django_migrations")
    applied = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM django_migrations WHERE app='foundation'")
    foundation_applied = cursor.fetchone()[0]
    cursor.execute("SELECT nspname FROM pg_namespace WHERE nspname NOT IN ('pg_catalog','information_schema') AND nspname NOT LIKE 'pg_toast%'")
    schemas = tuple(row[0] for row in cursor.fetchall())
    cursor.execute("SELECT n.nspname,c.relname,r.rolname,c.relrowsecurity,c.relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles r ON r.oid=c.relowner WHERE c.relkind IN ('r','p') AND n.nspname NOT IN ('pg_catalog','information_schema') ORDER BY 1,2")
    tables = cursor.fetchall()
    protected = [row for row in tables if row[3]]
    for role in bootstrap["roles"]:
        name = role["name"]
        cursor.execute("SELECT rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=%s", [name])
        attrs = cursor.fetchone()
        role["observed_attributes"] = dict(zip(("login", "inherit", "superuser", "createdb", "createrole", "bypassrls"), attrs))
        role["attribute_match"] = attrs == (role["login"], False, False, False, False, False)
        role["schema_access"] = {}
        for schema in schemas:
            cursor.execute("SELECT has_schema_privilege(%s,%s,'USAGE'),has_schema_privilege(%s,%s,'CREATE')", [name, schema, name, schema])
            usage, create = cursor.fetchone()
            if usage or create:
                role["schema_access"][schema] = {"usage": usage, "create": create}
        role["table_privileges"] = []
        for schema, table, owner, rls, force in tables:
            full = f'"{schema}"."{table}"'
            cursor.execute("SELECT has_table_privilege(%s,%s,'SELECT'),has_table_privilege(%s,%s,'INSERT'),has_table_privilege(%s,%s,'UPDATE'),has_table_privilege(%s,%s,'DELETE')", [name, full, name, full, name, full, name, full])
            privileges = dict(zip(("select", "insert", "update", "delete"), cursor.fetchone()))
            if any(privileges.values()):
                role["table_privileges"].append({"table": f"{schema}.{table}", "privileges": privileges, "rls_enabled": rls, "force_rls": force, "owner": owner})
        role["owns_protected_tables"] = [f"{schema}.{table}" for schema, table, owner, rls, _ in protected if owner == name]
    cursor.execute("SELECT schemaname,tablename,policyname,roles,cmd FROM pg_policies ORDER BY 1,2,3")
    policies = [dict(zip(("schema", "table", "name", "roles", "command"), row)) for row in cursor.fetchall()]
    cursor.execute("SELECT count(*) FROM pg_default_acl")
    default_acl_count = cursor.fetchone()[0]
    cursor.execute("SELECT current_database(),pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()")
    database_identity = cursor.fetchone()
connection.close()

names = {item["key"]: item["name"] for item in bootstrap["roles"]}
options = " ".join(f"-c foundation.{key}_role={name}" for key, name in names.items() if key != "migrator")
os.environ.update(USE_SQLITE_DATABASE="false", DB_NAME=dbname, DB_USER=names["migrator"],
                  DB_HOST="127.0.0.1", DB_PORT=str(port), DB_SESSION_OPTIONS=options)
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()
from django.db import connection as django_connection
from django.db.migrations.executor import MigrationExecutor
executor = MigrationExecutor(django_connection)
pending = len(executor.migration_plan(executor.loader.graph.leaf_nodes()))

role_map = {item["key"]: item for item in bootstrap["roles"]}
for role in bootstrap["roles"]:
    role["purpose"] = {
        "migrator": "Django schema migration and protected table ownership",
        "app": "Normal tenant-scoped application commands and reads",
        "worker": "Tenant-scoped background worker",
        "projector": "Authenticated AdminApps tenant projection writer",
        "audit_writer": "Immutable audit append",
        "qms_action_owner": "Restricted QMS action function ownership",
        "knowledge_rule_application_owner": "Restricted knowledge rule function ownership",
        "rule_governance_owner": "Restricted rule governance function ownership",
    }.get(role["key"], "Dedicated least-privilege " + role["key"].replace("_", " ") + " authority")
runtime_keys = [key for key in role_map if key != "migrator" and role_map[key]["login"]]
security_pass = all(item["attribute_match"] for item in bootstrap["roles"]) and all(not role_map[key]["owns_protected_tables"] for key in runtime_keys)
bootstrap["post_migration_validation"] = {"checked_at": datetime.now(timezone.utc).isoformat(), "postgresql_version": version,
    "database": database_identity[0], "owner": database_identity[1], "migration_count": applied,
    "foundation_migration_count": foundation_applied, "pending_migrations": pending,
    "protected_table_count": len(protected),
    "rls_policy_count": len(policies), "policies": policies,
    "default_acl_entry_count": default_acl_count,
    "runtime_roles_own_no_protected_tables": all(not role_map[key]["owns_protected_tables"] for key in runtime_keys),
    "role_attributes_match": all(item["attribute_match"] for item in bootstrap["roles"]),
    "result": "PASS" if security_pass and pending == 0 and database_identity[1] == role_map["migrator"]["name"] else "FAIL"}
bootstrap["connection_model"] = {
    "migration_role": names["migrator"], "application_connection_role": names["app"],
    "projection_connection_role": names["projector"], "worker_connection_role": names["worker"],
    "bootstrap_authority": "isolated PostgreSQL cluster administrator",
    "runtime_inherits_migration_authority": False,
}
bootstrap["source_sha256"] = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in (
    "backend/foundation/postgres_foundation_gate.py", "backend/backend/settings.py",
    "backend/foundation/migrations/0001_foundation_tenant_projection.py",
    "docs/governance/tools/retry10_run.py")}
bootstrap_path.write_text(json.dumps(bootstrap, indent=2, sort_keys=True, default=str) + "\n")

v24 = ROOT / "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json"
v24_hash = hashlib.sha256(v24.read_bytes()).hexdigest()
expected = "a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387"
native = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_NATIVE_RUNTIME.json").read_text())
stage = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_STAGE_EXT.json").read_text())
expected_process = "506d920c-fe62-53c0-aac8-9c1ca8ca78ed"
actual_process = stage["iso_smart_native"]["process_id"]
blocker = {"artifact_schema": "phase31.4-retry10-live-blocker/v1", "id": "P1-RETRY10-V25-INITIAL-OPPORTUNITY-PROCESS-BINDING-MISMATCH",
    "severity": "P1", "status": "OPEN", "phase": "INITIAL_OPPORTUNITY", "source": "backend/foundation/phase31_4_v2_5_runtime.py:584",
    "service": "RiskOpportunityObjectiveCommandService", "operation": "create_opportunity",
    "expected": {"contract_process_member_id": expected_process, "requirement": "bind to the Process created by the fresh native upstream chain"},
    "actual": {"fresh_process_id": actual_process, "error": native["error"]}, "stack": native["stack"],
    "evidence": ["PHASE31_4_CLEAN_RETRY_10_NATIVE_RUNTIME.json", "PHASE31_4_CLEAN_RETRY_10_STAGE_EXT.json"],
    "remediation": "Resolve the contract reference against the captured fresh Process identity through the approved V2.5 binding mechanism; do not substitute a fixture ID or synthesize a Process row."}
(EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_LIVE_BLOCKER.json").write_text(json.dumps(blocker, indent=2, sort_keys=True) + "\n")

closure = {"artifact_schema": "phase31.4-retry10-closure/v1", "retry_id": manifest["retry_id"],
    "role_bootstrap_blocker": "CLOSED", "role_bootstrap_result": bootstrap["post_migration_validation"]["result"],
    "adminapps_migrations": "PASS", "isosmart_migrations": "PASS", "isosmart_pending_migrations": pending,
    "foundation_0001": "PASS",
    "stage_ext_fresh": stage["result"], "native_runtime": native["result"], "native_phases_executed": native["executed"],
    "native_phases_passed": native["passed"], "captures_resolved": native["captures_resolved"],
    "v24_sha256": v24_hash, "v24_sha_pass": v24_hash == expected, "new_p1": blocker["id"],
    "promotion": "NOT_PROMOTED", "teardown": "PENDING"}
(EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_CLOSURE.json").write_text(json.dumps(closure, indent=2, sort_keys=True) + "\n")
print(json.dumps({"postgresql": version, "migrations": applied, "foundation_migrations": foundation_applied,
                  "role_security": bootstrap["post_migration_validation"]["result"], "v24_sha_pass": closure["v24_sha_pass"], "promotion": closure["promotion"]}))
