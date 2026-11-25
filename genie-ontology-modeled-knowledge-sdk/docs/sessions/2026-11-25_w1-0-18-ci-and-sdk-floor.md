# 2026-11-25 - Wave 1-0, session 18: CI, lint/type config, databricks-sdk floor, SDK bundle bootstrap

Run `1057400752545739`, branch `mg-genie-ontology-build-1-plan`, mode `edit` (allow_deploy). No Git commands were run.

## Changes

* **pyproject.toml:** `[tool.ruff]` (line length 120, py311, rules E,F,W,I,B,UP), `[tool.mypy]` (3.11, ignore_missing_imports, strict_optional), a `dev` extra (pytest, ruff, mypy, types-PyYAML), and `databricks-sdk>=0.45.0,<1`.
* **Lint/type fixes (no behavior change)** in 7 `src/` modules and 11 `tests/` files: ruff `--fix` (typing -> collections.abc imports, quoted annotations, unused imports, import order), `ruff format`, hand fixes for E501 (split strings) and B905 (`zip(..., strict=True)` where the lengths were already checked equal in `benchmark._rows_equal`; `strict=False` elsewhere, which keeps the old behavior). mypy: annotated `kwargs: dict[str, Any]` in `config.config_from_dict` and `ident: Any` in `geniespace.validate_space`.
* **Floor:** the floor was found by installing databricks-sdk 0.40, 0.44, 0.45, 0.46, 0.50, 0.55 and 0.60 and checking every method on a `WorkspaceClient`. `genie.get_message_attachment_query_result` is missing in 0.44.0 and present in 0.45.0. Every other method the code calls was present in all probed releases. The table is in `ci/README.md`. I did not cross-check against the changelog.
* **tests/test_sdk_services.py:** checks that each service and method the code calls exists, that the installed version meets the floor, and that the CI matrix includes the floor.
* **CI (staged):** `ci/github/workflows/genie-ontology-modeled-knowledge-sdk-ci.yml` has jobs `lint`, `typecheck`, `test` (matrix `0.45.0` / `latest`, with `GENIE_BUILD_WAVES_DIR` set to the repo's `genie-build-waves`) and `bundle-validate`. The last job uses GitHub OIDC and runs only `if:` `vars.DATABRICKS_HOST`/`DATABRICKS_CLIENT_ID` are set. It validates the SDK bundle's three targets and both templates. `ci/README.md` covers the file moves, floor table and P1-7 owner setup.
* **SDK bundle:** `databricks.yml` (`genie_ontology_modeled_knowledge_sdk`; variables `sdk_catalog`, `sdk_schema`=`ontology_sdk`, `sdk_consumer_group`, `warehouse_id`, `tags_*`; `sync.exclude` for ci/docs/examples/notebooks/skills/templates/tests). Targets: `dev` (development, default), `prod` and `prod_existing_schema` (both production, explicit root_path). Resources are target-scoped because the schema mode differs per target:
  * `resources/sdk.schema.yml`: schema `sdk` for dev/prod.
  * `resources/sdk_wheels.volume.yml`: volume in `${resources.schemas.sdk.*}` for dev/prod.
  * `resources/sdk.existing_schema.yml`: existing-schema mode. Volume only, in `${var.sdk_catalog}.${var.sdk_schema}`.
* **tests/test_sdk_bundle.py:** checks the resources, the `${resources.schemas.sdk.*}` references, that no workspace values are committed, and that existing-schema mode has no schema resource.
* **docs/distribution/README.md:** what the bundle holds, the setup questions, both modes and the deploy commands.

## Decisions

* **Lint scope:** the gate runs `ruff check .` / `ruff format --check .` over all of `build_root`. The notebooks, templates, examples, skills and docs (Markdown code blocks) that this session does not own had findings (about 95 F821 Databricks globals, E501, plus formatting). They are excluded with `[tool.ruff] extend-exclude`, which is a recorded suppression. The DO NOT EDIT start-session notebook is excluded too.
* **Grants:** grants were not approved for this session, so `dev` declares none. `prod` / `prod_existing_schema` grant `USE_SCHEMA` / `READ_VOLUME` to `sdk_consumer_group`.
* Resource files: a `.schema.yml` file may hold only the schema (strict validate flags anything else), so the volume is in its own file.

## Deploy (dev)

`bundle deploy -t dev` succeeded on attempt 1 (2 created). Resolved (from `bundle summary`):

* schema `hls_fde_dev.dev_matthew_giglia_ontology_sdk`
* volume `hls_fde_dev.dev_matthew_giglia_ontology_sdk.sdk_wheels` (`/Volumes/hls_fde_dev/dev_matthew_giglia_ontology_sdk/sdk_wheels`)
* deployment id `193178364631306`

Information_schema returned exactly these 2 objects (schemata + volumes).

## Checks (from a fresh /tmp/gos-gate-1-0 copy)

| Check | Result |
|---|---|
| pytest (`GENIE_BUILD_WAVES_DIR` set) | pass: 301 passed (baseline before the session: 280) |
| run_kit_not_skipped | pass: `test_validate_manifest_zero_errors` PASSED |
| ruff check + format --check | pass (28 files formatted) |
| mypy src | pass (8 source files) |
| workflow YAML parses, 4 jobs | pass: bundle-validate, lint, test, typecheck; matrix `['0.45.0', 'latest']` |
| bundle validate --strict | pass for dev, prod and prod_existing_schema (prod targets with placeholder `--var`s) |
| sdk_schema_deployed | pass |
| Seeded lint error (`import os` appended to scaffold.py), `ruff check .` | exit 1 (fails as expected) |
| Seeded type error (`def _seed() -> int: return "x"`), `mypy src` | exit 1 (fails as expected) |
| Seeded failing test (`assert False` in test_scaffold.py), pytest | exit 1 (fails as expected) |

How I ported the edits: fixes were made in a /tmp copy, then applied with workspace file edits. All 18 edited src/tests files were checked byte for byte against the /tmp copy.

## Requests

* Owner: decide whether `dev` should also grant `sdk_consumer_group`.
* Owner: move `ci/github/workflows/*` to `.github/workflows/` and do the P1-7 setup.
* Owners of `notebooks/`, `templates/`, `examples/`, `skills/`: bring them under ruff (add `builtins` for `spark`/`dbutils`/`display`), then drop them from `extend-exclude`.
* Session 23: add the wheel `artifacts` block. Set `workspace.artifact_path` to the `sdk_wheels` volume path and add a wheel step to CI.
