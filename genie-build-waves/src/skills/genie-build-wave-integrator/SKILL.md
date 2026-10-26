---
name: genie-build-wave-integrator
description: Integrates one wave after its parallel Genie Code sessions finish — checks session status files, runs the wave gate checks, optionally commits and pushes to a feature branch (git/hybrid modes), updates the sessions index, and writes the wave gate result file. Supports git, workspace, and hybrid workflow modes. Use when a job task passes wave, run_id, branch, build_root and manifest_path.
---

# Wave Integrator

You run once per wave, after every session of the wave has finished (successfully or not). In `git`/`hybrid` modes you are the **only** task allowed to commit. You run unattended with auto-approve.

## Inputs (from the job task parameters)

| Parameter | Meaning |
|---|---|
| `wave` | Wave id, e.g. `0`, `1`, `4a`, `4-1` |
| `run_id` | Job run id (same value the session tasks received) |
| `branch` | Feature branch to commit and push to (for `git`/`hybrid`; may be empty for `workspace`) |
| `build_root` | Absolute workspace path of the project |
| `manifest_path` | Absolute path of `waves.json` |

## Guardrails (hard rules)

### Always apply (all modes)

1. Do not fix session code or outputs. If something is broken, report it in the gate file; the run is repaired by re-running the failed session.
2. Deploy nothing, ever — not even for `converge` waves. Only read-only checks plus the checks listed in the wave `gate`. Runtime stability (`runtime_gate`) is checked deterministically by the gate notebook after you finish; do not try to reproduce it, and do not report it as passed.
3. Never write or print secret values.

### Git guardrails (workflow `git` or `hybrid`)

4. Commit and push **only** to the `branch` parameter. If `branch` is `main` or `master`, write a `fail` gate (step 7) and stop without committing. Never force-push, merge, rebase, reset, checkout or switch branches. If the Git folder is not on `branch`, write a `fail` gate and stop.
5. Stage files by explicit path. Never stage everything. Never stage anything under `status_dir`.

## Steps

### 1. Load the wave

Read `manifest_path`. Find the wave with `wave_id == wave`. Keep its `sessions`, `manual_prereqs`, `gate` and `runtime_gate`, plus top-level `workflow` (default `{"mode": "git"}`), `repo_root` (default: `build_root`), `bundle_target`, `status_dir`, `sessions_dir`.

Treat `converge` sessions exactly like `edit` sessions for file ownership, stray detection and staging (steps 3 and 6).

Determine: `workflow_mode` = `manifest.workflow.mode` or `"git"`.

**Archived waves.** Waves with `"archived": true` are earlier builds kept as history; they have no job tasks. In this skill, "first wave", "last wave" and "later wave" always mean **runnable** (non-archived) waves in manifest order. Never expect or look for `status_dir` files for sessions in archived waves, and never report them as missing. A `depends_on` entry naming an archived session is satisfied. If the wave you were given is itself archived, write a `fail` gate with `reason: "wave is archived; re-run setup"` and stop.

**Branch check (git/hybrid only, first wave only).** If this is the manifest's first runnable wave and `workflow_mode` is `git` or `hybrid`, check that `branch` exists on the remote: `git ls-remote --heads origin <branch>` (via the Git CLI on `repo_root`). If the branch is not found on the remote, write a `fail` gate with `reason: "branch not found on remote — it may have been merged and deleted. Retarget the build to a new feature branch, update the manifest, re-deploy with --var build_branch=<new>, re-run setup, and start a new run."` and stop without committing.

### 2. Collect session results

For each session, read `build_root/<status_dir>/<run_id>/<session_id>.json`. A missing file counts as `error` (the task crashed or never ran). A file with `status: "in_progress"` also counts as `error` (the session hit the turn limit or crashed before writing its final status). Build a table: session_id, mode, status, files_changed, assets_changed, failed/skipped checks, requests, blocking. For `converge` sessions also note the number of `attempts`, the last attempt's `result`, and every entry in `suppressions`.

**Incomplete session file credit.** When a session's status is `error` because its file is missing or `in_progress`, scan the working tree for files under its `owned_paths` (and not its `exclude_paths`). If any exist, add them to that session's `files_changed` in your table and note `reason: "incomplete session file credit"`. This prevents the stray detector from flagging code a partially-complete session left behind. The session still fails the gate (its status is `error`), so the repair run re-executes it.

