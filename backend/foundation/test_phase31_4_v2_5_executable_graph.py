import json
import unittest
from pathlib import Path

from .phase31_4_v2_5_executable_graph import (
    AGENT_CHAIN,
    PHASE_TOPOLOGY,
    build_executable_producer_graph,
    compose_agent_chain,
)


class ExecutableProducerGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        contract_path = root / "docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        cls.contract = json.loads(contract_path.read_text())

    def test_whole_graph_is_reachable_and_capture_complete(self):
        report = build_executable_producer_graph(self.contract)
        self.assertEqual(report["phase_count"], 33)
        self.assertEqual(report["reachable_phases"], 33)
        self.assertEqual(report["capture_count"], 565)
        self.assertEqual(report["reachable_capture_producers"], 565)
        self.assertEqual(report["missing_producers"], [])
        self.assertEqual(report["producer_consumer_contract"], "PASS")
        self.assertEqual(report["executable_producer_graph"], "PASS")

    def test_agent_chain_uses_source_backed_topological_order(self):
        report = build_executable_producer_graph(self.contract)
        chain = [item["producer"] for item in report["agent_chain"]]
        self.assertEqual(chain, [item[0] for item in AGENT_CHAIN])
        positions = {phase: report["topological_order"].index(phase) for _, phase, _, _ in AGENT_CHAIN}
        self.assertEqual(positions, dict(sorted(positions.items(), key=lambda item: item[1])))
        self.assertEqual(report["invalid_ordering"], [])
        self.assertEqual(len(report["broken_edges"]), 6)
        self.assertTrue(all(edge["status"] == "REMEDIATED" for edge in report["broken_edges"]))

    def test_missing_capture_producer_fails_closed(self):
        contract = json.loads(json.dumps(self.contract))
        for member in contract["field_bindings"]:
            for field in member["fields"]:
                if field.get("value_binding", {}).get("kind") == "CAPTURE_NATIVE_OUTPUT":
                    field["value_binding"]["native_source"] = "unrelated opportunity fallback"
                    report = build_executable_producer_graph(contract)
                    self.assertEqual(report["executable_producer_graph"], "FAIL")
                    self.assertEqual(report["reachable_capture_producers"], 564)
                    self.assertIn("unrelated opportunity fallback", report["missing_producers"])
                    return
        self.fail("contract has no native captures")

    def test_randomized_end_to_end_chain_has_no_historical_identity_dependency(self):
        identities = {producer: f"runtime-{index}-random" for index, (producer, *_rest) in enumerate(AGENT_CHAIN)}
        composed = compose_agent_chain(identities)
        self.assertEqual([item["producer"] for item in composed], list(identities))
        self.assertEqual([item["runtime_identity"] for item in composed], list(identities.values()))
        self.assertEqual(composed[-1]["native_operation"], "evaluate_execution_authorization")

    def test_all_phase_nodes_are_in_deterministic_topological_order(self):
        report = build_executable_producer_graph(self.contract)
        self.assertEqual(tuple(report["topological_order"]), PHASE_TOPOLOGY)
        self.assertEqual({item["phase_id"] for item in report["phases"]}, set(PHASE_TOPOLOGY))


if __name__ == "__main__":
    unittest.main()