# Session 23: Wheel, Entry Points & Versioning (R2)

## Scope
Ship the SDK as a versioned pure-Python wheel with `gos-*` commands; bundles and notebooks install the wheel instead of using vendored copies or `sys.path` edits. No deploy.

## Context
* [REQUESTS R2](REQUESTS.md#r2-ship-a-wheel-instead-of-vendored-modules); review gaps G1, G2, G7.
* Session 21 already changed both templates and `scaffold.py` (wave 1-1); build on its result.
* The wheel reaches a workspace through a **bundle-managed volume** `sdk_wheels` in the metric-views template (declared under the schema resource), so no owner-created volume is needed. Session 30 uploads the wheel after the first deploy.

## Tasks
1. Version `0.1.0`: `__init__.__version__` from `importlib.metadata`, setuptools reads it once; `CHANGELOG.md` (0.1.0 = build-1 changes, 0.0.1 = build-0).
2. `[project.scripts]`: `gos-check-config`, `gos-validate-mv`, `gos-build-manifest`, `gos-render-agents`, `gos-scaffold`, `gos-resolve-target`, `gos-benchmark`. `python -m` keeps working.
3. Metric-views template: `sdk_wheel` variable (default `/Volumes/${var.catalog}/<schema>/sdk_wheels/genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl`, schema through `${resources.schemas.<name>.name}`), the `sdk_wheels` volume resource, job environment `dependencies: [${var.sdk_wheel}]`; notebooks import `genie_ontology_modeled_knowledge_sdk`.
4. `scaffold_project(..., vendor=False)`: no vendored folder by default; `vendor=True` writes it plus `VENDORED_VERSION`; a test fails when a vendored copy differs from the SDK at that version.
5. `notebooks/init_ontology_project.ipynb`: install cell `%pip install <wheel path or version>` + `dbutils.library.restartPython()`; remove the `sys.path` bootstrap.
6. CI workflow: add a `wheel` job that builds and uploads the wheel as an artifact.
7. `tests/test_wheel.py`: builds the wheel into a temp dir and checks the entry points and package data (`schemas/*.json`) are present.

## Acceptance Criteria
- [ ] Gate checks `wheel` and `no_vendored_paths` pass (vendored paths in `skills/` are removed by sessions 24-26 in the same wave).
- [ ] `validate_bundles` for the metric-views template passes.
- [ ] Scaffold tests: default writes no vendored folder; `vendor=True` passes the drift test.

## Owned Paths
- `pyproject.toml`, `CHANGELOG.md`, `src/genie_ontology_modeled_knowledge_sdk/__init__.py`, `src/genie_ontology_modeled_knowledge_sdk/scaffold.py`
- `templates/ontology-metric-views/**`, `notebooks/init_ontology_project.ipynb`
- `tests/test_wheel.py`, `tests/test_scaffold.py`, `tests/test_template_mv_bundle.py`, `ci/github/workflows/genie-ontology-modeled-knowledge-sdk-ci.yml`

## Dependencies
- Sessions 18 (floor, CI), 21 (templates, scaffold).
