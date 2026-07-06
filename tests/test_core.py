"""Core correctness tests — 1년치 데이터가 오염되지 않기 위한 최소 불변량.

가장 중요한 테스트는 test_no_lookahead_live_mode:
common C4.5의 인과성 조건("t에서 절단해 계산한 값 = 전체 데이터 계산의 t 이전 값")을
합성 데이터로 직접 검증한다. 짝 테스트 test_interpolation_is_noncausal은
foundation의 선형보간이 왜 live에서 금지인지(과거 값이 미래 데이터에 따라 변함)를
실증한다 — v3 수정의 근거를 코드로 남기는 것.
"""
import numpy as np
import pandas as pd
import pytest

from pi_archive import channels as ch
from pi_archive import calibration, config, stress


# ------------------------------------------------------------ synthetic data

def make_raw(seed: int = 7) -> dict:
    """2004~2010 합성 신용 데이터. 2008-09~2009-03에 위기 bump."""
    rng = np.random.default_rng(seed)
    bdays = pd.bdate_range("2004-01-01", "2010-12-31")

    def crisis_mask(idx):
        return (idx >= "2008-09-01") & (idx <= "2009-03-31")

    dff = pd.Series(2.0 + np.cumsum(rng.normal(0, 0.02, len(bdays))), index=bdays)
    dff[crisis_mask(bdays)] += np.linspace(0, -1.5, crisis_mask(bdays).sum())  # 급격 인하

    cp = pd.Series(2.3 + rng.normal(0, 0.03, len(bdays)), index=bdays)
    tb = pd.Series(2.0 + rng.normal(0, 0.02, len(bdays)), index=bdays)
    cp[crisis_mask(bdays)] += 1.8  # funding stress spike

    # 주간 (수요일) 은행신용 — 위기에 수축
    weds = pd.date_range("2004-01-07", "2010-12-29", freq="W-WED")
    tot = pd.Series(8000 + np.cumsum(rng.normal(5, 10, len(weds))), index=weds)
    tot[crisis_mask(weds)] += np.linspace(0, 900, crisis_mask(weds).sum())

    # 재현 전용 TEDRATE — CP–T-bill과 상관되되 식별 가능하게 다른 시리즈
    ted = pd.Series(0.4 + rng.normal(0, 0.05, len(bdays)), index=bdays)
    ted[crisis_mask(bdays)] += 2.5

    # sensitivity용 DGS3MO — DTB3와 유사하되 basis 차이
    gs = tb + 0.06 + rng.normal(0, 0.01, len(bdays))

    return {
        "DFF": dff,
        "DCPF3M": cp,
        "DTB3": tb,
        "TOTBKCR": tot,
        "TEDRATE": ted,
        "DGS3MO": gs,
    }


# ------------------------------------------------- ★ 핵심: 인과성 불변량

def test_no_lookahead_live_mode():
    """live 모드: t에서 데이터 절단 후 계산한 값 == 전체 데이터 계산의 t 이전 값."""
    raw_full = make_raw()
    cutoff = pd.Timestamp("2008-06-30")
    raw_trunc = {k: s.loc[:cutoff] for k, s in raw_full.items()}

    full = ch.build_credit_channels(raw_full, mode="live")
    trunc = ch.build_credit_channels(raw_trunc, mode="live")

    common_idx = trunc.index.intersection(full.index)
    assert len(common_idx) > 500
    pd.testing.assert_frame_equal(
        full.loc[common_idx], trunc.loc[common_idx], check_exact=True
    )

    # 정규화·stress까지 포함해도 불변 (P99는 절단 이전의 고정 stable window)
    p99 = stress.p99_from_window(full, "2004-01-01", "2006-12-31")
    st_full = stress.compute_stress(stress.normalize(full, p99))
    st_trunc = stress.compute_stress(stress.normalize(trunc, p99))
    cols = ["S", "Sbar_w", "Pi"]
    pd.testing.assert_frame_equal(
        st_full.loc[common_idx, cols], st_trunc.loc[common_idx, cols], check_exact=True
    )


