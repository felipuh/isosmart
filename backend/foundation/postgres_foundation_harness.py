"""Blocking Phase 3 matrix against an isolated PostgreSQL 18.6 database.

Cluster role/database lifecycle is owned by ``postgres_foundation_gate.py``.
This process connects as five distinct LOGIN principals and never uses SET ROLE.
"""

import inspect
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID


BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from django.conf import settings


TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
CHILD_A = UUID("aaaaaaaa-0000-4000-8000-000000000001")
CHILD_B = UUID("bbbbbbbb-0000-4000-8000-000000000001")
ORG_A = UUID("aaaaaaaa-1000-4000-8000-000000000001")
ORG_B = UUID("bbbbbbbb-1000-4000-8000-000000000001")
BASE_MIGRATION = ("foundation", "0001_foundation_tenant_projection")
PHASE2_MIGRATION = ("foundation", "0002_projection_organization_user_foundation")
MIGRATION = ("foundation", "0003_eventing_immutable_audit_foundation")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def database(alias, user_key, password_key):
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["FOUNDATION_DB_NAME"],
        "USER": os.environ[user_key],
        "PASSWORD": os.environ[password_key],
        "HOST": os.environ.get("FOUNDATION_DB_HOST", "127.0.0.1"),
        "PORT": os.environ["FOUNDATION_DB_PORT"],
        "CONN_MAX_AGE": 0,
        "OPTIONS": {
                "options": (
                    f"-c foundation.app_role={os.environ['FOUNDATION_APP_ROLE']} "
                    f"-c foundation.worker_role={os.environ['FOUNDATION_WORKER_ROLE']} "
                    f"-c foundation.projector_role={os.environ['FOUNDATION_PROJECTOR_ROLE']} "
                    f"-c foundation.audit_writer_role={os.environ['FOUNDATION_AUDIT_WRITER_ROLE']} "
                    f"-c foundation.normative_curator_role={os.environ['FOUNDATION_NORMATIVE_CURATOR_ROLE']} "
                    f"-c foundation.agent_catalog_curator_role={os.environ['FOUNDATION_AGENT_CATALOG_CURATOR_ROLE']}"
                    f" -c foundation.human_approver_role={os.environ['FOUNDATION_HUMAN_APPROVER_ROLE']}"
                    f" -c foundation.execution_authorizer_role={os.environ['FOUNDATION_EXECUTION_AUTHORIZER_ROLE']}"
                    f" -c foundation.executor_role={os.environ['FOUNDATION_EXECUTOR_ROLE']}"
                    f" -c foundation.qms_action_owner_role={os.environ['FOUNDATION_QMS_ACTION_OWNER_ROLE']}"
                    f" -c foundation.learning_governance_role={os.environ['FOUNDATION_LEARNING_GOVERNANCE_ROLE']}"
                    f" -c foundation.learning_reviewer_role={os.environ['FOUNDATION_LEARNING_REVIEWER_ROLE']}"
                    f" -c foundation.learning_approver_role={os.environ['FOUNDATION_LEARNING_APPROVER_ROLE']}"
                    f" -c foundation.learning_authorizer_role={os.environ['FOUNDATION_LEARNING_AUTHORIZER_ROLE']}"
                    f" -c foundation.learning_application_executor_role={os.environ['FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE']}"
                    f" -c foundation.knowledge_rule_application_owner_role={os.environ['FOUNDATION_KNOWLEDGE_RULE_APPLICATION_OWNER_ROLE']}"
                    f" -c foundation.rule_governance_owner_role={os.environ['FOUNDATION_RULE_GOVERNANCE_OWNER_ROLE']}"
                    f" -c foundation.rule_publisher_role={os.environ['FOUNDATION_RULE_PUBLISHER_ROLE']}"
                    f" -c foundation.rule_activator_role={os.environ['FOUNDATION_RULE_ACTIVATOR_ROLE']}"
                    f" -c foundation.rule_adopter_role={os.environ['FOUNDATION_RULE_ADOPTER_ROLE']}"
                    f" -c foundation.rule_resolver_role={os.environ['FOUNDATION_RULE_RESOLVER_ROLE']}"
                    f" -c foundation.release_repair_role={os.environ['FOUNDATION_RELEASE_REPAIR_ROLE']}"
                    f" -c foundation.release_controller_role={os.environ['FOUNDATION_RELEASE_CONTROLLER_ROLE']}"
                )
            },
    }


def configure_django():
    settings.configure(
        SECRET_KEY="ephemeral-foundation-gate-only",
        INSTALLED_APPS=["foundation"],
        DATABASES={
            "default": database("default", "FOUNDATION_MIGRATOR_ROLE", "FOUNDATION_MIGRATOR_PASSWORD"),
            "app": database("app", "FOUNDATION_APP_ROLE", "FOUNDATION_APP_PASSWORD"),
            "worker": database("worker", "FOUNDATION_WORKER_ROLE", "FOUNDATION_WORKER_PASSWORD"),
            "projector": database("projector", "FOUNDATION_PROJECTOR_ROLE", "FOUNDATION_PROJECTOR_PASSWORD"),
            "audit_writer": database("audit_writer", "FOUNDATION_AUDIT_WRITER_ROLE", "FOUNDATION_AUDIT_WRITER_PASSWORD"),
            "normative_curator": database("normative_curator", "FOUNDATION_NORMATIVE_CURATOR_ROLE", "FOUNDATION_NORMATIVE_CURATOR_PASSWORD"),
            "agent_catalog_curator": database("agent_catalog_curator", "FOUNDATION_AGENT_CATALOG_CURATOR_ROLE", "FOUNDATION_AGENT_CATALOG_CURATOR_PASSWORD"),
            "human_approver": database("human_approver", "FOUNDATION_HUMAN_APPROVER_ROLE", "FOUNDATION_HUMAN_APPROVER_PASSWORD"),
            "execution_authorizer": database("execution_authorizer", "FOUNDATION_EXECUTION_AUTHORIZER_ROLE", "FOUNDATION_EXECUTION_AUTHORIZER_PASSWORD"),
            "executor": database("executor", "FOUNDATION_EXECUTOR_ROLE", "FOUNDATION_EXECUTOR_PASSWORD"),
            "learning_governance": database("learning_governance", "FOUNDATION_LEARNING_GOVERNANCE_ROLE", "FOUNDATION_LEARNING_GOVERNANCE_PASSWORD"),
            "learning_reviewer": database("learning_reviewer", "FOUNDATION_LEARNING_REVIEWER_ROLE", "FOUNDATION_LEARNING_REVIEWER_PASSWORD"),
            "learning_approver": database("learning_approver", "FOUNDATION_LEARNING_APPROVER_ROLE", "FOUNDATION_LEARNING_APPROVER_PASSWORD"),
            "learning_authorizer": database("learning_authorizer", "FOUNDATION_LEARNING_AUTHORIZER_ROLE", "FOUNDATION_LEARNING_AUTHORIZER_PASSWORD"),
            "learning_application": database("learning_application", "FOUNDATION_LEARNING_APPLICATION_EXECUTOR_ROLE", "FOUNDATION_LEARNING_APPLICATION_EXECUTOR_PASSWORD"),
            "rule_publisher": database("rule_publisher", "FOUNDATION_RULE_PUBLISHER_ROLE", "FOUNDATION_RULE_PUBLISHER_PASSWORD"),
            "rule_activator": database("rule_activator", "FOUNDATION_RULE_ACTIVATOR_ROLE", "FOUNDATION_RULE_ACTIVATOR_PASSWORD"),
            "rule_adopter": database("rule_adopter", "FOUNDATION_RULE_ADOPTER_ROLE", "FOUNDATION_RULE_ADOPTER_PASSWORD"),
            "rule_resolver": database("rule_resolver", "FOUNDATION_RULE_RESOLVER_ROLE", "FOUNDATION_RULE_RESOLVER_PASSWORD"),
            "release_repair": database("release_repair", "FOUNDATION_RELEASE_REPAIR_ROLE", "FOUNDATION_RELEASE_REPAIR_PASSWORD"),
            "release_controller": database("release_controller", "FOUNDATION_RELEASE_CONTROLLER_ROLE", "FOUNDATION_RELEASE_CONTROLLER_PASSWORD"),
        },
        DATABASE_ROUTERS=[],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        USE_TZ=True,
    )
    import django

    django.setup()


