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

INITIAL_ADMIN_PASSWORD = 'Admin@123456'

# Verificar si ya existe un usuario admin
if User.objects.filter(email='admin@isosmart.local').exists():
    print("✅ El usuario admin ya existe")
else:
    # Obtener o crear la organización por defecto
    org, created = Organization.objects.get_or_create(
        id=1,
        defaults={
            'name': 'Organización Demo',
            'slug': 'organizacion-demo',
            'legal_name': 'Organización Demo S.A.',
            'tax_id': '0000000000',
            'email': 'demo@isosmart.local',
            'phone': '0000000000',
            'address': 'Dirección Demo',
            'website': 'https://demo.isosmart.local',
        }
    )
    
    if created:
        print(f"✅ Organización creada: {org.name}")
    else:
        print(f"✅ Organización existente: {org.name}")
    
    # Crear usuario administrador
    user = User.objects.create_user(
        username='admin_isosmart',  # Username requerido por la tabla auth_user
        email='admin@isosmart.local',
        password=INITIAL_ADMIN_PASSWORD,  # ⚠️ Cambiar después del primer login
        first_name='Administrador',
        last_name='Sistema',
        is_active=True,
    )
    
    print(f"✅ Usuario creado: {user.email}")
    
    # Crear perfil de administrador
    profile = UserProfile.objects.create(
        user=user,
        organization=org,
        role='org_admin',
        job_title='Administrador del Sistema',
        is_active=True,
    )
    
    print(f"✅ Perfil creado: {profile.role} en {org.name}")
    
    print("\n" + "="*50)
    print("CREDENCIALES DE ACCESO INICIAL")
    print("="*50)
    print(f"Email: admin@isosmart.local")
    print(f"Password: {INITIAL_ADMIN_PASSWORD}")
    print("="*50)
    print("⚠️  Cambia la contraseña después del primer login!")
    print("="*50)
