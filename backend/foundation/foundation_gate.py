"""ISO 9000 Foundation Gate application command and score evaluation."""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from django.db import models
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash
from .models import (
    ConceptMastery,
    DomainEvent,
    LearningPath,
    QuestionBank,
    QuizAttempt,
    TransactionalOutbox,
)
from .tenant_context import TrustedTenantIdentity, trusted_tenant_context


FOUNDATION_COMPLETED_EVENT = "iso9000.foundation.completed"
FOUNDATION_COMPLETED_SCHEMA_VERSION = 1


class FoundationGateError(ValueError):
    def __init__(self, code, message, status_code=422):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class FoundationGateAttemptResult:
    attempt_id: UUID
    learning_path_id: UUID
    standard_edition_id: UUID
    question_bank_version: int
    score: Decimal
    passed: bool
    weak_concepts: tuple[str, ...]
    feedback: tuple[dict, ...]
    provenance_hash: str
    event_id: UUID | None
    outbox_id: UUID | None
    audit_id: UUID
    completed_at: object


def _option_ids(question):
    options = question.options_json
    if not isinstance(options, list) or len(options) < 2:
        raise FoundationGateError("QUESTION_INVALID", "question options must contain at least two choices")
    values = []
    for option in options:
        if not isinstance(option, dict) or not isinstance(option.get("id"), str) or not option["id"].strip():
            raise FoundationGateError("QUESTION_INVALID", "each question option requires a stable id")
        values.append(option["id"])
    if len(values) != len(set(values)):
        raise FoundationGateError("QUESTION_INVALID", "question option ids must be unique")
    return set(values)


def evaluate_foundation_attempt(*, questions, answers, required_score, critical_concepts=()):
    """Validate submitted choices and calculate a non-client-controlled result."""
    if not isinstance(answers, list) or not answers:
        raise FoundationGateError("ANSWERS_REQUIRED", "answers must be a non-empty list")
    questions_by_id = {str(question.id): question for question in questions}
    if not questions_by_id:
        raise FoundationGateError("QUESTION_BANK_EMPTY", "the selected learning path has no applicable questions", 409)

    supplied = {}
    for answer in answers:
        if not isinstance(answer, dict) or not isinstance(answer.get("question_id"), (str, UUID)):
            raise FoundationGateError("ANSWER_INVALID", "each answer requires a question_id")
        question_id = str(answer["question_id"])
        if question_id in supplied:
            raise FoundationGateError("ANSWER_DUPLICATE", "a question may be answered only once")
        question = questions_by_id.get(question_id)
        if question is None:
            raise FoundationGateError("QUESTION_NOT_APPLICABLE", "answer references a question outside this path")
        selected = answer.get("selected_option_ids")
        if not isinstance(selected, list) or not selected or any(not isinstance(item, str) for item in selected):
            raise FoundationGateError("ANSWER_INVALID", "selected_option_ids must be a non-empty list of strings")
        if len(selected) != len(set(selected)) or not set(selected) <= _option_ids(question):
            raise FoundationGateError("ANSWER_INVALID", "selected options are invalid for this question")
        answer_key = question.answer_key
        expected = answer_key.get("option_ids") if isinstance(answer_key, dict) else None
        if not isinstance(expected, list) or not expected or any(not isinstance(item, str) for item in expected):
            raise FoundationGateError("QUESTION_INVALID", "question answer key is invalid")
        if len(expected) != len(set(expected)) or not set(expected) <= _option_ids(question):
            raise FoundationGateError("QUESTION_INVALID", "question answer key references invalid options")
        supplied[question_id] = (question, sorted(selected), set(selected) == set(expected))

    if set(supplied) != set(questions_by_id):
        raise FoundationGateError("ANSWERS_INCOMPLETE", "every applicable question must be answered")

    total = len(supplied)
    correct = sum(1 for _, _, is_correct in supplied.values() if is_correct)
    score = (Decimal(correct) * Decimal("100") / Decimal(total)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP,
    )
    critical_concepts = set(critical_concepts or ())
    weak_concepts = sorted({
        question.concept_key
        for question, _, is_correct in supplied.values()
        if not is_correct
    })
    critical_pass = all(
        is_correct
        for question, _, is_correct in supplied.values()
        if question.critical or question.concept_key in critical_concepts
    )
    normalized_answers = [
        {"question_id": question_id, "selected_option_ids": selected}
        for question_id, (_, selected, _) in sorted(supplied.items())
    ]
    feedback = [
        {
            "question_id": question_id,
            "concept_key": question.concept_key,
            "correct": is_correct,
            "correct_option_ids": sorted(question.answer_key["option_ids"]),
            "explanation": question.explanation,
        }
        for question_id, (question, _, is_correct) in sorted(supplied.items())
    ]
    concept_scores = {}
    for concept in sorted({question.concept_key for question, _, _ in supplied.values()}):
        concept_total = sum(1 for question, _, _ in supplied.values() if question.concept_key == concept)
        concept_correct = sum(
            1 for question, _, is_correct in supplied.values()
            if question.concept_key == concept and is_correct
        )
        concept_scores[concept] = Decimal(concept_correct) * Decimal("100") / Decimal(concept_total)
    return {
        "score": score,
        "passed": score >= Decimal(str(required_score)) and critical_pass,
        "weak_concepts": weak_concepts,
        "answers": normalized_answers,
        "concept_scores": concept_scores,
        "feedback": feedback,
    }


