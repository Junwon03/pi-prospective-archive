#!/usr/bin/env python3
"""C-US calibration 실행기.

사용:
  export FRED_API_KEY=...            # https://fred.stlouisfed.org/docs/api/api_key.html
  python run_calibration.py fetch    # FRED에서 raw 내려받아 calibration/C-US/raw_calibration.csv 저장
  python run_calibration.py run [--strict]  # 등록된(window 고정) 사건 전부 실행 → results JSON 저장

원칙 (SPEC §5 / common C5):
- window 미등록 사건은 실행 거부됨 → calibration_plan.md commit 후 config.py에 반영할 것
- 결과는 pass/fail 요약뿐 아니라 raw 지표 전량을 저장 (전면 공개)
- 이 스크립트는 calibration 전용 — live snapshot 파이프라인은 별도 (동일 core 모듈 사용)

출력:
- calibration/C-US/live/calibration_results.json
  기존 v1 window-sliced harness 결과. v1 실패 이력을 보존하기 위해 계속 저장한다.
- calibration/C-US/reproduction/reproduction_results.json
  foundation reproduction only.
- calibration/C-US/open_date_v2/live/calibration_results.json
  open-date attribution scoring addendum v1에 따른 v2 결과.
- calibration/C-US/open_date_v2/reproduction/reproduction_results.json
  reproduction mode의 v2 full-disclosure 결과.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd  # noqa: E402

from pi_archive import calibration, config, fetch_fred  # noqa: E402

CAL_DIR = Path(__file__).parent / "calibration" / "C-US"
RAW_PATH = CAL_DIR / "raw_calibration.csv"


def cmd_fetch() -> None:
    CAL_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    series_ids = (list(config.FRED_SERIES) + list(config.SENSITIVITY_SERIES)
                  + list(config.REPRO_ONLY_SERIES))
    # REPRO_ONLY(TEDRATE): historical_repro + §5.3 정합성 기록용 (단종, 과거값은 제공됨)
    for sid in series_ids:
        print(f"fetching {sid} ...")
        frames.append(fetch_fred.fetch_series(sid, observation_start="1997-01-01"))
    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(RAW_PATH, index=False)
    print(f"saved {len(raw)} rows -> {RAW_PATH}")


def _collect_results(raw: dict, scoring_method: str) -> list[dict]:
    results = []
    for name, ev in config.CALIBRATION_EVENTS.items():
        if ev["stable"] is None:
            print(f"[skip] {name}: window 미등록 — calibration_plan.md 사전등록 후 실행")
            continue
        for mode in ev["modes"]:
            print(f"[run ] {name} ({mode}, {scoring_method}) ...")
            try:
                results.append(
                    calibration.run_event(
                        raw,
                        name,
                        mode=mode,
                        scoring_method=scoring_method,
                    )
                )
            except Exception as e:  # 실패도 기록 (전면 공개)
                results.append({
                    "event": name,
                    "mode": mode,
                    "kind": ev["kind"],
                    "scoring_method": scoring_method,
                    "error": repr(e),
                })
    return results


def _write_outputs(results: list[dict], base_dir: Path) -> dict:
    live_results = [r for r in results if r.get("mode") == "live" and "error" not in r]
    summary = calibration.passfail(live_results) if live_results else {"note": "no live results"}

    live_dir, repro_dir = base_dir / "live", base_dir / "reproduction"
    live_dir.mkdir(parents=True, exist_ok=True)
    repro_dir.mkdir(parents=True, exist_ok=True)

    live_out = {
        "results_full_disclosure": [r for r in results if r.get("mode") == "live"],
        "passfail_summary": summary,
    }
    repro_out = {
        "results_full_disclosure": [r for r in results if r.get("mode") == "historical_repro"],
        "note": (
            "foundation reproduction only — NOT the live frozen specification; "
            "excluded from pass/fail (SPEC §1.2)"
        ),
    }

    (live_dir / "calibration_results.json").write_text(
        json.dumps(live_out, indent=2, default=str), encoding="utf-8")
    (repro_dir / "reproduction_results.json").write_text(
        json.dumps(repro_out, indent=2, default=str), encoding="utf-8")

    print(f"\nsaved -> {live_dir}/calibration_results.json")
    print(f"saved -> {repro_dir}/reproduction_results.json")
    print(json.dumps(summary, indent=2))
    return summary


def cmd_run(strict: bool = False) -> None:
    if strict:
        calibration.assert_all_windows_registered()  # freeze-prep: TODO 있으면 실패
    if not RAW_PATH.exists():
        sys.exit(f"raw 없음: 먼저 `python run_calibration.py fetch` 실행 ({RAW_PATH})")
    raw_long = fetch_fred.load_raw_csv(str(RAW_PATH))
    all_ids = (list(config.FRED_SERIES) + list(config.SENSITIVITY_SERIES)
               + list(config.REPRO_ONLY_SERIES))
    raw = {sid: fetch_fred.raw_to_series(raw_long, sid)
           for sid in all_ids
           if sid in set(raw_long["series_id"])}

    print("\n=== v1: window-sliced harness (preserved full disclosure) ===")
    v1_results = _collect_results(raw, calibration.SCORING_WINDOW_SLICED_V1)
    v1_summary = _write_outputs(v1_results, CAL_DIR)

    print("\n=== v2: open-date attribution harness ===")
    v2_results = _collect_results(raw, calibration.SCORING_OPEN_DATE_V2)
    v2_summary = _write_outputs(v2_results, CAL_DIR / "open_date_v2")

    print("\n=== summary comparison ===")
    print(json.dumps({
        "v1_window_sliced": v1_summary,
        "v2_open_date_attribution": v2_summary,
    }, indent=2))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in ("fetch", "run"):
        sys.exit(__doc__)
    if args[0] == "fetch":
        cmd_fetch()
    else:
        cmd_run(strict="--strict" in args)
