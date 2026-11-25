# 2026-11-25 - Wave 1-1, session 21: templates and scaffold (required consumer_group, resolved target)

Run `1057400752545739`, branch `mg-genie-ontology-build-1-plan` (checked read-only), mode `edit`. No Git writes, no deploy. R4.3, R4.4, review gap G9, build-0 observations 27 and 28, and the session 06 note (`warehouse_id` required but unused).

## Changes

* **Required `consumer_group` (task 1):** removed the `account users` default from both `templates/ontology-metric-views/databricks.yml` and `templates/ontology-genie-agents/databricks.yml`. The descriptions now say Required, and both READMEs and their overrides examples name the group. Without it, `bundle validate --strict --target dev` fails with `Error: no value assigned to required variable consumer_group` (seen on both templates).
* **Optional `warehouse_id` (task 2):** the metric-views template now has `default: ""`. The dev placeholder `<set-in-variable-overrides>` is gone. The README says no job task uses it (every task runs on serverless): it is only for ad hoc checks, and it is copied into `resolved_target.json`.
* **New `src/genie_ontology_modeled_knowledge_sdk/targets.py` (task 3):**
  * `resolve_target(bundle_dir, target="dev", *, runner=None, schema_key="ontology_schema", extra_args=(), now=None)` runs `databricks bundle summary -o json --target <t>` in the bundle folder. The runner is injectable.
  * `target_from_summary(summary)` reads `resources.schemas.ontology_schema.{catalog_name,name}`, or the only schema if the bundle has exactly one. `warehouse_id` comes from `variables.warehouse_id.value`, and an empty value becomes `null`. Missing or unresolved `${...}` values raise `ValueError`.
  * `write_resolved_target(path, data)` writes exactly the keys `catalog, schema, warehouse_id, source, resolved_at`.
  * CLI: `python -m genie_ontology_modeled_knowledge_sdk.targets resolve --bundle <dir> --target dev --out <path> [--var k=v]`.
* **Registration notebook (task 4):** the exit summary of `notebooks/register_single_mv.ipynb` now also has `catalog` and `schema` (the target widgets), so the run output carries the resolved target. The cell is titled "Exit with summary and resolved target".
* **Agents README (task 5):** step 2 now resolves first (`targets resolve --bundle ../ontology-metric-views ...`), then runs `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check`.
* **`scaffold.py` (task 6):**
  * `render_schema_name(text, schema_name)` sets the `schema_name` variable default in `ontology-metric-views/databricks.yml` to `sdk_config.target_schema`. Names that are not plain identifiers are JSON-quoted, and `ValueError` is raised if the block is missing.
  * `PLACEHOLDER_FILES` (`ontology-genie-agents/agents/ontology_agent.geniespace.json`) is no longer copied. `agents/.gitkeep` is written instead.
  * The no-overwrite rule and the protected dirs are unchanged.
* **Tests (task 7):**
  * New `tests/test_targets.py`: fake runner, dev-prefixed and non-dev summaries, errors, CLI.
  * `tests/test_scaffold.py`: placeholder not copied; `schema_name` rendered, and only that line differs from the template; quoting and errors.
  * Template tests: no default group, optional warehouse, README content, notebook exit keys.

## Decisions

* `resolve_target` takes `catalog`/`schema` from the summary's resource config (`catalog_name`, `name`; in development mode `name` already carries the `dev_<user>_` prefix). It does not use the resource `id`: in a real `bundle summary` of the template, `id` was `hls_fde_dev.dev_matthew_giglia_ontology` while `catalog_name` was `main`, because the `id` came from an earlier deploy's state.
* `warehouse_id` is `null` (not `""`) when unset.
* The scaffolded `ontology-genie-agents/resources/genie_agents.yml` still has the `ontology_agent` entry. A fresh project's agents bundle therefore does not validate until curation writes agents and replaces that entry (documented in the agents README).

## Checks

| Check | Result |
|---|---|
| pytest, 4 session-21 test files (/tmp copy) | pass: 69 passed |
| pytest, full suite (/tmp copy) | fail: 334 passed, 4 failed, all in `tests/test_geniespace.py` (not owned by this session; `geniespace.py` shows as modified in `git status`, which suggests session 19's work in progress, but I did not investigate the cause) |
| `ruff check .` and `ruff format --check .` | pass (30 files formatted) |
| `mypy src` | pass (9 source files) |
| consumer_group_required: metric-views template, `bundle validate --strict --target dev` without `consumer_group` | pass: fails naming `consumer_group` |
| metric-views template validate with `--var consumer_group=example_group` | pass: Validation OK |
| agents template validate without / with `consumer_group` | fails naming `consumer_group` / Validation OK (uses its existing gitignored scratch overrides and `.rendered/`) |

## Assumptions and requests

* Assumption: session 19's `geniespace render --params` reads the keys `catalog`, `schema`, `warehouse_id` from `resolved_target.json` and accepts a `null` `warehouse_id`.
* Session 19 (or the integrator): the 4 `tests/test_geniespace.py` failures must be fixed before the wave 1-1 `pytest` gate can pass.
* Owner: the template's gitignored scratch overrides `templates/ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json` has no `consumer_group`, so plain `bundle validate` there now needs `--var consumer_group=...`. I did not edit it.
* Owner / P1-4: both TPC-H `variable-overrides.json` files need `consumer_group` (already planned).
* Session 25 (curation skill): when agents are written, replace the template's `ontology_agent` entry in the project's `resources/genie_agents.yml`.

## Repair run 109257611554257 (re-validation)

The wave 1-1 gate of run `1057400752545739` failed only because this session reported `blocked`: the full-suite failures it saw in `tests/test_geniespace.py` came from session 19's work in progress at the time, and the gate itself measured 403 passed. In this run the 11 files above were still uncommitted in the working tree (inherited; `git status` showed exactly these). I made no code changes; I re-ran every check on the current tree.

| Check | Result |
|---|---|
| Branch (read-only) | `mg-genie-ontology-build-1-plan` |
| pytest, full suite (/tmp copy) | pass: 402 passed, 1 skipped (`tests/test_run_kit.py`: genie-build-waves not next to the /tmp copy) |
| pytest, 4 session-21 test files | pass: 69 passed |
| `ruff check .`, `ruff format --check .`, `mypy src` | pass |
| consumer_group_required: metric-views template validate --strict --target dev without `consumer_group` | pass: fails with `no value assigned to required variable consumer_group` |
| metric-views template validate with `--var consumer_group=example_group` | pass: Validation OK |
| agents template validate without / with `consumer_group` | fails naming `consumer_group` / Validation OK |
| `target_from_summary` on a fake dev summary | pass: `{catalog: main, schema: dev_jane_doe_ontology, warehouse_id: null}` |

The previous request to session 19 is resolved. The owner request (scratch overrides need `consumer_group`) and the session 25 request still stand.

## Files modified

`templates/ontology-metric-views/{databricks.yml,README.md,notebooks/register_single_mv.ipynb}`, `templates/ontology-genie-agents/{databricks.yml,README.md}`, `src/genie_ontology_modeled_knowledge_sdk/{scaffold.py,targets.py}`, `tests/{test_targets.py,test_scaffold.py,test_template_mv_bundle.py,test_template_agent_bundle.py}`.
