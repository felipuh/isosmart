"""Create and tear down isolated PostgreSQL 18.6 resources for Retry 15."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_CLEAN_RETRY_15_RESOURCE_MANIFEST.json"
IMAGE = "docker.io/library/postgres@sha256:7341002d2b8c7c5bdd7542a671a95b36196c0b5b888daf454ae4fc33ba5346d7"
IMAGE_ID = "a6638641707cdf047e5d5c2781f437e2e809323cab22c70b280be8389fbb7878"
PREFIX = "phase31_4_retry15"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(*args: str) -> str:
    result = subprocess.run(("podman", *args), text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "podman command failed")
    return result.stdout.strip()


def save(data: dict) -> None:
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def resource(role: str) -> dict:
    return {
        "environment_id": f"{PREFIX}_{role}",
        "database_name": f"{PREFIX}_{role}",
        "container_name": f"{PREFIX}_{role}",
        "volume_name": f"{PREFIX}_{role}_data",
        "network_name": f"{PREFIX}_{role}_net",
        "postgresql_exact_version": "PostgreSQL 18.6",
        "image_digest": IMAGE.rsplit("@", 1)[1],
        "image_id": IMAGE_ID,
        "status": "PENDING",
        "container_removed": False,
        "volume_removed": False,
        "network_removed": False,
    }


def create() -> None:
    if MANIFEST.exists():
        raise RuntimeError(f"manifest already exists: {MANIFEST}")
    image = json.loads(run("image", "inspect", IMAGE, "--format", "{{json .}}"))
    if image.get("Id", "").removeprefix("sha256:") != IMAGE_ID or IMAGE not in image.get("RepoDigests", []):
        raise RuntimeError("approved PostgreSQL image identity mismatch")
    data = {
        "artifact_schema": "phase31.4-clean-retry-runtime-resources/v1",
        "retry_id": "Phase 31.4 V2.5 Clean Retry 15",
        "retry_tag": "CLEAN_RETRY_15",
        "execution_mode": "LIVE_NATIVE_EXECUTION",
        "allocated_at": now(),
        "approved_image": IMAGE,
        "approved_image_id": IMAGE_ID,
        "environments": {},
        "teardown_status": "PENDING",
    }
    save(data)
    try:
        for role in ("adminapps", "isosmart"):
            item = resource(role)
            data["environments"][role] = item
            save(data)
            item["volume_id"] = run("volume", "create", item["volume_name"])
            run("network", "create", "--disable-dns", item["network_name"])
            item["network_id"] = item["network_name"]
            item["container_id"] = run(
                "create", "--pull=never", "--name", item["container_name"],
                "--network", item["network_name"], "--publish", "127.0.0.1::5432",
                "--volume", f"{item['volume_name']}:/var/lib/postgresql",
                "--env", f"POSTGRES_DB={item['database_name']}",
                "--env", "POSTGRES_HOST_AUTH_METHOD=trust", IMAGE,
            )
            run("start", item["container_id"])
            observed = run("exec", item["container_id"], "postgres", "--version")
            if not observed.startswith("postgres (PostgreSQL) 18.6 "):
                raise RuntimeError(f"PostgreSQL version mismatch: {observed}")
            inspect = json.loads(run("inspect", item["container_id"], "--format", "{{json .}}"))
            item["port_mappings"] = inspect["NetworkSettings"]["Ports"]["5432/tcp"]
            item["observed_postgresql_version"] = observed
            item["status"] = "RUNNING_VERIFIED"
            save(data)
    except Exception as exc:
        data["creation_error"] = str(exc)
        save(data)
        raise
    print(json.dumps(data, indent=2, sort_keys=True))


def teardown() -> None:
    data = json.loads(MANIFEST.read_text())
    errors = []
    for item in data["environments"].values():
        for command, key, identifier in (
            (("rm", "--force", item["container_name"]), "container_removed", item["container_name"]),
            (("volume", "rm", item["volume_name"]), "volume_removed", item["volume_name"]),
            (("network", "rm", item["network_name"]), "network_removed", item["network_name"]),
        ):
            try:
                run(*command)
                item[key] = True
            except Exception as exc:
                if "does not exist" not in str(exc):
                    errors.append(f"{identifier}: {exc}")
                else:
                    item[key] = True
    data["teardown_status"] = "PASS" if not errors and all(
        item[key] for item in data["environments"].values() for key in ("container_removed", "volume_removed", "network_removed")
    ) else "FAIL"
    data["teardown_errors"] = errors
    data["teardown_completed_at"] = now()
    save(data)
    print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "teardown"))
    args = parser.parse_args()
    create() if args.action == "create" else teardown()