def expect_error(operation, fragment):
    try:
        operation()
    except Exception as exc:
        require(fragment.lower() in str(exc).lower(), f"unexpected database error: {exc}")
    else:
        raise AssertionError(f"database operation unexpectedly succeeded: {fragment}")


@contextmanager
def runtime_transaction(alias, tenant=None):
    from django.db import connections

    connection = connections[alias]
    connection.set_autocommit(False)
    cursor = connection.cursor()
    try:
        if tenant is not None:
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true), "
                "set_config('app.actor_id', %s, true), "
                "set_config('app.trace_id', %s, true)",
                [str(tenant), f"{alias}-actor", f"{alias}-trace"],
            )
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.set_autocommit(True)


def visible_projections(alias, tenant=None):
    with runtime_transaction(alias, tenant) as cursor:
        cursor.execute("SELECT display_name_snapshot FROM qms.tenant_projection ORDER BY display_name_snapshot")
        return [row[0] for row in cursor.fetchall()]


def visible_children(alias, tenant=None):
    with runtime_transaction(alias, tenant) as cursor:
        cursor.execute("SELECT payload FROM qms.foundation_test_tenant_child ORDER BY payload")
        return [row[0] for row in cursor.fetchall()]


def visible_organizations(alias, tenant=None):
    with runtime_transaction(alias, tenant) as cursor:
        cursor.execute("SELECT display_name FROM qms.organization ORDER BY display_name")
        return [row[0] for row in cursor.fetchall()]


def visible_users(alias, tenant=None):
    with runtime_transaction(alias, tenant) as cursor:
        cursor.execute("SELECT adminapps_user_id::text FROM qms.user_projection ORDER BY adminapps_user_id")
        return [row[0] for row in cursor.fetchall()]


def visible_phase3(alias, table, tenant=None):
    allowed = {
        "domain_event": "eventing.domain_event",
        "transactional_outbox": "eventing.transactional_outbox",
        "consumer_receipt": "eventing.consumer_receipt",
        "immutable_audit_log": "audit.immutable_audit_log",
    }
    with runtime_transaction(alias, tenant) as cursor:
        cursor.execute(f"SELECT count(*) FROM {allowed[table]}")
        return cursor.fetchone()[0]


def migrate(target):
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor

    connection = connections["default"]
    MigrationExecutor(connection).migrate([target])


def assert_forward_catalog(cursor):
    cursor.execute("SHOW server_version")
    server_version = cursor.fetchone()[0]
    cursor.execute("SHOW server_version_num")
    server_version_num = cursor.fetchone()[0]
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    require(server_version_num == "180006", f"server version number gate failed: {server_version_num}")
    require(server_version == "18.6" or server_version.startswith("18.6 ("), f"server gate failed: {server_version}")
    require("PostgreSQL 18.6" in version, "version() gate failed")

    cursor.execute(
        "SELECT n.nspname,c.relname,c.relrowsecurity,c.relforcerowsecurity,owner.rolname "
        "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "JOIN pg_roles owner ON owner.oid=c.relowner "
        "WHERE (n.nspname='qms' AND c.relname IN ('tenant_projection','organization','user_projection')) "
        "OR (n.nspname='eventing' AND c.relname IN ('domain_event','transactional_outbox','consumer_receipt')) "
        "OR (n.nspname='audit' AND c.relname='immutable_audit_log') "
        "ORDER BY c.relname"
    )
    protected_tables = cursor.fetchall()
    require(len(protected_tables) == 7, "Phase 3 protected tables missing")
    require(all(row[2] and row[3] for row in protected_tables), "ENABLE/FORCE RLS missing")
    require(all(row[4] == os.environ["FOUNDATION_MIGRATOR_ROLE"] for row in protected_tables), "runtime owns protected table")

    cursor.execute(
        "SELECT cmd, roles FROM pg_policies "
        "WHERE (schemaname='qms' AND tablename IN ('tenant_projection','organization','user_projection')) "
        "OR (schemaname='eventing' AND tablename IN ('domain_event','transactional_outbox','consumer_receipt')) "
        "OR (schemaname='audit' AND tablename='immutable_audit_log')"
    )
    policies = cursor.fetchall()
    require(len(policies) == 28, f"unexpected Phase 3 policy count: {len(policies)}")
    return server_version, server_version_num, version, protected_tables, policies


def create_fixture(cursor):
    app = os.environ["FOUNDATION_APP_ROLE"].replace('"', '""')
    worker = os.environ["FOUNDATION_WORKER_ROLE"].replace('"', '""')
    migrator = os.environ["FOUNDATION_MIGRATOR_ROLE"].replace('"', '""')
    cursor.execute(
        f'''CREATE TABLE qms.foundation_test_tenant_child (
            id uuid PRIMARY KEY,
            tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
            payload varchar(255) NOT NULL,
            UNIQUE (tenant_id, id)
        );
        CREATE FUNCTION qms.foundation_test_reject_tenant_change()
        RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
        BEGIN
            IF OLD.tenant_id IS DISTINCT FROM NEW.tenant_id THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='tenant_id is immutable';
            END IF;
            RETURN NEW;
        END $fn$;
        CREATE TRIGGER foundation_test_child_tenant_immutable
        BEFORE UPDATE ON qms.foundation_test_tenant_child
        FOR EACH ROW EXECUTE FUNCTION qms.foundation_test_reject_tenant_change();
        ALTER TABLE qms.foundation_test_tenant_child ENABLE ROW LEVEL SECURITY;
        ALTER TABLE qms.foundation_test_tenant_child FORCE ROW LEVEL SECURITY;
        CREATE POLICY foundation_test_child_select ON qms.foundation_test_tenant_child
          FOR SELECT TO "{app}", "{worker}"
          USING (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
        CREATE POLICY foundation_test_child_insert ON qms.foundation_test_tenant_child
          FOR INSERT TO "{app}", "{worker}"
          WITH CHECK (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
        CREATE POLICY foundation_test_child_update ON qms.foundation_test_tenant_child
          FOR UPDATE TO "{app}", "{worker}"
          USING (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid)
          WITH CHECK (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
        CREATE POLICY foundation_test_child_delete ON qms.foundation_test_tenant_child
          FOR DELETE TO "{app}", "{worker}"
          USING (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
        CREATE POLICY foundation_test_child_migrator ON qms.foundation_test_tenant_child
          FOR ALL TO "{migrator}" USING (true) WITH CHECK (true);
        GRANT SELECT,INSERT,UPDATE,DELETE ON qms.foundation_test_tenant_child TO "{app}", "{worker}";''',
        params=None,
    )


