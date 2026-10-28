from django.db import migrations, models
import uuid


FORWARD_SQL = r"""
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
DECLARE worker_role text := current_setting('foundation.worker_role', true);
DECLARE projector_role text := current_setting('foundation.projector_role', true);
DECLARE curator_role text := current_setting('foundation.normative_curator_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' OR
     projector_role IS NULL OR projector_role='' OR curator_role IS NULL OR curator_role='' THEN
    RAISE EXCEPTION 'IndustryProfile catalog roles are required';
  END IF;
  CREATE TABLE normative.industry_profile (
    industry_profile_id uuid PRIMARY KEY,
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    manufacturing_service_route text NOT NULL,
    terminology_pack text NOT NULL,
    CONSTRAINT normative_industry_profile_fields_nonblank CHECK (
      btrim(code)<>'' AND btrim(name)<>'' AND
      btrim(manufacturing_service_route)<>'' AND btrim(terminology_pack)<>''
    )
  );
  EXECUTE format('GRANT SELECT ON normative.industry_profile TO %I,%I,%I,%I',
                 app_role,worker_role,projector_role,curator_role);
  EXECUTE format('GRANT INSERT ON normative.industry_profile TO %I',curator_role);
END
$migration$;
"""

REVERSE_SQL = "DROP TABLE normative.industry_profile;"


class Migration(migrations.Migration):
    dependencies = [("foundation", "0031_tenant_standard_pack")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(
                    name="IndustryProfile",
                    fields=[
                        ("id", models.UUIDField(db_column="industry_profile_id", default=uuid.uuid4,
                                                editable=False, primary_key=True, serialize=False)),
                        ("code", models.TextField(unique=True)),
                        ("name", models.TextField()),
                        ("manufacturing_service_route", models.TextField()),
                        ("terminology_pack", models.TextField()),
                    ],
                    options={"db_table": 'normative"."industry_profile', "managed": False},
                ),
            ],
        ),
    ]