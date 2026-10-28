from django.db import migrations, models
import hashlib


def populate_token_hash(apps, schema_editor):
    RefreshTokenBlacklist = apps.get_model('authentication', 'RefreshTokenBlacklist')
    for entry in RefreshTokenBlacklist.objects.all().only('id', 'token', 'token_hash'):
        token = entry.token or ''
        entry.token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        entry.save(update_fields=['token_hash'])


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_alter_user_first_name_alter_user_is_active_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refreshtokenblacklist',
            name='token',
            field=models.TextField(),
        ),
        migrations.AddField(
            model_name='refreshtokenblacklist',
            name='token_hash',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.RunPython(populate_token_hash, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='refreshtokenblacklist',
            name='token_hash',
            field=models.CharField(max_length=64, unique=True),
        ),
    ]
