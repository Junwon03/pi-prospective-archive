# C-US Calibration Plan v1

> Target path in repository: `calibration/C-US/calibration_plan.md`
> Subtrack: `C-US`
> Applies to: `SPEC-1.0_common v4` and `SPEC-1.0-C-US v5`
> Status: **PRE-REGISTRATION PLAN — becomes active only when committed before any strict calibration run**
> Prepared date: 2026-07-06

---

## 0. Purpose

This file pre-registers the C-US calibration windows before running the C-US calibration pipeline.

Calibration is a **usability check**, not retrospective performance evidence. Its role is limited to checking whether the frozen C-US structure is available, non-redundant, directionally consistent with known positive stress episodes, and quiet on pre-registered negative controls. Passing calibration must not be described as prospective evidence.

Prospective evidence begins only after the C-US SPEC is frozen and official `valid` snapshots begin.

---

## 1. Non-negotiable pre-registration rule

Window selection in this file uses public historical chronology and pre-existing SPEC rules only.

The following were **not** used to choose or adjust the windows:

- `Sep(Pi)` results
- `Sep(Sbar)` results
- `S`, `Sbar_w`, or `Pi` plots
- red/yellow alert counts
- transformed channel outputs used for calibration scoring
- failed or successful calibration outputs from trial runs

Raw data availability checks are allowed only to confirm that required FRED series exist and cover the proposed dates. Raw or transformed data must not be used to move window boundaries before this plan is committed.

After this plan is committed, windows must not be modified in place. If a revision is necessary, create a new plan file, for example `calibration_plan_v2.md`, with a written reason, and keep this v1 file intact.

---

## 2. Frozen C-US live specification used in calibration

Live-mode calibration uses the same causal rules intended for the live archive:

| Channel | Definition | Live transform | Source |
|---|---|---|---|
| rho | `DFF` | `abs(delta over 5 trading observations)` | FRED |
| psi | `DCPF3M - DTB3` | `abs(delta over 5 trading observations)` | FRED |
| omega | `TOTBKCR` | level, as-of LOCF only | FRED |

Live alignment rules:

- `DFF`, `DCPF3M`, and `DTB3`: LOCF allowed up to 5 calendar days.
- `TOTBKCR`: LOCF allowed up to 14 calendar days.
- No future observation may be used.
- No linear interpolation is allowed in live-mode calibration.
- Historical TEDRATE reproduction, if run, must be labeled separately and must not be mixed with live-mode pass/fail.

---

## 3. Window definitions and the two-tier negative-control design

For each calibration event:

- `stable_window`: used to compute event-specific P99 normalization constants.
- `control_window`: used as the quiet comparison baseline for separation calculations.
- `crisis_window` or `evaluation_window`: used as the positive or negative evaluation window.

For negative controls, the evaluation window must not be identical to the stable window. Otherwise, absence of red alerts would be partly tautological.

**Two-tier negative-control design.** The two negative controls are deliberately split by role:

| Event | Role | What it tests |
|---|---|---|
| `QUIET_2017` | easy test | basic specificity — silence when nothing happens |
| `REPO_2019` | hard test | discrimination — withholding red on a real but sub-systemic stress |

Passing only the quiet control would demonstrate insensitivity, not discrimination. The framework's core claim — that it separates localized stress from systemic co-activation — is tested by the repo near-miss, not by the quiet year. Both must pass.

---

## 4. Pre-registered event table

### 4.1 Positive event: GFC_2008

| Field | Value |
|---|---|
| event_id | `GFC_2008` |
| label | positive |
| mode | historical reproduction + live-rule calibration |
| stable_window | `2004-01-01` to `2006-12-31` |
| control_window | `2004-01-09` to `2006-06-30` |
| crisis_window | `2005-01-05` to `2009-03-31` |
| status | inherited and fixed |

Rationale:

- This window is inherited from the foundation study's pre-existing 2008 setup, already fixed in the project record before this C-US calibration plan.
- It is not re-selected in this C-US calibration plan.
- The inherited historical reproduction run may use the original reproduction procedure, but the live-rule calibration run must use the causal C-US live rules end-to-end.

---

### 4.2 Positive event: CREDIT_SHOCK_2020

| Field | Value |
|---|---|
| event_id | `CREDIT_SHOCK_2020` |
| label | positive |
| mode | live-rule calibration |
| stable_window | `2014-01-01` to `2018-12-31` |
| control_window | `2017-01-01` to `2018-12-31` |
| crisis_window | `2020-01-01` to `2020-06-30` |
| status | newly pre-registered in this plan |

Rationale:

