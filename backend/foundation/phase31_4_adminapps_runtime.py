"""Canonical, temporary AdminApps runtime for disposable diagnostics.

The caller owns the context for the entire attempt, including service teardown.
No host virtualenv is modified and no parallel package list is maintained.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile


@contextmanager
def disposable_adminapps_runtime(repository_root, *, base=None):
    root = Path(repository_root).resolve()
    backend = root.parent / "adminapps/backend"
    manifest = backend / "requirements.txt"
    manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    env = dict(os.environ if base is None else base)
    with tempfile.TemporaryDirectory(prefix="phase31-adminapps-runtime-") as directory:
        runtime = Path(directory)
        subprocess.run([sys.executable, "-m", "venv", str(runtime)], check=True,
                       capture_output=True, text=True)
        python = runtime / "bin/python"
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(manifest)],
                       cwd=backend, env=env, check=True, capture_output=True, text=True)
        subprocess.run([str(python), "-m", "pip", "check"], cwd=backend, env=env,
                       check=True, capture_output=True, text=True)
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != manifest_sha:
            raise RuntimeError("AdminApps canonical manifest changed during provisioning")
        env["PHASE31_ADMINAPPS_PYTHON"] = str(python)
        yield env, {"canonical_manifest": str(manifest), "manifest_sha256": manifest_sha,
                    "interpreter": str(python), "environment_type": "isolated_temporary_venv",
                    "system_site_packages": False}
