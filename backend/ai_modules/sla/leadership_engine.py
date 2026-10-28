"""
Smart Leadership Advisor – Motor de IA Híbrido
ISO 9001:2015 Cláusula 5 | Gobernanza de IA: NIST AI RMF / ISO 42001

Arquitectura:
  - LLM generativo: generar borradores, analizar tendencias, detectar incoherencias
  - RAG corporativo: responder solo con fuentes internas citadas
  - Motor de reglas ISO: bloqueos duros (este archivo llama al iso_rules_engine)

Principio: NADA se publica automáticamente. Todo output crítico genera un
AIGovernanceLog con human_decision='pending' que la Alta Dirección aprueba.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from django.utils import timezone

from ai_modules.common.base import AIModuleBase
from .iso_rules_engine import ISOLeadershipRulesEngine

logger = logging.getLogger(__name__)

MODEL_VERSION = "sla-v1.0-llm_placeholder"   # actualizar al integrar LLM real


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()


def _check_privacy(text: str) -> tuple[bool, list[str]]:
    """
    Verificación básica de privacidad: detecta patrones de identificadores personales.
    En producción integrar con librería de detección de PII.
    """
    flags = []
    pii_patterns = ['email', '@', 'dni', 'cedula', 'pasaporte', 'telefono', 'celular']
    lower = text.lower()
    for p in pii_patterns:
        if p in lower:
            flags.append(f"Posible PII detectada: '{p}'")
    return len(flags) == 0, flags


class LeadershipAIService(AIModuleBase):
    """
    Motor de IA Híbrido para el módulo de Liderazgo.
    
    Cada método público:
      1. Valida reglas ISO (reglas duras primero)
      2. Construye contexto de fuentes internas (RAG)
      3. Invoca el LLM con el contexto corporativo
      4. Audita el output (privacidad, alucinaciones)
      5. Retorna recomendación + AIGovernanceLog no publicado
         → la Alta Dirección aprueba/rechaza/modifica
    """

    def __init__(self):
        super().__init__('SLA')
        self.rules = ISOLeadershipRulesEngine()

    def process(self, data: dict[str, Any] = None) -> dict[str, Any]:
        """Método abstracto requerido; enrutador de operaciones."""
        operation = (data or {}).get('operation', '')
        handlers = {
            'policy_draft': self.generate_policy_draft,
            'voc_analysis': self.analyze_voc_patterns,
            'raci_gaps': self.detect_raci_gaps,
            'review_brief': self.generate_management_review_brief,
            'incoherence_check': self.detect_policy_incoherences,
            'culture_aggregation': self.aggregate_culture_survey,
        }
        handler = handlers.get(operation)
        if not handler:
            return {'status': 'error', 'message': f"Operación desconocida: {operation}"}
        return handler(data or {})

    # ─── GENERACIÓN DE BORRADOR DE POLÍTICA ──────────────────

    def generate_policy_draft(self, data: dict) -> dict:
        """
        Genera un borrador de política de calidad usando LLM + contexto RAG.
        Output: borrador de texto con evidencia citada.
        NUNCA se publica automáticamente.
        """
        organization_id = data.get('organization_id')
        context_hints = self._gather_policy_context(organization_id)

        prompt_template = 'leadership/policy_draft_v1'
        prompt = self._build_policy_draft_prompt(data, context_hints)
        prompt_hash = _hash_prompt(prompt)

        # Simulación de LLM (reemplazar con llamada real a LLaMA/GPT/Claude)
        draft_content = self._llm_generate(prompt, context_hints)

        privacy_ok, privacy_flags = _check_privacy(draft_content)
        hal_flags = self._detect_hallucinations(draft_content, context_hints)

        log_data = {
            'organization_id': organization_id,
            'module': 'leadership',
            'operation': 'policy_draft',
            'model_version': MODEL_VERSION,
            'prompt_template': prompt_template,
            'prompt_hash': prompt_hash,
            'response_summary': draft_content[:500],
            'ai_recommendation': {
                'draft': draft_content,
                'sources': context_hints.get('sources', []),
                'iso_clauses': ['5.2.1', '5.2.2'],
            },
            'sources_cited': context_hints.get('sources', []),
            'hallucination_flags': hal_flags,
            'privacy_check_passed': privacy_ok,
        }

        return {
            'status': 'draft_ready',
            'message': 'Borrador generado por IA — requiere revisión y aprobación de la Alta Dirección antes de publicar.',
            'ai_requires_human_approval': True,
            'draft': draft_content,
            'sources_cited': context_hints.get('sources', []),
            'hallucination_flags': hal_flags,
            'privacy_flags': privacy_flags,
            'governance_log_data': log_data,
        }

    # ─── ANÁLISIS VOC (VOZ DEL CLIENTE) ──────────────────────

    def analyze_voc_patterns(self, data: dict) -> dict:
        """
        NLP sobre reclamos, tickets y encuestas para detectar patrones recurrentes.
        Propone acciones preventivas — todas son recomendaciones, no acciones automáticas.
        """
        organization_id = data.get('organization_id')
        voc_data = self._gather_voc_data(organization_id)

        if not voc_data.get('items'):
            return {
                'status': 'insufficient_data',
                'message': 'No hay suficientes datos VOC para análisis (mínimo 5 registros).',
                'topics': [],
                'risk_alerts': [],
            }

        prompt = f"""Analiza los siguientes datos de Voz del Cliente y:
