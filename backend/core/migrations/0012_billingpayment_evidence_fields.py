from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_billing_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingpayment',
            name='evidence_file',
            field=models.FileField(blank=True, null=True, upload_to='billing/evidence/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='billingpayment',
            name='evidence_uploaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
