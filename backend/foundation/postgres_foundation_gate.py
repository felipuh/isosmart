"""Reproducible PostgreSQL 18.6 lifecycle for the Phase 1.2 foundation gate.

Creates only run-id-scoped container, volume, database and LOGIN roles.  Every
resource is removed in ``finally`` and verified absent.  Secrets are generated
in memory and never printed or written to the repository.
"""

import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


POSTGRES_VERSION = "18.6"
POSTGRES_SHA256 = "983ee554ec53dbeb9b70797bef9fcf4e67e117e7e48ca1463cc80b3ff8e8ff3f"
DEBIAN_IMAGE = "docker.io/library/debian:bookworm-slim@sha256:362e64223cc0da95422b3b13c045186fc0a81250e765d31c025fbddf257f6143"
ROOT = Path(__file__).resolve().parents[2]
HARNESS = Path(os.environ.get(
    "FOUNDATION_HARNESS",
    str(Path(__file__).with_name("postgres_foundation_harness.py")),
)).resolve()

# This is the single, source-owned PostgreSQL identity contract.  The role
# settings are consumed by the active Foundation migrations (0001--0037), not
# invented at migration-failure time.  All of them must therefore exist before
# Django starts applying migrations.  Owner roles are deliberately NOLOGIN and
# can only be SET ROLE by the dedicated migrator through the memberships below.
ROLE_SPECS = (
    ("migrator", True, "BOOTSTRAP_REQUIRED", "database/schema migration owner"),
    ("app", True, "BOOTSTRAP_REQUIRED", "web/API runtime"),
    ("worker", True, "BOOTSTRAP_REQUIRED", "outbox worker runtime"),
    ("projector", True, "BOOTSTRAP_REQUIRED", "AdminApps projection ingress"),
    ("audit_writer", True, "BOOTSTRAP_REQUIRED", "immutable audit append runtime"),
    ("normative_curator", True, "BOOTSTRAP_REQUIRED", "normative curation runtime"),
    ("agent_catalog_curator", True, "BOOTSTRAP_REQUIRED", "agent catalog curation runtime"),
    ("human_approver", True, "BOOTSTRAP_REQUIRED", "human decision approval runtime"),
    ("execution_authorizer", True, "BOOTSTRAP_REQUIRED", "controlled execution authorization runtime"),
    ("executor", True, "BOOTSTRAP_REQUIRED", "controlled execution runtime"),
    ("learning_governance", True, "BOOTSTRAP_REQUIRED", "learning governance runtime"),
    ("learning_reviewer", True, "BOOTSTRAP_REQUIRED", "learning review runtime"),
    ("learning_approver", True, "BOOTSTRAP_REQUIRED", "learning approval runtime"),
    ("learning_authorizer", True, "BOOTSTRAP_REQUIRED", "learning authorization runtime"),
    ("learning_application_executor", True, "BOOTSTRAP_REQUIRED", "learning application runtime"),
    ("rule_publisher", True, "BOOTSTRAP_REQUIRED", "rule publication runtime"),
    ("rule_activator", True, "BOOTSTRAP_REQUIRED", "rule activation runtime"),
    ("rule_adopter", True, "BOOTSTRAP_REQUIRED", "rule adoption runtime"),
    ("rule_resolver", True, "BOOTSTRAP_REQUIRED", "rule resolution runtime"),
    ("release_repair", True, "BOOTSTRAP_REQUIRED", "release repair runtime"),
    ("release_controller", True, "BOOTSTRAP_REQUIRED", "release control runtime"),
    ("qms_action_owner", False, "BOOTSTRAP_REQUIRED", "restricted QMS function owner"),
    ("knowledge_rule_application_owner", False, "BOOTSTRAP_REQUIRED", "restricted application function owner"),
    ("rule_governance_owner", False, "BOOTSTRAP_REQUIRED", "restricted governance function owner"),
)
LOGIN_ROLES = tuple(key for key, login, _, _ in ROLE_SPECS if login)
OWNER_ROLES = tuple(key for key, login, _, _ in ROLE_SPECS if not login)


