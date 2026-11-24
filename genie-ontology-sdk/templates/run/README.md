# Run Kit — running the Genie Ontology pipeline with genie-build-waves

This folder is the run kit template. `genie_ontology_sdk.scaffold.scaffold_project` copies it into a new project and replaces the `{{project_name}}`, `{{domain_name}}` and `{{bundle_target}}` tokens:

| Template file | Lands in the project at |
|---|---|
| `waves.json`, `INDEX.md`, `README.md`, `plans/*.md` | `docs/plans/` (plan files keep the `plans/` sub-folder, matching `plan_file` in the manifest) |
| `PROJECT_MEMORY.md` | project root |

The kit holds no workspace-specific values. Hosts, catalogs, warehouses, groups and ids come from the bundles' gitignored `variable-overrides.json` files and from the genie-build-waves instance settings.

## Waves

See [INDEX.md](INDEX.md). There are 7 waves: `0` inputs check, `1` discovery (research, context and EDA in parallel), `2` metric view synthesis, `3` registration (deploy), `4` UC Pages + agent curation, `5` agent deployment (deploy), `6` tuning (deploy).

## Running a build

1. **Scaffold** the project with the SDK's `notebooks/init_ontology_project` notebook (or `scaffold_project`). Put it in a Git folder on a feature branch, never `main`.
2. **Owner prerequisites:** write `ontology-metric-views/.databricks/bundle/<target>/variable-overrides.json` and `ontology-genie-agents/.databricks/bundle/<target>/variable-overrides.json` (keys in each bundle README). Commit the scaffolded files on the feature branch.
3. **Deploy a genie-build-waves instance** for this project, following the genie-build-waves README. Point it at:
   * `build_root` = the project root (the folder with `sdk_config.json`)
   * `manifest_path` = `<build_root>/docs/plans/waves.json`
   * `branch` = the feature branch
   * the SDK skills: publish or copy `skills/ontology-*` so that build sessions can load them (`skills` overrides in the manifest, or the workspace skills folder of the job's run-as user)
4. **Run setup**, then check that `validate_manifest` reports 0 errors. Setup renders each session's `authorizations` into its prompt. Review them: sessions 06 and 10 are approved to run `register_metric_views`, and session 07 to write UC Pages.
5. **Start the build job.** Watch each wave's gate. Waves `3`, `5` and `6` need the required checks `registration_job`, `mv_smoke`, `agent_probe` and `benchmark_results`.
6. **Review and merge** the feature branch PR yourself. Sessions and the integrator never push to `main`.

## Re-runs

Re-running the build regenerates outputs (design decision: full regeneration). To redo only part of it, run the job with `only` set to the wave task keys you need, e.g. waves `5`-`6` after a metric view fix.

## Validating the template

`tests/test_run_kit.py` in the SDK renders this template with sample values and checks:

* genie-build-waves `validate_manifest` returns 0 errors (skipped if genie-build-waves cannot be found)
* every `plan_file` exists
* owned paths are disjoint within each wave
* the plans contain no Git write commands and no leftover tokens

The test looks for genie-build-waves in `$GENIE_BUILD_WAVES_DIR`, then in a `genie-build-waves` folder next to the SDK (or next to any of its parent folders).
