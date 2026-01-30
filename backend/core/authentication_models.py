"""
Modelos de Autenticación para ISO Smart
Sistema multitenancy con roles por organización
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El email es obligatorio'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser debe tener is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Modelo de Usuario personalizado para ISO Smart
    Usa email como identificador principal en lugar de username
    """
    
    username = None  # Removemos username
    email = models.EmailField(_('email'), unique=True)
    first_name = models.CharField(_('nombre'), max_length=150)
    last_name = models.CharField(_('apellido'), max_length=150)
    phone = models.CharField(_('teléfono'), max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Campos de control
    is_active = models.BooleanField(_('activo'), default=True)
    email_verified = models.BooleanField(_('email verificado'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_user_custom'
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name


class UserProfile(models.Model):
    """
    Perfil de usuario con relación a organización y rol
    Un usuario puede pertenecer a múltiples organizaciones con diferentes roles
    """
    
    ROLE_CHOICES = [
        ('org_admin', 'Administrador'),
        ('iso_manager', 'Responsable SGC'),
        ('auditor', 'Auditor'),
        ('user', 'Usuario'),
        ('viewer', 'Solo Lectura'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Cambiado de User a settings.AUTH_USER_MODEL
        on_delete=models.CASCADE, 
        related_name='profiles'
    )
    organization = models.ForeignKey(
        'core.Organization',  # Referencia al modelo existente
        on_delete=models.CASCADE,
        related_name='user_profiles'
    )
    role = models.CharField(
        _('rol'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='user'
    )
    
    # Campos adicionales por organización
    job_title = models.CharField(_('cargo'), max_length=100, blank=True)
    department = models.CharField(_('departamento'), max_length=100, blank=True)
    is_primary = models.BooleanField(
        _('organización principal'),
        default=False,
        help_text=_('Indica si esta es la organización principal del usuario')
    )
    
    # Control
    is_active = models.BooleanField(_('activo en organización'), default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user_profile'
        verbose_name = _('perfil de usuario')
        verbose_name_plural = _('perfiles de usuario')
        unique_together = ['user', 'organization']
        ordering = ['-is_primary', 'organization__name']
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Si es el primer perfil del usuario, hacerlo primario
        if not self.pk and not UserProfile.objects.filter(user=self.user).exists():
            self.is_primary = True
        super().save(*args, **kwargs)
    
    # Métodos de verificación de permisos
    def is_admin(self):
        return self.role == 'org_admin'
    
    def is_manager(self):
        return self.role in ['org_admin', 'iso_manager']
    
    def can_edit(self):
        return self.role in ['org_admin', 'iso_manager', 'user']
    
    def can_view(self):
        return True  # Todos los roles pueden ver


class RefreshTokenBlacklist(models.Model):
    """
    Lista negra de tokens de refresco invalidados
    Útil para logout y revocación de sesiones
    """
    
    token = models.CharField(max_length=500, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Cambiado de User a settings.AUTH_USER_MODEL
        on_delete=models.CASCADE
    )
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'auth_token_blacklist'
        verbose_name = _('token en lista negra')
        verbose_name_plural = _('tokens en lista negra')
    
    def __str__(self):
        return f"Blacklisted token for {self.user.email}"
