"""Offline source/contract proof for the Phase 31.4.5A decision gate."""

import ast
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/governance/fixtures/PHASE31_4_4B_ROW_LEVEL_EXECUTION_CONTRACT_V2_2.json"
AGENT_RUNTIME = ROOT / "backend/foundation/agent_runtime.py"
MIGRATION_0003 = ROOT / "backend/foundation/migrations/0003_eventing_immutable_audit_foundation.py"
MIGRATION_0011 = ROOT / "backend/foundation/migrations/0011_agent_definition_run_provenance_foundation.py"

EXPECTED_CONTRACT_HASH = "a4a36025ac8873508ce5ba840d5c2920d18ba4d430d18c2353ca53a2bf597f8d"
RUN_ID = "b87bdcde-c623-522f-a0ac-ff81f61df8e8"
START_EVENT_ID = "90e2d38f-9600-5701-a34c-c9827eafc88c"
START_AGGREGATE_ID = "51c9bad4-88fb-5608-b3c9-edd578efeeb9"
START_PHYSICAL_EVENT_ID = "1af3e9a8-65f7-5952-a991-1133872659f9"


def method_node(class_name, method_name):
    tree = ast.parse(AGENT_RUNTIME.read_text())
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method_name)


class AgentRunStartSerializationDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.runtime = AGENT_RUNTIME.read_text()
        cls.migration_0003 = MIGRATION_0003.read_text()
        cls.migration_0011 = MIGRATION_0011.read_text()

    def field_value(self, table, primary_key, field_name):
        member = next(
            item for item in self.contract["field_bindings"]
            if item["member_identity"] == {
                "primary_key_or_artifact_id": primary_key,
                "qualified_table_or_artifact_index": table,
            }
        )
        field = next(item for item in member["fields"] if item["name"] == field_name)
        binding = field["value_binding"]
        return binding.get("typed_value", binding.get("expected_output"))

    def test_frozen_contract_and_migration_boundary(self):
        self.assertEqual(hashlib.sha256(CONTRACT.read_bytes()).hexdigest(), EXPECTED_CONTRACT_HASH)
        self.assertFalse(any((ROOT / "backend/foundation/migrations").glob("0024_*")))

    def test_exact_event_is_not_bound_to_the_exact_agent_run_parent(self):
        self.assertEqual(
            self.field_value("eventing.domain_event", START_EVENT_ID, "event_id"),
            START_PHYSICAL_EVENT_ID,
        )
        self.assertNotEqual(START_EVENT_ID, START_PHYSICAL_EVENT_ID)
        self.assertEqual(self.field_value("qms.agent_run", RUN_ID, "id"), RUN_ID)
        self.assertEqual(
            self.field_value("eventing.domain_event", START_EVENT_ID, "aggregate_id"),
            START_AGGREGATE_ID,
        )
        self.assertNotEqual(START_AGGREGATE_ID, RUN_ID)
        self.assertNotEqual(
            self.field_value("eventing.domain_event", START_EVENT_ID, "aggregate_type"),
            "agent_run",
        )
        self.assertNotEqual(
            self.field_value("eventing.domain_event", START_EVENT_ID, "event_type"),
            "agent_run.started",
        )

    def test_native_start_cannot_accept_the_preassigned_run_identity(self):
        start = method_node("AgentRunCommandService", "start_agent_run")
        parameters = {argument.arg for argument in start.args.args + start.args.kwonlyargs}
        source = ast.get_source_segment(self.runtime, start)
        self.assertNotIn("run_id", parameters)
        self.assertIn("run_id = uuid4()", source)
        self.assertLess(source.index("AgentRun.objects"), source.index("self._event_outbox_audit"))

    def test_native_event_key_is_exactly_the_parent_identity(self):
        helper = ast.get_source_segment(
            self.runtime, method_node("AgentRunCommandService", "_event_outbox_audit")
        )
        self.assertIn('aggregate_type="agent_run", aggregate_id=run.id', helper)
        self.assertIn('.filter(aggregate_type="agent_run", aggregate_id=run.id)', helper)

    def test_parent_identity_serialization_premises_exist_only_for_coherent_key(self):
        self.assertIn("id uuid PRIMARY KEY", self.migration_0011)
        self.assertIn("UNIQUE(tenant_id,organization_id,id)", self.migration_0011)
        self.assertNotIn("idempotency_key", ast.get_source_segment(
            self.runtime, method_node("AgentRunCommandService", "start_agent_run")
        ))
        self.assertFalse(START_AGGREGATE_ID == RUN_ID)

    def test_later_same_stream_writers_lock_parent_before_allocation(self):
        for method_name in ("complete_agent_run_with_recommendation", "fail_agent_run"):
            source = ast.get_source_segment(
                self.runtime, method_node("AgentRunCommandService", method_name)
            )
            self.assertLess(source.index("select_for_update"), source.index("self._event_outbox_audit"))

    def test_domain_event_schema_does_not_allocate_or_uniquely_guard_stream_version(self):
        self.assertIn("aggregate_version bigint NOT NULL", self.migration_0003)
        self.assertIn(
            "ON eventing.domain_event(tenant_id,aggregate_type,aggregate_id,aggregate_version)",
            self.migration_0003,
        )
        self.assertNotIn(
            "UNIQUE (tenant_id,aggregate_type,aggregate_id,aggregate_version)",
            self.migration_0003,
        )

    def test_exact_contract_rejects_parent_identity_counterexample(self):
        def parent_identity_can_serialize(event_aggregate_id, parent_id):
            return event_aggregate_id == parent_id

        self.assertFalse(parent_identity_can_serialize(START_AGGREGATE_ID, RUN_ID))


if __name__ == "__main__":
    unittest.main()
