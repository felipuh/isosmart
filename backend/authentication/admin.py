"""
Configuración de Admin Django para modelos de autenticación
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, RefreshTokenBlacklist


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personalizado para el modelo User"""
    
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Información Personal'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Permisos'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Fechas'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para perfiles de usuario"""
    
    list_display = ('user', 'organization', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'organization')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'organization__name')
    raw_id_fields = ('user', 'organization')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('user', 'organization', 'role')}),
        (_('Información Adicional'), {
            'fields': ('job_title', 'department', 'phone', 'avatar', 'theme', 'language')
        }),
        (_('Notificaciones'), {
            'fields': ('notifications_enabled', 'email_notifications')
        }),
        (_('Estado'), {
            'fields': ('is_active',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RefreshTokenBlacklist)
class RefreshTokenBlacklistAdmin(admin.ModelAdmin):
    """Admin para tokens en lista negra"""
    
    list_display = ('user', 'blacklisted_at', 'token_preview', 'token_hash')
    list_filter = ('blacklisted_at',)
    search_fields = ('user__email', 'token', 'token_hash')
    readonly_fields = ('blacklisted_at', 'token', 'token_hash', 'user')
    ordering = ('-blacklisted_at',)
    
    def token_preview(self, obj):
        return obj.token[:50] + '...' if len(obj.token) > 50 else obj.token
    token_preview.short_description = 'Token'
