# Session 29: Guided Setup Notebook (R6)

## Scope
One notebook that takes a customer from inputs to a ready-to-run project: prerequisite checks, scaffold, both overrides files from the same inputs, skills reference, genie-build-waves vars file, and a final checklist.

## Context
* [REQUESTS R6](REQUESTS.md#r6-one-guided-setup-notebook); review gap G8; build-0 note "09: init default `main` is not accessible everywhere".
* Session 28 owns `scaffold.py`, `config.py` and schemas in this wave: put new logic in `setup_project.py` and call scaffold's public API only. If you need a scaffold change, record a request to session 28 in your summary.
* Never write into the SDK's own `examples/`; tests and manual tries use `/tmp` scratch projects.

## Tasks
1. `setup_project.py`:
   * `check_prereqs(ws, inputs) -> list[Check]`: catalog access and CREATE SCHEMA, warehouse exists and is usable, target folder is a Git folder on a non-`main` branch, skills schema and the six skills exist (from `sdk_config.skills`), Pages domain readable if set, and (wheel mode) the SDK wheel for the pinned `sdk_version` is readable at the stable path in the SDK volume;
   * `write_overrides(project_dir, inputs, force=False)`: both `variable-overrides.json` files with the same catalog and the resolved schema rule (dev prefix), `consumer_group`, `warehouse_id`, `sdk_volume_path` and `sdk_version` (wheel mode); never overwrites edited files without `force`;
   * `write_vars_file(path, inputs)`: the genie-build-waves instance vars file outside the repository;
   * `checklist(state) -> str`.
2. `notebooks/init_ontology_project.ipynb`: install cell per the repo convention (`%pip install --upgrade databricks-sdk <published wheel or pinned version>` + `dbutils.library.restartPython()`; session 23 wrote it, keep it); empty widget defaults; an `example` dropdown (`none`, `tpch`) that loads `examples/tpch/sdk_config.json`; a `vendor` widget (`false` by default) passed to `scaffold_project(vendor=...)`; does nothing until required inputs are set; prints the deploy, setup and run commands exactly.
3. `docs/usage.md`: the guided path first; a "Getting the SDK" section (R7a): wheel (default; volume, grants, `sdk_version` pin), vendored (opt-in for no package egress or locked-down workspaces; `vendor=True` / `gos-scaffold --vendor`), editable install for SDK development (`pip install -e .`); manual steps as an appendix.
4. `tests/test_setup_project.py`: fake clients; overrides match; second run no change; `force` behavior.

## Acceptance Criteria
- [ ] Gate check `guided_setup` passes.
- [ ] No shipped notebook contains a hard-coded catalog default; the only `sys.path` edit is the init notebook's guarded developer fallback.

## Owned Paths
- `notebooks/init_ontology_project.ipynb`, `src/genie_ontology_modeled_knowledge_sdk/setup_project.py`, `tests/test_setup_project.py`, `docs/usage.md`

## Dependencies
- Sessions 21, 23, 23b, 27.
