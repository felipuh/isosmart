"""Run Django migrations with Foundation's source-owned role session contract."""

import os
import sys
from pathlib import Path

# Executing this file by path makes ``foundation`` unavailable until the
# Django project root is explicitly on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundation.postgres_foundation_gate import ROLE_SPECS


def main():
    """Supply every governed role name before Django opens its DB connection."""
    options = []
    for key, *_ in ROLE_SPECS:
        name = os.environ.get(f"FOUNDATION_{key.upper()}_ROLE")
        if not name:
            raise RuntimeError(f"missing required migration role variable: FOUNDATION_{key.upper()}_ROLE")
        options.extend(("-c", f"foundation.{key}_role={name}"))
    os.environ["DB_SESSION_OPTIONS"] = " ".join(options)
    os.execvp(sys.executable, [sys.executable, "manage.py", "migrate", "--noinput"])


if __name__ == "__main__":
    main()
