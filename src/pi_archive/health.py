"""Health check — common v4 C15 필수 3종.

① 최근 snapshot 존재 (MAX_AGE_DAYS 이내)
② 필수 series fetch 성공 (raw에 각 시리즈 ok 행 존재)
③ manifest hash 검증 통과 (최신 run)

실패 시 예외 → workflow 실패 → GitHub이 알림. 무인화의 전제 = "깨지면 알아챈다".
첫 성공 snapshot 이후에는 snapshots/ARCHIVE_STARTED marker가 생기며, 그 뒤에는
no_snapshots_yet이 실패로 바뀐다.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from . import writer
from .daily import REQUIRED_SERIES

MAX_AGE_DAYS = 4  # 주말 + 휴장 하루 흡수
ARCHIVE_STARTED_FILE = "ARCHIVE_STARTED"


class HealthCheckFailure(RuntimeError):
    pass


def latest_run_dir(snapshots_root: str | Path, subtrack: str = "C-US") -> Path | None:
    base = Path(snapshots_root) / subtrack
    if not base.is_dir():
        return None
    date_dirs = sorted(d for d in base.iterdir()
                       if d.is_dir() and not d.name.startswith("."))
    if not date_dirs:
        return None
    runs = sorted(r for r in date_dirs[-1].iterdir()
                  if r.is_dir() and not r.name.startswith("."))
    return runs[-1] if runs else None


def run_health_check(snapshots_root: str | Path, subtrack: str = "C-US",
                     today: dt.date | None = None,
                     max_age_days: int = MAX_AGE_DAYS) -> dict:
    """3종 검사. 통과 시 요약 dict 반환, 실패 시 HealthCheckFailure."""
    snapshots_root = Path(snapshots_root)
    base = snapshots_root / subtrack
    marker_paths = (snapshots_root / ARCHIVE_STARTED_FILE,
                    snapshots_root.parent / ARCHIVE_STARTED_FILE)
    archive_started = any(p.exists() for p in marker_paths)
    if not base.is_dir():
        # 첫 수집 이전: 실패가 아니라 '아직 시작 전'. 단 ARCHIVE_STARTED가
        # 생긴 뒤에는 snapshot 부재가 조용히 초록으로 보이면 안 된다.
        # Primary marker 위치는 snapshots/ARCHIVE_STARTED이나, 초기 실험에서
        # repo-root marker를 둔 경우도 실패로 인식한다.
        if archive_started:
            raise HealthCheckFailure(
                f"{ARCHIVE_STARTED_FILE} exists but no {subtrack} snapshots directory was found")
        return {"status": "no_snapshots_yet",
                "note": "collection has not started; strict checks begin "
                        f"after snapshots/{ARCHIVE_STARTED_FILE} is committed"}

    run = latest_run_dir(snapshots_root, subtrack)
    if run is None:
        if archive_started:
            raise HealthCheckFailure(
                f"{ARCHIVE_STARTED_FILE} exists but {subtrack} contains no runs")
        raise HealthCheckFailure("snapshots directory exists but contains no runs")

    # ① 최신성
    today = today or dt.date.today()
    snap_date = dt.date.fromisoformat(run.parent.name)
    age = (today - snap_date).days
    if age > max_age_days:
        raise HealthCheckFailure(
            f"latest snapshot is {age} days old (> {max_age_days}): {run}")

    # ② fetch 성공 (필수 시리즈 각각 ok 행 존재)
    raw = pd.read_csv(run / "raw.csv")
    if raw.empty:
        raise HealthCheckFailure(f"raw.csv is empty: {run}")
    ok = raw[raw["fetch_status"] == "ok"]
    missing = [sid for sid in REQUIRED_SERIES
               if ok[ok["series_id"] == sid].empty]
    if missing:
        raise HealthCheckFailure(f"no successful observations for: {missing}")

    # ③ manifest 검증
    if not writer.verify_snapshot(run):
        raise HealthCheckFailure(f"manifest verification failed: {run}")

    return {"status": "ok", "latest_run": str(run), "age_days": age,
            "raw_rows": int(len(raw))}
