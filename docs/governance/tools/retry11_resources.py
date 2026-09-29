"""Create and destroy only the disposable PostgreSQL resources for Retry 11."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(os.environ.get("RETRY11_MANIFEST", ROOT / "docs/governance/evidence/PHASE31_4_CLEAN_RETRY_11_ATTEMPT_2_RESOURCE_MANIFEST.json"))
IMAGE = "docker.io/library/postgres@sha256:7341002d2b8c7c5bdd7542a671a95b36196c0b5b888daf454ae4fc33ba5346d7"
IMAGE_ID = "a6638641707cdf047e5d5c2781f437e2e809323cab22c70b280be8389fbb7878"
RETRY = os.environ.get("RETRY_ID", "Phase 31.4 V2.5 Clean Retry 12")
RESOURCE_PREFIX = os.environ.get("RETRY_RESOURCE_PREFIX", "phase31_4_retry12")

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    data = json.loads(MANIFEST.read_text())
    if data.get("retry_id") != RETRY or data.get("teardown_status") == "PASS":
        raise RuntimeError("Retry 11 manifest identity or lifecycle state invalid")
    return data

def save(data):
    data["updated_at"] = now()
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

def podman(*args, check=True):
    result = subprocess.run(("podman", *args), text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"podman {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()

def create(role):
    data = load()
    if role in data["environments"]:
        raise RuntimeError(f"Retry 11 {role} already allocated")
    prefix = f"{RESOURCE_PREFIX}_{role}"
    resource = {
        "environment_id": prefix, "database_name": prefix,
        "postgresql_exact_version": "PostgreSQL 18.6", "image_digest": IMAGE.split("@", 1)[1],
        "image_id": IMAGE_ID, "container_name": prefix, "container_id": None,
        "volume_name": prefix + "_data", "volume_id": None,
        "network_name": prefix + "_net", "network_id": None, "port_mappings": [],
        "creation_started_at": now(), "status": "CREATING",
    }
    data["environments"][role] = resource
    save(data)
    try:
        image = json.loads(podman("image", "inspect", IMAGE, "--format", "{{json .}}"))
        if image.get("Id", "").removeprefix("sha256:") != IMAGE_ID or IMAGE not in image.get("RepoDigests", []):
            raise RuntimeError("PostgreSQL 18.6 immutable image mismatch")
        resource["volume_id"] = podman("volume", "create", resource["volume_name"]); save(data)
        resource["network_id"] = podman("network", "create", "--disable-dns", resource["network_name"]); save(data)
        resource["container_id"] = podman("create", "--pull=never", "--name", resource["container_name"],
            "--network", resource["network_name"], "--publish", "127.0.0.1::5432",
            "--volume", resource["volume_name"] + ":/var/lib/postgresql",
            "--env", "POSTGRES_DB=postgres", "--env", "POSTGRES_HOST_AUTH_METHOD=trust", IMAGE); save(data)
        podman("start", resource["container_id"])
        version = podman("exec", resource["container_id"], "postgres", "--version")
        if not version.startswith("postgres (PostgreSQL) 18.6 "):
            raise RuntimeError("PostgreSQL version mismatch")
        inspected = json.loads(podman("inspect", resource["container_id"], "--format", "{{json .}}"))
        resource["port_mappings"] = inspected["NetworkSettings"]["Ports"]["5432/tcp"]
        resource["observed_postgresql_version"] = version
        resource["created_at"] = now(); resource["status"] = "RUNNING_VERIFIED"; save(data)
    except Exception as exc:
        resource["status"] = "CREATE_FAILED"; resource["error"] = str(exc); save(data); raise

def teardown():
    data = load(); data["teardown_attempted"] = True; data["teardown_started_at"] = now(); data["teardown_status"] = "IN_PROGRESS"; save(data)
    errors = []
    for resource in data["environments"].values():
        for kind, name, key in (("container", resource["container_name"], "container_removed"), ("volume", resource["volume_name"], "volume_removed"), ("network", resource["network_name"], "network_removed")):
            try:
                podman("rm", "--force", name) if kind == "container" else podman(kind, "rm", name)
            except Exception as exc:
                if "does not exist" not in str(exc).lower(): errors.append(str(exc))
            resource[key] = True; save(data)
        resource["status"] = "REMOVED_VERIFIED"
    names = {name for kind in ("ps", "volume", "network") for name in podman(kind, "-a" if kind == "ps" else "ls", "--format", "{{.Names}}", check=False).splitlines()}
    for resource in data["environments"].values():
        for name in (resource["container_name"], resource["volume_name"], resource["network_name"]):
            if name in names: errors.append("resource remains: " + name)
    data["container_removed"] = all(r["container_removed"] for r in data["environments"].values())
    data["volume_removed"] = all(r["volume_removed"] for r in data["environments"].values())
    data["network_removed"] = all(r["network_removed"] for r in data["environments"].values())
    data["post_teardown_inventory_verified"] = not errors; data["teardown_errors"] = errors; data["teardown_completed_at"] = now()
    data["teardown_status"] = "PASS" if not errors and data["container_removed"] and data["volume_removed"] and data["network_removed"] else "FAIL"; save(data)
    if data["teardown_status"] != "PASS": raise RuntimeError("Retry 11 teardown failed")

if __name__ == "__main__":
    import sys
    action = sys.argv[1]
    if action == "create": create(sys.argv[2])
    elif action == "teardown": teardown()
    else: raise SystemExit("usage: retry11_resources.py create adminapps|isosmart|teardown")
