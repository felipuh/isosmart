"""AI services for ISO 9001 clause 9 performance evaluation workflows."""

from ai_modules.common.base import AIModuleBase


class PerformanceAIService(AIModuleBase):
    def __init__(self):
        super().__init__('performance')

    def process(self, data):
        operation = (data or {}).get('operation', '')
        handlers = {
            'cockpit_summary': self.cockpit_summary,
            'indicator_drift': self.indicator_drift,
            'audit_assistant': self.audit_assistant,
            'executive_review_brief': self.executive_review_brief,
        }
        handler = handlers.get(operation)
        if not handler:
            return {'status': 'error', 'message': f'Operacion no soportada: {operation}'}
        return handler(data or {})

    def cockpit_summary(self, data):
        kpis = data.get('kpis') or {}
        needs_attention = (kpis.get('measurements') or {}).get('needs_attention', 0)
        open_findings = (kpis.get('findings') or {}).get('open', 0)

        priority = 'stable'
        if open_findings >= 5 or needs_attention >= 8:
            priority = 'critical'
        elif open_findings >= 2 or needs_attention >= 3:
            priority = 'warning'

        alerts = []
        if needs_attention:
            alerts.append(f'{needs_attention} mediciones requieren analisis y accion de contencion.')
        if open_findings:
            alerts.append(f'{open_findings} hallazgos de auditoria permanecen abiertos.')

        return {
            'status': 'cockpit_ready',
            'priority': priority,
            'alerts': alerts,
            'recommended_focus': [
                'Cerrar brechas de medicion con tendencias negativas consecutivas.',
                'Priorizar hallazgos mayores o con fecha vencida.',
                'Llevar riesgos de desempeno a revision por la direccion.',
            ],
        }

    def indicator_drift(self, data):
        measurements = data.get('measurements') or []
        total = len(measurements)
        below = sum(1 for item in measurements if item.get('status') in ['below_target', 'needs_attention'])
        drift = round((below / total) * 100, 1) if total else 0

        trend = 'positive'
        if drift >= 45:
            trend = 'negative'
        elif drift >= 20:
            trend = 'neutral'

        return {
            'status': 'analysis_ready',
            'drift_percentage': drift,
            'trend': trend,
            'suggested_actions': [
                'Revisar metas no realistas y recalibrar indicadores desalineados.',
                'Aplicar analisis de causa en indicadores por debajo de meta dos periodos consecutivos.',
            ],
        }

    def audit_assistant(self, data):
        findings = data.get('findings') or []
        prioritized = []
        for item in findings:
            score = 0
            f_type = item.get('finding_type')
            if f_type == 'nc_major':
                score += 50
            elif f_type == 'nc_minor':
                score += 30
            elif f_type == 'observation':
                score += 10
            if item.get('status') == 'open':
                score += 20

            prioritized.append({
                'finding_id': item.get('id'),
                'finding_number': item.get('finding_number'),
                'priority_score': min(score, 100),
            })

        prioritized.sort(key=lambda row: row['priority_score'], reverse=True)
        return {
            'status': 'prioritization_ready',
            'findings': prioritized,
            'top_priority': prioritized[:5],
        }

    def executive_review_brief(self, data):
        reviews = data.get('reviews') or []
        open_actions = sum(1 for item in reviews if item.get('status') in ['scheduled', 'in_progress'])
        completed = sum(1 for item in reviews if item.get('status') == 'completed')

        return {
            'status': 'brief_ready',
            'summary': {
                'total_reviews': len(reviews),
                'completed_reviews': completed,
                'open_reviews': open_actions,
            },
            'brief': [
                'Validar cumplimiento de acciones de revision por la direccion.',
                'Conectar decisiones con riesgos, recursos y objetivos de calidad.',
                'Confirmar evidencia de seguimiento para auditoria externa.',
            ],
        }
