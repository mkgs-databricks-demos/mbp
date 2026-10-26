# Bug: instances deployed from one folder share a local state cache and take over each other's jobs

**Status:** fixed on `mg-genie-build-waves-visible-failures-plan` (Fixes 1–4 implemented and tested; cleanup steps 2–4 open) · **Found:** 2026-10-26 · **Severity:** high: it silently replaces another project's build job and makes its runs unrepairable · **Area:** deployment (`instance_suffix`), setup

## Summary

README ("One deployment per project") says `instance_suffix` gives each project its own deployment state and jobs. That holds for the remote state (`.bundle/genie-build-waves<suffix>/<target>/state/`). But every instance is deployed from the same folder, `mbp/genie-build-waves`, and the CLI keeps a local state cache on the machine that runs the deploy. That cache is not keyed by `instance_suffix`. Its location depends on how the CLI is invoked: shell CLI runs use the folder's `.databricks/bundle/<target>/`, while the Genie Code CLI tool appears to use a separate cache in its own environment (see Evidence). Deploying instance B after instance A can reuse A's cached resource state. B then binds to A's job IDs, renames them, and resets them to the placeholder graph.

This is the documented procedure, not an edge case: the README tells every multi-project user to deploy several `instance_suffix` values from one folder.

## Impact (observed 2026-10-26)

* **Semantic Ground Truth build 4 lost its build job (restored).** Jobs `1079028753739581` (build), `818046072228128` (setup) and `557464573384466` (smoke) ran sGt build 4 (run `110489694161084`, waves `w4-0`..`w4-9`). The `-smoke` deploy renamed them `Build Waves Smoke: …`, reset the build job to one `placeholder` task and set its defaults to `manifest_path=.scratch/smoke-waves.json`, `build_root=mbp` and `branch=mg-genie-build-waves-visible-failures-plan`. Repairs use the job's current tasks, so the run could not be repaired. The original graph was restored the same day (Cleanup step 1); the repair from `w4-4` has not been tried yet. The smoke job is still the placeholder.
* **Hazard while the sGt run is pending.** Running sGt setup would change the build graph again (branch code adds `build_verdict`; sGt `waves.json` at `01cd9b9` archives 4-0..4-3), so do not run it until run `110489694161084` is repaired or abandoned.
* **AgenticTrading was next (averted).** The folder cache held AgenticTrading's state. `bundle summary --target dev --var=instance_suffix=-sgt-root ...` (run from the shell CLI, which uses the folder cache) showed AgenticTrading's jobs (build / smoke / setup `295400519518491` / `597498515869265` / `797765636204447`) renamed to `Semantic Ground Truth: …` instead of the sgt-root jobs (`551874922778444` / `105657567456728` / `468323402073052`). Not deployed; caught by reading the summary. The folder cache was moved aside to `.databricks/bundle/dev.bak-20261026T073033Z` (kept as evidence).
* Nothing fails or warns: `bundle validate --strict` passes, the deploy succeeds, setup succeeds.
* **Not affected:** setup was not run after the bad deploy, so no skills were republished and no automation prompts changed. Run history (including `110489694161084`) is intact.

## Evidence

Remote state per instance (`/Workspace/Users/matthew.giglia@databricks.com/.bundle/<root>/dev/state/`) and the local cache (`mbp/genie-build-waves/.databricks/bundle/dev/`):

| State | `resources.json` lineage | serial | Jobs (build / smoke / setup) | Last deploy |
| --- | --- | --- | --- | --- |
| `genie-build-waves` (default) | `a688c33c…` | 5 | `1079028753739581` / `557464573384466` / `818046072228128` | 2026-10-22 02:47 |
| `genie-build-waves-smoke` | `a688c33c…` (same as default) | 6 | same IDs as default | 2026-10-26 06:24 (seq 1, first deploy) |
| `genie-build-waves-sgt-root` | `37ca1892…` | 1 | `551874922778444` / `105657567456728` / `468323402073052` | 2026-10-22 23:04 |
| `genie-build-waves-agentic-trading` | `6282d847…` | 6 | `295400519518491` / `597498515869265` / `797765636204447` | 2026-10-23 06:40 |
| local cache `.databricks/bundle/dev` | `6282d847…` (AgenticTrading) | 6 | AgenticTrading's IDs | 2026-10-23 06:40 |

