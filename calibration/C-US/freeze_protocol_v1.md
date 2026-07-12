# C-US Freeze Protocol v1

Date: 2026-07-12
Subtrack: C-US
Status: Pre-freeze protocol

## Purpose

This document defines the freeze protocol for the C-US prospective archive.

The purpose of the freeze is to begin a timestamped, append-only, prospective record of C-US financial stress signals under a fixed diagnostic rule.

After freeze, valid snapshots are research records. They are not investment advice.

## Freeze Scope

The following definitions are frozen at the start of the valid archive.

### Channels

- rho = absolute 5-trading-observation change in DFF
- psi = absolute 5-trading-observation change in DCPF3M minus DTB3
- omega = TOTBKCR level, aligned by as-of LOCF

### Fill Rules

- DFF, DCPF3M, DTB3, DGS3MO, TEDRATE: LOCF up to 5 calendar days
- TOTBKCR: LOCF up to 14 calendar days

### Stress Construction

- S(t) = rho_hat(t) * psi_hat(t) * omega_hat(t)
- Sbar_w = rolling mean of S over 90 trading observations
- Pi_since_freeze = cumulative S from LIVE_FREEZE_DATE onward

### Alert Rule

- yellow = LIVE_MU + 2 * LIVE_SIGMA
- red = LIVE_MU + 3 * LIVE_SIGMA
- cooldown = 10 trading days
- horizon = 6 calendar months after red episode open date

### Frozen Live Constants

The following constants must be fixed before valid snapshots begin:

- LIVE_STABLE_WINDOW
- LIVE_P99
- LIVE_MU_SIGMA
- LIVE_FREEZE_DATE

## No Post-hoc Tuning Rule

After LIVE_* constants are committed, the following are not allowed in response to future market outcomes:

- changing channel definitions
- changing fill limits
- moving calibration windows
- removing QUIET_2017
- relaxing alert thresholds
- changing LIVE_P99
- changing LIVE_MU_SIGMA
- changing LIVE_FREEZE_DATE
- changing outcome thresholds after seeing future events

## Preserved Calibration Record

The pre-freeze calibration record includes both:

- v1 window-sliced harness result, preserved as full disclosure
- v2 open-date attribution result, following the calibration scoring addendum

The v1 result is not deleted. The v2 result clarifies episode attribution according to open-date episode semantics.

## Corrections

Implementation or data-ingestion errors discovered after freeze must not overwrite past valid snapshots.

Corrections must be documented through new commits and, where needed, correction snapshots. Any correction must explain whether it changes computed-value interpretation. If it changes frozen definitions or alert interpretation, a new SPEC version is required.

## Dry-run Record

The dry-run phase detected and corrected a trailing-edge LOCF implementation issue before freeze.

The correction implemented the existing as-of LOCF rule and did not change calibration windows, thresholds, channel definitions, or the calibration verdict.

## Prospective Interpretation

Future red and yellow states are research records.

They will be evaluated against the pre-specified outcome definitions and horizon. They are not trading, investment, or risk-management recommendations.