def test_interpolation_is_noncausal():
    """historical_repro(선형보간)의 주간 관측 사이 값은 미래 관측을 사용함을 실증
    → live 금지 근거 (v3 수정 사유의 코드 증거).

    같은 데이터에서: live(LOCF)는 두 주간 관측 사이 날짜에 '직전 관측값'을 주고
    (과거만 사용), 보간은 직전 값과 다른 값을 준다 = 다음(미래) 관측이 개입.
    """
    raw_full = make_raw()
    full_live = ch.build_credit_channels(raw_full, mode="live")
    full_interp = ch.build_credit_channels(raw_full, mode="historical_repro")

    weds = raw_full["TOTBKCR"].index
    w0, w1 = weds[100], weds[101]  # 표본 중간의 인접 주간 관측 쌍
    between = full_interp.index[(full_interp.index > w0) & (full_interp.index < w1)]
    assert len(between) >= 2

    prev_val = raw_full["TOTBKCR"].loc[w0]
    live_vals = full_live.loc[between, "omega_raw"]
    interp_vals = full_interp.loc[between, "omega_raw"]

    # live: 전부 직전 주간값과 동일 (과거만 사용 = 인과적)
    assert (live_vals - prev_val).abs().max() < 1e-12
    # 보간: 직전 값과 다름 = 미래 관측(w1)이 t 시점 값 계산에 개입 (비인과)
    assert (interp_vals - prev_val).abs().max() > 1e-9


# ------------------------------------------------------------- fill rules

def test_weekly_locf_within_limit():
    """주간 TOTBKCR: LOCF 14일 한도 내에서는 일별 정렬 성공 (NaN 없음)."""
    raw = make_raw()
    chan = ch.build_credit_channels(raw, mode="live")
    # warm-up(Δ5d) 이후 전 구간 3채널 유효
    assert not chan.isna().any().any()
    assert len(chan) > 1500


def test_gap_beyond_limit_marks_unavailable():
    """일별 채널에 6일 초과 공백 → 해당 구간 computed에서 제외 (unavailable)."""
    raw = make_raw()
    gap_start, gap_end = pd.Timestamp("2007-03-05"), pd.Timestamp("2007-03-16")
    cp = raw["DCPF3M"].copy()
    cp.loc[gap_start:gap_end] = np.nan  # 약 10 영업일 공백 (>5 calendar days LOCF 한도)
    raw["DCPF3M"] = cp

    chan = ch.build_credit_channels(raw, mode="live")
    # 공백 끝부분(LOCF 5일 초과 도달 후)은 grid에서 탈락해야 함
    hole = chan.loc["2007-03-12":"2007-03-16"]
    assert len(hole) == 0, "fill 한도 초과 구간이 computed에 남아 있음"


# --------------------------------------------------------------- identities

def test_S_is_channel_product():
    raw = make_raw()
    chan = ch.build_credit_channels(raw, mode="live")
    p99 = stress.p99_from_window(chan, "2004-01-01", "2006-12-31")
    st = stress.compute_stress(stress.normalize(chan, p99))
    recomputed = st["rho_hat"] * st["psi_hat"] * st["omega_hat"]
    pd.testing.assert_series_equal(st["S"], recomputed, check_names=False)


def test_p99_normalization_scale():
    """stable window 내에서 x̂의 99% 분위 ≈ 1 (정의상)."""
    raw = make_raw()
    chan = ch.build_credit_channels(raw, mode="live")
    p99 = stress.p99_from_window(chan, "2004-01-01", "2006-12-31")
    norm = stress.normalize(chan, p99).loc["2004-01-01":"2006-12-31"]
    for col in ("rho_hat", "psi_hat", "omega_hat"):
        q = norm[col].quantile(0.99)
        assert abs(q - 1.0) < 0.02, f"{col} stable P99 != 1: {q}"