The first `-smoke` deploy produced a state with the default instance's lineage at serial 5 + 1. That is the default state carried forward, not a new state. The CLI was v1.22.1 (direct engine).

The 06:24 `-smoke` deploy ran through the Genie Code CLI tool (`runDatabricksCli`) with `workingDirectory=/Workspace/Users/matthew.giglia@databricks.com/mbp/genie-build-waves`, on commit `0bda04e`. The folder cache still holds AgenticTrading's state (10-23 06:40) and has a single sync snapshot, so that deploy did not read or write the folder's `.databricks/`. It picked up the default instance's state from a different cache, most likely one in the CLI tool's serverless environment. So there appear to be two local caches:

* the folder cache, used by shell or `executeCode` CLI runs (it produced the AgenticTrading IDs in the sgt-root summary);
* the CLI tool's cache, which carried the default state into `-smoke`.

Either way, the mechanism is the same: a local cache from another instance won over an empty remote state.

## Expected

Deploying with `instance_suffix=X` uses only instance X's state. When X has no remote state, it creates new jobs. It never touches another instance's jobs.

## Root cause

The CLI keeps resource state in a local cache on the deploying machine, one per target, not per `workspace.root_path`. Switching `instance_suffix` changes only `root_path`, so the cache is shared across instances. When the new instance has no remote state, the local cache from another instance is used and its job IDs are updated.

Reproduced on 2026-10-26 with the shell CLI and two throwaway instances: after `bundle summary` for `-iso-a` (which writes the folder cache), `bundle summary` for `-iso-b` (no remote state) listed `-iso-a`'s three job IDs. With the folder cache removed, the same `-iso-b` summary listed no job IDs and the first deploy created new jobs. `bundle summary` itself rebuilds the folder cache from the instance's remote state when there is none.

Unverified: that the CLI reconciles local and remote state by keeping the higher serial. That rule is how the Terraform engine behaves; this bundle uses `engine: direct`. Check against the CLI v1.22.1 source before relying on it.

## Fixes (implemented 2026-10-26)

1. **Ownership checks, `src/notebooks/instance_guard.py`** (pure functions, shared by Fixes 2 and 3):
   * `deployment.metadata_file_path` of every job must be under the instance's `root_path`. Before the bad deploy, job `1079028753739581` pointed at `.bundle/genie-build-waves/dev/state/metadata.json`; afterwards at `.bundle/genie-build-waves-smoke/dev/state/metadata.json`. Setup's `jobs/reset` drops this field from the build and smoke jobs (`jobs_api.RESET_DROP_KEYS`), so in practice it is the setup job that carries it.
   * Summary vs remote state: with no remote `state/resources.json`, `bundle summary` must show no job IDs; with one, every summary ID must match it.
   * The build job's `manifest_path` default and the manifest its latest run used must match the instance's manifest. Only the latest run counts, because a project may legitimately move its manifest (sGt run `713417549836954` used `ground-truth-app/docs/plans/waves.json`).
   * Optional job-name check against `project_name` (setup only).
2. **Deploy wrapper, `scripts/deploy_instance.py --target <t> --vars <file> [--check-only] [--force] [--keep-cache]`** (Python rather than `.sh`, so it can share the checks and be unit tested):
   * Moves `.databricks/bundle/<target>` aside to `<target>.bak` (one backup, replaced each time), runs `bundle summary -o json`, reads the remote state and every named job, and runs the checks. Exit 2 without deploying on any problem unless `--force`.
   * Deploys, then checks that every job's `metadata_file_path` is under this root and that no existing job ID changed (exit 3 otherwise).
   * Moves the cache aside again at the end, so a later plain CLI command for another instance does not start from this instance's state.
   * It clears only the folder cache, not the Genie Code CLI tool's cache. The README tells Genie Code to run it through Python `subprocess` and not to deploy instances with the CLI tool.
   * Not done: one checkout per instance, or a CLI env var for the cache directory.
