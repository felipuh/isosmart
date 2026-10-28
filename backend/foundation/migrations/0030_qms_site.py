from django.db import migrations, models
import django.db.models.deletion
import uuid


FORWARD_SQL = r"""
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
DECLARE worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'QMS Site app and worker roles are required';
  END IF;
  CREATE TABLE qms.site (
    site_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    organization_id uuid NOT NULL,
    country text NOT NULL,
    timezone text NOT NULL,
    criticality text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_site_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_site_tenant_org_id_unique UNIQUE(tenant_id,organization_id,site_id)
  );
  CREATE INDEX qms_site_tenant_organization_idx ON qms.site(tenant_id,organization_id,site_id);
  ALTER TABLE qms.site ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.site FORCE ROW LEVEL SECURITY;
  EXECUTE format('CREATE POLICY qms_site_select ON qms.site FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('CREATE POLICY qms_site_insert ON qms.site FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  EXECUTE format('CREATE POLICY qms_site_update ON qms.site FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  EXECUTE format('CREATE POLICY qms_site_delete ON qms.site FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  EXECUTE format('CREATE POLICY qms_site_migrator ON qms.site FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON qms.site TO %I',app_role);
  EXECUTE format('GRANT SELECT ON qms.site TO %I',worker_role);
END
$migration$;
"""

REVERSE_SQL = "DROP TABLE qms.site;"


class Migration(migrations.Migration):
    dependencies = [("foundation", "0029_context_twin_result_completion")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(
                    name="Site",
                    fields=[
                        ("id", models.UUIDField(db_column="site_id", default=uuid.uuid4,
                                                editable=False, primary_key=True, serialize=False)),
                        ("country", models.TextField()),
                        ("timezone", models.TextField()),
                        ("criticality", models.TextField()),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("organization", models.ForeignKey(db_column="organization_id",
                                                           on_delete=django.db.models.deletion.PROTECT,
                                                           to="foundation.organization")),
                        ("tenant", models.ForeignKey(db_column="tenant_id",
                                                      on_delete=django.db.models.deletion.PROTECT,
                                                      to="foundation.tenantprojection")),
                    ],
                    options={"db_table": 'qms"."site', "managed": False},
                ),
            ],
        ),
    ]