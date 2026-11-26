# Changelog

All notable changes to the Genie Ontology Modeled Knowledge SDK. The version has one source, `pyproject.toml`; `genie_ontology_modeled_knowledge_sdk.__version__` reads it (see `tests/test_version.py`).

## 0.1.1 (build 1, republished 2026-11-26)

The 0.1.0 wheel was published in wave 1-2b and not rebuilt afterwards; 0.1.1 is the first wheel built from the full build-1 source.

* Adds the modules missing from the 0.1.0 wheel: `setup_project` (guided setup, prerequisite checks, overrides and vars files) and `skills_publish` (Unity Catalog skills publishing).
* `benchmark`: the verdict comes from `assessment`; `manual_assessment` is only a flag (0.1.0 scored every result BAD).
* `pages`: synonyms are compared order-insensitively (the Pages API stores them sorted), so a second upsert changes nothing.
* Consumer access per target through complex grant variables (`schema_grants`, `agent_permissions`, `sdk_schema_grants`, `sdk_volume_grants`): the deploying developer in `dev`, `account users` elsewhere, overridable per target; setup takes `readers` / `curators` and checks that groups are account-level.
* Templates and the TPC-H dogfood pin `sdk_version` `0.1.1` (an SDK bundle deploy replaces the volume's artifacts, so the 0.1.0 file is gone).
* The SDK bundle's wheel build removes `build/` and `dist/` first; a stale `build/lib` had shipped old module copies.

## 0.1.0 (build 1)

* Shipped as a versioned pure-Python wheel (`genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl`), built by the SDK bundle's `artifacts.sdk_wheel` block and uploaded to the SDK bundle's `sdk_wheels` volume (`workspace.artifact_path`).
* Console scripts: `gos-check-config`, `gos-validate-mv`, `gos-build-manifest`, `gos-render-agents`, `gos-scaffold`, `gos-resolve-target`, `gos-benchmark` (`python -m genie_ontology_modeled_knowledge_sdk.<module>` keeps working).
* `sdk_smoke` job in the SDK bundle: installs the built wheel through a job environment and exits with `__version__`.
* Metric-views template installs the pinned wheel through a job environment (`sdk_version`, `sdk_wheel_subpath`, `sdk_volume_path`, `sdk_wheel`).
* `scaffold_project(..., vendor=False)` by default; `vendor=True` copies the import closure of the SDK modules the template notebooks import and writes `VENDORED_VERSION`.
* Library and template fixes from build-1 waves 1-0 and 1-1 (CI, lint/type config, `databricks-sdk>=0.45.0` floor, SDK bundle, geniespace split and render, domain-scoped pages, required `consumer_group`, `targets.resolve_target`, benchmark library).

## 0.0.1 (build 0)

* First build: `config`, `mv_yaml`, `manifest`, `geniespace`, `pages`, `benchmark`, `scaffold`, six `skills/ontology-*`, two bundle templates, the run kit and the TPC-H dogfood. Distributed by vendoring modules into projects.
