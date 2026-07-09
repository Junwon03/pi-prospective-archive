"""Channel alignment and transforms — CAUSAL (as-of) by construction.

SPEC-1.0_common C4.5: live 계산은 snapshot 시점에 보이는 관측치만 사용한다.
이 모듈의 모든 live 함수는 LOCF(과거→현재)만 쓰며, 미래 관측을 요구하는
연산(선형보간, 중심 rolling, backward fill)은 존재하지 않는다.

historical 재현 모드(foundation 논문 재현)의 선형보간은 별도 함수로 격리하고
이름에 NONCAUSAL을 박아 live 경로에서 실수로 못 쓰게 한다.
"""
from __future__ import annotations

import pandas as pd

from . import config


# ----------------------------------------------------------------- align

def locf_align(series: pd.Series, limit_calendar_days: int, end=None) -> pd.Series:
    """As-of alignment: 일 캘린더로 reindex 후 과거값만 LOCF (한도 내).

    인과성 보장: t 시점 값은 t 이전 관측만으로 결정된다.
    한도 초과 gap은 NaN으로 남는다 (computed unavailable — SPEC §1.3).

    end가 주어지면 series의 마지막 관측일 이후에도 end까지 캘린더를 확장한다.
    이는 주간/지연 시리즈(TOTBKCR 등)가 일별 grid보다 먼저 끝나는 live
    snapshot에서, 허용 한도 내 trailing LOCF가 동작하게 하기 위한 것이다.
    미래값을 만들지 않고 마지막 관측값만 carry하므로 인과성은 유지된다.
    """
    s = series.dropna().sort_index()
    if s.empty:
        return s
    stop = s.index.max() if end is None else max(s.index.max(), pd.Timestamp(end))
    cal = pd.date_range(s.index.min(), stop, freq="D")
    return s.reindex(cal).ffill(limit=limit_calendar_days)


def linear_interp_NONCAUSAL_repro_only(series: pd.Series) -> pd.Series:
    """foundation 논문 재현 전용 (historical_repro 모드).

    선형보간은 다음 관측(미래)을 필요로 하므로 live에서 사용 금지
    (common C4.5). calibration/reproduction 라벨 하에서만 호출할 것.
    """
    s = series.dropna().sort_index()
    if s.empty:
        return s
    cal = pd.date_range(s.index.min(), s.index.max(), freq="D")
    return s.reindex(cal).interpolate(method="time", limit_direction="forward").ffill()


# ------------------------------------------------------------ transforms

def abs_delta_trading(series: pd.Series, k: int = config.DELTA_TRADING_DAYS) -> pd.Series:
    """|Δ over k 거래일 관측치| — 관측 행 기준 diff (과거 방향, 인과적)."""
    return series.diff(k).abs()


# --------------------------------------------------------- channel build

def build_credit_channels(
    raw: dict[str, pd.Series], mode: str = "live", psi_short: str = "DTB3",
    drop_incomplete: bool = True,
) -> pd.DataFrame:
    """C-US 3채널 원시 시계열 → 변환된 (rho, psi, omega) DataFrame.

    mode="live" (SPEC §1.2 live 조합, §1.4 live causal rule):
        Ψ = DCPF3M − psi_short (기본 DTB3; sensitivity 시 "DGS3MO" — SPEC §1.1,
        기록 전용이며 frozen primary를 바꾸는 데 사용 금지)
        Ω = TOTBKCR as-of LOCF
    mode="historical_repro" (SPEC §1.2 historical 조합 — foundation 재현 전용):
        Ψ = TEDRATE (raw에 TEDRATE 필수 — 없으면 거부)
        Ω = TOTBKCR 선형보간 (NONCAUSAL — live 사용 금지)

    반환 index = 세 채널 모두 유효한 거래일 관측치 (business days).
    """
    if mode not in ("live", "historical_repro"):
        raise ValueError(f"unknown mode: {mode}")

    lim = config.FILL_LIMIT_CALENDAR_DAYS

    if mode == "live":
        if psi_short not in ("DTB3", "DGS3MO"):
            raise ValueError(f"psi_short must be DTB3 (primary) or DGS3MO (sensitivity), got {psi_short}")

        obs_days = (
            raw["DFF"].dropna().index
            .union(raw["DCPF3M"].dropna().index)
            .union(raw[psi_short].dropna().index)
        )
        grid = pd.DatetimeIndex(sorted(d for d in obs_days if d.weekday() < 5))
        grid_end = grid.max() if len(grid) else None

        dff = locf_align(raw["DFF"], lim["DFF"], end=grid_end)
        cp = locf_align(raw["DCPF3M"], lim["DCPF3M"], end=grid_end)
        short = locf_align(raw[psi_short], lim[psi_short], end=grid_end)
        omega_daily = locf_align(raw["TOTBKCR"], lim["TOTBKCR"], end=grid_end)

        psi_base = (cp - short).reindex(grid)

    else:  # historical_repro — foundation 조합 재현 (SPEC §1.2)
        if "TEDRATE" not in raw:
            raise ValueError(
                "historical_repro requires TEDRATE (SPEC §1.2: "
                "historical = DFF x TEDRATE x TOTBKCR). live 조합 재현이 목적이면 mode='live'."
            )

        obs_days = raw["DFF"].dropna().index.union(raw["TEDRATE"].dropna().index)
        grid = pd.DatetimeIndex(sorted(d for d in obs_days if d.weekday() < 5))
        grid_end = grid.max() if len(grid) else None

        dff = locf_align(raw["DFF"], lim["DFF"], end=grid_end)
        ted = locf_align(raw["TEDRATE"], lim["TEDRATE"], end=grid_end)
        omega_daily = linear_interp_NONCAUSAL_repro_only(raw["TOTBKCR"])

        psi_base = ted.reindex(grid)

    rho = abs_delta_trading(dff.reindex(grid))
    psi = abs_delta_trading(psi_base)
    omega = omega_daily.reindex(grid)  # level (SPEC §1)

    df = pd.DataFrame({"rho_raw": rho, "psi_raw": psi, "omega_raw": omega})
    # drop_incomplete=False: live snapshot writer용 — 결측 행을 삭제하지 않고 보존해
    # computed_status="unavailable_fill_limit"로 기록할 수 있게 함 (감사 가능성).
    return df.dropna() if drop_incomplete else df
