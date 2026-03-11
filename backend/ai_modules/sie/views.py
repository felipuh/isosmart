"""
Vistas para Stakeholder Intelligence Engine (SIE)
Django REST Framework ViewSets y APIViews
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from ai_modules.sie.models.stakeholder import (
    StakeholderProfile,
    StakeholderChangeLog,
    StakeholderRelationship,
    StakeholderEngagementPlan
)
from ai_modules.sie.serializers import (
    StakeholderProfileSerializer,
    StakeholderProfileListSerializer,
    StakeholderChangeLogSerializer,
    StakeholderRelationshipSerializer,
    StakeholderEngagementPlanSerializer,
    StakeholderAnalysisResultSerializer
)
from ai_modules.sie.services.stakeholder_analyzer import StakeholderAnalyzer


class StakeholderProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Stakeholder Profiles
    
    Endpoints:
    - GET /api/sie/stakeholders/ - Lista todos los stakeholders
    - POST /api/sie/stakeholders/ - Crea un nuevo stakeholder
    - GET /api/sie/stakeholders/{id}/ - Detalle de un stakeholder
    - PUT /api/sie/stakeholders/{id}/ - Actualiza un stakeholder
    - DELETE /api/sie/stakeholders/{id}/ - Elimina un stakeholder
    - POST /api/sie/stakeholders/run_analysis/ - Ejecuta análisis de IA
    - GET /api/sie/stakeholders/critical/ - Lista stakeholders críticos
    - GET /api/sie/stakeholders/matrix/ - Matriz poder/interés
    """
    
    queryset = StakeholderProfile.objects.all()
    serializer_class = StakeholderProfileSerializer
    permission_classes = [IsAuthenticated]

    def _active_org_id(self):
        if getattr(self.request.user, 'is_superuser', False):
            org_param = self.request.query_params.get('organization_id')
            if org_param:
                try:
                    return int(org_param)
                except (ValueError, TypeError):
                    pass
            return None
        profile = getattr(self.request, 'user_profile', None)
        if profile and getattr(profile, 'organization_id', None):
            return profile.organization_id
        return None

    def perform_create(self, serializer):
        org_id = self._active_org_id()
        if not getattr(self.request.user, 'is_superuser', False):
            if not org_id:
                raise PermissionDenied('No se pudo resolver la organizacion activa')
            serializer.save(organization_id=org_id)
            return
        serializer.save()

    def perform_update(self, serializer):
        org_id = self._active_org_id()
        if not getattr(self.request.user, 'is_superuser', False):
            if not org_id:
                raise PermissionDenied('No se pudo resolver la organizacion activa')
            serializer.save(organization_id=org_id)
            return
        serializer.save()
    
    def get_serializer_class(self):
        """Usa serializer simplificado para listados"""
        if self.action == 'list':
            return StakeholderProfileListSerializer
        return StakeholderProfileSerializer
    
    def get_queryset(self):
        """Permite filtrar por tipo y estado"""
        queryset = StakeholderProfile.objects.all()

        org_id = self._active_org_id()
        if not getattr(self.request.user, 'is_superuser', False):
            if not org_id:
                return queryset.none()
            queryset = queryset.filter(organization_id=org_id)
        elif org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        stakeholder_type = self.request.query_params.get('type', None)
        is_active = self.request.query_params.get('active', None)
        is_critical = self.request.query_params.get('critical', None)
        
        if stakeholder_type:
            queryset = queryset.filter(stakeholder_type=stakeholder_type)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        if is_critical is not None:
            queryset = queryset.filter(is_critical=is_critical.lower() == 'true')
        
        return queryset.order_by('-influence_score', 'name')
    
    @action(detail=False, methods=['post'])
    def run_analysis(self, request):
        """
        Ejecuta el análisis completo de stakeholders con IA
        POST /api/sie/stakeholders/run_analysis/
        """
        try:
            analyzer = StakeholderAnalyzer()
            payload = {}
            if getattr(request, 'organization_id', None):
                payload['organization_id'] = request.organization_id
            result = analyzer.process(payload)
            
            serializer = StakeholderAnalysisResultSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e), 'status': 'error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """
        Lista stakeholders críticos
        GET /api/sie/stakeholders/critical/
        """
        critical_stakeholders = self.get_queryset().filter(
            is_critical=True,
            is_active=True
        ).order_by('-influence_score')
        
        serializer = self.get_serializer(critical_stakeholders, many=True)
        return Response({
            'count': critical_stakeholders.count(),
            'stakeholders': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def matrix(self, request):
        """
        Retorna datos para la matriz poder/interés
        GET /api/sie/stakeholders/matrix/
        """
        stakeholders = self.get_queryset().filter(is_active=True)
        
        matrix_data = {
            'manage_closely': [],     # Alto poder, Alto interés
            'keep_satisfied': [],     # Alto poder, Bajo interés
            'keep_informed': [],      # Bajo poder, Alto interés
            'monitor': []             # Bajo poder, Bajo interés
        }
        
        for sh in stakeholders:
            sh_data = {
                'id': sh.id,
                'name': sh.name,
                'type': sh.stakeholder_type,
                'power': sh.power,
                'interest': sh.interest,
                'influence_score': sh.influence_score,
                'satisfaction_score': sh.satisfaction_score
            }
            
            category = sh.engagement_category
            if 'Cerca' in category:
                matrix_data['manage_closely'].append(sh_data)
            elif 'Satisfecho' in category:
                matrix_data['keep_satisfied'].append(sh_data)
            elif 'Informado' in category:
                matrix_data['keep_informed'].append(sh_data)
            else:
                matrix_data['monitor'].append(sh_data)
        
        return Response(matrix_data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Estadísticas básicas de stakeholders
        GET /api/sie/stakeholders/stats/
        """
        try:
            queryset = self.get_queryset()
            total = queryset.count()
            by_type = queryset.values('stakeholder_type').annotate(count=Count('id'))
            by_power = queryset.values('power').annotate(count=Count('id'))
            by_interest = queryset.values('interest').annotate(count=Count('id'))

            critical_count = queryset.filter(is_critical=True).count()
            active_count = queryset.filter(is_active=True).count()

            return Response({
                'total_stakeholders': total,
                'active_count': active_count,
                'critical_count': critical_count,
                'by_type': {item['stakeholder_type']: item['count'] for item in by_type},
                'by_power': {item['power']: item['count'] for item in by_power},
                'by_interest': {item['interest']: item['count'] for item in by_interest}
            })

        except Exception as e:
            return Response(
                {'error': str(e), 'status': 'error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def change_history(self, request, pk=None):
        """
        Historial de cambios de un stakeholder
        GET /api/sie/stakeholders/{id}/change_history/
        """
        stakeholder = self.get_object()
        
        # Obtener cambios de los últimos 6 meses
        six_months_ago = timezone.now() - timedelta(days=180)
        changes = StakeholderChangeLog.objects.filter(
            stakeholder=stakeholder,
            detected_at__gte=six_months_ago
        ).order_by('-detected_at')
        
        serializer = StakeholderChangeLogSerializer(changes, many=True)
        return Response({
            'stakeholder': stakeholder.name,
            'change_count': changes.count(),
            'changes': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def update_satisfaction(self, request, pk=None):
        """
        Actualiza el score de satisfacción
        POST /api/sie/stakeholders/{id}/update_satisfaction/
        Body: {"satisfaction_score": 4.5}
        """
        stakeholder = self.get_object()
        new_score = request.data.get('satisfaction_score')
        
        if new_score is None:
            return Response(
                {'error': 'satisfaction_score requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_score = float(new_score)
            if not (0.0 <= new_score <= 10.0):
                raise ValueError("Score debe estar entre 0 y 10")
            
            old_score = stakeholder.satisfaction_score
            stakeholder.satisfaction_score = new_score
            stakeholder.save()
            
            # Registrar el cambio
            StakeholderChangeLog.objects.create(
                stakeholder=stakeholder,
                change_type='satisfaction_increase' if new_score > old_score else 'satisfaction_drop',
                previous_state={'satisfaction_score': old_score},
                new_state={'satisfaction_score': new_score},
                similarity_score=1.0 - abs(new_score - old_score) / 10.0
            )
            
            return Response({
                'success': True,
                'previous_score': old_score,
                'new_score': new_score,
                'risk_level': stakeholder.risk_level
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StakeholderChangeLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para logs de cambios (solo lectura)
    
    Endpoints:
    - GET /api/sie/change-logs/ - Lista cambios
    - GET /api/sie/change-logs/{id}/ - Detalle de cambio
    - GET /api/sie/change-logs/recent/ - Cambios recientes
    """
    
    queryset = StakeholderChangeLog.objects.all()
    serializer_class = StakeholderChangeLogSerializer
    permission_classes = [IsAuthenticated]

    def _active_org_id(self):
        if getattr(self.request.user, 'is_superuser', False):
            org_param = self.request.query_params.get('organization_id')
            if org_param:
                try:
                    return int(org_param)
                except (ValueError, TypeError):
                    pass
            return None
        profile = getattr(self.request, 'user_profile', None)
        if profile and getattr(profile, 'organization_id', None):
            return profile.organization_id
        return None
    
    def get_queryset(self):
        """Permite filtrar por stakeholder y tipo de cambio"""
        queryset = StakeholderChangeLog.objects.select_related('stakeholder').all()

        org_id = self._active_org_id()
        if not getattr(self.request.user, 'is_superuser', False):
            if not org_id:
                return queryset.none()
            queryset = queryset.filter(stakeholder__organization_id=org_id)
        elif org_id:
            queryset = queryset.filter(stakeholder__organization_id=org_id)
        
        stakeholder_id = self.request.query_params.get('stakeholder', None)
        change_type = self.request.query_params.get('type', None)
        
        if stakeholder_id:
            queryset = queryset.filter(stakeholder_id=stakeholder_id)
        
        if change_type:
            queryset = queryset.filter(change_type__icontains=change_type)
        
        return queryset.order_by('-detected_at')
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Cambios de las últimas 24 horas
        GET /api/sie/change-logs/recent/
        """
        yesterday = timezone.now() - timedelta(days=1)
        recent_changes = self.get_queryset().filter(
            detected_at__gte=yesterday
        ).order_by('-detected_at')[:50]
        
        serializer = self.get_serializer(recent_changes, many=True)
        return Response({
            'count': recent_changes.count(),
            'changes': serializer.data
        })


class StakeholderRelationshipViewSet(viewsets.ModelViewSet):
    """
    ViewSet para relaciones entre stakeholders
    
    Endpoints:
    - GET /api/sie/relationships/ - Lista relaciones
    - POST /api/sie/relationships/ - Crea relación
    - GET /api/sie/relationships/{id}/ - Detalle de relación
    - PUT /api/sie/relationships/{id}/ - Actualiza relación
    - DELETE /api/sie/relationships/{id}/ - Elimina relación
    """
    
    queryset = StakeholderRelationship.objects.all()
    serializer_class = StakeholderRelationshipSerializer
    permission_classes = [IsAuthenticated]

    def _active_org_id(self):
        if getattr(self.request.user, 'is_superuser', False):
            org_param = self.request.query_params.get('organization_id')
            if org_param:
                try:
                    return int(org_param)
                except (ValueError, TypeError):
                    pass
            return None
        profile = getattr(self.request, 'user_profile', None)
        if profile and getattr(profile, 'organization_id', None):
            return profile.organization_id
        return None
    
    def get_queryset(self):
        """Filtra por stakeholder"""
        queryset = StakeholderRelationship.objects.select_related('from_stakeholder', 'to_stakeholder').all()

        org_id = self._active_org_id()
        if not getattr(self.request.user, 'is_superuser', False):
            if not org_id:
                return queryset.none()
            queryset = queryset.filter(
                Q(from_stakeholder__organization_id=org_id)
                | Q(to_stakeholder__organization_id=org_id)
            )
        elif org_id:
            queryset = queryset.filter(
                Q(from_stakeholder__organization_id=org_id)
                | Q(to_stakeholder__organization_id=org_id)
            )
        
        stakeholder_id = self.request.query_params.get('stakeholder', None)
        
        if stakeholder_id:
            queryset = queryset.filter(
                Q(from_stakeholder_id=stakeholder_id)
                | Q(to_stakeholder_id=stakeholder_id)
            )
        
        return queryset.filter(is_active=True)


class StakeholderEngagementPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet para planes de engagement
    
    Endpoints:
    - GET /api/sie/engagement-plans/ - Lista planes
    - POST /api/sie/engagement-plans/ - Crea plan
    - GET /api/sie/engagement-plans/{id}/ - Detalle de plan
    - PUT /api/sie/engagement-plans/{id}/ - Actualiza plan
    - DELETE /api/sie/engagement-plans/{id}/ - Elimina plan
    - GET /api/sie/engagement-plans/active/ - Planes activos
    """
    
    queryset = StakeholderEngagementPlan.objects.all()
    serializer_class = StakeholderEngagementPlanSerializer
    permission_classes = [IsAuthenticated]

    def _active_org_id(self):
        if getattr(self.request.user, 'is_superuser', False):
            org_param = self.request.query_params.get('organization_id')
            if org_param:
                try:
                    return int(org_param)
                except (ValueError, TypeError):
                    pass
            return None
        profile = getattr(self.request, 'user_profile', None)
        if profile and getattr(profile, 'organization_id', None):
            return profile.organization_id
        return None
    
    def get_queryset(self):
        """Filtra por stakeholder y estado"""
        queryset = StakeholderEngagementPlan.objects.select_related('stakeholder').all()

        org_id = self._active_org_id()
        if not getattr(self.request.user, 'is_superuser', False):
            if not org_id:
                return queryset.none()
            queryset = queryset.filter(stakeholder__organization_id=org_id)
        elif org_id:
            queryset = queryset.filter(stakeholder__organization_id=org_id)
        
        stakeholder_id = self.request.query_params.get('stakeholder', None)
        plan_status = self.request.query_params.get('status', None)
        
        if stakeholder_id:
            queryset = queryset.filter(stakeholder_id=stakeholder_id)
        
        if plan_status:
            queryset = queryset.filter(status=plan_status)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Planes activos
        GET /api/sie/engagement-plans/active/
        """
        active_plans = StakeholderEngagementPlan.objects.filter(
            status='active'
        ).order_by('-created_at')
        
        serializer = self.get_serializer(active_plans, many=True)
        return Response({
            'count': active_plans.count(),
            'plans': serializer.data
        })
