# Setup branch from the manifest, deploy-approval checks, backlog items 10-11

Date: 2026-11-25 | Branch: `mg-genie-build-waves-branch-and-approval-checks`

## Problems (from a level 4 consumer build)
1. **Setup synced to an empty branch.** Setup's pull read the build job's `branch` default before patching the job; an earlier setup had emptied it (the manifest had no top-level `branch`), so `SETUP_SYNC_FAILED: the branch parameter is empty`, the monitor's grants commit was not pulled, and a second setup run (plus an owner approval) was needed.
2. **Deploy approval was taken for run approval.** Two `allow_deploy` sessions deployed a bundle in a subfolder and had to run its registration job (`bundle run`). Tier 1 implies only `bundle.deploy` of `bundle:build_root`, so the run was refused and the wave failed. Nothing warned at setup.

## Changes
* `branch_sync.setup_branch(manifest_branch, job_default)`: the manifest's top-level `branch` wins, then the job default; setup's "Pull the build branch" cell uses it and records `branch_source` in `setup_sync`.
* `validate_manifest`: error for a non-string / empty `branch` or `main` / `master`; warning when branch sync is on and there is no top-level `branch`.
* `authorizations.deploy_approval_warnings`: for `allow_deploy` / converge sessions in runnable waves, warns when the only deploy approval is the implied `bundle:build_root`, and when the scope, `context_notes` or `owned_assets` mention a run (`bundle run`, run-now, `run <snake_case_name>`) with no `jobs.run_now` approval. Called from `validate_authorizations`.
* `authorizations.plan_deploy_warnings(m, read_plan)`: the same run check on each deploying session's plan file (not repeated when the manifest already warns); setup's "Validate manifest" cell reads the plans and prints these warnings.
* Docs: `manifest-schema.md` `branch` row; planner skill rule "Deploy approval is not run approval".
* Backlog: item 7 (failed/blocked sessions end SUCCESS) moved to **adopt**; new item 10 (owner decisions recorded in Git) and item 11 (machine-checked wave preconditions).

## Verification
* pytest: 208 passed (9 new tests).
* Run against the consumer build's real manifest: warns for sessions 12 (manifest text) and 16 (plan text), the two sessions whose run was refused, and for the three deploying sessions' implied-only deploy approval. Example manifests: 0 errors.
* Not run against a live instance: setup notebook changes are exercised only through the pure helpers they call.

## Decisions
* Both checks are **warnings**, not errors: tier 3 monitor grants can still cover the gap at run time, and validate does not see them.
* The manifest `branch` is committed, not a run-time value, so preferring it keeps the rule that setup never follows a run-time parameter; the folder must still already be on that branch.

## Files modified
* `src/notebooks/branch_sync.py`, `src/notebooks/setup_build_waves_job.ipynb`, `src/notebooks/waves_manifest.py`, `src/notebooks/authorizations.py`
* `tests/test_branch_sync.py`, `tests/test_waves_manifest.py`, `tests/test_authorizations.py`
* `docs/manifest-schema.md`, `src/skills/genie-build-planner/SKILL.md`, `docs/plans/2026-11-15_framework-backlog.md`
* this summary, `docs/sessions/INDEX.md`
