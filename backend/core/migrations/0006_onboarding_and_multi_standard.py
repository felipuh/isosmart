from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_organization_external_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsettings',
            name='enabled_standards',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='organizationsettings',
            name='onboarding_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='organizationsettings',
            name='onboarding_completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='organizationsettings',
            name='onboarding_completed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_onboardings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='isoclauseconfig',
            name='standard_code',
            field=models.CharField(choices=[('ISO9001_2015', 'ISO 9001:2015'), ('ISO42001_2023', 'ISO/IEC 42001:2023'), ('ISO27001_2022', 'ISO/IEC 27001:2022'), ('ISO14001_2015', 'ISO 14001:2015'), ('ISO45001_2018', 'ISO 45001:2018')], default='ISO9001_2015', max_length=20),
        ),
        migrations.AlterUniqueTogether(
            name='isoclauseconfig',
            unique_together={('organization', 'standard_code', 'clause_number')},
        ),
    ]
