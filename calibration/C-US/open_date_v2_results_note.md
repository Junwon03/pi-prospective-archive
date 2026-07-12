# C-US Open-date Attribution v2 Results Note

Date: 2026-07-12
Subtrack: C-US
Status: Pre-freeze calibration scoring result note

## Purpose

This note records the result of the open-date attribution calibration harness.

The v2 harness was introduced after the QUIET_2017 diagnosis and the C-US Calibration Scoring Addendum v1. It aligns calibration scoring with the archive episode semantics, where a red episode is identified by its actual open date.

This note does not replace or delete the v1 window-sliced result.

## Preserved v1 Result

The original v1 window-sliced harness result remains preserved.

Top-level v1 summary:

positive_pass = 3
positive_total = 3
positive_criterion = true
negative_zero_red = false
nonredundancy_ok = true
overall_pass = false

Interpretation:

- Positive cases passed 3/3.
- Nonredundancy passed.
- QUIET_2017 failed under the v1 window-sliced harness.
- The v1 failure remains part of the audit trail.

## Open-date Attribution v2 Result

The v2 open-date attribution harness produced:

positive_pass = 3
positive_total = 3
positive_criterion = true
negative_zero_red = true
nonredundancy_ok = true
overall_pass = true

Interpretation:

- Positive cases passed 3/3.
- Nonredundancy passed.
- Negative zero-red criterion passed under open-date attribution.
- Overall v2 calibration passed.

## QUIET_2017 Attribution

For QUIET_2017, the v2 result was:

scoring_method = open_date_attribution_v2
n_red_episodes = 0
red_episodes_opened_in_window = 0
episodes = []
n_inherited_active_red_episodes = 1
inherited_active_episodes = [["2016-12-16", "2017-08-24"]]

Interpretation:

- No red episode newly opened inside the 2017 evaluation window.
- One inherited active red episode overlapped the 2017 window.
- The inherited episode opened on 2016-12-16 and closed on 2017-08-24.

## Audit Position

The v2 result is not a deletion of the v1 failure.

The audit trail is:

1. v1 window-sliced harness reported QUIET_2017 as failing.
2. QUIET_2017 diagnosis showed that the red episode actually opened before the 2017 window.
3. Calibration Scoring Addendum v1 specified open-date attribution and required inherited active episodes to remain disclosed.
4. The v2 harness implemented that rule.
5. v2 calibration passed while still disclosing the inherited active QUIET_2017 episode.

## No Post-hoc Tuning

This result does not change:

- calibration windows
- channel definitions
- fill limits
- thresholds
- QUIET_2017 inclusion
- event-specific P99 logic
- live freeze constants

The change is limited to episode attribution for calibration scoring, following the pre-freeze scoring addendum.

## Output Locations

v1 results:

- calibration/C-US/live/calibration_results.json
- calibration/C-US/reproduction/reproduction_results.json

v2 results:

- calibration/C-US/open_date_v2/live/calibration_results.json
- calibration/C-US/open_date_v2/reproduction/reproduction_results.json
