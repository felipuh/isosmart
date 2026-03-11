from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
import calendar
from .models import (
    ContextAnalysis, RiskMatrix, QualityObjective, 
    StakeholderProfile, ProcessMap, Document
)
from .serializers import DocumentSerializer, DocumentUploadSerializer, RiskMatrixSerializer, QualityObjectiveSerializer, QualityObjectiveSerializer
from authentication.models import UserProfile
from .organization_scoping import OrganizationScopedViewSetMixin
import logging
import os

logger = logging.getLogger(__name__)


def _parse_org_id(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError({'organization_id': 'organization_id invalido'})


def _allowed_org_ids_for_request(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return set()
    if user.is_superuser:
        return None
    return set(
        UserProfile.objects.filter(user=user, is_active=True).values_list('organization_id', flat=True)
    )


def _resolve_scoped_org_id(request):
    query_org_id = _parse_org_id(
        request.query_params.get('organization_id') or request.query_params.get('organization')
    )
    token_org_id = _parse_org_id(getattr(request, 'organization_id', None))

    if query_org_id and token_org_id and query_org_id != token_org_id:
        raise PermissionDenied('organization_id no coincide con el token activo')

    organization_id = query_org_id or token_org_id
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    allowed_org_ids = _allowed_org_ids_for_request(request)
    if allowed_org_ids is not None and organization_id not in allowed_org_ids:
        raise PermissionDenied('No autorizado para esta organizacion')

    return organization_id


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """Resumen ejecutivo del dashboard"""
    organization_id = _resolve_scoped_org_id(request)
    
    # Riesgos por nivel
    risks_by_level = RiskMatrix.objects.filter(
        organization_id=organization_id,
        status__in=['identified', 'under_analysis']
    ).values('risk_level').annotate(count=Count('id'))
    
    # Objetivos de calidad
    objectives = QualityObjective.objects.filter(organization_id=organization_id, status='active')
    objectives_data = []
    for obj in objectives:
        objectives_data.append({
            'id': obj.id,
            'indicator_name': obj.indicator_name,
            'baseline': obj.baseline_value,
            'target': obj.target_value,
            'current': obj.current_value,
            'progress': obj.progress_percentage,
            'responsible': obj.responsible
        })
    
    # Stakeholders
    stakeholders_count = StakeholderProfile.objects.filter(organization_id=organization_id, is_active=True).count()
    high_influence = StakeholderProfile.objects.filter(
        organization_id=organization_id,
        is_active=True, 
        influence_score__gte=0.8
    ).count()
    
    # Procesos
    processes = ProcessMap.objects.filter(organization_id=organization_id)
    process_health = processes.values('health_status').annotate(count=Count('id'))
    
    # Último análisis de contexto
    last_analysis = ContextAnalysis.objects.filter(
        organization_id=organization_id,
        status='completed'
    ).order_by('-timestamp').first()
    
    return Response({
        'organization_id': organization_id,
        'total_risks': RiskMatrix.objects.filter(organization_id=organization_id, status__in=['identified', 'under_analysis']).count(),
        'risks_by_level': {
            'critical': next((r['count'] for r in risks_by_level if r['risk_level'] == 'critico'), 0),
            'high': next((r['count'] for r in risks_by_level if r['risk_level'] == 'alto'), 0),
            'medium': next((r['count'] for r in risks_by_level if r['risk_level'] == 'medio'), 0),
            'low': next((r['count'] for r in risks_by_level if r['risk_level'] == 'bajo'), 0),
        },
        'total_objectives': objectives.count(),
        'objectives_progress': sum([obj.progress_percentage for obj in objectives]) / objectives.count() if objectives.count() > 0 else 0,
        'objectives_data': objectives_data,
        'total_stakeholders': stakeholders_count,
        'high_influence_stakeholders': high_influence,
        'total_processes': processes.count(),
        'process_coverage': 100 if processes.count() > 0 else 0,
        'process_health': {
            'healthy': next((p['count'] for p in process_health if p['health_status'] == 'healthy'), 0),
            'warning': next((p['count'] for p in process_health if p['health_status'] == 'warning'), 0),
            'critical': next((p['count'] for p in process_health if p['health_status'] == 'critical'), 0),
        },
        'last_context_analysis': {
            'id': last_analysis.id if last_analysis else None,
            'timestamp': last_analysis.timestamp.isoformat() if last_analysis else None,
            'documents_processed': last_analysis.total_documents_processed if last_analysis else 0
        } if last_analysis else None,
        'last_update': datetime.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def risk_matrix_list(request):
    """Lista consolidada de riesgos"""
    organization_id = _resolve_scoped_org_id(request)
    source = request.query_params.get('source', None)
    level = request.query_params.get('level', None)
    
    risks = RiskMatrix.objects.filter(organization_id=organization_id)
    
    if source:
        risks = risks.filter(source_module=source)
    if level:
        risks = risks.filter(risk_level=level)
    
    risks_data = []
    for risk in risks[:50]:  # Limitar a 50 para performance
        risks_data.append({
            'id': risk.id,
            'description': risk.risk_description,
            'source_module': risk.source_module,
            'risk_level': risk.risk_level,
            'probability': risk.probability,
            'impact': risk.impact,
            'status': risk.status,
            'responsible': risk.responsible,
            'mitigation_actions': risk.mitigation_actions,
            'detection_date': risk.detection_date.isoformat(),
            'iso_clause': risk.iso_clause
        })
    
    return Response({
        'organization_id': organization_id,
        'total': risks.count(),
        'risks': risks_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def context_analysis_latest(request):
    """Obtiene el último análisis de contexto"""
    organization_id = _resolve_scoped_org_id(request)
    analysis = ContextAnalysis.objects.filter(
        organization_id=organization_id,
        status='completed'
    ).order_by('-timestamp').first()
    
    if not analysis:
        return Response({
            'organization_id': organization_id,
            'message': 'No hay análisis completados'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'organization_id': organization_id,
        'id': analysis.id,
        'timestamp': analysis.timestamp.isoformat(),
        'status': analysis.status,
        'internal_insights': analysis.internal_insights,
        'external_insights': analysis.external_insights,
        'total_documents_processed': analysis.total_documents_processed,
        'execution_time_seconds': analysis.execution_time_seconds
    })


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    from django.db import connection
    
    try:
        # Verificar conexión a BD
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return Response({
            'status': 'healthy',
            'service': 'isosmart-backend',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class DocumentViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de documentos
    """
    queryset = Document.objects.all().order_by('-created_at')
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar documentos por tipo si se especifica"""
        queryset = super().get_queryset()
        
        # Filtrar por tipo si se especifica
        doc_type = self.request.query_params.get('type', None)
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo documento con archivo"""
        organization_id = self.get_organization_id()
        serializer = DocumentUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Extraer datos
                title = serializer.validated_data['title']
                content = serializer.validated_data.get('content', '')
                doc_type = serializer.validated_data['document_type']
                uploaded_file = serializer.validated_data['file']
                source = serializer.validated_data.get('source', 'Sistema')
                uploaded_by = request.user if request.user.is_authenticated else None
                
                # Crear documento
                document = Document.objects.create(
                    organization_id=organization_id,
                    title=title,
                    content=content,
                    document_type=doc_type,
                    file_path=uploaded_file,
                    source=source,
                    uploaded_by=uploaded_by
                )
                
                logger.info(f"Documento creado: {document.title} (ID: {document.id})")
                
                # Serializar respuesta
                response_serializer = DocumentSerializer(document)
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(f"Error creando documento: {str(e)}", exc_info=True)
                return Response(
                    {'error': f'Error al crear documento: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        logger.error(f"Errores de serialización: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar documento"""
        try:
            instance = self.get_object()
            instance.delete()
            
            logger.info(f"Documento eliminado: {instance.title} (ID: {instance.id})")
            
            return Response(
                {'message': 'Documento eliminado exitosamente'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error eliminando documento: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar archivo del documento"""
        try:
            document = self.get_object()
            
            if not document.file_path:
                raise Http404("Archivo no encontrado")
            
            # Obtener la ruta del archivo
            file_path = document.file_path.path
            
            if not os.path.exists(file_path):
                raise Http404("Archivo no existe en el servidor")
            
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(str(document.file_path.name))
            )
            
            logger.info(f"Descargando documento: {document.title}")
            
            return response
            
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error descargando documento: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de documentos"""
        queryset = self.get_queryset()
        total = queryset.count()
        by_type = {}
        
        for doc_type, _ in Document.TYPE_CHOICES:
            count = queryset.filter(
                document_type=doc_type
            ).count()
            by_type[doc_type] = count
        
        return Response({
            'total_documents': total,
            'by_type': by_type
        })

class RiskMatrixViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de la matriz de riesgos
    """
    queryset = RiskMatrix.objects.all().order_by('-detection_date')
    serializer_class = RiskMatrixSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar riesgos según parámetros"""
        queryset = super().get_queryset()
        
        # Filtrar por módulo fuente
        source = self.request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source_module=source)
        
        # Filtrar por nivel de riesgo
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(risk_level=level)
        
        # Filtrar por estado
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtrar por categoría
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(risk_category=category)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo riesgo"""
        # Si no viene source_module, asignar MANUAL
        data = request.data.copy()
        if 'source_module' not in data:
            data['source_module'] = 'MANUAL'
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            logger.info(f"Riesgo creado: ID {serializer.data['id']}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Cambiar estado de un riesgo"""
        try:
            risk = self.get_object()
            new_status = request.data.get('status')
            
            if new_status not in dict(RiskMatrix.STATUS_CHOICES):
                return Response(
                    {'error': 'Estado inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            risk.status = new_status
            risk.save()
            
            logger.info(f"Riesgo {risk.id} cambiado a estado: {new_status}")
            
            serializer = self.get_serializer(risk)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error cambiando estado: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Obtener riesgos agrupados por nivel"""
        base_queryset = self.get_queryset()
        levels = {}
        for level_code, level_name in RiskMatrix.LEVEL_CHOICES:
            risks = base_queryset.filter(
                risk_level=level_code,
                status__in=['identified', 'under_analysis']
            )
            levels[level_code] = {
                'name': level_name,
                'count': risks.count(),
                'risks': RiskMatrixSerializer(risks[:10], many=True).data
            }
        return Response(levels)
    
    @action(detail=False, methods=['get'])
    def matrix_data(self, request):
        """Obtener datos para la matriz visual de riesgos"""
        base_queryset = self.get_queryset()
        # Crear matriz 5x5 (probabilidad x impacto)
        matrix = {}
        
        prob_values = ['muy_baja', 'baja', 'media', 'alta', 'muy_alta']
        impact_values = ['muy_bajo', 'bajo', 'medio', 'alto', 'muy_alto']
        
        for prob in prob_values:
            matrix[prob] = {}
            for impact in impact_values:
                risks = base_queryset.filter(
                    probability=prob,
                    impact=impact,
                    status__in=['identified', 'under_analysis']
                )
                matrix[prob][impact] = {
                    'count': risks.count(),
                    'risks': [{'id': r.id, 'description': r.risk_description[:50]} for r in risks[:5]]
                }
        
        return Response({
            'matrix': matrix,
            'probability_labels': dict(RiskMatrix.PROBABILITY_CHOICES),
            'impact_labels': dict(RiskMatrix.IMPACT_CHOICES)
        })
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Obtener lista de categorías únicas"""
        categories = self.get_queryset().values_list(
            'risk_category', flat=True
        ).distinct()
        return Response(list(categories))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def risk_stats(request):
    """Estadísticas de riesgos"""
    organization_id = _resolve_scoped_org_id(request)
    scoped_risks = RiskMatrix.objects.filter(organization_id=organization_id)
    total = scoped_risks.count()
    active = scoped_risks.filter(status__in=['identified', 'under_analysis']).count()
    
    by_level = scoped_risks.filter(
        status__in=['identified', 'under_analysis']
    ).values('risk_level').annotate(count=Count('id'))
    
    by_source = scoped_risks.values('source_module').annotate(count=Count('id'))
    
    by_status = scoped_risks.values('status').annotate(count=Count('id'))
    
    by_category = scoped_risks.values('risk_category').annotate(count=Count('id'))
    
    return Response({
        'organization_id': organization_id,
        'total_risks': total,
        'active_risks': active,
        'by_level': {item['risk_level']: item['count'] for item in by_level},
        'by_source': {item['source_module']: item['count'] for item in by_source},
        'by_status': {item['status']: item['count'] for item in by_status},
        'by_category': {item['risk_category']: item['count'] for item in by_category}
    })


class QualityObjectiveViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de objetivos de calidad
    """
    queryset = QualityObjective.objects.all().order_by('-created_at')
    serializer_class = QualityObjectiveSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        source = self.request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source_module=source)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'source_module' not in data:
            data['source_module'] = 'MANUAL'
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Actualizar valor actual del objetivo"""
        try:
            objective = self.get_object()
            new_value = request.data.get('current_value')
            
            if new_value is not None:
                objective.current_value = float(new_value)
                
                # Auto-actualizar estado basado en progreso
                progress = objective.progress_percentage
                if progress >= 100:
                    objective.status = 'achieved'
                elif progress > 0:
                    objective.status = 'in_progress'
                
                objective.save()
            
            serializer = self.get_serializer(objective)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de objetivos"""
        queryset = self.get_queryset()
        total = queryset.count()
        
        by_status = {}
        for status_code, status_name in QualityObjective.STATUS_CHOICES:
            by_status[status_code] = queryset.filter(status=status_code).count()
        
        by_source = {}
        for source_code, source_name in QualityObjective.SOURCE_CHOICES:
            by_source[source_code] = queryset.filter(source_module=source_code).count()
        
        # Calcular progreso promedio
        objectives = queryset.filter(status__in=['active', 'in_progress'])
        avg_progress = 0
        if objectives.exists():
            total_progress = sum([obj.progress_percentage for obj in objectives])
            avg_progress = total_progress / objectives.count()
        
        achieved = queryset.filter(status='achieved').count()
        delayed = queryset.filter(status='delayed').count()
        
        return Response({
            'total_objectives': total,
            'by_status': by_status,
            'by_source': by_source,
            'average_progress': round(avg_progress, 1),
            'achieved_count': achieved,
            'delayed_count': delayed,
            'active_count': by_status.get('active', 0) + by_status.get('in_progress', 0)
        })
    
    @action(detail=False, methods=['get'])
    def dashboard_data(self, request):
        """Datos para el dashboard de objetivos"""
        objectives = self.get_queryset()[:10]
        
        data = []
        for obj in objectives:
            data.append({
                'id': obj.id,
                'indicator_name': obj.indicator_name,
                'objective_description': obj.objective_description,
                'baseline_value': obj.baseline_value,
                'target_value': obj.target_value,
                'current_value': obj.current_value,
                'progress': obj.progress_percentage,
                'status': obj.status,
                'responsible': obj.responsible,
                'deadline': obj.deadline,
                'measurement_unit': obj.measurement_unit
            })
        
        return Response(data)


# =====================================================
# ViewSets para Configuración y Multicliente
# =====================================================

from .models import (
    Organization,
    OrganizationSettings,
    ISOClauseConfig,
    AuditLog,
    OnboardingInsightSnapshot,
    BillingSubscription,
    BillingPayment,
)
from .serializers import (
    OrganizationSerializer, UserProfileSerializer, UserCreateSerializer,
    OrganizationSettingsSerializer, ISOClauseConfigSerializer, AuditLogSerializer,
    UserSerializer, OnboardingInsightSnapshotSerializer,
    BillingSubscriptionSerializer, BillingPaymentSerializer,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import json
from .services.onboarding_orchestrator import OnboardingOrchestrator
from .services.billing_notifications import (
    log_billing_event,
    notify_payment_registered,
    notify_payment_confirmed,
    notify_payment_rejected,
    notify_subscription_status_change,
)


User = get_user_model()


def _add_one_month(input_date):
    year = input_date.year
    month = input_date.month + 1
    if month == 13:
        month = 1
        year += 1
    day = min(input_date.day, calendar.monthrange(year, month)[1])
    return input_date.replace(year=year, month=month, day=day)


def _sync_org_active_with_subscription(subscription):
    if subscription.status in ['suspended', 'cancelled']:
        if subscription.organization.is_active:
            subscription.organization.is_active = False
            subscription.organization.save(update_fields=['is_active', 'updated_at'])
    else:
        if not subscription.organization.is_active:
            subscription.organization.is_active = True
            subscription.organization.save(update_fields=['is_active', 'updated_at'])


class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de la organización"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Dashboard de la organización"""
        org = self.get_object()
        
        return Response({
            'organization': OrganizationSerializer(org).data,
            'users_count': org.members.filter(is_active=True).count(),
            'total_documents': Document.objects.filter(organization=org).count(),
            'total_risks': RiskMatrix.objects.filter(organization=org).count(),
            'total_objectives': QualityObjective.objects.filter(organization=org).count(),
        })


class UserManagementViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('organization', None) or getattr(self.request, 'organization_id', None)
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        else:
            queryset = queryset.none()
        return queryset.select_related('user', 'organization')
    
    @action(detail=False, methods=['post'])
    def create_user(self, request):
        """Crear nuevo usuario con perfil"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Crear usuario Django
            user = User.objects.create(
                username=data['username'],
                email=data['email'],
                password=make_password(data['password']),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                is_active=True
            )
            
            # Obtener o crear organización por defecto
            org_id = request.data.get('organization_id')
            if org_id:
                org = Organization.objects.get(id=org_id)
            else:
                org, _ = Organization.objects.get_or_create(
                    slug='default',
                    defaults={'name': 'Organización Principal'}
                )
            
            # Crear perfil
            profile = UserProfile.objects.create(
                user=user,
                organization=org,
                role=data.get('role', 'user'),
                job_title=data.get('job_title', ''),
                department=data.get('department', '')
            )
            
            return Response(UserProfileSerializer(profile).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        """Cambiar rol de usuario"""
        profile = self.get_object()
        new_role = request.data.get('role')
        
        if new_role not in dict(UserProfile.ROLE_CHOICES):
            return Response({'error': 'Rol inválido'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.role = new_role
        profile.save()
        
        return Response(UserProfileSerializer(profile).data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activar/desactivar usuario"""
        profile = self.get_object()
        profile.is_active = not profile.is_active
        profile.user.is_active = profile.is_active
        profile.save()
        profile.user.save()
        
        return Response(UserProfileSerializer(profile).data)
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Resetear contraseña de usuario"""
        profile = self.get_object()
        new_password = request.data.get('password')
        
        if not new_password or len(new_password) < 8:
            return Response({'error': 'La contraseña debe tener al menos 8 caracteres'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.user.password = make_password(new_password)
        profile.user.save()
        
        return Response({'message': 'Contraseña actualizada correctamente'})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de usuarios"""
        org_id = request.query_params.get('organization')
        
        queryset = UserProfile.objects.all()
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        total = queryset.count()
        active = queryset.filter(is_active=True).count()
        by_role = {}
        for role_code, role_name in UserProfile.ROLE_CHOICES:
            by_role[role_code] = queryset.filter(role=role_code).count()
        
        return Response({
            'total_users': total,
            'active_users': active,
            'inactive_users': total - active,
            'by_role': by_role
        })


class SettingsViewSet(viewsets.ModelViewSet):
    """ViewSet para configuración de la organización"""
    queryset = OrganizationSettings.objects.all()
    serializer_class = OrganizationSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('organization') or getattr(self.request, 'organization_id', None)
        if org_id:
            return queryset.filter(organization_id=org_id)
        return queryset.none()

    def _resolve_org(self, request, key='organization'):
        request_org_id = _parse_org_id(
            request.query_params.get(key)
            or request.query_params.get(f'{key}_id')
            or request.data.get(f'{key}_id')
            or request.data.get(key)
        )
        token_org_id = _parse_org_id(getattr(request, 'organization_id', None))

        if request_org_id and token_org_id and request_org_id != token_org_id:
            raise PermissionDenied('organization_id no coincide con el token activo')

        org_id = request_org_id or token_org_id
        if org_id:
            allowed_org_ids = _allowed_org_ids_for_request(request)
            if allowed_org_ids is not None and org_id not in allowed_org_ids:
                raise PermissionDenied('No autorizado para esta organizacion')
            return Organization.objects.get(id=org_id)

        profile = UserProfile.objects.filter(user=request.user, is_active=True).select_related('organization').first()
        if profile:
            return profile.organization
        raise Organization.DoesNotExist('No hay organización activa')
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Obtener configuración actual (o crear por defecto)"""
        org = self._resolve_org(request)
        
        settings = OrganizationSettings.objects.filter(organization=org).first()
        if settings is None:
            settings = OrganizationSettings(
                organization=org,
                enabled_standards=['ISO9001_2015'],
                onboarding_completed=False,
            )
        
        return Response(OrganizationSettingsSerializer(settings).data)
    
    @action(detail=False, methods=['post'])
    def update_ai_modules(self, request):
        """Actualizar configuración de módulos de IA"""
        org = self._resolve_org(request)
        
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        
        # Actualizar módulos
        if 'ai_sca_enabled' in request.data:
            settings.ai_sca_enabled = request.data['ai_sca_enabled']
        if 'ai_sie_enabled' in request.data:
            settings.ai_sie_enabled = request.data['ai_sie_enabled']
        if 'ai_asb_enabled' in request.data:
            settings.ai_asb_enabled = request.data['ai_asb_enabled']
        if 'ai_spm_enabled' in request.data:
            settings.ai_spm_enabled = request.data['ai_spm_enabled']
        if 'ai_auto_analysis' in request.data:
            settings.ai_auto_analysis = request.data['ai_auto_analysis']
        if 'ai_analysis_frequency' in request.data:
            settings.ai_analysis_frequency = request.data['ai_analysis_frequency']
        
        settings.save()
        return Response(OrganizationSettingsSerializer(settings).data)
    
    @action(detail=False, methods=['post'])
    def update_notifications(self, request):
        """Actualizar configuración de notificaciones"""
        org = self._resolve_org(request)
        
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        
        fields = ['notify_risk_critical', 'notify_risk_high', 'notify_objective_deadline',
                  'notify_document_upload', 'notify_stakeholder_change', 'notification_email']
        
        for field in fields:
            if field in request.data:
                setattr(settings, field, request.data[field])
        
        settings.save()
        return Response(OrganizationSettingsSerializer(settings).data)
    
    @action(detail=False, methods=['post'])
    def trigger_backup(self, request):
        """Disparar backup manual"""
        org = self._resolve_org(request)
        
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        settings.last_backup_at = timezone.now()
        settings.save()
        
        # Aquí iría la lógica real de backup
        backup_log = AuditLog.objects.create(
            organization=org,
            user=request.user if request.user and request.user.is_authenticated else None,
            action='backup',
            module='settings',
            description='Ejecución manual de backup desde configuración.',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            new_values={
                'status': 'completed',
                'source': 'manual_trigger',
                'backup_frequency': settings.backup_frequency,
                'last_backup_at': settings.last_backup_at.isoformat() if settings.last_backup_at else None,
            },
        )
        
        return Response({
            'message': 'Backup iniciado correctamente',
            'last_backup_at': settings.last_backup_at,
            'backup_id': backup_log.id,
        })

    @action(detail=False, methods=['get'])
    def backup_history(self, request):
        """Obtener historial de backups manuales por organización"""
        org = self._resolve_org(request)

        try:
            limit = int(request.query_params.get('limit', 20))
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 100))

        logs = (
            AuditLog.objects.filter(
                organization=org,
                action='backup',
                module='settings',
            )
            .select_related('user')
            .order_by('-created_at')[:limit]
        )

        results = []
        for log in logs:
            if log.user:
                user_name = log.user.get_full_name().strip() or log.user.username
            else:
                user_name = 'Sistema'

            results.append({
                'id': log.id,
                'organization_id': org.id,
                'action': log.action,
                'module': log.module,
                'description': log.description,
                'status': (log.new_values or {}).get('status', 'completed'),
                'source': (log.new_values or {}).get('source', 'manual_trigger'),
                'triggered_by': user_name,
                'triggered_at': log.created_at.isoformat() if log.created_at else None,
                'last_backup_at': (log.new_values or {}).get('last_backup_at'),
            })

        settings = OrganizationSettings.objects.filter(organization=org).first()
        if not results and settings and settings.last_backup_at:
            results.append({
                'id': None,
                'organization_id': org.id,
                'action': 'backup',
                'module': 'settings',
                'description': 'Backup registrado desde marca temporal histórica.',
                'status': 'completed',
                'source': 'legacy_timestamp',
                'triggered_by': 'Sistema',
                'triggered_at': settings.last_backup_at.isoformat(),
                'last_backup_at': settings.last_backup_at.isoformat(),
            })

        return Response({
            'count': len(results),
            'results': results,
        })
    
    @action(detail=False, methods=['post'])
    def update_standards(self, request):
        """Actualizar estándares ISO habilitados"""
        org = self._resolve_org(request)
        
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        
        # Obtener estándares del request
        enabled_standards = request.data.get('enabled_standards')
        if enabled_standards is None:
            return Response(
                {'error': 'Se requiere el campo enabled_standards'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Asegurar que ISO 9001 siempre esté incluido
        if 'ISO9001_2015' not in enabled_standards:
            enabled_standards = ['ISO9001_2015'] + list(enabled_standards)
        
        settings.enabled_standards = enabled_standards
        settings.save()
        
        return Response({
            'message': 'Estándares actualizados correctamente',
            'enabled_standards': settings.enabled_standards,
        })
    
    @action(detail=False, methods=['post'])
    def update_language(self, request):
        """Actualizar idioma preferido de la organización"""
        org = self._resolve_org(request)
        
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        
        # Obtener idioma del request
        preferred_language = request.data.get('preferred_language')
        if preferred_language is None:
            return Response(
                {'error': 'Se requiere el campo preferred_language'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que sea un idioma válido
        valid_languages = ['es-LATAM', 'en', 'pt']
        if preferred_language not in valid_languages:
            return Response(
                {'error': f'Idioma no válido. Debe ser uno de: {", ".join(valid_languages)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        settings.preferred_language = preferred_language
        settings.save()
        
        # También actualizar el idioma del usuario actual
        user_profile = UserProfile.objects.filter(user=request.user, organization=org).first()
        if user_profile:
            # Mapear el formato de idioma
            language_map = {
                'es-LATAM': 'es',
                'en': 'en',
                'pt': 'pt',
            }
            user_profile.language = language_map.get(preferred_language, 'es')
            user_profile.save(update_fields=['language'])
        
        return Response({
            'message': 'Idioma actualizado correctamente',
            'preferred_language': settings.preferred_language,
        })

    @action(detail=False, methods=['get'])
    def onboarding_status(self, request):
        org = self._resolve_org(request)
        settings = OrganizationSettings.objects.filter(organization=org).first()
        if settings is None:
            return Response({
                'organization_id': org.id,
                'organization_name': org.name,
                'onboarding_completed': False,
                'enabled_standards': ['ISO9001_2015'],
            })
        return Response({
            'organization_id': org.id,
            'organization_name': org.name,
            'onboarding_completed': settings.onboarding_completed,
            'enabled_standards': settings.enabled_standards or ['ISO9001_2015'],
        })

    @action(detail=False, methods=['post'])
    def complete_onboarding(self, request):
        """Completar onboarding y guardar preferencias"""
        org = self._resolve_org(request)
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)

        # Obtener y guardar estándares ISO habilitados
        enabled_standards = request.data.get('enabled_standards') or settings.enabled_standards or ['ISO9001_2015']
        settings.enabled_standards = enabled_standards
        
        # Obtener y guardar idioma preferido
        preferred_language = request.data.get('preferred_language')
        if preferred_language:
            settings.preferred_language = preferred_language
            # También actualizar el idioma del usuario actual
            user_profile = UserProfile.objects.filter(user=request.user, organization=org).first()
            if user_profile:
                # Mapear el formato de idioma
                language_map = {
                    'es-LATAM': 'es',
                    'en': 'en',
                    'pt': 'pt',
                }
                user_profile.language = language_map.get(preferred_language, 'es')
                user_profile.save(update_fields=['language'])

        preferred_response_tone = request.data.get('preferred_response_tone')
        if preferred_response_tone:
            valid_tones = ['manager', 'technical']
            if preferred_response_tone not in valid_tones:
                return Response(
                    {'error': f'Tono no válido. Debe ser uno de: {", ".join(valid_tones)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            settings.preferred_response_tone = preferred_response_tone

        onboarding_profile = request.data.get('onboarding_profile')
        if onboarding_profile is not None:
            if not isinstance(onboarding_profile, dict):
                return Response(
                    {'error': 'El campo onboarding_profile debe ser un objeto JSON'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            settings.onboarding_profile = onboarding_profile
        
        # Marcar onboarding como completado
        settings.onboarding_completed = True
        settings.onboarding_completed_at = timezone.now()
        settings.onboarding_completed_by = request.user
        settings.save()

        return Response({
            'message': 'Onboarding completado correctamente',
            'organization_id': org.id,
            'enabled_standards': settings.enabled_standards,
            'preferred_language': settings.preferred_language,
            'preferred_response_tone': settings.preferred_response_tone,
            'onboarding_profile': settings.onboarding_profile,
        })

    @action(detail=False, methods=['post'])
    def run_onboarding_orchestration(self, request):
        """Ejecuta motores Fase 2 y guarda snapshot versionado"""
        org = self._resolve_org(request)
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)

        profile = settings.onboarding_profile or {}
        if not isinstance(profile, dict):
            profile = {}

        orchestrator = OnboardingOrchestrator()
        result = orchestrator.run(profile, settings.preferred_response_tone)

        last_version = (
            OnboardingInsightSnapshot.objects
            .filter(organization=org)
            .order_by('-version')
            .values_list('version', flat=True)
            .first()
            or 0
        )

        snapshot = OnboardingInsightSnapshot.objects.create(
            organization=org,
            generated_by=request.user,
            version=last_version + 1,
            input_profile=profile,
            organizational_profile_output=result.get('organizational_profile', {}),
            impact_savings_output=result.get('impact_savings', {}),
            purpose_alignment_output=result.get('purpose_alignment', {}),
            summary_output=result.get('summary', {}),
        )

        return Response({
            'message': 'Orquestación de onboarding ejecutada correctamente',
            'snapshot': OnboardingInsightSnapshotSerializer(snapshot).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def onboarding_insights(self, request):
        """Obtiene último snapshot o historial de insights de onboarding"""
        org = self._resolve_org(request)
        include_history = str(request.query_params.get('history', '')).lower() in ['1', 'true', 'yes']

        queryset = OnboardingInsightSnapshot.objects.filter(organization=org)
        if include_history:
            data = OnboardingInsightSnapshotSerializer(queryset[:20], many=True).data
            return Response({'results': data})

        latest = queryset.first()
        if latest is None:
            return Response({'detail': 'No hay insights de onboarding generados aún.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OnboardingInsightSnapshotSerializer(latest).data)

    @action(detail=False, methods=['get'])
    def onboarding_iso_skeleton(self, request):
        """Obtiene el Esqueleto ISO generado en Fase 3"""
        org = self._resolve_org(request)
        latest = OnboardingInsightSnapshot.objects.filter(organization=org).first()
        if latest is None:
            return Response({'detail': 'No hay snapshot de onboarding disponible.'}, status=status.HTTP_404_NOT_FOUND)

        iso_skeleton = (latest.summary_output or {}).get('iso_skeleton')
        if not iso_skeleton:
            return Response({'detail': 'El snapshot no contiene Esqueleto ISO generado.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'organization_id': org.id,
            'snapshot_version': latest.version,
            'generated_at': latest.created_at,
            'iso_skeleton': iso_skeleton,
        })

    @action(detail=False, methods=['get'])
    def onboarding_adaptive_route(self, request):
        """Obtiene la ruta adaptativa de implementación (Fase 4)"""
        org = self._resolve_org(request)
        latest = OnboardingInsightSnapshot.objects.filter(organization=org).first()
        if latest is None:
            return Response({'detail': 'No hay snapshot de onboarding disponible.'}, status=status.HTTP_404_NOT_FOUND)

        adaptive_route = (latest.summary_output or {}).get('adaptive_route')
        if not adaptive_route:
            return Response({'detail': 'El snapshot no contiene ruta adaptativa.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'organization_id': org.id,
            'snapshot_version': latest.version,
            'generated_at': latest.created_at,
            'adaptive_route': adaptive_route,
        })


class BillingViewSet(viewsets.ViewSet):
    """Motor interno de billing (sin pasarela externa)."""
    permission_classes = [IsAuthenticated]

    def _allowed_organization_ids(self, request):
        if request.user and request.user.is_superuser:
            return None
        return list(
            UserProfile.objects.filter(user=request.user, is_active=True)
            .values_list('organization_id', flat=True)
        )

    def _request_meta(self, request):
        return {
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }

    def _resolve_org(self, request):
        allowed_org_ids = self._allowed_organization_ids(request)
        org_id = (
            request.query_params.get('organization')
            or request.query_params.get('organization_id')
            or request.data.get('organization_id')
            or getattr(request, 'organization_id', None)
        )
        if org_id:
            if allowed_org_ids is not None and int(org_id) not in allowed_org_ids:
                raise Organization.DoesNotExist('No autorizado para esta organización')
            return Organization.objects.get(id=org_id)
        profile = UserProfile.objects.filter(user=request.user, is_active=True).select_related('organization').first()
        if profile:
            return profile.organization
        raise Organization.DoesNotExist('No hay organización activa')

    @action(detail=False, methods=['get'])
    def current(self, request):
        org = self._resolve_org(request)
        subscription, _ = BillingSubscription.objects.get_or_create(
            organization=org,
            defaults={
                'status': 'active',
                'payment_method': 'bank_transfer',
                'grace_days': 8,
                'current_period_start': timezone.now().date(),
                'current_period_end': _add_one_month(timezone.now().date()),
                'next_due_date': _add_one_month(timezone.now().date()),
            }
        )
        previous_status = subscription.status
        subscription.evaluate_status()
        subscription.save(update_fields=['status', 'past_due_since', 'suspended_at', 'updated_at'])
        _sync_org_active_with_subscription(subscription)
        notify_subscription_status_change(subscription, previous_status, source='api_current')

        return Response({
            'subscription': BillingSubscriptionSerializer(subscription).data,
            'recent_payments': BillingPaymentSerializer(subscription.payments.all()[:10], many=True).data,
        })

    @action(detail=False, methods=['post'])
    def update_payer(self, request):
        org = self._resolve_org(request)
        subscription, _ = BillingSubscription.objects.get_or_create(organization=org)
        old_values = {
            'payer_user': subscription.payer_user_id,
            'payer_name': subscription.payer_name,
            'payer_email': subscription.payer_email,
            'payment_method': subscription.payment_method,
            'grace_days': subscription.grace_days,
            'auto_suspend_enabled': subscription.auto_suspend_enabled,
            'monthly_price': str(subscription.monthly_price),
            'currency': subscription.currency,
        }

        if 'payer_user_id' in request.data:
            payer_user_id = request.data.get('payer_user_id')
            if payer_user_id:
                payer_user = User.objects.filter(id=payer_user_id).first()
                subscription.payer_user = payer_user
                if payer_user:
                    subscription.payer_name = payer_user.get_full_name() or payer_user.username
                    subscription.payer_email = payer_user.email
            else:
                subscription.payer_user = None

        for field in ['payer_name', 'payer_email', 'payer_phone', 'payment_method', 'grace_days', 'auto_suspend_enabled', 'monthly_price', 'currency', 'notes']:
            if field in request.data:
                setattr(subscription, field, request.data.get(field))

        subscription.save()
        meta = self._request_meta(request)
        log_billing_event(
            organization=org,
            user=request.user,
            action='update',
            description='Actualización de configuración de pagador y parámetros de facturación.',
            old_values=old_values,
            new_values={
                'payer_user': subscription.payer_user_id,
                'payer_name': subscription.payer_name,
                'payer_email': subscription.payer_email,
                'payment_method': subscription.payment_method,
                'grace_days': subscription.grace_days,
                'auto_suspend_enabled': subscription.auto_suspend_enabled,
                'monthly_price': str(subscription.monthly_price),
                'currency': subscription.currency,
            },
            ip_address=meta['ip_address'],
            user_agent=meta['user_agent'],
        )
        return Response(BillingSubscriptionSerializer(subscription).data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def register_payment(self, request):
        org = self._resolve_org(request)
        subscription, _ = BillingSubscription.objects.get_or_create(organization=org)

        serializer = BillingPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evidence_file = request.FILES.get('evidence_file')
        payment = BillingPayment.objects.create(
            subscription=subscription,
            status='pending',
            payment_method=serializer.validated_data.get('payment_method', subscription.payment_method),
            amount=serializer.validated_data.get('amount', subscription.monthly_price),
            currency=serializer.validated_data.get('currency', subscription.currency),
            due_date=serializer.validated_data.get('due_date') or subscription.next_due_date,
            reference=serializer.validated_data.get('reference', ''),
            evidence_file=evidence_file,
            evidence_uploaded_at=timezone.now() if evidence_file else None,
            created_by=request.user,
        )

        meta = self._request_meta(request)
        log_billing_event(
            organization=org,
            user=request.user,
            action='create',
            description='Registro de pago en estado pendiente.',
            new_values={
                'payment_id': payment.id,
                'amount': str(payment.amount),
                'currency': payment.currency,
                'reference': payment.reference,
                'has_evidence_file': bool(payment.evidence_file),
            },
            ip_address=meta['ip_address'],
            user_agent=meta['user_agent'],
        )
        notify_payment_registered(payment)
        return Response(BillingPaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def confirm_payment(self, request):
        org = self._resolve_org(request)
        subscription = BillingSubscription.objects.filter(organization=org).first()
        if not subscription:
            return Response({'detail': 'No existe suscripción para la organización.'}, status=status.HTTP_404_NOT_FOUND)

        payment_id = request.data.get('payment_id')
        payment = BillingPayment.objects.filter(id=payment_id, subscription=subscription).first()
        if not payment:
            return Response({'detail': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        previous_status = payment.status
        payment.status = 'confirmed'
        payment.confirmed_by = request.user
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'confirmed_by', 'paid_at', 'updated_at'])

        paid_date = payment.paid_at.date()
        subscription.last_payment_date = paid_date
        if not subscription.current_period_start:
            subscription.current_period_start = paid_date
        if not subscription.current_period_end:
            subscription.current_period_end = _add_one_month(paid_date)
        else:
            subscription.current_period_start = subscription.current_period_end
            subscription.current_period_end = _add_one_month(subscription.current_period_end)

        subscription.next_due_date = subscription.current_period_end
        subscription.status = 'active'
        subscription.past_due_since = None
        subscription.suspended_at = None
        subscription.save()
        _sync_org_active_with_subscription(subscription)

        meta = self._request_meta(request)
        log_billing_event(
            organization=org,
            user=request.user,
            action='update',
            description='Confirmación de pago de suscripción.',
            old_values={'payment_id': payment.id, 'status': previous_status},
            new_values={'payment_id': payment.id, 'status': payment.status, 'paid_at': payment.paid_at.isoformat() if payment.paid_at else None},
            ip_address=meta['ip_address'],
            user_agent=meta['user_agent'],
        )
        notify_payment_confirmed(payment)

        return Response({
            'payment': BillingPaymentSerializer(payment).data,
            'subscription': BillingSubscriptionSerializer(subscription).data,
        })

    @action(detail=False, methods=['post'])
    def reject_payment(self, request):
        org = self._resolve_org(request)
        subscription = BillingSubscription.objects.filter(organization=org).first()
        if not subscription:
            return Response({'detail': 'No existe suscripción para la organización.'}, status=status.HTTP_404_NOT_FOUND)

        payment_id = request.data.get('payment_id')
        payment = BillingPayment.objects.filter(id=payment_id, subscription=subscription).first()
        if not payment:
            return Response({'detail': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        previous_status = payment.status
        payment.status = 'rejected'
        payment.rejection_reason = request.data.get('rejection_reason', '')
        payment.confirmed_by = request.user
        payment.save(update_fields=['status', 'rejection_reason', 'confirmed_by', 'updated_at'])

        meta = self._request_meta(request)
        log_billing_event(
            organization=org,
            user=request.user,
            action='update',
            description='Rechazo de pago de suscripción.',
            old_values={'payment_id': payment.id, 'status': previous_status},
            new_values={'payment_id': payment.id, 'status': payment.status, 'rejection_reason': payment.rejection_reason},
            ip_address=meta['ip_address'],
            user_agent=meta['user_agent'],
        )
        notify_payment_rejected(payment)

        return Response(BillingPaymentSerializer(payment).data)

    @action(detail=False, methods=['post'])
    def evaluate(self, request):
        org = self._resolve_org(request)
        subscription = BillingSubscription.objects.filter(organization=org).first()
        if not subscription:
            return Response({'detail': 'No existe suscripción para la organización.'}, status=status.HTTP_404_NOT_FOUND)

        previous_status = subscription.status
        subscription.evaluate_status()
        subscription.save(update_fields=['status', 'past_due_since', 'suspended_at', 'updated_at'])
        _sync_org_active_with_subscription(subscription)
        notify_subscription_status_change(subscription, previous_status, source='api_manual')

        meta = self._request_meta(request)
        log_billing_event(
            organization=org,
            user=request.user,
            action='update',
            description='Evaluación manual de estado de facturación.',
            old_values={'status': previous_status},
            new_values={'status': subscription.status},
            ip_address=meta['ip_address'],
            user_agent=meta['user_agent'],
        )

        return Response(BillingSubscriptionSerializer(subscription).data)


class ISOClauseConfigViewSet(viewsets.ModelViewSet):
    """ViewSet para configuración de cláusulas ISO"""
    queryset = ISOClauseConfig.objects.all()
    serializer_class = ISOClauseConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('organization') or getattr(self.request, 'organization_id', None)
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        standard_code = self.request.query_params.get('standard_code') or self.request.query_params.get('standard')
        if standard_code:
            queryset = queryset.filter(standard_code=standard_code)
        return queryset

    @staticmethod
    def _standard_clauses_map():
        return {
            'ISO9001_2015': [
                ('4.1', 'Comprensión de la organización y su contexto'),
                ('4.2', 'Necesidades y expectativas de partes interesadas'),
                ('4.3', 'Determinación del alcance del SGC'),
                ('4.4', 'Sistema de gestión de la calidad y procesos'),
                ('5.1', 'Liderazgo y compromiso'),
                ('5.2', 'Política'),
                ('5.3', 'Roles, responsabilidades y autoridades'),
                ('6.1', 'Acciones para abordar riesgos y oportunidades'),
                ('6.2', 'Objetivos de la calidad'),
                ('6.3', 'Planificación de los cambios'),
                ('7.1', 'Recursos'),
                ('7.2', 'Competencia'),
                ('7.3', 'Toma de conciencia'),
                ('7.4', 'Comunicación'),
                ('7.5', 'Información documentada'),
                ('8.1', 'Planificación y control operacional'),
                ('8.2', 'Requisitos para productos y servicios'),
                ('8.3', 'Diseño y desarrollo'),
                ('8.4', 'Control de procesos, productos y servicios externos'),
                ('8.5', 'Producción y provisión del servicio'),
                ('8.6', 'Liberación de productos y servicios'),
                ('8.7', 'Control de salidas no conformes'),
                ('9.1', 'Seguimiento, medición, análisis y evaluación'),
                ('9.2', 'Auditoría interna'),
                ('9.3', 'Revisión por la dirección'),
                ('10.1', 'Generalidades'),
                ('10.2', 'No conformidad y acción correctiva'),
                ('10.3', 'Mejora continua'),
            ],
            'ISO42001_2023': [
                ('4', 'Contexto de la organización IA'),
                ('5', 'Liderazgo para SGIA'),
                ('6', 'Planificación del SGIA'),
                ('7', 'Soporte y recursos IA'),
                ('8', 'Operación del SGIA'),
                ('9', 'Evaluación del desempeño del SGIA'),
                ('10', 'Mejora del SGIA'),
            ],
            'ISO27001_2022': [
                ('4', 'Contexto de la organización'),
                ('5', 'Liderazgo'),
                ('6', 'Planificación'),
                ('7', 'Soporte'),
                ('8', 'Operación'),
                ('9', 'Evaluación del desempeño'),
                ('10', 'Mejora'),
            ],
            'ISO14001_2015': [
                ('4', 'Contexto de la organización'),
                ('5', 'Liderazgo'),
                ('6', 'Planificación ambiental'),
                ('7', 'Soporte'),
                ('8', 'Operación'),
                ('9', 'Evaluación del desempeño'),
                ('10', 'Mejora'),
            ],
            'ISO45001_2018': [
                ('4', 'Contexto de la organización'),
                ('5', 'Liderazgo y participación de trabajadores'),
                ('6', 'Planificación SST'),
                ('7', 'Apoyo'),
                ('8', 'Operación'),
                ('9', 'Evaluación del desempeño'),
                ('10', 'Mejora'),
            ],
        }

    def _resolve_org(self, request):
        org_id = request.data.get('organization_id') or request.query_params.get('organization') or getattr(request, 'organization_id', None)
        if org_id:
            return Organization.objects.get(id=org_id)
        profile = UserProfile.objects.filter(user=request.user, is_active=True).select_related('organization').first()
        if profile:
            return profile.organization
        raise Organization.DoesNotExist('No hay organización activa')
    
    @action(detail=False, methods=['post'])
    def initialize_iso9001(self, request):
        """Inicializar cláusulas ISO 9001:2015"""
        org = self._resolve_org(request)
        clauses = self._standard_clauses_map()['ISO9001_2015']
        created_count = 0
        for number, name in clauses:
            _, created = ISOClauseConfig.objects.get_or_create(
                organization=org,
                standard_code='ISO9001_2015',
                clause_number=number,
                defaults={'clause_name': name, 'is_applicable': True}
            )
            if created:
                created_count += 1
        
        return Response({
            'message': f'Se crearon {created_count} cláusulas ISO 9001:2015',
            'total_clauses': len(clauses)
        })

    @action(detail=False, methods=['post'])
    def initialize_standards(self, request):
        org = self._resolve_org(request)
        standard_codes = request.data.get('standards') or ['ISO9001_2015']
        clause_map = self._standard_clauses_map()

        created_count = 0
        touched_standards = []
        for code in standard_codes:
            if code not in clause_map:
                continue
            touched_standards.append(code)
            for number, name in clause_map[code]:
                _, created = ISOClauseConfig.objects.get_or_create(
                    organization=org,
                    standard_code=code,
                    clause_number=number,
                    defaults={'clause_name': name, 'is_applicable': True}
                )
                if created:
                    created_count += 1

        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        settings.enabled_standards = touched_standards or settings.enabled_standards or ['ISO9001_2015']
        settings.save(update_fields=['enabled_standards'])

        return Response({
            'message': 'Estándares inicializados correctamente',
            'standards': touched_standards,
            'created_clauses': created_count,
        })


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para logs de auditoría (solo lectura)"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not (self.request.user and self.request.user.is_superuser):
            allowed_org_ids = list(
                UserProfile.objects.filter(user=self.request.user, is_active=True)
                .values_list('organization_id', flat=True)
            )
            queryset = queryset.filter(organization_id__in=allowed_org_ids)

        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        # Filtros adicionales
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module=module)
        
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset[:100]  # Limitar a últimos 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data(request):
    """Exportar datos del sistema"""
    organization_id = _resolve_scoped_org_id(request)
    export_type = request.query_params.get('type', 'all')
    
    data = {}
    
    if export_type in ['all', 'risks']:
        data['risks'] = list(RiskMatrix.objects.filter(organization_id=organization_id).values())
    
    if export_type in ['all', 'objectives']:
        data['objectives'] = list(QualityObjective.objects.filter(organization_id=organization_id).values())
    
    if export_type in ['all', 'stakeholders']:
        data['stakeholders'] = list(StakeholderProfile.objects.filter(organization_id=organization_id).values())
    
    if export_type in ['all', 'documents']:
        data['documents'] = list(Document.objects.filter(organization_id=organization_id).values('id', 'title', 'document_type', 'source', 'created_at'))
    
    if export_type in ['all', 'processes']:
        data['processes'] = list(ProcessMap.objects.filter(organization_id=organization_id).values())

    try:
        AuditLog.objects.create(
            organization_id=organization_id,
            user=request.user if request.user and request.user.is_authenticated else None,
            action='export',
            module='settings',
            description='Exportación de datos desde endpoint /api/export/.',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            new_values={
                'export_type': export_type,
                'sections': list(data.keys()),
            },
        )
    except Exception:
        logger.exception('No se pudo registrar AuditLog para export_data')
    
    return Response({
        'organization_id': organization_id,
        'export_date': timezone.now().isoformat(),
        'export_type': export_type,
        'data': data
    })
