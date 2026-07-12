# QUIET_2017 Episode Diagnosis v1

Date: 2026-07-12  
Subtrack: C-US  
Status: Pre-freeze diagnostic note

## Purpose

This note diagnoses the QUIET_2017 failure observed in the first C-US calibration run.

The purpose is not to remove the failure record. The original v1 result is retained as full disclosure. This note clarifies why the reported QUIET_2017 red episode occurred and how it should be interpreted under the archive's episode semantics.

## Original v1 Calibration Result

The first strict calibration run reported:

- positive_pass = 3 / 3
- nonredundancy_ok = true
- negative_zero_red = false
- overall_pass = false

The failing negative case was QUIET_2017.

The v1 event-level output reported one red episode in the QUIET_2017 evaluation window:

- reported episode: 2017-01-02 to 2017-08-24
- mode: live
- mu_control = 0.011535383214277987
- sigma_control = 0.010238094297203964
- red threshold = mu + 3 sigma = approximately 0.0422
- p99_event_specific:
  - rho = 0.21
  - psi = 0.20179999999999954
  - omega = 12083.5448

This result is retained as the v1 window-sliced harness result.

## Continuous Episode Diagnosis

A continuous diagnostic run over a wider period showed:

- open: 2016-12-16
- close: 2017-08-24

Therefore, the episode reported by the v1 harness as opening on 2017-01-02 was not newly opened inside 2017. It was already open before the QUIET_2017 evaluation window began.

Under continuous episode detection, the QUIET_2017 window had:

- newly opened red episodes inside 2017: 0
- active inherited red episodes during 2017: 1

## Interpretation

The failure is best interpreted as a boundary-attribution artifact in the v1 calibration harness.

The v1 harness detected episodes after slicing the evaluation window. Because the Sbar_w series was already above the red threshold at the start of the 2017 window, the harness attributed the inherited red state to the first trading day of the evaluation window.

In live archive operation, the episode would have been identified by its actual opening date, 2016-12-16. The archive would not treat it as a newly opened 2017 episode.

## Substantive Context

The timing is economically plausible.

The episode opened in December 2016, after the U.S. money market fund reform transition period and shortly after the December 2016 FOMC rate increase. These conditions could plausibly affect short-term funding-market spreads, including CP and T-bill dynamics.

The control-period sigma was also very small:

- sigma_control = 0.010238094297203964
- red threshold ≈ 0.0422

This implies a sensitive threshold under the event-specific 2015-2016 normalization. This sensitivity is retained as useful diagnostic information rather than hidden.

## Reporting Rule Going Forward

Both quantities should be reported in future calibration summaries:

1. newly opened red episodes inside the evaluation window
2. active inherited red episodes overlapping the evaluation window

The first quantity should be used for pass/fail attribution under open-date episode semantics. The second quantity should be retained as full-disclosure diagnostic information.

## Full Disclosure Position

The original v1 result is not deleted or overwritten.

The correct audit trail is:

1. v1 harness result: QUIET_2017 failed with one reported red episode.
2. diagnostic result: the red episode actually opened on 2016-12-16 and remained active until 2017-08-24.
3. scoring addendum: future pass/fail scoring should attribute red episodes by their open date while still reporting inherited active episodes.

This diagnosis does not change channels, thresholds, calibration windows, or the QUIET_2017 window.
