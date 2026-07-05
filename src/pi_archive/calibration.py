"""Calibration runner — SPEC-1.0-C-US v5 §5.

원칙 (common C5):
- usability check이지 성능 최적화 아님
- 사건 window는 calibration_plan으로 실행 전 고정 (config에 None이면 실행 거부)
- 전면 공개: pass/fail만이 아니라 Sep(Π), Sep(S̄), max|r|, episode 수,
  결측률 raw 결과를 전부 산출·저장
- event-specific P99 (§2.2) — live frozen P99와 절대 혼용 금지
"""
from __future__ import annotations

import pandas as pd

from . import channels as ch
from . import config, stress


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


def run_event(raw: dict[str, pd.Series], event_name: str, mode: str) -> dict:
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

    eval_win = st.loc[ev["crisis"][0]:ev["crisis"][1], "Sbar_w"]
    episodes = stress.detect_episodes(eval_win, mu, sd) if sd == sd else []

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
        "n_red_episodes": len(episodes),
        "episodes": [(str(e.open_date.date()),
                      str(e.close_date.date()) if e.close_date is not None else None)
                     for e in episodes],
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
