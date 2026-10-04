from django.db import migrations, models


FORWARD_SQL = r"""
ALTER TABLE qms.organization
  ADD COLUMN sector text,
  ADD COLUMN size text,
  ADD COLUMN maturity text;
"""

REVERSE_SQL = r"""
ALTER TABLE qms.organization
  DROP COLUMN maturity,
  DROP COLUMN size,
  DROP COLUMN sector;
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0033_tenant_projection_profile_fields")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.AddField("organization", "sector", models.TextField(blank=True, null=True)),
                migrations.AddField("organization", "size", models.TextField(blank=True, null=True)),
                migrations.AddField("organization", "maturity", models.TextField(blank=True, null=True)),
            ],
        ),
    ]