from types import SimpleNamespace
import importlib
from uuid import uuid4

from django.test import SimpleTestCase

from foundation.foundation_gate import FoundationGateError, evaluate_foundation_attempt
from foundation.models import ConceptMastery, LearningPath, QuestionBank, QuizAttempt


def question(*, concept="context", correct="yes", critical=False):
    return SimpleNamespace(
        id=uuid4(),
        concept_key=concept,
        options_json=[{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}],
        answer_key={"option_ids": [correct]},
        explanation="Review the applicable concept.",
        critical=critical,
    )


class FoundationGateEvaluationTests(SimpleTestCase):
    def test_score_is_server_calculated_and_includes_concept_feedback(self):
        questions = [question(concept=f"concept-{index}") for index in range(5)]
        answers = [
            {"question_id": item.id if index == 0 else str(item.id), "selected_option_ids": ["yes"]}
            for index, item in enumerate(questions[:4])
        ] + [{"question_id": str(questions[4].id), "selected_option_ids": ["no"]}]

        result = evaluate_foundation_attempt(
            questions=questions, answers=answers, required_score=80,
        )

        self.assertEqual(str(result["score"]), "80.00")
        self.assertTrue(result["passed"])
        self.assertEqual(result["weak_concepts"], ["concept-4"])
        self.assertNotIn("answer_key", result["answers"][0])
        self.assertEqual(result["feedback"][-1]["correct_option_ids"], ["yes"])

    def test_critical_concept_requires_correct_answer_even_above_score_threshold(self):
        questions = [question(concept="critical", critical=True)] + [
            question(concept=f"concept-{index}") for index in range(4)
        ]
        answers = [
            {"question_id": str(item.id), "selected_option_ids": ["no" if index == 0 else "yes"]}
            for index, item in enumerate(questions)
        ]

        result = evaluate_foundation_attempt(
            questions=questions, answers=answers, required_score=80,
        )

        self.assertEqual(str(result["score"]), "80.00")
        self.assertFalse(result["passed"])

    def test_rejects_incomplete_duplicate_and_non_applicable_answers(self):
        first, second = question(), question(concept="risk")
        valid = {"question_id": str(first.id), "selected_option_ids": ["yes"]}
        with self.assertRaises(FoundationGateError) as incomplete:
            evaluate_foundation_attempt(questions=[first, second], answers=[valid], required_score=80)
        self.assertEqual(incomplete.exception.code, "ANSWERS_INCOMPLETE")

        with self.assertRaises(FoundationGateError) as duplicate:
            evaluate_foundation_attempt(
                questions=[first], answers=[valid, valid], required_score=80,
            )
        self.assertEqual(duplicate.exception.code, "ANSWER_DUPLICATE")

        invalid = {"question_id": str(first.id), "selected_option_ids": ["outside"]}
        with self.assertRaises(FoundationGateError) as invalid_choice:
            evaluate_foundation_attempt(questions=[first], answers=[invalid], required_score=80)
        self.assertEqual(invalid_choice.exception.code, "ANSWER_INVALID")

    def test_empty_bank_is_a_conflict_not_a_pass(self):
        with self.assertRaises(FoundationGateError) as caught:
            evaluate_foundation_attempt(
                questions=[],
                answers=[{"question_id": str(uuid4()), "selected_option_ids": ["x"]}],
                required_score=80,
            )
        self.assertEqual(caught.exception.code, "QUESTION_BANK_EMPTY")
        self.assertEqual(caught.exception.status_code, 409)


class FoundationGateStorageContractTests(SimpleTestCase):
    def test_attempt_and_mastery_are_tenant_and_user_scoped(self):
        for model in (QuizAttempt, ConceptMastery):
            fields = {field.name for field in model._meta.get_fields()}
            self.assertTrue({"tenant", "user"} <= fields, model.__name__)
            self.assertFalse(model._meta.managed)
        self.assertIn("standard_edition", {field.name for field in LearningPath._meta.get_fields()})
        self.assertIn("answer_key", {field.name for field in QuestionBank._meta.get_fields()})
        self.assertIn("provenance_hash", {field.name for field in QuizAttempt._meta.get_fields()})

    def test_postgresql_migration_defines_append_only_history_and_rls(self):
        migration = importlib.import_module("foundation.migrations.0025_iso9000_foundation_gate")
        sql = migration.FORWARD_SQL
        self.assertIn("CREATE TABLE qms.quiz_attempt", sql)
        self.assertIn("CREATE TABLE qms.concept_mastery", sql)
        self.assertIn("FOREIGN KEY(tenant_id,user_id)", sql)
        self.assertIn("ENABLE ROW LEVEL SECURITY", sql)
        self.assertIn("FORCE ROW LEVEL SECURITY", sql)
        self.assertIn("current_setting(''app.tenant_id'',true)", sql)
        self.assertIn("Foundation Gate attempts are append-only", sql)
        self.assertIn("SECURITY DEFINER", sql)
        self.assertIn("foundation_0025_resolve_tenant_projection", sql)
        self.assertIn("REVOKE ALL ON FUNCTION qms.foundation_0025_resolve_tenant_projection(uuid) FROM PUBLIC", sql)
        self.assertIn("GRANT EXECUTE ON FUNCTION qms.foundation_0025_resolve_tenant_projection(uuid)", sql)
        self.assertIn("DROP TABLE qms.concept_mastery", migration.REVERSE_SQL)