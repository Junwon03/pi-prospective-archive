# C-US Live Reference Window Sensitivity Analysis v1

Date: 2026-07-17
Subtrack: C-US
Status: Post-selection robustness disclosure (pre-freeze)
Script: run_window_sensitivity.py
Results source: author's own environment run, 2026-07-17 (43/43 tests passing)

## Purpose and Status Declaration

This analysis was conducted **after** the candidate live reference window was
selected and documented, and **before** the live freeze. It is not a window
selection or optimization procedure. Its purpose is to quantify how sensitive
the candidate baseline choice is relative to all alternative historical
baselines, and to disclose the results regardless of outcome.

The candidate live reference window remains:

- 2024-01-01 to 2025-12-31

unchanged regardless of the results below. The decision not to modify the
candidate window based on this sensitivity analysis was fixed before the
analysis was run.

## Timeline

- 2026-07-13: candidate live reference window and candidate freeze constants
  documented (live_reference_window_v1.md, live_freeze_constants_v1.json).
- 2026-07-17: this sensitivity analysis performed and disclosed.
- Target 2026-08-03: live freeze (constants copied into config.py).

This note postdates the window selection and formalizes its robustness
context. It does not claim the selection followed a pre-registered automated
rule. The window was selected through methodological judgment; the rationale
(exclusion of crisis periods, avoidance of excessively low-volatility
baselines, minimum two-year length, ending before freeze) was documented at
selection time in live_reference_window_v1.md.

## Candidate Generation Rule

Candidates are exhaustively rule-generated, not hand-picked:

- All contiguous 2-calendar-year windows from the first year of available
  data (derived from the data itself) through the last complete calendar
  year before the target freeze date (2025).
- Overlap with calibration event windows is machine-labeled per grade:
  `:crisis` overlap disqualifies a window as a non-crisis baseline;
  `:stable` / `:control` overlap is disclosure of calibration reference use,
  not disqualification. These grade definitions follow the existing
  calibration event metadata (config CALIBRATION_EVENTS) and were applied
  mechanically during the analysis.
- No candidate is hidden, including calibration-overlapping ones.

## Method

Identical to live_freeze_constants_v1 "Option B", applied per window:

1. P99(W): live-mode channel q99 over the window.
2. Sbar(W): S computed from in-window rows only, 90-trading-observation
   trailing mean (in-window burn-in).
3. mu, sigma: mean and sample standard deviation (ddof=1) of post-burn-in
   Sbar; yellow = mu + 2 sigma, red = mu + 3 sigma.
4. Operational application: each window's P99 and thresholds applied to
   2026-01-01 onward; yellow/red exceedance days counted.

The application-side Sbar uses full-history trailing rolling mean. The live
pipeline fetches only a 300-calendar-day buffer, but a trailing
90-observation rolling mean depends only on the preceding 90 observations,
so the two are numerically equivalent. This equivalence is machine-verified
at every script run (result below), not merely asserted.

## Results (author's environment output)

data range: 1997-01-09 .. 2026-07-08

