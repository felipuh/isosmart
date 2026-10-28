from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_user_must_change_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_history',
            field=models.JSONField(blank=True, default=list),
        ),
    ]