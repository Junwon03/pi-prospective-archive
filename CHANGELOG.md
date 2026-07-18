# Changelog

All notable changes to the C-US prospective archive are documented here.

This changelog is an audit-oriented summary. Full details are preserved in the repository history, calibration notes, SPEC files, snapshot metadata, and documentation files.

## [Pre-freeze] 2026-07-13

### Added

- Added English README describing the C-US pre-freeze prospective archive.
- Added data dictionary:
  - docs/data_dictionary.md
- Added versioning policy:
  - docs/versioning_policy.md
- Added citation metadata:
  - CITATION.cff
- Added code license:
  - LICENSE
- Added data/documentation/snapshot license:
  - LICENSE-DATA.md
- Added live reference window decision:
  - calibration/C-US/live_reference_window_v1.md
- Added live freeze constants candidate:
  - calibration/C-US/live_freeze_constants_v1.json
  - calibration/C-US/live_freeze_constants_v1.md
- Centralized FETCH_BUFFER_DAYS in `src/pi_archive/config.py` as a
  single-source ingestion parameter while preserving existing behavior.
- Added `PROSPECTIVE_TARGET_FREEZE_DATE` as planning/documentation metadata only;
  runtime prospective anchoring remains controlled by `LIVE_FREEZE_DATE`.

### Fixed

- Corrected trailing-edge LOCF alignment for live snapshots.
- Added regression test for delayed weekly series carrying forward to the live grid end within the fill limit.
- Verified post-fix dry-run snapshots advanced alert as-of date to the latest available trading day instead of stopping at the latest TOTBKCR print.

### Calibration

- Preserved v1 window-sliced calibration result:
  - positive_pass = 3
  - negative_zero_red = false
  - overall_pass = false
- Diagnosed QUIET_2017 boundary attribution:
  - actual red episode open date = 2016-12-16
  - actual close date = 2017-08-24
  - newly opened red episodes inside 2017 = 0
  - inherited active red episodes during 2017 = 1
- Added open-date attribution scoring addendum.
- Implemented v2 open-date attribution calibration harness.
- Preserved v2 result separately:
  - positive_pass = 3
  - negative_zero_red = true
  - overall_pass = true

### Outcome Definition

- Finalized primary outcome proxy:
  - KBE
- Finalized secondary market check:
  - BKX, if openly reproducible
- Finalized secondary banking outcome:
  - FDIC failed bank event with reported assets >= USD 10B
- Finalized target live freeze date:
  - 2026-08-03

### Live Constants Candidate

- Selected LIVE_STABLE_WINDOW:
  - 2024-01-01 to 2025-12-31
- Selected threshold estimation method:
  - Option B: in-window Sbar with 90-observation burn-in
- Candidate LIVE_P99:
  - rho = 0.25
  - psi = 0.1999999999999993
  - omega = 18958.8656
- Candidate LIVE_MU_SIGMA:
  - mu = 0.03397769653160021
  - sigma = 0.038047420246019654
- Implied thresholds:
  - yellow = 0.11007253702363952
  - red = 0.14811995726965918

### Status

- Archive status remains pre-freeze.
- Valid prospective snapshots have not started.
- Current snapshots are dry_run records only.
- Candidate constants are not official until copied into src/pi_archive/config.py and committed as the freeze commit.

## [Dry-run] 2026-07-05 to 2026-07-12

### Added

- Started C-US dry-run snapshot collection.
- Added manifest-based snapshot integrity checks.
- Added healthcheck workflow.
- Added full dependency lock.
- Added .gitignore for local artifacts.

### Validation

- Confirmed raw.csv, computed.csv, alert.json, meta.json, and manifest.sha256 generation.
- Confirmed manifest hash verification.
- Confirmed S = rho_hat * psi_hat * omega_hat identity within floating-point tolerance.
- Confirmed dry_run alert_level remains null before LIVE_MU_SIGMA freeze.

## [Calibration v1] 2026-07

### Added

- Added calibration plan:
  - calibration/C-US/calibration_plan.md
- Recorded v1 calibration output.
- Added failure analysis:
  - calibration/C-US/failure_analysis_v1.md
- Added freeze decision note:
  - calibration/C-US/freeze_decision_note_v1.md

### Result

- GFC_2008 passed.
- CREDIT_SHOCK_2020 passed.
- SVB_2023 passed.
- REPO_2019 hard negative passed.
- QUIET_2017 failed under the original window-sliced harness.
- v1 overall_pass = false.

### Audit Position

- The v1 failure is preserved.
- QUIET_2017 was not removed.
- The threshold was not relaxed.
- The calibration window was not moved.

## [Initial Structure] 2026-07

### Added

- Added SPEC files:
  - SPEC-1.0_common_v4.md
  - SPEC-1.0-C-US_v5.md
- Added source modules under src/pi_archive.
- Added tests.
- Added GitHub Actions workflows.
- Added run scripts:
  - run_snapshot.py
  - run_calibration.py
  - run_health_check.py
