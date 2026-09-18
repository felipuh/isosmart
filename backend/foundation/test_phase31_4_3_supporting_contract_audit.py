"""Offline source witnesses for 31.4.3; never an operational admission gate.

These tests establish additional necessary conditions, not complete fixture,
field-taxonomy, producer, authority or retention closure. No SQL is executed.
"""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest
from uuid import UUID, uuid5


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/governance/evidence/PHASE31_4_3_SUPPORTING_CONTRACT_AUDIT_V1.json"
SPEC = ROOT / "docs/governance/fixtures/PHASE31_3_COMPLETE_RETAINED_SYNTHETIC_LIFECYCLE_SPEC_V1.json"
MIGRATIONS = ROOT / "backend/foundation/migrations"


def sql_source(number):
    path, = MIGRATIONS.glob(f"{number:04d}_*.py")
    tree = ast.parse(path.read_text())
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "FORWARD_SQL"
                        for t in node.targets))


def method_source(filename, class_name, method_name):
    source = (ROOT / "backend/foundation" / filename).read_text()
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    return ast.get_source_segment(source, method)


def native_child_id(artifact_id, suffix):
    """Pure transcription of frozen 0022 SQL, including both forced nibbles."""
    if suffix not in {"event", "outbox", "audit", "curation"}:
        raise ValueError("only the four inspected native child suffixes")
    digest = hashlib.md5(f"{UUID(str(artifact_id))}:{suffix}".encode("utf-8")).hexdigest()
    return str(UUID(f"{digest[:8]}-{digest[8:12]}-4{digest[13:16]}-8{digest[17:20]}-{digest[20:]}"))


def support_metadata(roots):
    """Static ORM lower bound plus every nullable field; not live SQL closure."""
    from foundation import models

    pending, visited, edges, fields = list(roots), set(), [], []
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        model = getattr(models, name)
        for field in model._meta.concrete_fields:
            record = {"model": name, "table": model._meta.db_table.replace('"', ''),
                      "column": field.column, "type": field.get_internal_type(),
                      "nullable": field.null, "primary_key": field.primary_key}
            if field.is_relation:
                target = field.remote_field.model.__name__
                record["target_model"] = target
                record["target_column"] = field.target_field.column
                if not field.null:
                    edges.append({"source": name, "column": field.column, "target": target})
                    pending.append(target)
            fields.append(record)
    return {"classes": sorted(visited),
            "nonnull_edges": sorted(edges, key=lambda x: (x["source"], x["column"])),
            "fields": sorted(fields, key=lambda x: (x["model"], x["column"]))}


def verify_evidence_witnesses(document):
    """Integrity of quoted source only; does not approve any future producer."""
    for witness in document["source_witnesses"]:
        lines = (ROOT / witness["path"]).read_text().splitlines()
        actual = "\n".join(lines[witness["start"] - 1:witness["end"]])
        if actual != witness["source"]:
            raise ValueError(f"source witness differs: {witness['id']}")


class SupportingContractAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text())
        cls.spec = json.loads(SPEC.read_text())

    def test_diagnostic_is_not_an_approved_successor(self):
        self.assertEqual(self.evidence["status"], "DIAGNOSTIC_ONLY_NOT_AUTHORIZED")
        for key in ("mandatory_reading_complete", "successor_package_complete",
                    "producer_matrix_covers_every_created_row", "taxonomy_covers_every_lifecycle_field",
                    "database_creation_authorized", "lifecycle_execution_authorized"):
            self.assertIs(self.evidence[key], False)
        self.assertEqual(self.evidence["remaining_blockers"], ["B1", "B2", "B3", "B4"])
        self.assertIsNone(self.evidence["unknown_binding_count"])

    def test_source_witnesses_match_and_tampering_is_rejected(self):
        verify_evidence_witnesses(self.evidence)
        changed = deepcopy(self.evidence)
        changed["source_witnesses"][0]["source"] += " ALTERED"
        with self.assertRaises(ValueError):
            verify_evidence_witnesses(changed)

    def test_protected_sources_match(self):
        for path, digest in self.evidence["protected_file_hashes"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)
        self.assertEqual(len(list(MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.py"))), 23)
        self.assertFalse(list(MIGRATIONS.glob("0024*")))

    def test_native_identity_formula_matches_frozen_sql(self):
        sql = sql_source(22)
        for fragment in ("md5(p_id::text||':'||p_suffix)", "'-4'||substr", "'-8'||substr"):
            self.assertIn(fragment, sql)
        self.assertEqual(len(self.evidence["native_release_identity_vectors"]), 7)
        for item in self.evidence["native_release_identity_vectors"]:
            actual = native_child_id(item["parent_id"], item["suffix"])
            self.assertEqual(actual, item["id"])
            self.assertEqual(UUID(actual).version, 4)
            self.assertNotEqual(UUID(actual).version, 5)
            historical = self.spec[item["operation"]][item["spec_field"]]
            if isinstance(historical, dict):
                historical = historical["id"]
            self.assertEqual(actual, historical)

    def test_uuid5_cannot_replace_native_children(self):
        namespace = UUID(self.spec["experiment"]["namespace_uuid"])
        for item in self.evidence["native_release_identity_vectors"]:
            self.assertNotEqual(item["id"], str(uuid5(namespace, item["operation"] + "-" + item["suffix"])))
        self.assertIn("release_child_id", self.spec["canonicalization"])

    def test_claim_and_artifact_are_distinct_rows_with_equal_uuid(self):
        sql = sql_source(22)
        self.assertIn("VALUES(p_artifact,p_operation,p_artifact,p_rule", sql)
        for operation in ("publication", "activation"):
            self.assertEqual(self.spec[operation]["id"], self.spec[operation]["claim_id"])
        self.assertEqual(self.evidence["row_identity_key"], ["qualified_table", "primary_key"])

    def test_agent_run_requires_published_catalog_and_frozen_inputs(self):
        sql = sql_source(11)
        for fragment in ("definition.status IS DISTINCT FROM 'published'",
                         "policy_status IS DISTINCT FROM 'published'",
                         "agent run start requires frozen inputs",
                         "DEFERRABLE INITIALLY DEFERRED",
                         "run input requires running run and exact published edition/rule"):
            self.assertIn(fragment, sql)

    def test_completion_requires_reverse_link_and_exact_basis_set(self):
        sql = sql_source(11)
        self.assertIn("completed agent run requires exact Recommendation linkage", sql)
        self.assertIn("RecommendationBasis must exactly match frozen AgentRun inputs", sql)
        self.assertIn("FROM qms.recommendation_basis WHERE recommendation_id=NEW.recommendation_id", sql)
        body = method_source("agent_runtime.py", "AgentRunCommandService", "complete_agent_run_with_recommendation")
        self.assertLess(body.index("AgentRunRecommendation.objects"), body.index("run.status = AgentRun.Status.COMPLETED"))

    def test_agent_decision_must_precede_plan_not_only_authorization(self):
        body = method_source("action_authorization.py", "ActionPreparationService", "prepare_action_plan")
        self.assertLess(body.index("AgentDecision.objects"), body.index("ActionPlan.objects.using(self.using).create"))
        self.assertIn("ActionPlan requires the exact governed Recommendation", body)

    def test_catalog_audit_is_a_distinct_table_without_invented_domain_events(self):
        from foundation import models

        expected = {"AgentCatalogCurationAudit": 'governance"."curation_audit',
                    "NormativeCurationAudit": 'normative"."curation_audit',
                    "ImmutableAuditLog": 'audit"."immutable_audit_log'}
        for model, table in expected.items():
            self.assertEqual(getattr(models, model)._meta.db_table, table)
        for method in ("create_model_policy", "create_agent_definition", "_publish"):
            body = method_source("agent_runtime.py", "AgentCatalogCommandService", method)
            self.assertIn("self._audit(", body)
            self.assertNotIn("DomainEvent", body)
            self.assertNotIn("TransactionalOutbox", body)

    def test_identity_only_immutable_audit_exception_still_needs_sql_parity(self):
        sql = sql_source(3)
        self.assertIn("v_id uuid := uuidv7();", sql)
        self.assertIn("pg_advisory_xact_lock", sql)
        self.assertIn("sequence_number + 1, entry_hash INTO v_sequence, v_previous", sql)
        body = method_source("audit.py", "AuditWriterService", "append")
        self.assertNotIn("uuid4", body)
        self.assertIn("audit.append_immutable_audit", body)

    def test_graph_census_recomputes_and_exceeds_predecessor_lower_bound(self):
        actual = support_metadata(self.evidence["metadata_roots"])
        self.assertEqual(actual, self.evidence["source_metadata_census"])
        prior = json.loads((ROOT / "docs/governance/evidence/PHASE31_4_2_SUCCESSOR_DESIGN_DIAGNOSTIC_V1.json").read_text())
        self.assertTrue(set(prior["nonnull_model_fk_lower_bound"]["classes"]) < set(actual["classes"]))
        for model in ("AgentRunInput", "AgentRunRecommendation", "RecommendationBasis", "StandardEdition", "AgentCatalogCurationAudit"):
            self.assertIn(model, actual["classes"])
        self.assertFalse(self.evidence["source_metadata_is_complete_semantic_closure"])

    def test_signal_annotations_are_not_invented_model_columns(self):
        from foundation.models import LearningSignal

        columns = {field.column for field in LearningSignal._meta.concrete_fields}
        self.assertTrue({"synthetic", "automatic_learning", "normative", "production", "findings", "rationale"}.isdisjoint(columns))
        self.assertIn("selected_effectiveness_check_id", columns)

    def test_effectiveness_requires_real_provenance_and_conditional_branches(self):
        sql = sql_source(17)
        for fragment in ("e.status<>'succeeded'", "e.executor_type<>'controlled_opportunity'",
                         "r.outcome<>'opportunity_deferred'", "NEW.due_at<=n.created_at",
                         "measurement_definition_id IS NOT NULL", "predecessor_id IS NULL AND revision=1",
                         "EffectivenessCheck requires at least one exact Evidence revision"):
            self.assertIn(fragment, sql)

    def test_replay_is_not_fabricated_for_native_commands_without_caller_key(self):
        cases = [("governed_learning.py", "LearningSignalCommandService", "create_signal"),
                 ("effectiveness.py", "EffectivenessCheckCommandService", "record_effectiveness_check"),
                 ("human_decision.py", "HumanDecisionGateService", "record_human_approval")]
        for filename, cls, method in cases:
            tree = ast.parse(method_source(filename, cls, method))
            params = {a.arg for a in tree.body[0].args.args + tree.body[0].args.kwonlyargs}
            self.assertNotIn("idempotency_key", params)

    def test_all_fixed_digests_have_source_bytes_classification(self):
        fixed = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", json.dumps(self.evidence)))
        known = self.evidence["digest_provenance"]
        self.assertFalse(fixed - set(known))
        self.assertTrue(all(item["classification"] == "SOURCE_BYTES_HASH" for item in known.values()))


if __name__ == "__main__":
    unittest.main()
