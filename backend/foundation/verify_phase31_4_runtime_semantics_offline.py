"""Reproduce frozen semantic blockers with all external effects denied.

Exit 1 means Stage A cannot pass, even when the diagnostic tests pass.
No production composition, migration, database or lifecycle is executed.
"""

from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
OUTPUT_PATH = ROOT / "docs/governance/evidence/PHASE31_4_FROZEN_RUNTIME_SEMANTIC_REPRODUCTION_V1.json"


def main():
    from foundation.verify_phase31_4_4_offline import COUNTS, audit_hook, guarded
    sys.addaudithook(audit_hook)
    import django
    from django.conf import settings
    from django.db.backends.base.base import BaseDatabaseWrapper
    if django.get_version() != "4.2.22" or Path(sys.prefix).resolve() != ROOT / "backend/.venv":
        raise RuntimeError("backend/.venv with Django 4.2.22 is required")
    for method in ("connect", "ensure_connection", "cursor"):
        setattr(BaseDatabaseWrapper, method,
                guarded(getattr(BaseDatabaseWrapper, method), "database_attempts"))
    settings.configure(
        SECRET_KEY="offline-semantic-diagnostic-not-authority",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "foundation"],
        DATABASES={"default": {"ENGINE": "django.db.backends.dummy"}},
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField", USE_TZ=True, LOGGING_CONFIG=None,
    )
    django.setup()
    from foundation import controlled_opportunity, governed_learning_application, knowledge_rule_release
    for cls in (
        controlled_opportunity.ControlledOpportunityActionService,
        governed_learning_application.KnowledgeLayerRuleGovernedApplicationService,
        knowledge_rule_release.KnowledgeLayerRulePublicationService,
        knowledge_rule_release.KnowledgeLayerRuleActivationService,
        knowledge_rule_release.KnowledgeLayerRuleRuntimeAdoptionService,
    ):
        for name, method in list(vars(cls).items()):
            if not name.startswith("_") and callable(method):
                setattr(cls, name, guarded(method, "lifecycle_attempts"))
    knowledge_rule_release.InertRuntimeAdoptionResolver.resolve = guarded(
        knowledge_rule_release.InertRuntimeAdoptionResolver.resolve, "resolver_invocations")

    from foundation.phase31_4_v2_4_support_producer import _contract, CONTRACT_PATH, CONTRACT_SHA256
    contract = _contract()
    pinned = {
        str(CONTRACT_PATH.relative_to(ROOT)): CONTRACT_SHA256,
        "docs/governance/evidence/PHASE31_4_SYNTHETIC_CONTROL_PLANE_AUTHORITY_FIXTURE_V1.json":
            "d6d4391e7e6023d210296895f868fa9f9e1b4fd4a80476ae95e9f327d63665d5",
        "docs/governance/evidence/PHASE31_4_SYNTHETIC_AUTHORITY_FIXTURE_AUTHORIZATION_V1.json":
            "0d9dda57c1650aa4b2ba8fcd042b6981b2b89cdae844e009edc3c1252d4bc8db",
        "docs/governance/evidence/PHASE31_4_5B_V2_4_OPERATIONAL_CORRECTION_AUTHORIZATION_V1.json":
            "4e83049a9928cd0a93c97228f33093e282c16e8e5e8969882ea21c8cd83e373b",
        "docs/governance/evidence/PHASE31_4_5B_V2_3_TO_V2_4_CHANGESET_V1.json":
            "4204d022492de843d7f6763dfb05f3ce7ec5e166fc4c14de4b8b2c4cb80f27de",
        **contract["frozen_source_integrity"]["authoritative_file_sha256"],
        **contract["frozen_source_integrity"]["migration_file_sha256"],
        **contract["remaining_domain_event_source_audit"]["authoritative_source_sha256"],
    }
    # Preserve ADR-0017 against the historical manifest, without treating the
    # obsolete runtime member hashes as authority for new implementation.
    old_manifest = json.loads((ROOT / "docs/governance/evidence/PHASE31_4_5_RETRY5_OPERATIONAL_INPUT_MANIFEST_V1.json").read_text())
    for member in old_manifest["members"]:
        if member["path"] == "docs/adr/0017-ephemeral-exact-id-governed-application-adapter.md":
            pinned[member["path"]] = member["sha256"]
    integrity = {path: {"expected": digest, "observed": sha256((ROOT / path).read_bytes()).hexdigest()}
                 for path, digest in sorted(pinned.items())}
    if any(row["expected"] != row["observed"] for row in integrity.values()):
        raise RuntimeError("protected source integrity failure")
    if any((ROOT / "backend/foundation/migrations").glob("0024*")):
        raise RuntimeError("migration 0024 forbidden")

    predecessor = json.loads((ROOT / "docs/governance/evidence/PHASE31_4_2_SUCCESSOR_DESIGN_DIAGNOSTIC_V1.json").read_text())
    labels = predecessor["offline_validation"]["labels"] + [
        "foundation." + path.stem for path in sorted((ROOT / "backend/foundation").glob("test_phase31*.py"))
        if "foundation." + path.stem not in predecessor["offline_validation"]["labels"]
    ]
    from django.core.management import call_command
    from django.test.runner import DiscoverRunner
    output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        call_command("check", verbosity=1)
        call_command("makemigrations", check=True, dry_run=True, verbosity=1)
        suite = DiscoverRunner(verbosity=1).build_suite(labels)
        result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    compiled = 0
    for path in sorted((ROOT / "backend").rglob("*.py")):
        if any(part.startswith(".") or part == "__pycache__"
               for part in path.relative_to(ROOT / "backend").parts):
            continue
        compile(path.read_bytes(), str(path), "exec")
        compiled += 1
    parsed = 0
    for path in sorted((ROOT / "docs/governance").rglob("*.json")):
        if path == OUTPUT_PATH:
            continue  # This run's output is serialized and checked after the suite.
        json.loads(path.read_text(encoding="utf-8"))
        parsed += 1
    diagnostic_module = "foundation.test_phase31_4_frozen_runtime_semantics"
    unconfirmed = [test.id() for test, _ in result.errors + result.failures + result.skipped
                   if test.id().startswith(diagnostic_module + ".")]
    if unconfirmed:
        raise RuntimeError("semantic reproduction did not pass: " + ", ".join(unconfirmed)
                           + "\n" + output.getvalue())
    print(json.dumps({
        "schema": "phase31.4-frozen-runtime-semantic-reproduction/v1",
        "verdict": "NOT_PROMOTED", "stage": "A",
        "reason": "Frozen business material contradicts native validation; diagnostic successes are not lifecycle passes",
        "semantic_blockers": ["P1-FROZEN-ACTION-PLAN-PRECONDITIONS", "P1-FROZEN-CONTROLLED-OPPORTUNITY-GOVERNANCE"],
        "offline_P0": 0, "offline_P1_semantic_blockers": 2,
        "django_version": django.get_version(), "labels": labels,
        "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "attempts": dict(COUNTS), "postgresql_start_attempts": 0,
        "container_start_attempts": 0, "system_check": "PASS",
        "makemigrations_check_dry_run": "PASS", "compiled_count": compiled,
        "parsed_governance_json_count": parsed, "protected_integrity": integrity,
        "migration_0024_absent": True, "stage_b_executed": False,
        "production_composition_proved": False, "successor_manifest_created": False,
        "raw_output": output.getvalue(),
        "semantic_reproduction_tests_passed": 4,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