def run(command, *, env=None, capture=False, check=True):
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        check=check,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def wait_for_postgres(port, password):
    import psycopg2

    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            connection = psycopg2.connect(
                dbname="postgres", user="postgres", password=password,
                host="127.0.0.1", port=port, connect_timeout=2,
            )
            connection.close()
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("PostgreSQL readiness timeout")


def build_verified_image(engine, image, context):
    dockerfile = context / "Dockerfile"
    dockerfile.write_text(
        f"""FROM {DEBIAN_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl build-essential bison flex libreadline-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*
RUN curl --fail --proto '=https' --tlsv1.2 -o /tmp/postgresql.tar.gz https://ftp.postgresql.org/pub/source/v{POSTGRES_VERSION}/postgresql-{POSTGRES_VERSION}.tar.gz \\
 && echo '{POSTGRES_SHA256}  /tmp/postgresql.tar.gz' | sha256sum --check - \\
 && mkdir /tmp/postgresql && tar -xzf /tmp/postgresql.tar.gz -C /tmp/postgresql --strip-components=1 \\
 && cd /tmp/postgresql && ./configure --without-icu && make -j2 && make install \\
 && rm -rf /tmp/postgresql /tmp/postgresql.tar.gz \\
 && useradd --uid 999 --create-home postgres && mkdir -p /var/lib/postgresql/data && chown -R postgres:postgres /var/lib/postgresql
ENV PATH=/usr/local/pgsql/bin:$PATH PGDATA=/var/lib/postgresql/data
USER postgres
EXPOSE 5432
CMD ["sh", "-c", "if [ ! -s '$PGDATA/PG_VERSION' ]; then printf '%s\\n' \"$POSTGRES_PASSWORD\" > /tmp/pw && initdb --username=postgres --pwfile=/tmp/pw --auth-host=scram-sha-256 --auth-local=trust && rm -f /tmp/pw; fi; exec postgres -c listen_addresses='*'"]
""",
        encoding="utf-8",
    )
    run([engine, "build", "--pull=never", "--tag", image, str(context)])


def bootstrap(port, super_password, names, passwords):
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(
        dbname="postgres", user="postgres", password=super_password,
        host="127.0.0.1", port=port,
    )
    connection.autocommit = True
    with connection.cursor() as cursor:
        for role in LOGIN_ROLES:
            cursor.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS").format(sql.Identifier(names[role])),
                [passwords[role]],
            )
        for role in OWNER_ROLES:
            cursor.execute(
                sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS").format(
                    sql.Identifier(names[role])
                )
            )
            cursor.execute(
                sql.SQL("GRANT {} TO {} WITH SET TRUE").format(
                    sql.Identifier(names[role]), sql.Identifier(names["migrator"])
                )
            )
        cursor.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(names["database"]), sql.Identifier(names["migrator"])
            )
        )
    connection.close()


def bootstrap_idempotent(port, super_password, names, passwords):
    """Reuse the foundation gate bootstrap, refusing preexisting security drift.

    A partially initialized cluster requires DBA review instead of automatic
    reconciliation. A complete matching bootstrap is safe to invoke again.
    """
    import psycopg2

    role_names = [names[key] for key in (*LOGIN_ROLES, *OWNER_ROLES)]
    if len(set(role_names)) != len(role_names) or names["database"] == "postgres":
        raise ValueError("foundation role/database names are invalid or duplicated")
    connection = psycopg2.connect(
        dbname="postgres", user="postgres", password=super_password,
        host="127.0.0.1", port=port,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT rolname, rolcanlogin, rolinherit, rolsuper, rolcreatedb, "
                "rolcreaterole, rolbypassrls FROM pg_roles WHERE rolname=ANY(%s)",
                [role_names],
            )
            found = {row[0]: tuple(row[1:]) for row in cursor.fetchall()}
            cursor.execute(
                "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=%s",
                [names["database"]],
            )
            database = cursor.fetchone()
            if not found and database is None:
                connection.close()
                bootstrap(port, super_password, names, passwords)
                return bootstrap_idempotent(port, super_password, names, passwords)
            if database != (names["migrator"],) or len(found) != len(role_names):
                raise RuntimeError("partial or incorrectly owned foundation bootstrap")
            for key in (*LOGIN_ROLES, *OWNER_ROLES):
                expected = (key in LOGIN_ROLES, False, False, False, False, False)
                if found.get(names[key]) != expected:
                    raise RuntimeError(f"unsafe foundation role attributes: {names[key]}")
            cursor.execute(
                "SELECT parent.rolname, member.rolname, m.set_option, m.admin_option "
                "FROM pg_auth_members m JOIN pg_roles parent ON parent.oid=m.roleid "
                "JOIN pg_roles member ON member.oid=m.member "
                "WHERE parent.rolname=ANY(%s) OR member.rolname=ANY(%s)",
                [role_names, role_names],
            )
            memberships = set(cursor.fetchall())
            expected_memberships = {
                (names[key], names["migrator"], True, False) for key in OWNER_ROLES
            }
            if memberships != expected_memberships:
                raise RuntimeError("foundation role memberships differ from approved bootstrap")
            return {"roles": found, "database_owner": database[0], "memberships": sorted(memberships)}
    finally:
        if not connection.closed:
            connection.close()


