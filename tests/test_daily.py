"""daily(일일 snapshot 로직)·health(필수 3종) 테스트 — 전부 오프라인 합성 데이터."""
import datetime as dt
import json

import pytest

from pi_archive import config, daily
from pi_archive.health import HealthCheckFailure, run_health_check
from test_core import _raw_dict_to_long, make_raw


def _repo_with_specs(tmp_path):
    """daily.make_snapshot이 요구하는 repo 레이아웃 최소 재현."""
    (tmp_path / "SPEC-1.0_common_v4.md").write_text("common", encoding="utf-8")
    (tmp_path / "SPEC-1.0-C-US_v5.md").write_text("c-us", encoding="utf-8")
    (tmp_path / "requirements.lock").write_text("pandas==3.0.2", encoding="utf-8")
    return tmp_path


def test_make_snapshot_dry_run_before_freeze(tmp_path):
    """freeze 전(LIVE_* 미설정) → 자동으로 dry_run 신분, 임시 P99가 meta에 박제,
    manifest 검증 통과."""
    assert not daily.frozen_constants_ready()  # 기본 config: 전부 None
    raw = make_raw()
    repo = _repo_with_specs(tmp_path)
    run_dir = daily.make_snapshot(
        _raw_dict_to_long(raw), raw, repo_root=repo, code_git_commit="testsha",
        now_utc=dt.datetime(2026, 8, 15, 0, 5, 0, tzinfo=dt.timezone.utc))

    meta = json.loads((run_dir / "meta.json").read_text())
    assert meta["snapshot_status"] == "dry_run"
    assert meta["p99_used"]["rho"] > 0          # 임시 P99 투명 박제
    assert meta["mu_sigma_used"] is None
    from pi_archive.writer import verify_snapshot
    assert verify_snapshot(run_dir)


def test_make_snapshot_valid_after_freeze(tmp_path, monkeypatch):
    """freeze 후(LIVE_* 전부 설정) → 자동으로 valid 신분, frozen 상수 사용."""
    raw = make_raw()
    chan_p99 = daily.provisional_p99(raw)  # 형태만 빌려 frozen 값으로 주입
    monkeypatch.setattr(config, "LIVE_P99", chan_p99)
    monkeypatch.setattr(config, "LIVE_MU_SIGMA", {"mu": 0.1, "sigma": 0.05})
    monkeypatch.setattr(config, "LIVE_FREEZE_DATE", "2007-01-02")
    assert daily.frozen_constants_ready()

    repo = _repo_with_specs(tmp_path)
    run_dir = daily.make_snapshot(
        _raw_dict_to_long(raw), raw, repo_root=repo, code_git_commit="testsha",
        now_utc=dt.datetime(2026, 8, 15, 0, 5, 0, tzinfo=dt.timezone.utc))
    meta = json.loads((run_dir / "meta.json").read_text())
    assert meta["snapshot_status"] == "valid"
    assert meta["freeze_date"] == "2007-01-02"
    assert meta["p99_used"] == chan_p99          # frozen 상수 그대로


def test_make_snapshot_requires_spec_files(tmp_path):
    """SPEC 파일이 repo에 없으면 snapshot 생성 거부 (증거 체인 필수 요소)."""
    raw = make_raw()
    with pytest.raises(FileNotFoundError, match="SPEC"):
        daily.make_snapshot(_raw_dict_to_long(raw), raw, repo_root=tmp_path)


def test_observation_start_bounded():
    """fetch 창이 유계인지 — freeze 미설정 시 오늘 기준 버퍼."""
    start = daily.observation_start(today=dt.date(2026, 8, 15))
    assert start == (dt.date(2026, 8, 15)
                     - dt.timedelta(days=daily.FETCH_BUFFER_DAYS)).isoformat()


# ------------------------------------------------------------ health check

def _write_one_snapshot(tmp_path, now):
    raw = make_raw()
    repo = _repo_with_specs(tmp_path)
    return daily.make_snapshot(_raw_dict_to_long(raw), raw, repo_root=repo,
                               code_git_commit="testsha", now_utc=now)


def test_health_ok_and_no_snapshots_yet(tmp_path):
    # 수집 시작 전: 실패 아님 (명시 상태)
    res = run_health_check(tmp_path / "snapshots")
    assert res["status"] == "no_snapshots_yet"
    # snapshot 하나 생성 후: 3종 통과
    now = dt.datetime(2026, 8, 15, 0, 5, 0, tzinfo=dt.timezone.utc)
    _write_one_snapshot(tmp_path, now)
    res = run_health_check(tmp_path / "snapshots", today=dt.date(2026, 8, 17))
    assert res["status"] == "ok" and res["age_days"] == 2


def test_health_fails_on_stale_snapshot(tmp_path):
    now = dt.datetime(2026, 8, 15, 0, 5, 0, tzinfo=dt.timezone.utc)
    _write_one_snapshot(tmp_path, now)
    with pytest.raises(HealthCheckFailure, match="days old"):
        run_health_check(tmp_path / "snapshots", today=dt.date(2026, 8, 25))


def test_health_fails_on_tampered_manifest(tmp_path):
    now = dt.datetime(2026, 8, 15, 0, 5, 0, tzinfo=dt.timezone.utc)
    run_dir = _write_one_snapshot(tmp_path, now)
    # 파일 변조 → manifest 검증 실패해야 함
    (run_dir / "alert.json").write_text('{"tampered": true}', encoding="utf-8")
    with pytest.raises(HealthCheckFailure, match="manifest"):
        run_health_check(tmp_path / "snapshots", today=dt.date(2026, 8, 16))


def test_archive_started_marker_makes_empty_archive_fail(tmp_path):
    """첫 성공 이후 marker가 있으면 no_snapshots_yet green을 허용하지 않는다."""
    snapshots = tmp_path / "snapshots"
    snapshots.mkdir()
    (snapshots / "ARCHIVE_STARTED").write_text("started\n", encoding="utf-8")
    with pytest.raises(HealthCheckFailure, match="ARCHIVE_STARTED"):
        run_health_check(snapshots)


def test_mark_archive_started_creates_marker_under_snapshots(tmp_path):
    marker = daily.mark_archive_started(tmp_path)
    assert marker == tmp_path / "snapshots" / "ARCHIVE_STARTED"
    assert marker.exists()


def test_health_no_snapshots_yet_fails_after_archive_started_marker(tmp_path):
    """ARCHIVE_STARTED 이후에는 snapshot 부재가 조용히 green이면 안 된다."""
    (tmp_path / "ARCHIVE_STARTED").write_text("started\n", encoding="utf-8")
    with pytest.raises(HealthCheckFailure, match="ARCHIVE_STARTED"):
        run_health_check(tmp_path / "snapshots")


def test_current_git_head_returns_none_outside_git_repo(tmp_path):
    """로컬 임시 dry_run처럼 git repo가 아니면 None을 반환하고 예외를 내지 않는다."""
    assert daily.current_git_head(tmp_path) is None
