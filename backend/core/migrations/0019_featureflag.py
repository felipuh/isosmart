from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_externalcontextsignal_environmentalriskalert_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeatureFlag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('scope', models.CharField(
                    choices=[('global', 'Global'), ('organization', 'Por Organización')],
                    default='global',
                    max_length=20,
                )),
                ('organization', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='feature_flags',
                    to='core.organization',
                )),
                ('enabled', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Feature Flag',
                'verbose_name_plural': 'Feature Flags',
                'db_table': 'feature_flags',
                'unique_together': {('name', 'organization')},
            },
        ),
    ]
