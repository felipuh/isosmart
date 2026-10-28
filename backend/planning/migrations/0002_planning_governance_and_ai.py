from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('planning', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskopportunity',
            name='ai_sources',
            field=models.JSONField(blank=True, default=list, help_text='Fuentes de datos y evidencias usadas para justificar el riesgo/oportunidad'),
        ),
        migrations.AddField(
            model_name='riskopportunity',
            name='approval_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='riskopportunity',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='riskopportunity',
            name='proposed_actions',
            field=models.JSONField(blank=True, default=list, help_text='Acciones propuestas por reglas/IA'),
        ),
        migrations.AddField(
            model_name='riskopportunity',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planning_risks_approved', to=settings.AUTH_USER_MODEL, verbose_name='Aprobado por'),
        ),
        migrations.AlterField(
            model_name='riskopportunity',
            name='category',
            field=models.CharField(choices=[('strategic', 'Estratégico'), ('operational', 'Operacional'), ('financial', 'Financiero'), ('climatic', 'Climático'), ('cyber', 'Ciber'), ('compliance', 'Cumplimiento'), ('reputation', 'Reputacional'), ('technology', 'Tecnológico'), ('market', 'Mercado'), ('other', 'Otro')], max_length=50),
        ),
        migrations.AddField(
            model_name='qualityobjective',
            name='ai_recommendations',
            field=models.JSONField(blank=True, default=dict, help_text='Sugerencias IA para formular, medir o corregir el objetivo'),
        ),
        migrations.AddField(
            model_name='qualityobjective',
            name='approval_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='qualityobjective',
            name='forecast_summary',
            field=models.JSONField(blank=True, default=dict, help_text='Predicción simple de cumplimiento o atraso'),
        ),
        migrations.AddField(
            model_name='qualityobjective',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planning_objectives_approved', to=settings.AUTH_USER_MODEL, verbose_name='Aprobado por'),
        ),
        migrations.AddField(
            model_name='changecontrol',
            name='affected_versions',
            field=models.JSONField(blank=True, default=list, help_text='Versiones, documentos o procesos afectados por el cambio'),
        ),
        migrations.AddField(
            model_name='changecontrol',
            name='impact_estimated',
            field=models.JSONField(blank=True, default=dict, help_text='Impacto estimado estructurado antes de implementar el cambio'),
        ),
        migrations.AddField(
            model_name='changecontrol',
            name='implementation_plan',
            field=models.JSONField(blank=True, default=list, help_text='Cronograma o plan generado manualmente o por IA'),
        ),
        migrations.CreateModel(
            name='PlanningAIGovernanceLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_id', models.IntegerField(db_index=True)),
                ('operation', models.CharField(max_length=100)),
                ('model_version', models.CharField(default='unknown', max_length=100)),
                ('prompt_template', models.CharField(max_length=200)),
                ('prompt_hash', models.CharField(max_length=64)),
                ('response_summary', models.TextField()),
                ('ai_recommendation', models.JSONField(blank=True, default=dict)),
                ('data_sources', models.JSONField(blank=True, default=list)),
                ('privacy_check_passed', models.BooleanField(default=True)),
                ('human_decision', models.CharField(choices=[('pending', 'Pendiente'), ('accepted', 'Aceptado'), ('rejected', 'Rechazado'), ('modified', 'Modificado')], default='pending', max_length=20)),
                ('decided_at', models.DateTimeField(blank=True, null=True)),
                ('human_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('decided_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planning_ai_decisions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Log de Gobernanza IA de Planificacion',
                'verbose_name_plural': 'Logs de Gobernanza IA de Planificacion',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PlanningApprovalRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_id', models.IntegerField(db_index=True)),
                ('workflow_type', models.CharField(choices=[('risk_approval', 'Aprobación de Riesgo'), ('objective_approval', 'Aprobación de Objetivo'), ('change_approval', 'Aprobación de Cambio'), ('change_rejection', 'Rechazo de Cambio')], max_length=30)),
                ('reference_model', models.CharField(max_length=100)),
                ('reference_id', models.IntegerField()),
                ('title', models.CharField(max_length=300)),
                ('approved_at', models.DateTimeField(auto_now_add=True)),
                ('digital_signature', models.CharField(max_length=64)),
                ('content_snapshot', models.JSONField()),
                ('notes', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='planning_approval_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Registro de Aprobacion de Planificacion',
                'verbose_name_plural': 'Registros de Aprobacion de Planificacion',
                'ordering': ['-approved_at'],
            },
        ),
        migrations.CreateModel(
            name='PlanningVersionRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_id', models.IntegerField(db_index=True)),
                ('entity_type', models.CharField(choices=[('risk_opportunity', 'Riesgo/Oportunidad'), ('quality_objective', 'Objetivo de Calidad'), ('change_control', 'Control de Cambio')], max_length=30)),
                ('entity_id', models.IntegerField()),
                ('version_number', models.IntegerField()),
                ('snapshot', models.JSONField()),
                ('change_reason', models.CharField(blank=True, max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planning_version_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Version de Planificacion',
                'verbose_name_plural': 'Versiones de Planificacion',
                'ordering': ['-created_at'],
                'unique_together': {('entity_type', 'entity_id', 'version_number')},
            },
        ),
        migrations.AddIndex(
            model_name='planningaigovernancelog',
            index=models.Index(fields=['organization_id', 'operation'], name='planning_pl_organiz_95d70d_idx'),
        ),
        migrations.AddIndex(
            model_name='planningaigovernancelog',
            index=models.Index(fields=['human_decision'], name='planning_pl_human_d_5ca6c2_idx'),
        ),
        migrations.AddIndex(
            model_name='planningapprovalrecord',
            index=models.Index(fields=['organization_id', 'workflow_type'], name='planning_pl_organiz_a4bbdd_idx'),
        ),
        migrations.AddIndex(
            model_name='planningapprovalrecord',
            index=models.Index(fields=['reference_model', 'reference_id'], name='planning_pl_referen_24cb51_idx'),
        ),
        migrations.AddIndex(
            model_name='planningversionrecord',
            index=models.Index(fields=['organization_id', 'entity_type'], name='planning_pl_organiz_4d7304_idx'),
        ),
        migrations.AddIndex(
            model_name='planningversionrecord',
            index=models.Index(fields=['entity_type', 'entity_id'], name='planning_pl_entity__26470f_idx'),
        ),
    ]