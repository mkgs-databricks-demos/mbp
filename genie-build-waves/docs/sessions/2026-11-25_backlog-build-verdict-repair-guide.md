# Backlog: build-level verdict, repair guide fix

Date: 2026-11-25 | Branch: `mg-genie-build-waves-backlog-verdict-repair-guide` | File: `docs/plans/2026-11-15_framework-backlog.md`

## Problem
The external monitor's final report for a level 4 consumer build listed two framework gaps no backlog item covered:
1. Each run's `build_verdict` judges only its own waves, so a build that passed across three runs and a repair has no single build-level verdict.
2. `docs/prompts/repair-failed-wave.md` still says to repair from `w<w>_sessions` to rerun a failed session, which reruns nothing (a `blocked` / `fail` iteration ends SUCCESS) and contradicts the monitor skill.

## Changes
* Backlog item 12: a build ledger keyed by manifest `build` and a second verdict line (`BUILD_COMPLETE` / `BUILD_INCOMPLETE`), with open edge cases.
* Backlog item 13: split the repair guide's "A session" row into fresh run (`fail` / `blocked`) and repair (`error` / timed out), add the owner-decision repair from `w<w>_integrate`, link "Goal over mechanism"; revert when item 7 ships. Marked "before a new level 4 project".
* Summary table rows 12 and 13.

## Decisions
* Item 13 stays a backlog item (docs-only, small) as the owner asked, rather than editing the repair guide in this change.

## Files modified
* `docs/plans/2026-11-15_framework-backlog.md`
* this summary, `docs/sessions/INDEX.md`