def test_sep_pi_known_ratio():
    """구성된 S(제어 1.0, 위기 5.0)에서 Sep(S̄)=5, Sep(Π)=5×(N_c/N_k) 정확 재현."""
    idx = pd.bdate_range("2020-01-01", "2020-12-31")
    s = pd.Series(1.0, index=idx)
    s.loc["2020-07-01":"2020-09-30"] = 5.0
    df = pd.DataFrame({"S": s})
    res = stress.sep_pi(
        df,
        crisis=("2020-07-01", "2020-09-30"),
        control=("2020-02-01", "2020-04-30"),
    )
    assert res["Sep_Sbar"] == pytest.approx(5.0)
    expected_pi_ratio = 5.0 * res["N_crisis"] / res["N_control"]
    assert res["Sep_Pi"] == pytest.approx(expected_pi_ratio)


# ---------------------------------------------------------------- episodes

def _sbar(vals, start="2024-01-01"):
    return pd.Series(vals, index=pd.bdate_range(start, periods=len(vals)))


def test_episode_short_dip_stays_one_episode():
    """red 후 yellow 미만 하락이 cooldown(10) 미만이면 같은 episode."""
    mu, sd = 0.0, 1.0  # yellow=2, red=3
    vals = [0.5] * 5 + [3.5] * 5 + [1.0] * 6 + [3.5] * 5 + [1.0] * 15
    eps = stress.detect_episodes(_sbar(vals), mu, sd, cooldown=10)
    assert len(eps) == 1
    assert eps[0].close_date is not None  # 마지막 15일 < yellow로 close


def test_episode_cooldown_splits_two_episodes():
    """yellow 미만 연속 10일 이상 → close 후 재상승은 새 episode."""
    mu, sd = 0.0, 1.0
    vals = [3.5] * 5 + [1.0] * 12 + [3.5] * 5 + [1.0] * 12
    eps = stress.detect_episodes(_sbar(vals), mu, sd, cooldown=10)
    assert len(eps) == 2
    assert all(e.close_date is not None for e in eps)


def test_episode_yellow_only_never_opens():
    """yellow(2σ)만 넘고 red(3σ) 미달이면 episode 미개시."""
    mu, sd = 0.0, 1.0
    vals = [2.5] * 30
    eps = stress.detect_episodes(_sbar(vals), mu, sd)
    assert len(eps) == 0


# ------------------------------------------------------ 사전등록 강제 (SPEC §5.1)

def test_calibration_refuses_unregistered_windows(monkeypatch):
    """window 미등록 사건 실행 시도 → 거부되어야 함.

    실제 C-US v1 calibration events는 calibration_plan.md 이후 모두 등록되어야 하므로,
    이 테스트는 임시 dummy event를 주입해 사전등록 guard 자체를 검증한다.
    """
    raw = make_raw()
    events = dict(config.CALIBRATION_EVENTS)
    events["UNREGISTERED_DUMMY"] = {
        "kind": "positive",
        "stable": None,
        "control": None,
        "crisis": None,
        "modes": ["live"],
    }
    monkeypatch.setattr(config, "CALIBRATION_EVENTS", events)

    with pytest.raises(RuntimeError, match="pre-registered"):
        calibration.run_event(raw, "UNREGISTERED_DUMMY", mode="live")


def test_calibration_runs_registered_event():
    """window 고정된 GFC_2008은 실행되고 raw 지표 전량이 산출된다."""
    raw = make_raw()
    res = calibration.run_event(raw, "GFC_2008", mode="live")
    for key in (
        "Sep_Pi",
        "Sep_Sbar",
        "stable_max_abs_corr",
        "n_red_episodes",
        "missingness",
        "p99_event_specific",
    ):
        assert key in res
    assert res["Sep_Pi"] > 0
    # 합성 데이터에 위기 bump를 넣었으므로 분리가 나와야 정상
    assert res["Sep_Pi"] > 1.0


# ------------------------------------------ SPEC-코드 일치 (SPEC §1.1·§1.2)

