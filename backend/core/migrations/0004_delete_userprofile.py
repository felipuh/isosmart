# Generated manually on 2026-01-29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_organization_userprofile_organizationsettings_and_more'),
        ('authentication', '0002_userprofile'),
    ]

    operations = [
        # We're moving UserProfile to authentication app, but keeping the database table
        # This is a state-only operation to remove it from core's migration state
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name='UserProfile',
                ),
            ],
            # Don't drop the table - it's being managed by authentication app now
            database_operations=[],
        ),
    ]
