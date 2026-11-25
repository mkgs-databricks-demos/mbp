# 2026-11-25 - Wave 1-2, session 23: wheel distribution (partial, in progress)

Run `109257611554257`, branch `mg-genie-ontology-build-1-plan` (checked read-only through the repos API), mode `edit`, continuation 0. No Git writes, no deploy.

## Status

**In progress.** Plan tasks 1-4 are written. Tasks 5-10 are not started. One SDK bundle validate check fails with placeholder vars (see Open problem). A continuation run should start from `progress.next` in the status file.

## Changes so far

* **Task 1, versioning:** `pyproject.toml` `version = "0.1.0"` (single source). `__init__.__version__` reads `pyproject.toml` when the package sits in an SDK source tree (name must match), otherwise `importlib.metadata.version("genie-ontology-modeled-knowledge-sdk")`, else `0+unknown`. New `CHANGELOG.md` (0.1.0 = build 1, 0.0.1 = build 0).
* **Task 2, entry points:** `[project.scripts]` for `gos-check-config`, `gos-validate-mv`, `gos-build-manifest`, `gos-render-agents`, `gos-scaffold`, `gos-resolve-target`, `gos-benchmark`. All point at existing `main()` functions except `gos-check-config`: `config.py` has no CLI and is not owned by this session, so `check_config_main` lives in `__init__.py`.
* **Task 3, SDK bundle:** `artifacts.sdk_wheel` (`type: whl`, `path: .`, build `python -m pip wheel --no-deps --no-build-isolation -w dist .`; the `build` module is not installed on the serverless compute used here). `workspace.artifact_path: ${resources.volumes.sdk_wheels.volume_path}` on all three targets. Sync no longer excludes `notebooks/**`; it excludes only `notebooks/init_ontology_project.ipynb`, so `sdk_smoke.ipynb` syncs. `build/**` and `dist/**` excludes were removed, because `--strict` rejects patterns that match no files.
* **Task 4, smoke job:** `resources/sdk_smoke.job.yml` (serverless, job environment `sdk`, `environment_version: "2"`, dependency `../dist/*.whl`, `environment_key` on the notebook task). `notebooks/sdk_smoke.ipynb` (confirmed `.ipynb` on disk): install cell, then it imports the installed package, fails if it is not under site-packages or if `__version__` differs from the wheel metadata or the optional `expected_version` widget, imports every library module, and exits with `__version__`.

## Checks run

| Check | Result |
|---|---|
| `bundle validate --strict -t dev` (SDK bundle, real gitignored overrides) | pass: `artifact_path` resolved to the dev `sdk_wheels` volume path; smoke dependency rewritten to `./dist/*.whl`; notebook path resolved |
| `bundle validate --strict -t dev` with placeholder `--var` values | **fail**: `volume ci_placeholder.<dev schema>.sdk_wheels does not exist at workspace.artifact_path` |
| pytest, wheel build, installed-wheel tests, vendor modes | not run (tasks 5-10 open) |

## Open problem

The CLI checks that the `/Volumes/...` `artifact_path` exists during validate. The gate check `sdk_bundle_validate` (and CI) validate with placeholder catalog values, so they fail. Options for the continuation: test whether a composed path or a different placement avoids the check, or ask the owner to allow real values (or an existing placeholder volume) for that check. `prod` / `prod_existing_schema` were not validated after the change.

## Not done (plan build-1/23)

Task 5 (metric-views template `sdk_version` / `sdk_wheel_subpath` / `sdk_volume_path` / `sdk_wheel` and job environment), 6 (scaffold `vendor=False` default plus import-closure vendoring), 7 (init notebook guarded dev fallback and install cell), 8 (CI wheel job), 9 (README "Getting the SDK", `docs/distribution/README.md` with CLI version and keys), 10 (`tests/test_version.py`, `tests/test_wheel.py`, `tests/test_sdk_bundle.py` updates: the new job file is top-level `resources:`, so the existing "target-scoped only" assertion will fail until it is narrowed to the schema/volume files; `tests/test_template_mv_bundle.py` must allow `environment_key`).

