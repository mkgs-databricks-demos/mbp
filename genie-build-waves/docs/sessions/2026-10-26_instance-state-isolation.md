# 2026-10-26: Instance state isolation (shared local state cache)

Branch: `mg-genie-build-waves-visible-failures-plan` (same PR as the visible-failures work). Bug report and full evidence: [docs/plans/2026-10-26_instance-state-isolation.md](../plans/2026-10-26_instance-state-isolation.md).

## Problem

To smoke-test the visible-failures changes on a separate instance, I deployed with `instance_suffix=-smoke` through the Genie Code CLI tool. The deploy reported "0 created, 3 changed": it bound to the default instance's jobs, which ran Semantic Ground Truth build 4 (`1079028753739581` build, `557464573384466` smoke, `818046072228128` setup). It renamed them `Build Waves Smoke: …`, reset the build job to the placeholder and pointed the defaults at `.scratch/smoke-waves.json`, so run `110489694161084` could no longer be repaired. Setup was not run, so no skills or automations changed.

## Root cause

`instance_suffix` changes only `workspace.root_path`, which isolates the remote state. The CLI's local state cache is per target, not per root, and is shared by every instance deployed from the folder. With no remote state for the new instance, the cached state of another instance wins and its job IDs are updated. The folder cache held AgenticTrading's state (a `-sgt-root` deploy from the shell would have taken over AgenticTrading next); the CLI tool used a separate cache that held the default instance's state. Reproduced with two throwaway instances on the shell CLI.

## Changes

* **Recovery (user approved):** redeployed the default instance with sGt's original vars after checking `bundle summary`, then reset the build job to the 40 tasks generated with `main`'s `waves_manifest.py` from sGt `waves.json` at `f3583c3` and the run's automation IDs. Read-back: same keys and specs as run `110489694161084`, no `build_verdict`.
* **Folder cache** moved aside to `.databricks/bundle/dev.bak-20261026T073033Z` (AgenticTrading state, kept as evidence).
* **Fix 1:** new `src/notebooks/instance_guard.py`: job `deployment.metadata_file_path` under the instance root, summary IDs vs remote `state/resources.json` (none allowed on a first deploy), build job manifest default and latest run manifest, optional job-name check.
* **Fix 2:** new `scripts/deploy_instance.py --target --vars [--check-only] [--force] [--keep-cache]`: moves the cache aside (one `<target>.bak`), checks, deploys, checks again, clears the cache again.
* **Fix 3:** setup cell "Instance ownership guard" (after "Validate manifest", before publishing), raising `INSTANCE_GUARD_FAILED` unless `force=true`. `setup_build_waves.job.yml` passes `bundle_root_path`, `project_name`, `setup_job_id` (`{{job.id}}`) and a new `force` job parameter; older setup jobs skip those checks and still run the manifest and run-history checks.
* **Fix 4:** README section 2 deploys with the script and a vars file; "One deployment per project" explains the cache, the plain-CLI `bundle summary` check, not deploying with the Genie Code CLI tool, and `force=true`.
* **Tests:** `tests/test_instance_guard.py` (18). Full suite 83 passed; `bundle validate --strict` passes.

## Live verification

* `--check-only`: sGt default and `-sgt-root` pass with their own IDs; `-smoke` refused (4 problems).
* `-iso-a` deployed with the script (new jobs `241604026886178` / `323419435946288` / `780349073334800`). With its cache present, a plain `bundle summary` for `-iso-b` listed `-iso-a`'s IDs; the script with `--keep-cache` refused it (5 problems); without it, `-iso-b` deployed as new jobs (`927439263840019` / `434544607772029` / `632159916325954`) and `-iso-a`'s jobs were unchanged.
* Setup guard cell code against live jobs: owners pass, old parameters skip and pass, the incident raises 7 problems, `force` continues.
* Not run: a real setup job (guardrail; `{{job.id}}` checked against the docs only) and a deliberate plain-CLI bad deploy.

## Decisions

* Python script instead of the planned `.sh`, so the wrapper shares the guard and is unit tested.
* History check uses only the build job's latest run, because sGt legitimately changed its manifest path earlier (run `713417549836954`).
* The setup guard is defence in depth: after a bad deploy the names, defaults and metadata match the new instance, so only the run history shows the takeover.

## Open

* Delete the six throwaway `-iso-a` / `-iso-b` jobs and `.bundle/genie-build-waves-iso-a`, `-iso-b` (blocked by the guardrail; needs approval).
* The `-smoke` remote state still references the sGt jobs; the guard now refuses it, but delete `.bundle/genie-build-waves-smoke` or unbind it.
* sGt: repair run `110489694161084` from `w4-4_integrate` (after the session 36 rerun); do not run sGt setup until then. The sGt smoke job is still the placeholder.
* Report cleanup steps 2–4: which sGt instance is canonical, job ownership, redeploy `-sgt-root` with the script.
* After merge: deploy each instance with `scripts/deploy_instance.py`, then run setup (so the new guard parameters reach each setup job).

## Files

* `src/notebooks/instance_guard.py` (new)
* `scripts/deploy_instance.py` (new)
* `tests/test_instance_guard.py` (new)
* `src/notebooks/setup_build_waves_job.ipynb`
* `resources/setup_build_waves.job.yml`
* `README.md`
* `docs/plans/2026-10-26_instance-state-isolation.md` (new)
* `docs/sessions/2026-10-26_instance-state-isolation.md`, `docs/sessions/INDEX.md`
