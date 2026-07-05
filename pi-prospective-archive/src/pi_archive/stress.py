"""Normalization, stress computation, and episode logic.

SPEC-1.0-C-US v5 §2 (P99), §3 (S̄_w, thresholds), common C6 (episodes).
모든 연산은 인과적: rolling은 과거 방향(trailing)만, 미래 참조 없음.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config


# ------------------------------------------------------------------- P99

def p99_from_window(channels: pd.DataFrame, start: str, end: str) -> dict:
    """stable window에서 채널별 P99 산출 (SPEC §2)."""
    win = channels.loc[start:end]
    if win.empty:
        raise ValueError(f"empty stable window {start}..{end}")
    return {
        "rho": float(win["rho_raw"].quantile(0.99)),
        "psi": float(win["psi_raw"].quantile(0.99)),
        "omega": float(win["omega_raw"].quantile(0.99)),
    }


def normalize(channels: pd.DataFrame, p99: dict) -> pd.DataFrame:
    """x̂ = x / P99 (SPEC §2). P99는 밖에서 주입 — 어디서 왔는지(§2.1 vs §2.2)는
    호출자가 책임진다 (이원화 원칙)."""
    for k in ("rho", "psi", "omega"):
        if not p99.get(k) or p99[k] <= 0:
            raise ValueError(f"invalid P99 for {k}: {p99.get(k)}")
    out = pd.DataFrame(index=channels.index)
    out["rho_hat"] = channels["rho_raw"] / p99["rho"]
    out["psi_hat"] = channels["psi_raw"] / p99["psi"]
    out["omega_hat"] = channels["omega_raw"] / p99["omega"]
    return out


# ---------------------------------------------------------------- stress

def compute_stress(norm: pd.DataFrame,
                   w: int = config.SBAR_WINDOW_TRADING_DAYS,
                   tau0: float = config.TAU0) -> pd.DataFrame:
    """S = ρ̂·Ψ̂·Ω̂;  S̄_w = trailing rolling mean (w 거래일 관측치);
    Π = 누적합 × τ₀ (foundation과 동일한 관측치-가중 적분)."""
    out = norm.copy()
    out["S"] = out["rho_hat"] * out["psi_hat"] * out["omega_hat"]
    out["Sbar_w"] = out["S"].rolling(window=w, min_periods=w).mean()  # trailing = 인과적
    out["Pi"] = out["S"].cumsum() * tau0
    return out


def pi_since(S: pd.Series, origin, tau0: float = config.TAU0) -> pd.Series:
    """Π의 적분 원점을 고정한 누적 (SPEC C-US v4 §3: live Π = Pi_since_freeze).

    cumsum이 입력 데이터 시작점에 의존하는 문제(fetch start가 바뀌면 Π 절대값이
    달라짐)를 제거: origin(=freeze일) 이전 기여는 0, origin 이전 날짜의 Π는 NaN.
    → 같은 날짜의 Π 값이 history 시작점과 무관하게 유일하게 정의된다."""
    origin = pd.Timestamp(origin)
    s = S.copy().fillna(0.0)
    s.loc[s.index < origin] = 0.0
    out = s.cumsum() * tau0
    out.loc[out.index < origin] = float("nan")
    return out


def sep_pi(stress: pd.DataFrame, crisis: tuple, control: tuple,
           tau0: float = config.TAU0) -> dict:
    """Sep(Π) = Π_crisis/Π_control;  Sep(S̄) = 시간정규화 (Π/T) 비율, T = N·τ₀."""
    c = stress.loc[crisis[0]:crisis[1], "S"]
    k = stress.loc[control[0]:control[1], "S"]
    if c.empty or k.empty:
        raise ValueError("empty crisis/control window")
    pi_c, pi_k = c.sum() * tau0, k.sum() * tau0
    t_c, t_k = len(c) * tau0, len(k) * tau0
    sep = pi_c / pi_k if pi_k > 0 else float("inf")
    sep_sbar = (pi_c / t_c) / (pi_k / t_k) if pi_k > 0 else float("inf")
    return {"Pi_crisis": pi_c, "Pi_control": pi_k,
            "N_crisis": len(c), "N_control": len(k),
            "Sep_Pi": sep, "Sep_Sbar": sep_sbar}


# -------------------------------------------------------------- episodes

@dataclass
class Episode:
    open_date: pd.Timestamp
    close_date: pd.Timestamp | None  # None = still open
    episode_id: str


def detect_episodes(sbar: pd.Series, mu: float, sigma: float,
                    subtrack: str = "C-US",
                    yellow_k: float = config.YELLOW_SIGMA,
                    red_k: float = config.RED_SIGMA,
                    cooldown: int = config.EPISODE_COOLDOWN_TRADING_DAYS
                    ) -> list[Episode]:
    """common C6: red 첫 충족일 open; S̄_w < yellow 기준으로 연속 cooldown
    거래일 유지 시 close; open 중 재상승은 같은 episode."""
    red_thr = mu + red_k * sigma
    yellow_thr = mu + yellow_k * sigma

    episodes: list[Episode] = []
    open_ep: Episode | None = None
    below_streak = 0

    for date, val in sbar.dropna().items():
        if open_ep is None:
            if val > red_thr:
                open_ep = Episode(open_date=date, close_date=None,
                                  episode_id=f"{subtrack}-red-{date.date()}")
                below_streak = 0
        else:
            if val < yellow_thr:
                below_streak += 1
                if below_streak >= cooldown:
                    open_ep.close_date = date
                    episodes.append(open_ep)
                    open_ep = None
                    below_streak = 0
            else:
                below_streak = 0  # 재상승 → streak 리셋, 같은 episode 유지

    if open_ep is not None:
        episodes.append(open_ep)  # still open
    return episodes