def test_historical_repro_uses_tedrate():
    """SPEC §1.2: historical 조합 = DFF × TEDRATE × TOTBKCR.
    repro 모드의 Ψ는 |Δ5|TEDRATE여야 하며 CP–T-bill과 달라야 한다.
    """
    raw = make_raw()
    repro = ch.build_credit_channels(raw, mode="historical_repro")
    live = ch.build_credit_channels(raw, mode="live")

    # repro Ψ == |Δ5|TEDRATE (직접 재계산과 일치)
    ted = ch.locf_align(raw["TEDRATE"], 5).reindex(repro.index)
    expected_psi = ted.diff(5).abs().dropna()
    common = repro.index.intersection(expected_psi.index)
    pd.testing.assert_series_equal(
        repro.loc[common, "psi_raw"],
        expected_psi.loc[common],
        check_names=False,
        check_exact=True,
    )

    # repro Ψ ≠ live Ψ (합성 TEDRATE와 CP–T-bill은 다른 시리즈)
    both = repro.index.intersection(live.index)
    assert (repro.loc[both, "psi_raw"] - live.loc[both, "psi_raw"]).abs().max() > 1e-9


def test_historical_repro_requires_tedrate():
    """TEDRATE 없이 repro 모드 호출 → 거부 (SPEC §1.2 강제)."""
    raw = make_raw()
    raw.pop("TEDRATE")
    with pytest.raises(ValueError, match="TEDRATE"):
        ch.build_credit_channels(raw, mode="historical_repro")


def test_sensitivity_recorded_but_not_in_passfail():
    """SPEC §1.1: DGS3MO sensitivity는 결과에 기록되되 pass/fail에 미사용."""
    raw = make_raw()
    res = calibration.run_event(raw, "GFC_2008", mode="live")
    sens = res["sensitivity_DCPF3M_minus_DGS3MO"]
    assert sens is not None and "Sep_Pi" in sens and "error" not in sens
    assert "record-only" in sens["note"]
    # passfail은 primary 지표만 사용 — sensitivity 값을 바꿔도 판정 불변
    base = calibration.passfail([res])
    res2 = {**res, "sensitivity_DCPF3M_minus_DGS3MO": {"Sep_Pi": -999}}
    assert calibration.passfail([res2]) == base


# ---------------------------------------------- writer / strict

def _raw_dict_to_long(raw: dict) -> pd.DataFrame:
    rows = []
    for sid, s in raw.items():
        for d, v in s.items():
            rows.append(
                {
                    "provider": "FRED",
                    "series_id": sid,
                    "observation_date": str(d.date()),
                    "realtime_start": None,
                    "realtime_end": None,
                    "value": v,
                    "unit": None,
                    "fetch_status": "ok",
                    "fetched_at_utc": "2026-08-15T00:05:00Z",
                }
            )
    return pd.DataFrame(rows)


def _spec_and_lock(tmp_path):
    common = tmp_path / "SPEC-1.0_common.md"
    common.write_text("common", encoding="utf-8")
    sub = tmp_path / "SPEC-1.0-C-US.md"
    sub.write_text("c-us", encoding="utf-8")
    lock = tmp_path / "requirements.lock"
    lock.write_text("pandas==3.0.2", encoding="utf-8")
    return {"common": common, "subtrack": sub}, lock


def test_snapshot_writer_roundtrip(tmp_path):
    """writer가 5개 파일 생성, manifest hash 검증 통과, unavailable 기록,
    append-only 위반 시 거부.
    """
    import datetime as dt
    from pi_archive import writer

    raw = make_raw()
    # 인위적 결측: fill 한도 초과 gap → computed_status로 기록되어야 함
    cp = raw["DCPF3M"].copy()
    cp.loc["2007-03-05":"2007-03-16"] = np.nan
    raw["DCPF3M"] = cp

    specs, lock = _spec_and_lock(tmp_path)
    p99 = {"rho": 0.05, "psi": 0.10, "omega": 8500.0}
    now = dt.datetime(2026, 8, 15, 0, 5, 0, tzinfo=dt.timezone.utc)

    run_dir = writer.write_snapshot(
        raw_long=_raw_dict_to_long(raw),
        raw_series=raw,
        subtrack="C-US",
        base_dir=tmp_path / "snapshots",
        spec_paths=specs,
        p99=p99,
        freeze_date="2006-01-02",
        lock_path=lock,
        now_utc=now,
        snapshot_status="dry_run",
    )

    for f in ("raw.csv", "computed.csv", "alert.json", "meta.json", "manifest.sha256"):
        assert (run_dir / f).exists()
    assert writer.verify_snapshot(run_dir)

    comp = pd.read_csv(run_dir / "computed.csv")
    assert "computed_status" in comp.columns
    assert (comp["computed_status"] == "unavailable_fill_limit").any()  # gap 기록됨
    assert (comp["computed_status"] == "ok").sum() > 1000
    assert set(comp.columns) == set(writer.COMPUTED_COLUMNS)

    # raw에 snapshot_id/subtrack 포함 (common C11.2)
    rawcsv = pd.read_csv(run_dir / "raw.csv")
    assert {"snapshot_id", "subtrack"} <= set(rawcsv.columns)

    # append-only: 동일 run 재작성 거부
    with pytest.raises(FileExistsError):
        writer.write_snapshot(
            raw_long=_raw_dict_to_long(raw),
            raw_series=raw,
            subtrack="C-US",
            base_dir=tmp_path / "snapshots",
            spec_paths=specs,
            p99=p99,
            freeze_date="2006-01-02",
            lock_path=lock,
            now_utc=now,
            snapshot_status="dry_run",
        )


