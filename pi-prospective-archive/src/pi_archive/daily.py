"""Daily snapshot logic — GitHub Actions 일일 수집의 핵심.

신분 자동 전환 (common v4):
- config의 LIVE_P99 / LIVE_MU_SIGMA / LIVE_FREEZE_DATE가 **전부** 설정됨
  → 공식 snapshot (status="valid", frozen 상수 사용 — writer가 일치를 강제)
- 하나라도 None → **dry_run** (평가 제외 시운전. 임시 P99 사용, meta에 박제)

fetch 창 경계:
- 매일 1997년부터 전체를 fetch하면 raw.csv가 하루 수 MB → repo가 연 수백 MB로 비대.
- Π(Pi_since_freeze)는 freeze일 이후의 S만 필요하고, S̄_w(90 거래일)·Δ5·LOCF의
  warm-up은 freeze일 이전 FETCH_BUFFER_DAYS로 충분히 커버됨.
- 따라서 observation_start = (freeze일 또는 오늘) − FETCH_BUFFER_DAYS.
  → raw는 프로젝트 수명(1.5~2년) 동안 유계, snapshot당 수백 KB 수준 유지.
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
from pathlib import Path

import pandas as pd

from . import channels as ch
from . import config, fetch_fred, stress, writer

# warm-up 여유: 90 거래일(S̄_w) + 5(Δ) + LOCF gap → 300 calendar days면 넉넉
FETCH_BUFFER_DAYS = 300

REQUIRED_SERIES = list(config.FRED_SERIES)  # DFF, DCPF3M, DTB3, TOTBKCR


def observation_start(today: dt.date | None = None) -> str:
    today = today or dt.date.today()
    origin = (dt.date.fromisoformat(config.LIVE_FREEZE_DATE)
              if config.LIVE_FREEZE_DATE else today)
    return (origin - dt.timedelta(days=FETCH_BUFFER_DAYS)).isoformat()


def fetch_all(api_key: str | None = None,
              today: dt.date | None = None) -> tuple[pd.DataFrame, dict]:
    """필수 시리즈 fetch → (raw_long, raw_series). 하나라도 실패하면 예외
    (불완전 snapshot이 만들어지느니 실패가 낫다 — common C13)."""
    start = observation_start(today)
    frames = []
    for sid in REQUIRED_SERIES:
        frames.append(fetch_fred.fetch_series(sid, api_key=api_key,
                                              observation_start=start))
    raw_long = pd.concat(frames, ignore_index=True)
    raw_series = {sid: fetch_fred.raw_to_series(raw_long, sid)
                  for sid in REQUIRED_SERIES}
    return raw_long, raw_series


def provisional_p99(raw_series: dict) -> dict:
    """dry_run 전용 임시 P99 — fetch된 전 구간의 q99.

    live frozen P99가 아니며 평가에 사용되지 않는다. 목적은 파이프라인
    시운전에서 computed가 형태상 완전하게 생성되는지 확인하는 것뿐.
    사용된 값은 meta.p99_used에 그대로 박제되어 투명하다."""
    chan = ch.build_credit_channels(raw_series, mode="live")
    p99 = {
        "rho": float(chan["rho_raw"].quantile(0.99)),
        "psi": float(chan["psi_raw"].quantile(0.99)),
        "omega": float(chan["omega_raw"].quantile(0.99)),
    }
    for k, v in p99.items():
        if not v or v <= 0:
            raise ValueError(f"provisional P99 invalid for {k}: {v}")
    return p99


def frozen_constants_ready() -> bool:
    return all(x is not None for x in (
        config.LIVE_P99, config.LIVE_MU_SIGMA, config.LIVE_FREEZE_DATE))




def current_git_head(repo_root: str | Path) -> str | None:
    """실제 계산에 사용된 checkout HEAD를 반환한다.

    Actions의 GITHUB_SHA는 trigger 시점 SHA라서, 실행 중 ff-only 동기화가
    있었다면 실제 계산 코드와 어긋날 수 있다. 감사 체인에는 현재 worktree의
    HEAD가 더 정확하다. git 정보가 없는 로컬 dry_run에서는 None을 허용한다.
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(repo_root), text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def mark_archive_started(repo_root: str | Path) -> Path:
    """첫 성공 snapshot 이후 healthcheck strict mode를 켜는 marker 생성.

    첫 수집 전에는 healthcheck가 no_snapshots_yet을 허용하지만, 이 marker가
    committed 된 뒤에는 snapshot 부재가 실패다. marker는 snapshots/ 아래에
    두어 기존 `git add snapshots/`에 포함되게 한다.
    """
    marker = Path(repo_root) / "snapshots" / "ARCHIVE_STARTED"
    marker.parent.mkdir(parents=True, exist_ok=True)
    if not marker.exists():
        marker.write_text(
            "This archive has produced at least one successful snapshot.\n"
            "After this marker is committed, healthcheck must fail if snapshots disappear.\n",
            encoding="utf-8",
        )
    return marker


def make_snapshot(raw_long: pd.DataFrame, raw_series: dict,
                  repo_root: str | Path,
                  code_git_commit: str | None = None,
                  now_utc: dt.datetime | None = None) -> Path:
    """오늘의 snapshot 생성. 신분(dry_run/valid)은 frozen 상수 유무로 자동 결정."""
    root = Path(repo_root)
    spec_paths = {"common": root / "SPEC-1.0_common_v4.md",
                  "subtrack": root / "SPEC-1.0-C-US_v5.md"}
    for name, p in spec_paths.items():
        if not p.is_file():
            raise FileNotFoundError(f"SPEC file missing in repo: {p} ({name})")
    lock_path = root / "requirements.lock"

    if frozen_constants_ready():
        status = "valid"
        p99, mu_sigma = config.LIVE_P99, config.LIVE_MU_SIGMA
        freeze_date = config.LIVE_FREEZE_DATE
    else:
        status = "dry_run"
        p99, mu_sigma = provisional_p99(raw_series), None
        now = now_utc or dt.datetime.now(dt.timezone.utc)
        freeze_date = now.date().isoformat()  # dry_run 한정 자리표시 원점

    return writer.write_snapshot(
        raw_long=raw_long, raw_series=raw_series, subtrack="C-US",
        base_dir=root / "snapshots", spec_paths=spec_paths,
        p99=p99, freeze_date=freeze_date, mu_sigma=mu_sigma,
        lock_path=lock_path,
        code_git_commit=(code_git_commit or current_git_head(root)
                         or os.environ.get("GITHUB_SHA")),
        snapshot_status=status, now_utc=now_utc)
