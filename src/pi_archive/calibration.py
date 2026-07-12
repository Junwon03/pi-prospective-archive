"""Calibration runner — SPEC-1.0-C-US v5 §5.

원칙 (common C5):
- usability check이지 성능 최적화 아님
- 사건 window는 calibration_plan으로 실행 전 고정 (config에 None이면 실행 거부)
- 전면 공개: pass/fail만이 아니라 Sep(Π), Sep(S̄), max|r|, episode 수,
  결측률 raw 결과를 전부 산출·저장
- event-specific P99 (§2.2) — live frozen P99와 절대 혼용 금지

v2 scoring addendum:
- episode identity는 open date 기준(common C6)
- calibration pass/fail은 evaluation window 안에서 새로 open한 red episode만 count
- window 시작 전에 이미 열려 있던 inherited active red episode는 별도 disclosure로 기록
"""
from __future__ import annotations

import pandas as pd

from . import channels as ch
from . import config, stress


EPISODE_CONTEXT_DAYS = 365
SCORING_WINDOW_SLICED_V1 = "window_sliced_v1"
SCORING_OPEN_DATE_V2 = "open_date_attribution_v2"


def missingness_report(raw: dict[str, pd.Series], start: str, end: str) -> dict:
    """구간 내 채널별 결측률 (fill 이전, 원시 관측 기준)."""
    out = {}
    for sid, s in raw.items():
        win = s.loc[start:end]
        n = len(win)
        out[sid] = {"n_obs": n, "n_missing": int(win.isna().sum()),
                    "missing_rate": float(win.isna().mean()) if n else None}
    return out


def stable_max_corr(chan: pd.DataFrame, start: str, end: str) -> float:
    """stable 기간 변환 후 채널 pairwise max|r| (common C3 기준 4: < 0.7)."""
    win = chan.loc[start:end, ["rho_raw", "psi_raw", "omega_raw"]]
    corr = win.corr().abs()
    vals = [corr.iloc[i, j] for i in range(3) for j in range(i + 1, 3)]
    return float(max(vals))


def _episode_pair(e: stress.Episode) -> tuple[str, str | None]:
    return (
        str(e.open_date.date()),
        str(e.close_date.date()) if e.close_date is not None else None,
    )


def _episode_overlaps_window(e: stress.Episode, start: pd.Timestamp, end: pd.Timestamp) -> bool:
    """Episode가 평가창과 겹치는지 판정.

    close_date=None은 still-open으로 간주한다.
    """
    close = e.close_date if e.close_date is not None else pd.Timestamp.max
    return e.open_date <= end and close >= start


def open_date_episode_attribution(
    stress_df: pd.DataFrame,
    eval_window: tuple[str, str],
    mu: float,
    sigma: float,
    context_days: int = EPISODE_CONTEXT_DAYS,
) -> dict:
    """Open-date episode attribution (scoring addendum v1).

    기존 v1 하네스는 evaluation window만 잘라 episode detection을 수행했다.
    이 경우 window 시작 전에 이미 열린 episode가 window 첫날에 새로 열린 것처럼
    오귀속될 수 있다. v2는 충분한 context window에서 episode를 먼저 찾은 뒤,
    open_date가 evaluation window 안에 있는 episode만 primary pass/fail count로 센다.

    window 시작 전에 열린 상태로 evaluation window와 겹치는 episode는
    inherited_active로 별도 공개한다.
    """
    eval_start = pd.Timestamp(eval_window[0])
    eval_end = pd.Timestamp(eval_window[1])
    context_start = eval_start - pd.Timedelta(days=context_days)
    context_end = eval_end + pd.Timedelta(days=context_days)

    context_sbar = stress_df.loc[context_start:context_end, "Sbar_w"]
    context_episodes = stress.detect_episodes(context_sbar, mu, sigma)

    opened = [
        e for e in context_episodes
        if eval_start <= e.open_date <= eval_end
    ]
    inherited = [
        e for e in context_episodes
        if e.open_date < eval_start and _episode_overlaps_window(e, eval_start, eval_end)
    ]

    return {
        "scoring_method": SCORING_OPEN_DATE_V2,
        "episode_context_days": context_days,
        "episode_context_window": (
            str(context_start.date()),
            str(context_end.date()),
        ),
        "red_episodes_opened_in_window": len(opened),
        "n_red_episodes": len(opened),
        "episodes": [_episode_pair(e) for e in opened],
        "n_inherited_active_red_episodes": len(inherited),
        "inherited_active_episodes": [_episode_pair(e) for e in inherited],
        "all_context_episodes": [_episode_pair(e) for e in context_episodes],
    }


def window_sliced_episode_attribution(
    stress_df: pd.DataFrame,
    eval_window: tuple[str, str],
    mu: float,
    sigma: float,
) -> dict:
    """Original v1 window-sliced attribution.

    v1 결과를 보존하기 위해 기존 방식도 명시적으로 남긴다.
    """
    eval_sbar = stress_df.loc[eval_window[0]:eval_window[1], "Sbar_w"]
    episodes = stress.detect_episodes(eval_sbar, mu, sigma)
    return {
        "scoring_method": SCORING_WINDOW_SLICED_V1,
        "n_red_episodes": len(episodes),
        "episodes": [_episode_pair(e) for e in episodes],
    }


