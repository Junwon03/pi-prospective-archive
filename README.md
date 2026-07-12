# pi-prospective-archive

**Pre-freeze prospective archive for the Π Structural Stability framework — C-US subtrack**

This repository is a prospective, versioned, append-only archive for the C-US financial stress subtrack.

The archive is designed to freeze a diagnostic rule before future market outcomes occur, then record daily source data, computed stress values, alert summaries, metadata, and file hashes in chronological order. Its purpose is to make post-hoc rule fitting auditable and difficult: once frozen, the definitions, constants, alert rules, and outcome criteria are not changed in response to future events.

This repository is a research record. Nothing in this repository constitutes investment, trading, portfolio allocation, or risk-management advice.

---

## Current Status

| Component                   | Status                                       |
| --------------------------- | -------------------------------------------- |
| C-US subtrack               | Pre-freeze / dry-run                         |
| Target valid archive start  | 2026-08-03                                   |
| Prospective evidence status | Not yet active                               |
| Current snapshots           | `dry_run` only                               |
| Calibration                 | v1 and v2 records preserved                  |
| Primary outcome proxy       | KBE                                          |
| Secondary market check      | BKX, if openly reproducible                  |
| Secondary banking outcome   | FDIC failed bank event with assets ≥ USD 10B |

Valid prospective evidence begins only after the C-US freeze commit and release. All dry-run snapshots, calibration outputs, diagnostics, and pre-freeze notes are audit records, not prospective evidence.

---

## What This Repository Is

This repository is:

* a pre-freeze diagnostic archive for the C-US financial stress subtrack;
* an append-only record of daily source observations and computed stress signals;
* a reproducible implementation of a fixed, causal stress construction;
* a time-stamped audit trail for calibration, dry-run validation, implementation fixes, and future valid snapshots;
* a foundation for a prospective financial-stress dataset intended for long-horizon research use.

The target archive horizon is at least 500 days and potentially up to 2 years or more.

---

## What This Repository Is Not

This repository is not:

* an investment signal;
* a trading model;
* a portfolio allocation tool;
* a probabilistic forecasting model;
* a post-hoc backtest optimization project;
* a service that changes its rule after seeing future market outcomes.

Alerts are research records only.

---

## Core Diagnostic Construction

The C-US archive uses a multiplicative stress construction:

```text
S(t) = rho_hat(t) * psi_hat(t) * omega_hat(t)
```

For the C-US live specification:

```text
rho   = absolute 5-trading-observation change in DFF
psi   = absolute 5-trading-observation change in DCPF3M - DTB3
omega = TOTBKCR level, aligned by as-of LOCF
```

The smoothed alert metric is:

```text
Sbar_w = trailing 90-trading-observation rolling mean of S
```

The live alert thresholds will be:

```text
yellow = LIVE_MU + 2 * LIVE_SIGMA
red    = LIVE_MU + 3 * LIVE_SIGMA
```

The target freeze date is:

```text
LIVE_FREEZE_DATE = 2026-08-03
```

---

## Freeze Constants Candidate

The current pre-freeze candidate constants are recorded in:

```text
calibration/C-US/live_freeze_constants_v1.json
calibration/C-US/live_freeze_constants_v1.md
```

Current selected method:

```text
Option B: in-window Sbar with 90-observation burn-in
```

Candidate values:

```text
LIVE_STABLE_WINDOW = 2024-01-01 to 2025-12-31

LIVE_P99:
rho   = 0.25
psi   = 0.1999999999999993
omega = 18958.8656

LIVE_MU_SIGMA:
mu    = 0.03397769653160021
sigma = 0.038047420246019654

Implied thresholds:
yellow = 0.11007253702363952
red    = 0.14811995726965918
```

These values are not official until copied into `src/pi_archive/config.py` and committed as the freeze commit.

---

## Outcome Definition

The primary prospective outcome is U.S. bank-sector equity stress.

Primary market proxy:

```text
KBE — SPDR S&P Bank ETF
```

Primary drawdown rule:

```text
reference price = KBE close on red episode open date
drawdown = 1 - min_close_within_6_months / close_on_red_open_date
```

Outcome classes:

```text
correction = KBE drawdown >= 12% and < 25%
collapse   = KBE drawdown >= 25%
```

Secondary market check:

```text
BKX — KBW Nasdaq Bank Index, if openly reproducible
```

Secondary banking outcome:

```text
FDIC failed bank event with reported total assets >= USD 10B
```

The outcome definition is recorded in:

```text
calibration/C-US/outcome_definition_v1.md
```

---

## Calibration Record

The archive preserves both the original v1 calibration result and the later v2 open-date attribution result.

### v1 Window-Sliced Harness

The original v1 window-sliced calibration result is preserved as full disclosure.

Top-level result:

```text
positive_pass = 3
positive_total = 3
positive_criterion = true
negative_zero_red = false
nonredundancy_ok = true
overall_pass = false
```

QUIET_2017 failed under the v1 window-sliced harness.

### QUIET_2017 Diagnosis

A later diagnostic showed that the QUIET_2017 red episode was not newly opened inside 2017.

Continuous episode diagnosis:

```text
actual open date  = 2016-12-16
actual close date = 2017-08-24
```

Therefore:

```text
newly opened red episodes inside 2017 = 0
inherited active red episodes in 2017 = 1
```

This diagnosis is recorded in:

```text
calibration/C-US/quiet_2017_episode_diagnosis_v1.md
```

### v2 Open-Date Attribution Harness

The v2 harness aligns scoring with the archive episode semantics: red episodes are attributed by their actual open date, while inherited active episodes are still disclosed.

Top-level v2 result:

