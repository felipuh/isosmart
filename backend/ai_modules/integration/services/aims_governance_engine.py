"""ISO/IEC 42001 AIMS governance heuristics for AI oversight endpoints."""

from ai_modules.common.base import AIModuleBase


class AIMSGovernanceService(AIModuleBase):
    def __init__(self):
        super().__init__('aims_governance')

    def process(self, data):
        operation = (data or {}).get('operation', '')
        handlers = {
            'aims_overview': self.aims_overview,
            'model_lifecycle_check': self.model_lifecycle_check,
            'risk_register': self.risk_register,
            'audit_log_digest': self.audit_log_digest,
        }
        handler = handlers.get(operation)
        if not handler:
            return {'status': 'error', 'message': f'Operacion no soportada: {operation}'}
        return handler(data or {})

    def aims_overview(self, data):
        models = data.get('models') or []
        risks = data.get('risks') or []
        controls = data.get('controls') or []

        lifecycle_coverage = round((sum(1 for m in models if m.get('has_lifecycle_record')) / len(models)) * 100, 1) if models else 0
        risk_coverage = round((sum(1 for r in risks if r.get('has_treatment')) / len(risks)) * 100, 1) if risks else 0
        control_maturity = round((sum(1 for c in controls if c.get('implemented')) / len(controls)) * 100, 1) if controls else 0

        return {
            'status': 'overview_ready',
            'framework': 'ISO/IEC 42001:2023',
            'kpis': {
                'lifecycle_coverage': lifecycle_coverage,
                'risk_coverage': risk_coverage,
                'control_maturity': control_maturity,
            },
            'recommended_actions': [
                'Formalizar registro de ciclo de vida para todo modelo en produccion.',
                'Alinear riesgos de IA con tratamiento documentado y responsable asignado.',
                'Asegurar controles de explicabilidad, sesgo y trazabilidad para auditoria.',
            ],
        }

    def model_lifecycle_check(self, data):
        models = data.get('models') or []
        findings = []
        for item in models:
            gaps = []
            if not item.get('owner'):
                gaps.append('falta responsable del modelo')
            if not item.get('has_validation_report'):
                gaps.append('falta reporte de validacion')
            if not item.get('has_monitoring_plan'):
                gaps.append('falta plan de monitoreo post-despliegue')

            findings.append({
                'model_id': item.get('id'),
                'model_name': item.get('name'),
                'gaps': gaps,
                'status': 'needs_attention' if gaps else 'compliant',
            })

        return {
            'status': 'lifecycle_check_ready',
            'models': findings,
        }

    def risk_register(self, data):
        risks = data.get('risks') or []
        ranked = []
        for item in risks:
            likelihood = int(item.get('likelihood') or 1)
            impact = int(item.get('impact') or 1)
            score = likelihood * impact
            ranked.append({
                'risk_id': item.get('id'),
                'title': item.get('title'),
                'score': score,
                'level': 'high' if score >= 12 else 'medium' if score >= 6 else 'low',
            })

        ranked.sort(key=lambda row: row['score'], reverse=True)
        return {
            'status': 'risk_register_ready',
            'risks': ranked,
            'top_risks': ranked[:5],
        }

    def audit_log_digest(self, data):
        events = data.get('events') or []
        incidents = [e for e in events if e.get('type') in ['bias_alert', 'safety_incident', 'privacy_event']]
        return {
            'status': 'digest_ready',
            'summary': {
                'total_events': len(events),
                'high_relevance_events': len(incidents),
            },
            'alerts': incidents[:10],
        }
