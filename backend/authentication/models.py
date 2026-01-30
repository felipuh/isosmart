"""
Modelos de Autenticación para ISO Smart
Sistema multitenancy con roles por organización
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
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
        db_table = 'auth_user'
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
        User, 
        on_delete=models.CASCADE, 
        related_name='profiles'
    )
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='members'  # Changed from 'user_profiles' to match core.0003
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user'
    )
    
    # Fields from core.0003 migration
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)
    theme = models.CharField(
        max_length=10,
        choices=[('light', 'Claro'), ('dark', 'Oscuro'), ('system', 'Sistema')],
        default='light'
    )
    language = models.CharField(max_length=10, default='es')
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'  # Matches core.0003
        unique_together = (('user', 'organization'),)  # Must be tuple or list
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() if self.user else ""

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
        User,
        on_delete=models.CASCADE,
        related_name='blacklisted_tokens',
        null=True
    )
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'refresh_token_blacklist'
        ordering = ['-blacklisted_at']
    
    def __str__(self):
        return f"Blacklisted token for {self.user.email if self.user else 'unknown'} at {self.blacklisted_at}"

    def __str__(self):
        return f"Blacklisted token for {self.user.email}"
