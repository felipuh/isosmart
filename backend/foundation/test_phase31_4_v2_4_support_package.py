"""Offline contract tests for the frozen V2.4 support package."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import tempfile
import unittest

from foundation.phase31_4_v2_4_security_installer import (
    SecurityInstaller, SecurityPlanError, assert_static_sql_safety, build_security_plan,
    teardown_plan,
)
from foundation.phase31_4_v2_4_support_producer import (
    CONTRACT_PATH, PRODUCER_IDENTIFIER, ExactSupportProducer,
    StrictBindingRenderer, UnresolvedBinding, bound_retention_port,
    build_support_plan, retain_b3_release,
)
from foundation.postgres_phase31_4_clean_retry_3_harness import (
    PHASES, CleanRetry3Harness, ConcretePhaseHandlers, PhaseTransitionError,
)
from foundation.phase31_4_v2_4_execution_wiring import (
    OPERATIONS, PRODUCER_PHASES, validate_execution_wiring,
)
from foundation.phase31_4_v2_4_execution_backend import (
    ADR0017ParityExecutor, BoundOperation, CallableExecutionPort,
    OPERATION_CLASSES, V24ExecutionSession,
    field_execution_inventory, operation_envelopes,
)
from foundation.phase31_4_postgres18_environment import (
    EnvironmentBackendError, EnvironmentIdentity, POSTGRES_IMMUTABLE_IMAGE,
    POSTGRES_IMAGE_ID,
    Postgres18EnvironmentBackend,
)


class ProducerTests(unittest.TestCase):
    def test_identifier_parameterlessness_and_exact_coverage(self):
        self.assertEqual(PRODUCER_IDENTIFIER, "phase31.4.4-exact-support-producer/v1")
        self.assertEqual(list(inspect.signature(build_support_plan).parameters), [])
        plan = build_support_plan()
        self.assertEqual(len(plan), 118)
        self.assertEqual(len({member.qualified_identity for member in plan}), 118)

    def test_v24_only_and_all_binding_kinds_are_closed(self):
        source = inspect.getsource(__import__(
            "foundation.phase31_4_v2_4_support_producer", fromlist=["*"]))
        self.assertNotIn("ROW_LEVEL_EXECUTION_CONTRACT_V2_3", source)
        contract = json.loads(CONTRACT_PATH.read_text())
        expected = set(contract["value_binding_allowed_kinds"])
        actual = {field.binding_kind for member in build_support_plan() for field in member.fields}
        self.assertTrue(actual <= expected)
        from foundation.phase31_4_v2_4_support_producer import SUPPORTED_BINDINGS
        self.assertEqual(SUPPORTED_BINDINGS, expected)

    def test_strict_renderer_does_not_coerce_or_invent_values(self):
        renderer = StrictBindingRenderer()
        field = {"name": "enabled", "schema": {"database_type": "boolean", "nullable": False},
                 "value_binding": {"kind": "EXACT_LITERAL", "typed_value": "true",
                                   "database_type_or_schema_type": "boolean"}}
        with self.assertRaises(Exception):
            renderer.render(field, {})
        deferred = {"name": "id", "schema": {"database_type": "uuid", "nullable": False},
                    "value_binding": {"kind": "NATIVE_OUTPUT",
                                      "database_type_or_schema_type": "uuid", "producer": "native"}}
        with self.assertRaises(UnresolvedBinding):
            renderer.render(deferred, {})

    def test_uuidv5_and_adr0017_bindings_render_exactly(self):
        contract = json.loads(CONTRACT_PATH.read_text())
        fields = [field for member in contract["field_bindings"] for field in member["fields"]]
        renderer = StrictBindingRenderer()
        derived = next(field for field in fields
                       if field["value_binding"]["kind"] == "DETERMINISTIC_DERIVATION")
        self.assertEqual(renderer.render(derived, {}),
                         derived["value_binding"]["expected_output"])
        mapped = next(field for field in fields
                      if field["value_binding"]["kind"] == "ADR0017_MAPPED_OUTPUT")
        self.assertEqual(renderer.render(mapped, {}),
                         mapped["value_binding"]["output_identity"])

    def test_event_outbox_audit_and_serialization_matrix(self):
        rows = ExactSupportProducer().domain_event_matrix()
        self.assertEqual(len(rows), 13)
        self.assertEqual({row.serialization_kind for row in rows}, {
            "PARENT_CREATION_IDENTITY_SERIALIZATION", "PARENT_ROW_SELECT_FOR_UPDATE",
            "SOURCE_AUTHORIZED_ADVISORY_XACT_LOCK", "SOURCE_PROVEN_TRANSACTIONAL_STATE_EXCLUSION",
        })
        self.assertTrue(all(row.event_identity_authorized and row.outbox_identity_authorized
                            and row.audit_identity_authorized for row in rows))
        inventory = ExactSupportProducer().identity_exception_inventory()
        self.assertEqual(inventory["audit_identity"], "NATIVE_UUIDV7_OUTPUT")
        self.assertEqual(len(inventory["adr0017_application_outputs"]), 7)

    def test_transaction_retention_runtime_and_phase29_prohibitions(self):
        transaction = ExactSupportProducer().transaction_contract()
        self.assertIn("immediate precommit revalidation", transaction)
        self.assertIn("postcommit canonical retention before downstream use", transaction)
        operational = json.dumps([member.__dict__ for member in build_support_plan()], default=str)
        self.assertNotIn("phase31.4.4a.synthetic", operational)
        contract = json.loads(CONTRACT_PATH.read_text())
        self.assertEqual(contract["phase29"]["operational_dependencies"], [])
        self.assertFalse(contract["promotion_flags"]["RuntimeAdoption"])

    def test_all_members_have_closed_native_phase_wiring(self):
        wiring = validate_execution_wiring()
        self.assertEqual(len(wiring), 118)
        self.assertEqual(set(PRODUCER_PHASES), {
            member.producer for member in build_support_plan()
        })
        self.assertTrue(all(operation.retention_reread and
                            operation.immediate_precommit_revalidation
                            for operation in OPERATIONS))


class SecurityInstallerTests(unittest.TestCase):
    def test_roles_policies_privileges_and_function_envelope(self):
        plan = build_security_plan()
        install = "\n".join(plan.install)
        self.assertIn("NOLOGIN NOSUPERUSER NOINHERIT NOBYPASSRLS", install)
        self.assertIn("LOGIN NOSUPERUSER NOINHERIT NOBYPASSRLS", install)
        self.assertIn("SET search_path = pg_catalog", install)
        self.assertIn("REVOKE ALL ON FUNCTION", install)
        self.assertNotIn("GRANT ALL", install)
        self.assertNotIn("USING (true)", install)
        self.assertNotIn("WITH CHECK (true)", install)
        self.assertIn("current_setting('app.tenant_id', true)::uuid", install)
        assert_static_sql_safety(plan.install)

    def test_teardown_is_complete_and_fail_closed(self):
        for values in ((False, True, 0), (True, False, 0), (True, True, 1)):
            with self.assertRaises(SecurityPlanError):
                teardown_plan(closure_complete=values[0], export_matches_live=values[1], blockers=values[2])
        teardown = "\n".join(teardown_plan(
            closure_complete=True, export_matches_live=True, blockers=0))
        self.assertIn("DROP FUNCTION", teardown)
        self.assertIn("DROP ROLE", teardown)
        self.assertNotIn("DROP TABLE", teardown)


class ExecutableWiringTests(unittest.TestCase):
    class Authority:
        def __init__(self): self.calls = []
        def read(self, operation_id):
            self.calls.append(operation_id)
            return {"authorized": True, "operation_id": operation_id, "revision": 1}

    class Port:
        def __init__(self): self.calls = []
        def begin(self, operation): self.calls.append(("begin", operation.entry_function))
        def invoke(self, operation, material):
            self.calls.append(("invoke", operation.entry_function, tuple(material)))
            return {}
        def reread(self, operation):
            self.calls.append(("reread", operation.entry_function)); return {}
        def commit(self, operation): self.calls.append(("commit", operation.entry_function))
        def rollback(self, operation): self.calls.append(("rollback", operation.entry_function))
        def checkpoint(self, phase, ledger): self.calls.append(("checkpoint", phase))

    def test_29_exact_source_operations_have_closed_classification(self):
        envelopes = operation_envelopes()
        self.assertEqual(len(envelopes), 29)
        self.assertEqual(len({row.operation.operation_id for row in envelopes}), 29)
        self.assertTrue({row.classification for row in envelopes} <= OPERATION_CLASSES)
        self.assertTrue(all(row.operation.entry_function.count(":") == 1 for row in envelopes))

    def test_every_operation_reaches_declared_source_with_fresh_precommit_authority(self):
        port, authority = self.Port(), self.Authority()
        session = V24ExecutionSession(port, authority)
        for operation in OPERATIONS:
            session.execute_operation(operation)
        invoked = [call[1] for call in port.calls if call[0] == "invoke"]
        self.assertEqual(invoked, [operation.entry_function for operation in OPERATIONS])
        self.assertEqual(authority.calls,
                         [item for operation in OPERATIONS for item in
                          (operation.operation_id, operation.operation_id)])
        self.assertEqual(len(session.ledger.retained_operations), 29)

    def test_all_1664_fields_have_concrete_execution_classification(self):
        inventory = field_execution_inventory()
        self.assertEqual(len(inventory), 1664)
        self.assertNotIn("PLAN_ONLY", {row[2] for row in inventory})

    def test_adr0017_parity_allows_only_seven_identities(self):
        keys = ExactSupportProducer().identity_exception_inventory()["adr0017_application_outputs"]
        reference = {key: "native" for key in keys}
        adapter = dict(reference)
        adapter.update({key: value for key, value in keys.items()})
        self.assertEqual(len(ADR0017ParityExecutor(reference, adapter).verify()), 7)
        adapter["business_payload"] = "changed"
        with self.assertRaises(Exception):
            ADR0017ParityExecutor(reference, adapter).verify()

    def test_concrete_callable_backend_invokes_all_exact_bound_targets(self):
        calls = []
        handlers = {}
        for operation in OPERATIONS:
            def invoke(material, selected=operation):
                calls.append(selected.entry_function); return {}
            handlers[operation.operation_id] = BoundOperation(
                operation.source_path, operation.symbol, invoke, lambda: {}
            )
        class Transaction:
            def begin(self, owner): return None
            def commit(self, owner): return None
            def rollback(self, owner): return None
            def checkpoint(self, phase, ledger): return None
        port = CallableExecutionPort(handlers, Transaction())
        for operation in OPERATIONS:
            port.invoke(operation, {})
        self.assertEqual(calls, [operation.entry_function for operation in OPERATIONS])

    def test_retention_functions_reach_bound_capture_port(self):
        class Retention:
            def __init__(self): self.calls = []
            def capture(self, name): self.calls.append(name); return {"retained": name}
        port = Retention()
        with bound_retention_port(port):
            self.assertEqual(retain_b3_release()["retained"], "B3_RELEASE")
        self.assertEqual(port.calls, ["B3_RELEASE"])


class EnvironmentBackendTests(unittest.TestCase):
    class Runner:
        def __init__(self): self.commands = []
        def run(self, argv, *, env=None):
            self.commands.append(tuple(argv))
            if tuple(argv)[:3] == ("podman", "image", "inspect"):
                return json.dumps({
                    "RepoDigests": [POSTGRES_IMMUTABLE_IMAGE],
                    "Id": "sha256:" + POSTGRES_IMAGE_ID,
                    "Os": "linux", "Architecture": "amd64",
                })
            return "PostgreSQL 18.6\n" if tuple(argv)[-2:] == ("postgres", "--version") else "ok\n"

    def backend(self):
        runner = self.Runner()
        backend = Postgres18EnvironmentBackend(
            runner, EnvironmentIdentity("retry5-test", "iso-p31-test", "iso_p31_test")
        )
        return runner, backend

    def test_command_composition_pins_18_6_and_network_none(self):
        runner, backend = self.backend()
        commands = backend.creation_commands()
        self.assertIn(POSTGRES_IMMUTABLE_IMAGE, commands[0])
        self.assertIn("none", commands[0])
        self.assertIn("--pull=never", commands[0])
        backend.create()
        self.assertEqual(runner.commands[1:], list(commands))

    def test_image_mismatch_stops_before_container_creation(self):
        for changed in (
            {"RepoDigests": ["docker.io/library/postgres:18.6"]},
            {"Id": "sha256:" + "0" * 64},
            {"Os": "windows"}, {"Architecture": "arm64"},
        ):
            runner, backend = self.backend()
            original = runner.run
            def altered(argv, *, env=None):
                result = original(argv, env=env)
                if tuple(argv)[:3] == ("podman", "image", "inspect"):
                    payload = json.loads(result)
                    payload.update(changed)
                    return json.dumps(payload)
                return result
            runner.run = altered
            with self.assertRaises(EnvironmentBackendError):
                backend.create()
            self.assertEqual(len(runner.commands), 1)

    def test_missing_image_and_wrong_server_version_fail_closed(self):
        runner, backend = self.backend()
        def missing(argv, *, env=None):
            raise FileNotFoundError("image missing")
        runner.run = missing
        with self.assertRaises(EnvironmentBackendError):
            backend.create()
        self.assertFalse(backend.created)
        runner, backend = self.backend()
        original = runner.run
        def wrong_version(argv, *, env=None):
            result = original(argv, env=env)
            return "PostgreSQL 18.5\n" if tuple(argv)[-2:] == ("postgres", "--version") else result
        runner.run = wrong_version
        with self.assertRaises(EnvironmentBackendError):
            backend.create()
        self.assertFalse(backend.created)

    def test_teardown_is_structurally_fail_closed(self):
        runner, backend = self.backend()
        backend.create()
        with self.assertRaises(EnvironmentBackendError):
            backend.guarded_teardown(p0=0, p1=1, full_closure=True,
                                     final_live_export_match=True, teardown_eligible=True)
        self.assertNotIn("rm", [part for command in runner.commands for part in command])


class HarnessTests(unittest.TestCase):
    @staticmethod
    def handlers(**updates):
        handlers = {phase: (lambda: None) for phase in PHASES}
        handlers.update(updates)
        return handlers

    def test_exact_phase_machine_and_skip_denial(self):
        self.assertEqual(len(PHASES), 33)
        harness = CleanRetry3Harness(handlers=self.handlers())
        with self.assertRaises(PhaseTransitionError):
            harness.advance("ENVIRONMENT_CREATE")

    def test_application_activation_and_teardown_are_guarded(self):
        harness = CleanRetry3Harness(handlers=self.handlers())
        for phase in PHASES[:PHASES.index("ADR0017_PARITY")]:
            harness.advance(phase)
        with self.assertRaises(PhaseTransitionError):
            harness.advance("APPLICATION")
        harness.advance("ADR0017_PARITY")
        harness.advance("APPLICATION")
        for phase in PHASES[len(harness.completed):PHASES.index("LIVE_COMPARE") + 1]:
            harness.advance(phase)
        with self.assertRaises(Exception):
            harness.authorize_teardown(closure_complete=False,
                                       export_matches_live=True, blockers=0)

    def test_protected_failure_is_retained(self):
        def fail():
            raise RuntimeError("catalog mismatch")
        harness = CleanRetry3Harness(handlers=self.handlers(PRECREATION_INTEGRITY=fail))
        with self.assertRaises(RuntimeError):
            harness.advance("PRECREATION_INTEGRITY")

    def test_missing_handler_fails_closed(self):
        harness = CleanRetry3Harness()
        with self.assertRaises(PhaseTransitionError):
            harness.advance("PRECREATION_INTEGRITY")
        self.assertIsNotNone(harness.blocked)
        self.assertFalse(harness.blocked.teardown_eligible)
        with self.assertRaises(PhaseTransitionError):
            harness.advance("PRECREATION_INTEGRITY")

    def test_concrete_factory_closes_all_33_handlers(self):
        class Session:
            def __init__(self): self.phases = []
            def execute_phase(self, phase): self.phases.append(phase)
        class Environment:
            def create(self): return None
            def configure_database(self): return None
            def apply_migrations(self): return None
            def guarded_teardown(self, **kwargs): return None
        class Installer:
            def install(self): return "INSTALLED_EXACT"
            def verify(self): return None
            def teardown(self, **kwargs): return None
        implementation = ConcretePhaseHandlers(Session(), Environment(), Installer())
        handlers = implementation.mapping()
        self.assertEqual(len(handlers), 33)
        self.assertEqual(set(handlers), set(PHASES))
        harness = CleanRetry3Harness.concrete(implementation)
        harness.advance("PRECREATION_INTEGRITY")
        self.assertEqual(implementation.session.phases, ["PRECREATION_INTEGRITY"])


if __name__ == "__main__":
    unittest.main()
