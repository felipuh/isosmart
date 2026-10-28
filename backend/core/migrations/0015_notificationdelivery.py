from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_backfill_and_enforce_organization_not_null'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('billing_payment_registered', 'Pago registrado'), ('billing_payment_confirmed', 'Pago confirmado'), ('billing_payment_rejected', 'Pago rechazado'), ('billing_status_changed', 'Cambio de estado de facturacion'), ('billing_due_reminder', 'Recordatorio de cobro'), ('risk_critical', 'Riesgo critico'), ('risk_high', 'Riesgo alto'), ('objective_deadline', 'Vencimiento de objetivo o accion'), ('stakeholder_change', 'Cambio de stakeholder')], max_length=50)),
                ('channel', models.CharField(choices=[('email', 'Email')], default='email', max_length=20)),
                ('event_key', models.CharField(max_length=255, unique=True)),
                ('recipients', models.JSONField(blank=True, default=list)),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('sent', 'Enviada'), ('failed', 'Fallida'), ('skipped', 'Omitida')], default='pending', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_deliveries', to='core.organization')),
            ],
            options={
                'db_table': 'notification_deliveries',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notificationdelivery',
            index=models.Index(fields=['organization', 'event_type'], name='notificatio_organiz_6e1f3f_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationdelivery',
            index=models.Index(fields=['status', '-created_at'], name='notificatio_status_8f275b_idx'),
        ),
    ]