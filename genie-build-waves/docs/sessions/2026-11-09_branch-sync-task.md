# 2026-11-09: Branch sync task (`w<wave>_sync`)

## Problem

The integrator commits and pushes from the `build_root` Git folder and never pulls. A fix pushed to the build branch from another clone (a person, or an external monitor such as Devin in the `devin-genie-build-waves-test` project) never reaches the folder, and the integrator's next push is rejected as non-fast-forward. Pulling by hand does not work for an unattended repair.

## Repos API behaviour (probe, 2026-11-08)

Two scratch Git folders of a private test repo (`devin-test-sync-probe`, `devin-test-sync-consumer`, branch `mg-genie-sync-probe`):

* `repos.update(id, branch=<current branch>)` pulls. Uncommitted files the incoming commits do not touch stay as they are, including untracked files.
* If an incoming commit changes an uncommitted file, the call fails with `BadRequest: Conflict pulling from remote. Conflicting files: probe/b.txt.`; the working tree and HEAD are unchanged.
* `workspace.get_status` reports a Git folder root as `DIRECTORY`, so the root is found by trying `repos.get` on `build_root` and its parents.
* A new branch checked out in a Git folder is pushed to the remote at once.

## Changes

* `src/notebooks/branch_sync.py` (new): pure helpers: result path, Git folder candidates, branch check (no switching, never `main`/`master`), conflict-file parsing, `git log` parsing, result record and `SYNC_FAILED` / `SYNC_PULLED` / `SYNC_UP_TO_DATE` messages.
* `src/notebooks/sync_branch.ipynb` (new): finds the Git folder, checks the branch, pulls, lists pulled commits and files (git CLI, best effort), writes `wave_<w>_sync.json`, sets task value `synced`. Never raises.
* `waves_manifest.py`: `sync_enabled` (git/hybrid unless `workflow.sync_branch` is false), `sync_keys`, `sync_notebook_path`; per wave `w<w>_sync` (takes the previous gate_check dependency) -> `w<w>_synced` (If/else) -> `w<w>_sessions`; `build_verdict` depends on gates and syncs; `job_task_count` +2 per wave; `sync_branch` validation (bool; warning in workspace mode); task-limit error mentions `sync_branch`.
* `gate_helpers.py`: `build_verdict(..., sync_results)` fails a wave whose sync failed (its gate is Excluded), crashed, or wrote nothing while the wave did not run; message says repair from `w<w>_sync`.
* `build_verdict.ipynb`: reads `wave_<w>_sync.json`. `find_incomplete_sessions.ipynb`: no continuation pass if `w<w>_sync` ended in a state other than SUCCESS.
* Docs: README (phase 0, diagram, task table, repair table, fixes from another clone), `manifest-schema.md` (`workflow.sync_branch`, Branch Sync section, task counts), `repair-failed-wave.md` (repair from `w<w>_sync`, `only` list), monitor requirements (optional level 3: push a fix, repair from `w<w>_sync`, one-writer rules, acceptance check), integrator skill (never pull; non-fast-forward push is a `fail` gate).
* Setup notebook comment on the task graph.

## Decisions

* Sync is on by default in git/hybrid (opt out with `workflow.sync_branch: false`); job task count per wave becomes 9 with one continuation pass.
* The sync notebook never raises: a failed task would make the If/else Upstream failed while the wave's `run_if: ALL_DONE` tasks still ran. It sets `synced=false` instead, and `build_verdict` turns that into the run failure.
* The sync never switches branches and does not resolve conflicts; both fail the wave with the reason.
* Push only while no run is active (the job runs one run at a time).

## Verification

* 167 tests pass (16 new: graph shape, `sync_enabled`, validation, path override, helpers with the real conflict text, verdict with failed / crashed / silent / skipped sync).
* The notebook's sync cell, run against the scratch Git folder: up to date -> `synced=true` and result file; folder on another branch -> `synced=false` with the message; path outside any Git folder -> `synced=false`.
* `bundle validate --strict` OK.
* Not run: a build job with the new tasks (pull and conflict paths are covered by the probe and unit tests only).

## Left to do

* Delete scratch Git folders `devin-test-sync-probe`, `devin-test-sync-consumer`, the stray folder `/Workspace/Users/matthew.giglia@databricks.com/not-a-repo` (created by the live check) and the test repo branches `mg-genie-sync-probe`, `mg-genie-sync-probe-local` (deletion was blocked for the agent).
* First real run with sync: the `devin-genie-build-waves-test` instance.

## Files

`src/notebooks/branch_sync.py`, `src/notebooks/sync_branch.ipynb`, `src/notebooks/waves_manifest.py`, `src/notebooks/gate_helpers.py`, `src/notebooks/build_verdict.ipynb`, `src/notebooks/find_incomplete_sessions.ipynb`, `src/notebooks/setup_build_waves_job.ipynb`, `src/skills/genie-build-wave-integrator/SKILL.md`, `README.md`, `docs/manifest-schema.md`, `docs/prompts/repair-failed-wave.md`, `docs/plans/2026-11-03_devin-monitor-requirements.md`, `tests/test_branch_sync.py`, `tests/test_gate_helpers.py`, `tests/test_waves_manifest.py`.
