from django.db import migrations, models


FORWARD_SQL = r"""
ALTER TABLE qms.user_projection
  ADD COLUMN email text,
  ADD COLUMN role text,
  ADD COLUMN mfa_status text;
"""

REVERSE_SQL = r"""
ALTER TABLE qms.user_projection
  DROP COLUMN mfa_status,
  DROP COLUMN role,
  DROP COLUMN email;
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0034_organization_source_profile_fields")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.AddField("userprojection", "email", models.TextField(blank=True, null=True)),
                migrations.AddField("userprojection", "role", models.TextField(blank=True, null=True)),
                migrations.AddField("userprojection", "mfa_status", models.TextField(blank=True, null=True)),
            ],
        ),
    ]