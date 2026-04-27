from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from django.conf import settings as django_settings
from django.http import FileResponse, Http404
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
import calendar
from .models import (
    ContextAnalysis, FeatureFlag, RiskMatrix, QualityObjective,
    StakeholderProfile, ProcessMap, Document
)
from .serializers import DocumentSerializer, DocumentUploadSerializer, RiskMatrixSerializer, QualityObjectiveSerializer, QualityObjectiveSerializer
from authentication.models import UserProfile
from .organization_scoping import OrganizationScopedViewSetMixin
from integration.services.auto_indexing import queue_core_document_index, remove_indexed_artifact
from core.services.document_service import DocumentCreationError, create_document_from_upload
from core.services.health_service import HealthCheckError, check_database_connection
import logging
import os

logger = logging.getLogger(__name__)

# Commercial rollout policy (configurable):
# - settings.COMMERCIAL_ENABLED_STANDARDS: global list
# - settings.COMMERCIAL_ENABLED_STANDARDS_BY_ORG: per-org overrides
STANDARD_CATALOG = (
    'ISO9001_2015',
    'ISO42001_2023',
    'ISO27001_2022',
    'ISO14001_2015',
    'ISO45001_2018',
)


def _to_standard_candidates(raw_values):
    if isinstance(raw_values, (list, tuple, set)):
        return [str(value).strip() for value in raw_values if value not in (None, '')]
    return []


def _resolve_commercially_available_standards(organization_id=None):
    global_candidates = _to_standard_candidates(
        getattr(django_settings, 'COMMERCIAL_ENABLED_STANDARDS', ['ISO9001_2015'])
    )
    if not global_candidates:
        global_candidates = ['ISO9001_2015']

    overrides = getattr(django_settings, 'COMMERCIAL_ENABLED_STANDARDS_BY_ORG', {}) or {}
    override_candidates = None
    if organization_id is not None:
        override_candidates = overrides.get(organization_id)
        if override_candidates is None:
            override_candidates = overrides.get(str(organization_id))

    source_candidates = _to_standard_candidates(override_candidates) if override_candidates is not None else global_candidates

    available = []
    for code in source_candidates:
        if code in STANDARD_CATALOG and code not in available:
            available.append(code)

    if 'ISO9001_2015' not in available:
        available.insert(0, 'ISO9001_2015')

    return available