class FoundationGateCommandService:
    def __init__(self, *, using="app"):
        self.using = using

    def submit_attempt(
        self, *, identity, user_projection_id, learning_path_id, answers,
        actor_id, trace_id, role_code=None, industry_code=None,
    ):
        if not isinstance(identity, TrustedTenantIdentity):
            raise TypeError("identity must be a TrustedTenantIdentity")
        trace_id = UUID(str(trace_id))
        now = timezone.now()
        attempt_id = uuid4()
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using,
        ):
            path = LearningPath.objects.using(self.using).select_related(
                "standard_edition__standard",
            ).get(
                id=learning_path_id,
                active=True,
                standard_edition__status="published",
                standard_edition__standard__code__icontains="9000",
                standard_edition__edition__icontains="2026",
            )
            if path.role_code and path.role_code != role_code:
                raise FoundationGateError("LEARNING_PATH_NOT_APPLICABLE", "learning path is not applicable to this role", 404)
            if path.industry_code and path.industry_code != industry_code:
                raise FoundationGateError("LEARNING_PATH_NOT_APPLICABLE", "learning path is not applicable to this industry", 404)
            question_query = QuestionBank.objects.using(self.using).filter(
                learning_path_id=path.id,
                publication_state=QuestionBank.PublicationState.PUBLISHED,
            )
            if industry_code:
                question_query = question_query.filter(
                    models.Q(industry_code__isnull=True) | models.Q(industry_code=industry_code),
                )
            else:
                question_query = question_query.filter(industry_code__isnull=True)
            questions = list(question_query.order_by("-version", "id"))
            if questions:
                bank_version = questions[0].version
                questions = [question for question in questions if question.version == bank_version]
            else:
                bank_version = 1
            result = evaluate_foundation_attempt(
                questions=questions,
                answers=answers,
                required_score=path.required_score,
                critical_concepts=path.critical_concepts,
            )
            completion_already_recorded = QuizAttempt.objects.using(self.using).filter(
                tenant_id=identity.tenant_id,
                user_id=user_projection_id,
                learning_path_id=path.id,
                passed=True,
            ).exists()
            provenance = {
                "attempt_id": str(attempt_id),
                "tenant_id": str(identity.tenant_id),
                "user_projection_id": str(user_projection_id),
                "learning_path_id": str(path.id),
                "question_bank_version": bank_version,
                "standard_edition_id": str(path.standard_edition_id),
                "answers": result["answers"],
                "score": str(result["score"]),
                "passed": result["passed"],
                "weak_concepts": result["weak_concepts"],
                "required_score": str(path.required_score),
                "trace_id": str(trace_id),
            }
            provenance_hash = canonical_hash(provenance)
            attempt = QuizAttempt.objects.using(self.using).create(
                id=attempt_id,
                tenant_id=identity.tenant_id,
                user_id=user_projection_id,
                learning_path_id=path.id,
                question_bank_version=bank_version,
                answers=result["answers"],
                weak_concepts=result["weak_concepts"],
                score=result["score"],
                passed=result["passed"],
                provenance_hash=provenance_hash,
                started_at=now,
                completed_at=now,
            )
            for concept, score in result["concept_scores"].items():
                ConceptMastery.objects.using(self.using).update_or_create(
                    tenant_id=identity.tenant_id,
                    user_id=user_projection_id,
                    concept_key=concept,
                    defaults={
                        "score": score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                        "last_assessed_at": now,
                        "retraining_due_at": now + timedelta(days=7) if concept in result["weak_concepts"] else None,
                        "latest_attempt_id": attempt.id,
                    },
                )

            event_id = None
            outbox_id = None
            if result["passed"] and not completion_already_recorded:
                event_id = uuid4()
                event_payload = {
                    "attempt_id": str(attempt.id),
                    "learning_path_id": str(path.id),
                    "standard_edition_id": str(path.standard_edition_id),
                    "user_projection_id": str(user_projection_id),
                    "score": str(attempt.score),
                    "provenance_hash": provenance_hash,
                }
                DomainEvent.objects.using(self.using).create(
                    event_id=event_id,
                    tenant_id=identity.tenant_id,
                    event_type=FOUNDATION_COMPLETED_EVENT,
                    schema_version=FOUNDATION_COMPLETED_SCHEMA_VERSION,
                    aggregate_type="quiz_attempt",
                    aggregate_id=attempt.id,
                    aggregate_version=1,
                    occurred_at=now,
                    trace_id=trace_id,
                    source="iso-smart-foundation-gate",
                    payload=event_payload,
                    payload_hash=canonical_hash(event_payload),
                )
                outbox = TransactionalOutbox.objects.using(self.using).create(
                    tenant_id=identity.tenant_id,
                    domain_event_id=event_id,
                    status=TransactionalOutbox.Status.PENDING,
                    publish_attempts=0,
                    available_at=now,
                )
                outbox_id = outbox.id

            audit_id = AuditWriterService(using=self.using).append(AuditAppend(
                tenant_id=identity.tenant_id,
                stream_type="foundation_gate_attempt",
                stream_id=attempt.id,
                actor_type="human",
                actor_id=str(actor_id),
                action="iso9000.foundation.attempt_recorded",
                entity_type="quiz_attempt",
                entity_id=attempt.id,
                trace_id=trace_id,
                occurred_at=now,
                after_hash=provenance_hash,
                metadata={
                    "learning_path_id": str(path.id),
                    "standard_edition_id": str(path.standard_edition_id),
                    "passed": attempt.passed,
                    "score": str(attempt.score),
                    "event_id": str(event_id) if event_id else None,
                },
            ))
            return FoundationGateAttemptResult(
                attempt.id, path.id, path.standard_edition_id, bank_version, attempt.score,
                attempt.passed, tuple(attempt.weak_concepts), tuple(result["feedback"]),
                provenance_hash, event_id, outbox_id, audit_id, attempt.completed_at,
            )