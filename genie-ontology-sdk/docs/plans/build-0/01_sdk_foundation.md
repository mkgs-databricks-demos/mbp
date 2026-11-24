# Session 01: SDK Foundation & Input Contract

## Scope
Create the Python package skeleton `src/genie_ontology_sdk/`, `pyproject.toml`, the input-contract module `config.py` with its JSON schema, the pytest scaffold, and `docs/design/sdk-layout.md`. Every later session builds on these files.

## Context
* Input contract: L100 "Inputs & Interface Contract" and [L200-A](../../design/L200-A-input-validation.md) (validation rules table).
* Reference only: [l300-pipeline/01_input_validation_scaffolding.md](../../design/l300-pipeline/01_input_validation_scaffolding.md). Do **not** copy its `git checkout -b` step: build sessions never run Git.
* Contracts every session relies on are in [INDEX.md](../INDEX.md#cross-session-contracts). Implement them exactly.
* Pure Python 3.11+, no Spark imports in library modules. Databricks access goes through an injected `WorkspaceClient`, so tests can pass a fake.
* Tests: run pytest from a `/tmp` copy of `build_root` (`cp -r <build_root> /tmp/gos && cd /tmp/gos && python -m pytest -q`), because pytest in place on `/Workspace` fails with OSError 95.

## Tasks
1. `pyproject.toml`: project `genie-ontology-sdk`, version `0.0.1`, `src` layout, deps `pyyaml`, `jsonschema`, `databricks-sdk`; optional `test` extra with `pytest`. Configure `[tool.pytest.ini_options] pythonpath = ["src"]`, `testpaths = ["tests"]`.
2. `src/genie_ontology_sdk/__init__.py`: `__version__`, and a module list in the docstring.
3. `src/genie_ontology_sdk/schemas/sdk_config.schema.json`: JSON Schema (draft 2020-12) for the L100 inputs. Required: `target_catalog`, `target_schema`, `domain_name`, `domain_context`, and at least one of `source_catalogs` / `source_schemas` / `source_tables`. Optional: `supplemental_volume_dirs`, `dashboard_inputs`, `source_catalog_for_reads`, `source_schema_for_reads`, `warehouse_id`, `max_metric_views_per_agent` (default 50), `project_root`. `domain_name` is snake_case.
4. `src/genie_ontology_sdk/config.py`:
   * `SdkConfig` dataclass, with `load_config(path)`, `config_from_dict(d)`, `to_dict()`.
   * `validate_config(d) -> list[str]`: schema errors, plus a check that table names have 3 parts.
   * `check_access(cfg, ws) -> list[str]`: the L200-A UC checks via `ws.catalogs/schemas/tables.get` and volume `ws.files.list_directory_contents`. Returns problems; never raises.
   * `expand_tables(cfg, ws) -> list[str]`: catalogs/schemas -> 3-part table names (sorted, unique).
5. `tests/conftest.py`: a `FakeWorkspaceClient` with in-memory catalogs/schemas/tables/volume dirs.
6. `tests/test_config.py`: valid/invalid configs, the missing-source rule, the 2-part-name error, expand_tables, and check_access problem messages.
7. `docs/design/sdk-layout.md`: the repo layout (`src/`, `tests/`, `skills/`, `templates/`, `notebooks/`, `examples/`) and which build-0 session owns each part.

## Acceptance Criteria
- [ ] `python -m pytest -q` (from a `/tmp` copy) passes, with at least 8 tests in `tests/test_config.py`.
- [ ] `python -c "import genie_ontology_sdk, genie_ontology_sdk.config"` works with `PYTHONPATH=src`.
- [ ] The schema rejects a config with no source inputs and accepts the TPC-H config from INDEX.md.
- [ ] No workspace-specific values (hosts, catalogs other than `samples`, user names) in any owned file.

## Owned Paths / Assets
- `pyproject.toml`
- `src/genie_ontology_sdk/__init__.py`, `src/genie_ontology_sdk/config.py`, `src/genie_ontology_sdk/schemas/**`
- `tests/conftest.py`, `tests/test_config.py`
- `docs/design/sdk-layout.md`

## Dependencies
- None (first session).
