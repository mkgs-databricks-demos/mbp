# Session 09: Init Tool & TPC-H Dogfood Scaffold

## Scope
Build `src/genie_ontology_modeled_knowledge_sdk/scaffold.py` and `notebooks/init_ontology_project.ipynb`. They validate inputs, then scaffold a project from `templates/`: both bundles, the run kit, `sdk_config.json`, the docs folders, and a vendored library. Then use them to create the dogfood project `examples/tpch/` for `samples.tpch`.

## Context
* [L200-A](../../design/L200-A-input-validation.md) folder structure; session 01 `config.py`; templates from sessions 06-08.
* Dogfood config, the TPC-H example in [INDEX.md](../INDEX.md#cross-session-contracts):
  * `domain_name: tpch_supply_chain`
  * source tables `samples.tpch.{customer,orders,lineitem,part,partsupp,supplier,nation,region}`
  * `target_catalog: main`, `target_schema: ontology_tpch` as documented example values (the real dev catalog comes from the gitignored bundle overrides at deploy time)
  * `max_metric_views_per_agent: 50`
* Manual prerequisite (owner, before this wave): `examples/tpch/ontology-metric-views/.databricks/bundle/dev/variable-overrides.json` (`catalog`, `warehouse_id`) and `examples/tpch/ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json` (`catalog`, `schema` = the dev-prefixed metric view schema, `warehouse_id`, `curator_group`). Both are gitignored. **Never overwrite or print their values**; the scaffold must skip existing files.
* `samples` is read-only: registration writes into the overrides' catalog. Source references stay `${source_catalog}.${source_schema}` = `samples.tpch` (bundle variables).
* The notebook's first cell is "Install latest Databricks SDK" (`%pip install --upgrade databricks-sdk` + `dbutils.library.restartPython()`), then widgets for every input-contract field, then `validate_config` + `check_access`, then `scaffold_project`, then a summary.

## Tasks
1. `scaffold.py`:
   * `scaffold_project(cfg, target_dir, sdk_root, *, force=False) -> ScaffoldReport`
   * copies `templates/ontology-metric-views`, `templates/ontology-genie-agents`, and `templates/run/*` (into `docs/plans/`, `PROJECT_MEMORY.md`), rendering `{{...}}` tokens
   * vendors `mv_yaml.py`, `manifest.py`, `geniespace.py` into `ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored/`
   * writes `sdk_config.json` and docs folders with `.gitkeep`
   * never overwrites existing files unless `force`; never touches `.databricks/`
2. `notebooks/init_ontology_project.ipynb` as above. Run it on serverless only for the access check with TPC-H inputs: `check_access` must report 0 problems for the 8 `samples.tpch` tables.
3. `tests/test_scaffold.py`: scaffold into `tmp_path`; check the layout, no `{{` left, vendored files identical to `src/`, idempotent second run (0 files written), existing files are skipped.
4. Run `scaffold_project` for TPC-H into `examples/tpch/`. Add `examples/tpch/README.md` (what this dogfood example is, how to reproduce, the overrides files).

## Acceptance Criteria
- [ ] pytest (from a `/tmp` copy) passes, including `tests/test_scaffold.py`.
- [ ] `examples/tpch/` contains `sdk_config.json` (valid per schema), both bundles, `docs/plans/waves.json`, and the vendored library.
- [ ] Both `examples/tpch` bundles pass `bundle validate --strict --target dev` with the owner's overrides (agents bundle after the render step if session 07 chose it).
- [ ] The `variable-overrides.json` files are unchanged and untracked.

## Owned Paths / Assets
- `src/genie_ontology_modeled_knowledge_sdk/scaffold.py`, `notebooks/init_ontology_project.ipynb`, `tests/test_scaffold.py`
- `examples/tpch/**`

## Dependencies
- Sessions 01, 02, 03 (library), 06, 07 (bundle templates), 08 (run kit).
