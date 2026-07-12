# C-US Outcome Definition v1

Date: 2026-07-12
Subtrack: C-US
Status: Pre-freeze final outcome definition
Target LIVE_FREEZE_DATE: 2026-08-03

## Purpose

This document defines how future C-US red episodes will be evaluated prospectively.

Outcome definitions are fixed before official valid snapshots begin. They must not be changed after observing future market outcomes.

The purpose is to avoid post-hoc outcome selection and to make future hit, near-miss, and false-alarm classifications reproducible.

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

Primary market proxy:

- SPDR S&P Bank ETF
- Ticker: KBE

KBE is selected as the primary outcome proxy because it is a transparent, liquid, ticker-based bank-sector market proxy with easily reproducible daily price data.

## Primary Drawdown Rule

The reference price is the closing price of KBE on the red episode open date.

The minimum KBE closing price within the 6-calendar-month horizon is used to compute forward drawdown.

Drawdown = 1 - min_close_within_horizon / close_on_red_open_date

This open-date anchored rule avoids discretionary peak selection after the fact.

## Primary Outcome Classes

Collapse outcome:

- KBE drawdown >= 25 percent within the 6-month horizon

Correction outcome:

- KBE drawdown >= 12 percent and < 25 percent within the 6-month horizon

No primary outcome:

- KBE drawdown < 12 percent within the 6-month horizon

## Secondary Market Check

Secondary market check:

- KBW Nasdaq Bank Index
- Ticker: BKX

BKX may be used as a secondary market reference if an openly reproducible data source is available.

BKX is not the primary pass/fail outcome proxy unless explicitly redefined before freeze. If BKX data are not openly reproducible under the archive constraints, BKX will be omitted from formal pass/fail scoring and discussed only descriptively if appropriate.

## Secondary Banking Outcome

Secondary banking outcome: FDIC bank failure event.

A secondary banking outcome is recorded if an FDIC failed bank event occurs within the 6-month horizon and the failed institution has reported total assets of at least USD 10 billion.

FDIC asset threshold:

- USD 10 billion

Bank failure events below USD 10 billion may be recorded descriptively but are not counted as secondary prospective hits.

## Near-miss Classification

A near-miss may be recorded when market or banking stress occurs but does not meet the primary KBE drawdown threshold or the secondary FDIC threshold.

Near-miss classification is descriptive. It must not replace the primary and secondary outcome definitions.

Examples of possible near-miss evidence include:

- visible bank-sector drawdown below the 12 percent threshold
- significant funding-market disturbance
- regional bank stress that does not meet the FDIC USD 10 billion failure threshold
- official emergency liquidity intervention without primary or secondary threshold satisfaction

Near-miss classifications must be explicitly labeled as descriptive and excluded from primary pass/fail scoring.

## False Alarm Classification

A red episode is classified as a false alarm if no primary outcome, no secondary banking outcome, and no documented near-miss occurs within the 6-month horizon.

## Multiple Red Episodes

If multiple red episodes occur, each episode is evaluated by its own open date and 6-month horizon.

If horizons overlap, each episode is still reported separately. Overlapping outcomes must be disclosed rather than merged silently.

## Data Source Requirement

Outcome data sources must be documented when outcomes are evaluated.

For KBE, the required minimum fields are:

- date
- close price
- data source
- retrieval date or access method

For FDIC failed bank events, the required minimum fields are:

- failed institution name
- failure date
- reported total assets
- FDIC source reference or archived source note

## No Investment Advice

Alerts are research records. They are not trading, investment, portfolio allocation, or risk-management advice.

## Freeze Requirement

Before valid snapshots begin, the archive must record:

- final LIVE_FREEZE_DATE in config.py
- final LIVE_P99 in config.py
- final LIVE_MU_SIGMA in config.py
- this outcome definition document
- freeze release/tag
- archive citation and data access instructions

This document fixes the outcome framework for the C-US prospective archive v1.
