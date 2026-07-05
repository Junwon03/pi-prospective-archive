#!/usr/bin/env python3
"""일일 snapshot 실행기 (GitHub Actions가 호출).

동작: FRED fetch → snapshot 생성 (freeze 전 = dry_run 자동 / 후 = valid 자동).
필요 환경변수: FRED_API_KEY. (Actions에서는 repo secret으로 주입)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from pi_archive import daily  # noqa: E402

if __name__ == "__main__":
    raw_long, raw_series = daily.fetch_all()
    repo_root = Path(__file__).parent
    run_dir = daily.make_snapshot(raw_long, raw_series, repo_root=repo_root)
    daily.mark_archive_started(repo_root)
    status = "valid" if daily.frozen_constants_ready() else "dry_run"
    print(f"snapshot written ({status}): {run_dir}")
