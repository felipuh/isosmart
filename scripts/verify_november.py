"""Offline baseline checks; no databases, servers or external API calls."""
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
           OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
JOBS = [['integration/tests_staging_p0_offline.py'], ['integration/tests_b_offline.py'], ['integration/tests_d_offline.py'], ['integration/tests_d_session_offline.py'], ['integration/tests_recovery_p0_offline.py'], ['integration/tests_me_p0_offline.py']]
CWD = ROOT / 'backend'
for command in JOBS:
    subprocess.run([sys.executable, '-B', *command], cwd=CWD, env=ENV, check=True)