3. **Guard in setup** (new cell "Instance ownership guard" after "Validate manifest", before anything is published or reset): runs `instance_guard.setup_problems` on the build, smoke and setup jobs and the build job's last 5 runs, and raises `INSTANCE_GUARD_FAILED` unless the new job parameter `force=true`. `setup_build_waves.job.yml` now passes `bundle_root_path: ${workspace.root_path}`, `project_name: ${var.project_name}`, `setup_job_id: "{{job.id}}"` and `force`. Setup jobs deployed before this change lack those values: the root, name and setup-job checks are skipped with a message, and the manifest and run-history checks still run. After a bad deploy the names, defaults and metadata all match the new instance, so the run-history check is the one that catches it.
4. **Docs:** README section 2 now deploys with the script (vars file example), "One deployment per project" explains that `instance_suffix` isolates remote state only, how the cache takes over another instance's jobs, the plain-CLI `bundle summary` check, not to deploy with the Genie Code CLI tool, and the setup guard / `force=true`. The Genie Code prompts and the architecture table point at the script and the guard.
5. **Cleanup of the current state:**
   1. **Done 2026-10-26 (build job only).** Redeployed the default instance with sGt's original vars (after `bundle summary` showed `1079028753739581` / `557464573384466` / `818046072228128`). Generated 40 tasks with `main`'s `waves_manifest.py` from sGt `waves.json` at `f3583c3` (the version setup run `541168640326389` used; `01cd9b9` archives 4-0..4-3 and was not used) and the run's automation IDs, then applied them with `jobs/reset` and restored the parameter defaults (`branch=mg-genie-build-4`, sGt `build_root` / `manifest_path`). Read-back: same 40 keys as run `110489694161084`, no differences in dependencies, `run_if` or task specs, timeouts and retries match the pre-incident job, no `build_verdict`. The repair from `w4-4_integrate` has not been tried yet. The smoke job is still the placeholder; the next sGt setup run regenerates it.
   2. Confirm which sGt instance is canonical: the default instance (jobs `1079028753739581` / `557464573384466` / `818046072228128`, which ran build 4) or `-sgt-root` (`551874922778444` / `105657567456728` / `468323402073052`).
   3. Decide who owns jobs `1079028753739581`, `818046072228128` and `557464573384466`. The default and `-smoke` states both reference them; keep one and unbind or delete the other.
   4. Then redeploy sgt-root from a clean cache and confirm its own job IDs.

## Tests (2026-10-26)

* **Unit:** `tests/test_instance_guard.py`, 18 tests: path matching (including the `-smoke` prefix trap), summary/state ID parsing, the incident (first deploy with a foreign cache; redeploy of the `-smoke` state), owner redeploy and clean first deploy pass, deleted jobs, latest-run-only history, the setup guard after the bad deploy (only the history check fires), optional setup inputs, `force`, the cache move (one backup) and the post-deploy check. Full suite: 83 passed. `bundle validate --strict` passes.
* **Live, `--check-only`:** sGt default instance passes (summary = remote state = `1079028753739581` / `557464573384466` / `818046072228128`); `-sgt-root` passes with its own IDs; `-smoke` is refused with 4 problems (smoke and setup jobs deployed from the default root, build job manifest default, latest run `110489694161084` used sGt's manifest).
* **Live, throwaway instances (shell CLI):** `-iso-a` deployed with the script created `241604026886178` / `323419435946288` / `780349073334800`. With `-iso-a`'s cache present, a plain `bundle summary` for `-iso-b` showed `-iso-a`'s IDs (bug reproduced); the script with `--keep-cache --check-only` refused it with 5 problems. The script without `--keep-cache` deployed `-iso-b` as new jobs `927439263840019` / `434544607772029` / `632159916325954`, and `-iso-a`'s three jobs were identical before and after (name, metadata path, parameters, tasks). Owner re-checks for both pass.
* **Setup guard, against live jobs:** the cell's code, run with the values the job passes: owners (`-iso-a`, sGt) pass; sGt with the old setup parameters skips the root/name/setup checks and passes; the incident (smoke manifest and root on the sGt jobs) raises 7 problems; `force=true` continues.
* **Not tested:** a real setup job run with the new parameters (so `{{job.id}}` resolution is checked only against the docs), the plain-CLI bad deploy onto the throwaway jobs, and the Genie Code CLI tool path (its cache cannot be inspected). The six `-iso-a` / `-iso-b` jobs and their remote state folders still need deleting.

## Related

* `docs/sessions/2026-10-26_visible-failures.md` (the `-smoke` deploy at 06:24 on commit `0bda04e`).
* Semantic Ground Truth: `docs/sessions/2026-10-26_agent-skills-volume-otel-grants.md`; build 4 run `110489694161084`.
* `.scratch/smoke-waves.json`: the manifest the bad deploy wrote into the job defaults.
