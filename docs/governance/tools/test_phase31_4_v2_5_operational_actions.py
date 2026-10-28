"""Focused tests for V2.5 operational service command construction."""

import importlib.util
import os
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "docs/governance/tools/phase31_4_v2_5_operational_actions.py"
SPEC = importlib.util.spec_from_file_location("phase31_4_v2_5_operational_actions", MODULE_PATH)
assert SPEC and SPEC.loader
actions = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(actions)


def _capture_service(system: str, port: str = "43123"):
    environment = {
        "PHASE31_ADMINAPPS_DB_ENDPOINT": "postgresql://127.0.0.1:54321/admin_db",
        "PHASE31_ISOSMART_DB_ENDPOINT": "postgresql://127.0.0.1:54322/iso_db",
        "PHASE31_INTEGRATION_KEY": "integration-key",
        "PHASE31_EVENT_KEY": "event-key",
        "ADMIN_APPS_BASE_URL": "http://127.0.0.1:43124",
        "PORT": port,
    }
    captured = {}

    def capture(executable, argv, env):
        captured.update(executable=executable, argv=argv, env=env)

    with patch.dict(os.environ, environment, clear=False), patch.object(actions.os, "execve", capture):
        actions.service(system)
    return captured


def test_adminapps_service_uses_absolute_manage_path_and_preserves_launch_contract():
    captured = _capture_service("adminapps")
    root = actions.ADMIN

    assert captured["executable"] == str(root / ".venv/bin/python")
    assert captured["argv"] == [
        str(root / ".venv/bin/python"),
        str(root / "manage.py"),
        "runserver",
        "--noreload",
        "127.0.0.1:43123",
    ]
    assert Path(captured["argv"][1]).is_absolute()
    assert captured["env"]["DB_NAME"] == "admin_db"
    assert captured["env"]["DB_PORT"] == "54321"
    assert captured["env"]["RETRY16_INTEGRATION_KEY"] == "integration-key"


def test_isosmart_service_uses_absolute_manage_path_and_preserves_launch_contract():
    captured = _capture_service("isosmart", port="43125")
    root = actions.ROOT / "backend"

    assert captured["executable"] == str(root / ".venv/bin/python")
    assert captured["argv"] == [
        str(root / ".venv/bin/python"),
        str(root / "manage.py"),
        "runserver",
        "--noreload",
        "127.0.0.1:43125",
    ]
    assert Path(captured["argv"][1]).is_absolute()
    assert captured["env"]["DB_NAME"] == "iso_db"
    assert captured["env"]["DB_PORT"] == "54322"
    assert captured["env"]["ADMIN_APPS_API_KEY"] == "integration-key"
    assert captured["env"]["ADMIN_APPS_BASE_URL"] == "http://127.0.0.1:43124/api/integration"