def test_pi_since_freeze_invariant_to_history_start(tmp_path):
    """Π 적분 원점 고정 검증: fetch 시작점이 달라도(2004 vs 2005)
    freeze일 이후 Pi_since_freeze 값은 동일해야 한다.
    """
    from pi_archive import stress as st_mod

    raw_a = make_raw()
    raw_b = {k: s.loc["2005-01-01":] for k, s in raw_a.items()}

    freeze = "2007-01-02"
    p99 = {"rho": 0.05, "psi": 0.10, "omega": 8500.0}

    def compute(raw):
        chan = ch.build_credit_channels(raw, mode="live")
        st = st_mod.compute_stress(st_mod.normalize(chan, p99))
        return st_mod.pi_since(st["S"], freeze)

    pa, pb = compute(raw_a), compute(raw_b)
    common = pa.dropna().index.intersection(pb.dropna().index)
    assert len(common) > 500
    assert (pa.loc[common] - pb.loc[common]).abs().max() < 1e-12


def test_strict_mode_fails_on_todo_windows(monkeypatch):
    """freeze-prep strict: TODO window가 하나라도 있으면 실패."""
    events = dict(config.CALIBRATION_EVENTS)
    events["UNREGISTERED_DUMMY"] = {
        "kind": "negative",
        "stable": ("2014-01-01", "2016-12-31"),
        "control": None,
        "crisis": ("2017-01-01", "2017-12-31"),
        "modes": ["live"],
    }
    monkeypatch.setattr(config, "CALIBRATION_EVENTS", events)

    assert "UNREGISTERED_DUMMY" in calibration.unregistered_events()
    with pytest.raises(RuntimeError, match="unregistered"):
        calibration.assert_all_windows_registered()


def test_registered_calibration_events_match_plan():
    """calibration_plan.md v1 반영 후 canonical C-US events는 모두 등록되어 있어야 함."""
    assert calibration.unregistered_events() == []
    assert {
        "GFC_2008",
        "CREDIT_SHOCK_2020",
        "SVB_2023",
        "REPO_2019",
        "QUIET_2017",
    } <= set(config.CALIBRATION_EVENTS)


def test_correction_reason_controlled_vocabulary(tmp_path):
    """common C10.3: correction_reason은 통제 어휘 외 거부."""
    import datetime as dt
    from pi_archive import writer

    raw = make_raw()
    specs, lock = _spec_and_lock(tmp_path)
    with pytest.raises(ValueError, match="controlled vocabulary"):
        writer.write_snapshot(
            raw_long=_raw_dict_to_long(raw),
            raw_series=raw,
            subtrack="C-US",
            base_dir=tmp_path / "snapshots",
            spec_paths=specs,
            p99={"rho": 0.05, "psi": 0.10, "omega": 8500.0},
            freeze_date="2006-01-02",
            lock_path=lock,
            snapshot_status="correction",
            correction_reason="I_FELT_LIKE_IT",
            now_utc=dt.datetime(2026, 8, 15, 3, 12, 0, tzinfo=dt.timezone.utc),
        )


# ----------------------------------------- simplicity pass (v5) 검증

