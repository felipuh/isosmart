# Generated manually on 2026-01-29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # User model: auth_user table already exists from Django's default auth
        # We just track the state without creating the table
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='User',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('password', models.CharField(max_length=128, verbose_name='password')),
                        ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                        ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                        ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                        ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                        ('email', models.EmailField(max_length=254, unique=True, verbose_name='email')),
                        ('first_name', models.CharField(max_length=150, verbose_name='nombre')),
                        ('last_name', models.CharField(max_length=150, verbose_name='apellido')),
                        ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='teléfono')),
                        ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                        ('is_active', models.BooleanField(default=True, verbose_name='activo')),
                        ('email_verified', models.BooleanField(default=False, verbose_name='email verificado')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('last_login_ip', models.GenericIPAddressField(blank=True, null=True)),
                        ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                        ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                    ],
                    options={
                        'db_table': 'auth_user',
                        'verbose_name': 'usuario',
                        'verbose_name_plural': 'usuarios',
                    },
                ),
            ],
            # Table auth_user already exists - don't create it
            database_operations=[],
        ),
        migrations.CreateModel(
            name='RefreshTokenBlacklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=500, unique=True)),
                ('blacklisted_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='blacklisted_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'refresh_token_blacklist',
                'ordering': ['-blacklisted_at'],
            },
        ),
    ]