- The stable and control windows are **inherited unchanged from the pre-existing foundation repo-event setup**, already fixed in the project record before this C-US calibration plan, making window-tuning for this event structurally difficult to allege.
- The stable and control windows deliberately exclude the 2019-09 repo spike because the repo episode is a separate pre-registered negative near-miss control, not part of a quiet baseline.
- The crisis window begins in January 2020 to include pre-acute buildup and avoid selecting only the peak stress days.
- The main acute funding stress is expected around March 2020, but the window is intentionally broad and fixed before calibration.
- The Federal Reserve established the Commercial Paper Funding Facility on 2020-03-17 to support credit flow through the commercial paper market; this supports treating the episode as a credit/funding-market stress event rather than a generic pandemic-only event.
- NBER dates the 2020 recession peak to February 2020 and trough to April 2020; the selected crisis window covers the macro-financial contraction and early stabilization interval.

---

### 4.3 Positive event: SVB_2023

| Field | Value |
|---|---|
| event_id | `SVB_2023` |
| label | positive |
| mode | live-rule calibration |
| stable_window | `2021-01-01` to `2021-12-31` |
| control_window | `2021-01-01` to `2021-12-31` |
| crisis_window | `2023-01-01` to `2023-06-30` |
| status | newly pre-registered in this plan |

Rationale:

- The 2022 tightening cycle is excluded from the stable window for **two independent reasons**:
  - (a) Including 2022 would normalize away a structurally active policy-rate-change regime in the `rho = DFF` channel. The tightening cycle began in March 2022, with multiple 75bp hikes later in 2022; including that regime would inflate the rho P99 and absorb genuine crisis signal into the baseline.
  - (b) 2022 contains known stress episodes — the September 2022 UK gilt/LDI crisis and the crypto-market cascade — violating the "no known stress events" stable-window criterion independently of the tightening-regime argument.
