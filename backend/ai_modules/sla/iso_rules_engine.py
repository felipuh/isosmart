"""
Motor de Reglas ISO – Smart Leadership Advisor (SLA)
Lógica simbólica / reglas duras derivadas de ISO 9001:2015 y 2026 Cláusula 5.

Principio: estas reglas nunca se omiten, ni siquiera con output de IA.
Separación explícita: IA recomienda, reglas ISO bloquean, humano decide.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleViolation:
    rule_id: str
    severity: str          # 'blocker' | 'warning'
    message: str
    field: str = ''
    suggestion: str = ''


@dataclass
class RuleResult:
    passed: bool
    violations: list[RuleViolation] = field(default_factory=list)

    def add(self, violation: RuleViolation):
        self.violations.append(violation)
        if violation.severity == 'blocker':
            self.passed = False


class ISOLeadershipRulesEngine:
    """
    Reglas duras ISO 9001:2015 / 2026 – Cláusula 5.
    Validadas server-side; el frontend muestra mensajes de bloqueo.
    """

    # ─── 5.2 Política de Calidad ──────────────────────────────

    def validate_quality_policy(self, data: dict) -> RuleResult:
        """
        ISO 5.2.1: La política debe:
        a) ser apropiada al propósito y contexto de la organización
        b) proporcionar un marco para los objetivos de calidad
        c) incluir compromiso con el cumplimiento de los requisitos aplicables
        d) incluir compromiso con la mejora continua del SGC
        """
        result = RuleResult(passed=True)

        content = (data.get('content') or '').strip()
        if len(content) < 50:
            result.add(RuleViolation(
                rule_id='ISO_5.2.1_a',
                severity='blocker',
                field='content',
                message='La política debe tener contenido sustantivo (mínimo 50 caracteres).',
                suggestion='Describa el propósito y contexto de la organización.'
            ))

        framework = (data.get('framework_for_objectives') or '').strip()
        if not framework:
            result.add(RuleViolation(
                rule_id='ISO_5.2.1_b',
                severity='warning',
                field='framework_for_objectives',
                message='ISO 5.2.1b: La política debe proporcionar un marco para los objetivos de calidad.',
                suggestion='Describa cómo la política guía la definición de objetivos medibles.'
            ))

        commitment_req = (data.get('commitment_requirements') or '').strip()
        if not commitment_req:
            result.add(RuleViolation(
                rule_id='ISO_5.2.1_c',
                severity='blocker',
                field='commitment_requirements',
                message='ISO 5.2.1c: La política debe declarar el compromiso con el cumplimiento de requisitos aplicables.',
                suggestion='Incluya una declaración explícita de cumplimiento de requisitos legales, reglamentarios y del cliente.'
            ))

        commitment_imp = (data.get('commitment_improvement') or '').strip()
        if not commitment_imp:
            result.add(RuleViolation(
                rule_id='ISO_5.2.1_d',
                severity='blocker',
                field='commitment_improvement',
                message='ISO 5.2.1d: La política debe incluir compromiso con la mejora continua del SGC.',
                suggestion='Declare explícitamente el compromiso de la alta dirección con la mejora continua.'
            ))

        return result

    # ─── 5.3 Roles, Responsabilidades y Autoridades ──────────

    def validate_decision_has_responsible(self, data: dict) -> RuleResult:
        """
        ISO 5.3: Ninguna decisión puede existir sin responsable asignado.
        Regla no delegable de la alta dirección.
        """
        result = RuleResult(passed=True)
        if not data.get('responsible') and not data.get('responsible_id'):
            result.add(RuleViolation(
                rule_id='ISO_5.3_responsible',
                severity='blocker',
                field='responsible',
                message='ISO 5.3: Toda decisión debe tener un responsable asignado explícitamente.',
                suggestion='Asigne un responsable antes de registrar esta decisión.'
            ))
        return result

    def validate_raci_completeness(self, entries: list[dict]) -> RuleResult:
        """
        Regla RACI: Cada actividad debe tener al menos un Responsable (R)
        y exactamente un Accountable (A).
        """
        result = RuleResult(passed=True)
        for entry in entries:
            activity = entry.get('activity', '?')
            if not entry.get('accountable_roles'):
                result.add(RuleViolation(
                    rule_id='RACI_A_required',
                    severity='blocker',
                    field='accountable_roles',
                    message=f"Actividad '{activity}': debe tener exactamente un Accountable (A).",
                    suggestion='Asigne el rol que rinde cuentas del resultado de la actividad.'
                ))
            if not entry.get('responsible_roles'):
                result.add(RuleViolation(
                    rule_id='RACI_R_required',
                    severity='warning',
                    field='responsible_roles',
                    message=f"Actividad '{activity}': no tiene Responsible (R) asignado.",
                    suggestion='Asigne al menos un rol que ejecute la actividad.'
                ))
        return result

    # ─── 5.1 Liderazgo y Compromiso ──────────────────────────

    def validate_management_review_inputs(self, review_data: dict) -> RuleResult:
        """
        ISO 9001:2015 – 9.3.2: Las entradas de la revisión deben incluir
        temas específicos (KPIs, reclamos, no conformidades, objetivos, etc.).
        """
        result = RuleResult(passed=True)
        agenda = review_data.get('agenda_items', [])
        if not agenda:
            result.add(RuleViolation(
                rule_id='ISO_9.3.2_inputs',
                severity='warning',
                field='agenda_items',
                message='ISO 9.3.2: La revisión por la dirección debe incluir puntos de agenda documentados.',
                suggestion='Agregue al menos los inputs mandatorios: estado de objetivos, satisfacción del cliente, desempeño de procesos.'
            ))

        if not review_data.get('facilitator') and not review_data.get('facilitator_id'):
            result.add(RuleViolation(
                rule_id='ISO_5.1_facilitator',
                severity='blocker',
                field='facilitator',
                message='La revisión por la dirección debe tener un facilitador designado (alta dirección o delegado).',
                suggestion='Designe al responsable de conducir la reunión.'
            ))
        return result

    def validate_objective_has_kpi(self, objective_data: dict) -> RuleResult:
        """Regla: Todo objetivo de calidad debe tener al menos un KPI/indicador asociado."""
        result = RuleResult(passed=True)
        if not objective_data.get('kpi_ids') and not objective_data.get('indicator'):
            result.add(RuleViolation(
                rule_id='ISO_6.2_kpi',
                severity='warning',
                field='kpi_ids',
                message='ISO 6.2: Los objetivos de calidad deben ser medibles — asigne al menos un KPI/indicador.',
                suggestion='Vincule un indicador existente o cree uno nuevo para este objetivo.'
            ))
        return result

    def validate_no_individual_survey_data(self, response_data: dict) -> RuleResult:
        """
        Regla de privacidad por diseño (ISO 2026, EU AI Act):
        Las respuestas de encuestas de cultura nunca deben incluir user_id.
        """
        result = RuleResult(passed=True)
        if response_data.get('user') or response_data.get('user_id') or response_data.get('email'):
            result.add(RuleViolation(
                rule_id='PRIVACY_survey_anon',
                severity='blocker',
                field='user',
                message='Privacidad por diseño: las respuestas de encuesta de cultura son anónimas. '
                        'No se permite registrar identidad del respondiente.',
                suggestion='Elimine el campo user/user_id/email de la solicitud.'
            ))
        return result

    def validate_all(self, entity_type: str, data: Any) -> RuleResult:
        """Dispatcher de reglas por tipo de entidad."""
        validators = {
            'quality_policy': self.validate_quality_policy,
            'review_decision': self.validate_decision_has_responsible,
            'management_review': self.validate_management_review_inputs,
            'raci_entries': lambda d: self.validate_raci_completeness(d if isinstance(d, list) else [d]),
            'survey_response': self.validate_no_individual_survey_data,
        }
        validator = validators.get(entity_type)
        if validator:
            return validator(data)
        return RuleResult(passed=True)
