from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
from .models import (
    ContextAnalysis, RiskMatrix, QualityObjective, 
    StakeholderProfile, ProcessMap, Document
)
from .serializers import DocumentSerializer, DocumentUploadSerializer, RiskMatrixSerializer, QualityObjectiveSerializer, QualityObjectiveSerializer
import logging
import os

logger = logging.getLogger(__name__)


@api_view(['GET'])
@csrf_exempt
def dashboard_summary(request):
    """Resumen ejecutivo del dashboard"""
    
    # Riesgos por nivel
    risks_by_level = RiskMatrix.objects.filter(
        status__in=['identified', 'under_analysis']
    ).values('risk_level').annotate(count=Count('id'))
    
    # Objetivos de calidad
    objectives = QualityObjective.objects.filter(status='active')
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
    stakeholders_count = StakeholderProfile.objects.filter(is_active=True).count()
    high_influence = StakeholderProfile.objects.filter(
        is_active=True, 
        influence_score__gte=0.8
    ).count()
    
    # Procesos
    processes = ProcessMap.objects.all()
    process_health = processes.values('health_status').annotate(count=Count('id'))
    
    # Último análisis de contexto
    last_analysis = ContextAnalysis.objects.filter(
        status='completed'
    ).order_by('-timestamp').first()
    
    return Response({
        'total_risks': RiskMatrix.objects.filter(status__in=['identified', 'under_analysis']).count(),
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
@csrf_exempt
def risk_matrix_list(request):
    """Lista consolidada de riesgos"""
    source = request.query_params.get('source', None)
    level = request.query_params.get('level', None)
    
    risks = RiskMatrix.objects.all()
    
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
        'total': risks.count(),
        'risks': risks_data
    })


@api_view(['GET'])
@csrf_exempt
def context_analysis_latest(request):
    """Obtiene el último análisis de contexto"""
    analysis = ContextAnalysis.objects.filter(
        status='completed'
    ).order_by('-timestamp').first()
    
    if not analysis:
        return Response({
            'message': 'No hay análisis completados'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'id': analysis.id,
        'timestamp': analysis.timestamp.isoformat(),
        'status': analysis.status,
        'internal_insights': analysis.internal_insights,
        'external_insights': analysis.external_insights,
        'total_documents_processed': analysis.total_documents_processed,
        'execution_time_seconds': analysis.execution_time_seconds
    })


