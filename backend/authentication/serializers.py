"""
Serializers de Autenticación para ISO Smart
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'last_login', 'date_joined'
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
    organization_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        organization_id = attrs.get('organization_id')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Credenciales inválidas. Verifica tu email y contraseña.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'Esta cuenta ha sido desactivada.',
                    code='authorization'
                )
            
            # Obtener perfil de organización
            profiles = UserProfile.objects.filter(user=user, is_active=True)
            
            if not profiles.exists():
                raise serializers.ValidationError(
                    'No tienes acceso a ninguna organización.',
                    code='authorization'
                )
            
            # Si se especifica organización, verificar acceso
            if organization_id:
                profile = profiles.filter(organization_id=organization_id).first()
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
        return attrs
    
    def create(self, validated_data):
        organization_id = validated_data.pop('organization_id')
        role = validated_data.pop('role')
        validated_data.pop('confirm_password')
        
        user = User.objects.create_user(**validated_data)
        
        # Crear perfil en la organización
        UserProfile.objects.create(
            user=user,
            organization_id=organization_id,
            role=role,
            is_primary=True
        )
        
        return user
