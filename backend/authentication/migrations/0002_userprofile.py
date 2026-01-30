# Generated manually on 2026-01-29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        ('core', '0003_organization_userprofile_organizationsettings_and_more'),
    ]

    operations = [
        # Note: UserProfile table already exists from core.0003, so we use state_operations
        # to track the model without creating the table
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='UserProfile',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('role', models.CharField(choices=[('org_admin', 'Administrador'), ('iso_manager', 'Responsable SGC'), ('auditor', 'Auditor'), ('user', 'Usuario'), ('viewer', 'Solo Lectura')], default='user', max_length=20)),
                        ('job_title', models.CharField(blank=True, max_length=100)),
                        ('department', models.CharField(blank=True, max_length=100)),
                        ('phone', models.CharField(blank=True, max_length=50)),
                        ('avatar', models.ImageField(blank=True, null=True, upload_to='users/avatars/')),
                        ('theme', models.CharField(choices=[('light', 'Claro'), ('dark', 'Oscuro'), ('system', 'Sistema')], default='light', max_length=10)),
                        ('language', models.CharField(default='es', max_length=10)),
                        ('notifications_enabled', models.BooleanField(default=True)),
                        ('email_notifications', models.BooleanField(default=True)),
                        ('is_active', models.BooleanField(default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='core.organization')),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'user_profiles',
                        'unique_together': {('user', 'organization')},
                    },
                ),
            ],
            # No database operations needed - table already exists
            database_operations=[],
        ),
    ]
