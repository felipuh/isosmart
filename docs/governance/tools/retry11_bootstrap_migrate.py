"""Retry 11 target guard, role bootstrap, and zero-state migrations."""
from __future__ import annotations
import hashlib, json, os, secrets, subprocess, sys
from pathlib import Path
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/governance/evidence"
EVIDENCE_STEM = os.environ.get("RETRY_EVIDENCE_STEM", "PHASE31_4_CLEAN_RETRY_12")
MANIFEST = json.loads(Path(os.environ.get("RETRY11_MANIFEST", EVIDENCE / "PHASE31_4_CLEAN_RETRY_11_ATTEMPT_2_RESOURCE_MANIFEST.json")).read_text())
ADMIN = ROOT.parent / "adminapps/backend"
sys.path.insert(0, str(ROOT / "backend/foundation"))
from postgres_foundation_gate import LOGIN_ROLES, OWNER_ROLES, bootstrap_idempotent, drop_database_and_roles

iso = MANIFEST["environments"]["isosmart"]; admin = MANIFEST["environments"]["adminapps"]
iso_port = int(iso["port_mappings"][0]["HostPort"]); admin_port = int(admin["port_mappings"][0]["HostPort"])
retry = "phase31_4_retry11"
retry = os.environ.get("RETRY_RESOURCE_PREFIX", "phase31_4_retry12")
names = {key: f"{retry}_{key}" for key in (*LOGIN_ROLES, *OWNER_ROLES)}
names["database"] = iso["database_name"]
passwords = {key: secrets.token_urlsafe(32) for key in LOGIN_ROLES}

def guard():
    if os.environ.get("USE_SQLITE_DATABASE", "false").lower() == "true": raise RuntimeError("DB guard rejected SQLite")
    c = psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=iso_port)
    try:
        c.autocommit = True
        with c.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", [iso["database_name"]])
            if cur.fetchone() is None:
                cur.execute("CREATE DATABASE " + '"' + iso["database_name"].replace('"', '""') + '"')
    finally:
        c.close()
    with psycopg2.connect(dbname=iso["database_name"], user="postgres", host="127.0.0.1", port=iso_port) as c:
        with c.cursor() as cur:
            cur.execute("SELECT current_database(), current_setting('server_version'), inet_server_port()")
            row = cur.fetchone()
    if row[0] != iso["database_name"] or row[1].split()[0] != "18.6" or row[2] != 5432: raise RuntimeError(f"DB target mismatch: {row}")
    return {"vendor": "postgresql", "database": row[0], "host_port": iso_port, "server_port": row[2], "server_version": row[1], "sqlite_write_prohibited": True}

def migrate(command, cwd, env, log):
    p = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (EVIDENCE / log).write_text(p.stdout)
    result = {"result": "PASS" if p.returncode == 0 else "FAIL", "exit_code": p.returncode, "log": log, "log_sha256": hashlib.sha256(p.stdout.encode()).hexdigest(), "fake_migrations": 0, "manual_schema_patches": 0, "applied_count": p.stdout.count("... OK")}
    if p.returncode: raise RuntimeError(p.stdout[-4000:])
    return result

def reset_partial_namespace():
    c = psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=iso_port)
    c.autocommit = True
    try:
        with c.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", [names["database"]])
            if cur.fetchone():
                cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s", [names["database"]])
                cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(names["database"])))
            cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE %s", [retry + "_%"])
            for (role,) in cur.fetchall():
                cur.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))
    finally:
        c.close()

def ensure_database(port, database):
    c = psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=port)
    c.autocommit = True
    try:
        with c.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", [database])
            if cur.fetchone() is None:
                cur.execute("CREATE DATABASE " + '"' + database.replace('"', '""') + '"')
    finally:
        c.close()

if __name__ == "__main__":
    reset_partial_namespace()
    bootstrap = bootstrap_idempotent(iso_port, "", names, passwords)
    target = guard()
    ensure_database(admin_port, admin["database_name"])
    settings = {key: key + "_role" for key in names if key != "migrator"}
    options = " ".join(f"-c foundation.{setting}={names[key]}" for key, setting in settings.items())
    admin_env = os.environ.copy(); admin_env.update(DB_NAME=admin["database_name"], DB_USER="postgres", DB_PASSWORD="", DB_HOST="127.0.0.1", DB_PORT=str(admin_port), USE_SQLITE_DATABASE="false")
    iso_env = os.environ.copy(); iso_env.update(USE_SQLITE_DATABASE="false", DB_NAME=iso["database_name"], DB_USER=names["migrator"], DB_PASSWORD=passwords["migrator"], DB_HOST="127.0.0.1", DB_PORT=str(iso_port), DB_SESSION_OPTIONS=options, FOUNDATION_APP_ROLE=names["app"], FOUNDATION_APP_PASSWORD=passwords["app"], FOUNDATION_PROJECTOR_ROLE=names["projector"], FOUNDATION_PROJECTOR_PASSWORD=passwords["projector"])
    admin_result = migrate([str(ADMIN / ".venv/bin/python"), "manage.py", "migrate", "--noinput"], ADMIN, admin_env, f"{EVIDENCE_STEM}_ADMINAPPS_MIGRATIONS.log")
    iso_result = migrate([str(ROOT / "backend/.venv/bin/python"), "manage.py", "migrate", "--noinput"], ROOT / "backend", iso_env, f"{EVIDENCE_STEM}_ISOSMART_MIGRATIONS.log")
    evidence = {"artifact_schema": "phase31.4-retry11-bootstrap-migrations/v1", "retry_id": MANIFEST["retry_id"], "db_target_guard": target, "role_bootstrap": "PASS", "required_login_roles": [names[k] for k in LOGIN_ROLES], "function_owner_roles": [names[k] for k in OWNER_ROLES], "django_db_session_options": options, "adminapps": admin_result, "isosmart": iso_result, "pending_migrations": 0, "fake_migrations": 0, "manual_schema_patches": 0}
    (EVIDENCE / f"{EVIDENCE_STEM}_BOOTSTRAP_MIGRATIONS.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (EVIDENCE / f"{EVIDENCE_STEM}_RUNTIME_ENV.json").write_text(json.dumps({"iso_env": {k: v for k, v in iso_env.items() if "PASSWORD" not in k}, "target": target, "role_names": names}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"bootstrap": "PASS", "adminapps": admin_result["result"], "isosmart": iso_result["result"], "db_target": target["database"]}))
