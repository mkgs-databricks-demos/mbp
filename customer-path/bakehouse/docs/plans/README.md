# Run Kit — running the Genie Ontology pipeline with genie-build-waves

This folder is the run kit template. `genie_ontology_modeled_knowledge_sdk.scaffold.scaffold_project` copies it into a new project and replaces the `bakehouse`, `bakehouse_retail_sales`, `dev`, `genie-build-bakehouse` (the build feature branch, never `main`) and `0.1.1` tokens. With `vendor=True` it also drops the SDK-wheel prerequisite and records `sdk_distribution: vendored` in `sdk_config.json` (default `wheel`):

| Template file | Lands in the project at |
|---|---|
| `waves.json`, `INDEX.md`, `README.md`, `plans/*.md` | `docs/plans/` (plan files keep the `plans/` sub-folder, matching `plan_file` in the manifest) |
| `PROJECT_MEMORY.md` | project root |

The kit holds no workspace-specific values. Hosts, catalogs, warehouses, groups and ids come from the bundles' gitignored `variable-overrides.json` files and from the genie-build-waves instance settings.

## Waves

See [INDEX.md](INDEX.md). There are 15 waves: `0` inputs check, `1` discovery (in parallel), `2` metric view synthesis, `3` registration (deploy), `4` UC Pages + agent curation, `5` agent deployment (deploy), `6` benchmark authoring (3 parallel sessions), `7` baseline (deploy), `8`-`10` mandatory tuning iterations, `11`-`13` conditional iterations with the asymptote gate on `13`, `14` independent report simulation.

## Running a build

1. **Scaffold** the project with the SDK's `notebooks/init_ontology_project` notebook (or `scaffold_project`). Put it in a Git folder on a feature branch, never `main`.
2. **Owner prerequisites:** write `ontology-metric-views/.databricks/bundle/<target>/variable-overrides.json` and `ontology-genie-agents/.databricks/bundle/<target>/variable-overrides.json` (keys in each bundle README), including `sdk_volume_path` for the SDK wheel (wheel mode: the wheel `0.1.1` is in the SDK `sdk_wheels` volume and the run-as principals have `READ VOLUME`). Set `pages_domain_id` in `sdk_config.json` to an existing Discover domain, or accept the Pages dry run only. Commit the scaffolded files on the feature branch.
3. **Deploy a genie-build-waves instance** for this project, following the genie-build-waves README. Point it at:
   * `build_root` = the project root (the folder with `sdk_config.json`)
   * `manifest_path` = `<build_root>/docs/plans/waves.json`
   * `branch` = the feature branch
   * the SDK skills: publish them to Unity Catalog (SDK `notebooks/publish_skills`) and record `skills` in `sdk_config.json`; sessions load them by id and fall back to `skills/<folder>/SKILL.md` in the SDK checkout. Skills must be published before the build starts
4. **Run setup**, then check that `validate_manifest` reports 0 errors. Setup renders each session's `authorizations` into its prompt. Review them: sessions 06, 09, 11 and 12-17 name their project bundles in `bundle.deploy`; 06 and 12-17 may run `register_metric_views`; 07 and 12-17 may write DRAFT pages in `pages_domain_id`.
5. **Start the build job.** Watch each wave's gate and its `required_checks` (see INDEX.md). If the asymptote is not reached after iteration 6, the wave `13` gate fails and you decide whether to append iterations.
6. **Review and merge** the feature branch PR yourself. Sessions and the integrator never push to `main`.

## Re-runs

Re-running the build regenerates outputs (design decision: full regeneration). To redo only part of it, run the job with `only` set to the wave task keys you need, e.g. waves `5`-`6` after a metric view fix.

## Validating the template

`tests/test_run_kit.py` in the SDK renders this template with sample values and checks:

* genie-build-waves `validate_manifest` and `validate_authorizations` return 0 errors and 0 warnings, and the job task count is under 1,000 (skipped if genie-build-waves cannot be found)
* top-level `branch`, approvals per deploying session, the Pages `manual_prereqs`, at least 3 mandatory iteration waves and the asymptote check; a deliberately broken copy fails
* no import-path instructions (environment variable or interpreter path edits): the kit uses the installed wheel, and the vendored copy is only mentioned for vendor=True
* every `plan_file` exists
* owned paths are disjoint within each wave
* the plans contain no Git write commands and no leftover tokens

The test looks for genie-build-waves in `$GENIE_BUILD_WAVES_DIR`, then in a `genie-build-waves` folder next to the SDK (or next to any of its parent folders).
