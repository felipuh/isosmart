import copy
import hashlib
import json
from types import SimpleNamespace
from uuid import UUID

from django.test import SimpleTestCase

from foundation.learning_delta import (
    AGENT_DEFINITION_OPERATION,
    CANONICALIZATION_VERSION,
    KNOWLEDGE_RULE_OPERATION,
    MODEL_POLICY_OPERATION,
    AgentDefinitionAutonomyReduction,
    KnowledgeLayerRuleSourceReferenceCorrection,
    LearningDeltaContractError,
    ModelPolicyApprovedModelRemoval,
    build_canonical_delta,
    canonical_delta_bytes,
    eligibility_classification,
    validate_canonical_delta_document,
)


TARGET_ID = UUID("11111111-1111-4111-8111-111111111111")
LINEAGE_ID = UUID("22222222-2222-4222-8222-222222222222")
EDITION_ID = UUID("33333333-3333-4333-8333-333333333333")
TARGET_HASH = "a" * 64
SOURCE_HASH = "b" * 64


def build(command, target_type, snapshot, edition=None):
    return build_canonical_delta(
        command=command, target_type=target_type, target_id=TARGET_ID,
        target_lineage_id=LINEAGE_ID, target_version="v1", target_hash=TARGET_HASH,
        target_snapshot=snapshot, edition_snapshot=edition,
    )


