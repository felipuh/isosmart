from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
from .models import (
    ContextAnalysis, RiskMatrix, QualityObjective, 
    StakeholderProfile, ProcessMap, Document
)
from .serializers import DocumentSerializer, DocumentUploadSerializer
import logging
import os
#from ai_modules.sca.tasks import analyze_context_periodic, analyze_document

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

@api_view(['POST'])
@csrf_exempt
def trigger_context_analysis(request):
    """Dispara análisis de contexto manual"""
    try:
        task = analyze_context_periodic.delay()
        
        return Response({
            'status': 'success',
            'message': 'Análisis de contexto iniciado',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        
        # Verificar Celery
        from backend.celery import app
        inspect = app.control.inspect()
        active_workers = inspect.active()
        
        return Response({
            'status': 'healthy',
            'service': 'isosmart-backend',
            'database': 'connected',
            'celery_workers': len(active_workers) if active_workers else 0,
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
        """Filtrar documentos activos por defecto"""
        queryset = super().get_queryset()
        
        # Filtrar por tipo si se especifica
        doc_type = self.request.query_params.get('type', None)
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        
        # Filtrar por activos
        is_active = self.request.query_params.get('active', 'true')
        if is_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo documento con archivo"""
        serializer = DocumentUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Extraer datos
                title = serializer.validated_data['title']
                description = serializer.validated_data.get('description', '')
                doc_type = serializer.validated_data['document_type']
                uploaded_file = serializer.validated_data['file']
                uploaded_by = serializer.validated_data.get('uploaded_by', 'Sistema')
                
                # Crear documento
                document = Document.objects.create(
                    title=title,
                    description=description,
                    document_type=doc_type,
                    file_path=uploaded_file,
                    file_size=uploaded_file.size,
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
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar documento (soft delete)"""
        try:
            instance = self.get_object()
            instance.is_active = False
            instance.save()
            
            logger.info(f"Documento desactivado: {instance.title} (ID: {instance.id})")
            
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
            
            file_path = document.file_path.path
            
            if not os.path.exists(file_path):
                raise Http404("Archivo no existe en el servidor")
            
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(file_path)
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
        total = Document.objects.filter(is_active=True).count()
        by_type = {}
        
        for doc_type, _ in Document.DOCUMENT_TYPES:
            count = Document.objects.filter(
                is_active=True,
                document_type=doc_type
            ).count()
            by_type[doc_type] = count
        
        total_size = sum(
            doc.file_size or 0 
            for doc in Document.objects.filter(is_active=True)
        )
        
        return Response({
            'total_documents': total,
            'by_type': by_type,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        })