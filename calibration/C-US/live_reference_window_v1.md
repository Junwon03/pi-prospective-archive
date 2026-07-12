# C-US Live Reference Window v1

Date: 2026-07-13
Subtrack: C-US
Status: Pre-freeze reference-window decision
Target LIVE_FREEZE_DATE: 2026-08-03

## Purpose

This document fixes the live reference window used to compute the C-US archive's frozen live normalization and alert thresholds.

The live reference window is not a crisis calibration window. It is the pre-freeze reference regime used to estimate LIVE_P99 and LIVE_MU_SIGMA before valid prospective snapshots begin.

## Selected Live Reference Window

LIVE_STABLE_WINDOW:

- Start: 2024-01-01
- End: 2025-12-31

This window will be used to compute:

- LIVE_P99
- LIVE_MU_SIGMA

The resulting constants will be frozen in config.py before valid snapshots begin.

## Rationale

The 2024-2025 window is selected for the following reasons.

First, it is fully closed before the planned live freeze date. This avoids using post-freeze or future data in the frozen live constants.

Second, it is closer to the current interest-rate and banking regime than older low-rate periods. This matters because C-US is designed to monitor contemporary U.S. credit and bank-sector stress.

Third, it avoids major crisis windows used in calibration and diagnosis, including:

- the 2008 global financial crisis
- the 2020 COVID credit shock
- the 2023 SVB/regional bank stress period

Fourth, it avoids the 2015-2016 low-volatility reference issue diagnosed during QUIET_2017 analysis. That diagnostic showed that very low control-period sigma can create overly sensitive red thresholds.

Fifth, it avoids using 2026 dry-run observations to set live thresholds. The 2026 dry-run period is reserved for operational validation before freeze, not for optimizing live constants.

Sixth, the window is not selected to be perfectly flat or artificially quiet. It may contain ordinary non-systemic market disturbances, policy-related volatility, and funding-market noise. This is intentional. The QUIET_2017 diagnosis showed that an excessively low-volatility reference regime can produce a very small sigma and an overly sensitive red threshold. The live reference window is therefore intended to include normal reference-regime disturbances while excluding major systemic crisis windows.

## Terminology

This window is called a live reference window rather than a quiet window.

It is not claimed to be a perfectly quiet market period. It is a fixed pre-freeze reference regime selected before valid archive operation begins.

## Frozen-Constant Use

After LIVE_P99 and LIVE_MU_SIGMA are computed from this window and committed, they must not be changed in response to future market outcomes.

The following are not allowed after freeze:

- moving the live reference window
- recomputing LIVE_P99 using later data
- recomputing LIVE_MU_SIGMA using later data
- changing thresholds after seeing future alerts or outcomes

## Relationship to Calibration

This live reference window does not alter:

- calibration_plan.md
- calibration v1 results
- open-date attribution v2 results
- event-specific P99 values used in calibration
- QUIET_2017 inclusion
- outcome definitions

Calibration remains a pre-freeze usability and diagnostic check. The live reference window is used only for the frozen prospective archive constants.

## Planned Freeze

Target LIVE_FREEZE_DATE:

- 2026-08-03

The actual freeze date must be recorded in config.py and in the freeze release.
