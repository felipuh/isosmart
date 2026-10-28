from django.db import migrations, models
import django.db.models.deletion


def _get_fallback_organization(Organization):
    fallback = Organization.objects.order_by('id').first()
    if fallback:
        return fallback

    base_slug = 'legacy-backfill'
    slug = base_slug
    suffix = 1
    while Organization.objects.filter(slug=slug).exists():
        suffix += 1
        slug = f'{base_slug}-{suffix}'

    return Organization.objects.create(
        name='Legacy Backfill Organization',
        slug=slug,
        email='',
    )


def _build_user_org_map(UserProfile):
    user_org_map = {}

    for profile in UserProfile.objects.filter(is_active=True).order_by('id').values('user_id', 'organization_id'):
        user_org_map.setdefault(profile['user_id'], profile['organization_id'])

    for profile in UserProfile.objects.order_by('id').values('user_id', 'organization_id'):
        user_org_map.setdefault(profile['user_id'], profile['organization_id'])

    return user_org_map


def backfill_organization_fields(apps, schema_editor):
    Organization = apps.get_model('core', 'Organization')
    ContextAnalysis = apps.get_model('core', 'ContextAnalysis')
    Document = apps.get_model('core', 'Document')
    StakeholderProfile = apps.get_model('core', 'StakeholderProfile')
    ProcessMap = apps.get_model('core', 'ProcessMap')
    RiskMatrix = apps.get_model('core', 'RiskMatrix')
    QualityObjective = apps.get_model('core', 'QualityObjective')
    UserProfile = apps.get_model('authentication', 'UserProfile')

    fallback_org = _get_fallback_organization(Organization)
    fallback_org_id = fallback_org.id

    user_org_map = _build_user_org_map(UserProfile)

    # Give base org to entities that had no resolvable ownership before multitenancy.
    StakeholderProfile.objects.filter(organization_id__isnull=True).update(organization_id=fallback_org_id)
    ProcessMap.objects.filter(organization_id__isnull=True).update(organization_id=fallback_org_id)

    stakeholder_org_by_id = dict(
        StakeholderProfile.objects.values_list('id', 'organization_id')
    )
    process_org_by_code = {
        process_code: org_id
        for process_code, org_id in ProcessMap.objects.exclude(process_id__isnull=True).values_list('process_id', 'organization_id')
        if process_code
    }

    for item in ContextAnalysis.objects.filter(organization_id__isnull=True).only('id', 'created_by_id'):
        item.organization_id = user_org_map.get(item.created_by_id, fallback_org_id)
        item.save(update_fields=['organization'])

    for item in Document.objects.filter(organization_id__isnull=True).only('id', 'uploaded_by_id'):
        item.organization_id = user_org_map.get(item.uploaded_by_id, fallback_org_id)
        item.save(update_fields=['organization'])

    for item in QualityObjective.objects.filter(organization_id__isnull=True).only('id', 'process_id'):
        org_id = process_org_by_code.get(item.process_id) if item.process_id else None
        item.organization_id = org_id or fallback_org_id
        item.save(update_fields=['organization'])

    for item in RiskMatrix.objects.filter(organization_id__isnull=True).only('id', 'source_module', 'source_id', 'process_id'):
        org_id = None

        if item.source_module == 'SIE' and item.source_id:
            org_id = stakeholder_org_by_id.get(item.source_id)

        if not org_id and item.process_id:
            org_id = process_org_by_code.get(item.process_id)

        item.organization_id = org_id or fallback_org_id
        item.save(update_fields=['organization'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_contextanalysis_organization_document_organization_and_more'),
        ('authentication', '0004_refresh_token_hash'),
    ]

    operations = [
        migrations.RunPython(backfill_organization_fields, noop_reverse),
        migrations.AlterField(
            model_name='contextanalysis',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='context_analyses', to='core.organization'),
        ),
        migrations.AlterField(
            model_name='document',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='core.organization'),
        ),
        migrations.AlterField(
            model_name='processmap',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='process_maps', to='core.organization'),
        ),
        migrations.AlterField(
            model_name='qualityobjective',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quality_objectives', to='core.organization'),
        ),
        migrations.AlterField(
            model_name='riskmatrix',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_matrices', to='core.organization'),
        ),
        migrations.AlterField(
            model_name='stakeholderprofile',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stakeholders', to='core.organization'),
        ),
    ]