- The stable window is shorter than the preferred 2-3 year baseline, but a **shorter window with a clean rationale is preferred over a longer contaminated one**. One year of daily observations (~250) is not ideal for tail estimation, but it is accepted here as a pre-registered minimum because extending into 2022 would contaminate the baseline. This limitation is disclosed before calibration.
- The control window equals the stable window; a one-year baseline leaves no room for a separate sub-window. This constraint is stated openly rather than hidden.
- **Considered and rejected:** excluding 2021 due to the March 2021 Archegos episode. Archegos was a concentrated loss event at a small number of banks, not a broad stress in short-term funding markets (the psi channel's measurement target); it therefore does not meet the stable-window exclusion criterion, and 2021 is retained.
- The crisis window begins in January 2023 to include pre-failure regional-bank stress buildup, and ends in June 2023 to cover the failure cluster: Silicon Valley Bank closed 2023-03-10, Signature Bank closed 2023-03-12, and First Republic Bank closed 2023-05-01, per FDIC 2023 bank-failure records.
- Note: this event performs, with the replacement psi spread (`DCPF3M - DTB3`), the out-of-sample check that the foundation study could not run due to LIBOR discontinuation.

---

### 4.4 Negative near-miss control: REPO_2019

| Field | Value |
|---|---|
| event_id | `REPO_2019` |
| label | negative_near_miss |
| mode | historical reproduction + live-rule calibration |
| stable_window | `2014-01-01` to `2018-12-31` |
| control_window | `2017-01-01` to `2018-12-31` |
| evaluation_window | `2019-01-01` to `2020-02-29` |
| expected pass condition | red episode count = 0 |
| status | inherited and fixed |

Rationale:

- This window is inherited from the foundation study's pre-existing repo near-miss setup, already fixed in the project record before this C-US calibration plan.
- The repo episode is intentionally retained as the **hard negative control** (see §3): it is not a quiet baseline but a real turbulence window, used to test whether the frozen rules avoid declaring a red systemic episode on a known non-collapse stress event.

---

### 4.5 Negative quiet control: QUIET_2017

| Field | Value |
|---|---|
| event_id | `QUIET_2017` |
| label | negative_quiet |
| mode | live-rule calibration |
| stable_window | `2014-01-01` to `2016-12-31` |
| control_window | `2015-01-01` to `2016-12-31` |
| evaluation_window | `2017-01-01` to `2017-12-31` |
| expected pass condition | red episode count = 0 |
| status | newly pre-registered in this plan |

Rationale:

- The quiet window is intentionally selected as a low-stress negative control (the **easy test** of §3); the harder negative control is `REPO_2019`.
- 2017 is a historically documented low-volatility year with no known credit-stress episodes.
- The evaluation year is outside the stable window, so red episode absence is not tautologically guaranteed by using the same dates for normalization and evaluation.
- **Considered and rejected:** using a recent year as the quiet control. Recent years contain well-known market-turbulence and policy-shock episodes, making a strict zero-red pass condition less clean for a negative control. A negative control must be an unambiguously quiet year.
- The 2016 U.S. money-market-fund reform period is acknowledged as a possible source of short-rate/spread level shifts. The frozen psi transform uses a 5-observation absolute change functional, not a raw spread level, which should reduce level-shift contamination. This is noted here before calibration rather than handled by moving windows after results.

---

## 5. Pass/fail criteria

Calibration pass/fail follows the C-US SPEC and common SPEC rules.

### Positive events

Positive events: `GFC_2008`, `CREDIT_SHOCK_2020`, `SVB_2023`

Pass condition:

- At least 2 of 3 positive events must satisfy `Sep(Pi) > 1.0` and `Sep(Sbar) >= 1.0` under the live-rule specification.

### Negative controls

Negative controls: `REPO_2019`, `QUIET_2017`

Pass condition:

- red episode count = 0 for each negative control.

### Structural checks

- Each event-specific stable window must have transformed-channel pairwise `max_abs_corr < 0.7`.
- Required FRED series must exist over the needed windows.
- Missingness must be resolvable under the C-US channel-specific LOCF rules, or the affected dates must be marked unavailable rather than dropped.
- `DCPF3M - DGS3MO` sensitivity may be recorded, but it must not alter the primary frozen specification.

---

## 6. Required outputs to store after running calibration

After this plan is committed and calibration is run, store all raw results under `calibration/C-US/`.

Required disclosure:

- event-specific P99 values
- `Sep(Pi)` for each event
- `Sep(Sbar)` for each event
- stable-window pairwise correlations
- red episode counts for negative controls
- missingness/fill-limit statistics
- sensitivity results for `DCPF3M - DGS3MO`
- pass/fail summary

Do not store only the final pass/fail label.

---

## 7. What to do if calibration fails

Failure does not justify silent window movement.

If calibration fails:

1. Keep this file unchanged.
2. Commit all failed results.
3. Write a failure analysis note.
4. If redesign is justified, create a new file such as `calibration_plan_v2.md`.
5. Explain exactly what changed and why.
6. Re-run only after committing the new plan.

This preserves the audit trail and prevents hidden post-hoc fitting.

---

## 8. Live archive stable window is not fixed here

This file fixes event-specific calibration windows only.

The live archive stable reference window used to compute frozen live P99, live `mu_control`, and live `sigma_control` is a separate freeze decision. It must be selected and documented before official `valid` snapshots begin, but it is not defined by this calibration plan.

---

## 9. Implementation table for code/config

If the calibration pipeline uses a Python event table, encode the newly fixed events as follows:

```yaml
CREDIT_SHOCK_2020:
  label: positive
  mode: live
  stable_start: 2014-01-01
  stable_end: 2018-12-31
  control_start: 2017-01-01
  control_end: 2018-12-31
  crisis_start: 2020-01-01
  crisis_end: 2020-06-30

SVB_2023:
  label: positive
  mode: live
  stable_start: 2021-01-01
  stable_end: 2021-12-31
  control_start: 2021-01-01
  control_end: 2021-12-31
  crisis_start: 2023-01-01
  crisis_end: 2023-06-30

QUIET_2017:
  label: negative_quiet
  mode: live
  stable_start: 2014-01-01
  stable_end: 2016-12-31
  control_start: 2015-01-01
  control_end: 2016-12-31
  crisis_start: 2017-01-01   # evaluation_start role for negative control
  crisis_end: 2017-12-31     # evaluation_end role for negative control
  expected_red_episodes: 0
```

For negative controls, the current implementation may use `crisis_start` / `crisis_end` as the generic evaluation-window fields. In that case, the `QUIET_2017` dates above are the evaluation window and must not be interpreted as a positive crisis label.

The inherited events should remain exactly as specified in `SPEC-1.0-C-US v5` unless the code requires exact-date expansion.

---

## 10. External historical references used for window justification

These references are used only to justify historical chronology, not to tune calibration outputs.

- NBER Business Cycle Dating Committee announcement, 2020 peak/trough chronology: https://www.nber.org/news/business-cycle-dating-committee-announcement-july-19-2021
- Federal Reserve Commercial Paper Funding Facility page, CPFF established on 2020-03-17: https://www.federalreserve.gov/monetarypolicy/cpff.htm
- Federal Reserve FOMC meeting calendars and statements, 2022 tightening-regime chronology: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- FDIC 2023 bank-failure records: https://www.fdic.gov/resources/resolutions/bank-failures/in-brief/2023
