# Session 08: Pipeline-Run Kit (Run Manifest + Run Plans)

## Scope
Create `templates/run/`: a genie-build-waves manifest template and session plans that run the SDK pipeline for one domain in a user's project. Adapt them from [docs/design/l300-pipeline/](../../design/l300-pipeline/README.md) and fix every known issue. Add a test that renders the template and validates it with genie-build-waves' `validate_manifest`.

## Context
* Reference: [l300-pipeline/waves.json](../../design/l300-pipeline/waves.json), its INDEX and plans 01-10. The issues to fix are in [l300-pipeline/README.md](../../design/l300-pipeline/README.md) and PROJECT_MEMORY findings 1-5 and 13.
* genie-build-waves rules (read `../genie-build-waves/docs/manifest-schema.md`):
  * wave ids use letters, digits, `_`, `-`
  * waves are sequential and sessions within a wave run in parallel
  * `edit` sessions need `owned_paths` (disjoint within a wave)
  * deploying needs `allow_deploy`, with one deployer per wave
  * sessions never run Git; the build branch is a job parameter
  * gates are concrete
* The run kit uses the SDK skills (`skills/ontology-*`, sessions 05a/05b) and the bundles that `scaffold.py` creates in the project (`ontology-metric-views/`, `ontology-genie-agents/`).
* Target run waves:
  * `0` init (edit + allow_execute): check access with `config.check_access`, write `docs/inputs_report.md`
  * `1` discovery, 3 parallel sessions: research -> `docs/research/**` + `docs/semantics/**`; context -> `docs/context/**`; EDA -> `docs/data_profiles/**`
  * `2` MV synthesis -> `ontology-metric-views/metric_views/**`
  * `3` registration (allow_deploy)
  * `4` UC Pages (edit + allow_execute, `docs/pages/**`) parallel with agent curation (`ontology-genie-agents/agents/**`, `ontology-genie-agents/resources/**`, `docs/domain_manifest.yml`)
  * `5` agent deployment (allow_deploy)
  * `6` tuning (allow_deploy)
* Placeholders in the template are double-brace tokens `{{project_name}}`, `{{domain_name}}`, `{{bundle_target}}`, replaced by `scaffold.py` (session 09). No other workspace values.

## Tasks
1. `templates/run/waves.json`: hybrid workflow, `plans_dir: docs/plans`, `context_files` = `sdk_config.json`, `PROJECT_MEMORY.md`, `docs/inputs_report.md`. Use `validate_bundles` for both project bundles on waves 2-6, and `required_checks` for runtime waves (`registration_job`, `mv_smoke`, `agent_probe`, `benchmark_results`).
2. `templates/run/plans/*.md`: one per run session in planner format (Scope, Context, Tasks, Acceptance Criteria, Owned Paths, Dependencies). Each names the skill to load and the SDK functions to call (INDEX.md contracts).
3. `templates/run/INDEX.md` (wave map), `templates/run/PROJECT_MEMORY.md` (starter), `templates/run/README.md` (how to deploy genie-build-waves for a run).
4. `tests/test_run_kit.py`: replace the `{{...}}` tokens with sample values, then import `waves_manifest` from `../genie-build-waves/src/notebooks` (skip with a reason if the folder is absent). Assert `validate_manifest` returns 0 errors, every `plan_file` exists, `owned_paths` are disjoint within each wave (simple glob prefix check), and there is no `git checkout` / `git commit` text in the plans.

## Acceptance Criteria
- [ ] `validate_manifest` on the rendered template: 0 errors (warnings listed in the session summary).
- [ ] pytest (from a `/tmp` copy that includes the sibling `genie-build-waves` folder, or skip documented) passes.
- [ ] Discovery sessions (research/context/EDA) are in one wave with disjoint `owned_paths`.
- [ ] No plan contains Git write commands or workspace-specific identifiers.

## Owned Paths / Assets
- `templates/run/**`
- `tests/test_run_kit.py`

## Dependencies
- Sessions 05a/05b: skill names and output contracts. Session 01: `config.py` API.
