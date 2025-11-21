from rest_framework.decorators import api_view
from rest_framework.response import Response
from ai_modules.sca.tasks import analyze_context_periodic
from ai_modules.sie.services.stakeholder_mapper import StakeholderMapper
from ai_modules.spm.services.process_mapper import ProcessMapper

@api_view(['POST'])
def trigger_context_analysis(request):
    """Dispara análisis de contexto manual"""
    task = analyze_context_periodic.delay()
    return Response({'task_id': task.id, 'status': 'processing'})

@api_view(['GET'])
def get_stakeholder_network(request):
    """Retorna red de stakeholders visualizable"""
    mapper = StakeholderMapper()
    stakeholders = StakeholderProfile.objects.all().values()
    
    graph = mapper.build_stakeholder_network(list(stakeholders))
    influence = mapper.calculate_influence()
    
    # Convertir a formato JSON para frontend
    network_data = {
        'nodes': [{'id': n, **graph.nodes[n], 'influence': influence[n]} for n in graph.nodes()],
        'edges': [{'source': e[0], 'target': e[1], **graph.edges[e]} for e in graph.edges()]
    }
    
    return Response(network_data)

@api_view(['POST'])
def generate_process_map(request):
    """Genera mapa de proceso con IA"""
    mapper = ProcessMapper()
    process_data = request.data
    
    process_map = mapper.map_process(process_data)
    
    # Guardar en BD
    ProcessMap.objects.update_or_create(
        process_id=process_data['id'],
        defaults={'process_data': process_map, 'process_name': process_data['nombre']}
    )
    
    return Response(process_map)

@api_view(['GET'])
def get_risk_matrix_consolidated(request):
    """Retorna matriz de riesgos consolidada desde todos los módulos"""
    risks = RiskMatrix.objects.filter(status='active').values()
    
    # Agrupar por módulo origen
    consolidated = {
        'SCA': [r for r in risks if r['source_module'] == 'SCA'],
        'SIE': [r for r in risks if r['source_module'] == 'SIE'],
        'SPM': [r for r in risks if r['source_module'] == 'SPM']
    }
    
    return Response(consolidated)