```text
positive_pass = 3
positive_total = 3
positive_criterion = true
negative_zero_red = true
nonredundancy_ok = true
overall_pass = true
```

The v2 result is stored separately under:

```text
calibration/C-US/open_date_v2/
```

The v1 failure is not deleted or overwritten.

---

## Repository Structure

```text
SPEC-1.0_common_v4.md
SPEC-1.0-C-US_v5.md

src/pi_archive/
  calibration.py
  channels.py
  config.py
  daily.py
  fetch_fred.py
  health.py
  stress.py
  writer.py

tests/
  test_core.py
  test_daily.py
  test_workflows.py

.github/workflows/
  ci.yml
  collect_c_us.yml
  healthcheck.yml

calibration/C-US/
  calibration_plan.md
  failure_analysis_v1.md
  freeze_decision_note_v1.md
  quiet_2017_episode_diagnosis_v1.md
  calibration_scoring_addendum_v1.md
  open_date_v2_results_note.md
  live_reference_window_v1.md
  live_freeze_constants_v1.json
  live_freeze_constants_v1.md
  outcome_definition_v1.md
  freeze_protocol_v1.md
  dry_run_stability_note_v1.md
  live/
  reproduction/
  open_date_v2/

snapshots/C-US/
  YYYY-MM-DD/
    RUN_ID/
      raw.csv
      computed.csv
      alert.json
      meta.json
      manifest.sha256

docs/
  data_dictionary.md
  versioning_policy.md

CITATION.cff
LICENSE
LICENSE-DATA.md
requirements.lock
run_calibration.py
run_snapshot.py
run_health_check.py
```

---

## Snapshot Files

Each snapshot contains:

```text
raw.csv
computed.csv
alert.json
meta.json
manifest.sha256
```

### raw.csv

Source observations retrieved for the snapshot.

### computed.csv

Aligned channel values, normalized channel values, stress values, and alert-related computed fields.

### alert.json

Latest alert summary for the snapshot.

### meta.json

Audit metadata including:

```text
snapshot_id
subtrack
spec_version
created_at_utc
code_git_commit
p99_used
mu_sigma_used
freeze_date
spec hashes
environment_hash
snapshot_status
data_sources
file hashes
```

### manifest.sha256

SHA-256 hashes of local snapshot files:

```text
raw.csv
computed.csv
alert.json
meta.json
```

The manifest intentionally covers local snapshot files only. Code, SPEC, and environment integrity are recorded in `meta.json`.

---

## Reproducibility

Clone the repository:

```bash
git clone https://github.com/Junwon03/pi-prospective-archive
cd pi-prospective-archive
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.lock
```

Run tests:

```bash
python -m pytest -q
```

Expected current result:

```text
43 passed
```

---

## Dry-Run and Valid Snapshots

Snapshot status values:

```text
dry_run
valid
correction
```

Current status:

```text
dry_run
```

Dry-run snapshots are operational validation records and are excluded from prospective evidence.

Valid snapshots begin only after the freeze release.

---

## No-Lookahead Rule

Live computation must not use:

* future observations;
* centered rolling windows;
* backward fill;
* noncausal interpolation.

Live alignment uses past observations only.

The test suite includes invariants for causal calculation, LOCF behavior, episode semantics, snapshot contracts, and official snapshot requirements.

---

## Correction Policy

Past valid snapshots are not overwritten.

If an error is found after freeze, the archive must use a documented correction path rather than silently replacing history.

A correction must record:

```text
correction_reason
supersedes
whether computed-value interpretation changed
whether a new SPEC version is required
```

If a correction changes frozen definitions or alert interpretation, a new SPEC version is required.

---

## Documentation

Important audit and documentation files:

```text
docs/data_dictionary.md
docs/versioning_policy.md

calibration/C-US/freeze_protocol_v1.md
calibration/C-US/dry_run_stability_note_v1.md
calibration/C-US/outcome_definition_v1.md
calibration/C-US/live_reference_window_v1.md
calibration/C-US/live_freeze_constants_v1.md
```

Calibration audit files:

```text
calibration/C-US/calibration_plan.md
calibration/C-US/failure_analysis_v1.md
calibration/C-US/freeze_decision_note_v1.md
calibration/C-US/quiet_2017_episode_diagnosis_v1.md
calibration/C-US/calibration_scoring_addendum_v1.md
calibration/C-US/open_date_v2_results_note.md
calibration/C-US/rerun_note_after_locf_patch.md
```

---

## Citation

Citation metadata is provided in:

```text
CITATION.cff
```

Before the freeze release, cite the repository URL and commit hash.

After freeze, cite the release DOI once available.

When reusing snapshot data, preserve:

```text
snapshot_id
code_git_commit
manifest hash
snapshot_status
```

---

## License

Software code is released under the MIT License.

Repository-created documentation, metadata, computed archive outputs, manifests, calibration notes, and derived C-US archive records are released under the data license described in:

```text
LICENSE-DATA.md
```

Raw upstream observations remain subject to their original provider terms.

---

## AI Assistance Disclosure

The project design, methodological decisions, verification responsibility, and final research interpretation remain the responsibility of the author.

AI systems were used as research and implementation assistants for code drafting, debugging, documentation, review, and test design.

Assistance included:

```text
Anthropic Claude models — architecture discussion, code drafting, test design, diagnostic review
OpenAI GPT-5.5 models — design review, code review, bug diagnosis, documentation drafting, testing guidance
```

AI assistance does not replace author responsibility for final validation.

---

## Author

Junwon Lee

Independent researcher / undergraduate researcher

GitHub: `Junwon03`

---

## Disclaimer

This archive is a research record.

Nothing in this repository constitutes investment advice, trading advice, portfolio allocation advice, or risk-management advice.
