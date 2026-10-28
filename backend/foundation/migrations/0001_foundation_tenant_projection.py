"""Frozen foundation baseline: TenantProjection schema and database controls.

Cluster-scoped LOGIN roles are deliberately outside this migration.  The
deployment/test bootstrap must set ``foundation.app_role`` and
``foundation.worker_role`` on the migration connection before applying it.
"""

import uuid

from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
    schema_was_created boolean := false;
BEGIN
    IF app_role IS NULL OR app_role = '' OR worker_role IS NULL OR worker_role = '' THEN
        RAISE EXCEPTION 'foundation runtime roles were not supplied by cluster bootstrap';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = app_role AND rolcanlogin) OR
       NOT EXISTS (SELECT FROM pg_roles WHERE rolname = worker_role AND rolcanlogin) THEN
        RAISE EXCEPTION 'foundation runtime roles must be existing LOGIN principals';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_namespace WHERE nspname = 'qms') THEN
        CREATE SCHEMA qms;
        schema_was_created := true;
    END IF;

    CREATE TABLE qms.foundation_0001_ownership (
        singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
        schema_was_created boolean NOT NULL
    );
    INSERT INTO qms.foundation_0001_ownership(schema_was_created)
    VALUES (schema_was_created);

    CREATE TABLE qms.tenant_projection (
        id uuid PRIMARY KEY,
        adminapps_tenant_id uuid NOT NULL UNIQUE,
        source_version bigint NOT NULL,
        source_event_id uuid UNIQUE,
        display_name_snapshot varchar(255) NOT NULL,
        lifecycle_status varchar(32) NOT NULL DEFAULT 'pending',
        provisioning_status varchar(32) NOT NULL DEFAULT 'pending',
        reconciliation_status varchar(32) NOT NULL DEFAULT 'in_sync',
        reconciliation_error_code varchar(64),
        last_synced_at timestamptz NOT NULL,
        last_reconciled_at timestamptz,
        suspended_at timestamptz,
        deletion_requested_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT foundation_tenant_source_version_nonnegative CHECK (source_version >= 0),
        CONSTRAINT foundation_tenant_lifecycle_valid CHECK (lifecycle_status IN
            ('pending','active','suspended','deprovisioning','deleted_tombstone','drifted','unknown')),
        CONSTRAINT foundation_tenant_provisioning_valid CHECK (provisioning_status IN
            ('pending','partial','complete','failed')),
        CONSTRAINT foundation_tenant_reconciliation_valid CHECK (reconciliation_status IN
            ('in_sync','stale','missing_local','unexpected_local','version_conflict','authority_unavailable'))
    );

    CREATE FUNCTION qms.foundation_reject_tenant_projection_protected_change()
    RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, qms AS $function$
    BEGIN
        IF OLD.id IS DISTINCT FROM NEW.id THEN
            RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'tenant projection id is immutable';
        END IF;
        IF OLD.adminapps_tenant_id IS DISTINCT FROM NEW.adminapps_tenant_id THEN
            RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'AdminApps tenant identity is immutable';
        END IF;
        IF NEW.source_version < OLD.source_version THEN
            RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'source version cannot decrease';
        END IF;
        RETURN NEW;
    END
    $function$;

    CREATE TRIGGER foundation_tenant_projection_protected_change
    BEFORE UPDATE ON qms.tenant_projection
    FOR EACH ROW EXECUTE FUNCTION qms.foundation_reject_tenant_projection_protected_change();

    ALTER TABLE qms.tenant_projection ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.tenant_projection FORCE ROW LEVEL SECURITY;

    EXECUTE format(
        'CREATE POLICY foundation_tenant_projection_select ON qms.tenant_projection '
        'FOR SELECT TO %I, %I USING (id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid)',
        app_role, worker_role
    );
    EXECUTE format(
        'CREATE POLICY foundation_tenant_projection_migrator ON qms.tenant_projection '
        'FOR ALL TO %I USING (true) WITH CHECK (true)',
        current_user
    );
    EXECUTE format('GRANT USAGE ON SCHEMA qms TO %I, %I', app_role, worker_role);
    EXECUTE format('GRANT SELECT ON qms.tenant_projection TO %I, %I', app_role, worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DO $migration$
DECLARE
    schema_was_created boolean;
BEGIN
    SELECT o.schema_was_created INTO schema_was_created
    FROM qms.foundation_0001_ownership o WHERE o.singleton;

    DROP TABLE qms.tenant_projection;
    DROP FUNCTION qms.foundation_reject_tenant_projection_protected_change();
    DROP TABLE qms.foundation_0001_ownership;

    IF schema_was_created THEN
        DROP SCHEMA qms;
    END IF;
END
$migration$;
"""


def apply_postgresql_foundation(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_postgresql_foundation(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="TenantProjection",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("adminapps_tenant_id", models.UUIDField(editable=False, unique=True)),
                ("source_version", models.BigIntegerField()),
                ("source_event_id", models.UUIDField(null=True, unique=True)),
                ("display_name_snapshot", models.CharField(max_length=255)),
                ("lifecycle_status", models.CharField(choices=[("pending", "Pending"), ("active", "Active"), ("suspended", "Suspended"), ("deprovisioning", "Deprovisioning"), ("deleted_tombstone", "Deleted tombstone"), ("drifted", "Drifted"), ("unknown", "Unknown")], default="pending", max_length=32)),
                ("provisioning_status", models.CharField(choices=[("pending", "Pending"), ("partial", "Partial"), ("complete", "Complete"), ("failed", "Failed")], default="pending", max_length=32)),
                ("reconciliation_status", models.CharField(choices=[("in_sync", "In sync"), ("stale", "Stale"), ("missing_local", "Missing local"), ("unexpected_local", "Unexpected local"), ("version_conflict", "Version conflict"), ("authority_unavailable", "Authority unavailable")], default="in_sync", max_length=32)),
                ("reconciliation_error_code", models.CharField(blank=True, max_length=64, null=True)),
                ("last_synced_at", models.DateTimeField()),
                ("last_reconciled_at", models.DateTimeField(blank=True, null=True)),
                ("suspended_at", models.DateTimeField(blank=True, null=True)),
                ("deletion_requested_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": 'qms"."tenant_projection',
                "managed": False,
                "constraints": [
                    models.CheckConstraint(check=models.Q(("lifecycle_status__in", ["pending", "active", "suspended", "deprovisioning", "deleted_tombstone", "drifted", "unknown"])), name="foundation_tenant_lifecycle_valid"),
                    models.CheckConstraint(check=models.Q(("provisioning_status__in", ["pending", "partial", "complete", "failed"])), name="foundation_tenant_provisioning_valid"),
                    models.CheckConstraint(check=models.Q(("reconciliation_status__in", ["in_sync", "stale", "missing_local", "unexpected_local", "version_conflict", "authority_unavailable"])), name="foundation_tenant_reconciliation_valid"),
                    models.CheckConstraint(check=models.Q(("source_version__gte", 0)), name="foundation_tenant_source_version_nonnegative"),
                ],
            },
        ),
        migrations.RunPython(apply_postgresql_foundation, reverse_postgresql_foundation),
    ]