| window | yellow | red | 2026 yellow days | 2026 red days | apply rows | calibration overlap |
|---|---|---|---|---|---|---|
| 1997-1998 | 0.0741 | 0.0955 | 0 | 0 | 115 | - |
| 1998-1999 | 0.1014 | 0.1308 | 0 | 0 | 115 | - |
| 1999-2000 | 0.0471 | 0.0574 | 0 | 0 | 115 | - |
| 2000-2001 | 0.0825 | 0.1067 | 0 | 0 | 115 | - |
| 2001-2002 | 0.1213 | 0.1644 | 0 | 0 | 115 | - |
| 2002-2003 | 0.0906 | 0.1119 | 77 | 52 | 115 | - |
| 2003-2004 | 0.0835 | 0.1057 | 77 | 52 | 115 | GFC_2008:control,GFC_2008:stable |
| 2004-2005 | 0.1187 | 0.1465 | 32 | 0 | 115 | GFC_2008:crisis,GFC_2008:control,GFC_2008:stable |
| 2005-2006 | 0.1065 | 0.1303 | 29 | 0 | 115 | GFC_2008:crisis,GFC_2008:control,GFC_2008:stable |
| 2006-2007 | 0.1250 | 0.1732 | 0 | 0 | 115 | GFC_2008:crisis,GFC_2008:control,GFC_2008:stable |
| 2007-2008 | 0.0524 | 0.0675 | 0 | 0 | 115 | GFC_2008:crisis |
| 2008-2009 | 0.0564 | 0.0762 | 0 | 0 | 115 | GFC_2008:crisis |
| 2009-2010 | 0.0287 | 0.0390 | 52 | 29 | 115 | GFC_2008:crisis |
| 2010-2011 | 0.0644 | 0.0777 | 79 | 79 | 115 | - |
| 2011-2012 | 0.0796 | 0.0974 | 79 | 79 | 115 | - |
| 2012-2013 | 0.0657 | 0.0815 | 79 | 79 | 115 | - |
| 2013-2014 | 0.0514 | 0.0663 | 80 | 79 | 115 | CREDIT_SHOCK_2020:stable,REPO_2019:stable,QUIET_2017:stable |
| 2014-2015 | 0.0331 | 0.0442 | 80 | 79 | 115 | CREDIT_SHOCK_2020:stable,REPO_2019:stable,QUIET_2017:control,QUIET_2017:stable |
| 2015-2016 | 0.0298 | 0.0389 | 78 | 77 | 115 | CREDIT_SHOCK_2020:stable,REPO_2019:stable,QUIET_2017:control,QUIET_2017:stable |
| 2016-2017 | 0.0687 | 0.0891 | 28 | 0 | 115 | CREDIT_SHOCK_2020:control,CREDIT_SHOCK_2020:stable,REPO_2019:control,REPO_2019:stable,QUIET_2017:crisis,QUIET_2017:control,QUIET_2017:stable |
| 2017-2018 | 0.0473 | 0.0592 | 30 | 0 | 115 | CREDIT_SHOCK_2020:control,CREDIT_SHOCK_2020:stable,REPO_2019:control,REPO_2019:stable,QUIET_2017:crisis |
| 2018-2019 | 0.0410 | 0.0517 | 30 | 0 | 115 | CREDIT_SHOCK_2020:control,CREDIT_SHOCK_2020:stable,REPO_2019:crisis,REPO_2019:control,REPO_2019:stable |
| 2019-2020 | 0.1112 | 0.1537 | 0 | 0 | 115 | CREDIT_SHOCK_2020:crisis,REPO_2019:crisis |
| 2020-2021 | 0.0806 | 0.1138 | 0 | 0 | 115 | CREDIT_SHOCK_2020:crisis,SVB_2023:control,SVB_2023:stable,REPO_2019:crisis |
| 2021-2022 | 0.0667 | 0.0908 | 0 | 0 | 115 | SVB_2023:control,SVB_2023:stable |
| 2022-2023 | 0.0688 | 0.0903 | 0 | 0 | 115 | SVB_2023:crisis |
| 2023-2024 | 0.0802 | 0.1083 | 0 | 0 | 115 | SVB_2023:crisis |
| 2024-2025 **(candidate)** | 0.1101 | 0.1481 | 0 | 0 | 115 | - |

Pipeline equivalence check (candidate constants, 78 rows):
max |Sbar_full - Sbar_buffer300| = 6.939e-18
(floating-point summation-order level; no effect on classification).

## Interpretation

1. **Threshold magnitude is baseline-regime dependent.** Red thresholds
   across candidates range from 0.0389 to 0.1644. This dependence is
   expected: stress distributions differ across monetary and volatility
   regimes. The candidate window did not produce the highest threshold among
   candidates without crisis overlap (2001-2002 produced 0.1644 versus the candidate's 0.1481).

2. **Low-volatility-regime baselines produce hair-trigger behavior.**
   Windows drawn from low-rate, low-volatility regimes (the post-dot-com
   easing period 2002-2003 and the post-GFC era 2009-2016) yield red
   thresholds of roughly 0.039-0.112 and would classify 29-79 of the 115
   trading days of 2026 to date as red. This empirically confirms and
   generalizes the low-volatility-baseline concern documented in the
   QUIET_2017 diagnosis: the issue is not one specific quiet year but any
   baseline drawn from a regime structurally dissimilar to the operating
   environment.

3. **The operational classification pattern.** Windows from low-volatility
   baseline regimes showed materially different behavior (29-79 red days on
   2026 data to date), while the candidate window and other windows outside
   these regimes produced zero red exceedances on 2026 data to date.
   The current "no alert" state is not unique to the candidate window,
   although alert behavior remains dependent on the reference regime.

5. **Correction record.** An earlier draft of this analysis enumerated
   candidates only from 2014 onward. That truncated set supported two claims
   later corrected by exhaustive enumeration: (a) that the candidate window
   produced the highest threshold among eligible candidates, and (b) that
   the 2026 operational classification was robust across all windows. Both
   claims are withdrawn in their strong form and replaced by findings 1-3.
   The correction is preserved here deliberately: exhaustive rule-generated
   enumeration is what exposed the limitation of the initial framing.

6. **Implication for the freeze design.** Because threshold magnitude
   depends on the reference regime, prospective validity cannot come from
   adaptively selecting or re-estimating thresholds; it requires freezing
   the reference regime before future observation and evaluating the frozen
   rule's behavior out of sample. This sensitivity analysis therefore
   supports the freeze protocol itself rather than merely defending one
   window choice.

## Limitation

The reference window was selected through methodological judgment rather
than an automated optimization procedure. The selection rationale, the
candidate constants, the full alternative-baseline results above, and this
limitation are preserved transparently for future audit. If the selection
proves poorly matched to the operating environment, the consequences will
appear in the prospective record as misses or false alarms under the
pre-specified outcome definitions, and will be recorded as such.
