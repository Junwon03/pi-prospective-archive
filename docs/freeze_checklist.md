# C-US Freeze Checklist

Project: pi-prospective-archive
Subtrack: C-US
Target LIVE_FREEZE_DATE: 2026-08-03
Status: Pre-freeze checklist

## Purpose

This checklist defines the required steps before the C-US archive can switch from dry_run snapshots to valid prospective snapshots.

The freeze must not be performed until all required items are complete.

## 1. Repository State

- [ ] main branch is up to date
- [ ] working tree is clean
- [ ] no uncommitted files
- [ ] no accidental local artifacts
- [ ] no __pycache__ committed
- [ ] no .DS_Store committed
- [ ] no force-push history rewrite
- [ ] python -m pytest -q passes

Expected test result:

43 passed

## 2. CI and Automation

- [ ] GitHub Actions CI is green
- [ ] collect-c-us workflow is green
- [ ] healthcheck workflow is green
- [ ] latest dry_run snapshot is present
- [ ] latest dry_run snapshot has manifest.sha256
- [ ] latest dry_run snapshot passes healthcheck

## 3. Required Protocol Documents

- [ ] SPEC-1.0_common_v4.md
- [ ] SPEC-1.0-C-US_v5.md
- [ ] calibration/C-US/freeze_protocol_v1.md
- [ ] calibration/C-US/dry_run_stability_note_v1.md
- [ ] calibration/C-US/outcome_definition_v1.md
- [ ] calibration/C-US/live_reference_window_v1.md
- [ ] calibration/C-US/live_freeze_constants_v1.json
- [ ] calibration/C-US/live_freeze_constants_v1.md
- [ ] docs/data_dictionary.md
- [ ] docs/versioning_policy.md
- [ ] docs/freeze_checklist.md
- [ ] CHANGELOG.md
- [ ] CITATION.cff
- [ ] LICENSE
- [ ] LICENSE-DATA.md

## 4. Calibration Record

- [ ] calibration/C-US/calibration_plan.md exists
- [ ] calibration/C-US/failure_analysis_v1.md exists
- [ ] calibration/C-US/freeze_decision_note_v1.md exists
- [ ] calibration/C-US/rerun_note_after_locf_patch.md exists
- [ ] calibration/C-US/quiet_2017_episode_diagnosis_v1.md exists
- [ ] calibration/C-US/calibration_scoring_addendum_v1.md exists
- [ ] calibration/C-US/open_date_v2_results_note.md exists
- [ ] calibration/C-US/live/calibration_results.json exists
- [ ] calibration/C-US/reproduction/reproduction_results.json exists
- [ ] calibration/C-US/open_date_v2/live/calibration_results.json exists
- [ ] calibration/C-US/open_date_v2/reproduction/reproduction_results.json exists

Expected calibration status:

- [ ] v1 window-sliced result preserved
- [ ] v1 overall_pass = false
- [ ] QUIET_2017 v1 failure preserved
- [ ] v2 open-date attribution result preserved
- [ ] v2 overall_pass = true
- [ ] inherited active QUIET_2017 episode disclosed

## 5. Outcome Definition

Required final outcome settings:

- [ ] Primary market proxy = KBE
- [ ] Secondary market check = BKX if openly reproducible
- [ ] Secondary banking outcome = FDIC failed bank event
- [ ] FDIC asset threshold = USD 10B
- [ ] Outcome horizon = 6 calendar months after red episode open date
- [ ] Drawdown rule = 1 - min_close_within_horizon / close_on_red_open_date
- [ ] Correction = KBE drawdown >= 12% and < 25%
- [ ] Collapse = KBE drawdown >= 25%
- [ ] Alerts are research records, not investment advice

## 6. Live Constants Candidate

Expected values from live_freeze_constants_v1:

LIVE_STABLE_WINDOW:

- [ ] 2024-01-01 to 2025-12-31

LIVE_P99:

- [ ] rho = 0.25
- [ ] psi = 0.1999999999999993
- [ ] omega = 18958.8656

LIVE_MU_SIGMA:

- [ ] mu = 0.03397769653160021
- [ ] sigma = 0.038047420246019654

Implied thresholds:

- [ ] yellow = 0.11007253702363952
- [ ] red = 0.14811995726965918

Selected method:

- [ ] Option B: in-window Sbar with 90-observation burn-in

## 7. Config Freeze Patch

Before freeze, src/pi_archive/config.py must be updated with:

- [ ] LIVE_STABLE_WINDOW = ("2024-01-01", "2025-12-31")
- [ ] LIVE_P99 with reviewed values
- [ ] LIVE_MU_SIGMA with reviewed values
- [ ] LIVE_FREEZE_DATE = "2026-08-03"

After patch:

- [ ] python -m pytest -q passes
- [ ] config constants match live_freeze_constants_v1
- [ ] official snapshot tests still pass

## 8. First Valid Snapshot

After freeze:

- [ ] collect-c-us produces snapshot_status = valid
- [ ] meta.json mu_sigma_used is not null
- [ ] meta.json p99_used equals LIVE_P99
- [ ] meta.json freeze_date equals LIVE_FREEZE_DATE
- [ ] Pi_since_freeze begins at LIVE_FREEZE_DATE
- [ ] healthcheck passes

## 9. Release and DOI

Freeze release requirements:

- [ ] create git tag: c-us-freeze-v1.0
- [ ] create GitHub release: C-US Prospective Archive Freeze v1.0
- [ ] release notes summarize frozen rule and valid start
- [ ] connect or archive release with Zenodo
- [ ] record DOI after Zenodo release
- [ ] update CITATION.cff with version and DOI if available

## 10. Prohibited After Freeze

After v1.0 freeze, do not:

- [ ] change LIVE_P99 in response to future outcomes
- [ ] change LIVE_MU_SIGMA in response to future outcomes
- [ ] change LIVE_FREEZE_DATE
- [ ] move LIVE_STABLE_WINDOW
- [ ] remove QUIET_2017
- [ ] delete v1 failure records
- [ ] delete inherited active episode records
- [ ] relax thresholds
- [ ] change outcome definitions
- [ ] overwrite valid snapshots
- [ ] force-push public history

## 11. Allowed After Freeze

Allowed without changing frozen rule:

- [ ] README improvements
- [ ] documentation clarifications
- [ ] citation metadata updates
- [ ] healthcheck improvements that do not alter computed values
- [ ] packaging or release improvements
- [ ] correction snapshots with documented correction_reason

If computed-value interpretation changes, create a new SPEC version.

## Freeze Approval

Freeze should proceed only after all required items above are checked.

Final freeze commit message recommendation:

freeze C-US live constants v1.0

Recommended release tag:

c-us-freeze-v1.0