def test_verify_fails_on_missing_manifest_entry(tmp_path):
    """manifest에 존재하지 않는 파일 항목 → verify 실패."""
    import datetime as dt
    from pi_archive import writer

    raw = make_raw()
    specs, lock = _spec_and_lock(tmp_path)
    run_dir = writer.write_snapshot(
        raw_long=_raw_dict_to_long(raw),
        raw_series=raw,
        subtrack="C-US",
        base_dir=tmp_path / "snapshots",
        spec_paths=specs,
        p99={"rho": 0.05, "psi": 0.10, "omega": 8500.0},
        freeze_date="2006-01-02",
        lock_path=lock,
        snapshot_status="dry_run",
        now_utc=dt.datetime(2026, 8, 16, 0, 5, 0, tzinfo=dt.timezone.utc),
    )
    assert writer.verify_snapshot(run_dir)
    with open(run_dir / "manifest.sha256", "a", encoding="utf-8") as f:
        f.write("deadbeef" * 8 + "  missing.txt\n")
    assert not writer.verify_snapshot(run_dir)  # 누락 파일 → 반드시 False


def test_manifest_covers_only_local_files(tmp_path):
    """simplicity: manifest는 run 폴더 내 4파일만. SPEC/lock은 meta 담당."""
    import datetime as dt
    import json
    from pi_archive import writer

    raw = make_raw()
    specs, lock = _spec_and_lock(tmp_path)
    run_dir = writer.write_snapshot(
        raw_long=_raw_dict_to_long(raw),
        raw_series=raw,
        subtrack="C-US",
        base_dir=tmp_path / "snapshots",
        spec_paths=specs,
        p99={"rho": 0.05, "psi": 0.10, "omega": 8500.0},
        freeze_date="2006-01-02",
        lock_path=lock,
        snapshot_status="dry_run",
        now_utc=dt.datetime(2026, 8, 17, 0, 5, 0, tzinfo=dt.timezone.utc),
    )
    names = [
        l.split(None, 1)[1].strip()
        for l in (run_dir / "manifest.sha256").read_text().strip().splitlines()
    ]
    assert sorted(names) == ["alert.json", "computed.csv", "meta.json", "raw.csv"]

    meta = json.loads((run_dir / "meta.json").read_text())
    # SPEC/환경/계산상수는 meta에 박제
    assert meta["spec_common_sha256"] and meta["spec_subtrack_sha256"]
    assert meta["environment_hash"]
    assert meta["p99_used"]["rho"] == 0.05
    assert meta["freeze_date"] == "2006-01-02"
    assert meta["snapshot_status"] == "dry_run"


def test_official_snapshot_requires_frozen_constants(tmp_path):
    """freeze 이전(mu_sigma 없음)에 status=valid → 거부.
    frozen 상수 미설정 상태에서 공식 snapshot → 거부.
    """
    import datetime as dt
    from pi_archive import writer

    raw = make_raw()
    specs, lock = _spec_and_lock(tmp_path)
    kw = dict(
        raw_long=_raw_dict_to_long(raw),
        raw_series=raw,
        subtrack="C-US",
        base_dir=tmp_path / "snapshots",
        spec_paths=specs,
        p99={"rho": 0.05, "psi": 0.10, "omega": 8500.0},
        freeze_date="2006-01-02",
        lock_path=lock,
        now_utc=dt.datetime(2026, 8, 18, 0, 5, 0, tzinfo=dt.timezone.utc),
    )

    with pytest.raises(ValueError, match="dry_run"):
        writer.write_snapshot(**kw, snapshot_status="valid")  # mu_sigma 없음

    with pytest.raises(ValueError, match="not frozen yet"):
        writer.write_snapshot(
            **kw,
            snapshot_status="valid",
            mu_sigma={"mu": 0.1, "sigma": 0.05},
        )  # LIVE_* 미설정


