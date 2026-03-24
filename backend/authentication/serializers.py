"""
Serializers de Autenticación para ISO Smart
"""

from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import PasswordResetToken, User, UserProfile
from core.models import Organization


PASSWORD_REUSE_REASON_CODE = 'PASSWORD_REUSE_RECENT'
TEMP_PASSWORD_EXPIRED_REASON_CODE = 'TEMP_PASSWORD_EXPIRED'


def _is_password_reused(user, raw_password):
    if check_password(raw_password, user.password):
        return True

    for previous_hash in (user.password_history or []):
        if previous_hash and check_password(raw_password, previous_hash):
            return True
    return False


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'must_change_password', 'last_login', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de usuario en una organización"""
    
    user = UserSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'organization', 'organization_name',
            'role', 'role_display', 'job_title', 'department',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoginSerializer(serializers.Serializer):
    """Serializer para el login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    organization_id = serializers.CharField(required=False, allow_null=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        organization_id = attrs.get('organization_id')
        organization = None

        _INVALID_CREDENTIALS_MSG = 'Credenciales inválidas o cuenta temporalmente bloqueada.'
        max_attempts = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
        lockout_minutes = getattr(settings, 'LOGIN_LOCKOUT_MINUTES', 15)

        if email and password:
            # Look up user for lockout check before calling authenticate()
            try:
                candidate = User.objects.get(email=email)
            except User.DoesNotExist:
                candidate = None

            if candidate and candidate.is_locked():
                raise serializers.ValidationError(_INVALID_CREDENTIALS_MSG, code='account_locked')

            if organization_id:
                try:
                    organization = Organization.objects.get(id=int(organization_id))
                except (ValueError, Organization.DoesNotExist):
                    organization = Organization.objects.filter(external_id=organization_id).first()

            external_org_id = organization.external_id if organization else organization_id

            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password,
                organization_id=external_org_id
            )

            if not user:
                if candidate:
                    candidate.record_failed_login(
                        max_attempts=max_attempts, lockout_minutes=lockout_minutes
                    )
                raise serializers.ValidationError(_INVALID_CREDENTIALS_MSG, code='authorization')

            if not user.is_active:
                raise serializers.ValidationError(
                    'Esta cuenta ha sido desactivada.',
                    code='authorization'
                )

            # Successful authentication — clear any previous failures
            user.reset_login_attempts()

            temporary_expiry = user.get_temporary_password_expiry()
            if temporary_expiry and timezone.now() >= temporary_expiry:
                raise serializers.ValidationError(
                    {
                        'detail': 'Tu contraseña temporal ha expirado. Solicita un restablecimiento con un administrador.',
                        'reason_code': TEMP_PASSWORD_EXPIRED_REASON_CODE,
                    },
                    code='authorization',
                )

            temp_password_warning = None
            if temporary_expiry:
                warning_days = max(0, int(getattr(settings, 'TEMP_PASSWORD_WARNING_DAYS', 2)))
                seconds_left = (temporary_expiry - timezone.now()).total_seconds()
                if seconds_left > 0:
                    days_left = int((seconds_left - 1) // 86400) + 1
                    if days_left <= warning_days:
                        temp_password_warning = {
                            'reason_code': 'TEMP_PASSWORD_EXPIRING',
                            'days_left': days_left,
                            'expires_at': temporary_expiry,
                        }
            
            # Obtener perfil de organización
            profiles = UserProfile.objects.filter(user=user, is_active=True)
            
            if not profiles.exists():
                raise serializers.ValidationError(
                    'No tienes acceso a ninguna organización.',
                    code='authorization'
                )
            
            # Si se especifica organización, verificar acceso
            if organization_id:
                if not organization:
                    organization = Organization.objects.filter(external_id=organization_id).first()

                if organization:
                    profile = profiles.filter(organization_id=organization.id).first()
                else:
                    profile = None

                if not profile:
                    raise serializers.ValidationError(
                        'No tienes acceso a esta organización.',
                        code='authorization'
                    )
            else:
                # Usar primera organización disponible (ordenada por ID)
                profile = profiles.first()
            
            attrs['user'] = user
            attrs['profile'] = profile
            attrs['temp_password_warning'] = temp_password_warning
            
        else:
            raise serializers.ValidationError(
                'Debes proporcionar email y contraseña.',
                code='authorization'
            )
        
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    """Serializer para la respuesta de login con tokens"""
    
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    profile = UserProfileSerializer()
    organizations = serializers.ListField(child=serializers.DictField())


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer para refresh de token"""
    
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """Serializer para logout"""
    
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value
    
    def validate_new_password(self, value):
        validate_password(value)
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })
        return attrs


class SwitchOrganizationSerializer(serializers.Serializer):
    """Serializer para cambiar de organización activa"""
    
    organization_id = serializers.IntegerField()
    
    def validate_organization_id(self, value):
        user = self.context['request'].user
        profile = UserProfile.objects.filter(
            user=user,
            organization_id=value,
            is_active=True
        ).first()
        
        if not profile:
            raise serializers.ValidationError(
                'No tienes acceso a esta organización.'
            )
        
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuarios (usado por admins)"""
    
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    organization_id = serializers.IntegerField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'password', 'confirm_password', 'organization_id', 'role'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })

        existing_user = User.objects.filter(email=attrs['email']).first()
        if existing_user:
            if _is_password_reused(existing_user, attrs['password']):
                raise serializers.ValidationError({
                    'detail': 'No puedes reutilizar una contraseña reciente en esta alta/invitación.',
                    'reason_code': PASSWORD_REUSE_REASON_CODE,
                })
            raise serializers.ValidationError({'email': 'Este correo ya está registrado.'})

        return attrs
    
    def create(self, validated_data):
        organization_id = validated_data.pop('organization_id')
        role = validated_data.pop('role')
        phone = validated_data.pop('phone', '')
        validated_data.pop('confirm_password')
        
        user = User.objects.create_user(**validated_data)
        
        # Crear perfil en la organización
        UserProfile.objects.create(
            user=user,
            organization_id=organization_id,
            role=role,
            phone=phone,
        )

        # Enforce first-login password rotation for new tenant users.
        user.mark_temporary_password()
        user.save(update_fields=['must_change_password', 'temporary_password_set_at'])
        
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer para solicitar recuperacion de contrasena."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar nueva contrasena mediante token."""

    selector = serializers.CharField()
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })

        selector = attrs['selector'].strip()
        raw_token = attrs['token'].strip()
        reset_token = PasswordResetToken.objects.filter(selector=selector).select_related('user').first()

        if not reset_token or not reset_token.is_available() or not reset_token.matches(raw_token):
            raise serializers.ValidationError({
                'token': 'El enlace de recuperación es inválido o ha expirado.'
            })

        attrs['reset_token'] = reset_token
        return attrs
