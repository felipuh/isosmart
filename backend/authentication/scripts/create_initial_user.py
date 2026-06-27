"""
Script para crear usuario administrador inicial en ISO Smart
Ejecutar después de las migraciones

Uso:
    cd /home/aplicacion/projects/isosmart/backend
    source venv_ai/bin/activate
    python manage.py shell < authentication/scripts/create_initial_user.py
"""

from authentication.models import User, UserProfile
from core.models import Organization

INITIAL_ADMIN_EMAIL = 'admin@isosmart.local'
INITIAL_ADMIN_PASSWORD = 'Admin@123456'


org = Organization.objects.filter(slug='smart3ai', is_active=True).first()
if not org:
    org, created = Organization.objects.get_or_create(
        slug='smart3ai',
        defaults={
            'name': 'Smart3AI',
            'legal_name': 'Smart3AI',
            'tax_id': '0000000000',
            'email': 'felipe@smart3ai.com',
            'phone': '0000000000',
            'address': 'Direccion Smart3AI',
            'website': 'https://smart3ai.local',
            'is_active': True,
        }
    )
else:
    created = False

if created:
    print(f"Organizacion creada: {org.name}")
else:
    print(f"Organizacion existente: {org.name}")

user, user_created = User.objects.get_or_create(
    email=INITIAL_ADMIN_EMAIL,
    defaults={
        'username': 'admin_isosmart',
        'first_name': 'Administrador',
        'last_name': 'Sistema',
        'is_active': True,
        'is_staff': True,
        'is_superuser': True,
    },
)

user.username = user.username or 'admin_isosmart'
user.first_name = user.first_name or 'Administrador'
user.last_name = user.last_name or 'Sistema'
user.is_active = True
user.is_staff = True
user.is_superuser = True
user.set_password(INITIAL_ADMIN_PASSWORD)
user.save()

if user_created:
    print(f"Usuario creado: {user.email}")
else:
    print(f"Usuario actualizado: {user.email}")

profile, profile_created = UserProfile.objects.update_or_create(
    user=user,
    organization=org,
    defaults={
        'role': 'org_admin',
        'job_title': 'Administrador del Sistema',
        'is_active': True,
    },
)

if profile_created:
    print(f"Perfil creado: {profile.role} en {org.name}")
else:
    print(f"Perfil actualizado: {profile.role} en {org.name}")

print("\n" + "=" * 50)
print("CREDENCIALES DE ACCESO INICIAL")
print("=" * 50)
print(f"Email: {INITIAL_ADMIN_EMAIL}")
print(f"Password: {INITIAL_ADMIN_PASSWORD}")
print("=" * 50)
print("Cambia la contrasena despues del primer login.")
print("=" * 50)
