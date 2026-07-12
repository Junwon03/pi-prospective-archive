# C-US Calibration Scoring Addendum v1

Date: 2026-07-12  
Subtrack: C-US  
Status: Pre-freeze scoring clarification

## Purpose

This addendum clarifies how red episodes should be attributed for calibration pass/fail scoring.

It does not alter the registered events, windows, channels, transformations, thresholds, or calibration data. It only aligns the calibration scoring harness with the archive's episode semantics.

## Episode Semantics

A red episode is identified by its opening date.

The episode identity follows the archive convention:

- episode_id = {subtrack}-red-{open_date}

The evaluation horizon is also anchored to the red episode opening date.

Therefore, for pass/fail scoring, a red episode should be attributed to the date on which it opens.

## Negative Window Scoring Rule

For a negative calibration window, the primary red-count metric is:

- number of red episodes whose open_date falls inside the evaluation window

A negative event fails the primary red-count criterion if one or more red episodes open inside the evaluation window.

A red episode that opened before the evaluation window but remains active during the window is not counted as a newly opened red episode for the primary pass/fail criterion.

However, inherited active episodes must still be disclosed.

## Required Disclosure Metrics

For every negative calibration event, future reports should include:

1. red_episodes_opened_in_window
2. inherited_red_episodes_active_in_window
3. episode open and close dates
4. threshold values used for detection
5. whether the event passes under open-date attribution
6. whether any active red state overlapped the evaluation window

This prevents selective reporting.

## Application to QUIET_2017

The v1 window-sliced harness reported one red episode in QUIET_2017:

- reported episode: 2017-01-02 to 2017-08-24

A continuous diagnostic run showed the actual episode identity:

- actual open date: 2016-12-16
- actual close date: 2017-08-24

Therefore, under open-date attribution:

- red_episodes_opened_in_window = 0
- inherited_red_episodes_active_in_window = 1

This means QUIET_2017 contains no newly opened red episode, but it does contain an inherited active red state. Both facts must be reported.

## Positive Window Scoring Rule

For positive calibration windows, the primary detection criterion remains whether a red episode opens inside the crisis/evaluation window.

If a red episode opens before the crisis window and remains active into the crisis window, it should be reported as an inherited active red episode and evaluated separately. It should not be silently converted into a newly opened crisis-window signal.

## No Post-hoc Tuning

This addendum does not permit:

- changing calibration windows
- removing QUIET_2017
- relaxing the red threshold
- changing channel definitions
- changing fill limits
- changing LIVE_P99 or LIVE_MU_SIGMA after freeze
- deleting v1 failure records

The v1 result remains part of the audit trail.

## Rationale

The addendum corrects a scoring-attribution issue.

The archive is continuous by design. Live episodes are not created independently inside isolated evaluation windows. A calibration harness that slices the evaluation window before episode detection can misattribute an already-open episode to the first day of the sliced window.

To match the prospective archive semantics, future scoring should detect episodes over a sufficiently long context window and then attribute each episode by its actual open date.

## Implementation Guidance

The calibration harness should:

1. compute the full Sbar_w series needed for the event;
2. run episode detection over a context window that begins before the evaluation window;
3. count only episodes whose open_date falls inside the target evaluation window for primary pass/fail scoring;
4. separately report episodes already active at the start of the evaluation window.

The original v1 harness result should remain preserved and cited as the pre-addendum window-sliced result.
