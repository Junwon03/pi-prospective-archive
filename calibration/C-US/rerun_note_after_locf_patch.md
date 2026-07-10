# Calibration Rerun After Trailing LOCF Fix

Date: 2026-07-10

The trailing-edge LOCF implementation was corrected before freeze.
This correction implements the existing SPEC as-of LOCF rule and does not alter calibration windows, thresholds, channels, or pass/fail criteria.

After the fix, calibration was rerun with fresh FRED data using:

```bash
python run_calibration.py fetch && python run_calibration.py run --strict
```

Top-level result remained unchanged:

```json
{
  "positive_pass": 3,
  "positive_total": 3,
  "positive_criterion": true,
  "negative_zero_red": false,
  "nonredundancy_ok": true,
  "overall_pass": false
}
```

Interpretation: the LOCF patch corrected live trailing-edge availability but did not change the pre-freeze calibration verdict.
