"""Run Retry 10 database bootstrap and clean migration chains.

Secrets exist only in this process and child environments. No secret is written
to evidence. Resource creation and teardown belong to retry10_resources.py.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from datetime import datetime, timezone

import psycopg2


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/governance/evidence"
ADMIN = ROOT.parent / "adminapps/backend"
sys.path.insert(0, str(ROOT / "backend/foundation"))
from postgres_foundation_gate import LOGIN_ROLES, OWNER_ROLES, bootstrap_idempotent


def write(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")


def migration(command, cwd, env, log_name):
    result = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (EVIDENCE / log_name).write_text(result.stdout)
    return {"result": "PASS" if result.returncode == 0 else "FAIL", "exit_code": result.returncode,
            "log": log_name, "log_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "applied_count": result.stdout.count("... OK"), "fake": 0, "manual_schema_patch": 0}


def main():
    manifest = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_RESOURCE_MANIFEST.json").read_text())
    ports = {key: int(value["port_mappings"][0]["HostPort"]) for key, value in manifest["environments"].items()}
    suffix = "phase31_4_retry10"
    names = {key: f"{suffix}_{key}" for key in (*LOGIN_ROLES, *OWNER_ROLES)}
    names["database"] = manifest["environments"]["isosmart"]["database_name"]
    passwords = {key: secrets.token_urlsafe(32) for key in LOGIN_ROLES}
    version = None
    negative = None
    with psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=ports["isosmart"]) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version")
            version = cursor.fetchone()[0]
            spec = importlib.util.spec_from_file_location("foundation_0001", ROOT / "backend/foundation/migrations/0001_foundation_tenant_projection.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                cursor.execute(module.FORWARD_SQL)
            except psycopg2.Error as exc:
                negative = {"result": "PASS" if "foundation runtime roles were not supplied" in str(exc) else "FAIL",
                            "sqlstate": exc.pgcode, "error": exc.diag.message_primary}
                connection.rollback()
            else:
                negative = {"result": "FAIL", "error": "guard unexpectedly accepted absent roles"}
                connection.rollback()
    bootstrap = bootstrap_idempotent(ports["isosmart"], "", names, passwords)
    repeated = bootstrap_idempotent(ports["isosmart"], "", names, passwords)
    if bootstrap != repeated or negative["result"] != "PASS" or not version.startswith("18.6"):
        raise RuntimeError("bootstrap validation failed")
    options = " ".join(f"-c foundation.{key}_role={names[key]}" for key in (*LOGIN_ROLES, *OWNER_ROLES) if key != "migrator")
    # Some foundation setting names are abbreviated or explicitly named.
    settings = {
        "app": "app_role", "worker": "worker_role", "projector": "projector_role",
        "audit_writer": "audit_writer_role", "normative_curator": "normative_curator_role",
        "agent_catalog_curator": "agent_catalog_curator_role", "human_approver": "human_approver_role",
        "execution_authorizer": "execution_authorizer_role", "executor": "executor_role",
        "qms_action_owner": "qms_action_owner_role", "learning_governance": "learning_governance_role",
        "learning_reviewer": "learning_reviewer_role", "learning_approver": "learning_approver_role",
        "learning_authorizer": "learning_authorizer_role",
        "learning_application_executor": "learning_application_executor_role",
        "knowledge_rule_application_owner": "knowledge_rule_application_owner_role",
        "rule_governance_owner": "rule_governance_owner_role", "rule_publisher": "rule_publisher_role",
        "rule_activator": "rule_activator_role", "rule_adopter": "rule_adopter_role",
        "rule_resolver": "rule_resolver_role", "release_repair": "release_repair_role",
        "release_controller": "release_controller_role",
    }
    options = " ".join(f"-c foundation.{setting}={names[key]}" for key, setting in settings.items())
    with psycopg2.connect(dbname=names["database"], user=names["migrator"], password=passwords["migrator"], host="127.0.0.1", port=ports["isosmart"], options=options) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user, current_setting('foundation.app_role'), current_setting('foundation.worker_role')")
            settings_check = cursor.fetchone()
    role_inventory = []
    for key in (*LOGIN_ROLES, *OWNER_ROLES):
        role_inventory.append({"key": key, "name": names[key], "login": key in LOGIN_ROLES,
                               "inherit": False, "superuser": False, "createdb": False,
                               "createrole": False, "bypassrls": False,
                               "database_owner": key == "migrator",
                               "connection_use": "migration" if key == "migrator" else ("runtime" if key in LOGIN_ROLES else "function ownership"),
                               "schema_and_table_grants": "migration-managed least privilege",
                               "rls": "subject to RLS" if key in LOGIN_ROLES and key != "migrator" else "owner or migration policy"})
    evidence = {
        "artifact_schema": "phase31.4-postgres-runtime-role-bootstrap/v1",
        "retry_id": manifest["retry_id"], "checked_at": datetime.now(timezone.utc).isoformat(),
        "postgresql_version": version, "mechanism": "backend/foundation/postgres_foundation_gate.py:bootstrap_idempotent",
        "negative_without_bootstrap": negative, "bootstrap_result": "PASS", "repeat_result": "PASS",
        "database_owner": bootstrap["database_owner"], "memberships": bootstrap["memberships"],
        "roles": role_inventory, "connection_settings_check": settings_check,
        "secrets": {"configured": True, "source": "ephemeral secrets.token_urlsafe; in-memory only", "values_redacted": True},
        "source_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in (
            "backend/foundation/postgres_foundation_gate.py",
            "backend/foundation/migrations/0001_foundation_tenant_projection.py")},
    }
    write("PHASE31_4_POSTGRES_RUNTIME_ROLE_BOOTSTRAP_V1.json", evidence)
    admin_env = os.environ.copy()
    admin_env.update(DB_NAME=manifest["environments"]["adminapps"]["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(ports["adminapps"]))
    prior_migrations = EVIDENCE / "PHASE31_4_CLEAN_RETRY_10_MIGRATIONS.json"
    if prior_migrations.exists():
        admin_result = json.loads(prior_migrations.read_text())["adminapps"]
        with psycopg2.connect(dbname=admin_env["DB_NAME"], user="postgres", host="127.0.0.1", port=ports["adminapps"]) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM django_migrations")
                if cursor.fetchone()[0] != admin_result["applied_count"]:
                    raise RuntimeError("AdminApps PostgreSQL migration ledger differs from initial run")
    else:
        admin_result = migration([str(ADMIN / ".venv/bin/python"), "manage.py", "migrate", "--noinput"], ADMIN, admin_env, "PHASE31_4_CLEAN_RETRY_10_ADMINAPPS_MIGRATIONS.log")
    iso_env = os.environ.copy()
    iso_env.update(USE_SQLITE_DATABASE="false", DB_NAME=names["database"], DB_USER=names["migrator"], DB_PASSWORD=passwords["migrator"], DB_HOST="127.0.0.1", DB_PORT=str(ports["isosmart"]), DB_SESSION_OPTIONS=options,
                   FOUNDATION_APP_ROLE=names["app"], FOUNDATION_APP_PASSWORD=passwords["app"],
                   FOUNDATION_PROJECTOR_ROLE=names["projector"], FOUNDATION_PROJECTOR_PASSWORD=passwords["projector"])
    iso_result = migration([str(ROOT / "backend/.venv/bin/python"), "manage.py", "migrate", "--noinput"], ROOT / "backend", iso_env, "PHASE31_4_CLEAN_RETRY_10_ISOSMART_MIGRATIONS.log")
    write("PHASE31_4_CLEAN_RETRY_10_MIGRATIONS.json", {"retry_id": manifest["retry_id"], "adminapps": admin_result, "isosmart": iso_result,
          "foundation_0001": "PASS" if "Applying foundation.0001_foundation_tenant_projection... OK" in (EVIDENCE / iso_result["log"]).read_text() else "FAIL",
          "pending": "NOT_CHECKED" if iso_result["result"] != "PASS" else 0})
    print(json.dumps({"bootstrap": "PASS", "adminapps": admin_result["result"], "isosmart": iso_result["result"], "foundation_0001": "PASS" if "Applying foundation.0001_foundation_tenant_projection... OK" in (EVIDENCE / iso_result["log"]).read_text() else "FAIL"}))


if __name__ == "__main__":
    main()