def _normalize_enabled_standards(raw_values, organization_id=None):
    allowed = set(_resolve_commercially_available_standards(organization_id))
    candidates = _to_standard_candidates(raw_values)

    normalized = []
    for code in candidates:
        if code in allowed and code not in normalized:
            normalized.append(code)

    if 'ISO9001_2015' in allowed and 'ISO9001_2015' not in normalized:
        normalized.insert(0, 'ISO9001_2015')

    if not normalized:
        normalized = _resolve_commercially_available_standards(organization_id)[:1]

    return normalized


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
        'climate_context': analysis.climate_context,
        'environmental_scope': analysis.environmental_scope,
        'total_documents_processed': analysis.total_documents_processed,
        'execution_time_seconds': analysis.execution_time_seconds
    })


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    try:
        check_database_connection()
        
        return Response({
            'status': 'healthy',
            'service': 'isosmart-backend',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })

    except HealthCheckError as exc:
        logger.warning("Health check failed", extra={'error': str(exc)})
        return Response({
            'status': 'unhealthy',
            'error': 'database_unavailable'
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

        serializer.is_valid(raise_exception=True)

        try:
            document = create_document_from_upload(
                organization_id=organization_id,
                validated_data=serializer.validated_data,
                uploaded_by=request.user if request.user.is_authenticated else None,
            )
        except DocumentCreationError as exc:
            logger.error("Error creando documento", exc_info=True)
            return Response(
                {'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(f"Documento creado: {document.title} (ID: {document.id})")
        response_serializer = DocumentSerializer(document)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        document = serializer.save()
        queue_core_document_index(document)
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar documento"""
        try:
            instance = self.get_object()
            org_id = instance.organization_id
            document_id = f'core_document_{instance.id}'
            instance.delete()
            remove_indexed_artifact(org_id, document_id)
            
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
    NotificationDelivery,
    OnboardingInsightSnapshot,
    BillingSubscription,
    BillingPayment,
)
from .serializers import (
    OrganizationSerializer, UserProfileSerializer, UserCreateSerializer,
    OrganizationSettingsSerializer, ISOClauseConfigSerializer, AuditLogSerializer,
    UserSerializer, OnboardingInsightSnapshotSerializer,
    BillingSubscriptionSerializer, BillingPaymentSerializer, NotificationDeliverySerializer,
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


def _request_ip_address(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _create_audit_log(request, organization, action, module, description, old_values=None, new_values=None):
    return AuditLog.objects.create(
        organization=organization,
        user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
        action=action,
        module=module,
        description=description,
        ip_address=_request_ip_address(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        old_values=old_values or {},
        new_values=new_values or {},
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

    def _resolve_role(self, request, org_id=None):
        if request.user and request.user.is_superuser:
            return 'org_admin'

        queryset = UserProfile.objects.filter(user=request.user, is_active=True)
        if org_id:
            profile = queryset.filter(organization_id=org_id).first()
        else:
            profile = queryset.first()
        return profile.role if profile else None

    def _require_roles(self, request, allowed_roles, org_id=None):
        role = self._resolve_role(request, org_id=org_id)
        if role not in allowed_roles:
            raise PermissionDenied('No autorizado para esta accion')

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user and self.request.user.is_superuser:
            return queryset

        allowed_org_ids = _allowed_org_ids_for_request(self.request)
        if allowed_org_ids is None:
            return queryset
        return queryset.filter(id__in=allowed_org_ids)

    def perform_create(self, serializer):
        self._require_roles(self.request, {'org_admin'})
        serializer.save()

    def perform_update(self, serializer):
        self._require_roles(self.request, {'org_admin'}, org_id=serializer.instance.id)
        serializer.save()

    def perform_destroy(self, instance):
        self._require_roles(self.request, {'org_admin'}, org_id=instance.id)
        super().perform_destroy(instance)
    
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

    def _resolve_org_id(self, request):
        return _parse_org_id(
            request.query_params.get('organization')
            or request.query_params.get('organization_id')
            or request.data.get('organization_id')
            or getattr(request, 'organization_id', None)
        )

    def _current_role(self, request, org_id=None):
        if request.user and request.user.is_superuser:
            return 'org_admin'

        resolved_org_id = org_id or self._resolve_org_id(request)
        queryset = UserProfile.objects.filter(user=request.user, is_active=True)
        if resolved_org_id:
            profile = queryset.filter(organization_id=resolved_org_id).first()
        else:
            profile = queryset.first()
        return profile.role if profile else None

    def _require_roles(self, request, allowed_roles, org_id=None):
        role = self._current_role(request, org_id=org_id)
        if role not in allowed_roles:
            raise PermissionDenied('No autorizado para esta accion')
    
    def get_queryset(self):
        self._require_roles(self.request, {'org_admin'}, org_id=self._resolve_org_id(self.request))

        queryset = super().get_queryset()
        org_id = self._resolve_org_id(self.request)
        allowed_org_ids = _allowed_org_ids_for_request(self.request)
        if org_id and allowed_org_ids is not None and org_id not in allowed_org_ids:
            raise PermissionDenied('No autorizado para esta organizacion')

        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        else:
            queryset = queryset.none()
        return queryset.select_related('user', 'organization')
    
    @action(detail=False, methods=['post'])
    def create_user(self, request):
        """Crear nuevo usuario con perfil"""
        self._require_roles(request, {'org_admin'}, org_id=self._resolve_org_id(request))

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
        self._require_roles(request, {'org_admin'}, org_id=self._resolve_org_id(request))

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
        self._require_roles(request, {'org_admin'}, org_id=self._resolve_org_id(request))

        profile = self.get_object()
        profile.is_active = not profile.is_active
        profile.user.is_active = profile.is_active
        profile.save()
        profile.user.save()
        
        return Response(UserProfileSerializer(profile).data)
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Resetear contraseña de usuario"""
        self._require_roles(request, {'org_admin'}, org_id=self._resolve_org_id(request))

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
        org_id = self._resolve_org_id(request)
        self._require_roles(request, {'org_admin'}, org_id=org_id)

        allowed_org_ids = _allowed_org_ids_for_request(request)
        if org_id and allowed_org_ids is not None and org_id not in allowed_org_ids:
            raise PermissionDenied('No autorizado para esta organizacion')
        
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

    def _current_role(self, request, org=None):
        if request.user and request.user.is_superuser:
            return 'org_admin'

        queryset = UserProfile.objects.filter(user=request.user, is_active=True)
        if org is not None:
            profile = queryset.filter(organization=org).first()
        else:
            profile = queryset.first()
        return profile.role if profile else None

    def _require_roles(self, request, allowed_roles, org=None):
        role = self._current_role(request, org=org)
        if role not in allowed_roles:
            raise PermissionDenied('No autorizado para esta accion')

    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('organization') or getattr(self.request, 'organization_id', None)
        if org_id:
            return queryset.filter(organization_id=org_id)
        return queryset.none()

    def _resolve_org(self, request, key='organization'):
        org_id = _parse_org_id(
            request.query_params.get(key)
            or request.query_params.get(f'{key}_id')
            or request.data.get(f'{key}_id')
            or request.data.get(key)
            or getattr(request, 'organization_id', None)
        )
        if org_id:
            token_org_id = _parse_org_id(getattr(request, 'organization_id', None))
            if token_org_id and token_org_id != org_id:
                raise PermissionDenied('organization_id no coincide con el token activo')

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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
        
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
        
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
        
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        previous_backup_at = settings.last_backup_at.isoformat() if settings.last_backup_at else None
        settings.last_backup_at = timezone.now()
        settings.save(update_fields=['last_backup_at', 'updated_at'])
        
        backup_log = _create_audit_log(
            request,
            org,
            action='backup',
            module='settings',
            description='Backup manual ejecutado desde configuracion',
            old_values={'last_backup_at': previous_backup_at},
            new_values={
                'last_backup_at': settings.last_backup_at.isoformat(),
                'backup_frequency': settings.backup_frequency,
                'auto_backup_enabled': settings.auto_backup_enabled,
            },
        )
        
        return Response({
            'message': 'Backup iniciado correctamente',
            'last_backup_at': settings.last_backup_at,
            'history_entry': AuditLogSerializer(backup_log).data,
        })

    @action(detail=False, methods=['get'])
    def backups(self, request):
        """Obtener historial reciente de backups manuales"""
        org = self._resolve_org(request)

        limit = request.query_params.get('limit', '10')
        try:
            limit = min(max(int(limit), 1), 100)
        except (TypeError, ValueError):
            raise ValidationError({'limit': 'limit invalido'})

        queryset = AuditLog.objects.filter(
            organization=org,
            action='backup',
            module='settings',
        ).select_related('user').order_by('-created_at')

        total = queryset.count()
        serializer = AuditLogSerializer(queryset[:limit], many=True)
        return Response({
            'count': total,
            'results': serializer.data,
        })

    @action(detail=False, methods=['get'])
    def notification_history(self, request):
        """Obtener historial reciente de entregas de notificaciones."""
        org = self._resolve_org(request)

        limit = request.query_params.get('limit', '10')
        try:
            limit = min(max(int(limit), 1), 100)
        except (TypeError, ValueError):
            raise ValidationError({'limit': 'limit invalido'})

        queryset = NotificationDelivery.objects.filter(organization=org).order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        total = queryset.count()
        serializer = NotificationDeliverySerializer(queryset[:limit], many=True)
        return Response({
            'count': total,
            'results': serializer.data,
        })

    @action(detail=False, methods=['get'])
    def business_report(self, request):
        """Generar reporte de negocio en formato PDF, XLSX o CSV."""
        from . import reports as report_module

        org = self._resolve_org(request)
        report_type = request.query_params.get('type', 'sgq_executive')
        fmt = request.query_params.get('file_format') or request.query_params.get('fmt') or 'pdf'
        date_from = request.query_params.get('date_from') or None
        date_to = request.query_params.get('date_to') or None
        status_filter = request.query_params.get('status') or None

        user_name = (
            request.user.get_full_name() or request.user.username
            if request.user and request.user.is_authenticated else 'Sistema'
        )

        try:
            buf, content_type, filename = report_module.generate_report(
                organization=org,
                report_type=report_type,
                fmt=fmt,
                date_from=date_from,
                date_to=date_to,
                status_filter=status_filter,
                user_name=user_name,
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)
        except Exception as exc:
            logger.exception("Error generating business report: %s", exc)
            return Response({'error': 'Error al generar el reporte.'}, status=500)

        _create_audit_log(
            request,
            org,
            action='export',
            module='reports',
            description=f'Reporte generado: tipo={report_type} formato={fmt}',
            new_values={'type': report_type, 'format': fmt, 'date_from': date_from, 'date_to': date_to},
        )

        response = HttpResponse(buf.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    @action(detail=False, methods=['post'])
    def update_standards(self, request):
        """Actualizar estándares ISO habilitados"""
        org = self._resolve_org(request)
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
        
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        
        # Obtener estándares del request
        enabled_standards = request.data.get('enabled_standards')
        if enabled_standards is None:
            return Response(
                {'error': 'Se requiere el campo enabled_standards'},
                status=status.HTTP_400_BAD_REQUEST
            )

        enabled_standards = _normalize_enabled_standards(enabled_standards, org.id)
        
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
        
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
        commercially_available_standards = _resolve_commercially_available_standards(org.id)
        settings = OrganizationSettings.objects.filter(organization=org).first()
        if settings is None:
            return Response({
                'organization_id': org.id,
                'organization_name': org.name,
                'onboarding_completed': False,
                'enabled_standards': _normalize_enabled_standards([], org.id),
                'commercially_available_standards': commercially_available_standards,
            })
        return Response({
            'organization_id': org.id,
            'organization_name': org.name,
            'onboarding_completed': settings.onboarding_completed,
            'enabled_standards': _normalize_enabled_standards(settings.enabled_standards, org.id),
            'commercially_available_standards': commercially_available_standards,
        })

    @action(detail=False, methods=['post'])
    def complete_onboarding(self, request):
        """Completar onboarding y guardar preferencias"""
        org = self._resolve_org(request)
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)

        # Obtener y guardar estándares ISO habilitados
        enabled_standards = _normalize_enabled_standards(
            request.data.get('enabled_standards') or settings.enabled_standards,
            org.id,
        )
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
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
            # Empty state is expected until onboarding orchestration runs.
            return Response(None)
        return Response(OnboardingInsightSnapshotSerializer(latest).data)

    @action(detail=False, methods=['get'])
    def onboarding_iso_skeleton(self, request):
        """Obtiene el Esqueleto ISO generado en Fase 3"""
        org = self._resolve_org(request)
        latest = OnboardingInsightSnapshot.objects.filter(organization=org).first()
        if latest is None:
            return Response({
                'organization_id': org.id,
                'snapshot_version': None,
                'generated_at': None,
                'iso_skeleton': None,
            })

        iso_skeleton = (latest.summary_output or {}).get('iso_skeleton')
        return Response({
            'organization_id': org.id,
            'snapshot_version': latest.version,
            'generated_at': latest.created_at,
            'iso_skeleton': iso_skeleton or None,
        })

    @action(detail=False, methods=['get'])
    def onboarding_adaptive_route(self, request):
        """Obtiene la ruta adaptativa de implementación (Fase 4)"""
        org = self._resolve_org(request)
        latest = OnboardingInsightSnapshot.objects.filter(organization=org).first()
        if latest is None:
            return Response({
                'organization_id': org.id,
                'snapshot_version': None,
                'generated_at': None,
                'adaptive_route': None,
            })

        adaptive_route = (latest.summary_output or {}).get('adaptive_route')
        return Response({
            'organization_id': org.id,
            'snapshot_version': latest.version,
            'generated_at': latest.created_at,
            'adaptive_route': adaptive_route or None,
        })


class BillingViewSet(viewsets.ViewSet):
    """Motor interno de billing (sin pasarela externa)."""
    permission_classes = [IsAuthenticated]

    def _resolve_role(self, request, org_id=None):
        if request.user and request.user.is_superuser:
            return 'org_admin'

        queryset = UserProfile.objects.filter(user=request.user, is_active=True)
        if org_id:
            profile = queryset.filter(organization_id=org_id).first()
        else:
            profile = queryset.first()
        return profile.role if profile else None

    def _require_roles(self, request, allowed_roles, org):
        role = self._resolve_role(request, org_id=org.id)
        if role not in allowed_roles:
            raise PermissionDenied('No autorizado para esta accion')

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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org)
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
        self._require_roles(request, {'org_admin', 'iso_manager', 'user'}, org)
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org)
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org)
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org)
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

    def _resolve_role(self, request, org_id=None):
        if request.user and request.user.is_superuser:
            return 'org_admin'

        queryset = UserProfile.objects.filter(user=request.user, is_active=True)
        if org_id:
            profile = queryset.filter(organization_id=org_id).first()
        else:
            profile = queryset.first()
        return profile.role if profile else None

    def _require_roles(self, request, allowed_roles, org=None):
        role = self._resolve_role(request, org_id=org.id if org else None)
        if role not in allowed_roles:
            raise PermissionDenied('No autorizado para esta accion')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('organization') or self.request.query_params.get('organization_id') or getattr(self.request, 'organization_id', None)
        if org_id:
            allowed_org_ids = _allowed_org_ids_for_request(self.request)
            if allowed_org_ids is not None and int(org_id) not in allowed_org_ids:
                raise PermissionDenied('No autorizado para esta organizacion')
            queryset = queryset.filter(organization_id=org_id)
        elif not (self.request.user and self.request.user.is_superuser):
            allowed_org_ids = _allowed_org_ids_for_request(self.request)
            queryset = queryset.filter(organization_id__in=allowed_org_ids)
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
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
        self._require_roles(request, {'org_admin', 'iso_manager'}, org=org)
        standard_codes = _normalize_enabled_standards(request.data.get('standards'), org.id)
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
        settings.enabled_standards = _normalize_enabled_standards(
            touched_standards or settings.enabled_standards,
            org.id,
        )
        settings.save(update_fields=['enabled_standards'])

        return Response({
            'message': 'Estándares inicializados correctamente',
            'standards': touched_standards,
            'created_clauses': created_count,
        })

    def perform_create(self, serializer):
        org = self._resolve_org(self.request)
        self._require_roles(self.request, {'org_admin', 'iso_manager'}, org=org)
        serializer.save()

    def perform_update(self, serializer):
        org = serializer.instance.organization
        self._require_roles(self.request, {'org_admin', 'iso_manager'}, org=org)
        serializer.save()

    def perform_destroy(self, instance):
        self._require_roles(self.request, {'org_admin', 'iso_manager'}, org=instance.organization)
        super().perform_destroy(instance)


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

    organization = Organization.objects.get(id=organization_id)
    _create_audit_log(
        request,
        organization,
        action='export',
        module='settings',
        description=f'Exportacion de datos tipo {export_type}',
        new_values={
            'export_type': export_type,
            'sections': sorted(data.keys()),
        },
    )
    
    return Response({
        'organization_id': organization_id,
        'export_date': timezone.now().isoformat(),
        'export_type': export_type,
        'data': data
    })


# =====================================================
# Feature Flags endpoint
# =====================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feature_flags_view(request):
    """
    GET /api/core/feature-flags/
    Returns {flag_name: bool} resolved for the requesting user's organization context.
    Superusers may pass ?org_id=<id> to query a specific organization.
    """
    profile = getattr(request.user, 'userprofile', None)

    if request.user.is_superuser and request.query_params.get('org_id'):
        try:
            from .models import Organization
            org = Organization.objects.get(pk=request.query_params['org_id'])
        except Organization.DoesNotExist:
            return Response({'detail': 'Organization not found.'}, status=404)
    elif profile and profile.organization:
        org = profile.organization
    else:
        org = None

    flags = FeatureFlag.objects.resolve_all(organization=org)
    return Response(flags)
