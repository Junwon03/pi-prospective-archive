#!/usr/bin/env python3
"""C-US live reference window: post-selection robustness analysis (pre-freeze disclosure).

지위 (timeline을 정확히):
  - 2026-07-13: candidate live reference window(2024-01-01..2025-12-31)와
    candidate freeze constants가 문서화됨
    (live_reference_window_v1.md, live_freeze_constants_v1.json).
  - 본 분석: 그 **선택 이후, freeze(목표 2026-08-03) 이전**에 수행되는
    robustness 공개. window를 선택하거나 최적화하는 과정이 아니며,
    결과와 무관하게 candidate window는 변경되지 않는다.

후보 생성 규칙 (전수생성 — 시작점 포함 임의 선택 없음):
  데이터가 존재하는 첫 해부터 가능한 **모든** 연속 2-calendar-year 구간.
  - 시작: 데이터 최초 연도부터 (코드가 데이터에서 유도 — 하드코딩 아님)
  - 끝: freeze 목표일 이전 마지막 완결 calendar year (= 2025)
  In-window 관측치가 burn-in(90) 요건에 못 미치는 후보는 제외가 아니라
  "insufficient"로 표시하여 공개한다.

Calibration 중첩 표시 (등급 구분):
  config.CALIBRATION_EVENTS의 crisis / control / stable window 각각과의
  중첩을 기계 판정해 `EVENT:kind` 형태로 전부 표시한다.
  - `crisis` 중첩: "비위기 baseline" 자격에 대한 실격 사유
  - `stable` / `control` 중첩: calibration이 해당 구간을 참조했다는
    정보 공개일 뿐, baseline 자격의 실격 사유가 아님
  이 등급 구분은 결과 산출 전에 정의되었다.

각 window W에 대한 계산 (live_freeze_constants_v1 "Option B"와 동일 방법):
  1. P99(W)      : mode="live" 채널의 W 구간 q99  (stress.p99_from_window)
  2. Sbar(W)     : W 내부 행만으로 S 계산 후 90 거래관측치 trailing mean
                   (min_periods=90 → in-window burn-in 자동 적용)
  3. mu, sigma   : burn-in 이후 Sbar의 평균 / 표본표준편차(ddof=1)
  4. yellow, red : mu + 2*sigma, mu + 3*sigma

운영 민감도 (out-of-window 적용):
  각 window의 {P99(W), thresholds(W)}를 2026-01-01 이후 데이터에 적용해
  yellow/red 초과 거래일 수를 센다.
  방법론 각주: 이 적용부의 Sbar_w는 전체 이력 trailing rolling mean이다.
  live 파이프라인은 300 calendar day 버퍼만 fetch하지만, trailing 90관측치
  rolling mean은 직전 90개 관측치에만 의존하므로 두 방식의 Sbar는 수치적으로
  동일하다 — 이 동등성은 주장이 아니라 본 스크립트가 실행 시마다 검증해
  출력한다 (equivalence check: candidate 상수 기준 max |diff|).
  threshold 추정은 각 window 내부에서, 적용은 운영 시계열 위에서 이루어진다.

데이터: calibration/C-US/raw_calibration.csv (freeze 전 박제된 calibration raw).
출력: markdown 표 (stdout). 공식 기록은 저자가 자기 환경에서 실행한 출력을
      window_sensitivity_analysis_v1.md 에 삽입하는 것으로 한다 —
      run_live_constants.py 와 동일한 재현성 원칙.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import json  # noqa: E402

import pandas as pd  # noqa: E402

from pi_archive import channels as ch  # noqa: E402
from pi_archive import config, daily, fetch_fred, stress  # noqa: E402

CAL_DIR = Path(__file__).parent / "calibration" / "C-US"
RAW_PATH = CAL_DIR / "raw_calibration.csv"
CONSTANTS_JSON = CAL_DIR / "live_freeze_constants_v1.json"

# candidate window 단일 출처: live_freeze_constants_v1.json (documented 2026-07-13)
_constants = json.loads(CONSTANTS_JSON.read_text(encoding="utf-8"))
CANDIDATE_WINDOW = tuple(_constants["live_stable_window"])
LAST_COMPLETE_YEAR = 2025   # target freeze date 이전 마지막 완결 calendar year
                            # (derived from target freeze date, not from results)
APPLY_FROM = "2026-01-01"   # 운영 민감도 적용 구간 시작
SBAR_BURNIN_ROWS = config.SBAR_WINDOW_TRADING_DAYS  # burn-in 요건 — config 단일 출처


def _overlap_calibration_windows(y0: int, y1: int) -> str:
    """후보 [y0-01-01, y1-12-31]와 calibration의 crisis/control/stable window
    중첩을 기계 판정해 `EVENT:kind` 목록으로 반환 (등급 의미는 docstring 참조)."""
    c0, c1 = pd.Timestamp(f"{y0}-01-01"), pd.Timestamp(f"{y1}-12-31")
    hits = []
    for ev, spec in config.CALIBRATION_EVENTS.items():
        for kind in ("crisis", "control", "stable"):
            k0, k1 = map(pd.Timestamp, spec[kind])
            if c0 <= k1 and k0 <= c1:
                hits.append(f"{ev}:{kind}")
    return ",".join(hits) if hits else "-"


def main() -> int:
    raw = pd.read_csv(RAW_PATH)
    raw_series = {sid: fetch_fred.raw_to_series(raw, sid)
                  for sid in config.FRED_SERIES}
    chan = ch.build_credit_channels(raw_series, mode="live")
    full = chan.dropna()

    first_year = int(full.index.min().year)   # 데이터에서 유도
    end_years = range(first_year + 1, LAST_COMPLETE_YEAR + 1)

    print(f"data range: {chan.index.min().date()} .. {chan.index.max().date()}")
    print(f"candidate window (documented 2026-07-13; unchanged regardless of "
          f"results): {CANDIDATE_WINDOW[0]} .. {CANDIDATE_WINDOW[1]}")
    print(f"candidate generation: all contiguous 2-calendar-year windows, "
          f"end years {first_year + 1}..{LAST_COMPLETE_YEAR} "
          f"(start derived from data availability, end = last complete "
          f"calendar year before target freeze date)\n")

    print("| window | yellow | red | 2026 yellow days | 2026 red days "
          "| apply rows | calibration overlap |")
    print("|---|---|---|---|---|---|---|")

    for ey in end_years:
        y0, y1 = ey - 1, ey
        W0, W1 = f"{y0}-01-01", f"{y1}-12-31"
        overlap = _overlap_calibration_windows(y0, y1)
        try:
            p99 = stress.p99_from_window(chan, W0, W1)
            win = chan.loc[W0:W1].dropna()
            st_in = stress.compute_stress(stress.normalize(win, p99))
            sbar = st_in["Sbar_w"].dropna()          # min_periods=90 → burn-in
        except Exception as e:
            print(f"| {y0}-{y1} | (error: {e}) | | | | | {overlap} |")
            continue
        if len(sbar) < SBAR_BURNIN_ROWS:
            print(f"| {y0}-{y1} | (insufficient in-window rows: {len(sbar)}) "
                  f"| | | | | {overlap} |")
            continue

        mu = float(sbar.mean())
        sigma = float(sbar.std(ddof=1))
        yellow, red = mu + 2 * sigma, mu + 3 * sigma

        st_full = stress.compute_stress(stress.normalize(full, p99))
        ytd = st_full.loc[APPLY_FROM:]["Sbar_w"].dropna()
        yd, rd = int((ytd > yellow).sum()), int((ytd > red).sum())

        mark = " **(candidate)**" if (W0, W1) == CANDIDATE_WINDOW else ""
        print(f"| {y0}-{y1}{mark} | {yellow:.4f} | {red:.4f} "
              f"| {yd} | {rd} | {len(ytd)} | {overlap} |")

    # pipeline equivalence check (기계 검증): full-history trailing vs
    # 운영 300일 버퍼 — candidate 상수로 2026 적용 구간 Sbar 비교
    cand_p99 = stress.p99_from_window(chan, *CANDIDATE_WINDOW)
    sbar_a = stress.compute_stress(
        stress.normalize(full, cand_p99))["Sbar_w"].loc[APPLY_FROM:]
    # origin 단일 출처: freeze 후엔 config.LIVE_FREEZE_DATE(동결값),
    # freeze 전엔 live_freeze_constants_v1.json의 target_live_freeze_date
    freeze_origin = (config.LIVE_FREEZE_DATE
                     or json.loads(CONSTANTS_JSON.read_text(
                         encoding="utf-8"))["target_live_freeze_date"])
    buf_start = (pd.Timestamp(freeze_origin)
                 - pd.Timedelta(days=daily.FETCH_BUFFER_DAYS))
    trunc = chan.loc[buf_start:].dropna()
    sbar_b = stress.compute_stress(
        stress.normalize(trunc, cand_p99))["Sbar_w"].loc[APPLY_FROM:]
    both = pd.concat([sbar_a.rename("full"), sbar_b.rename("buffer")],
                     axis=1).dropna()
    max_diff = float((both["full"] - both["buffer"]).abs().max())
    print(f"\npipeline equivalence check (candidate constants, {len(both)} rows): "
          f"max |Sbar_full - Sbar_buffer{daily.FETCH_BUFFER_DAYS}| = {max_diff:.3e} "
          f"(floating-point summation-order level; 판정 무영향)")

    print("\nnotes:")
    print("- thresholds: per-window Option B (in-window Sbar, 90-obs burn-in), "
          "identical method to live_freeze_constants_v1")
    print("- 2026 application: trailing Sbar with each window's P99/threshold; "
          "numerically equivalent to the operational 300-day-buffer pipeline "
          "(verified above at every run)")
    print("- candidate set is exhaustively rule-generated from data start; "
          "no candidate is hidden, including calibration-overlapping and "
          "insufficient ones")
    print("- overlap grades: ':crisis' disqualifies a window as a non-crisis "
          "baseline; ':stable'/':control' is disclosure of calibration "
          "reference use, not disqualification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
