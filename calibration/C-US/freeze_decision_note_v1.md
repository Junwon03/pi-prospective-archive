# C-US Freeze Decision Note v1

This note records the decision after C-US calibration v1.

Initial calibration scoring under the window-sliced v1 attribution resulted in
overall_pass = false.

Reason: QUIET_2017 produced one red episode under the initial window-sliced
episode attribution.

Decision:
- Do not remove QUIET_2017.
- Do not move the quiet-control window.
- Do not relax the red threshold.
- Do not alter the frozen channel definitions, transformations, or alert logic in response to this result.

Interpretation:
- Positive events passed 3/3.
- REPO_2019 hard negative produced zero red episodes.
- Nonredundancy passed.
- QUIET_2017 is retained as a disclosed calibration case. Under the initial
window-sliced attribution, it exposed an episode attribution issue. Under the
final open-date attribution scoring, no red episode was attributed to the
evaluation window.

Prospective position:
The purpose of this archive is not to optimize retrospective calibration until every historical window passes.
The purpose is to freeze a transparent rule and measure its future behavior prospectively.
Future valid snapshots will be used to measure actual false-alarm behavior, near-miss behavior, and hit behavior without post-hoc adjustment.

Final calibration position:

The final prospective specification uses open-date attribution scoring
(SCORING_OPEN_DATE_V2). The scoring change does not alter the frozen channel
definitions, transformations, thresholds, reference windows, or alert logic.
It only corrects episode attribution so that episodes are assigned based on
their opening date rather than whether an already-open episode overlaps the
evaluation window.

The final freeze decision therefore preserves:
- the original channel construction,
- the selected reference window,
- the frozen threshold methodology,
- and the prospective evaluation rule.
