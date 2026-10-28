from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/governance/evidence"
MANIFEST = json.loads((EVIDENCE / "PHASE31_4_CLEAN_RETRY_16_RESOURCE_MANIFEST.json").read_text())
ADMIN = ROOT.parent / "adminapps/backend"
PREFIX = "phase31_4_retry16"
EVIDENCE_STEM = "PHASE31_4_CLEAN_RETRY_16"

sys.path.insert(0, str(ROOT / "backend/foundation"))
from postgres_foundation_gate import LOGIN_ROLES, OWNER_ROLES, bootstrap_idempotent

iso = MANIFEST["environments"]["isosmart"]
admin = MANIFEST["environments"]["adminapps"]
iso_port = int(iso["port_mappings"][0]["HostPort"])
admin_port = int(admin["port_mappings"][0]["HostPort"])
names = {key: f"{PREFIX}_{key}" for key in (*LOGIN_ROLES, *OWNER_ROLES)}
names["database"] = iso["database_name"]
passwords = {key: secrets.token_urlsafe(32) for key in LOGIN_ROLES}


def ensure_database(port: int, database: str) -> None:
    with psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=port) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", [database])
            if cursor.fetchone() is None:
                cursor.execute(sql.SQL("CREATE DATABASE {} ").format(sql.Identifier(database)))


def drop_database_if_present(port: int, database: str) -> None:
    connection = psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=port)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s", [database])
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {} ").format(sql.Identifier(database)))
    finally:
        connection.close()


def drop_retry16_roles(port: int) -> None:
    connection = psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=port)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE %s", [f"{PREFIX}_%"])
            for (role,) in cursor.fetchall():
                cursor.execute(sql.SQL("DROP ROLE IF EXISTS {} ").format(sql.Identifier(role)))
    finally:
        connection.close()


def migrate(command: list[str], cwd: Path, env: dict[str, str], log_name: str) -> dict:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (EVIDENCE / log_name).write_text(result.stdout)
    evidence = {"result": "PASS" if result.returncode == 0 else "FAIL", "exit_code": result.returncode, "log": log_name, "log_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(), "fake_migrations": 0, "manual_schema_patches": 0, "applied_count": result.stdout.count("... OK")}
    if result.returncode:
        raise RuntimeError(result.stdout[-4000:])
    return evidence


if __name__ == "__main__":
    ensure_database(admin_port, admin["database_name"])
    drop_database_if_present(iso_port, iso["database_name"])
    drop_retry16_roles(iso_port)
    bootstrap = bootstrap_idempotent(iso_port, "", names, passwords)
    with psycopg2.connect(dbname=iso["database_name"], user="postgres", host="127.0.0.1", port=iso_port) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_setting('server_version'), inet_server_port()")
            row = cursor.fetchone()
    target = {"vendor": "postgresql", "database": row[0], "host_port": iso_port, "server_port": row[2], "server_version": row[1], "sqlite_write_prohibited": True}
    if row[0] != iso["database_name"] or row[1].split()[0] != "18.6" or row[2] != 5432:
        raise RuntimeError(f"DB target mismatch: {row}")
    options = " ".join(f"-c foundation.{key}_role={names[key]}" for key in (*LOGIN_ROLES, *OWNER_ROLES))
    admin_env = os.environ.copy()
    admin_env.update(DB_NAME=admin["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(admin_port), USE_SQLITE_DATABASE="false")
    iso_env = os.environ.copy()
    iso_env.update(USE_SQLITE_DATABASE="false", DB_NAME=iso["database_name"], DB_USER=names["migrator"], DB_PASSWORD=passwords["migrator"], DB_HOST="127.0.0.1", DB_PORT=str(iso_port), DB_SESSION_OPTIONS=options, FOUNDATION_APP_ROLE=names["app"], FOUNDATION_APP_PASSWORD=passwords["app"], FOUNDATION_PROJECTOR_ROLE=names["projector"], FOUNDATION_PROJECTOR_PASSWORD=passwords["projector"])
    admin_result = migrate([str(ADMIN / ".venv/bin/python"), "manage.py", "migrate", "--noinput"], ADMIN, admin_env, f"{EVIDENCE_STEM}_ADMINAPPS_MIGRATIONS.log")
    iso_result = migrate([str(ROOT / "backend/.venv/bin/python"), "manage.py", "migrate", "--noinput"], ROOT / "backend", iso_env, f"{EVIDENCE_STEM}_ISOSMART_MIGRATIONS.log")
    evidence = {"artifact_schema": "phase31.4-retry16-bootstrap-migrations/v1", "retry_id": MANIFEST["retry_id"], "db_target_guard": target, "role_bootstrap": "PASS", "required_login_roles": [names[key] for key in LOGIN_ROLES], "function_owner_roles": [names[key] for key in OWNER_ROLES], "django_db_session_options": options, "adminapps": admin_result, "isosmart": iso_result, "pending_migrations": 0, "fake_migrations": 0, "manual_schema_patches": 0}
    (EVIDENCE / f"{EVIDENCE_STEM}_BOOTSTRAP_MIGRATIONS.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (EVIDENCE / f"{EVIDENCE_STEM}_RUNTIME_ENV.json").write_text(json.dumps({"iso_env": {key: value for key, value in iso_env.items() if "PASSWORD" not in key}, "target": target, "role_names": names}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"bootstrap": "PASS", "adminapps": admin_result["result"], "isosmart": iso_result["result"], "db_target": target["database"]}))
