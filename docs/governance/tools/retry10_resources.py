"""Scoped, durable Podman resource ledger for Phase 31.4 Clean Retry 10.

Every successful create command is followed by an atomic manifest write before
the next command. Names are retry scoped; teardown never uses a global prune.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile


RETRY = "Phase 31.4 V2.5 Clean Retry 10"
IMAGE = "docker.io/library/postgres@sha256:7341002d2b8c7c5bdd7542a671a95b36196c0b5b888daf454ae4fc33ba5346d7"
IMAGE_ID = "a6638641707cdf047e5d5c2781f437e2e809323cab22c70b280be8389fbb7878"
VERSION = "PostgreSQL 18.6"
DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "evidence/PHASE31_4_CLEAN_RETRY_10_RESOURCE_MANIFEST.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def persist(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, prefix=".retry10-", delete=False) as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def read(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("retry_id") != RETRY or data.get("execution_mode") != "LIVE_NATIVE_EXECUTION":
        raise ValueError("manifest identity mismatch")
    return data


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(("podman", *args), text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"podman {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def initialize(path: Path, graph_root: str, run_root: str) -> dict:
    if path.exists():
        raise FileExistsError(f"Retry 10 manifest already exists: {path}")
    data = {
        "artifact_schema": "phase31.4-retry10-runtime-resources/v1",
        "retry_id": RETRY,
        "retry_tag": "CLEAN_RETRY_10",
        "execution_mode": "LIVE_NATIVE_EXECUTION",
        "allocated_at": now(),
        "runtime_host": os.uname().nodename,
        "podman_context": "local rootless default",
        "podman_storage_root": graph_root,
        "podman_run_root": run_root,
        "environments": {},
        "teardown_attempted": False,
        "teardown_started_at": None,
        "teardown_completed_at": None,
        "container_removed": False,
        "DB_resource_removed": False,
        "volume_removed": False,
        "network_removed": False,
        "post_teardown_inventory_verified": False,
        "teardown_status": "PENDING",
    }
    persist(path, data)
    return data


def create(path: Path, role: str) -> dict:
    data = read(path)
    if role not in ("adminapps", "isosmart") or role in data["environments"]:
        raise ValueError("invalid or already allocated environment role")
    suffix = f"phase31_4_retry10_{role}"
    resource = {
        "environment_id": suffix,
        "database_name": suffix,
        "postgresql_exact_version": VERSION,
        "image_digest": IMAGE.rsplit("@", 1)[1],
        "image_id": IMAGE_ID,
        "container_name": suffix,
        "container_id": None,
        "volume_name": f"{suffix}_data",
        "volume_id": None,
        "network_name": f"{suffix}_net",
        "network_id": None,
        "port_mappings": [],
        "creation_started_at": now(),
        "created_at": None,
        "status": "CREATING",
        "container_removed": False,
        "volume_removed": False,
        "network_removed": False,
    }
    data["environments"][role] = resource
    persist(path, data)
    try:
        image = json.loads(run("image", "inspect", IMAGE, "--format", "{{json .}}"))
        if image.get("Id", "").removeprefix("sha256:") != IMAGE_ID or IMAGE not in image.get("RepoDigests", []):
            raise RuntimeError("frozen PostgreSQL image identity mismatch")
        resource["volume_id"] = run("volume", "create", resource["volume_name"])
        persist(path, data)
        run("network", "create", "--disable-dns", resource["network_name"])
        network = json.loads(run("network", "inspect", resource["network_name"], "--format", "{{json .}}"))
        resource["network_id"] = network.get("id") or network.get("ID") or resource["network_name"]
        persist(path, data)
        resource["container_id"] = run(
            "create", "--pull=never", "--name", resource["container_name"],
            "--network", resource["network_name"], "--publish", "127.0.0.1::5432",
            "--volume", f"{resource['volume_name']}:/var/lib/postgresql",
            "--env", f"POSTGRES_DB={'postgres' if role == 'isosmart' else resource['database_name']}",
            "--env", "POSTGRES_HOST_AUTH_METHOD=trust", IMAGE,
        )
        persist(path, data)
        return start_and_verify(path, data, resource)
    except Exception as exc:
        resource["status"] = "CREATE_FAILED"
        resource["error"] = str(exc)
        persist(path, data)
        raise


def start_and_verify(path: Path, data: dict, resource: dict) -> dict:
    before = json.loads(run("inspect", resource["container_id"], "--format", "{{json .}}"))
    if not before.get("State", {}).get("Running"):
        run("start", resource["container_id"])
    resource["status"] = "STARTED"
    persist(path, data)
    observed_version = run("exec", resource["container_id"], "postgres", "--version")
    if not observed_version.startswith("postgres (PostgreSQL) 18.6 "):
        raise RuntimeError(f"PostgreSQL version mismatch: {observed_version}")
    resource["observed_postgresql_version"] = observed_version
    inspected = json.loads(run("inspect", resource["container_id"], "--format", "{{json .}}"))
    resource["port_mappings"] = inspected.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp") or []
    resource["created_at"] = now()
    resource["status"] = "RUNNING_VERIFIED"
    resource.pop("error", None)
    persist(path, data)
    return resource


def resume(path: Path, role: str) -> dict:
    data = read(path)
    resource = data["environments"][role]
    if resource["status"] != "CREATE_FAILED" or not resource["container_id"]:
        raise ValueError("only a tracked failed container can be resumed")
    try:
        return start_and_verify(path, data, resource)
    except Exception as exc:
        resource["status"] = "CREATE_FAILED"
        resource["error"] = str(exc)
        persist(path, data)
        raise


def repair_network(path: Path, role: str) -> dict:
    """Replace an unstarted DNS network and container, retaining old IDs."""
    data = read(path)
    resource = data["environments"][role]
    if resource["status"] != "CREATE_FAILED" or not resource["container_id"]:
        raise ValueError("network repair requires a tracked failed container")
    old = {key: resource.get(key) for key in ("container_id", "network_id", "created_at")}
    run("rm", "--force", resource["container_name"])
    resource["container_id"] = None
    persist(path, data)
    run("network", "rm", resource["network_name"])
    resource["network_id"] = None
    persist(path, data)
    resource.setdefault("retired_resources", []).append(old)
    run("network", "create", "--disable-dns", resource["network_name"])
    network = json.loads(run("network", "inspect", resource["network_name"], "--format", "{{json .}}"))
    resource["network_id"] = network.get("id") or network.get("ID")
    persist(path, data)
    resource["container_id"] = run(
        "create", "--pull=never", "--name", resource["container_name"],
        "--network", resource["network_name"], "--publish", "127.0.0.1::5432",
        "--volume", f"{resource['volume_name']}:/var/lib/postgresql",
        "--env", "POSTGRES_DB=postgres",
        "--env", "POSTGRES_HOST_AUTH_METHOD=trust", IMAGE,
    )
    persist(path, data)
    try:
        return start_and_verify(path, data, resource)
    except Exception as exc:
        resource["status"] = "CREATE_FAILED"
        resource["error"] = str(exc)
        persist(path, data)
        raise


def teardown(path: Path) -> dict:
    data = read(path)
    data["teardown_attempted"] = True
    data["teardown_started_at"] = now()
    data["teardown_status"] = "IN_PROGRESS"
    persist(path, data)
    errors = []
    for resource in data["environments"].values():
        for kind, identifier, key in (
            ("container", resource["container_name"], "container_removed"),
            ("volume", resource["volume_name"], "volume_removed"),
            ("network", resource["network_name"], "network_removed"),
        ):
            if resource[key]:
                continue
            if not resource.get(f"{kind}_id"):
                resource[key] = True
                persist(path, data)
                continue
            try:
                command = ("rm", "--force", identifier) if kind == "container" else (kind, "rm", identifier)
                run(*command)
                resource[key] = True
            except Exception as exc:
                errors.append(f"{kind} {identifier}: {exc}")
            persist(path, data)
    inventory = {
        "container": set(run("ps", "-a", "--format", "{{.Names}}").splitlines()),
        "volume": set(run("volume", "ls", "--format", "{{.Name}}").splitlines()),
        "network": set(run("network", "ls", "--format", "{{.Name}}").splitlines()),
    }
    for resource in data["environments"].values():
        for kind, identifier in (("container", resource["container_name"]), ("volume", resource["volume_name"]), ("network", resource["network_name"])):
            if identifier in inventory[kind]:
                errors.append(f"{kind} still present: {identifier}")
        for retired in resource.get("retired_resources", []):
            if retired.get("container_id") and retired["container_id"] in run("ps", "-a", "--format", "{{.ID}}").splitlines():
                errors.append(f"retired container still present: {retired['container_id']}")
    resources = tuple(data["environments"].values())
    data["container_removed"] = all(item["container_removed"] for item in resources)
    data["DB_resource_removed"] = data["container_removed"] and all(item["volume_removed"] for item in resources)
    data["volume_removed"] = all(item["volume_removed"] for item in resources)
    data["network_removed"] = all(item["network_removed"] for item in resources)
    data["post_teardown_inventory_verified"] = not errors
    data["teardown_completed_at"] = now()
    data["teardown_status"] = "PASS" if not errors and all((data["container_removed"], data["DB_resource_removed"], data["volume_removed"], data["network_removed"])) else "FAIL"
    data["teardown_errors"] = errors
    data.setdefault("teardown_attempts", []).append({
        "started_at": data["teardown_started_at"],
        "completed_at": data["teardown_completed_at"],
        "status": data["teardown_status"],
        "errors": errors,
    })
    if data["teardown_status"] == "PASS":
        for resource in resources:
            resource["status"] = "REMOVED_VERIFIED"
    persist(path, data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("init", "create", "resume", "repair-network", "teardown"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--role", choices=("adminapps", "isosmart"))
    args = parser.parse_args()
    if args.action == "init":
        info = json.loads(run("info", "--format", "{{json .}}"))
        result = initialize(args.manifest, info["store"]["graphRoot"], info["store"]["runRoot"])
    elif args.action in ("create", "resume", "repair-network"):
        if args.role is None:
            parser.error("create/resume requires --role")
        if args.action == "create":
            result = create(args.manifest, args.role)
        elif args.action == "resume":
            result = resume(args.manifest, args.role)
        else:
            result = repair_network(args.manifest, args.role)
    else:
        result = teardown(args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