**Inherited files.** A session rerun in a new build run keeps the uncommitted changes an earlier run of it left in its `owned_paths` (the usual recovery after a failed gate is a new run, not a repair). Those files are in its top-level `files_changed` but in none of this run's attempts. A file in a `converge` session's `files_changed` that no attempt lists is **inherited** when a status file of the **same session** from another run (`status_dir/<other_run_id>/<session_id>.json`, top-level or attempt `files_changed`) lists it; the newest such run is its source. An inherited file must match the session's `owned_paths` and not its `exclude_paths`; if it does not, the session is inconsistent.

A `converge` session is inconsistent, and you treat it as `fail`, when `status` is `pass` and any of these holds: its last attempt is not `stable`; an attempt's file is missing from `files_changed`; `files_changed` has a file that is neither in an attempt nor inherited; an inherited file is outside its `owned_paths` or in its `exclude_paths`. In short: `files_changed` must equal the inherited files plus the union of the attempts' `files_changed`. The gate notebook applies the same rule independently (`session_status.py`).

For each manual prereq, check its `done_when` condition by reading the files on disk (and branch history, if Git is available).

### 3. Check the working tree (git/hybrid only)

If `workflow_mode` is `workspace`: **skip this step entirely.** There is no Git working tree to check.

Otherwise, use Git status (read-only) on `repo_root`. Every changed or untracked file under `build_root` must be one of:
- in a session's `files_changed` and matching that session's `owned_paths` (and not its `exclude_paths`), or
- a session summary named in a status file, or
- under `status_dir` (never staged), or
- **carryover** left by an earlier run (see below).

Anything else is a **stray**. Do not stage strays; list them in the gate file. Strays fail the gate. If a file is in a session's `files_changed` but outside its `owned_paths`, treat it as a stray too. Files credited to an incomplete session (step 2, "incomplete session file credit") are not strays.

**Carryover.** Failed or interrupted runs leave files behind: summaries an integrator never committed (it crashed or never started), and code from non-passing sessions that step 6 deliberately leaves uncommitted. A fresh run (new `run_id`) must not mistake these for strays. Classify a file that is not claimed by this run as carryover when one of these holds, checked in this order:
1. `summary`: it is under `sessions_dir` and is named like a runner summary (`<YYYY-MM-DD>_w<wave>-<session_id>-<slug>.md`) for a session that exists in the manifest, or it is named as a summary in a status file under `status_dir/<other_run_id>/`.
2. `prior_run_code`: it is in the `files_changed` of a status file under `status_dir/<other_run_id>/` and matches that session's `owned_paths`.
3. `owned_by_later_wave`: it matches the `owned_paths` (and not the `exclude_paths`) of an `edit` or `converge` session in a runnable wave that comes **after** this one in the manifest. That session will rewrite and claim it.

Inherited files (step 2) are claimed by this run, so they are not strays and do not go through the list above; record each one in `carryover_files` with `kind: "inherited"`, `source: "run <earlier_run_id> / session <session_id>"`, `claimed_by: "<session_id>"`, and `staged` set to whether you staged it (step 6).

Record each carryover file with its `kind` and the run id or session id that explains it. Carryover does not fail the gate, with one exception: in the manifest's **last** runnable wave, any remaining `prior_run_code` or `owned_by_later_wave` file is unclaimed and fails the gate (`reason: "unclaimed carryover"`), so a human decides whether to keep or discard it. Never discard or revert carryover yourself.

For `hybrid` mode: only `edit`- and `converge`-mode sessions produce files to check. Ignore `execute`/`configure` sessions in the stray analysis.

### 4. Run the gate checks

