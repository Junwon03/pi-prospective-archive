# C-US Live Freeze Constants v1

Date: 2026-07-13
Subtrack: C-US
Status: Pre-freeze constants candidate
Target LIVE_FREEZE_DATE: 2026-08-03

## Purpose

This file records the candidate live constants for the C-US prospective archive.

These constants are computed from the pre-registered live reference window and are intended for later insertion into `src/pi_archive/config.py` after review.

## Live Reference Window

- Start: 2024-01-01
- End: 2025-12-31

## Selected Method

Option B is selected:

- P99 is computed from transformed raw channels over the full live reference window.
- LIVE_MU_SIGMA is computed from Sbar_w inside the live reference window after excluding the 90-observation warm-up period.

This avoids carrying 2023 information into the live threshold estimation.

## Candidate LIVE_P99

- rho: 0.25
- psi: 0.1999999999999993
- omega: 18958.8656

## Candidate LIVE_MU_SIGMA

- mu: 0.03397769653160021
- sigma: 0.038047420246019654

## Implied Thresholds

- yellow = mu + 2 sigma = 0.11007253702363952
- red = mu + 3 sigma = 0.14811995726965918

## Diagnostics

- code_git_commit: 88166beef5457064eecc7a5c2a87ab44edeff59c
- source_raw_file: calibration/C-US/raw_calibration.csv
- channel_rows_total: 7451
- stable_channel_rows: 426
- stable_sbar_nonnull_rows: 337
- stable_sbar_start: 2024-06-26
- stable_sbar_end: 2025-12-31
- stable_S_min: 0.0
- stable_S_max: 1.599655737313748
- stable_Sbar_min: 0.0
- stable_Sbar_max: 0.11110279413728984
- stable_yellow_days: 34
- stable_red_days: 0

## Option Comparison

### Option A: Full-history trailing Sbar

- rows: 426
- start: 2024-01-09
- end: 2025-12-31
- mu: 0.026879069791430208
- sigma: 0.036547419284784013
- yellow: 0.09997390836099823
- red: 0.13652132764578226
- yellow_days: 35
- red_days: 0

### Option B: In-window Sbar with 90-observation burn-in

- rows: 337
- start: 2024-06-26
- end: 2025-12-31
- mu: 0.03397769653160021
- sigma: 0.038047420246019654
- yellow: 0.11007253702363952
- red: 0.14811995726965918
- yellow_days: 34
- red_days: 0

## Audit Position

These values are candidate freeze constants.

They must be reviewed before being copied into `src/pi_archive/config.py`.

After freeze, LIVE_P99, LIVE_MU_SIGMA, and LIVE_FREEZE_DATE must not be changed in response to future market outcomes.
