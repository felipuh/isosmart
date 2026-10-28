"""AI services for ISO 9001 clause 10 improvement workflows."""

from ai_modules.common.base import AIModuleBase


class ImprovementAIService(AIModuleBase):
    def __init__(self):
        super().__init__('improvement')

    def process(self, data):
        operation = (data or {}).get('operation', '')
        handlers = {
            'cockpit_summary': self.cockpit_summary,
            'root_cause_intelligence': self.root_cause_intelligence,
            'corrective_tracker': self.corrective_tracker,
            'continual_optimizer': self.continual_optimizer,
        }
        handler = handlers.get(operation)
        if not handler:
            return {'status': 'error', 'message': f'Operacion no soportada: {operation}'}
        return handler(data or {})

    def cockpit_summary(self, data):
        kpis = data.get('kpis') or {}
        critical_nc = (kpis.get('nonconformities') or {}).get('critical', 0)
        overdue_actions = (kpis.get('corrective_actions') or {}).get('overdue', 0)
        success = (kpis.get('improvements') or {}).get('successful', 0)

        maturity = 'controlled'
        if critical_nc > 0 or overdue_actions > 3:
            maturity = 'at_risk'
        elif success > 0:
            maturity = 'improving'

        return {
            'status': 'cockpit_ready',
            'maturity': maturity,
            'alerts': [
                f'{critical_nc} no conformidades criticas requieren contencion inmediata.' if critical_nc else 'Sin no conformidades criticas activas.',
                f'{overdue_actions} acciones correctivas vencidas.' if overdue_actions else 'Sin acciones correctivas vencidas.',
            ],
        }

    def root_cause_intelligence(self, data):
        nonconformities = data.get('nonconformities') or []
        suggestions = []
        source_map = {
            'internal_audit': 'Falla de estandarizacion o implementacion parcial de controles.',
            'customer_complaint': 'Brecha de requisito del cliente o validacion tardia de salida.',
            'process_monitoring': 'Variacion no controlada del proceso y seguimiento insuficiente.',
            'product_inspection': 'Especificacion tecnica no asegurada en produccion.',
            'supplier_issue': 'Control insuficiente de proveedor externo y criterios de recepcion.',
        }

        for nc in nonconformities[:10]:
            source = nc.get('source')
            suggestions.append({
                'nc_id': nc.get('id'),
                'nc_number': nc.get('nc_number'),
                'suggested_cause': source_map.get(source, 'Causa multifactorial pendiente de validacion estructurada.'),
                'analysis_method': '5 Whys + Ishikawa',
            })

        return {
            'status': 'analysis_ready',
            'suggestions': suggestions,
        }

    def corrective_tracker(self, data):
        actions = data.get('actions') or []
        overdue = [a for a in actions if a.get('is_overdue')]
        low_progress = [a for a in actions if (a.get('completion_percentage') or 0) < 50 and a.get('status') == 'in_progress']

        return {
            'status': 'tracking_ready',
            'summary': {
                'total_actions': len(actions),
                'overdue': len(overdue),
                'low_progress': len(low_progress),
            },
            'recommended_actions': [
                'Escalar acciones vencidas al responsable de proceso y comite de calidad.',
                'Aplicar seguimiento semanal a acciones con progreso menor al 50%.',
            ],
        }

    def continual_optimizer(self, data):
        initiatives = data.get('initiatives') or []
        prioritized = []
        for item in initiatives:
            score = 0
            if item.get('priority') == 'critical':
                score += 50
            elif item.get('priority') == 'high':
                score += 35
            if item.get('status') in ['approved', 'in_progress']:
                score += 25
            if item.get('status') == 'successful':
                score -= 10

            prioritized.append({
                'initiative_id': item.get('id'),
                'initiative_number': item.get('initiative_number'),
                'optimization_score': max(0, min(score, 100)),
            })

        prioritized.sort(key=lambda row: row['optimization_score'], reverse=True)
        return {
            'status': 'optimization_ready',
            'prioritized_initiatives': prioritized,
            'next_wave': prioritized[:5],
        }
