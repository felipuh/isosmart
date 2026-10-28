"""
Comando para sincronizar organizaciones desde Admin Apps
python manage.py sync_organizations
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify
from integration.client import admin_apps_client
import logging

logger = logging.getLogger(__name__)

ROLE_MAP = {
    'superadmin': 'org_admin',
    'admin': 'org_admin',
    'org_admin': 'org_admin',
    'iso_manager': 'iso_manager',
    'auditor': 'auditor',
    'user': 'user',
    'viewer': 'viewer',
}


class Command(BaseCommand):
    help = 'Sincroniza organizaciones desde Admin Apps'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar sincronización completa (ignorar caché)',
        )
        parser.add_argument(
            '--org-id',
            type=str,
            help='Sincronizar solo una organización específica (UUID)',
        )
    
    def handle(self, *args, **options):
        from core.models import Organization
        
        force = options['force']
        org_id = options.get('org_id')
        
        self.stdout.write(self.style.NOTICE('Iniciando sincronización con Admin Apps...'))
        
        # Verificar conexión
        health = admin_apps_client.health_check()
        if 'error' in health:
            raise CommandError(f"No se puede conectar a Admin Apps: {health['error']}")
        
        self.stdout.write(self.style.SUCCESS(f"✓ Conectado a Admin Apps ({health.get('service')})"))
        
        if org_id:
            # Sincronizar una organización específica
            self._sync_organization(org_id, force)
        else:
            # Sincronizar todas las organizaciones
            self._sync_all_organizations(force)
        
        self.stdout.write(self.style.SUCCESS('Sincronización completada'))
    
    def _sync_all_organizations(self, force):
        """Sincroniza todas las organizaciones"""
        from core.models import Organization
        
        result = admin_apps_client.get_organizations(use_cache=not force)
        
        if 'error' in result:
            raise CommandError(f"Error obteniendo organizaciones: {result['error']}")
        
        organizations = result.get('organizations', [])
        self.stdout.write(f"Encontradas {len(organizations)} organizaciones en Admin Apps")
        
        created = 0
        updated = 0
        
        for org_data in organizations:
            code = org_data.get('code')
            name = org_data.get('name', '')
            slug_source = code or name
            slug = slugify(slug_source) if slug_source else None
            is_active = org_data.get('is_active', True)
            org, was_created = Organization.objects.update_or_create(
                external_id=org_data['id'],
                defaults={
                    'name': name,
                    'slug': slug or f"org-{org_data['id']}",
                    'is_active': is_active,
                }
            )
            
            if was_created:
                created += 1
                self.stdout.write(f"  + Creada: {org.name}")
            else:
                updated += 1
                self.stdout.write(f"  ~ Actualizada: {org.name}")

            self._sync_organization_users(org_data['id'], force)
        
        self.stdout.write(self.style.SUCCESS(
            f"Resumen: {created} creadas, {updated} actualizadas"
        ))
    
    def _sync_organization(self, org_id, force):
        """Sincroniza una organización específica"""
        from core.models import Organization
        
        result = admin_apps_client.get_organization(org_id, use_cache=not force)
        
        if 'error' in result:
            raise CommandError(f"Error obteniendo organización {org_id}: {result['error']}")
        
        code = result.get('code')
        name = result.get('name', '')
        slug_source = code or name
        slug = slugify(slug_source) if slug_source else None
        is_active = result.get('is_active', True)
        org, created = Organization.objects.update_or_create(
            external_id=result['id'],
            defaults={
                'name': name,
                'slug': slug or f"org-{result['id']}",
                'is_active': is_active,
            }
        )
        
        action = "Creada" if created else "Actualizada"
        self.stdout.write(self.style.SUCCESS(f"{action}: {org.name}"))
        
        # Sincronizar usuarios de la organización
        self._sync_organization_users(org_id, force)
    
    def _sync_organization_users(self, org_id, force):
        """Sincroniza usuarios de una organización"""
        from django.contrib.auth import get_user_model
        from core.models import Organization
        from authentication.models import UserProfile
        
        User = get_user_model()
        
        result = admin_apps_client.get_organization_users(org_id, use_cache=not force)
        
        if 'error' in result:
            self.stdout.write(self.style.WARNING(
                f"Error obteniendo usuarios: {result['error']}"
            ))
            return
        
        users = result.get('users', [])
        self.stdout.write(f"  Sincronizando {len(users)} usuarios...")
        
        try:
            organization = Organization.objects.get(external_id=org_id)
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Organización {org_id} no existe localmente"
            ))
            return
        
        for user_data in users:
            user, user_created = User.objects.update_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_active': True,
                }
            )
            
            if user_created:
                user.set_unusable_password()
                user.save()
            
            mapped_role = ROLE_MAP.get(user_data.get('role', 'user'), 'user')
            profile, profile_created = UserProfile.objects.update_or_create(
                user=user,
                organization=organization,
                defaults={
                    'role': mapped_role,
                    'job_title': user_data.get('job_title', ''),
                    'department': user_data.get('department', ''),
                    'is_active': True,
                }
            )
            
            status = "+" if user_created else "~"
            self.stdout.write(f"    {status} {user.email} ({user_data['role']})")
