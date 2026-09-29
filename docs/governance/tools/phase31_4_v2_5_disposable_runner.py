#!/usr/bin/env python3
"""Repository entry point for the reusable Phase 31.4 disposable runner."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from foundation.phase31_4_v2_5_disposable_runner import cli_main


if __name__ == "__main__":
    raise SystemExit(cli_main())
