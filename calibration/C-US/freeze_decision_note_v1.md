# C-US Freeze Decision Note v1

This note records the decision after C-US calibration v1.

Calibration v1 result: overall_pass = false.

Reason: QUIET_2017 produced one red episode.

Decision:
- Do not remove QUIET_2017.
- Do not move the quiet-control window.
- Do not relax the red threshold.
- Do not alter the frozen channel definitions, transformations, or alert logic in response to this result.

Interpretation:
- Positive events passed 3/3.
- REPO_2019 hard negative produced zero red episodes.
- Nonredundancy passed.
- QUIET_2017 is retained as a disclosed specificity limitation / low-grade false-positive record.

Prospective position:
The purpose of this archive is not to optimize retrospective calibration until every historical window passes.
The purpose is to freeze a transparent rule and measure its future behavior prospectively.
Future valid snapshots will be used to measure actual false-alarm behavior, near-miss behavior, and hit behavior without post-hoc adjustment.
