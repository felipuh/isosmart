import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Organization
from integration.client import admin_apps_client


class Command(BaseCommand):
    help = 'Smoke check AdminApps product entitlement for ISO Smart.'

    def add_arguments(self, parser):
        parser.add_argument('--organization-slug', default='smart3ai')
        parser.add_argument('--organization-id', type=int, default=None)
        parser.add_argument(
            '--no-fallback',
            action='store_true',
            help='Fail if AdminApps cannot validate access directly. Required for target/staging/production smoke.',
        )

    def handle(self, *args, **options):
        fallback_allowed = not options['no_fallback']
        if options['organization_id']:
            organization = Organization.objects.filter(id=options['organization_id']).first()
        else:
            organization = Organization.objects.filter(slug=options['organization_slug']).first()

        if not organization:
            raise CommandError('Organization not found for ISO Smart AdminApps smoke.')

        health = admin_apps_client.health_check()
        product_access = admin_apps_client.validate_product_access(
            organization.id,
            getattr(settings, 'ISO_SMART_PRODUCT_CODE', 'ISO_SMART'),
            use_cache=False,
            allow_local_fallback=fallback_allowed,
        )

        adminapps_available = 'error' not in health
        product_enabled = bool(product_access.get('allowed'))
        fallback_source = bool(product_access.get('fallback'))

        self.stdout.write(f'organization={organization.id} slug={organization.slug}')
        self.stdout.write(f'adminapps_available={adminapps_available}')
        self.stdout.write(f'fallback_allowed={fallback_allowed}')
        self.stdout.write(f'product_access_source={product_access.get("source", "adminapps")}')
        self.stdout.write(f'iso_smart_access_enabled={product_enabled}')
        self.stdout.write(f'iso_smart_access_reason={product_access.get("reason", "unknown")}')
        self.stdout.write(f'billing_status={product_access.get("billing_status", "unknown")}')

        if options['no_fallback'] and fallback_source:
            raise CommandError('AdminApps fallback was used while --no-fallback is required.')
        if options['no_fallback'] and not adminapps_available:
            raise CommandError('AdminApps is not available while --no-fallback is required.')

        if fallback_source:
            self.stdout.write(
                self.style.WARNING(
                    'AdminApps fallback local explicito activo: solo demo/test y no sustituye billing real.'
                )
            )

        if not product_enabled:
            raise CommandError('ISO_SMART entitlement is not enabled for this organization.')

        self.stdout.write(self.style.SUCCESS('ISO Smart AdminApps smoke passed.'))