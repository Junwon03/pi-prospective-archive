# C-US Freeze Completion Record

Project: pi-prospective-archive
Subtrack: C-US
Freeze date: 2026-08-03
Status: **Freeze completed; first valid snapshot and DOI pending**

## Frozen Baseline

- Freeze commit: `68731c6546ebd4845531aac03e1f3be198aab61a`
- Release tag: `c-us-freeze-v1.0`
- Test result at freeze: `44 passed`
- LIVE_STABLE_WINDOW: `2024-01-01` to `2025-12-31`
- LIVE_P99: `rho=0.25`, `psi=0.1999999999999993`, `omega=18958.8656`
- LIVE_MU_SIGMA: `mu=0.03397769653160021`, `sigma=0.038047420246019654`
- LIVE_FREEZE_DATE: `2026-08-03`

## Completed Before Freeze

- [x] main branch and working tree verified
- [x] automated tests passed
- [x] GitHub Actions, collection dry-run, and healthcheck verified
- [x] dry-run snapshots and manifest integrity verified
- [x] common and C-US SPEC files recorded
- [x] calibration plan, v1 failure record, diagnosis, scoring addendum, and v2 pass record preserved
- [x] live reference window and frozen constants recorded
- [x] outcome definition fixed: KBE primary, BKX optional secondary market check, FDIC threshold USD 10B
- [x] config.py patched with frozen constants
- [x] live-constant consistency and official-snapshot tests passed
- [x] freeze commit and tag created

## Post-Freeze Pending

These items remain pending and do not change the frozen analytical rule.

- [ ] generate the first post-freeze snapshot with `snapshot_status = valid`
- [ ] confirm `meta.json` records the frozen P99, μ/σ, freeze date, and `Pi_since_freeze` anchor
- [ ] run healthcheck on the first valid snapshot
- [ ] archive the release in Zenodo or another DOI-issuing repository
- [ ] add the DOI to citation metadata after it is issued

## Prohibited Under Frozen v1.0

- change LIVE_P99, LIVE_MU_SIGMA, LIVE_FREEZE_DATE, or LIVE_STABLE_WINDOW in response to future outcomes
- remove calibration failures or inherited active episode records
- relax alert or outcome thresholds
- overwrite valid snapshots
- force-push public archive history

## Allowed Maintenance

- README and documentation clarification
- citation metadata updates
- healthcheck or packaging improvements that do not alter computed values
- explicit correction snapshots with a documented `correction_reason`

Any change to the frozen diagnostic rule requires a new major SPEC version and must not overwrite v1.0 records.
