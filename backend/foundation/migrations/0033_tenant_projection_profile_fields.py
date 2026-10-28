from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = r"""
ALTER TABLE qms.tenant_projection
  ADD COLUMN plan text,
  ADD COLUMN locale text,
  ADD COLUMN industry_profile_id uuid;
ALTER TABLE qms.tenant_projection
  ADD CONSTRAINT qms_tenant_industry_profile_fk
  FOREIGN KEY(industry_profile_id)
  REFERENCES normative.industry_profile(industry_profile_id) ON DELETE RESTRICT;
CREATE INDEX qms_tenant_industry_profile_idx
  ON qms.tenant_projection(industry_profile_id) WHERE industry_profile_id IS NOT NULL;
"""

REVERSE_SQL = r"""
DROP INDEX qms.qms_tenant_industry_profile_idx;
ALTER TABLE qms.tenant_projection DROP CONSTRAINT qms_tenant_industry_profile_fk;
ALTER TABLE qms.tenant_projection
  DROP COLUMN industry_profile_id,
  DROP COLUMN locale,
  DROP COLUMN plan;
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0032_global_industry_profile")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.AddField(
                    model_name="tenantprojection", name="plan",
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="tenantprojection", name="locale",
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="tenantprojection", name="industry_profile",
                    field=models.ForeignKey(blank=True, db_column="industry_profile_id",
                                            null=True, on_delete=django.db.models.deletion.PROTECT,
                                            to="foundation.industryprofile"),
                ),
            ],
        ),
    ]