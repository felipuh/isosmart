"""
Management command to activate (or deactivate) a feature flag for a specific organization.

Usage:
  python manage.py activate_feature_flag --flag billing_revenue_dashboard --org-id <uuid> --enable
  python manage.py activate_feature_flag --flag billing_revenue_dashboard --org-id <uuid> --disable
"""
from django.core.management.base import BaseCommand, CommandError
from core.models import FeatureFlag, Organization


class Command(BaseCommand):
    help = 'Activate or deactivate a feature flag for a specific organization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flag',
            type=str,
            required=True,
            help='Feature flag name (e.g., billing_revenue_dashboard)'
        )
        parser.add_argument(
            '--org-id',
            type=str,
            required=True,
            help='Organization UUID'
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Enable the flag for this organization'
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Disable the flag for this organization'
        )

    def handle(self, *args, **options):
        flag_name = options['flag']
        org_id = options['org_id']
        
        if not options['enable'] and not options['disable']:
            raise CommandError('Specify either --enable or --disable')
        
        if options['enable'] and options['disable']:
            raise CommandError('Cannot specify both --enable and --disable')
        
        # Find organization
        try:
            org = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization with id "{org_id}" not found')
        
        # Create or update org-specific flag
        enabled = options['enable']
        flag, created = FeatureFlag.objects.get_or_create(
            name=flag_name,
            organization=org,
            defaults={'enabled': enabled, 'scope': 'organization'}
        )
        
        if not created:
            flag.enabled = enabled
            flag.save()
            action = 'Updated'
        else:
            action = 'Created'
        
        status = 'ENABLED' if enabled else 'DISABLED'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} org-specific flag: {org.name} → {flag_name}={status}'
            )
        )
        
        # Show current resolution
        resolved = FeatureFlag.objects.resolve_all(organization=org)
        self.stdout.write(
            f'\nFlag resolution for {org.name}:'
        )
        self.stdout.write(f'  {flag_name}: {resolved.get(flag_name, "NOT SET")}')
