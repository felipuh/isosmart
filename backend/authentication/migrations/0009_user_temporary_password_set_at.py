from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0008_user_password_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='temporary_password_set_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
