from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
User = get_user_model()
from core.models import (
    Document, StakeholderProfile, ScopeElement, ProcessMap,
    RiskMatrix, QualityObjective
)
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Popula la base de datos con datos de prueba'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creando datos de prueba...')
        
        # Crear usuario admin si no existe
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@isosmart.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('✓ Usuario admin creado'))
        
        # Crear documentos de prueba
        docs = [
            {
                'title': 'Acta de Reunión Gerencial Q4 2025',
                'document_type': 'acta',
                'content': 'Logramos mejorar la eficiencia del proceso de compras en un 20%. Se identificó la necesidad de capacitación adicional en el equipo de ventas.',
                'source': 'Gerencia General'
            },
            {
                'title': 'Reporte de Auditoría Interna',
                'document_type': 'reporte',
                'content': 'Se identificó un riesgo en el proceso de aprobación de órdenes de compra. Tiempo de ciclo promedio: 72 horas.',
                'source': 'Auditoría Interna'
            },
            {
                'title': 'Política de Calidad 2025',
                'document_type': 'politica',
                'content': 'Nuestra organización se compromete a la mejora continua y la satisfacción del cliente mediante procesos eficientes.',
                'source': 'Dirección'
            }
        ]
        
        for doc_data in docs:
            Document.objects.get_or_create(
                title=doc_data['title'],
                defaults=doc_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(docs)} documentos creados'))
        
        # Crear stakeholders de prueba
        stakeholders = [
            {
                'name': 'Cliente ABC Corp',
                'stakeholder_type': 'cliente',
                'influence_score': 0.95,
                'power': 'alto',
                'interest': 'alto',
                'expectations': ['Entrega en 7 días', 'Calidad certificada', 'Soporte 24/7'],
                'satisfaction_score': 4.2
            },
            {
                'name': 'Proveedor XYZ',
                'stakeholder_type': 'proveedor',
                'influence_score': 0.75,
                'power': 'medio',
                'interest': 'alto',
                'expectations': ['Pagos puntuales', 'Órdenes claras'],
                'satisfaction_score': 4.5
            },
            {
                'name': 'Ministerio de Salud',
                'stakeholder_type': 'regulador',
                'influence_score': 0.90,
                'power': 'alto',
                'interest': 'medio',
                'expectations': ['Cumplimiento normativo', 'Reportes mensuales'],
                'satisfaction_score': 4.0
            }
        ]
        
        for sh_data in stakeholders:
            StakeholderProfile.objects.get_or_create(
                name=sh_data['name'],
                defaults=sh_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(stakeholders)} stakeholders creados'))
        
        # Crear elementos de alcance
        scope_elements = [
            {
                'process_id': 'PROC-001',
                'process_name': 'Gestión de Ventas',
                'included': True,
                'process_type': 'core',
                'iso_clauses_covered': ['8.2', '8.3', '8.5']
            },
            {
                'process_id': 'PROC-002',
                'process_name': 'Compras y Adquisiciones',
                'included': True,
                'process_type': 'core',
                'iso_clauses_covered': ['8.4']
            },
            {
                'process_id': 'PROC-003',
                'process_name': 'Recursos Humanos',
                'included': True,
                'process_type': 'soporte',
                'iso_clauses_covered': ['7.1', '7.2', '7.3']
            },
            {
                'process_id': 'PROC-004',
                'process_name': 'Gestión de Calidad',
                'included': True,
                'process_type': 'estrategico',
                'iso_clauses_covered': ['5.1', '5.2', '5.3', '9.1', '9.2', '9.3']
            }
        ]
        
        for scope_data in scope_elements:
            ScopeElement.objects.get_or_create(
                process_id=scope_data['process_id'],
                defaults=scope_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(scope_elements)} elementos de alcance creados'))
        
        # Crear mapas de procesos
        process_maps = [
            {
                'process_id': 'PROC-001',
                'process_name': 'Gestión de Ventas',
                'owner': 'Juan Pérez - Gerente Comercial',
                'health_status': 'healthy',
                'process_data': {
                    'actividades': ['Prospección', 'Cotización', 'Negociación', 'Cierre'],
                    'entradas': ['Lead', 'Requisitos del cliente'],
                    'salidas': ['Contrato firmado', 'Orden de venta']
                },
                'predicted_risks': [
                    {
                        'description': 'Tiempo de respuesta a cotizaciones superior a 48h',
                        'probability': 'media',
                        'impact': 'medio',
                        'level': 'medio'
                    }
                ],
                'generated_kpis': [
                    {'nombre': 'Tiempo de ciclo de venta', 'valor_actual': 15, 'unidad': 'días', 'meta': 10},
                    {'nombre': 'Tasa de conversión', 'valor_actual': 35, 'unidad': '%', 'meta': 45}
                ]
            },
            {
                'process_id': 'PROC-002',
                'process_name': 'Compras y Adquisiciones',
                'owner': 'María González - Gerente de Compras',
                'health_status': 'warning',
                'process_data': {
                    'actividades': ['Requisición', 'Cotización', 'Aprobación', 'Orden de compra'],
                    'entradas': ['Requisición de compra'],
                    'salidas': ['Orden de compra aprobada']
                },
                'predicted_risks': [
                    {
                        'description': 'Proceso de aprobación con múltiples cuellos de botella',
                        'probability': 'alta',
                        'impact': 'alto',
                        'level': 'alto'
                    }
                ],
                'generated_kpis': [
                    {'nombre': 'Tiempo de ciclo OC', 'valor_actual': 72, 'unidad': 'horas', 'meta': 48},
                    {'nombre': 'Órdenes rechazadas', 'valor_actual': 8, 'unidad': '%', 'meta': 3}
                ]
            }
        ]
        
        for pm_data in process_maps:
            ProcessMap.objects.get_or_create(
                process_id=pm_data['process_id'],
                defaults=pm_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(process_maps)} mapas de procesos creados'))
        
        # Crear riesgos de prueba
        risks = [
            {
                'source_module': 'SCA',
                'risk_description': 'Nuevo decreto BCCR sobre reportería financiera trimestral',
                'risk_category': 'regulatory',
                'probability': 'alta',
                'impact': 'alto',
                'risk_level': 'critico',
                'mitigation_actions': '1. Evaluar capacidad actual\n2. Ajustar proceso de reportería\n3. Capacitar equipo',
                'responsible': 'Director Financiero',
                'iso_clause': '4.1',
                'deadline': datetime.now().date() + timedelta(days=90)
            },
            {
                'source_module': 'SPM',
                'source_id': 1,
                'risk_description': 'Tiempo de ciclo de compras excede estándar de industria',
                'risk_category': 'process',
                'probability': 'alta',
                'impact': 'medio',
                'risk_level': 'alto',
                'mitigation_actions': 'Implementar sistema de aprobaciones automatizado',
                'responsible': 'Gerente de Compras',
                'iso_clause': '4.4',
                'process_id': 'PROC-002',
                'deadline': datetime.now().date() + timedelta(days=60)
            },
            {
                'source_module': 'SIE',
                'risk_description': 'Cliente ABC Corp ha cambiado expectativas de entrega',
                'risk_category': 'stakeholder',
                'probability': 'alta',
                'impact': 'alto',
                'risk_level': 'critico',
                'mitigation_actions': 'Reunión urgente con cliente para alineación de expectativas',
                'responsible': 'Gerente Comercial',
                'iso_clause': '4.2',
                'deadline': datetime.now().date() + timedelta(days=15)
            }
        ]
        
        for risk_data in risks:
            RiskMatrix.objects.get_or_create(
                risk_description=risk_data['risk_description'],
                defaults=risk_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(risks)} riesgos creados'))
        
        # Crear objetivos de calidad
        objectives = [
            {
                'source_module': 'SPM',
                'objective_description': 'Reducir tiempo de ciclo de órdenes de compra',
                'indicator_name': 'Tiempo promedio ciclo OC',
                'measurement_unit': 'horas',
                'baseline_value': 72.0,
                'target_value': 48.0,
                'current_value': 68.0,
                'measurement_frequency': 'mensual',
                'responsible': 'María González',
                'deadline': datetime.now().date() + timedelta(days=180),
                'process_id': 'PROC-002'
            },
            {
                'source_module': 'SCA',
                'objective_description': 'Mejorar eficiencia del proceso de ventas',
                'indicator_name': 'Tasa de conversión',
                'measurement_unit': '%',
                'baseline_value': 35.0,
                'target_value': 45.0,
                'current_value': 38.0,
                'measurement_frequency': 'mensual',
                'responsible': 'Juan Pérez',
                'deadline': datetime.now().date() + timedelta(days=365),
                'process_id': 'PROC-001'
            },
            {
                'source_module': 'MANUAL',
                'objective_description': 'Aumentar satisfacción del cliente',
                'indicator_name': 'NPS (Net Promoter Score)',
                'measurement_unit': 'puntos',
                'baseline_value': 65.0,
                'target_value': 80.0,
                'current_value': 70.0,
                'measurement_frequency': 'trimestral',
                'responsible': 'Director General',
                'deadline': datetime.now().date() + timedelta(days=365)
            }
        ]
        
        for obj_data in objectives:
            QualityObjective.objects.get_or_create(
                indicator_name=obj_data['indicator_name'],
                defaults=obj_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(objectives)} objetivos de calidad creados'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Datos de prueba creados exitosamente'))