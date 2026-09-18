"""Deterministically generate the non-self-referential Retry5 input manifest."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from .phase31_4_operational_manifest import ROOT, SCHEMA, _local_import_closure
from .phase31_4_v2_4_execution_wiring import OPERATIONS
from .postgres_phase31_4_clean_retry_3_harness import PHASES


OUTPUT = ROOT / "docs/governance/evidence/PHASE31_4_5_RETRY5_OPERATIONAL_INPUT_MANIFEST_V1.json"


GOVERNANCE = (
    "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json",
    "docs/governance/evidence/PHASE31_4_5B_V2_4_OPERATIONAL_CORRECTION_AUTHORIZATION_V1.json",
    "docs/governance/evidence/PHASE31_4_5B_V2_4_AUTHORIZATION_PROMOTION_RECORD_V1.json",
    "docs/governance/evidence/PHASE31_4_5B_V2_3_TO_V2_4_CHANGESET_V1.json",
    "docs/governance/fixtures/PHASE31_4_5A_RETRY1_ROW_LEVEL_EXECUTION_CONTRACT_V2_3.json",
    "docs/governance/fixtures/PHASE31_4_4B_ROW_LEVEL_EXECUTION_CONTRACT_V2_2.json",
    "docs/governance/fixtures/PHASE31_4_4A_ROW_LEVEL_EXECUTION_CONTRACT_V2_1.json",
    "docs/governance/fixtures/PHASE31_4_4_ROW_LEVEL_EXECUTION_CONTRACT_V2.json",
    "docs/adr/0017-ephemeral-exact-id-governed-application-adapter.md",
    "docs/adr/0018-row-level-execution-ready-v2-contract.md",
    "docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V2.md",
    "docs/governance/PHASE31_4_4_SUPPORTING_FIXTURE_PRODUCER_CONTRACT_V1.md",
    "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json",
    "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json",
    "docs/governance/evidence/PHASE31_4_5A_AGENT_RUN_START_EVENT_SERIALIZATION_DECISION_V1.json",
    "docs/governance/evidence/PHASE31_4_5A_RETRY1_AGENTRUN_SOURCE_REACHABILITY_AND_SERIALIZATION_V1.json",
    "docs/governance/fixtures/SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_SOURCE_MANIFEST_V1.json",
    "docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_CANDIDATE_POLICY_V1.md",
    "docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_POC_POLICY_V1.md",
    "docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_ACTIVATION_POC_POLICY_V1.md",
)

ROOTS = (
    "backend/foundation/phase31_4_v2_4_support_producer.py",
    "backend/foundation/phase31_4_v2_4_execution_wiring.py",
    "backend/foundation/phase31_4_v2_4_execution_backend.py",
    "backend/foundation/phase31_4_v2_4_security_installer.py",
    "backend/foundation/phase31_4_postgres18_environment.py",
    "backend/foundation/postgres_phase31_4_clean_retry_3_harness.py",
    "backend/foundation/phase31_4_operational_manifest.py",
    "backend/foundation/test_phase31_4_v2_4_support_package.py",
    "backend/foundation/test_phase31_4_retry5_operational_manifest.py",
    "backend/foundation/generate_phase31_4_retry5_manifest.py",
)


def _digest(relative: str) -> str:
    return sha256((ROOT / relative).read_bytes()).hexdigest()


def generate() -> dict:
    migrations = tuple(next(
        path.relative_to(ROOT).as_posix()
        for path in sorted((ROOT / "backend/foundation/migrations").glob(f"{index:04d}_*.py"))
    ) for index in range(1, 24))
    sources = tuple(operation.source_path for operation in OPERATIONS)
    runtime = ("backend/manage.py", "backend/backend/settings.py",
               "backend/foundation/fixtures/adminapps_projection_events.json")
    closure_roots = sorted(set(ROOTS) | set(sources))
    closure = sorted(_local_import_closure(closure_roots))
    paths = sorted(set(GOVERNANCE) | set(migrations) | set(runtime) | set(closure))
    members = []
    for path in paths:
        if path in migrations:
            artifact_class, role = "MIGRATION", "ordered frozen schema/source operation"
        elif path in GOVERNANCE:
            artifact_class, role = "GOVERNANCE", "authorized execution input"
        elif path.endswith(".json"):
            artifact_class, role = "SOURCE_FIXTURE", "runtime/source configuration"
        elif path.endswith("settings.py") or path.endswith("manage.py"):
            artifact_class, role = "RUNTIME_CONFIGURATION", "future Clean Retry runtime"
        else:
            artifact_class, role = "IMPLEMENTATION", "project-local execution/import closure"
        members.append({
            "path": path, "artifact_class": artifact_class, "execution_role": role,
            "sha256": _digest(path), "required": True, "mutable_during_retry": False,
            "provenance": "repository byte frozen by Phase 31.4.5 Retry5",
        })
    document = {
        "schema": SCHEMA,
        "non_self_referential": True,
        "external_expected_sha256_required": True,
        "members": members,
        "order_sensitive_sets": {"migrations_0001_0023": list(migrations)},
        "phase_machine_order": list(PHASES),
        "import_roots": closure_roots,
        "import_closure": closure,
        "counts": {"members": len(members), "imports": len(closure),
                   "migrations": len(migrations), "phases": len(PHASES),
                   "named_operations": len(OPERATIONS)},
    }
    OUTPUT.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document


if __name__ == "__main__":
    generated = generate()
    print(f"members={generated['counts']['members']}")