def drop_database_and_roles(port, super_password, names):
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(
        dbname="postgres", user="postgres", password=super_password,
        host="127.0.0.1", port=port,
    )
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()",
            [names["database"]],
        )
        cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(names["database"])))
        for role in reversed((*LOGIN_ROLES, *OWNER_ROLES)):
            cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(names[role])))
        cursor.execute("SELECT count(*) FROM pg_roles WHERE rolname=ANY(%s)", [[names[key] for key in (*LOGIN_ROLES, *OWNER_ROLES)]])
        if cursor.fetchone()[0] != 0:
            raise RuntimeError("ephemeral LOGIN roles remain after scoped teardown")
    connection.close()


def main():
    engine = shutil.which("podman") or shutil.which("docker")
    if not engine:
        raise RuntimeError("Podman or Docker is required")
    engine_name = Path(engine).name
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + secrets.token_hex(3)
    safe_id = run_id.lower().replace("_", "")
    names = {
        "container": f"isosmart-foundation-pg186-{safe_id}",
        "volume": f"isosmart-foundation-pgdata-{safe_id}",
        "image": f"localhost/isosmart-postgres-18.6-foundation:{safe_id}",
        "database": f"foundation_gate_{safe_id}",
        "migrator": f"foundation_migrator_{safe_id}",
        "app": f"foundation_app_{safe_id}",
        "worker": f"foundation_worker_{safe_id}",
        "projector": f"foundation_projector_{safe_id}",
        "audit_writer": f"foundation_audit_writer_{safe_id}",
        "normative_curator": f"foundation_normative_curator_{safe_id}",
        "agent_catalog_curator": f"foundation_agent_catalog_curator_{safe_id}",
        "human_approver": f"foundation_human_approver_{safe_id}",
        "execution_authorizer": f"foundation_execution_authorizer_{safe_id}",
        "executor": f"foundation_executor_{safe_id}",
        "learning_governance": f"foundation_learning_governance_{safe_id}",
        "learning_reviewer": f"foundation_learning_reviewer_{safe_id}",
        "learning_approver": f"foundation_learning_approver_{safe_id}",
        "learning_authorizer": f"foundation_learning_authorizer_{safe_id}",
        "learning_application_executor": f"foundation_klr_app_exec_{safe_id}",
        "knowledge_rule_application_owner": f"foundation_klr_app_owner_{safe_id}",
        "rule_governance_owner": f"foundation_klr_gov_owner_{safe_id}",
        "rule_publisher": f"foundation_klr_publisher_{safe_id}",
        "rule_activator": f"foundation_klr_activator_{safe_id}",
        "rule_adopter": f"foundation_klr_adopter_{safe_id}",
        "rule_resolver": f"foundation_klr_resolver_{safe_id}",
        "release_repair": f"foundation_klr_repair_{safe_id}",
        "release_controller": f"foundation_klr_controller_{safe_id}",
        "qms_action_owner": f"foundation_qms_action_owner_{safe_id}",
    }
    passwords = {key: secrets.token_urlsafe(32) for key in ("super", "migrator", "app", "worker", "projector", "audit_writer", "normative_curator", "agent_catalog_curator", "human_approver", "execution_authorizer", "executor", "learning_governance", "learning_reviewer", "learning_approver", "learning_authorizer", "learning_application_executor", "rule_publisher", "rule_activator", "rule_adopter", "rule_resolver", "release_repair", "release_controller")}
    context = Path(tempfile.mkdtemp(prefix=f"isosmart-foundation-{safe_id}-"))
    port = None
    roles_created = False
    image_created = False
    container_created = False
    volume_created = False
    harness_result = None
    official_preexisting = False
    started = datetime.now(timezone.utc)
    try:
        official = f"docker.io/library/postgres:{POSTGRES_VERSION}"
        official_preexisting = run([engine, "image", "exists", official], check=False).returncode == 0
        pull = run([engine, "pull", official], capture=True, check=False)
        image = official
        supply_chain = "official image"
        if pull.returncode != 0:
            build_verified_image(engine, names["image"], context)
            image = names["image"]
            image_created = True
            supply_chain = f"official source SHA-256 {POSTGRES_SHA256}"
        elif not official_preexisting:
            image_created = True

        run([engine, "volume", "create", names["volume"]], capture=True)
        volume_created = True
        volume_target = "/var/lib/postgresql" if image == official else "/var/lib/postgresql/data"
        volume_mount = f"{names['volume']}:{volume_target}"
        if engine_name == "podman":
            volume_mount += ":U"
        run([
            engine, "run", "--detach", "--name", names["container"],
            "--publish", "127.0.0.1::5432", "--volume", volume_mount,
            "--env", f"POSTGRES_PASSWORD={passwords['super']}", image,
        ], capture=True)
        container_created = True
        inspected = run([engine, "port", names["container"], "5432/tcp"], capture=True).stdout.strip()
        port = int(inspected.rsplit(":", 1)[1])
        try:
            wait_for_postgres(port, passwords["super"])
        except Exception:
            logs = run([engine, "logs", names["container"]], capture=True, check=False)
            print((logs.stdout + logs.stderr).replace(passwords["super"], "<redacted>"), file=sys.stderr)
            raise
        bootstrap_first = bootstrap_idempotent(port, passwords["super"], names, passwords)
        roles_created = True
        bootstrap_second = bootstrap_idempotent(port, passwords["super"], names, passwords)
        if bootstrap_first != bootstrap_second:
            raise RuntimeError("bootstrap repeat changed the approved role contract")

        env = os.environ.copy()
        env.update({
            "FOUNDATION_DB_HOST": "127.0.0.1", "FOUNDATION_DB_PORT": str(port),
            "FOUNDATION_DB_NAME": names["database"],
            "FOUNDATION_MIGRATOR_ROLE": names["migrator"], "FOUNDATION_MIGRATOR_PASSWORD": passwords["migrator"],
            "FOUNDATION_APP_ROLE": names["app"], "FOUNDATION_APP_PASSWORD": passwords["app"],
            "FOUNDATION_WORKER_ROLE": names["worker"], "FOUNDATION_WORKER_PASSWORD": passwords["worker"],
            "FOUNDATION_PROJECTOR_ROLE": names["projector"], "FOUNDATION_PROJECTOR_PASSWORD": passwords["projector"],
            "FOUNDATION_AUDIT_WRITER_ROLE": names["audit_writer"], "FOUNDATION_AUDIT_WRITER_PASSWORD": passwords["audit_writer"],
            "FOUNDATION_NORMATIVE_CURATOR_ROLE": names["normative_curator"], "FOUNDATION_NORMATIVE_CURATOR_PASSWORD": passwords["normative_curator"],
            "FOUNDATION_AGENT_CATALOG_CURATOR_ROLE": names["agent_catalog_curator"], "FOUNDATION_AGENT_CATALOG_CURATOR_PASSWORD": passwords["agent_catalog_curator"],
            "FOUNDATION_HUMAN_APPROVER_ROLE": names["human_approver"], "FOUNDATION_HUMAN_APPROVER_PASSWORD": passwords["human_approver"],
            "FOUNDATION_EXECUTION_AUTHORIZER_ROLE": names["execution_authorizer"], "FOUNDATION_EXECUTION_AUTHORIZER_PASSWORD": passwords["execution_authorizer"],
            "FOUNDATION_EXECUTOR_ROLE": names["executor"], "FOUNDATION_EXECUTOR_PASSWORD": passwords["executor"],
            "FOUNDATION_LEARNING_GOVERNANCE_ROLE": names["learning_governance"], "FOUNDATION_LEARNING_GOVERNANCE_PASSWORD": passwords["learning_governance"],
            "FOUNDATION_LEARNING_REVIEWER_ROLE": names["learning_reviewer"], "FOUNDATION_LEARNING_REVIEWER_PASSWORD": passwords["learning_reviewer"],
            "FOUNDATION_LEARNING_APPROVER_ROLE": names["learning_approver"], "FOUNDATION_LEARNING_APPROVER_PASSWORD": passwords["learning_approver"],
            "FOUNDATION_LEARNING_AUTHORIZER_ROLE": names["learning_authorizer"], "FOUNDATION_LEARNING_AUTHORIZER_PASSWORD": passwords["learning_authorizer"],
            "FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE": names["learning_application_executor"], "FOUNDATION_LEARNING_APPLICATION_EXECUTOR_PASSWORD": passwords["learning_application_executor"],
            "FOUNDATION_KNOWLEDGE_RULE_APPLICATION_OWNER_ROLE": names["knowledge_rule_application_owner"],
            "FOUNDATION_RULE_GOVERNANCE_OWNER_ROLE": names["rule_governance_owner"],
            "FOUNDATION_RULE_PUBLISHER_ROLE": names["rule_publisher"], "FOUNDATION_RULE_PUBLISHER_PASSWORD": passwords["rule_publisher"],
            "FOUNDATION_RULE_ACTIVATOR_ROLE": names["rule_activator"], "FOUNDATION_RULE_ACTIVATOR_PASSWORD": passwords["rule_activator"],
            "FOUNDATION_RULE_ADOPTER_ROLE": names["rule_adopter"], "FOUNDATION_RULE_ADOPTER_PASSWORD": passwords["rule_adopter"],
            "FOUNDATION_RULE_RESOLVER_ROLE": names["rule_resolver"], "FOUNDATION_RULE_RESOLVER_PASSWORD": passwords["rule_resolver"],
            "FOUNDATION_RELEASE_REPAIR_ROLE": names["release_repair"], "FOUNDATION_RELEASE_REPAIR_PASSWORD": passwords["release_repair"],
            "FOUNDATION_RELEASE_CONTROLLER_ROLE": names["release_controller"], "FOUNDATION_RELEASE_CONTROLLER_PASSWORD": passwords["release_controller"],
            "FOUNDATION_QMS_ACTION_OWNER_ROLE": names["qms_action_owner"],
        })
        harness_result = run([sys.executable, str(HARNESS)], env=env, capture=True, check=False)
        if harness_result.returncode != 0:
            print(harness_result.stdout, end="")
            print(harness_result.stderr, file=sys.stderr)
            raise RuntimeError("foundation security matrix failed")
        print(harness_result.stdout, end="")
        print(json.dumps({
            "lifecycle": "PASS", "run_id": run_id, "engine": engine_name,
            "endpoint": f"127.0.0.1:{port}", "database": names["database"],
            "roles": [names[key] for key in (*LOGIN_ROLES, *OWNER_ROLES)],
            "bootstrap_first_run": "PASS", "bootstrap_second_run": "PASS_IDEMPOTENT",
            "supply_chain": supply_chain, "started_at": started.isoformat(),
        }, indent=2))
    finally:
        if roles_created and port is not None:
            drop_database_and_roles(port, passwords["super"], names)
        if container_created:
            run([engine, "rm", "--force", names["container"]], capture=True, check=False)
        if volume_created:
            run([engine, "volume", "rm", names["volume"]], capture=True, check=False)
        if image_created:
            run([engine, "image", "rm", image], capture=True, check=False)
        shutil.rmtree(context, ignore_errors=True)
        checks = {
            "container_absent": run([engine, "container", "exists", names["container"]], check=False).returncode != 0,
            "volume_absent": run([engine, "volume", "exists", names["volume"]], check=False).returncode != 0,
            "temp_absent": not context.exists(),
        }
        if not all(checks.values()):
            raise RuntimeError(f"scoped teardown verification failed: {checks}")
        print(json.dumps({"teardown": "PASS", **checks}, indent=2))


if __name__ == "__main__":
    main()
