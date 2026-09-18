"""Bounded offline diagnostic runner. Never creates a test database.

Run with backend/.venv/bin/python -B from the repository root. Normal project
settings, harnesses, lifecycle commands and the RuntimeAdoption resolver are
excluded. Output is a JSON validation record, not an execution authorization.
"""

import contextlib
import functools
import io
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
COUNTS = {"database_attempts": 0, "network_attempts": 0,
          "resolver_invocations": 0, "lifecycle_attempts": 0,
          "subprocess_attempts": 0}


def deny(kind):
    COUNTS[kind] += 1
    raise RuntimeError(f"31.4.3 offline boundary: {kind}")


def audit_hook(event, args):
    if event.startswith("socket."):
        deny("network_attempts")
    if event in {"sqlite3.connect", "sqlite3.connect/handle"}:
        deny("database_attempts")
    if event in {"subprocess.Popen", "os.system", "os.fork", "os.posix_spawn"}:
        deny("subprocess_attempts")


def guarded(method, kind):
    @functools.wraps(method)
    def blocked(*args, **kwargs):
        deny(kind)
    return blocked


def main():
    sys.addaudithook(audit_hook)
    import django
    from django.conf import settings
    from django.db.backends.base.base import BaseDatabaseWrapper

    if django.get_version() != "4.2.22":
        raise RuntimeError("Django 4.2.22 required")
    if Path(sys.prefix).resolve() != (ROOT / "backend/.venv").resolve():
        raise RuntimeError("backend/.venv required")
    for method in ("connect", "ensure_connection", "cursor"):
        setattr(BaseDatabaseWrapper, method,
                guarded(getattr(BaseDatabaseWrapper, method), "database_attempts"))
    settings.configure(
        SECRET_KEY="offline-diagnostic-not-an-authority",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "foundation"],
        DATABASES={"default": {"ENGINE": "django.db.backends.dummy"}},
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField", USE_TZ=True,
        LOGGING_CONFIG=None,
    )
    django.setup()
    from foundation import controlled_opportunity, governed_learning_application, knowledge_rule_release
    classes = [
        governed_learning_application.KnowledgeLayerRuleGovernedApplicationService,
        controlled_opportunity.ControlledOpportunityActionService,
        knowledge_rule_release.KnowledgeLayerRulePublicationService,
        knowledge_rule_release.KnowledgeLayerRuleActivationService,
        knowledge_rule_release.KnowledgeLayerRuleRuntimeAdoptionService,
    ]
    for cls in classes:
        for name, method in list(vars(cls).items()):
            if not name.startswith("_") and callable(method):
                setattr(cls, name, guarded(method, "lifecycle_attempts"))
    cls = knowledge_rule_release.InertRuntimeAdoptionResolver
    cls.resolve = guarded(cls.resolve, "resolver_invocations")

    previous = json.loads((ROOT / "docs/governance/evidence/PHASE31_4_2_SUCCESSOR_DESIGN_DIAGNOSTIC_V1.json").read_text())
    labels = previous["offline_validation"]["labels"] + [
        "foundation.test_phase31_4_2_native_binding_audit",
        "foundation.test_phase31_4_3_supporting_contract_audit",
    ]
    from django.core.management import call_command
    from django.test.runner import DiscoverRunner

    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        call_command("check", verbosity=1)
        call_command("makemigrations", check=True, dry_run=True, verbosity=1)
        suite = DiscoverRunner(verbosity=1).build_suite(labels)
        result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    compiled = 0
    for path in sorted((ROOT / "backend").rglob("*.py")):
        if any(part.startswith(".") or part in {"__pycache__", "node_modules"}
               for part in path.relative_to(ROOT / "backend").parts):
            continue
        compile(path.read_bytes(), str(path), "exec")
        compiled += 1
    record = {
        "scope": "auth/contenttypes/Foundation, dummy DB, no normal project settings; source diagnostics only",
        "django_version": django.get_version(), "labels": labels,
        "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "attempts": COUNTS, "system_check": "PASS",
        "makemigrations_check_dry_run": "PASS", "compiled_count": compiled,
        "operational_tests": "NOT EXECUTED", "raw_output": output.getvalue(),
        "complete_v2_acceptance": "NOT EXECUTED: no complete V2 package exists",
        "excluded": ["all PostgreSQL harnesses", "resolver-invoking tests",
                     "Publication service revocation test", "unselected Foundation tests",
                     "normal project settings and database checks"],
    }
    print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.wasSuccessful() and not any(COUNTS.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