Run each check in the wave `gate` list. Interpret each check description and execute it:
- **Bundle checks:** `bundle validate --strict --target <bundle_target>` via the Databricks CLI.
- **Declared bundle validations:** if the wave has `validate_bundles`, run `bundle validate --strict --target <target>` from each entry's `root` (a relative `root` resolves against `build_root`), and record every entry in `bundle_validations` with `root` and `target` copied exactly as written in the manifest. Any non-`pass` fails the gate, and the gate notebook checks that every entry was reported. If a `gate` line asks for the same validation, run it once and reference the `bundle_validations` entry in that check's detail.
- **Language checks:** typecheck, lint, test — only if a runtime is available; otherwise `skipped`.
- **State checks:** table exists, row count > 0, app running, service active, model logged, etc. — via read-only SDK/CLI/SQL calls.
- **Quality checks:** metric thresholds, schema matches, data validation.

Record each as `pass`, `fail` or `skipped` with a one-line detail. Skipped checks do not fail the gate but must be listed.

If a `gate` line describes runtime state that is also covered by `runtime_gate` (app running, no error logs, soak), record it as `skipped` with detail `deferred to runtime_gate`.

### 5. Update the sessions index

Update `build_root/<sessions_dir>/INDEX.md`: add one line per session summary from this wave at the top (reverse-chronological), with date, wave, session id, title, mode, status. Create the file with a short header if it does not exist.

### 6. Commit (git/hybrid only)

If `workflow_mode` is `workspace`: **skip this step.** Go directly to step 7.

Otherwise:

1. Stage, by explicit path: the `files_changed` of every `edit`- or `converge`-mode session with status `pass`, their summary files, the summary files of non-passing sessions, every `summary` carryover file (add an `INDEX.md` line for any that is not listed yet), and `INDEX.md`. A passing session's `files_changed` includes its inherited files, so they are committed with the session that inherited them. Do **not** stage `prior_run_code` or `owned_by_later_wave` carryover; the owning session claims it. Do **not** stage code from sessions whose status is not `pass`; leave it in the working tree for the repair run. Do **not** stage anything from `execute`/`configure` sessions (they don't produce tracked files).
2. If anything is staged, commit with message:
   ```
   wave(<wave>): <comma-separated session ids that passed>

   Automated wave integration (job run <run_id>).
   Sessions: <id>=<status>, ...
   Gate: <pass|fail> (<n> checks, <m> skipped)
   Carryover: <k> summaries staged, <j> code files left for their owners
   Inherited: <session_id> <n> files from run <earlier_run_id>, ...   (omit when none)
   ```
   then push the `branch` parameter. Record the commit SHA.
3. If nothing is staged, skip the commit and note it.

### 7. Write the gate file

Path: `build_root/<status_dir>/<run_id>/wave_<wave>_gate.json`:

```json
{
  "wave": "1",
  "run_id": "123456",
  "workflow_mode": "git | workspace | hybrid",
  "status": "pass | fail",
  "sessions": {"03": "pass", "04": "fail"},
  "manual_prereqs": {"02": "done | missing"},
  "checks": [{"name": "bundle validate --strict", "result": "pass", "detail": ""}],
  "bundle_validations": [{"root": "my-app", "target": "dev", "result": "pass | fail", "detail": "first error line when fail"}],
  "stray_files": [],
  "carryover_files": [{"path": "docs/sessions/2026-10-20_w3-09-routes.md", "kind": "summary | prior_run_code | owned_by_later_wave | inherited", "source": "run 376065156883918 / session 09", "claimed_by": "09 (inherited only)", "staged": true}],
  "requests": [{"from": "07", "path": "package.json", "change": "..."}],
  "suppressions": [{"from": "14", "path": "tsconfig.server.json", "kind": "compile-exclude", "why": "..."}],
  "commit_sha": "abc1234 or empty",
  "reason": "one line when status is fail"
}
```

`status` is `pass` only if every session is `pass`, every manual prereq is `done`, no check `fail`ed, every `bundle_validations` entry is `pass`, and there are no strays and, in the last runnable wave, no unclaimed carryover (in `git`/`hybrid` mode). Copy every session's `suppressions` into the gate file so a human can review them. Your `pass` is necessary but not sufficient when the wave has a `runtime_gate`: the gate notebook adds its own runtime verdict. The next job task reads this file and stops the run on `fail`, so write it even when you hit an error (use `status: "fail"` and put the error in `reason`).

### 8. Final response

At most 6 lines: wave, workflow mode, gate status, per-session status, commit SHA (or "n/a" for workspace), skipped checks, suppressions count, carryover count, and any `requests` the next wave or the user must act on.
