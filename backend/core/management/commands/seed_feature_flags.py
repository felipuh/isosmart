from django.core.management.base import BaseCommand, CommandError

from core.models import FeatureFlag, Organization


DEFAULT_FLAGS = {
    'billing_revenue_dashboard': False,
    'onboarding_orchestration_v2': False,
    'alerts_predictive_risk': False,
}


class Command(BaseCommand):
    help = 'Seed default feature flags and optional organization override for IsoSmart.'

    def add_arguments(self, parser):
        parser.add_argument('--org-slug', type=str, help='Organization slug for override.')
        parser.add_argument('--enable-revenue-dashboard', action='store_true', help='Enable billing_revenue_dashboard for organization override.')

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for name, enabled in DEFAULT_FLAGS.items():
            obj, was_created = FeatureFlag.objects.get_or_create(
                name=name,
                organization=None,
                defaults={
                    'scope': FeatureFlag.SCOPE_GLOBAL,
                    'enabled': enabled,
                    'description': f'Default global flag for {name}',
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created global flag: {obj.name}={obj.enabled}'))
            elif obj.enabled != enabled:
                obj.enabled = enabled
                obj.scope = FeatureFlag.SCOPE_GLOBAL
                obj.save(update_fields=['enabled', 'scope', 'updated_at'])
                updated += 1
                self.stdout.write(self.style.WARNING(f'Updated global flag: {obj.name}={obj.enabled}'))

        org_slug = options.get('org_slug')
        if org_slug:
            try:
                organization = Organization.objects.get(slug=org_slug)
            except Organization.DoesNotExist as exc:
                raise CommandError(f'Organization not found for slug={org_slug}') from exc

            org_enabled = bool(options.get('enable_revenue_dashboard'))
            org_flag, was_created = FeatureFlag.objects.get_or_create(
                name='billing_revenue_dashboard',
                organization=organization,
                defaults={
                    'scope': FeatureFlag.SCOPE_ORGANIZATION,
                    'enabled': org_enabled,
                    'description': 'Organization override for revenue dashboard rollout',
                },
            )
            if not was_created and org_flag.enabled != org_enabled:
                org_flag.enabled = org_enabled
                org_flag.scope = FeatureFlag.SCOPE_ORGANIZATION
                org_flag.save(update_fields=['enabled', 'scope', 'updated_at'])
                updated += 1
            elif was_created:
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Org override set: {organization.slug} billing_revenue_dashboard={org_flag.enabled}'
                )
            )

        self.stdout.write(self.style.SUCCESS(f'Done. created={created} updated={updated}'))
