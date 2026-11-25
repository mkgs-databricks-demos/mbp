# 2026-11-24 — Wave 0-0 / Session 01: SDK Foundation & Input Contract

* Build run: job `419885870201924`, run `701596191246320`, task `w0-0_session`, continuation 0
* Mode: `edit` (`allow_execute: true`), workflow `hybrid`, branch `mg-genie-ontology-modeled-knowledge-sdk` (verified read-only via the Repos API; head `1900ef6e01a0`)
* Status: **pass**

## Changes

| File | What |
|---|---|
| `pyproject.toml` | `genie-ontology-sdk` 0.0.1, setuptools `src` layout, deps `pyyaml`, `jsonschema`, `databricks-sdk`; `test` extra `pytest`; package data `schemas/*.json`; pytest `pythonpath = ["src"]`, `testpaths = ["tests"]` |
| `src/genie_ontology_sdk/__init__.py` | `__version__ = "0.0.1"`, module list docstring; no eager submodule imports |
| `src/genie_ontology_sdk/schemas/sdk_config.schema.json` | Draft 2020-12 schema: required `target_catalog`, `target_schema`, `domain_name` (snake_case), `domain_context`; `anyOf` at least one non-empty `source_catalogs` / `source_schemas` / `source_tables`; optional keys per plan; `additionalProperties: false` |
| `src/genie_ontology_sdk/config.py` | `SdkConfig` (+ `to_dict`), `load_schema`, `load_config` (JSON or YAML), `config_from_dict` (raises `ValueError` listing all problems), `validate_config`, `check_access` (never raises), `expand_tables` |
| `tests/conftest.py` | `FakeWorkspaceClient` (in-memory catalogs/schemas/tables/volume dirs, `FakeNotFound`), fixtures `fake_ws`, `tpch_config`; constants `TPCH_TABLES`, `TPCH_CONFIG` |
| `tests/test_config.py` | 23 test functions (31 collected with parametrization) |
| `docs/design/sdk-layout.md` | Repo tree, ownership by session, conventions, input contract summary |

## Decisions

* **Friendly missing-source message.** The schema `anyOf` error is translated by `validate_config` into `config: at least one of source_catalogs, source_schemas, source_tables must be a non-empty list`.
* **Name shape checks in Python, not the schema:** `source_tables[i]` must be 3-part, `source_schemas[i]` must be 2-part (`catalog.schema`). The 2-part schema rule is needed for `ws.schemas.get(full_name)` and `ws.tables.list(catalog_name, schema_name)`; it goes slightly beyond the plan's literal text (recorded as an assumption).
* **Extra optional keys:** `repo_path` (L100 input) and `$schema` are allowed alongside the plan's optional keys, because `additionalProperties: false` would otherwise reject an L100-shaped config. Session 09 (`scaffold`) should write only schema keys.
* **`to_dict` omits `None` and empty lists** so it round-trips through `validate_config` (empty source lists would fail `minItems`).
* **`check_access`** checks existence/readability only (catalog, schema, table `get`; target catalog; `source_catalog_for_reads`; volume dirs via `files.list_directory_contents`, consuming the first item so lazy iterators really call the API). Fine-grained privileges (`CREATE SCHEMA`, `SELECT`) are not checked; an access error from `get` is reported the same way. Dashboard inputs that look like files are checked via their parent directory.
* **`expand_tables`** skips `information_schema`, dedupes and sorts; API errors propagate (run `check_access` first).
* Placeholders `main` / `ontology_tpch` come from the INDEX TPC-H config; no other catalogs besides `samples`.

## Checks

| Check | Result |
|---|---|
| Gate pytest (`cp -r build_root /tmp/gos-gate && pip install -q pyyaml jsonschema pytest && python -m pytest -q`) | pass — 31 passed |
| `tests/test_config.py` has >= 8 tests | pass — 31 collected |
| `PYTHONPATH=src python -c 'import genie_ontology_sdk, genie_ontology_sdk.config'` | pass (exit 0) |
| Schema rejects no-source config, accepts INDEX TPC-H config | pass (`test_schema_rejects_config_with_no_source_inputs`, `test_schema_is_draft_2020_12_and_accepts_tpch_config`) |
| No workspace-specific values in owned files (grep for hosts, user names, workspace catalogs) | pass — none found |

First run had 1 failure: a test appended a duplicate to `source_tables`, which the schema correctly rejects (`uniqueItems`). Fixed the test to exercise dedup via overlapping `source_schemas` instead.

## Notes for later sessions

* Import shared fakes with `from conftest import FakeWorkspaceClient, TPCH_CONFIG, TPCH_TABLES` or use fixtures `fake_ws` / `tpch_config`. Request changes to `conftest.py` through your status file.
* Python on serverless is 3.12; the package targets >= 3.11.

## Requests

None.