## Continuation 1 (same run)

Done in this pass:

* **Task 5, template:** `templates/ontology-metric-views/databricks.yml` adds `sdk_version` (default `0.1.0`), `sdk_volume_path` (no default; dev placeholder `/Volumes/main/ontology_sdk/sdk_wheels` next to the other dev placeholders), `sdk_wheel_subpath` (default `.internal`, the CLI's artifact upload sub-folder; 23b confirms it) and `sdk_wheel` (default composed from the three; the CLI accepted variable references in a variable default). The job has environment `sdk` (`dependencies: [${var.sdk_wheel}]`) and `environment_key: sdk` on all four tasks, including the forEach inner task, plus a commented `libraries: [{whl: ...}]` block for classic compute. `load_sdk()` unchanged.
* **Task 6, scaffold:** `scaffold_project(..., vendor=False)`. Default: the template's vendored folder is not copied at all. `vendor=True`: copies `vendored_modules(sdk_root)` (import closure parsed from the template notebooks' code cells and the modules' own SDK imports; today `manifest.py`, `mv_yaml.py`) plus README and `VENDORED_VERSION`. `VENDORED_MODULES` was removed. CLI `--vendor`.
* **Task 10 (part):** `tests/test_scaffold.py` (default vendors nothing, default notebooks resolve the installed package, closure, vendored copies identical and closed), `tests/test_template_mv_bundle.py` (new vars, dev placeholder, `environment_key` allowed, job environment test), `tests/test_sdk_bundle.py` (job file exempt from the target-scoped rule; artifact, artifact_path, smoke environment, limited sync), new `tests/test_version.py` and `tests/test_wheel.py`.

Checks run in this pass (from a /tmp copy):

| Check | Result |
|---|---|
| `bundle validate --strict -t dev` of the metric-views template (`--var consumer_group=...`) | pass |
| pytest (PYTHONPATH=src) | 418 passed, 1 skipped, 1 failed: `tests/test_config.py::test_version` still asserts `0.0.1` (not an owned path; request below) |
| `pip wheel --no-deps -w dist .` | builds `genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl` |
| installed wheel (`pip install --prefix`, since `venv` lacks ensurepip here): all 7 `gos-*` `--help` | rc 0; `__file__` under site-packages, `__version__` 0.1.0 |
| SDK bundle validate with placeholder vars | still fails (CLI checks that the `/Volumes` artifact_path volume exists) |

Still open: task 7 (init notebook guarded fallback and install cell; template notebook install cells still `%pip install --upgrade databricks-sdk pyyaml`), task 8 (CI), task 9 (README "Getting the SDK", `docs/distribution/README.md` with CLI version and keys), the installed-wheel test-suite run from a directory without `src/`, and the placeholder artifact_path problem.

## Requests

* Owner (or the owner of `tests/test_config.py`): change `test_version` to expect `0.1.0`, or remove it in favour of `tests/test_version.py`.

* Owner: add `dist/` and `build/` to `.gitignore` (bundle sync honours it; the explicit excludes cannot be used before the first build under `--strict`).

## Files modified

`pyproject.toml`, `CHANGELOG.md`, `databricks.yml`, `resources/sdk_smoke.job.yml`, `notebooks/sdk_smoke.ipynb`, `src/genie_ontology_modeled_knowledge_sdk/__init__.py`, `src/genie_ontology_modeled_knowledge_sdk/scaffold.py`, `templates/ontology-metric-views/databricks.yml`, `templates/ontology-metric-views/resources/register_metric_views.job.yml`, `tests/test_scaffold.py`, `tests/test_template_mv_bundle.py`, `tests/test_sdk_bundle.py`, `tests/test_version.py`, `tests/test_wheel.py`.