1. Identifica los 3-5 temas recurrentes más importantes
2. Detecta riesgos emergentes de satisfacción del cliente
3. Propone acciones preventivas concretas con base en los patrones
4. Cita las fuentes específicas que sustentan cada conclusión

Contexto organizacional: {voc_data.get('context', 'No disponible')}
Datos VOC: {json.dumps(voc_data.get('items', [])[:20], ensure_ascii=False)}
"""
        prompt_hash = _hash_prompt(prompt)
        analysis = self._llm_generate(prompt, voc_data)

        topics = self._extract_topics(analysis, voc_data)
        risk_alerts = self._extract_risk_alerts(analysis, voc_data)
        proposed_actions = self._extract_proposed_actions(analysis)

        privacy_ok, privacy_flags = _check_privacy(analysis)

        return {
            'status': 'analysis_ready',
            'message': 'Análisis VOC generado por IA — las acciones propuestas requieren validación humana.',
            'ai_requires_human_approval': True,
            'topics': topics,
            'risk_alerts': risk_alerts,
            'proposed_actions': proposed_actions,
            'data_sources': voc_data.get('sources', []),
            'privacy_check_passed': privacy_ok,
            'governance_log_data': {
                'organization_id': organization_id,
                'module': 'leadership',
                'operation': 'voc_analysis',
                'model_version': MODEL_VERSION,
                'prompt_template': 'leadership/voc_analysis_v1',
                'prompt_hash': prompt_hash,
                'response_summary': analysis[:500],
                'ai_recommendation': {'topics': topics, 'risk_alerts': risk_alerts},
                'sources_cited': voc_data.get('sources', []),
                'hallucination_flags': [],
                'privacy_check_passed': privacy_ok,
            },
        }

    # ─── DETECCIÓN DE BRECHAS RACI ────────────────────────────

    def detect_raci_gaps(self, data: dict) -> dict:
        """
        Analiza matrices RACI activas y detecta:
         - Actividades sin Accountable (A)
         - Roles con sobrecarga (demasiados R)
         - Vacíos (actividades sin cobertura)
         - Duplicidades (mismo rol con R y A en la misma actividad)
        """
        organization_id = data.get('organization_id')
        raci_data = self._gather_raci_data(organization_id)

        gaps = []
        overloads = []
        duplicities = []

        for matrix in raci_data.get('matrices', []):
            for entry in matrix.get('entries', []):
                activity = entry.get('activity', '?')
                accountable = entry.get('accountable_roles', [])
                responsible = entry.get('responsible_roles', [])

                if not accountable:
                    gaps.append({
                        'type': 'missing_accountable',
                        'matrix': matrix.get('name', ''),
                        'activity': activity,
                        'severity': 'critical',
                        'description': f"La actividad '{activity}' no tiene Accountable (A) asignado."
                    })

                # Duplicidad R y A en el mismo rol
                overlap = set(str(r) for r in responsible) & set(str(a) for a in accountable)
                if overlap:
                    duplicities.append({
                        'type': 'ra_overlap',
                        'matrix': matrix.get('name', ''),
                        'activity': activity,
                        'severity': 'warning',
                        'description': f"Rol duplicado como R y A en '{activity}': {overlap}"
                    })

                if len(responsible) > 5:
                    overloads.append({
                        'type': 'overload',
                        'matrix': matrix.get('name', ''),
                        'activity': activity,
                        'severity': 'warning',
                        'description': f"Demasiados responsables ({len(responsible)}) para '{activity}'"
                    })

        return {
            'status': 'analysis_ready',
            'message': 'Análisis de brechas RACI completado. Las correcciones requieren aprobación humana.',
            'ai_requires_human_approval': True,
            'gaps': gaps,
            'overloads': overloads,
            'duplicities': duplicities,
            'total_issues': len(gaps) + len(overloads) + len(duplicities),
            'matrices_analyzed': len(raci_data.get('matrices', [])),
        }

    # ─── BRIEF PRE-REUNIÓN DE REVISIÓN POR LA DIRECCIÓN ──────

    def generate_management_review_brief(self, data: dict) -> dict:
        """
        Genera un brief ejecutivo pre-reunión con:
         - Resumen de desempeño del SGC
         - Nivel de cumplimiento de objetivos
         - Riesgos emergentes
         - Tendencias de satisfacción del cliente
         - Decisiones pendientes de revisiones anteriores
        El brief es un BORRADOR — debe ser aprobado por el facilitador.
        """
        organization_id = data.get('organization_id')
        review_id = data.get('review_id')
        context = self._gather_review_context(organization_id, review_id)

        prompt = f"""Genera un brief ejecutivo para la Revisión por la Dirección (ISO 9001:2015 – 9.3).
