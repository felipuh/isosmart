"""Offline reproductions of frozen V2.4/native contradictions, not POC passes.

These tests deliberately prove rejection. They must never be counted as
successful production bindings or as an offline P1=0 promotion gate.
"""

import ast
from copy import deepcopy
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from uuid import UUID

from foundation.phase31_4_v2_4_support_producer import _contract, StrictBindingRenderer


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "backend/foundation/migrations/0015_first_controlled_qms_mutation_poc.py"


def member_fields(table):
    members = [row for row in _contract()["field_bindings"]
               if row["member_identity"]["qualified_table_or_artifact_index"] == table]
    if len(members) != 1:
        raise AssertionError(f"expected one frozen member: {table}")
    return {field["name"]: field for field in members[0]["fields"]}


def literal(table, name):
    binding = member_fields(table)[name]["value_binding"]
    if binding["kind"] != "EXACT_LITERAL":
        raise AssertionError(f"not an exact literal: {table}.{name}")
    return deepcopy(binding["typed_value"])


def forward_sql(path):
    """Read migration SQL without importing or executing the migration."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "FORWARD_SQL"
                        for target in node.targets))


class FrozenRuntimeSemanticContradictionTests(unittest.TestCase):
    def test_real_prepare_rejects_exact_preconditions_before_transaction(self):
        from foundation.action_authorization import ActionPreparationService
        from foundation.tenant_context import TrustedTenantIdentity

        fields = member_fields("qms.action_plan")
        material = {name: literal("qms.action_plan", name) for name in (
            "action_type", "target_type", "target_id", "parameters", "impact",
            "reversibility", "preconditions", "dry_run_supported", "required_autonomy",
            "idempotency_key",
        )}
        original = deepcopy(material)
        tenant = literal("qms.tenant_projection", "id")
        decision = literal("qms.agent_decision", "id")
        trace = StrictBindingRenderer().render(fields["trace_id"], {})
        self.assertEqual(material["preconditions"], ["synthetic-test-only"])
        with patch("foundation.action_authorization.trusted_tenant_context",
                   side_effect=AssertionError("transaction boundary must not be reached")) as boundary:
            with self.assertRaisesRegex(ValueError, r"^preconditions\[0\] must be an object$"):
                ActionPreparationService().prepare_action_plan(
                    identity=TrustedTenantIdentity("offline-semantic-reproduction", UUID(tenant)),
                    agent_decision_id=UUID(decision), actor_id="offline-semantic-reproduction",
                    trace_id=trace, **material,
                )
            boundary.assert_not_called()
        self.assertEqual(material, original)

    def test_every_native_accepted_precondition_is_an_object_not_frozen_text(self):
        from foundation.action_authorization import _preconditions

        # This is a diagnostic control, never substituted into the frozen fixture.
        accepted = _preconditions([{
            "identity": "diagnostic-only", "type": "diagnostic-only", "expected": True,
        }])
        self.assertIsInstance(accepted[0], dict)
        self.assertNotEqual(accepted, literal("qms.action_plan", "preconditions"))
        with self.assertRaisesRegex(ValueError, "must be an object"):
            _preconditions(literal("qms.action_plan", "preconditions"))

    def test_frozen_a0_and_target_type_contradict_unchanged_sql_guard(self):
        sql = forward_sql(MIGRATION)
        function = sql.split("CREATE FUNCTION qms.foundation_0015_controlled_opportunity_execution(", 1)[1]
        function = function.split("END $fn$;", 1)[0]
        guard = function.split("IF a.outcome<>", 1)[1].split("END IF;", 1)[0]
        self.assertIn("p.required_autonomy<>3", guard)
        self.assertIn("p.target_type<>'Opportunity'", guard)
        self.assertIn("a.effective_autonomy_ceiling<3", guard)
        self.assertIn("run.effective_autonomy_ceiling<3", guard)
        self.assertIn("dec.decision_autonomy<3", guard)
        self.assertIn("ERRCODE='42501',MESSAGE='controlled governance validation denied'", guard)
        self.assertEqual(literal("qms.action_plan", "required_autonomy"), 0)
        self.assertEqual(literal("qms.action_plan", "target_type"), "opportunity")
        self.assertEqual(literal("qms.execution_authorization", "effective_autonomy_ceiling"), 0)
        self.assertEqual(literal("qms.agent_run", "effective_autonomy_ceiling"), 0)
        self.assertEqual(literal("qms.agent_decision", "decision_autonomy"), 0)
        # Check every later frozen migration: no replacement removes this guard.
        for path in sorted(MIGRATION.parent.glob("*.py")):
            if path.name[:4].isdigit() and 16 <= int(path.name[:4]) <= 23:
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(re.search(
                    r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+"
                    r"qms\.foundation_0015_controlled_opportunity_execution\s*\(",
                    text, flags=re.I,
                ), path.name)
        recovery = forward_sql(next(MIGRATION.parent.glob("0016_*.py")))
        self.assertIn("RETURN qms.foundation_0015_controlled_opportunity_execution(", recovery)

    def test_fixed_target_text_cannot_be_the_sql_uuid_target(self):
        sql = forward_sql(MIGRATION)
        self.assertIn("lineage_id=p.target_id::uuid", sql)
        with self.assertRaises(ValueError):
            UUID(literal("qms.action_plan", "target_id"))

