#!/usr/bin/env python3
"""C-US live freeze constants reproducibility verifier.

This script reproduces the frozen candidate constants
(LIVE_P99 and LIVE_MU_SIGMA) from calibration/C-US/raw_calibration.csv
and verifies exact equality against the recorded reference file.

Usage:
  python run_live_constants.py           # recompute + verify against reference
  python run_live_constants.py --print   # print computed values only

Method:
- Channels:
    rho   = |Δ5 DFF|
    psi   = |Δ5 (DCPF3M - DTB3)|
    omega = TOTBKCR level with as-of LOCF
- P99:
    computed from transformed channels over LIVE_STABLE_WINDOW
- Sbar:
    90-trading-observation trailing mean of S
    using in-window burn-in only
- mu/sigma:
    mean and sample standard deviation (ddof=1)
    after the 90-observation burn-in period

Freeze principle:
After freeze, this script is a verification tool only.
A mismatch between this output and frozen constants indicates
a code/data reproducibility issue. It is not a justification
for changing frozen constants after observing future outcomes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd  # noqa: E402

from pi_archive import channels as ch  # noqa: E402
from pi_archive import config, fetch_fred, stress  # noqa: E402


CAL_DIR = Path(__file__).parent / "calibration" / "C-US"
RAW_PATH = CAL_DIR / "raw_calibration.csv"
JSON_PATH = CAL_DIR / "live_freeze_constants_v1.json"


def compute() -> dict:
    raw = pd.read_csv(RAW_PATH)

    raw_series = {
        sid: fetch_fred.raw_to_series(raw, sid)
        for sid in config.FRED_SERIES
    }

    channels = ch.build_credit_channels(
        raw_series,
        mode="live",
    )

    reference = json.loads(
        JSON_PATH.read_text(encoding="utf-8")
    )

    window = tuple(reference["live_stable_window"])

    p99 = stress.p99_from_window(
        channels,
        *window,
    )

    # Confirm the computation uses the same frozen reference window
    assert list(window) == reference["live_stable_window"]

    stable = (
        channels
        .loc[window[0]:window[1]]
        .dropna()
    )

    stress_result = stress.compute_stress(
        stress.normalize(stable, p99)
    )

    sbar = stress_result["Sbar_w"].dropna()

    mu = float(sbar.mean())
    sigma = float(sbar.std(ddof=1))

    return {
        "live_stable_window": list(window),
        "live_p99": p99,
        "live_mu_sigma": {
            "mu": mu,
            "sigma": sigma,
        },
        "thresholds": {
            "yellow": mu + 2 * sigma,
            "red": mu + 3 * sigma,
        },
        "diagnostics": {
            "stable_sbar_nonnull_rows": int(len(sbar)),
            "stable_sbar_start": str(
                sbar.index.min().date()
            ),
            "stable_sbar_end": str(
                sbar.index.max().date()
            ),
        },
    }


def main() -> int:
    out = compute()

    print(json.dumps(out, indent=2))

    if "--print" in sys.argv:
        return 0

    ref = json.loads(
        JSON_PATH.read_text(encoding="utf-8")
    )

    checks = [
        (
            "p99.rho",
            out["live_p99"]["rho"],
            ref["live_p99"]["rho"],
        ),
        (
            "p99.psi",
            out["live_p99"]["psi"],
            ref["live_p99"]["psi"],
        ),
        (
            "p99.omega",
            out["live_p99"]["omega"],
            ref["live_p99"]["omega"],
        ),
        (
            "mu",
            out["live_mu_sigma"]["mu"],
            ref["live_mu_sigma"]["mu"],
        ),
        (
            "sigma",
            out["live_mu_sigma"]["sigma"],
            ref["live_mu_sigma"]["sigma"],
        ),
    ]

    ok = True

    for name, computed, reference in checks:
        match = computed == reference
        ok &= match

        print(
            f"{'PASS' if match else 'FAIL'} "
            f"{name}: "
            f"computed={computed!r} "
            f"reference={reference!r}"
        )

    print(
        "overall:",
        "PASS (bit-exact)" if ok else "FAIL"
    )

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
