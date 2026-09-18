"""Phase 2 additive projection boundary and Organization foundation.

The frozen 0001 is not altered.  LOGIN creation remains cluster/bootstrap work;
this migration receives existing app, worker and projector role names via GUCs.
"""

import uuid

from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
    projector_role text := current_setting('foundation.projector_role', true);
BEGIN
    IF app_role IS NULL OR app_role = '' OR worker_role IS NULL OR worker_role = '' OR
       projector_role IS NULL OR projector_role = '' THEN
        RAISE EXCEPTION 'foundation app, worker and projector roles are required';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname=projector_role AND rolcanlogin) THEN
        RAISE EXCEPTION 'foundation projector must be an existing LOGIN principal';
    END IF;

    CREATE TABLE qms.organization (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        display_name varchar(255) NOT NULL,
        legal_name varchar(255),
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT foundation_organization_tenant_id_id_unique UNIQUE (tenant_id,id)
    );
    CREATE INDEX foundation_organization_tenant_idx ON qms.organization(tenant_id,id);

    CREATE TABLE qms.user_projection (
        id uuid PRIMARY KEY,
        adminapps_user_id uuid NOT NULL UNIQUE,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        source_version bigint NOT NULL,
        source_event_id uuid NOT NULL UNIQUE,
        lifecycle_status varchar(32) NOT NULL DEFAULT 'active',
        last_synced_at timestamptz NOT NULL,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT foundation_user_source_version_nonnegative CHECK (source_version >= 0),
        CONSTRAINT foundation_user_lifecycle_valid CHECK
          (lifecycle_status IN ('active','suspended','revoked','deleted_tombstone')),
        CONSTRAINT foundation_user_tenant_id_id_unique UNIQUE (tenant_id,id)
    );
    CREATE INDEX foundation_user_projection_tenant_idx ON qms.user_projection(tenant_id,id);

    CREATE FUNCTION qms.foundation_reject_organization_tenant_change()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $function$
    BEGIN
        IF OLD.id IS DISTINCT FROM NEW.id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='organization id is immutable';
        END IF;
        IF OLD.tenant_id IS DISTINCT FROM NEW.tenant_id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='organization tenant_id is immutable';
        END IF;
        RETURN NEW;
    END $function$;
    CREATE TRIGGER foundation_organization_tenant_immutable
      BEFORE UPDATE ON qms.organization FOR EACH ROW
      EXECUTE FUNCTION qms.foundation_reject_organization_tenant_change();

    CREATE FUNCTION qms.foundation_reject_user_projection_protected_change()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $function$
    BEGIN
        IF OLD.id IS DISTINCT FROM NEW.id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='user projection id is immutable';
        END IF;
        IF OLD.adminapps_user_id IS DISTINCT FROM NEW.adminapps_user_id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='AdminApps user identity is immutable';
        END IF;
        IF OLD.tenant_id IS DISTINCT FROM NEW.tenant_id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='user projection tenant_id is immutable';
        END IF;
        IF NEW.source_version < OLD.source_version THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='source version cannot decrease';
        END IF;
        RETURN NEW;
    END $function$;
    CREATE TRIGGER foundation_user_projection_protected_change
      BEFORE UPDATE ON qms.user_projection FOR EACH ROW
      EXECUTE FUNCTION qms.foundation_reject_user_projection_protected_change();

    ALTER TABLE qms.organization ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.organization FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.user_projection ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.user_projection FORCE ROW LEVEL SECURITY;

    EXECUTE format('CREATE POLICY foundation_organization_select ON qms.organization FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_organization_insert ON qms.organization FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_organization_update ON qms.organization FOR UPDATE TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_organization_delete ON qms.organization FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY foundation_organization_migrator ON qms.organization FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);

    EXECUTE format('CREATE POLICY foundation_user_projection_select ON qms.user_projection FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_user_projection_projector_select ON qms.user_projection FOR SELECT TO %I USING (current_setting(''app.projection_source'',true)=''adminapps'')',projector_role);
    EXECUTE format('CREATE POLICY foundation_user_projection_projector_insert ON qms.user_projection FOR INSERT TO %I WITH CHECK (current_setting(''app.projection_source'',true)=''adminapps'')',projector_role);
    EXECUTE format('CREATE POLICY foundation_user_projection_projector_update ON qms.user_projection FOR UPDATE TO %I USING (current_setting(''app.projection_source'',true)=''adminapps'') WITH CHECK (current_setting(''app.projection_source'',true)=''adminapps'')',projector_role);
    EXECUTE format('CREATE POLICY foundation_user_projection_migrator ON qms.user_projection FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);

    EXECUTE format('CREATE POLICY foundation_tenant_projection_projector_select ON qms.tenant_projection FOR SELECT TO %I USING (current_setting(''app.projection_source'',true)=''adminapps'')',projector_role);
    EXECUTE format('CREATE POLICY foundation_tenant_projection_projector_insert ON qms.tenant_projection FOR INSERT TO %I WITH CHECK (current_setting(''app.projection_source'',true)=''adminapps'')',projector_role);
    EXECUTE format('CREATE POLICY foundation_tenant_projection_projector_update ON qms.tenant_projection FOR UPDATE TO %I USING (current_setting(''app.projection_source'',true)=''adminapps'') WITH CHECK (current_setting(''app.projection_source'',true)=''adminapps'')',projector_role);

    EXECUTE format('GRANT USAGE ON SCHEMA qms TO %I',projector_role);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.tenant_projection,qms.user_projection TO %I',projector_role);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON qms.organization TO %I',app_role);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.organization TO %I',worker_role);
    EXECUTE format('GRANT SELECT ON qms.user_projection TO %I,%I',app_role,worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DO $migration$
DECLARE
    projector_role text := current_setting('foundation.projector_role', true);
BEGIN
    DROP POLICY foundation_tenant_projection_projector_update ON qms.tenant_projection;
    DROP POLICY foundation_tenant_projection_projector_insert ON qms.tenant_projection;
    DROP POLICY foundation_tenant_projection_projector_select ON qms.tenant_projection;
    IF projector_role IS NOT NULL AND projector_role <> '' THEN
        EXECUTE format('REVOKE SELECT,INSERT,UPDATE ON qms.tenant_projection FROM %I',projector_role);
        EXECUTE format('REVOKE USAGE ON SCHEMA qms FROM %I',projector_role);
    END IF;
    DROP TABLE qms.user_projection;
    DROP FUNCTION qms.foundation_reject_user_projection_protected_change();
    DROP TABLE qms.organization;
    DROP FUNCTION qms.foundation_reject_organization_tenant_change();
END
$migration$;
"""


def apply_phase2(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase2(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0001_foundation_tenant_projection")]
    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("display_name", models.CharField(max_length=255)),
                ("legal_name", models.CharField(blank=True, max_length=255, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, related_name="qms_organizations", to="foundation.tenantprojection")),
            ],
            options={"db_table": 'qms"."organization', "managed": False},
        ),
        migrations.CreateModel(
            name="UserProjection",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("adminapps_user_id", models.UUIDField(editable=False, unique=True)),
                ("source_version", models.BigIntegerField()),
                ("source_event_id", models.UUIDField(unique=True)),
                ("lifecycle_status", models.CharField(choices=[("active", "Active"), ("suspended", "Suspended"), ("revoked", "Revoked"), ("deleted_tombstone", "Deleted tombstone")], default="active", max_length=32)),
                ("last_synced_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, related_name="user_projections", to="foundation.tenantprojection")),
            ],
            options={"db_table": 'qms"."user_projection', "managed": False},
        ),
        migrations.RunPython(apply_phase2, reverse_phase2),
    ]