def run_event(
    raw: dict[str, pd.Series],
    event_name: str,
    mode: str,
    scoring_method: str = SCORING_WINDOW_SLICED_V1,
) -> dict:
    """단일 calibration 사건 실행 → raw 결과 dict (전면 공개용)."""
    ev = config.CALIBRATION_EVENTS[event_name]
    for key in ("stable", "control", "crisis"):
        if ev[key] is None:
            raise RuntimeError(
                f"{event_name}.{key} window is not pre-registered. "
                "calibration_plan.md를 commit해 window를 고정한 뒤 config에 반영할 것 "
                "(SPEC §5.1 — 실행 전 사전등록 필수)."
            )
    if mode not in ev["modes"]:
        raise ValueError(f"{event_name} does not allow mode={mode}")
    if scoring_method not in (SCORING_WINDOW_SLICED_V1, SCORING_OPEN_DATE_V2):
        raise ValueError(f"unknown scoring_method: {scoring_method}")

    chan = ch.build_credit_channels(raw, mode=mode)

    # event-specific P99 (§2.2) — 이 사건의 사전등록 stable window에서만
    p99 = stress.p99_from_window(chan, *ev["stable"])
    norm = stress.normalize(chan, p99)
    st = stress.compute_stress(norm)

    sep = stress.sep_pi(st, ev["crisis"], ev["control"])

    # control 기간 기반 μ/σ (이 사건 내부용 — live μ/σ와 별개)
    ctrl_sbar = st.loc[ev["control"][0]:ev["control"][1], "Sbar_w"].dropna()
    mu = float(ctrl_sbar.mean()) if len(ctrl_sbar) else float("nan")
    sd = float(ctrl_sbar.std(ddof=1)) if len(ctrl_sbar) > 1 else float("nan")

    if sd == sd:
        if scoring_method == SCORING_OPEN_DATE_V2:
            episode_info = open_date_episode_attribution(st, ev["crisis"], mu, sd)
        else:
            episode_info = window_sliced_episode_attribution(st, ev["crisis"], mu, sd)
    else:
        episode_info = {
            "scoring_method": scoring_method,
            "n_red_episodes": 0,
            "episodes": [],
            "episode_detection_note": "sigma_control is NaN; episode detection skipped",
        }
        if scoring_method == SCORING_OPEN_DATE_V2:
            episode_info.update({
                "episode_context_days": EPISODE_CONTEXT_DAYS,
                "red_episodes_opened_in_window": 0,
                "n_inherited_active_red_episodes": 0,
                "inherited_active_episodes": [],
                "all_context_episodes": [],
            })

    # ---- sensitivity: DCPF3M − DGS3MO (SPEC §1.1 — 기록 전용, passfail 미사용) ----
    sensitivity = None
    if mode == "live" and "DGS3MO" in raw:
        try:
            chan_s = ch.build_credit_channels(raw, mode="live", psi_short="DGS3MO")
            p99_s = stress.p99_from_window(chan_s, *ev["stable"])
            st_s = stress.compute_stress(stress.normalize(chan_s, p99_s))
            sep_s = stress.sep_pi(st_s, ev["crisis"], ev["control"])
            sensitivity = {
                "variant": "DCPF3M_minus_DGS3MO",
                "note": "record-only; never used to alter the frozen primary (SPEC §1.1)",
                "Sep_Pi": sep_s["Sep_Pi"],
                "Sep_Sbar": sep_s["Sep_Sbar"],
                "stable_max_abs_corr": stable_max_corr(chan_s, *ev["stable"]),
            }
        except Exception as e:  # sensitivity 실패는 primary를 막지 않음 — 기록만
            sensitivity = {"variant": "DCPF3M_minus_DGS3MO", "error": repr(e)}

    return {
        "event": event_name,
        "kind": ev["kind"],
        "mode": mode,
        "p99_event_specific": p99,
        "windows": {k: ev[k] for k in ("stable", "control", "crisis")},
        **sep,
        "mu_control": mu,
        "sigma_control": sd,
        **episode_info,
        "stable_max_abs_corr": stable_max_corr(chan, *ev["stable"]),
        "sensitivity_DCPF3M_minus_DGS3MO": sensitivity,
        "missingness": missingness_report(raw, ev["stable"][0], ev["crisis"][1]),
    }


def unregistered_events() -> list[str]:
    """window 미등록(사전등록 안 된) 사건 목록."""
    return [name for name, ev in config.CALIBRATION_EVENTS.items()
            if any(ev[k] is None for k in ("stable", "control", "crisis"))]


def assert_all_windows_registered() -> None:
    """strict mode (freeze-prep): TODO window가 하나라도 남아 있으면 실패.

    실험 중에는 skip-and-run이 편하지만, freeze 직전 run이 '일부만 돌리고 pass'를
    내는 것은 위험 — freeze 전 최종 calibration은 반드시 이 검사를 통과해야 한다."""
    missing = unregistered_events()
    if missing:
        raise RuntimeError(
            f"strict mode: unregistered calibration windows remain: {missing}. "
            "calibration_plan.md를 commit해 window를 고정하고 config에 반영할 것."
        )


def passfail(results: list[dict]) -> dict:
    """SPEC §5.2 판정. raw 결과는 별도 전량 저장 — 이 함수는 요약만."""
    pos = [r for r in results if r["kind"] == "positive"]
    neg = [r for r in results if r["kind"] == "negative"]
    pos_ok = sum(1 for r in pos if r["Sep_Pi"] > 1.0 and r["Sep_Sbar"] >= 1.0)
    neg_ok = all(r["n_red_episodes"] == 0 for r in neg)
    corr_ok = all(r["stable_max_abs_corr"] < 0.7 for r in results)
    return {
        "positive_pass": pos_ok,
        "positive_total": len(pos),
        "positive_criterion": pos_ok >= 2,
        "negative_zero_red": neg_ok,
        "nonredundancy_ok": corr_ok,
        "overall_pass": (pos_ok >= 2) and neg_ok and corr_ok,
    }
