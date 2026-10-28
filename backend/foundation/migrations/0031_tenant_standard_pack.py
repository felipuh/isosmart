from django.db import migrations, models
import django.db.models.deletion
import uuid


FORWARD_SQL = r"""
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
DECLARE worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'StandardPack app and worker roles are required';
  END IF;
  CREATE TABLE qms.standard_pack (
    pack_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    standard_edition_id uuid NOT NULL REFERENCES normative.standard_edition(id) ON DELETE RESTRICT,
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp()
  );
  CREATE INDEX qms_standard_pack_tenant_edition_idx
    ON qms.standard_pack(tenant_id,standard_edition_id);
  ALTER TABLE qms.standard_pack ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.standard_pack FORCE ROW LEVEL SECURITY;
  EXECUTE format('CREATE POLICY qms_standard_pack_tenant ON qms.standard_pack FOR ALL TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('CREATE POLICY qms_standard_pack_migrator ON qms.standard_pack FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON qms.standard_pack TO %I',app_role);
  EXECUTE format('GRANT SELECT ON qms.standard_pack TO %I',worker_role);
END
$migration$;
"""

REVERSE_SQL = "DROP TABLE qms.standard_pack;"


class Migration(migrations.Migration):
    dependencies = [("foundation", "0030_qms_site")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(
                    name="StandardPack",
                    fields=[
                        ("id", models.UUIDField(db_column="pack_id", default=uuid.uuid4,
                                                editable=False, primary_key=True, serialize=False)),
                        ("status", models.TextField()),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("standard_edition", models.ForeignKey(db_column="standard_edition_id",
                                                               on_delete=django.db.models.deletion.PROTECT,
                                                               to="foundation.standardedition")),
                        ("tenant", models.ForeignKey(db_column="tenant_id",
                                                     on_delete=django.db.models.deletion.PROTECT,
                                                     to="foundation.tenantprojection")),
                    ],
                    options={"db_table": 'qms"."standard_pack', "managed": False},
                ),
            ],
        ),
    ]