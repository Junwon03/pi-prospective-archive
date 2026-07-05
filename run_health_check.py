#!/usr/bin/env python3
"""Health check 실행기 (Actions가 호출). 실패 시 non-zero exit → 알림."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from pi_archive.health import HealthCheckFailure, run_health_check  # noqa: E402

if __name__ == "__main__":
    try:
        result = run_health_check(Path(__file__).parent / "snapshots")
    except HealthCheckFailure as e:
        print(f"HEALTH CHECK FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, indent=2))