def seed(cursor):
    cursor.execute(
        "INSERT INTO qms.tenant_projection "
        "(id,adminapps_tenant_id,source_version,source_event_id,display_name_snapshot,"
        "lifecycle_status,provisioning_status,reconciliation_status,last_synced_at) "
        "VALUES (%s,%s,5,%s,'Tenant A','active','complete','in_sync',statement_timestamp()),"
        "(%s,%s,5,%s,'Tenant B','active','complete','in_sync',statement_timestamp())",
        [str(TENANT_A), "10000000-0000-4000-8000-000000000001", "a0000000-0000-4000-8000-000000000001",
         str(TENANT_B), "20000000-0000-4000-8000-000000000001", "b0000000-0000-4000-8000-000000000001"],
    )
    cursor.execute(
        "INSERT INTO qms.foundation_test_tenant_child(id,tenant_id,payload) VALUES (%s,%s,'A only'),(%s,%s,'B only')",
        [str(CHILD_A), str(TENANT_A), str(CHILD_B), str(TENANT_B)],
    )
    cursor.execute(
        "INSERT INTO qms.organization(id,tenant_id,display_name) VALUES (%s,%s,'Organization A'),(%s,%s,'Organization B')",
        [str(ORG_A), str(TENANT_A), str(ORG_B), str(TENANT_B)],
    )


