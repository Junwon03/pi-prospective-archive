# Versioning Policy

Project: pi-prospective-archive  
Subtrack: C-US  
Status: Pre-freeze versioning policy  
Target LIVE_FREEZE_DATE: 2026-08-03

## Purpose

This document defines how the C-US prospective archive is versioned.

The goal is to preserve a transparent audit trail across dry-run operation, freeze, valid prospective collection, corrections, and future SPEC changes.

## Versioning Principles

The archive follows these principles:

1. Do not overwrite past valid snapshots.
2. Do not force-push public archive history.
3. Do not silently alter frozen rules.
4. Preserve failed calibration results and correction history.
5. Separate dry-run records from valid prospective records.
6. Use releases and tags to identify frozen archive states.
7. Use new major versions when frozen definitions change.

## Version Classes

### v0.x — Dry-run and pre-freeze versions

v0.x versions refer to pre-freeze development, dry-run operation, calibration, diagnostics, and implementation validation.

Dry-run snapshots are not prospective evidence.

Examples:

- dry-run collection tests
- calibration v1/v2 results
- LOCF bug discovery and correction
- healthcheck validation
- pre-freeze protocol documents
- live constants candidate calculation

### v1.0 — First frozen C-US prospective archive

v1.0 is the first official frozen version of the C-US prospective archive.

The v1.0 freeze release must include:

- frozen SPEC files
- frozen code commit
- frozen requirements.lock
- frozen LIVE_STABLE_WINDOW
- frozen LIVE_P99
- frozen LIVE_MU_SIGMA
- frozen LIVE_FREEZE_DATE
- outcome definition
- data dictionary
- versioning policy
- calibration and dry-run audit records

Valid prospective snapshots begin only after v1.0 freeze.

### v1.x — Maintenance releases under the same frozen rule

v1.x releases may include:

- documentation improvements
- README updates
- data dictionary clarifications
- non-semantic workflow improvements
- healthcheck improvements
- archive packaging improvements
- citation metadata updates

v1.x releases must not change the frozen diagnostic rule.

The following must remain unchanged in v1.x:

- channel definitions
- fill limits
- LIVE_P99
- LIVE_MU_SIGMA
- LIVE_FREEZE_DATE
- alert threshold formula
- episode semantics
- primary outcome definition
- FDIC threshold
- calibration windows

### v2.0 — New frozen rule or SPEC change

A v2.0 release is required if the archive changes any frozen diagnostic definition.

Examples requiring v2.0:

- changing channel definitions
- changing fill limits
- changing LIVE_STABLE_WINDOW after freeze
- recomputing LIVE_P99 after freeze
- recomputing LIVE_MU_SIGMA after freeze
- changing red/yellow threshold formula
- changing episode open/close semantics
- changing primary outcome proxy after freeze
- changing FDIC asset threshold after freeze
- introducing a new subtrack that changes interpretation of the original C-US archive

v2.0 must not overwrite v1.x records.

## Snapshot Status Versioning

Each snapshot has a snapshot_status.

### dry_run

dry_run snapshots are operational tests before freeze.

They may be used for debugging, validation, and audit history, but not as prospective evidence.

### valid

valid snapshots are official prospective records after freeze.

A valid snapshot must use frozen LIVE_P99, LIVE_MU_SIGMA, and LIVE_FREEZE_DATE.

### correction

correction snapshots document errors or corrections.

Corrections must not overwrite the original snapshot.

A correction must record:

- correction_reason
- supersedes
- whether computed-value interpretation changed
- whether a new SPEC version is required

## Correction Policy

Corrections are allowed only as explicit, documented records.

Correction examples:

- provider data retrieval error
- file generation error
- manifest mismatch
- missing snapshot file
- implementation bug discovered after freeze

If a correction changes the meaning of computed values, the archive must document whether the correction remains within v1.x or requires v2.0.

## Prohibited Actions After Freeze

After v1.0 freeze, the following are prohibited:

- deleting past valid snapshots
- force-pushing public archive history
- changing frozen constants in response to market outcomes
- removing failed or inconvenient records
- changing outcome thresholds after observing future outcomes
- silently replacing a valid snapshot with a corrected version

## Git Tags and Releases

The first official freeze release should use:

- tag: c-us-freeze-v1.0
- release title: C-US Prospective Archive Freeze v1.0

Future maintenance releases should use tags such as:

- c-us-v1.1
- c-us-v1.2

A future rule-changing release should use:

- c-us-v2.0

## Zenodo and DOI Policy

The freeze release should be archived through Zenodo or another DOI-issuing repository.

The DOI should identify the frozen v1.0 archive state.

Future major versions should receive separate archived releases.

## Citation Policy

Users should cite the relevant release or DOI.

For v1.0 prospective archive claims, users should cite the v1.0 freeze release and identify the snapshot_id and code_git_commit used in any analysis.

## Relationship to Calibration

Calibration outputs are part of the pre-freeze audit trail.

The archive preserves:

- v1 window-sliced harness result
- QUIET_2017 episode diagnosis
- calibration scoring addendum
- v2 open-date attribution result

Future valid archive interpretation should cite the frozen v1.0 rule and the pre-freeze calibration record.

## Relationship to README

README is an orientation document.

It may summarize current status, but the authoritative audit records are the SPEC, calibration notes, freeze protocol, outcome definition, data dictionary, and versioning policy.

## Valid Archive Start

The target valid archive start is:

2026-08-03

The actual valid start must be documented in:

- config.py
- freeze release note
- meta.json of the first valid snapshot
