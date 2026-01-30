"""
Views de Autenticación para ISO Smart
"""

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from django.conf import settings

from .models import User, UserProfile, RefreshTokenBlacklist
from .serializers import (
    LoginSerializer,
    TokenResponseSerializer,
    RefreshTokenSerializer,
    LogoutSerializer,
    UserSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    SwitchOrganizationSerializer,
    UserRegistrationSerializer,
)
from .permissions import IsOrgAdmin


class LoginView(APIView):
    """
    Vista de Login
    POST /api/auth/login/
    
    Retorna tokens JWT y datos del usuario
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        profile = serializer.validated_data['profile']
        
        # Generar tokens
        refresh = RefreshToken.for_user(user)
        
        # Agregar claims personalizados al token
        refresh['organization_id'] = profile.organization_id
        refresh['role'] = profile.role
        refresh['profile_id'] = profile.id
        
        access = refresh.access_token
        access['organization_id'] = profile.organization_id
        access['role'] = profile.role
        access['profile_id'] = profile.id
        
        # Actualizar último login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Obtener todas las organizaciones del usuario
        all_profiles = UserProfile.objects.filter(
            user=user, is_active=True
        ).select_related('organization')
        
        organizations = [
            {
                'id': p.organization.id,
                'name': p.organization.name,
                'role': p.role,
                'role_display': p.get_role_display(),
                'is_current': p.id == profile.id
            }
            for p in all_profiles
        ]
        
        response_data = {
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data,
            'organizations': organizations,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Vista de Logout
    POST /api/auth/logout/
    
    Invalida el refresh token
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            
            # Agregar a lista negra
            RefreshTokenBlacklist.objects.create(
                token=str(token),
                user=request.user,
                expires_at=timezone.now() + settings.SIMPLE_JWT.get(
                    'REFRESH_TOKEN_LIFETIME',
                    timezone.timedelta(days=7)
                )
            )
            
            token.blacklist()
            
        except TokenError:
            pass  # Token ya expirado o inválido, ignorar
        
        return Response(
            {'detail': 'Sesión cerrada exitosamente.'},
            status=status.HTTP_200_OK
        )


class RefreshTokenView(APIView):
    """
    Vista para refrescar tokens
    POST /api/auth/refresh/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
            
            # Verificar que no esté en lista negra
            if RefreshTokenBlacklist.objects.filter(token=str(refresh)).exists():
                return Response(
                    {'detail': 'Token inválido o expirado.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generar nuevo access token
            access = refresh.access_token
            
            response_data = {
                'access': str(access),
            }
            
            # Rotar refresh token si está configurado
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                refresh.set_jti()
                refresh.set_exp()
                response_data['refresh'] = str(refresh)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response(
                {'detail': 'Token inválido o expirado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class MeView(APIView):
    """
    Vista para obtener datos del usuario actual
    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Obtener perfil activo (del token o primario)
        organization_id = getattr(request, 'organization_id', None)
        
        if organization_id:
            profile = UserProfile.objects.filter(
                user=user,
                organization_id=organization_id,
                is_active=True
            ).select_related('organization').first()
        else:
            profile = UserProfile.objects.filter(
                user=user,
                is_active=True
            ).order_by('-is_primary').select_related('organization').first()
        
        # Obtener todas las organizaciones
        all_profiles = UserProfile.objects.filter(
            user=user, is_active=True
        ).select_related('organization')
        
        organizations = [
            {
                'id': p.organization.id,
                'name': p.organization.name,
                'role': p.role,
                'role_display': p.get_role_display(),
                'is_current': profile and p.id == profile.id
            }
            for p in all_profiles
        ]
        
        response_data = {
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data if profile else None,
            'organizations': organizations,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class SwitchOrganizationView(APIView):
    """
    Vista para cambiar de organización activa
    POST /api/auth/switch-organization/
    
    Retorna nuevos tokens con la organización seleccionada
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SwitchOrganizationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        organization_id = serializer.validated_data['organization_id']
        user = request.user
        
        profile = UserProfile.objects.filter(
            user=user,
            organization_id=organization_id,
            is_active=True
        ).select_related('organization').first()
        
        # Generar nuevos tokens
        refresh = RefreshToken.for_user(user)
        refresh['organization_id'] = profile.organization_id
        refresh['role'] = profile.role
        refresh['profile_id'] = profile.id
        
        access = refresh.access_token
        access['organization_id'] = profile.organization_id
        access['role'] = profile.role
        access['profile_id'] = profile.id
        
        # Obtener todas las organizaciones
        all_profiles = UserProfile.objects.filter(
            user=user, is_active=True
        ).select_related('organization')
        
        organizations = [
            {
                'id': p.organization.id,
                'name': p.organization.name,
                'role': p.role,
                'role_display': p.get_role_display(),
                'is_current': p.id == profile.id
            }
            for p in all_profiles
        ]
        
        response_data = {
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data,
            'organizations': organizations,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    Vista para cambiar contraseña
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            {'detail': 'Contraseña actualizada exitosamente.'},
            status=status.HTTP_200_OK
        )


class UserListView(generics.ListCreateAPIView):
    """
    Vista para listar y crear usuarios de la organización
    GET/POST /api/auth/users/
    
    Solo para org_admin
    """
    permission_classes = [IsAuthenticated, IsOrgAdmin]
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        organization_id = getattr(self.request, 'organization_id', None)
        if organization_id:
            return UserProfile.objects.filter(
                organization_id=organization_id
            ).select_related('user', 'organization')
        return UserProfile.objects.none()
    
    def create(self, request, *args, **kwargs):
        # Usar serializer de registro
        data = request.data.copy()
        data['organization_id'] = getattr(request, 'organization_id', None)
        
        serializer = UserRegistrationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Obtener el perfil creado
        profile = UserProfile.objects.get(user=user)
        
        return Response(
            UserProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para ver/editar/eliminar usuario de la organización
    GET/PUT/PATCH/DELETE /api/auth/users/<id>/
    
    Solo para org_admin
    """
    permission_classes = [IsAuthenticated, IsOrgAdmin]
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        organization_id = getattr(self.request, 'organization_id', None)
        if organization_id:
            return UserProfile.objects.filter(
                organization_id=organization_id
            ).select_related('user', 'organization')
        return UserProfile.objects.none()
    
    def perform_destroy(self, instance):
        # No eliminar el usuario, solo desactivar el perfil
        instance.is_active = False
        instance.save()
