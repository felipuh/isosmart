"""Focused offline tests for the reusable Phase 31.4 V2.5 runner.

The test suite deliberately uses an in-memory container-engine fake.  It
exercises the durable authorization, manifest, recovery, and state-machine
contracts without contacting Podman, Docker, PostgreSQL, or AdminApps.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from typing import Any, Mapping, Sequence

from .phase31_4_v2_5_disposable_runner import (
    AUTH_LABEL,
    CONSUMPTION_NAME,
    DIAGNOSTIC_CLASSIFICATION,
    EVIDENCE_EXECUTION,
    MANIFEST_NAME,
    POSTGRES_IMAGE_ID,
    POSTGRES_IMMUTABLE_IMAGE,
    POSTGRES_VERSION_PREFIX,
    PROTECTED_RUNNER_PATHS,
    ROLE_LABEL,
    RUN_LABEL,
    CommandResult,
    DisposableEvidenceRunner,
    RunInputs,
    RunnerError,
    RunState,
    StateTransitionError,
    canonical_run_slug,
    verify_authorization,
)


_UNSET = object()


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class RunnerArtifacts:
    inputs: RunInputs
    authorization_path: Path
    integrity_path: Path
    evidence_root: Path
    consumption_registry: Path


class FakeDatabaseProbe:
    def __init__(self, *, result: int = 1, error: BaseException | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def wait_for_select_one(self, **kwargs: Any) -> int:
        self.calls.append(dict(kwargs))
        if self.error is not None:
            raise self.error
        return self.result


class FakePodmanExecutor:
    """Small stateful Podman substitute with injectable command failures."""

    def __init__(
        self,
        *,
        fail_action: str | None = None,
        fail_occurrence: int = 1,
        raise_action: str | None = None,
        raised: BaseException | None = None,
    ) -> None:
        self.fail_action = fail_action
        self.fail_occurrence = fail_occurrence
        self.raise_action = raise_action
        self.raised = raised or RuntimeError("injected command exception")
        self.commands: list[tuple[str, ...]] = []
        self.action_counts: Counter[str] = Counter()
        self.resources: dict[str, dict[str, dict[str, Any]]] = {
            "container": {},
            "volume": {},
            "network": {},
        }
        self.removed: list[tuple[str, str]] = []
        self._next_port = 54000

    @staticmethod
    def _labels(argv: Sequence[str]) -> dict[str, str]:
        labels: dict[str, str] = {}
        for index, part in enumerate(argv[:-1]):
            if part == "--label":
                key, value = argv[index + 1].split("=", 1)
                labels[key] = value
        return labels

    @staticmethod
    def _action(argv: tuple[str, ...]) -> str:
        if argv[:3] == ("podman", "image", "inspect"):
            return "image_inspect"
        if argv[:3] == ("podman", "volume", "create"):
            return "volume_create"
        if argv[:3] == ("podman", "network", "create"):
            return "network_create"
        if argv[:2] == ("podman", "create"):
            return "container_create"
        if argv[:4] == ("podman", "container", "inspect", "--format"):
            if "NetworkSettings.Ports" in argv[4]:
                return "port_inspect"
            return "cleanup_container_inspect"
        if len(argv) >= 4 and argv[0] == "podman" and argv[2:4] == ("inspect", "--format"):
            return f"cleanup_{argv[1]}_inspect"
        if argv[:2] == ("podman", "start"):
            return "postgres_start"
        if argv[:2] == ("podman", "exec"):
            return "postgres_version"
        if argv[:2] == ("podman", "logs"):
            return "postgres_logs"
        if len(argv) >= 3 and argv[0] == "podman" and argv[2] == "exists":
            return f"cleanup_{argv[1]}_exists"
        if argv[:3] == ("podman", "rm", "--force"):
            return "cleanup_container_remove"
        if len(argv) >= 3 and argv[0] == "podman" and argv[2] == "rm":
            return f"cleanup_{argv[1]}_remove"
        return "unexpected"

    def _injected_result(self, action: str) -> CommandResult | None:
        self.action_counts[action] += 1
        occurrence = self.action_counts[action]
        if action == self.raise_action and occurrence == self.fail_occurrence:
            raise self.raised
        if action == self.fail_action and occurrence == self.fail_occurrence:
            return CommandResult(125, stderr=f"injected {action} failure")
        return None

    def _inspect(self, kind: str, name: str) -> CommandResult:
        resource = self.resources[kind].get(name)
        if resource is None:
            return CommandResult(125, stderr=f"no such {kind}: {name}")
        return CommandResult(0, stdout=json.dumps(resource["labels"]))

    def run(self, argv: Sequence[str]) -> CommandResult:
        command = tuple(str(part) for part in argv)
        self.commands.append(command)
        action = self._action(command)
        injected = self._injected_result(action)
        if injected is not None:
            return injected

        if action == "image_inspect":
            return CommandResult(
                0,
                stdout=json.dumps(
                    {
                        "RepoDigests": [POSTGRES_IMMUTABLE_IMAGE],
                        "Id": "sha256:" + POSTGRES_IMAGE_ID,
                        "Os": "linux",
                        "Architecture": "amd64",
                    }
                ),
            )
        if action in {"volume_create", "network_create"}:
            kind = action.removesuffix("_create")
            name = command[-1]
            self.resources[kind][name] = {
                "labels": self._labels(command),
                "id": f"{kind}-id-{len(self.resources[kind]) + 1}",
            }
            return CommandResult(0, stdout=self.resources[kind][name]["id"])
        if action == "container_create":
            name = command[command.index("--name") + 1]
            container_id = f"container-id-{len(self.resources['container']) + 1}"
            self.resources["container"][name] = {
                "labels": self._labels(command),
                "id": container_id,
                "port": None,
            }
            return CommandResult(0, stdout=container_id)
        if action == "port_inspect":
            name = command[-1]
            resource = self.resources["container"].get(name)
            if resource is None:
                return CommandResult(125, stderr=f"no such container: {name}")
            if resource["port"] is None:
                self._next_port += 1
                resource["port"] = self._next_port
            return CommandResult(
                0,
                stdout=json.dumps(
                    {
                        "5432/tcp": [
                            {"HostIp": "127.0.0.1", "HostPort": str(resource["port"])}
                        ]
                    }
                ),
            )
        if action.startswith("cleanup_") and action.endswith("_inspect"):
            kind = action.removeprefix("cleanup_").removesuffix("_inspect")
            return self._inspect(kind, command[-1])
        if action == "postgres_start":
            return CommandResult(0, stdout=command[-1])
        if action == "postgres_version":
            return CommandResult(0, stdout=POSTGRES_VERSION_PREFIX + " (Debian build)")
        if action == "postgres_logs":
            return CommandResult(0, stdout="synthetic postgres log\n")
        if action.startswith("cleanup_") and action.endswith("_exists"):
            kind = action.removeprefix("cleanup_").removesuffix("_exists")
            return CommandResult(0 if command[-1] in self.resources[kind] else 1)
        if action.startswith("cleanup_") and action.endswith("_remove"):
            kind = action.removeprefix("cleanup_").removesuffix("_remove")
            name = command[-1]
            if name not in self.resources[kind]:
                return CommandResult(125, stderr=f"no such {kind}: {name}")
            del self.resources[kind][name]
            self.removed.append((kind, name))
            return CommandResult(0, stdout=name)
        raise AssertionError(f"unexpected fake command: {command!r}")


class DisposableEvidenceRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _artifacts(
        self,
        *,
        run_id: str = "Phase 31.4 V2.5 Disposable Unit Run A",
        execution_kind: str = EVIDENCE_EXECUTION,
        explicit_slug: object = _UNSET,
        evidence_slug: str | None = None,
        protect_runner: bool = True,
        run_executed: object = "NO",
    ) -> RunnerArtifacts:
        canonical = canonical_run_slug(run_id)
        selected_slug = (
            evidence_slug
            if evidence_slug is not None
            else str(explicit_slug) if explicit_slug is not _UNSET else canonical
        )
        evidence_root = self.root / "docs/governance/evidence/runs" / selected_slug
        registry = self.root / "docs/governance/evidence/unit_authorization_consumptions"

        protected_paths = (
            list(PROTECTED_RUNNER_PATHS)
            if protect_runner
            else ["backend/foundation/non_runner_control.py"]
        )
        sources: list[dict[str, str]] = []
        for index, relative in enumerate(protected_paths, start=1):
            source = self.root / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(f"synthetic protected source {index}\n", encoding="utf-8")
            sources.append({"path": relative, "sha256": _digest(source)})

        integrity_path = self.root / "docs/governance/evidence/CURRENT_UNIT_INTEGRITY.json"
        self._write_json(
            integrity_path,
            {
                "generation": "UNIT-GENERATION-1",
                "sources": sources,
                "migration_file_sha256": {},
            },
        )
        integrity_sha = _digest(integrity_path)

        authorization: dict[str, Any] = {
            "run_id": run_id,
            "authorization_status": (
                "RUNNER_ENVIRONMENT_DIAGNOSTIC_AUTHORIZED"
                if execution_kind == DIAGNOSTIC_CLASSIFICATION
                else "DISPOSABLE_EVIDENCE_RUN_AUTHORIZED"
            ),
            "run_executed": run_executed,
            "execution_kind": execution_kind,
            "evidence_root": evidence_root.relative_to(self.root).as_posix(),
            "integrity": {
                "artifact_path": integrity_path.relative_to(self.root).as_posix(),
                "sha256": integrity_sha,
            },
        }
        if explicit_slug is not _UNSET:
            authorization["canonical_run_slug"] = explicit_slug
        authorization_path = (
            self.root / "docs/governance/authorizations" / f"{selected_slug}.json"
        )
        self._write_json(authorization_path, authorization)

        inputs = RunInputs(
            repository_root=self.root,
            run_id=run_id,
            authorization_artifact=authorization_path,
            expected_authorization_sha256=_digest(authorization_path),
            current_integrity_generation="UNIT-GENERATION-1",
            expected_integrity_sha256=integrity_sha,
            evidence_root=evidence_root,
            execution_kind=execution_kind,
            consumption_registry=registry,
            validation_attempt=1,
            readiness_timeout_seconds=0.25,
        )
        return RunnerArtifacts(
            inputs=inputs,
            authorization_path=authorization_path,
            integrity_path=integrity_path,
            evidence_root=evidence_root,
            consumption_registry=registry,
        )

    @staticmethod
    def _persisted(artifacts: RunnerArtifacts) -> dict[str, Any]:
        return json.loads((artifacts.evidence_root / MANIFEST_NAME).read_text(encoding="utf-8"))

    def test_fresh_authorization_is_consumed_once_and_initial_manifest_is_durable(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor()

        manifest = DisposableEvidenceRunner(artifacts.inputs, executor=executor).prepare()

        self.assertEqual(manifest["current_state"], RunState.AUTHORIZED.value)
        self.assertTrue(manifest["authorization"]["consumed"])
        self.assertEqual(executor.commands, [])
        self.assertTrue((artifacts.evidence_root / CONSUMPTION_NAME).is_file())
        registry_record = artifacts.consumption_registry / (
            f"{artifacts.inputs.expected_authorization_sha256}.json"
        )
        self.assertTrue(registry_record.is_file())
        self.assertEqual(self._persisted(artifacts)["current_state"], "AUTHORIZED")

    def test_consumed_authorization_fails_closed_before_any_resource_command(self) -> None:
        artifacts = self._artifacts()
        DisposableEvidenceRunner(artifacts.inputs, executor=FakePodmanExecutor()).prepare()
        second_executor = FakePodmanExecutor()

        with self.assertRaises(RunnerError) as raised:
            DisposableEvidenceRunner(artifacts.inputs, executor=second_executor).prepare()

        self.assertEqual(raised.exception.code, "AUTHORIZATION_ALREADY_CONSUMED")
        self.assertEqual(second_executor.commands, [])

    def test_consumed_retry19_authorization_cannot_resume_or_change_historical_evidence(self) -> None:
        artifacts = self._artifacts(
            run_id="Phase 31.4 V2.5 Clean Retry 19",
            run_executed="YES",
        )
        artifacts.evidence_root.mkdir(parents=True)
        historical = artifacts.evidence_root / "historical-state.json"
        historical.write_text('{"state":"CONSUMED / FAILED"}\n', encoding="utf-8")
        before = historical.read_bytes()
        executor = FakePodmanExecutor()

        with self.assertRaises(RunnerError) as raised:
            DisposableEvidenceRunner(artifacts.inputs, executor=executor).prepare()

        self.assertEqual(raised.exception.code, "AUTHORIZATION_ALREADY_CONSUMED")
        self.assertEqual(executor.commands, [])
        self.assertEqual(historical.read_bytes(), before)
        self.assertFalse((artifacts.evidence_root / MANIFEST_NAME).exists())

    def test_nonempty_evidence_root_collision_fails_before_consumption(self) -> None:
        artifacts = self._artifacts()
        artifacts.evidence_root.mkdir(parents=True)
        (artifacts.evidence_root / "foreign-evidence.json").write_text("{}\n", encoding="utf-8")

        with self.assertRaises(RunnerError) as raised:
            DisposableEvidenceRunner(artifacts.inputs, executor=FakePodmanExecutor()).prepare()

        self.assertEqual(raised.exception.code, "EVIDENCE_ROOT_COLLISION")
        self.assertFalse(artifacts.consumption_registry.exists())
        self.assertFalse((artifacts.evidence_root / MANIFEST_NAME).exists())

    def test_canonical_slug_is_deterministic_and_preserves_version_punctuation(self) -> None:
        run_id = "Phase 31.4 V2.5 Clean Retry UNIT"
        expected = "Phase_31.4_V2.5_Clean_Retry_UNIT"

        self.assertEqual(canonical_run_slug(run_id), expected)
        self.assertEqual(canonical_run_slug(f"  {run_id}  "), expected)

    def test_divergent_explicit_slug_is_not_a_second_valid_run_identity(self) -> None:
        run_id = "Phase 31.4 V2.5 Clean Retry UNIT"
        divergent = "Phase_31.4.V2.5_Clean_Retry_UNIT"
        artifacts = self._artifacts(
            run_id=run_id,
            explicit_slug=divergent,
            evidence_slug=divergent,
        )

        with self.assertRaises(RunnerError):
            verify_authorization(artifacts.inputs)

    def test_allocation_failure_persists_failed_state_and_command_evidence(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor(fail_action="volume_create")
        runner = DisposableEvidenceRunner(
            artifacts.inputs, executor=executor, database_probe=FakeDatabaseProbe()
        )

        with self.assertRaises(RunnerError) as raised:
            runner.start_to_ready(("adminapps",))

        self.assertEqual(raised.exception.code, "VOLUME_CREATION_FAILURE")
        persisted = self._persisted(artifacts)
        self.assertEqual(persisted["current_state"], "FAILED")
        self.assertEqual(persisted["last_confirmed_state"], "FAILED")
        self.assertEqual(persisted["allocation_state"], "FAILED")
        self.assertEqual(persisted["failure"]["domain"], "DISPOSABLE_EXECUTION_TOOLING_BLOCKER")
        failed_commands = [
            command for command in persisted["command_history"] if command["status"] == "FAIL"
        ]
        self.assertEqual([command["step"] for command in failed_commands], ["allocate_adminapps_volume"])

    def test_unexpected_tooling_exception_before_bootstrap_retains_traceback(self) -> None:
        artifacts = self._artifacts()

        class ExplodingRunner(DisposableEvidenceRunner):
            def _verify_image(self) -> None:
                raise ValueError("synthetic allocator defect")

        runner = ExplodingRunner(
            artifacts.inputs,
            executor=FakePodmanExecutor(),
            database_probe=FakeDatabaseProbe(),
        )
        with self.assertRaisesRegex(ValueError, "allocator defect"):
            runner.start_to_ready(("adminapps",))

        persisted = self._persisted(artifacts)
        failure = persisted["failure"]
        self.assertEqual(failure["code"], "TOOLING_EXCEPTION_BEFORE_BOOTSTRAP")
        self.assertEqual(failure["domain"], "DISPOSABLE_EXECUTION_TOOLING_BLOCKER")
        self.assertEqual(failure["state_at_failure"], "ALLOCATING")
        self.assertEqual(failure["exception_type"], "ValueError")
        self.assertIn("synthetic allocator defect", failure["traceback"])
        self.assertIn("ValueError", failure["traceback"])

    def test_partial_allocation_records_known_resources_before_failure(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor(fail_action="network_create")
        runner = DisposableEvidenceRunner(
            artifacts.inputs, executor=executor, database_probe=FakeDatabaseProbe()
        )

        with self.assertRaises(RunnerError) as raised:
            runner.start_to_ready(("adminapps",))

        self.assertEqual(raised.exception.code, "NETWORK_CREATION_FAILURE")
        persisted = self._persisted(artifacts)
        resource = persisted["resources"]["adminapps"]
        self.assertEqual(resource["volume_status"], "CREATED")
        self.assertIsNotNone(resource["volume_id"])
        self.assertEqual(resource["network_status"], "INTENDED")
        self.assertEqual(resource["container_status"], "INTENDED")
        self.assertTrue(resource["cleanup_required"])
        self.assertEqual(
            [event["event"] for event in persisted["resource_events"]],
            ["RESOURCE_INTENT_PERSISTED", "VOLUME_CREATED"],
        )
        self.assertIn(resource["volume_name"], executor.resources["volume"])

    def test_cleanup_after_partial_allocation_removes_only_manifest_scoped_resources(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor(fail_action="volume_create", fail_occurrence=2)
        runner = DisposableEvidenceRunner(
            artifacts.inputs, executor=executor, database_probe=FakeDatabaseProbe()
        )
        with self.assertRaises(RunnerError):
            runner.start_to_ready(("adminapps", "isosmart"))

        executor.resources["volume"]["foreign-volume"] = {
            "labels": {RUN_LABEL: "foreign-run", AUTH_LABEL: "0" * 64, ROLE_LABEL: "foreign"},
            "id": "foreign-id",
        }
        before_cleanup = self._persisted(artifacts)
        first = before_cleanup["resources"]["adminapps"]
        expected_removed = {
            ("container", first["container_name"]),
            ("volume", first["volume_name"]),
            ("network", first["network_name"]),
        }

        cleaned = runner.cleanup()

        self.assertEqual(set(executor.removed), expected_removed)
        self.assertIn("foreign-volume", executor.resources["volume"])
        self.assertFalse(any("prune" in command for command in executor.commands))
        self.assertEqual(cleaned["cleanup"]["status"], "PASS")
        self.assertEqual(cleaned["current_state"], "TEARDOWN_COMPLETE")

    def test_cleanup_refuses_a_manifest_name_with_foreign_labels(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor(fail_action="network_create")
        runner = DisposableEvidenceRunner(
            artifacts.inputs, executor=executor, database_probe=FakeDatabaseProbe()
        )
        with self.assertRaises(RunnerError):
            runner.start_to_ready(("adminapps",))
        resource = dict(runner.manifest["resources"]["adminapps"])
        volume_name = resource["volume_name"]
        executor.resources["volume"][volume_name]["labels"][RUN_LABEL] = "foreign-run"

        with self.assertRaises(RunnerError) as raised:
            runner.cleanup()

        self.assertEqual(raised.exception.code, "CLEANUP_INCOMPLETE")
        self.assertIn(volume_name, executor.resources["volume"])
        self.assertNotIn(("volume", volume_name), executor.removed)
        persisted = self._persisted(artifacts)
        self.assertEqual(persisted["cleanup"]["status"], "FAIL")
        self.assertIn("refusing to remove unscoped volume", persisted["cleanup"]["errors"][0]["exception"])

    def test_interruption_manifest_supports_cleanup_only_recovery(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor(
            raise_action="port_inspect",
            raised=KeyboardInterrupt("synthetic process interruption"),
        )
        runner = DisposableEvidenceRunner(
            artifacts.inputs, executor=executor, database_probe=FakeDatabaseProbe()
        )

        with self.assertRaises(KeyboardInterrupt):
            runner.start_to_ready(("adminapps",))

        interrupted = self._persisted(artifacts)
        self.assertEqual(interrupted["current_state"], "FAILED")
        self.assertEqual(interrupted["failure"]["code"], "RUNNER_PROCESS_INTERRUPTION")
        self.assertEqual(interrupted["resources"]["adminapps"]["container_status"], "CREATED")
        self.assertEqual(interrupted["command_history"][-1]["status"], "EXCEPTION")

        recovered = DisposableEvidenceRunner.recover_for_cleanup(
            repository_root=self.root,
            evidence_root=artifacts.evidence_root,
            executor=executor,
        )
        for operation in (
            lambda: recovered.allocate(("adminapps",)),
            recovered.bootstrap,
        ):
            with self.assertRaises(RunnerError) as raised:
                operation()
            self.assertEqual(raised.exception.code, "RECOVERY_IS_CLEANUP_ONLY")

        cleaned = recovered.cleanup()
        self.assertEqual(cleaned["current_state"], "TEARDOWN_COMPLETE")
        self.assertEqual(cleaned["business_outcome"], "FAILED")
        self.assertEqual(cleaned["cleanup"]["remaining_resources"], [])
        self.assertTrue(cleaned["cleanup"]["post_teardown_absence_verified"])

    def test_successful_allocation_and_postgres_proof_advance_exactly_to_ready(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor()
        probe = FakeDatabaseProbe(result=1)
        runner = DisposableEvidenceRunner(
            artifacts.inputs, executor=executor, database_probe=probe
        )

        manifest = runner.start_to_ready(("adminapps", "isosmart"))

        self.assertEqual(
            [transition["to"] for transition in manifest["state_transitions"]],
            ["AUTHORIZED", "ALLOCATING", "RESOURCES_ALLOCATED", "BOOTSTRAPPING", "READY"],
        )
        self.assertEqual(manifest["allocation_state"], "SUCCEEDED")
        self.assertEqual(len(manifest["host_ports"]), 2)
        self.assertEqual(len(set(manifest["host_ports"])), 2)
        self.assertEqual(len(probe.calls), 2)
        for role, resource in manifest["resources"].items():
            self.assertEqual(resource["postgresql_status"], "READY", role)
            self.assertEqual(resource["connection_result"], "PASS", role)
            self.assertEqual(resource["select_one_result"], 1, role)
        self.assertEqual(self._persisted(artifacts)["current_state"], "READY")

    def test_postgresql_failure_after_allocation_has_runtime_domain(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor(fail_action="postgres_start")
        runner = DisposableEvidenceRunner(
            artifacts.inputs, executor=executor, database_probe=FakeDatabaseProbe()
        )

        with self.assertRaises(RunnerError) as raised:
            runner.start_to_ready(("adminapps",))

        self.assertEqual(raised.exception.code, "POSTGRES_STARTUP_FAILURE")
        self.assertEqual(raised.exception.domain, "POSTGRESQL_RUNTIME_BLOCKER")
        persisted = self._persisted(artifacts)
        self.assertEqual(persisted["allocation_state"], "SUCCEEDED")
        self.assertEqual(persisted["failure"]["domain"], "POSTGRESQL_RUNTIME_BLOCKER")
        self.assertEqual(persisted["failure"]["state_at_failure"], "BOOTSTRAPPING")
        self.assertEqual(persisted["current_state"], "FAILED")

    def test_state_machine_denies_skipping_from_authorized_to_bootstrapping(self) -> None:
        artifacts = self._artifacts()
        executor = FakePodmanExecutor()
        runner = DisposableEvidenceRunner(
            artifacts.inputs, executor=executor, database_probe=FakeDatabaseProbe()
        )
        runner.prepare()

        with self.assertRaises(StateTransitionError) as raised:
            runner.bootstrap()

        self.assertEqual(raised.exception.code, "INVALID_STATE_TRANSITION")
        self.assertEqual(runner.manifest["current_state"], "AUTHORIZED")
        self.assertEqual(executor.commands, [])

    def _ready_runner(
        self, *, execution_kind: str = EVIDENCE_EXECUTION, suffix: str = ""
    ) -> tuple[RunnerArtifacts, DisposableEvidenceRunner]:
        artifacts = self._artifacts(
            run_id=f"Phase 31.4 V2.5 {execution_kind} State Machine Unit {suffix}".strip(),
            execution_kind=execution_kind,
        )
        runner = DisposableEvidenceRunner(
            artifacts.inputs,
            executor=FakePodmanExecutor(),
            database_probe=FakeDatabaseProbe(),
        )
        runner.start_to_ready(("adminapps", "isosmart"))
        return artifacts, runner

    def test_precreation_and_stage_ext_follow_the_explicit_graph(self) -> None:
        artifacts, runner = self._ready_runner()

        runner._transition(RunState.PRECREATION_RUNNING, reason="unit precreation start")
        runner._transition(RunState.PRECREATION_PASS, reason="unit precreation pass")
        runner._transition(RunState.STAGE_EXT_RUNNING, reason="unit stage ext start")

        persisted = self._persisted(artifacts)
        self.assertEqual(
            [item["to"] for item in persisted["state_transitions"]],
            [
                "AUTHORIZED", "ALLOCATING", "RESOURCES_ALLOCATED", "BOOTSTRAPPING",
                "READY", "PRECREATION_RUNNING", "PRECREATION_PASS", "STAGE_EXT_RUNNING",
            ],
        )
        for transition in persisted["state_transitions"]:
            self.assertEqual(transition["run_id"], artifacts.inputs.run_id)
            self.assertEqual(transition["execution_kind"], EVIDENCE_EXECUTION)
            self.assertIn("run_slug", transition)
            self.assertIn("validation_attempt", transition)

    def test_precreation_and_stage_ext_running_can_fail_then_teardown(self) -> None:
        for terminal_before_failure in (
            RunState.PRECREATION_RUNNING,
            RunState.PRECREATION_PASS,
            RunState.STAGE_EXT_RUNNING,
        ):
            with self.subTest(state=terminal_before_failure.value):
                artifacts, runner = self._ready_runner(suffix=terminal_before_failure.value)
                runner._transition(RunState.PRECREATION_RUNNING, reason="unit start")
                if terminal_before_failure in {RunState.PRECREATION_PASS, RunState.STAGE_EXT_RUNNING}:
                    runner._transition(RunState.PRECREATION_PASS, reason="unit pass")
                if terminal_before_failure == RunState.STAGE_EXT_RUNNING:
                    runner._transition(RunState.STAGE_EXT_RUNNING, reason="unit stage")
                runner._transition(RunState.FAILED, reason="unit failure")
                runner.cleanup()
                self.assertEqual(self._persisted(artifacts)["current_state"], "TEARDOWN_COMPLETE")

    def test_state_machine_rejects_precreation_stage_skips_and_terminal_replay(self) -> None:
        artifacts = self._artifacts()
        runner = DisposableEvidenceRunner(
            artifacts.inputs,
            executor=FakePodmanExecutor(),
            database_probe=FakeDatabaseProbe(),
        )
        runner.prepare()
        with self.assertRaises(StateTransitionError):
            runner._transition(RunState.PRECREATION_RUNNING, reason="invalid early precreation")

        _, ready = self._ready_runner()
        with self.assertRaises(StateTransitionError):
            ready._transition(RunState.STAGE_EXT_RUNNING, reason="invalid stage skip")
        ready._transition(RunState.PRECREATION_RUNNING, reason="unit start")
        ready._transition(RunState.PRECREATION_PASS, reason="unit pass")
        with self.assertRaises(StateTransitionError):
            ready._transition(RunState.PRECREATION_PASS, reason="invalid terminal replay")

    def test_precreation_rejects_a_premature_or_non_durable_ready_manifest(self) -> None:
        _, runner = self._ready_runner()
        runner._manifest["resources"]["isosmart"]["postgresql_status"] = "STARTED"
        with self.assertRaises(RunnerError) as raised:
            runner._transition(RunState.PRECREATION_RUNNING, reason="invalid premature ready")
        self.assertEqual(raised.exception.code, "PRECREATION_READINESS_INVARIANT_FAILURE")
        self.assertEqual(runner.manifest["current_state"], "READY")

    def test_diagnostic_and_formal_modes_share_protected_operational_transitions(self) -> None:
        for execution_kind in (DIAGNOSTIC_CLASSIFICATION, EVIDENCE_EXECUTION):
            with self.subTest(execution_kind=execution_kind):
                artifacts = self._artifacts(
                    run_id=f"Phase 31.4 V2.5 {execution_kind} Shared Path Unit",
                    execution_kind=execution_kind,
                )
                runner = DisposableEvidenceRunner(
                    artifacts.inputs,
                    executor=FakePodmanExecutor(),
                    database_probe=FakeDatabaseProbe(),
                )
                runner.run_evidence(
                    precreation=lambda manifest: {"status": "PASS"},
                    stage_ext=lambda manifest: {"status": "PASS"},
                )
                persisted = self._persisted(artifacts)
                self.assertEqual(persisted["current_state"], "TEARDOWN_COMPLETE")
                self.assertEqual(
                    [item["to"] for item in persisted["state_transitions"]][4:],
                    [
                        "READY", "PRECREATION_RUNNING", "PRECREATION_PASS",
                        "STAGE_EXT_RUNNING", "STAGE_EXT_PASS", "COMPLETED",
                        "TEARDOWN_COMPLETE",
                    ],
                )
                self.assertTrue(all(
                    item["execution_kind"] == execution_kind
                    for item in persisted["state_transitions"]
                ))

    def test_diagnostic_precreation_failure_is_persisted_and_cleaned_up(self) -> None:
        artifacts = self._artifacts(
            run_id="Phase 31.4 V2.5 Diagnostic Precreation Failure Unit",
            execution_kind=DIAGNOSTIC_CLASSIFICATION,
        )
        runner = DisposableEvidenceRunner(
            artifacts.inputs,
            executor=FakePodmanExecutor(),
            database_probe=FakeDatabaseProbe(),
        )

        with self.assertRaises(RunnerError) as raised:
            runner.run_evidence(
                precreation=lambda manifest: {"status": "FAIL"},
                stage_ext=lambda manifest: self.fail("Stage EXT must not run"),
            )

        self.assertEqual(raised.exception.code, "PRECREATION_FAILURE")
        persisted = self._persisted(artifacts)
        self.assertEqual(persisted["current_state"], "TEARDOWN_COMPLETE")
        self.assertEqual(persisted["business_outcome"], "FAILED")
        self.assertEqual(persisted["cleanup"]["status"], "PASS")
        self.assertEqual(
            [item["to"] for item in persisted["state_transitions"]][-3:],
            ["PRECREATION_RUNNING", "FAILED", "TEARDOWN_COMPLETE"],
        )

    def test_formal_evidence_is_denied_while_runner_is_outside_integrity(self) -> None:
        formal = self._artifacts(protect_runner=False)

        with self.assertRaises(RunnerError) as raised:
            DisposableEvidenceRunner(formal.inputs, executor=FakePodmanExecutor()).prepare()

        self.assertEqual(raised.exception.code, "RUNNER_SOURCE_NOT_IN_INTEGRITY_GENERATION")
        self.assertFalse(formal.evidence_root.exists())
        self.assertFalse(formal.consumption_registry.exists())

        diagnostic = self._artifacts(
            run_id="Phase 31.4 V2.5 Runner Environment Diagnostic Unit",
            execution_kind=DIAGNOSTIC_CLASSIFICATION,
            protect_runner=False,
        )
        diagnostic_manifest = DisposableEvidenceRunner(
            diagnostic.inputs, executor=FakePodmanExecutor()
        ).prepare()
        self.assertTrue(diagnostic_manifest["integrity"]["reconciliation_required"])
        self.assertFalse(diagnostic_manifest["integrity"]["runner_sources_protected"])

    def test_versioned_authorizations_coexist_and_old_is_superseded(self) -> None:
        artifacts = self._artifacts()
        artifacts.evidence_root.mkdir(parents=True)
        directory = artifacts.evidence_root / "authorizations"
        old_path = directory / "authorization_v5.json"
        old_document = json.loads(artifacts.authorization_path.read_text(encoding="utf-8"))
        old_document.update(authorization_id="retry20-v5", issued_at="2026-09-23T00:00:00Z",
                            baseline_generation="UNIT-GENERATION-1",
                            baseline_sha256=_digest(artifacts.integrity_path), consumed=False)
        self._write_json(old_path, old_document)
        old_bytes = old_path.read_bytes(); old_sha = _digest(old_path)
        new_path = directory / "authorization_v6.json"
        new_document = dict(old_document)
        new_document.update(authorization_id="retry20-v6", issued_at="2026-09-24T00:00:00Z",
                            supersedes={"authorization_id":"retry20-v5", "authorization_sha256":old_sha})
        self._write_json(new_path, new_document)
        old_inputs = replace(artifacts.inputs, authorization_artifact=old_path,
                             expected_authorization_sha256=old_sha)
        with self.assertRaises(RunnerError) as raised:
            verify_authorization(old_inputs)
        self.assertEqual(raised.exception.code, "AUTHORIZATION_SUPERSEDED")
        new_inputs = replace(artifacts.inputs, authorization_artifact=new_path,
                             expected_authorization_sha256=_digest(new_path))
        verified = verify_authorization(new_inputs)
        self.assertEqual(verified.document["authorization_id"], "retry20-v6")
        self.assertFalse(verified.document["consumed"])
        self.assertEqual(old_path.read_bytes(), old_bytes)

    def test_historical_authorization_only_is_not_execution_collision(self) -> None:
        artifacts = self._artifacts()
        artifacts.evidence_root.mkdir(parents=True)
        historical = artifacts.evidence_root / "PHASE31_AUTHORIZATION_V5.json"
        historical.write_text(artifacts.authorization_path.read_text(encoding="utf-8"), encoding="utf-8")
        verified = verify_authorization(artifacts.inputs)
        self.assertEqual(verified.run_slug, artifacts.evidence_root.name)

    def test_resource_manifest_is_execution_started_not_authorization_collision(self) -> None:
        artifacts = self._artifacts()
        artifacts.evidence_root.mkdir(parents=True)
        (artifacts.evidence_root / MANIFEST_NAME).write_text("{}\n", encoding="utf-8")
        with self.assertRaises(RunnerError) as raised:
            verify_authorization(artifacts.inputs)
        self.assertEqual(raised.exception.code, "EXECUTION_ALREADY_STARTED")


if __name__ == "__main__":
    unittest.main()
