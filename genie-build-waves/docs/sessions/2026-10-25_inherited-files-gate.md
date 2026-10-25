# 2026-10-25 — Gate credits inherited files on reruns

## Problem

When a wave's gate fails, the integrator leaves the session's code uncommitted, and the recovery is a new build run from that wave (repair re-runs nothing: a `blocked`/`fail` session still ends its `for_each` iteration as SUCCESS). The rerun session keeps the earlier changes and lists them in its top-level `files_changed`, but no attempt of the new run touched them. The integrator rule "`files_changed` is the union of the attempts' `files_changed`" then failed a session that converged cleanly. Seen live: AgenticTrading w13a session 35a, run 138577054371415 (5 files from run 663035567712054).

## Root cause

The union rule had no notion of files carried over by the same session from an earlier run, and it lived only in the integrator skill (agent-interpreted). The gate notebook did not check it.

## Decision

The gate **infers** inherited files rather than relying on the runner to declare them (baseline; a runner-side or preflight declaration can be added later for edits with no earlier status file, such as interactive human fixes). A file in a converge session's `files_changed` that no attempt lists is inherited when the same session's status file in another run (`status_dir/<other_run_id>/<session_id>.json`) lists it; the newest such run is the source.

## Changes

* `src/notebooks/session_status.py` (new): glob matching for `owned_paths` / `exclude_paths`, `prior_run_files`, `check_files_changed`. Rule: `files_changed` == inherited + union of attempts; inherited files must be owned and not excluded; attempt files missing from `files_changed` and unexplained files still fail.
* `src/notebooks/wave_gate_check.ipynb`: static gate applies the rule independently for passing converge sessions; prints inherited files and warns (does not fail) when the integrator did not record them in `carryover_files`.
* `src/skills/genie-build-wave-integrator/SKILL.md`: inherited-file rule in step 2, `kind: "inherited"` carryover with `claimed_by`, staged with the inheriting session, `Inherited:` commit-message line.
* `src/skills/genie-build-session-runner/SKILL.md`: status contract for `files_changed` (inherited + attempts; edits before attempt 1 go in attempt 1).
* `README.md`, `docs/prompts/repair-failed-wave.md`: inherited files; new run (not repair) is the recovery path.
* `tests/test_session_status.py` (new, 9 tests): inherited from failed prior run, inherited outside `owned_paths` / in `exclude_paths` fails, no inherited files unchanged, plus unexplained file, missing attempt file, re-edited file, newest-run / other-session / malformed-file handling, edit mode unchecked.

## Checks

* `pytest tests`: 41 passed.
* Real data (read-only): `check_files_changed` on AgenticTrading 35a run 138577054371415 returns exactly the 5 files as inherited from run 663035567712054, no problems.

## Deployment notes

The gate notebook and module are read from the live `mbp` folder (no bundle redeploy). The skills need a setup run to republish to UC after merge; repair any pending run (for example AgenticTrading 138577054371415 from `w13a_integrate`) before setup changes the job structure.