class ExactLearningDeltaContractTests(SimpleTestCase):
    def model_snapshot(self):
        return {"id": str(TARGET_ID), "lineage_id": str(LINEAGE_ID), "version": "v1",
                "approved_models": ["gpt-a", "gpt-b"], "guardrails": {"gate": True},
                "data_classes": ["internal"], "human_gate_rules": {"A3": True}}

    def agent_snapshot(self):
        return {"id": str(TARGET_ID), "lineage_id": str(LINEAGE_ID), "version": "v1",
                "autonomy_max": 3, "purpose": "assist", "capability": "recommend"}

    def knowledge_snapshots(self):
        old = f"iso-smart-source-ref-v1:{EDITION_ID}:{SOURCE_HASH}:clause/1"
        target = {"id": str(TARGET_ID), "lineage_id": str(LINEAGE_ID), "version": "v1",
                  "source_reference": old, "logic_json": {"fixed": True}}
        edition = {"id": str(EDITION_ID), "status": "published", "source_hash": SOURCE_HASH}
        return target, edition, old

    def test_deterministic_bytes_and_hash(self):
        command = ModelPolicyApprovedModelRemoval(("gpt-a",), "v2")
        left, right = build(command, "ModelPolicy", self.model_snapshot()), build(command, "ModelPolicy", self.model_snapshot())
        self.assertEqual(left.canonical_bytes, right.canonical_bytes)
        self.assertEqual(left.delta_hash, hashlib.sha256(left.canonical_bytes).hexdigest())
        self.assertEqual(left.delta_hash, right.delta_hash)
        self.assertNotIn(b" ", left.canonical_bytes)

    def test_unicode_and_key_order_are_canonical(self):
        value = {"z": "café", "a": {"quote": "\"\\\n", "integer": 0}}
        self.assertEqual(canonical_delta_bytes(value), b'{"a":{"integer":0,"quote":"\\\"\\\\\\n"},"z":"caf\xc3\xa9"}')

    def test_null_float_and_lone_surrogate_rejected(self):
        for value in ({"x": None}, {"x": 1.0}, {"x": "\ud800"}):
            with self.assertRaises(LearningDeltaContractError):
                canonical_delta_bytes(value)

    def test_unknown_field_and_versions_rejected(self):
        material = build(ModelPolicyApprovedModelRemoval(("gpt-a",), "v2"), "ModelPolicy", self.model_snapshot())
        for key, value in (("extra", True), ("canonicalization_version", "v2"),
                           ("operation_version", "v2"), ("delta_schema_version", "unknown")):
            document = copy.deepcopy(material.document)
            document[key] = value
            with self.assertRaises(LearningDeltaContractError):
                validate_canonical_delta_document(document, self.model_snapshot())

    def test_target_identity_version_and_hash_shape_rejected(self):
        material = build(ModelPolicyApprovedModelRemoval(("gpt-a",), "v2"), "ModelPolicy", self.model_snapshot())
        for key, value in (("target_id", str(EDITION_ID)), ("target_version", "latest"), ("target_hash", "A" * 64)):
            document = copy.deepcopy(material.document)
            document[key] = value
            with self.assertRaises(LearningDeltaContractError):
                validate_canonical_delta_document(document, self.model_snapshot())

    def test_model_policy_accepts_exact_removal_only(self):
        material = build(ModelPolicyApprovedModelRemoval(("gpt-a",), "v2"), "ModelPolicy", self.model_snapshot())
        self.assertEqual(material.operation_id, MODEL_POLICY_OPERATION)
        for removed in ((), ("gpt-c",), ("gpt-b", "gpt-a"), ("gpt-a", "gpt-a")):
            with self.assertRaises(LearningDeltaContractError):
                build(ModelPolicyApprovedModelRemoval(removed, "v2"), "ModelPolicy", self.model_snapshot())

    def test_agent_autonomy_strict_reduction_only(self):
        material = build(AgentDefinitionAutonomyReduction(2, "v2"), "AgentDefinition", self.agent_snapshot())
        self.assertEqual(material.operation_id, AGENT_DEFINITION_OPERATION)
        for value in (3, 4, -1, True):
            with self.assertRaises(LearningDeltaContractError):
                build(AgentDefinitionAutonomyReduction(value, "v2"), "AgentDefinition", self.agent_snapshot())

    def test_knowledge_reference_accepts_only_locator_correction(self):
        target, edition, old = self.knowledge_snapshots()
        new = f"iso-smart-source-ref-v1:{EDITION_ID}:{SOURCE_HASH}:clause/1.1"
        material = build(KnowledgeLayerRuleSourceReferenceCorrection(old, new, EDITION_ID, SOURCE_HASH, "v2"),
                         "KnowledgeLayerRule", target, edition)
        self.assertEqual(material.operation_id, KNOWLEDGE_RULE_OPERATION)
        for invalid in (old, "free text", new + "?secret=x"):
            with self.assertRaises(LearningDeltaContractError):
                build(KnowledgeLayerRuleSourceReferenceCorrection(old, invalid, EDITION_ID, SOURCE_HASH, "v2"),
                      "KnowledgeLayerRule", target, edition)

    def test_retained_synthetic_reference_is_closed_and_locator_only(self):
        old = (
            f"iso-smart-synthetic-poc-source-ref-v1:{EDITION_ID}:{SOURCE_HASH}:"
            "fixture/element/A"
        )
        new = (
            f"iso-smart-synthetic-poc-source-ref-v1:{EDITION_ID}:{SOURCE_HASH}:"
            "fixture/element/B"
        )
        target = {
            "id": str(TARGET_ID), "lineage_id": str(LINEAGE_ID), "version": "v1",
            "source_reference": old, "logic_json": {"fixture_only": True},
        }
        edition = {"id": str(EDITION_ID), "status": "published", "source_hash": SOURCE_HASH}
        material = build(
            KnowledgeLayerRuleSourceReferenceCorrection(old, new, EDITION_ID, SOURCE_HASH, "sN+1"),
            "KnowledgeLayerRule", target, edition,
        )
        self.assertEqual(material.operation_id, KNOWLEDGE_RULE_OPERATION)
        for invalid in (
            f"iso-smart-source-ref-v1:{EDITION_ID}:{SOURCE_HASH}:fixture/element/B",
            f"iso-smart-synthetic-poc-source-ref-v1:{EDITION_ID}:{SOURCE_HASH}:clause/B",
            f"iso-smart-synthetic-poc-source-ref-v1:{EDITION_ID}:{'c' * 64}:fixture/element/B",
        ):
            with self.assertRaises(LearningDeltaContractError):
                build(
                    KnowledgeLayerRuleSourceReferenceCorrection(old, invalid, EDITION_ID, SOURCE_HASH, "sN+1"),
                    "KnowledgeLayerRule", target, edition,
                )

    def test_operation_target_mismatch_and_arbitrary_payload_rejected(self):
        material = build(AgentDefinitionAutonomyReduction(2, "v2"), "AgentDefinition", self.agent_snapshot())
        document = json.loads(material.canonical_bytes)
        document["target_type"] = "ModelPolicy"
        document["payload"]["unrelated"] = "mutation"
        with self.assertRaises(LearningDeltaContractError):
            validate_canonical_delta_document(document, self.agent_snapshot())

    def test_complete_positive_eligibility_and_permanent_legacy_inertness(self):
        legacy = SimpleNamespace(canonical_delta_id=None, canonicalization_version=None,
            delta_schema_version=None, operation_id=None, operation_version=None, delta_hash=None)
        partial = SimpleNamespace(**vars(legacy)); partial.canonical_delta_id = TARGET_ID
        exact = SimpleNamespace(canonical_delta_id=TARGET_ID, canonicalization_version=CANONICALIZATION_VERSION,
            delta_schema_version="schema", operation_id=MODEL_POLICY_OPERATION,
            operation_version="v1", delta_hash=TARGET_HASH)
        self.assertEqual(eligibility_classification(legacy), "LEGACY_INERT")
        self.assertEqual(eligibility_classification(partial), "LEGACY_INERT")
        self.assertEqual(eligibility_classification(exact), "CANONICAL_DELTA_V1_ELIGIBLE")
