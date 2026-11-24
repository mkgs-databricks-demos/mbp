# Session 09 (wave 0-3): Init Tool & TPC-H Dogfood Scaffold

Run: build run `701596191246320`, task `w0-3_session`, branch `mg-genie-ontology-modeled-knowledge-sdk`, mode `edit` (`allow_execute: true`).

## Changes

* `src/genie_ontology_sdk/scaffold.py`: `scaffold_project(cfg, target_dir, sdk_root, *, force=False, project_name=None, bundle_target="dev") -> ScaffoldReport`, `render_tokens`, CLI `python -m genie_ontology_sdk.scaffold`.
  * Copies `templates/ontology-metric-views` and `templates/ontology-genie-agents`. Copies `templates/run/{waves.json,INDEX.md,README.md,plans/}` to `docs/plans/` (keeping the `plans/` sub-folder, per session 08's request) and `templates/run/PROJECT_MEMORY.md` to the project root.
  * Renders only `{{project_name}}`, `{{domain_name}}`, `{{bundle_target}}`. Jobs dynamic references (`{{input.name}}`, `{{tasks...}}`) and `${...}` are kept.
  * Vendors `mv_yaml.py`, `manifest.py`, `geniespace.py` byte-for-byte into `ontology-metric-views/src/genie_ontology_sdk_vendored/`.
  * Writes `sdk_config.json` (`SdkConfig.to_dict`) and `docs/{research,semantics,context,data_profiles,registration,pages,deployment,tuning,sessions}/.gitkeep`.
  * Never overwrites unless `force`. A file with identical content counts as `unchanged`, so a second run writes 0 files. It never reads or writes `.databricks/` or `.rendered/`, even with `force`.
* `notebooks/init_ontology_project.ipynb`: the install cell (`%pip install --upgrade databricks-sdk pyyaml jsonschema` + `dbutils.library.restartPython()`), overview, one widget per `sdk_config` field plus scaffold options (`target_dir` empty = check only), `validate_config` + `check_access`, `scaffold_project`, then a JSON summary.
* `tests/test_scaffold.py`: 16 tests covering layout, plan files, no run tokens left, preserved Jobs references, vendored files identical, valid `sdk_config`, protected dirs, idempotent second run, skip/force behavior, overrides untouched, bad config, bad sdk root, and the CLI.
* `examples/tpch/`: scaffolded with `scaffold_project` (44 files), plus `examples/tpch/README.md`.

## Decisions

* `project_name` and `bundle_target` are optional keyword-only arguments, so the contract signature still holds. The dogfood uses `project_name="tpch"`.
* In the generic "no `{{` left" test, vendored `.py` files are skipped: their f-strings use `{{ }}` legitimately. A byte-for-byte equality test covers them instead.
* `sdk_config.json` keeps `target_catalog: main` / `target_schema: ontology_tpch` as the documented example values. The real catalog comes only from the gitignored overrides.

## Checks

| Check | Result |
|---|---|
| pytest from a `/tmp` copy of build_root (after the scaffold) | pass: 271 passed, 1 skipped (the skip is session 08's genie-build-waves lookup) |
| `tests/test_scaffold.py` | pass: 16 passed |
| Notebook run on serverless (install, widgets, config, access check) with TPC-H inputs | ran. `check_access` gave 1 problem: `target catalog 'main'` is not accessible in this workspace. All 8 `samples.tpch` tables had 0 problems (the plan criterion) |
| `check_access` with the target catalog from the MV overrides (value not printed) | 0 problems |
| `examples/tpch/sdk_config.json` `validate_config` | 0 errors |
| Second `scaffold_project` run on `examples/tpch` | 0 files written, 44 unchanged |
| `examples/tpch/ontology-metric-views` `bundle validate --strict --target dev` | Validation OK |
| `examples/tpch/ontology-genie-agents` render (exit 0) + `bundle validate --strict --target dev` | Validation OK |
| Overrides files unchanged (sha256 before/after scaffold) | pass |
| Overrides untracked: `git check-ignore` on both, not staged, not in `git status` | pass |

The render step wrote `examples/tpch/ontology-genie-agents/.rendered/ontology_agent.geniespace.json`. It is gitignored (verified) and left in place for the gate.

## Notes and requests

* Gate item "git status shows no tracked or staged variable-overrides.json": the only tracked file with that name is `tests/fixtures/geniespace/variable-overrides.json`, a session 03 test fixture, not an owner overrides file. A gate that greps `git ls-files` by name would match it. Scope the check to `examples/` or `.databricks/` paths.
* The notebook's default `target_catalog` is `main`, which is not accessible in this workspace. Users must set their own catalog, and the access check fails loudly otherwise (intended).

## Files

`src/genie_ontology_sdk/scaffold.py`, `tests/test_scaffold.py`, `notebooks/init_ontology_project.ipynb`, `examples/tpch/README.md`, and the 44 scaffolded files under `examples/tpch/` (listed in the status file).
