# Changelog

All notable changes to the Genie Ontology Modeled Knowledge SDK. The version has one source, `pyproject.toml`; `genie_ontology_modeled_knowledge_sdk.__version__` reads it (see `tests/test_version.py`).

## 0.1.0 (build 1)

* Shipped as a versioned pure-Python wheel (`genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl`), built by the SDK bundle's `artifacts.sdk_wheel` block and uploaded to the SDK bundle's `sdk_wheels` volume (`workspace.artifact_path`).
* Console scripts: `gos-check-config`, `gos-validate-mv`, `gos-build-manifest`, `gos-render-agents`, `gos-scaffold`, `gos-resolve-target`, `gos-benchmark` (`python -m genie_ontology_modeled_knowledge_sdk.<module>` keeps working).
* `sdk_smoke` job in the SDK bundle: installs the built wheel through a job environment and exits with `__version__`.
* Metric-views template installs the pinned wheel through a job environment (`sdk_version`, `sdk_wheel_subpath`, `sdk_volume_path`, `sdk_wheel`).
* `scaffold_project(..., vendor=False)` by default; `vendor=True` copies the import closure of the SDK modules the template notebooks import and writes `VENDORED_VERSION`.
* Library and template fixes from build-1 waves 1-0 and 1-1 (CI, lint/type config, `databricks-sdk>=0.45.0` floor, SDK bundle, geniespace split and render, domain-scoped pages, required `consumer_group`, `targets.resolve_target`, benchmark library).

## 0.0.1 (build 0)

* First build: `config`, `mv_yaml`, `manifest`, `geniespace`, `pages`, `benchmark`, `scaffold`, six `skills/ontology-*`, two bundle templates, the run kit and the TPC-H dogfood. Distributed by vendoring modules into projects.
