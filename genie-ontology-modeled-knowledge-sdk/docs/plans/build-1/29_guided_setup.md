# Session 29: Guided Setup Notebook (R6)

## Scope
One notebook that takes a customer from inputs to a ready-to-run project: prerequisite checks, scaffold, both overrides files from the same inputs, skills reference, genie-build-waves vars file, and a final checklist.

## Context
* [REQUESTS R6](REQUESTS.md#r6-one-guided-setup-notebook); review gap G8; build-0 note "09: init default `main` is not accessible everywhere".
* Session 28 owns `scaffold.py`, `config.py` and schemas in this wave: put new logic in `setup_project.py` and call scaffold's public API only. If you need a scaffold change, record a request to session 28 in your summary.
* Never write into the SDK's own `examples/`; tests and manual tries use `/tmp` scratch projects.

## Tasks
1. `setup_project.py`:
   * `check_prereqs(ws, inputs) -> list[Check]`: catalog access and CREATE SCHEMA, warehouse exists and is usable, target folder is a Git folder on a non-`main` branch, skills schema and the six skills exist (from `sdk_config.skills`), Pages domain readable if set;
   * `write_overrides(project_dir, inputs, force=False)`: both `variable-overrides.json` files with the same catalog and the resolved schema rule (dev prefix), `consumer_group`, `warehouse_id`; never overwrites edited files without `force`;
   * `write_vars_file(path, inputs)`: the genie-build-waves instance vars file outside the repository;
   * `checklist(state) -> str`.
2. `notebooks/init_ontology_project.ipynb`: empty widget defaults; an `example` dropdown (`none`, `tpch`) that loads `examples/tpch/sdk_config.json`; does nothing until required inputs are set; prints the deploy, setup and run commands exactly.
3. `docs/usage.md`: the guided path first; manual steps as an appendix.
4. `tests/test_setup_project.py`: fake clients; overrides match; second run no change; `force` behavior.

## Acceptance Criteria
- [ ] Gate check `guided_setup` passes.
- [ ] No shipped notebook contains `sys.path` edits or a hard-coded catalog default.

## Owned Paths
- `notebooks/init_ontology_project.ipynb`, `src/genie_ontology_modeled_knowledge_sdk/setup_project.py`, `tests/test_setup_project.py`, `docs/usage.md`

## Dependencies
- Sessions 21, 23, 27.
