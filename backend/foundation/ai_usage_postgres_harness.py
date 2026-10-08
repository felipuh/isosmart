"""Focused disposable PostgreSQL evidence for controlled AI usage production."""

import sys
import unittest

import postgres_foundation_harness as foundation_gate


def run():
    foundation_gate.configure_django()
    from django.conf import settings
    from django.core.management import call_command
    from foundation.test_value_discovery_postgres import ValueDiscoveryPostgreSQLTests

    settings.IS_DEVELOPMENT = False
    call_command("migrate", database="default", verbosity=0, interactive=False)
    suite = unittest.TestSuite([
        ValueDiscoveryPostgreSQLTests("test_controlled_execution_persists_evidence_transition_event_outbox_and_audit"),
    ])
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("AI_USAGE_CONTROLLED_POSTGRES_PASS=1")


if __name__ == "__main__":
    run()
