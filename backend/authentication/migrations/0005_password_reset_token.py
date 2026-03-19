from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_refresh_token_hash'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('selector', models.CharField(db_index=True, max_length=32, unique=True)),
                ('token_hash', models.CharField(max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'password_reset_tokens',
                'ordering': ['-requested_at'],
            },
        ),
    ]