def test_official_snapshot_enforces_config_match(tmp_path, monkeypatch):
    """freeze 후: 공식 snapshot의 p99/mu_sigma/freeze_date가 config frozen 상수와
    다르면 거부, 일치하면 통과.
    """
    import datetime as dt
    from pi_archive import config as cfg, writer

    frozen_p99 = {"rho": 0.05, "psi": 0.10, "omega": 8500.0}
    frozen_ms = {"mu": 0.1, "sigma": 0.05}
    monkeypatch.setattr(cfg, "LIVE_P99", frozen_p99)
    monkeypatch.setattr(cfg, "LIVE_MU_SIGMA", frozen_ms)
    monkeypatch.setattr(cfg, "LIVE_FREEZE_DATE", "2026-08-20")

    raw = make_raw()
    specs, lock = _spec_and_lock(tmp_path)
    kw = dict(
        raw_long=_raw_dict_to_long(raw),
        raw_series=raw,
        subtrack="C-US",
        base_dir=tmp_path / "snapshots",
        spec_paths=specs,
        lock_path=lock,
        now_utc=dt.datetime(2026, 8, 21, 0, 5, 0, tzinfo=dt.timezone.utc),
    )

    with pytest.raises(ValueError, match="does not match frozen"):
        writer.write_snapshot(
            **kw,
            p99={"rho": 9.9, "psi": 0.10, "omega": 8500.0},
            mu_sigma=frozen_ms,
            freeze_date="2026-08-20",
            snapshot_status="valid",
        )

    run_dir = writer.write_snapshot(
        **kw,
        p99=frozen_p99,
        mu_sigma=frozen_ms,
        freeze_date="2026-08-20",
        snapshot_status="valid",
        code_git_commit="abc123",
    )

    from pi_archive.writer import verify_snapshot
    assert verify_snapshot(run_dir)


def test_official_snapshot_requires_audit_metadata(tmp_path, monkeypatch):
    """공식 snapshot은 repo commit과 requirements.lock hash가 있어야 한다."""
    import datetime as dt
    from pi_archive import config as cfg, writer

    frozen_p99 = {"rho": 0.05, "psi": 0.10, "omega": 8500.0}
    frozen_ms = {"mu": 0.1, "sigma": 0.05}
    monkeypatch.setattr(cfg, "LIVE_P99", frozen_p99)
    monkeypatch.setattr(cfg, "LIVE_MU_SIGMA", frozen_ms)
    monkeypatch.setattr(cfg, "LIVE_FREEZE_DATE", "2026-08-20")

    raw = make_raw()
    specs, lock = _spec_and_lock(tmp_path)
    kw = dict(
        raw_long=_raw_dict_to_long(raw),
        raw_series=raw,
        subtrack="C-US",
        base_dir=tmp_path / "snapshots",
        spec_paths=specs,
        p99=frozen_p99,
        mu_sigma=frozen_ms,
        freeze_date="2026-08-20",
        snapshot_status="valid",
        now_utc=dt.datetime(2026, 8, 22, 0, 5, 0, tzinfo=dt.timezone.utc),
    )

    with pytest.raises(ValueError, match="code_git_commit"):
        writer.write_snapshot(**kw, lock_path=lock)

    with pytest.raises(ValueError, match="requirements.lock"):
        writer.write_snapshot(**kw, code_git_commit="abc123")


def test_dry_run_without_threshold_has_null_alert_level(tmp_path):
    """dry_run에서 μ/σ가 없으면 pending_freeze 같은 제4상태를 쓰지 않는다."""
    import datetime as dt
    import json
    from pi_archive import writer

    raw = make_raw()
    specs, lock = _spec_and_lock(tmp_path)
    run_dir = writer.write_snapshot(
        raw_long=_raw_dict_to_long(raw),
        raw_series=raw,
        subtrack="C-US",
        base_dir=tmp_path / "snapshots",
        spec_paths=specs,
        p99={"rho": 0.05, "psi": 0.10, "omega": 8500.0},
        freeze_date="2006-01-02",
        lock_path=lock,
        snapshot_status="dry_run",
        now_utc=dt.datetime(2026, 8, 23, 0, 5, 0, tzinfo=dt.timezone.utc),
    )
    comp = pd.read_csv(run_dir / "computed.csv")
    assert comp["alert_level"].dropna().empty
    alert = json.loads((run_dir / "alert.json").read_text())
    assert alert["alert_level"] is None