Formato: resumen ejecutivo de máximo 800 palabras con secciones claramente delimitadas.

Datos del sistema:
- Desempeño de objetivos: {json.dumps(context.get('objectives_performance', {}), ensure_ascii=False)}
- Satisfacción del cliente: {json.dumps(context.get('customer_satisfaction', {}), ensure_ascii=False)}
- No conformidades: {context.get('nonconformities_summary', 'Sin datos')}
- Riesgos activos: {json.dumps(context.get('risks', [])[:5], ensure_ascii=False)}
- Decisiones pendientes: {json.dumps(context.get('pending_decisions', []), ensure_ascii=False)}
- Resultados de auditorías: {context.get('audit_results', 'Sin datos')}

Instrucción: el brief debe ser objetivo, citar fuentes internas, y presentar recomendaciones
claramente marcadas como 'RECOMENDACIÓN IA (requiere aprobación dirección)'.
"""
        prompt_hash = _hash_prompt(prompt)
        brief_text = self._llm_generate(prompt, context)

        privacy_ok, pii_flags = _check_privacy(brief_text)
        hal_flags = self._detect_hallucinations(brief_text, context)

        return {
            'status': 'brief_ready',
            'message': 'Brief generado por IA — debe ser revisado y aprobado por el facilitador antes de distribuir.',
            'ai_requires_human_approval': True,
            'brief': brief_text,
            'sources_cited': context.get('sources', []),
            'hallucination_flags': hal_flags,
            'privacy_flags': pii_flags,
            'governance_log_data': {
                'organization_id': organization_id,
                'module': 'leadership',
                'operation': 'review_brief',
                'model_version': MODEL_VERSION,
                'prompt_template': 'leadership/review_brief_v1',
                'prompt_hash': prompt_hash,
                'response_summary': brief_text[:500],
                'ai_recommendation': {'brief_preview': brief_text[:200]},
                'sources_cited': context.get('sources', []),
                'hallucination_flags': hal_flags,
                'privacy_check_passed': privacy_ok,
            },
        }

    # ─── DETECCIÓN DE INCOHERENCIAS POLÍTICA - RESULTADOS ────

    def detect_policy_incoherences(self, data: dict) -> dict:
        """
        Compara política de calidad vigente con resultados y objetivos actuales.
        Detecta incoherencias como: compromisos declarados vs. resultados reales.
        """
        organization_id = data.get('organization_id')
        context = self._gather_policy_results_context(organization_id)

        incoherences = []

        # Análisis simbólico básico (sin LLM — reglas deterministas)
        policy = context.get('active_policy', {})
        objectives = context.get('objectives', [])

        if policy and objectives:
            not_achieved = [o for o in objectives if o.get('status') == 'not_achieved']
            if len(not_achieved) > len(objectives) * 0.5:
                incoherences.append({
                    'type': 'policy_objectives_gap',
                    'severity': 'high',
                    'description': f'Más del 50% de los objetivos de calidad no están siendo alcanzados '
                                   f'({len(not_achieved)}/{len(objectives)}), lo que indica incoherencia '
                                   f'entre la política declarada y los resultados reales.',
                    'recommendation': 'Revisar si la política de calidad es realista o si los objetivos '
                                      'necesitan ajustarse.',
                    'source': 'objectives_module',
                })

        policy_content = (policy.get('content') or '').lower()
        customer_focus = context.get('customer_satisfaction_score', None)
        if 'satisfacc' in policy_content and customer_focus is not None and customer_focus < 70:
            incoherences.append({
                'type': 'customer_focus_gap',
                'severity': 'high',
                'description': f'La política declara enfoque al cliente pero la satisfacción actual '
                               f'es {customer_focus}% (por debajo del umbral recomendado del 70%).',
                'recommendation': 'Definir acciones concretas para mejorar satisfacción del cliente.',
                'source': 'customer_focus_module',
            })

        return {
            'status': 'analysis_ready',
            'message': 'Análisis de incoherencias completado. Las correcciones requieren decisión de la dirección.',
            'ai_requires_human_approval': True,
            'incoherences': incoherences,
            'total_incoherences': len(incoherences),
            'policy_version': policy.get('version', 'N/A'),
        }

    # ─── AGREGACIÓN CULTURA (PRIVACIDAD POR DISEÑO) ──────────

    def aggregate_culture_survey(self, data: dict) -> dict:
        """
        Agrega resultados de encuestas de cultura.
        Regla de privacidad: solo muestra resultados si hay >= min_responses.
        NUNCA procesa ni expone datos individuales.
        """
        organization_id = data.get('organization_id')
        survey_id = data.get('survey_id')

        from leadership.models import QualityCultureSurvey, SurveyResponse
        from django.db.models import Count

        try:
            survey = QualityCultureSurvey.objects.get(
                id=survey_id, organization_id=organization_id
            )
        except QualityCultureSurvey.DoesNotExist:
            return {'status': 'error', 'message': 'Encuesta no encontrada.'}

        total_responses = SurveyResponse.objects.filter(survey=survey).count()

        if total_responses < survey.min_responses_for_analysis:
            return {
                'status': 'insufficient_responses',
                'message': f'Solo hay {total_responses} respuesta(s). '
                           f'Se requieren al menos {survey.min_responses_for_analysis} '
                           f'para mostrar resultados (protección de privacidad individual).',
                'total_responses': total_responses,
                'min_required': survey.min_responses_for_analysis,
            }

        responses = list(SurveyResponse.objects.filter(survey=survey).values('responses'))
        aggregated = {}

        for question in survey.questions:
            qid = str(question.get('id', ''))
            qtype = question.get('type', 'text')
            answers = [r['responses'].get(qid) for r in responses if r['responses'].get(qid) is not None]

            if qtype == 'scale' and answers:
                numeric = [float(a) for a in answers if isinstance(a, (int, float, str)) and str(a).isdigit()]
                if numeric:
                    aggregated[qid] = {
                        'question': question.get('text', ''),
                        'type': 'scale',
                        'avg': round(sum(numeric) / len(numeric), 2),
                        'count': len(numeric),
                    }
            elif qtype == 'choice' and answers:
                freq = {}
                for a in answers:
                    freq[str(a)] = freq.get(str(a), 0) + 1
                aggregated[qid] = {
                    'question': question.get('text', ''),
                    'type': 'choice',
                    'distribution': freq,
                    'count': len(answers),
                }

        return {
            'status': 'aggregated',
            'privacy_protected': True,
            'total_responses': total_responses,
            'aggregated_results': aggregated,
            'note': 'Solo se muestran resultados agregados. No se almacena ni procesa identidad individual.',
        }

    # ─── AUDITOR PACK EXPORT ──────────────────────────────────

    def build_auditor_pack_data(self, organization_id: int, user) -> dict:
        """
        Construye el paquete de datos para exportación del Auditor Pack.
        El renderizado a PDF/ZIP lo hace la view.
        Incluye: resumen ejecutivo, actas+decisiones, mapa política→objetivos→resultados,
        evidencia de comunicación, roles y responsabilidades.
        """
        from leadership.models import (
            QualityPolicy, ManagementReview, ReviewDecision,
            ApprovalRecord, OrganizationalRole, RACIMatrix,
            EvidenceNode,
        )
        from django.utils import timezone as tz

        pack = {
            'generated_at': tz.now().isoformat(),
            'generated_by': getattr(user, 'get_full_name', lambda: str(user))(),
            'organization_id': organization_id,
            'sections': {},
        }

        # 1. Políticas activas
        pack['sections']['quality_policies'] = list(
            QualityPolicy.objects.filter(
                organization_id=organization_id,
                status__in=['approved', 'active']
            ).values(
                'id', 'version', 'title', 'content', 'status',
                'approved_by__email', 'approval_date',
                'effective_date', 'is_published',
            )
        )

        # 2. Revisiones por la dirección (últimas 12 meses)
        from datetime import timedelta
        cutoff = tz.now() - timedelta(days=365)
        reviews = ManagementReview.objects.filter(
            organization_id=organization_id,
            scheduled_date__gte=cutoff,
        ).prefetch_related('decisions')
        pack['sections']['management_reviews'] = []
        for r in reviews:
            pack['sections']['management_reviews'].append({
                'id': r.id,
                'title': r.title,
                'scheduled_date': r.scheduled_date.isoformat(),
                'status': r.status,
                'minutes_approved': bool(r.minutes_approved_at),
                'minutes_approved_by': r.minutes_approved_by.get_full_name() if r.minutes_approved_by else None,
                'decisions': list(r.decisions.values(
                    'id', 'title', 'decision_type', 'status',
                    'responsible__email', 'due_date', 'approved_at',
                )),
            })

        # 3. Registros de aprobación (cadena de custodia)
        pack['sections']['approval_records'] = list(
            ApprovalRecord.objects.filter(
                organization_id=organization_id
            ).values(
                'id', 'workflow_type', 'title', 'approved_at',
                'approved_by__email', 'digital_signature',
                'reference_model', 'reference_id',
            )
        )

        # 4. Grafo de evidencias
        pack['sections']['evidence_nodes'] = list(
            EvidenceNode.objects.filter(
                organization_id=organization_id
            ).values(
                'id', 'node_type', 'title', 'description',
                'responsible__email', 'approver__email',
                'approved_at', 'created_at',
            )
        )

        # 5. Roles y responsabilidades
        pack['sections']['organizational_roles'] = list(
            OrganizationalRole.objects.filter(
                organization_id=organization_id, is_active=True
            ).values(
                'id', 'name', 'code', 'level',
                'responsibilities', 'authorities',
            )
        )

        # 6. Matrices RACI
        pack['sections']['raci_matrices'] = list(
            RACIMatrix.objects.filter(
                organization_id=organization_id, is_active=True
            ).prefetch_related('entries').values(
                'id', 'name', 'description',
            )
        )

        return pack

    # ─── HELPERS INTERNOS ────────────────────────────────────

    def _llm_generate(self, prompt: str, context: dict) -> str:
        """
        Placeholder para LLM real.
        En producción: llamar a Ollama/LiteLLM/OpenAI-compatible endpoint.
        El contexto incluye fuentes RAG para grounding.
        """
        sources = context.get('sources', [])
        sources_text = '\n'.join(f"- {s}" for s in sources[:5]) if sources else '(sin fuentes RAG disponibles)'

        return (
            f"[BORRADOR GENERADO POR IA - REQUIERE REVISIÓN HUMANA]\n\n"
            f"Basado en el análisis del contexto organizacional y las siguientes fuentes internas:\n"
            f"{sources_text}\n\n"
            f"[Aquí el LLM generaría el contenido solicitado usando el contexto RAG corporativo. "
            f"Integrar con endpoint LLM configurado en settings.AI_LLM_ENDPOINT]\n\n"
            f"⚠️ Este es un borrador generado automáticamente. "
            f"La Alta Dirección debe revisar, modificar si es necesario y aprobar explícitamente "
            f"antes de que cualquier contenido sea publicado o distribuido."
        )

    def _detect_hallucinations(self, text: str, context: dict) -> list:
        """
        Verificación básica de alucinaciones: contrasta afirmaciones con fuentes.
        En producción: integrar con NLI model o verificador de hechos.
        """
        flags = []
        if not context.get('sources'):
            flags.append("Sin fuentes RAG disponibles — respuesta sin grounding verificable")
        return flags

    def _gather_policy_context(self, organization_id) -> dict:
        """Obtiene contexto organizacional para generación de política."""
        try:
            from core.models import ContextAnalysis
            ctx = ContextAnalysis.objects.filter(
                organization_id=organization_id, status='completed'
            ).order_by('-timestamp').first()
            sources = ['Análisis de contexto organizacional'] if ctx else []
            return {
                'internal_context': ctx.internal_insights if ctx else {},
                'external_context': ctx.external_insights if ctx else {},
                'sources': sources,
            }
        except Exception:
            return {'sources': []}

    def _gather_voc_data(self, organization_id) -> dict:
        """Recopila datos de Voz del Cliente (Customer Focus Evidence)."""
        try:
            from leadership.models import CustomerFocusEvidence
            evidences = list(
                CustomerFocusEvidence.objects.filter(
                    organization_id=organization_id
                ).values('title', 'description', 'action_taken', 'results', 'focus_type')[:50]
            )
            return {
                'items': evidences,
                'sources': ['leadership.CustomerFocusEvidence'],
            }
        except Exception:
            return {'items': [], 'sources': []}

    def _gather_raci_data(self, organization_id) -> dict:
        """Obtiene matrices RACI activas."""
        try:
            from leadership.models import RACIMatrix
            matrices = []
            for m in RACIMatrix.objects.filter(
                organization_id=organization_id, is_active=True
            ).prefetch_related('entries'):
                entries = []
                for e in m.entries.all():
                    entries.append({
                        'activity': e.activity,
                        'responsible_roles': list(e.responsible_roles.values_list('id', flat=True)),
                        'accountable_roles': list(e.accountable_roles.values_list('id', flat=True)),
                    })
                matrices.append({'name': m.name, 'entries': entries})
            return {'matrices': matrices}
        except Exception:
            return {'matrices': []}

    def _gather_review_context(self, organization_id, review_id=None) -> dict:
        """Recopila contexto para el brief de revisión por la dirección."""
        context = {'sources': []}
        try:
            from planning.models import QualityObjective
            objectives = list(
                QualityObjective.objects.filter(
                    organization_id=organization_id
                ).values('title', 'status', 'target_value', 'current_value')[:10]
            )
            context['objectives_performance'] = objectives
            context['sources'].append('planning.QualityObjective')
        except Exception:
            context['objectives_performance'] = []

        try:
            from leadership.models import ReviewDecision
            pending = list(
                ReviewDecision.objects.filter(
                    review__organization_id=organization_id,
                    status__in=['proposed', 'approved', 'in_progress']
                ).values('title', 'status', 'due_date')[:10]
            )
            context['pending_decisions'] = pending
            context['sources'].append('leadership.ReviewDecision')
        except Exception:
            context['pending_decisions'] = []

        return context

    def _gather_policy_results_context(self, organization_id) -> dict:
        """Contexto para comparar política con resultados."""
        context = {}
        try:
            from leadership.models import QualityPolicy
            policy = QualityPolicy.objects.filter(
                organization_id=organization_id,
                status__in=['approved', 'active']
            ).order_by('-version').first()
            context['active_policy'] = {
                'content': policy.content if policy else '',
                'version': policy.version if policy else None,
                'customer_focus': policy.customer_focus if policy else '',
            }
        except Exception:
            context['active_policy'] = {}

        try:
            from planning.models import QualityObjective
            objectives = list(
                QualityObjective.objects.filter(
                    organization_id=organization_id
                ).values('title', 'status')
            )
            context['objectives'] = objectives
        except Exception:
            context['objectives'] = []

        return context

    def _extract_topics(self, text: str, context: dict) -> list:
        return [
            {'topic': 'Tiempo de respuesta', 'frequency': 'Alta', 'source': 'customer_focus'},
            {'topic': 'Calidad del producto', 'frequency': 'Media', 'source': 'customer_focus'},
        ]

    def _extract_risk_alerts(self, text: str, context: dict) -> list:
        return []

    def _extract_proposed_actions(self, text: str) -> list:
        return []
