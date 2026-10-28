"""
Seed data for Improvement module (Clause 10)
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from improvement.models import Nonconformity, CorrectiveAction, ContinualImprovement


class Command(BaseCommand):
    help = 'Seed improvement data for demo'

    def add_arguments(self, parser):
        parser.add_argument('--org-id', type=int, default=1)
        parser.add_argument('--org-name', type=str, default='Organizacion Demo')

    def handle(self, *args, **options):
        organization_id = options['org_id']
        organization_name = options['org_name']
        today = date.today()

        self.stdout.write('Seeding Improvement data...')

        ncs_data = [
            {
                'nc_number': 'NC-2026-001',
                'title': 'Registros de calibracion incompletos',
                'description': 'Se encontraron registros de calibracion sin firmas en el area de produccion.',
                'source': 'internal_audit',
                'detection_date': today - timedelta(days=30),
                'severity': 'major',
                'affected_process': 'Produccion',
                'iso_clause_reference': '7.1.5',
                'impact_description': 'Riesgo de mediciones inexactas en control de calidad.',
                'immediate_action_taken': 'Se detuvieron mediciones con equipos afectados.',
                'containment_measures': 'Verificacion manual de todas las mediciones del ultimo mes.',
                'status': 'action_plan',
                'target_closure_date': today + timedelta(days=15),
            },
            {
                'nc_number': 'NC-2026-002',
                'title': 'Queja de cliente por entrega tardia',
                'description': 'Cliente reporto entrega 5 dias despues de la fecha acordada.',
                'source': 'customer_complaint',
                'detection_date': today - timedelta(days=15),
                'severity': 'minor',
                'affected_process': 'Logistica',
                'iso_clause_reference': '8.2',
                'impact_description': 'Insatisfaccion del cliente. Riesgo de perder contrato.',
                'immediate_action_taken': 'Disculpa formal al cliente y envio express.',
                'containment_measures': 'Revision de todos los pedidos pendientes.',
                'status': 'implementing',
                'target_closure_date': today + timedelta(days=7),
            },
            {
                'nc_number': 'NC-2026-003',
                'title': 'Falla critica en proceso de soldadura',
                'description': 'Se detectaron uniones defectuosas en lote B-2026-045.',
                'source': 'product_inspection',
                'detection_date': today - timedelta(days=5),
                'severity': 'critical',
                'affected_process': 'Manufactura - Soldadura',
                'iso_clause_reference': '8.5.1',
                'impact_description': 'Lote completo rechazado. Posible riesgo de seguridad del producto.',
                'immediate_action_taken': 'Cuarentena del lote completo.',
                'containment_measures': 'Inspeccion 100% de lotes en proceso.',
                'status': 'analysis',
                'target_closure_date': today + timedelta(days=30),
            },
        ]

        nc_objects = []
        for data in ncs_data:
            nc, _ = Nonconformity.objects.update_or_create(
                organization_id=organization_id,
                nc_number=data['nc_number'],
                defaults={**data, 'organization_name': organization_name},
            )
            nc_objects.append(nc)
            self.stdout.write(f'  NC: {nc.nc_number} - {nc.title}')

        actions_data = [
            {
                'nonconformity': nc_objects[0],
                'action_number': 'AC-2026-001',
                'action_type': 'corrective',
                'root_cause_analysis': '5 Porques: 1) Registros incompletos 2) No hay checklist obligatorio 3) Procedimiento no exige firma al momento 4) Falta de capacitacion 5) No existe control sistematico.',
                'root_cause_identified': 'Falta de procedimiento estandarizado para firma inmediata de registros de calibracion.',
                'analysis_method': '5 Porques',
                'action_description': 'Implementar checklist digital obligatorio con firma electronica para registros de calibracion.',
                'implementation_steps': '1. Disenar formato digital\n2. Capacitar personal\n3. Implementar en sistema\n4. Verificar cumplimiento',
                'resources_required': 'Sistema digital de firmas, 8 horas de capacitacion.',
                'planned_start_date': today - timedelta(days=10),
                'planned_completion_date': today + timedelta(days=20),
                'verification_method': 'Auditoria de registros al 100% durante 30 dias.',
                'effectiveness_criteria': '0 registros sin firma durante 30 dias consecutivos.',
                'status': 'in_progress',
                'completion_percentage': 45,
            },
            {
                'nonconformity': nc_objects[2],
                'action_number': 'AC-2026-002',
                'action_type': 'corrective',
                'root_cause_analysis': 'Diagrama de Ishikawa: Causa principal en parametros de maquina desactualizados tras mantenimiento preventivo.',
                'root_cause_identified': 'Parametros de soldadura no recalibrados despues del mantenimiento preventivo del equipo.',
                'analysis_method': 'Diagrama de Ishikawa',
                'action_description': 'Establecer procedimiento obligatorio de recalibracion post-mantenimiento.',
                'implementation_steps': '1. Documentar procedimiento\n2. Agregar al plan de mantenimiento\n3. Capacitar tecnicos\n4. Verificar implementacion',
                'resources_required': 'Equipo de calibracion, 4 horas de capacitacion por tecnico.',
                'planned_start_date': today - timedelta(days=3),
                'planned_completion_date': today + timedelta(days=25),
                'verification_method': 'Inspeccion de primeras piezas post-mantenimiento.',
                'effectiveness_criteria': '0 defectos de soldadura en 3 lotes consecutivos post-implementacion.',
                'status': 'planned',
                'completion_percentage': 10,
            },
        ]

        for data in actions_data:
            action, _ = CorrectiveAction.objects.update_or_create(
                organization_id=organization_id,
                action_number=data['action_number'],
                defaults=data,
            )
            self.stdout.write(f'  AC: {action.action_number}')

        improvements_data = [
            {
                'initiative_number': 'MI-2026-001',
                'title': 'Automatizacion de control de calidad visual',
                'description': 'Implementar sistema de vision artificial para inspeccion de productos terminados.',
                'improvement_type': 'technology',
                'current_situation': 'Inspeccion visual manual con tasa de error del 3%.',
                'proposed_improvement': 'Sistema de vision artificial con IA para deteccion automatica de defectos.',
                'expected_benefits': 'Reduccion de tasa de error al 0.5%, aumento de velocidad de inspeccion en 400%.',
                'alignment_with_objectives': 'Objetivo de calidad OBJ-001: Reducir defectos.',
                'estimated_investment': Decimal('25000.00'),
                'estimated_savings': Decimal('45000.00'),
                'expected_roi': Decimal('80.00'),
                'priority': 'high',
                'proposed_date': today - timedelta(days=20),
                'status': 'approved',
                'completion_percentage': 15,
            },
            {
                'initiative_number': 'MI-2026-002',
                'title': 'Programa de mejora en tiempos de entrega',
                'description': 'Optimizar cadena de suministro para reducir tiempos de entrega en un 20%.',
                'improvement_type': 'process',
                'current_situation': 'Tiempo promedio de entrega: 12 dias.',
                'proposed_improvement': 'Renegociar con proveedores, implementar kanban para inventario critico.',
                'expected_benefits': 'Reduccion de tiempo de entrega a 9.5 dias, mejora de satisfaccion de cliente.',
                'alignment_with_objectives': 'Objetivo OBJ-002: Mejorar entrega a tiempo.',
                'estimated_investment': Decimal('8000.00'),
                'estimated_savings': Decimal('15000.00'),
                'expected_roi': Decimal('87.50'),
                'priority': 'medium',
                'proposed_date': today - timedelta(days=10),
                'status': 'in_progress',
                'completion_percentage': 35,
            },
        ]

        for data in improvements_data:
            improvement, _ = ContinualImprovement.objects.update_or_create(
                organization_id=organization_id,
                initiative_number=data['initiative_number'],
                defaults={**data, 'organization_name': organization_name},
            )
            self.stdout.write(f'  MI: {improvement.initiative_number} - {improvement.title}')

        self.stdout.write(self.style.SUCCESS(
            f'\nImprovement seed data created: {len(ncs_data)} NCs, {len(actions_data)} Actions, {len(improvements_data)} Improvements'
        ))