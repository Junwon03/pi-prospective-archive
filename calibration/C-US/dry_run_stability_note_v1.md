# C-US Dry-run Stability Note v1

Date: 2026-07-12
Subtrack: C-US
Status: Pre-freeze dry-run record

## Purpose

This note records what was learned during the C-US dry-run period before official freeze.

The dry-run phase is not prospective evidence. Its purpose is to test operations, data ingestion, snapshot generation, manifest validation, and live as-of computation before valid snapshots begin.

## Dry-run Components Tested

The dry-run phase tested:

- GitHub Actions scheduled collection
- FRED data ingestion
- snapshot writing
- raw.csv, computed.csv, alert.json, meta.json generation
- manifest.sha256 hash validation
- healthcheck behavior
- requirements.lock installation on GitHub runner
- dry_run snapshot status
- null alert_level before LIVE_MU_SIGMA is frozen

## Calibration and Scoring Context

Before freeze, the following were completed:

- calibration_plan.md was pre-registered
- calibration v1 results were saved
- QUIET_2017 v1 failure was preserved
- QUIET_2017 episode attribution was diagnosed
- calibration scoring addendum was written
- open-date attribution v2 results were generated
- v1 and v2 results were both retained

## Detected Implementation Issue

During dry-run, a trailing-edge LOCF issue was detected.

Weekly or delayed series such as TOTBKCR did not carry forward to the end of the daily live grid when the latest weekly observation was older than the latest daily observations.

This caused computed rows after the latest TOTBKCR print to be marked unavailable even when they were still within the 14 calendar day fill limit.

## Correction

The implementation was corrected by extending LOCF alignment to the live grid end while preserving the calendar-day fill limit.

This correction uses only past observed values and therefore preserves the as-of and no-lookahead rule.

## Post-correction Verification

After the correction:

- pytest passed with 41 tests, later 43 tests after calibration scoring tests
- collect-c-us completed successfully
- healthcheck completed successfully
- alert asof_date advanced to the latest available trading day rather than stopping at the latest TOTBKCR print
- S(t) continued to match rho_hat * psi_hat * omega_hat within floating-point tolerance
- manifest hashes matched snapshot files

## Calibration Rerun After LOCF Fix

Calibration was rerun after the LOCF correction.

The top-level v1 verdict remained unchanged:

positive_pass = 3
positive_total = 3
positive_criterion = true
negative_zero_red = false
nonredundancy_ok = true
overall_pass = false

Open-date attribution v2 produced:

positive_pass = 3
positive_total = 3
positive_criterion = true
negative_zero_red = true
nonredundancy_ok = true
overall_pass = true

## Interpretation

The dry-run phase performed its intended role.

It exposed an implementation-level availability issue before freeze, allowed correction, preserved the audit trail, and confirmed that the correction did not change the calibration verdict.

The archive is now ready to proceed toward live constants and freeze preparation.