@api_view(['GET'])
@csrf_exempt
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


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de documentos
    """
    queryset = Document.objects.all().order_by('-created_at')
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)
    
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
        total = Document.objects.all().count()
        by_type = {}
        
        for doc_type, _ in Document.TYPE_CHOICES:
            count = Document.objects.filter(
                document_type=doc_type
            ).count()
            by_type[doc_type] = count
        
        return Response({
            'total_documents': total,
            'by_type': by_type
        })

class RiskMatrixViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de la matriz de riesgos
    """
    queryset = RiskMatrix.objects.all().order_by('-detection_date')
    serializer_class = RiskMatrixSerializer
    
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
            serializer.save()
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
        levels = {}
        for level_code, level_name in RiskMatrix.LEVEL_CHOICES:
            risks = RiskMatrix.objects.filter(
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
        # Crear matriz 5x5 (probabilidad x impacto)
        matrix = {}
        
        prob_values = ['muy_baja', 'baja', 'media', 'alta', 'muy_alta']
        impact_values = ['muy_bajo', 'bajo', 'medio', 'alto', 'muy_alto']
        
        for prob in prob_values:
            matrix[prob] = {}
            for impact in impact_values:
                risks = RiskMatrix.objects.filter(
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
        categories = RiskMatrix.objects.values_list(
            'risk_category', flat=True
        ).distinct()
        return Response(list(categories))


@api_view(['GET'])
@csrf_exempt
def risk_stats(request):
    """Estadísticas de riesgos"""
    total = RiskMatrix.objects.count()
    active = RiskMatrix.objects.filter(status__in=['identified', 'under_analysis']).count()
    
    by_level = RiskMatrix.objects.filter(
        status__in=['identified', 'under_analysis']
    ).values('risk_level').annotate(count=Count('id'))
    
    by_source = RiskMatrix.objects.values('source_module').annotate(count=Count('id'))
    
    by_status = RiskMatrix.objects.values('status').annotate(count=Count('id'))
    
    by_category = RiskMatrix.objects.values('risk_category').annotate(count=Count('id'))
    
    return Response({
        'total_risks': total,
        'active_risks': active,
        'by_level': {item['risk_level']: item['count'] for item in by_level},
        'by_source': {item['source_module']: item['count'] for item in by_source},
        'by_status': {item['status']: item['count'] for item in by_status},
        'by_category': {item['risk_category']: item['count'] for item in by_category}
    })


class QualityObjectiveViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de objetivos de calidad
    """
    queryset = QualityObjective.objects.all().order_by('-created_at')
    serializer_class = QualityObjectiveSerializer
    
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
            serializer.save()
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
        total = QualityObjective.objects.count()
        
        by_status = {}
        for status_code, status_name in QualityObjective.STATUS_CHOICES:
            by_status[status_code] = QualityObjective.objects.filter(status=status_code).count()
        
        by_source = {}
        for source_code, source_name in QualityObjective.SOURCE_CHOICES:
            by_source[source_code] = QualityObjective.objects.filter(source_module=source_code).count()
        
        # Calcular progreso promedio
        objectives = QualityObjective.objects.filter(status__in=['active', 'in_progress'])
        avg_progress = 0
        if objectives.exists():
            total_progress = sum([obj.progress_percentage for obj in objectives])
            avg_progress = total_progress / objectives.count()
        
        achieved = QualityObjective.objects.filter(status='achieved').count()
        delayed = QualityObjective.objects.filter(status='delayed').count()
        
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
        objectives = QualityObjective.objects.all()[:10]
        
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

from .models import Organization, OrganizationSettings, ISOClauseConfig, AuditLog
from authentication.models import UserProfile
from .serializers import (
    OrganizationSerializer, UserProfileSerializer, UserCreateSerializer,
    OrganizationSettingsSerializer, ISOClauseConfigSerializer, AuditLogSerializer,
    UserSerializer
)
from django.contrib.auth.hashers import make_password
import json


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
            'total_documents': Document.objects.count(),
            'total_risks': RiskMatrix.objects.count(),
            'total_objectives': QualityObjective.objects.count(),
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
        org_id = (
            request.query_params.get(key)
            or request.query_params.get(f'{key}_id')
            or request.data.get(f'{key}_id')
            or request.data.get(key)
            or getattr(request, 'organization_id', None)
        )
        if org_id:
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
        
        return Response({
            'message': 'Backup iniciado correctamente',
            'last_backup_at': settings.last_backup_at
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
        })


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
    
    def get_queryset(self):
        queryset = super().get_queryset()
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
def export_data(request):
    """Exportar datos del sistema"""
    export_type = request.query_params.get('type', 'all')
    
    data = {}
    
    if export_type in ['all', 'risks']:
        data['risks'] = list(RiskMatrix.objects.values())
    
    if export_type in ['all', 'objectives']:
        data['objectives'] = list(QualityObjective.objects.values())
    
    if export_type in ['all', 'stakeholders']:
        data['stakeholders'] = list(StakeholderProfile.objects.values())
    
    if export_type in ['all', 'documents']:
        data['documents'] = list(Document.objects.values('id', 'title', 'document_type', 'source', 'created_at'))
    
    if export_type in ['all', 'processes']:
        data['processes'] = list(ProcessMap.objects.values())
    
    return Response({
        'export_date': timezone.now().isoformat(),
        'export_type': export_type,
        'data': data
    })