def run():
    configure_django()
    from django.db import connections
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    migrator = connections["default"]
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.tenant_projection')")
        require(cursor.fetchone()[0] is None, "database was not empty for foundation")

    # Empty DB 0001 -> 0002 -> 0003, reverse only Phase 3, then forward again.
    migrate(MIGRATION)
    with migrator.cursor() as cursor:
        first_version = assert_forward_catalog(cursor)[:3]
    migrate(PHASE2_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('qms.tenant_projection'),to_regclass('qms.organization'),"
            "to_regclass('qms.user_projection'),to_regclass('eventing.domain_event'),"
            "to_regclass('audit.immutable_audit_log')"
        )
        require(
            cursor.fetchone() == ("qms.tenant_projection", "qms.organization", "qms.user_projection", None, None),
            "Phase 3 reverse did not preserve the promoted 0001 + 0002 foundation",
        )
    migrate(MIGRATION)

    with migrator.cursor() as cursor:
        server_version, server_version_num, version, protected_tables, policies = assert_forward_catalog(cursor)
        cursor.execute(
            "SELECT rolname,rolcanlogin,rolsuper,rolbypassrls FROM pg_roles "
            "WHERE rolname IN (%s,%s,%s,%s,%s) ORDER BY rolname",
            [os.environ["FOUNDATION_MIGRATOR_ROLE"], os.environ["FOUNDATION_APP_ROLE"],
             os.environ["FOUNDATION_WORKER_ROLE"], os.environ["FOUNDATION_PROJECTOR_ROLE"],
             os.environ["FOUNDATION_AUDIT_WRITER_ROLE"]],
        )
        role_rows = cursor.fetchall()
        require(len(role_rows) == 5 and all(r[1] for r in role_rows), "required LOGIN principals missing")
        runtime_rows = [r for r in role_rows if r[0] != os.environ["FOUNDATION_MIGRATOR_ROLE"]]
        require(all(not r[2] and not r[3] for r in runtime_rows), "runtime principal bypasses RLS")
        create_fixture(cursor)
        seed(cursor)

    from foundation.projection_contract import validate_projection_event
    from foundation.projection_writer import (
        InvalidLifecycleTransition,
        ProjectionResultKind,
        ProjectionVersionConflict,
        ProjectionVersionRegression,
        ProjectionWriterService,
    )

    fixtures = json.loads(
        (BACKEND_ROOT / "foundation" / "fixtures" / "adminapps_projection_events.json").read_text(encoding="utf-8")
    )
    writer = ProjectionWriterService(using="projector")
    tenant_c_id = "30000000-0000-4000-8000-000000000001"
    tenant_create = dict(fixtures["tenant_valid"], aggregate_id=tenant_c_id, adminapps_tenant_id=tenant_c_id)
    created = writer.apply(validate_projection_event(tenant_create))
    replay = writer.apply(validate_projection_event(tenant_create))
    tenant_advance = dict(fixtures["tenant_version_advancement"], aggregate_id=tenant_c_id, adminapps_tenant_id=tenant_c_id)
    advanced = writer.apply(validate_projection_event(tenant_advance))
    require(created.kind is ProjectionResultKind.APPLIED, "tenant event was not applied")
    require(replay.kind is ProjectionResultKind.IDEMPOTENT_REPLAY, "same event/version was not idempotent")
    require(advanced.source_version == 2, "higher tenant source version was not applied")
    tenant_conflict = dict(fixtures["tenant_same_version_conflict"], aggregate_id=tenant_c_id, adminapps_tenant_id=tenant_c_id)
    expect_error(lambda: writer.apply(validate_projection_event(tenant_conflict)), "already belongs to event")
    tenant_lower = dict(fixtures["tenant_lower_version"], aggregate_id=tenant_c_id, adminapps_tenant_id=tenant_c_id)
    expect_error(lambda: writer.apply(validate_projection_event(tenant_lower)), "is lower than")

    invalid_transition = dict(
        tenant_advance,
        event_id="abababab-abab-4bab-8bab-abababababab",
        source_version=3,
        payload={"display_name": "must rollback", "lifecycle_status": "deleted_tombstone"},
    )
    expect_error(lambda: writer.apply(validate_projection_event(invalid_transition)), "is not allowed")
    with connections["default"].cursor() as cursor:
        cursor.execute(
            "SELECT source_version,display_name_snapshot FROM qms.tenant_projection WHERE adminapps_tenant_id=%s",
            [tenant_c_id],
        )
        require(cursor.fetchone() == (2, "Tenant A Updated"), "failed projection event left partial state")

    user_created = writer.apply(validate_projection_event(fixtures["user_valid"]))
    user_replay = writer.apply(validate_projection_event(fixtures["user_valid"]))
    user_advanced = writer.apply(validate_projection_event(fixtures["user_version_advancement"]))
    require(user_created.kind is ProjectionResultKind.APPLIED, "user projection create failed")
    require(user_replay.kind is ProjectionResultKind.IDEMPOTENT_REPLAY, "user replay was not idempotent")
    require(user_advanced.source_version == 2, "user version advancement failed")
    user_conflict = dict(
        fixtures["user_version_advancement"],
        event_id="67676767-6767-4676-8676-676767676767",
        payload={"lifecycle_status": "active"},
    )
    expect_error(lambda: writer.apply(validate_projection_event(user_conflict)), "already belongs to event")
    user_lower = dict(
        fixtures["user_valid"],
        event_id="56565656-5656-4565-8565-565656565656",
    )
    expect_error(lambda: writer.apply(validate_projection_event(user_lower)), "is lower than")
    user_b = dict(
        fixtures["user_valid"],
        event_id="b5555555-5555-4555-8555-555555555555",
        aggregate_id="60000000-0000-4000-8000-000000000001",
        adminapps_tenant_id="20000000-0000-4000-8000-000000000001",
    )
    writer.apply(validate_projection_event(user_b))

    projection_matrix = {
        "app_a": visible_projections("app", TENANT_A),
        "app_b": visible_projections("app", TENANT_B),
        "app_none": visible_projections("app"),
        "worker_a": visible_projections("worker", TENANT_A),
        "worker_b": visible_projections("worker", TENANT_B),
        "worker_none": visible_projections("worker"),
    }
    require(projection_matrix == {
        "app_a": ["Tenant A"], "app_b": ["Tenant B"], "app_none": [],
        "worker_a": ["Tenant A"], "worker_b": ["Tenant B"], "worker_none": [],
    }, "TenantProjection A/B/none matrix failed")

    child_matrix = {
        "app_a": visible_children("app", TENANT_A), "app_b": visible_children("app", TENANT_B),
        "app_none": visible_children("app"), "worker_a": visible_children("worker", TENANT_A),
        "worker_b": visible_children("worker", TENANT_B), "worker_none": visible_children("worker"),
    }
    require(child_matrix == {
        "app_a": ["A only"], "app_b": ["B only"], "app_none": [],
        "worker_a": ["A only"], "worker_b": ["B only"], "worker_none": [],
    }, "synthetic child A/B/none matrix failed")

    organization_matrix = {
        "app_a": visible_organizations("app", TENANT_A), "app_b": visible_organizations("app", TENANT_B),
        "app_none": visible_organizations("app"), "worker_a": visible_organizations("worker", TENANT_A),
        "worker_b": visible_organizations("worker", TENANT_B), "worker_none": visible_organizations("worker"),
    }
    require(organization_matrix == {
        "app_a": ["Organization A"], "app_b": ["Organization B"], "app_none": [],
        "worker_a": ["Organization A"], "worker_b": ["Organization B"], "worker_none": [],
    }, "Organization A/B/none matrix failed")

    user_matrix = {
        "app_a": visible_users("app", TENANT_A), "app_b": visible_users("app", TENANT_B),
        "app_none": visible_users("app"), "worker_a": visible_users("worker", TENANT_A),
        "worker_b": visible_users("worker", TENANT_B), "worker_none": visible_users("worker"),
    }
    require(user_matrix == {
        "app_a": ["50000000-0000-4000-8000-000000000001"],
        "app_b": ["60000000-0000-4000-8000-000000000001"], "app_none": [],
        "worker_a": ["50000000-0000-4000-8000-000000000001"],
        "worker_b": ["60000000-0000-4000-8000-000000000001"], "worker_none": [],
    }, "UserProjection A/B/none matrix failed")

    for alias in ("app", "worker"):
        for projection_table in ("tenant_projection", "user_projection"):
            for command in ("INSERT", "UPDATE", "DELETE"):
                with migrator.cursor() as cursor:
                    cursor.execute(
                        "SELECT has_table_privilege(%s,%s,%s)",
                        [os.environ[f"FOUNDATION_{alias.upper()}_ROLE"], f"qms.{projection_table}", command],
                    )
                    require(cursor.fetchone()[0] is False, f"{alias} has {projection_table} {command}")

        def projection_update():
            with runtime_transaction(alias, TENANT_A) as cursor:
                cursor.execute("UPDATE qms.tenant_projection SET display_name_snapshot='forbidden' WHERE id=%s", [str(TENANT_A)])
        expect_error(projection_update, "permission denied")

        def projection_insert():
            with runtime_transaction(alias, TENANT_A) as cursor:
                cursor.execute(
                    "INSERT INTO qms.tenant_projection(id,adminapps_tenant_id,source_version,display_name_snapshot,last_synced_at) "
                    "VALUES (%s,%s,1,'forbidden',statement_timestamp())",
                    ["aaaaaaaa-0000-4000-8000-000000000088", "40000000-0000-4000-8000-000000000001"],
                )
        expect_error(projection_insert, "permission denied")

        def projection_delete():
            with runtime_transaction(alias, TENANT_A) as cursor:
                cursor.execute("DELETE FROM qms.tenant_projection WHERE id=%s", [str(TENANT_A)])
        expect_error(projection_delete, "permission denied")

    with migrator.cursor() as cursor:
        for command in ("INSERT", "UPDATE", "DELETE"):
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.organization',%s)",
                [os.environ["FOUNDATION_PROJECTOR_ROLE"], command],
            )
            require(cursor.fetchone()[0] is False, f"projector has Organization {command}")
        cursor.execute(
            "SELECT has_table_privilege(%s,'qms.tenant_projection','DELETE'),"
            "has_table_privilege(%s,'qms.user_projection','DELETE')",
            [os.environ["FOUNDATION_PROJECTOR_ROLE"], os.environ["FOUNDATION_PROJECTOR_ROLE"]],
        )
        require(cursor.fetchone() == (False, False), "projector can delete projections")

    def untrusted_projector_insert():
        with runtime_transaction("projector") as cursor:
            cursor.execute(
                "INSERT INTO qms.tenant_projection "
                "(id,adminapps_tenant_id,source_version,source_event_id,display_name_snapshot,last_synced_at) "
                "VALUES (%s,%s,1,%s,'untrusted',statement_timestamp())",
                ["dddddddd-dddd-4ddd-8ddd-dddddddddddd", "40000000-0000-4000-8000-000000000001",
                 "dddddddd-0000-4000-8000-000000000001"],
            )
    expect_error(untrusted_projector_insert, "row-level security")

    org_temp = "aaaaaaaa-1000-4000-8000-000000000077"
    with runtime_transaction("app", TENANT_A) as cursor:
        cursor.execute(
            "INSERT INTO qms.organization(id,tenant_id,display_name) VALUES (%s,%s,'Temporary')",
            [org_temp, str(TENANT_A)],
        )
        cursor.execute("UPDATE qms.organization SET display_name='Temporary Updated' WHERE id=%s", [org_temp])
        require(cursor.rowcount == 1, "Organization A update was not allowed")
        cursor.execute("UPDATE qms.organization SET display_name='cross' WHERE id=%s", [str(ORG_B)])
        require(cursor.rowcount == 0, "Organization A updated tenant B")
        cursor.execute("DELETE FROM qms.organization WHERE id=%s", [str(ORG_B)])
        require(cursor.rowcount == 0, "Organization A deleted tenant B")
        cursor.execute("DELETE FROM qms.organization WHERE id=%s", [org_temp])
        require(cursor.rowcount == 1, "Organization A delete was not allowed")

    def organization_wrong_insert():
        with runtime_transaction("app", TENANT_A) as cursor:
            cursor.execute(
                "INSERT INTO qms.organization(id,tenant_id,display_name) VALUES (%s,%s,'wrong')",
                ["aaaaaaaa-1000-4000-8000-000000000099", str(TENANT_B)],
            )
    expect_error(organization_wrong_insert, "row-level security")

    def organization_no_context_insert():
        with runtime_transaction("app") as cursor:
            cursor.execute(
                "INSERT INTO qms.organization(id,tenant_id,display_name) VALUES (%s,%s,'none')",
                ["aaaaaaaa-1000-4000-8000-000000000098", str(TENANT_A)],
            )
    expect_error(organization_no_context_insert, "row-level security")

    with runtime_transaction("app") as cursor:
        cursor.execute("UPDATE qms.organization SET display_name='none' WHERE id=%s", [str(ORG_A)])
        require(cursor.rowcount == 0, "no-context Organization update was visible")
        cursor.execute("DELETE FROM qms.organization WHERE id=%s", [str(ORG_A)])
        require(cursor.rowcount == 0, "no-context Organization delete was visible")

    def organization_tenant_move_independent_of_rls():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.organization SET tenant_id=%s WHERE id=%s", [str(TENANT_B), str(ORG_A)])
    expect_error(organization_tenant_move_independent_of_rls, "organization tenant_id is immutable")
    migrator.rollback()

    with runtime_transaction("worker", TENANT_A) as cursor:
        cursor.execute("UPDATE qms.organization SET display_name='Organization A Worker' WHERE id=%s", [str(ORG_A)])
        require(cursor.rowcount == 1, "worker scoped Organization update failed")

    def worker_organization_delete():
        with runtime_transaction("worker", TENANT_A) as cursor:
            cursor.execute("DELETE FROM qms.organization WHERE id=%s", [str(ORG_A)])
    expect_error(worker_organization_delete, "permission denied")

    def wrong_insert():
        with runtime_transaction("app", TENANT_A) as cursor:
            cursor.execute("INSERT INTO qms.foundation_test_tenant_child(id,tenant_id,payload) VALUES (%s,%s,'wrong')", ["aaaaaaaa-0000-4000-8000-000000000099", str(TENANT_B)])
    expect_error(wrong_insert, "row-level security")

    def no_context_insert():
        with runtime_transaction("app") as cursor:
            cursor.execute("INSERT INTO qms.foundation_test_tenant_child(id,tenant_id,payload) VALUES (%s,%s,'none')", ["aaaaaaaa-0000-4000-8000-000000000098", str(TENANT_A)])
    expect_error(no_context_insert, "row-level security")

    def tenant_move():
        with runtime_transaction("app", TENANT_A) as cursor:
            cursor.execute("UPDATE qms.foundation_test_tenant_child SET tenant_id=%s WHERE id=%s", [str(TENANT_B), str(CHILD_A)])
    expect_error(tenant_move, "tenant_id is immutable")

    with migrator.cursor() as cursor:
        for column, value in (("lifecycle_status", "invalid"), ("provisioning_status", "invalid"), ("reconciliation_status", "invalid")):
            def invalid_status(column=column, value=value):
                with migrator.cursor() as invalid_cursor:
                    invalid_cursor.execute(f"UPDATE qms.tenant_projection SET {column}=%s WHERE id=%s", [value, str(TENANT_A)])
            expect_error(invalid_status, "check constraint")
        migrator.rollback()

        def external_id_change():
            with migrator.cursor() as c:
                c.execute("UPDATE qms.tenant_projection SET adminapps_tenant_id=%s WHERE id=%s", ["30000000-0000-4000-8000-000000000001", str(TENANT_A)])
        expect_error(external_id_change, "AdminApps tenant identity is immutable")
        migrator.rollback()

        def version_decrease():
            with migrator.cursor() as c:
                c.execute("UPDATE qms.tenant_projection SET source_version=4 WHERE id=%s", [str(TENANT_A)])
        expect_error(version_decrease, "source version cannot decrease")
        migrator.rollback()

        def user_external_id_change():
            with migrator.cursor() as c:
                c.execute(
                    "UPDATE qms.user_projection SET adminapps_user_id=%s WHERE adminapps_user_id=%s",
                    ["70000000-0000-4000-8000-000000000001", "50000000-0000-4000-8000-000000000001"],
                )
        expect_error(user_external_id_change, "AdminApps user identity is immutable")
        migrator.rollback()

        def user_tenant_change():
            with migrator.cursor() as c:
                c.execute(
                    "UPDATE qms.user_projection SET tenant_id=%s WHERE adminapps_user_id=%s",
                    [str(TENANT_B), "50000000-0000-4000-8000-000000000001"],
                )
        expect_error(user_tenant_change, "user projection tenant_id is immutable")
        migrator.rollback()

        def user_version_decrease():
            with migrator.cursor() as c:
                c.execute(
                    "UPDATE qms.user_projection SET source_version=1 WHERE adminapps_user_id=%s",
                    ["50000000-0000-4000-8000-000000000001"],
                )
        expect_error(user_version_decrease, "source version cannot decrease")
        migrator.rollback()

    pool_reuse = [visible_children("app", TENANT_A), visible_children("app"), visible_children("app", TENANT_B)]
    require(pool_reuse == [["A only"], [], ["B only"]], "connection reuse leaked context")
    try:
        with runtime_transaction("app", TENANT_A) as cursor:
            cursor.execute("SELECT payload FROM qms.foundation_test_tenant_child")
            raise RuntimeError("intentional rollback")
    except RuntimeError:
        pass
    rollback_reuse = [visible_children("app"), visible_children("app", TENANT_B)]
    require(rollback_reuse == [[], ["B only"]], "rollback leaked context")
    organization_pool_reuse = [
        visible_organizations("app", TENANT_A),
        visible_organizations("app"),
        visible_organizations("app", TENANT_B),
    ]
    require(
        organization_pool_reuse == [["Organization A Worker"], [], ["Organization B"]],
        "Organization connection reuse leaked context",
    )

    identity = TrustedTenantIdentity("authorized-subject-a", TENANT_A)
    with trusted_tenant_context(identity, actor_id=identity.subject, trace_id="trusted-trace", using="app"):
        with connections["app"].cursor() as cursor:
            cursor.execute("SELECT display_name_snapshot FROM qms.tenant_projection")
            require(cursor.fetchall() == [("Tenant A",)], "permanent trusted context failed")
    with connections["app"].cursor() as cursor:
        cursor.execute("SELECT NULLIF(current_setting('app.tenant_id',true),'')")
        require(cursor.fetchone()[0] is None, "trusted context survived commit")
    signature = inspect.signature(trusted_tenant_context)
    require(not ({"tenant_id", "body", "query", "header"} & set(signature.parameters)), "spoofable public context API")

    # Raw SQL allowed operations remain protected on the temporary child.
    disposable = "aaaaaaaa-0000-4000-8000-000000000077"
    with runtime_transaction("app", TENANT_A) as cursor:
        cursor.execute("INSERT INTO qms.foundation_test_tenant_child VALUES (%s,%s,'temp')", [disposable, str(TENANT_A)])
        cursor.execute("UPDATE qms.foundation_test_tenant_child SET payload='updated' WHERE id=%s", [disposable])
        require(cursor.rowcount == 1, "raw UPDATE failed")
        cursor.execute("DELETE FROM qms.foundation_test_tenant_child WHERE id=%s", [disposable])
        require(cursor.rowcount == 1, "raw DELETE failed")

    # Phase 3: business mutation + event + outbox + audit always share one commit.
    from copy import copy
    from uuid import uuid4

    from foundation.audit import calculate_entry_hash, verify_audit_stream
    from foundation.canonical import canonical_hash, canonical_json
    from foundation.eventing import (
        ConsumerReceiptService,
        OrganizationEventingService,
        OutboxDeliveryService,
        PayloadIntegrityConflict,
        ReceiptResultKind,
        ReplayService,
    )
    from foundation.models import ImmutableAuditLog

    identity_a = TrustedTenantIdentity("authorized-subject-a", TENANT_A)
    identity_b = TrustedTenantIdentity("authorized-subject-b", TENANT_B)
    command = OrganizationEventingService(using="app")
    trace_a1 = UUID("aaaaaaaa-3000-4000-8000-000000000001")
    success = command.rename(
        identity=identity_a, organization_id=ORG_A, display_name="Organization A Event 1",
        actor_id="actor-a", trace_id=trace_a1,
        correlation_id=UUID("aaaaaaaa-3100-4000-8000-000000000001"),
        causation_id=UUID("aaaaaaaa-3200-4000-8000-000000000001"),
    )
    with runtime_transaction("app", TENANT_A) as cursor:
        cursor.execute(
            "SELECT o.display_name,e.tenant_id=e2.tenant_id,e.trace_id,a.trace_id,a.entity_id "
            "FROM qms.organization o "
            "JOIN eventing.domain_event e ON e.aggregate_id=o.id "
            "JOIN eventing.transactional_outbox e2 ON e2.domain_event_id=e.event_id "
            "JOIN audit.immutable_audit_log a ON a.entity_id=o.id AND a.trace_id=e.trace_id "
            "WHERE o.id=%s AND e.event_id=%s AND e2.id=%s AND a.id=%s",
            [str(ORG_A), str(success.event_id), str(success.outbox_id), str(success.audit_id)],
        )
        require(
            cursor.fetchone() == ("Organization A Event 1", True, trace_a1, trace_a1, ORG_A),
            "successful atomic Organization/event/outbox/audit traceability failed",
        )

    with runtime_transaction("app", TENANT_A) as cursor:
        cursor.execute("SELECT display_name FROM qms.organization WHERE id=%s", [str(ORG_A)])
        rollback_pre_name = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM eventing.domain_event")
        rollback_pre_events = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM eventing.transactional_outbox")
        rollback_pre_outbox = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM audit.immutable_audit_log")
        rollback_pre_audit = cursor.fetchone()[0]
    expect_error(
        lambda: command.rename(
            identity=identity_a, organization_id=ORG_A, display_name="MUST ROLLBACK",
            actor_id="actor-a", trace_id=UUID("aaaaaaaa-3000-4000-8000-000000000099"),
            fail_before_commit=True,
        ),
        "deliberate Phase 3 rollback",
    )
    with runtime_transaction("app", TENANT_A) as cursor:
        cursor.execute("SELECT display_name FROM qms.organization WHERE id=%s", [str(ORG_A)])
        require(cursor.fetchone()[0] == rollback_pre_name, "Organization mutation survived rollback")
        cursor.execute("SELECT count(*) FROM eventing.domain_event")
        require(cursor.fetchone()[0] == rollback_pre_events, "DomainEvent survived rollback")
        cursor.execute("SELECT count(*) FROM eventing.transactional_outbox")
        require(cursor.fetchone()[0] == rollback_pre_outbox, "Outbox survived rollback")
        cursor.execute("SELECT count(*) FROM audit.immutable_audit_log")
        require(cursor.fetchone()[0] == rollback_pre_audit, "Audit entry survived rollback")

    # Complete a three-entry organization stream and create symmetric tenant B data.
    for suffix in (2, 3):
        command.rename(
            identity=identity_a, organization_id=ORG_A,
            display_name=f"Organization A Event {suffix}", actor_id="actor-a", trace_id=uuid4(),
        )
    command.rename(
        identity=identity_b, organization_id=ORG_B, display_name="Organization B Event 1",
        actor_id="actor-b", trace_id=uuid4(),
    )
    with trusted_tenant_context(identity_a, actor_id="verifier", trace_id=uuid4(), using="app"):
        require(
            verify_audit_stream(tenant_id=TENANT_A, stream_type="organization", stream_id=ORG_A, using="app"),
            "three-entry audit chain did not verify",
        )
        entries = list(
            ImmutableAuditLog.objects.using("app")
            .filter(stream_type="organization", stream_id=ORG_A)
            .order_by("sequence_number")
        )
        require([entry.sequence_number for entry in entries] == [1, 2, 3], "audit sequence is not monotonic")
        require(entries[0].previous_entry_hash is None, "audit genesis previous hash is not null")
        require(entries[1].previous_entry_hash == entries[0].entry_hash, "audit chain link 1->2 failed")
        require(entries[2].previous_entry_hash == entries[1].entry_hash, "audit chain link 2->3 failed")
        tampered_copy = copy(entries[1])
        tampered_copy.metadata_canonical = canonical_json({"copied": "modified payload"})
        tampered_copy.payload_hash = canonical_hash({"copied": "modified payload"})
        require(calculate_entry_hash(tampered_copy) != entries[1].entry_hash, "tampered audit copy was not detected")

    # At-least-once delivery preserves the row and increments every claim attempt.
    delivery = OutboxDeliveryService(using="worker")
    worker_trace = UUID("aaaaaaaa-4000-4000-8000-000000000001")
    claimed_id = delivery.claim_next(
        identity=identity_a, worker_id="worker-a", trace_id=worker_trace
    )
    require(claimed_id is not None, "worker did not claim an available outbox row")
    delivery.mark_failed(
        identity=identity_a, outbox_id=claimed_id, worker_id="worker-a",
        trace_id=worker_trace, error_code="temporary_failure",
    )
    retry_id = delivery.claim_next(
        identity=identity_a, worker_id="worker-a", trace_id=worker_trace
    )
    require(retry_id == claimed_id, "failed outbox row was not selected for retry")
    delivery.mark_published(
        identity=identity_a, outbox_id=retry_id, worker_id="worker-a", trace_id=worker_trace
    )
    with runtime_transaction("worker", TENANT_A) as cursor:
        cursor.execute(
            "SELECT status,publish_attempts,published_at IS NOT NULL,lease_owner IS NULL,lease_expires_at IS NULL FROM eventing.transactional_outbox WHERE id=%s",
            [str(claimed_id)],
        )
        require(cursor.fetchone() == ("published", 2, True, True, True), "outbox retry/publish history failed")

    from datetime import timedelta

    crash_delivery = OutboxDeliveryService(using="worker", lease_duration=timedelta(microseconds=1))
    crashed_claim = crash_delivery.claim_next(
        identity=identity_a, worker_id="crashed-worker", trace_id=worker_trace
    )
    recovered_claim = crash_delivery.claim_next(
        identity=identity_a, worker_id="recovery-worker", trace_id=worker_trace
    )
    require(crashed_claim == recovered_claim, "expired outbox lease was not reclaimed")
    crash_delivery.mark_failed(
        identity=identity_a, outbox_id=recovered_claim, worker_id="recovery-worker",
        trace_id=worker_trace, error_code="recovery_proof",
    )

    # Durable Inbox: one effect, same-hash duplicate, different-hash conflict.
    receipt_service = ConsumerReceiptService(using="worker")
    receipt_event_a = UUID("aaaaaaaa-5000-4000-8000-000000000001")
    receipt_event_b = UUID("bbbbbbbb-5000-4000-8000-000000000001")
    effects = []
    payload_a = {"value": 1, "nested": {"b": 2, "a": 1}}
    first_receipt = receipt_service.receive(
        identity=identity_a, consumer_name="phase3.test.consumer", event_id=receipt_event_a,
        payload=payload_a, trace_id=uuid4(), handler=lambda payload: effects.append(payload["value"]),
    )
    duplicate_receipt = receipt_service.receive(
        identity=identity_a, consumer_name="phase3.test.consumer", event_id=receipt_event_a,
        payload={"nested": {"a": 1, "b": 2}, "value": 1}, trace_id=uuid4(),
        handler=lambda payload: effects.append(999),
    )
    require(first_receipt.kind is ReceiptResultKind.PROCESSED, "first receipt was not processed")
    require(duplicate_receipt.kind is ReceiptResultKind.IDEMPOTENT_DUPLICATE, "replay was not idempotent")
    require(effects == [1], "duplicate receipt repeated the business effect")
    with runtime_transaction("worker", TENANT_A) as cursor:
        cursor.execute(
            "SELECT payload_hash,status,attempts FROM eventing.consumer_receipt WHERE event_id=%s",
            [str(receipt_event_a)],
        )
        original_receipt = cursor.fetchone()
    try:
        receipt_service.receive(
            identity=identity_a, consumer_name="phase3.test.consumer", event_id=receipt_event_a,
            payload={"value": 2}, trace_id=uuid4(), handler=lambda payload: effects.append(2),
        )
    except PayloadIntegrityConflict:
        pass
    else:
        raise AssertionError("payload substitution was accepted")
    with runtime_transaction("worker", TENANT_A) as cursor:
        cursor.execute(
            "SELECT payload_hash,status,attempts FROM eventing.consumer_receipt WHERE event_id=%s",
            [str(receipt_event_a)],
        )
        require(cursor.fetchone() == original_receipt, "payload substitution overwrote the receipt")
    require(effects == [1], "payload substitution executed a business effect")
    receipt_service.receive(
        identity=identity_b, consumer_name="phase3.test.consumer", event_id=receipt_event_b,
        payload={"value": 10}, trace_id=uuid4(), handler=lambda payload: None,
    )

    # Replay is an explicit append-only audit operation; the receipt remains intact.
    replay_id = ReplayService(using="app").request(
        identity=identity_a, event_id=receipt_event_a, consumer_name="phase3.test.consumer",
        actor_id="replay-operator", trace_id=uuid4(), reason="controlled Phase 3 replay test",
    )
    audit_writer_replay_id = ReplayService(using="audit_writer").request(
        identity=identity_a, event_id=UUID("aaaaaaaa-5000-4000-8000-000000000002"),
        consumer_name="phase3.audit-writer.consumer", actor_id="audit-writer-operator",
        trace_id=uuid4(), reason="prove real audit writer append boundary",
    )
    require(replay_id and audit_writer_replay_id, "controlled replay audit append failed")
    with runtime_transaction("worker", TENANT_A) as cursor:
        cursor.execute("SELECT count(*) FROM eventing.consumer_receipt WHERE event_id=%s", [str(receipt_event_a)])
        require(cursor.fetchone()[0] == 1, "replay operation deleted a durable receipt")

    # Two real audit-writer connections serialize one stream without duplicate sequence values.
    import threading

    concurrent_event_id = UUID("aaaaaaaa-5000-4000-8000-000000000003")
    barrier = threading.Barrier(2)
    concurrent_ids = []
    concurrent_errors = []
    result_lock = threading.Lock()

    def append_concurrently(index):
        try:
            barrier.wait(timeout=10)
            appended = ReplayService(using="audit_writer").request(
                identity=identity_a, event_id=concurrent_event_id,
                consumer_name=f"phase3.concurrent.consumer.{index}",
                actor_id=f"concurrent-writer-{index}", trace_id=uuid4(),
                reason=f"concurrent serialization proof {index}",
            )
            with result_lock:
                concurrent_ids.append(appended)
        except Exception as exc:
            with result_lock:
                concurrent_errors.append(str(exc))
        finally:
            connections["audit_writer"].close()

    threads = [threading.Thread(target=append_concurrently, args=(index,)) for index in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    require(not any(thread.is_alive() for thread in threads), "concurrent audit append timed out")
    require(not concurrent_errors and len(concurrent_ids) == 2, f"concurrent audit append failed: {concurrent_errors}")
    with trusted_tenant_context(identity_a, actor_id="verifier", trace_id=uuid4(), using="app"):
        concurrent_entries = list(
            ImmutableAuditLog.objects.using("app")
            .filter(stream_type="event-replay", stream_id=concurrent_event_id)
            .order_by("sequence_number")
        )
        require([entry.sequence_number for entry in concurrent_entries] == [1, 2], "concurrent audit sequence duplicated or skipped")
        require(
            verify_audit_stream(
                tenant_id=TENANT_A, stream_type="event-replay",
                stream_id=concurrent_event_id, using="app",
            ),
            "concurrent audit chain did not verify",
        )

    phase3_matrix = {}
    for table in ("domain_event", "transactional_outbox", "consumer_receipt", "immutable_audit_log"):
        values = {
            "app_a": visible_phase3("app", table, TENANT_A),
            "app_b": visible_phase3("app", table, TENANT_B),
            "app_none": visible_phase3("app", table),
            "worker_a": visible_phase3("worker", table, TENANT_A),
            "worker_b": visible_phase3("worker", table, TENANT_B),
            "worker_none": visible_phase3("worker", table),
        }
        require(values["app_a"] > 0 and values["app_b"] > 0, f"{table} lacks A/B fixtures")
        require(values["app_a"] == values["worker_a"], f"{table} A visibility differs by role")
        require(values["app_b"] == values["worker_b"], f"{table} B visibility differs by role")
        require(values["app_none"] == values["worker_none"] == 0, f"{table} no-context read did not fail closed")
        phase3_matrix[table] = values

    # Runtime cannot mutate history or forge audit sequence/hash through direct DML.
    def app_event_update():
        with runtime_transaction("app", TENANT_A) as cursor:
            cursor.execute("UPDATE eventing.domain_event SET event_type='forged' WHERE event_id=%s", [str(success.event_id)])
    expect_error(app_event_update, "permission denied")

    def app_event_delete():
        with runtime_transaction("app", TENANT_A) as cursor:
            cursor.execute("DELETE FROM eventing.domain_event WHERE event_id=%s", [str(success.event_id)])
    expect_error(app_event_delete, "permission denied")

    for alias in ("app", "worker", "audit_writer"):
        def audit_update(alias=alias):
            with runtime_transaction(alias, TENANT_A) as cursor:
                cursor.execute("UPDATE audit.immutable_audit_log SET action='forged' WHERE id=%s", [str(success.audit_id)])
        expect_error(audit_update, "permission denied")

        def audit_delete(alias=alias):
            with runtime_transaction(alias, TENANT_A) as cursor:
                cursor.execute("DELETE FROM audit.immutable_audit_log WHERE id=%s", [str(success.audit_id)])
        expect_error(audit_delete, "permission denied")

    def audit_truncate():
        with runtime_transaction("app", TENANT_A) as cursor:
            cursor.execute("TRUNCATE audit.immutable_audit_log")
    expect_error(audit_truncate, "permission denied")

    def audit_direct_forge():
        with runtime_transaction("audit_writer", TENANT_A) as cursor:
            cursor.execute(
                "INSERT INTO audit.immutable_audit_log(id,tenant_id,stream_type,stream_id,sequence_number,actor_type,action,entity_type,entity_id,trace_id,occurred_at,entry_hash) "
                "VALUES (%s,%s,'forged',%s,999,'forged','forged','forged',%s,%s,statement_timestamp(),%s)",
                [str(uuid4()), str(TENANT_A), str(ORG_A), str(ORG_A), str(uuid4()), "0" * 64],
            )
    expect_error(audit_direct_forge, "permission denied")

    # DB-level tenant/history guards are exercised as the migration owner, independently from RLS.
    guarded_updates = (
        ("UPDATE eventing.domain_event SET tenant_id=%s WHERE event_id=%s", [str(TENANT_B), str(success.event_id)], "append-only"),
        ("UPDATE eventing.transactional_outbox SET tenant_id=%s WHERE id=%s", [str(TENANT_B), str(success.outbox_id)], "identity and tenant are immutable"),
        ("UPDATE eventing.consumer_receipt SET tenant_id=%s WHERE event_id=%s", [str(TENANT_B), str(receipt_event_a)], "identity, tenant and payload hash are immutable"),
        ("UPDATE audit.immutable_audit_log SET tenant_id=%s WHERE id=%s", [str(TENANT_B), str(success.audit_id)], "append-only"),
    )
    for sql, params, fragment in guarded_updates:
        def guarded_update(sql=sql, params=params):
            with migrator.cursor() as cursor:
                cursor.execute(sql, params)
        expect_error(guarded_update, fragment)
        migrator.rollback()

    # No-context writes fail closed on every Phase 3 write surface.
    def no_context_event_insert():
        with runtime_transaction("app") as cursor:
            cursor.execute(
                "INSERT INTO eventing.domain_event(event_id,tenant_id,event_type,schema_version,aggregate_type,aggregate_id,aggregate_version,occurred_at,trace_id,source,payload,payload_hash) "
                "VALUES (%s,%s,'forged',1,'organization',%s,99,statement_timestamp(),%s,'test','{}',%s)",
                [str(uuid4()), str(TENANT_A), str(ORG_A), str(uuid4()), canonical_hash({})],
            )
    expect_error(no_context_event_insert, "row-level security")

    phase3_pool_reuse = {
        table: [visible_phase3("app", table, TENANT_A), visible_phase3("app", table), visible_phase3("app", table, TENANT_B)]
        for table in ("domain_event", "transactional_outbox", "consumer_receipt", "immutable_audit_log")
    }
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0 for values in phase3_pool_reuse.values()), "Phase 3 pool reuse leaked tenant context")
    try:
        with runtime_transaction("worker", TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM eventing.consumer_receipt")
            raise RuntimeError("intentional Phase 3 worker rollback")
    except RuntimeError:
        pass
    require(
        [visible_phase3("worker", "consumer_receipt"), visible_phase3("worker", "consumer_receipt", TENANT_B)] == [0, 1],
        "Phase 3 worker rollback leaked tenant context",
    )

    with migrator.cursor() as cursor:
        cursor.execute("DROP TABLE qms.foundation_test_tenant_child")
        cursor.execute("DROP FUNCTION qms.foundation_test_reject_tenant_change()")
    migrate(PHASE2_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('qms.tenant_projection'),to_regclass('qms.organization'),"
            "to_regclass('qms.user_projection'),to_regclass('eventing.domain_event'),"
            "to_regclass('audit.immutable_audit_log'),to_regclass('qms.foundation_test_tenant_child')"
        )
        require(
            cursor.fetchone() == ("qms.tenant_projection", "qms.organization", "qms.user_projection", None, None, None),
            "final Phase 3 reverse did not preserve promoted 0001 + 0002",
        )

    evidence = {
        "status": "PASS", "server_version": server_version, "server_version_num": server_version_num, "version": version,
        "principals": [list(r) for r in role_rows], "protected_tables": [list(r) for r in protected_tables],
        "projection_policies": [list(r) for r in policies], "projection_matrix": projection_matrix,
        "organization_matrix": organization_matrix, "user_projection_matrix": user_matrix,
        "synthetic_child_matrix": child_matrix, "projection_writes": "app/worker INSERT/UPDATE/DELETE denied; projector projection-only, no DELETE",
        "projection_event_semantics": "apply/replay/higher/conflict/lower PASS for TenantProjection and UserProjection",
        "projection_rollback": "invalid lifecycle rolled back with version and display snapshot unchanged",
        "protected_changes": "tenant/user external IDs immutable; Organization/User tenant immutable; source downgrade denied",
        "pool_reuse": pool_reuse, "organization_pool_reuse": organization_pool_reuse, "rollback_reuse": rollback_reuse,
        "trusted_context": "outermost SET LOCAL; commit cleanup; request-shaped values absent from public signature",
        "phase3_matrix": phase3_matrix,
        "atomic_success": "Organization + DomainEvent + Outbox + Audit committed with shared tenant/trace",
        "atomic_rollback": "Organization + DomainEvent + Outbox + Audit all rolled back",
        "inbox": "first processed; same-hash duplicate idempotent; payload substitution rejected without overwrite/effect",
        "outbox": "pending/failed/expired lease -> processing -> published/failed; attempts increment; rows retained",
        "audit_chain": "three entries verified; copied/modified payload failed recomputation; concurrent stream serialized as 1,2",
        "audit_controls": "runtime UPDATE/DELETE/TRUNCATE and direct forge denied; tenant/history guards tested",
        "phase3_pool_reuse": phase3_pool_reuse,
        "forward_reverse_forward": "0001 -> 0002 -> 0003 -> 0002 -> 0003 PASS", "final_reverse": "0003 -> 0002 PASS", "synthetic_fixture_removed": True,
        "first_forward_version": first_version,
    }
    print(json.dumps(evidence, indent=2, default=str, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
