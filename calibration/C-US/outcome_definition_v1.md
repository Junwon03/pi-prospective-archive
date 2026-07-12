# C-US Outcome Definition v1

Date: 2026-07-12
Subtrack: C-US
Status: Pre-freeze outcome definition draft

## Purpose

This document defines how future C-US red episodes will be evaluated prospectively.

Outcome definitions must be fixed before valid snapshots begin. They must not be changed after observing future market outcomes.

## Alert Event

A red episode begins when Sbar_w first exceeds:

LIVE_MU + 3 * LIVE_SIGMA

A yellow state is defined as Sbar_w exceeding:

LIVE_MU + 2 * LIVE_SIGMA

Episode close follows the 10-trading-day cooldown rule defined in the SPEC.

The episode identity is determined by open date.

## Evaluation Horizon

The primary evaluation horizon is 6 calendar months after the red episode open date.

## Primary Outcome

Primary outcome: U.S. bank-sector equity stress.

A collapse outcome is recorded if the selected U.S. bank-sector market proxy declines by at least 25 percent within the 6-month horizon after the red episode open date.

A correction outcome is recorded if the selected U.S. bank-sector market proxy declines by at least 12 percent but less than 25 percent within the 6-month horizon.

If neither threshold is reached within 6 months, the red episode is classified as no-primary-outcome unless a secondary outcome or documented near-miss occurs.

## Drawdown Measurement Rule

The reference price is the closing price of the selected market proxy on the red episode open date.

The minimum closing price within the 6-month horizon is used to compute drawdown.

Drawdown = 1 - min_close_within_horizon / close_on_red_open_date

This rule avoids discretionary peak selection after the fact.

## Primary Market Proxy

The primary market proxy must be fixed before freeze.

Candidate proxies:

- SPDR S&P Bank ETF, KBE
- KBW Nasdaq Bank Index, BKX

For operational reproducibility, a liquid bank-sector ETF proxy may be preferred if index close data are harder to reconstruct openly.

The final proxy must be documented before freeze.

## Secondary Outcome

Secondary outcome: FDIC bank failure event above a pre-specified asset threshold.

Recommended starting threshold:

- FDIC asset threshold = USD 10 billion

Bank failure events below the threshold may be recorded descriptively but are not counted as secondary prospective hits unless the threshold is revised before freeze.

The final threshold must be documented before freeze.

## Near-miss Classification

A near-miss may be recorded when market or banking stress occurs but does not meet the primary collapse threshold or secondary FDIC threshold.

Near-miss classification is descriptive and must not replace the primary and secondary outcome definitions.

## False Alarm Classification

A red episode is classified as a false alarm if no primary outcome, secondary outcome, or documented near-miss occurs within the 6-month horizon.

## No Investment Advice

Alerts are research records. They are not trading, investment, portfolio allocation, or risk-management advice.

## Freeze Requirement

Before valid snapshots begin, this document must be updated or supplemented with:

- final primary market proxy
- final FDIC asset threshold
- final outcome data source
- final freeze date
