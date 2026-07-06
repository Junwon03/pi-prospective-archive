# C-US Calibration Failure Analysis v1

This file records the first C-US pre-freeze calibration run.

Overall result: FAIL

Summary

- positive_pass = 3 / 3
- negative_zero_red = false
- nonredundancy_ok = true
- overall_pass = false

Positive events passed:
- GFC_2008
- CREDIT_SHOCK_2020
- SVB_2023

Hard negative passed:
- REPO_2019

Failed event:
- QUIET_2017
- red episodes: 1
- episode: 2017-01-02 to 2017-08-24

Conclusion

The v1 calibration result is preserved without modifying the pre-registered windows.
If redesign is required, create calibration_plan_v2.md before any re-run.
