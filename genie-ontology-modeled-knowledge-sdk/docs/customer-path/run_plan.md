# Customer Path Run Plan: Second Domain (R9)

Proves the customer path on a second domain by following only the published instructions ([docs/usage.md](../usage.md), the guided notebook `notebooks/init_ontology_project`, the [run kit README](../../templates/run/README.md)), the published SDK skills (R1) and the published wheel (R2, `vendor=False`). No hand edits to generated plans or the manifest. Every deviation goes in the [intervention log](#intervention-log).

This is owner prerequisite **P1-6** before wave `1-16`. Build sessions cannot create Git folders, write outside the SDK `build_root` or deploy genie-build-waves instances, so the steps below are run by the owner (or Devin with the owner's hand-off approval). Session 44 reads the result.

## Dataset

| Item | Value |
|---|---|
| Dataset | `samples.bakehouse` (retail franchise sales) |
| Source tables | `samples.bakehouse.sales_transactions` (3,333 rows), `sales_customers` (300), `sales_franchises` (48), `sales_suppliers` (27) |
| Excluded | `media_customer_reviews`, `media_gold_reviews_chunked`: free-text reviews and RAG chunks, not metric-view sources |
| Why | Preferred by plan 43; readable by the build identity (row counts and columns read on 2026-11-26); a small multi-table star (transactions to customers, franchises; franchises to suppliers) in a different domain from TPC-H |
| Inputs | [sdk_config.example.json](sdk_config.example.json): replace `<target_catalog>`, `<target_schema>`, `<warehouse_id>`, `<sdk_catalog>`, `<sdk_schema>` (the guided notebook widgets take the same values) |
| Dry scaffold | Session 43: `scaffold_project(..., vendor=False)` into `/tmp` gave 43 files, 15 waves, 20 sessions, 190 job tasks; `validate_manifest` and `validate_authorizations` 0 errors / 0 warnings; no vendored files; `sdk_version` pinned to `0.1.0` in the metric-views bundle |

## Steps

In the order of `docs/usage.md` steps 0-4 and the guided notebook cells. **Who:** O = owner (or Devin with hand-off approval), B = child build (genie-build-waves sessions).

| # | Step (source) | Who | Expected evidence |
|---|---|---|---|
| 1 | SDK set up once per workspace (usage step 0): `notebooks/setup_sdk`, then `bundle validate --strict`, `bundle deploy`, `bundle run sdk_smoke`, `bundle summary` at the SDK root; publish the six skills with `notebooks/publish_skills` | O | Smoke run prints the SDK version; `bundle summary` shows the SDK schema and `sdk_wheels` volume; six skills listed in the SDK schema. Skip if already done for build-1 (R1/R2) and note it |
| 2 | Prerequisites (usage step 1): target catalog with CREATE SCHEMA, SQL warehouse, Genie enabled, Discover domain if Pages are wanted, Databricks CLI with `genie_spaces` support, a genie-build-waves checkout | O | Recorded catalog, warehouse and (optional) domain; CLI version |
| 3 | Create a **separate** Git folder for the child project on a feature branch, never `main` (usage step 1, notebook prerequisite check) | O | Git folder path and branch; `check_prereqs` Git-folder check `pass` in step 6 |
| 4 | Open `notebooks/init_ontology_project` on serverless; run the install cell; set `sdk_wheel` to the published wheel and run the wheel install cell (usage step 2.1) | O | Notebook prints `SDK <version> from <site-packages>` (not "Developer mode") |
| 5 | Fill the widgets from `sdk_config.example.json` (`domain_name`, `domain_context`, `source_tables`, `target_catalog`, `target_schema`, `warehouse_id`, `max_metric_views_per_agent`), plus `target_dir` (the Git folder), `project_name`, `bundle_target` = `dev`, `vendor` = `false`, `consumer_group`/`readers`, `curators`, `sdk_volume_path`, `sdk_version`, **skills reference** `skills_catalog` / `skills_schema` (the SDK schema), `branch`, optional `pages_domain_id`, `vars_file` (outside the project), `genie_build_waves_dir` (usage step 2.2) | O | Widget values recorded (no secrets) |
| 6 | Run the validation cell: `validate_config`, `check_access`, `check_prereqs` (usage step 2.3) | O | `validate_config: 0 errors`, `check_access: 0 problems`, every prerequisite `pass` (any `action` is an intervention) |
| 7 | Run the scaffold cell: `scaffold_project` (vendor=false), **overrides** for both bundles (`write_overrides`), **vars file** (`write_vars_file`) (usage steps 2.4 and 3) | O | Scaffold report (files written); both `.databricks/bundle/dev/variable-overrides.json` exist and are gitignored; vars file outside the project |
| 8 | Read the checklist cell (usage step 2.5); validate both bundles: metric views `bundle validate --strict --target dev`; agents `gos-render-agents render agents .rendered --params ...` then `bundle validate --strict --target dev` (usage step 3) | O | Both validates exit 0 |
| 9 | Commit the scaffolded files on the feature branch and push (usage step 4, checklist) | O | Commit id on the feature branch; `git status` shows no overrides files |
| 10 | `deploy_instance.py`: `python scripts/deploy_instance.py --target dev --vars <vars file> --check-only`, then without `--check-only` (usage step 4.1) | O | Instance jobs deployed; job ids recorded in the child project's session notes (not here) |
| 11 | Skills: confirm the child sessions load the SDK skills by UC id from the SDK schema (usage step 4.2) | O, B | First child session summary names the UC skill it loaded (or the fallback path) |
| 12 | Setup: `scripts/setup_helper` with `vars_file`, `action=run_setup`; `validate_manifest` 0 errors; review rendered session authorizations (usage step 4.3) | O | Setup output with 0 manifest errors; authorizations reviewed |
| 13 | Run: start the build job from the setup output (`branch`, `build_root`, `manifest_path`) (usage step 4.5) | O | Build job run id |
| 14 | Monitor: watch each wave gate and `required_checks`; Pages wave per usage step 4.4; tuning until the asymptote (run kit waves `8`-`13`); report simulation (wave `14`) | O, B | `.build-status/<run_id>/build_verdict.json` in the child project; every wave `pass` or stopped only on a documented owner prerequisite |
| 15 | Record `customer_path_root` in the SDK's `.local/build-1.json` (P1-6 done-when) and leave the feature branch PR for owner review | O | `.local/build-1.json` has `customer_path_root`; session 44 can read the verdict |

## Intervention log

One row per deviation from the published steps: a manual fix, an unclear instruction, a missing prerequisite, a re-run. Session 44 links each row to a documented prerequisite or a build-2 request.

| # | step | who | what happened | why | fix or prerequisite | link |
|---|---|---|---|---|---|---|

## Known doc gaps found while preparing (session 43)

Recorded for session 44; not interventions yet. Log them above if they bite during the run.

* The notebook does not pass its `branch` widget to `scaffold_project`, so the run kit `waves.json` `branch` defaults to `genie-build-<project_name>` while the vars file uses the `branch` widget. Use a branch named `genie-build-<project_name>` or expect a mismatch.
* The run kit README says to record `skills` (and `pages_domain_id`) in `sdk_config.json`; the notebook takes `skills_catalog` / `skills_schema` / `pages_domain_id` widgets but does not write them into `sdk_config.json`.
* The notebook widget default `max_metric_views_per_agent` = `50` triggers a `config_warnings` warning (agents are split at 30); the example uses `30`.
* usage.md step 2.2 lists a `consumer_group` widget; the notebook widgets are `readers` / `curators`.
