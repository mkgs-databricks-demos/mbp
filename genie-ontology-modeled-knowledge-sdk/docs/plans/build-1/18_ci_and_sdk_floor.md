# Session 18: CI, Lint/Type Config, databricks-sdk Floor & SDK Bundle Bootstrap (R5, R7, R7a)

## Scope
Add `ruff` and `mypy` configuration and fix their findings, raise the `databricks-sdk` floor to the first release with every API the SDK calls, add a test that imports every SDK service used, and write the CI workflow (staged under `ci/`, moved to the repo root by the owner). Then bootstrap the **SDK bundle** at `build_root` (a schema resource and the `sdk_wheels` volume, no artifacts yet) and deploy it to dev, so the SDK's own schema exists before any later wave needs it. Deploy only the SDK bundle. No Git commands.

## Context
* [REQUESTS R5, R7](REQUESTS.md#r5-add-ci); review gaps G3, G4.
* Build-0 note (session 08): the gate's `/tmp` pytest copy cannot find genie-build-waves, so the `validate_manifest` test in `tests/test_run_kit.py` skips. Fix: every gate and CI job sets `GENIE_BUILD_WAVES_DIR` (the repo's `genie-build-waves/` folder). Keep the sibling-folder fallback.
* APIs to cover for the floor: `w.genie.start_conversation_and_wait`, `w.genie.get_message_attachment_query_result`, the Genie eval-runs API used by session 22 (`/api/2.0/genie/spaces/{id}/eval-runs`; if the SDK has no wrapper, `w.api_client.do` is fine and needs no floor), the skills create/finalize API used by session 27, `w.files`, `w.statement_execution`, `w.workspace`. Find the first release with each from the databricks-sdk-py changelog; set `databricks-sdk>=<floor>,<next major>`.
* Repo-root files: sessions write only inside `build_root` ([INDEX](INDEX.md#repository-root-files)).
* **SDK bundle (owner decision 2026-11-25, [R7a](REQUESTS.md#r7a-sdk-wheel-distribution)):** the SDK is set up as a bundle with a schema resource. SDK setup asks which catalog and schema the customer wants, recommending a **new** schema the bundle creates. That one schema holds the published skills (session 27), the `sdk_wheels` volume (sessions 23/23b) and build-only `scratch_*` pattern-check views (session 25). For this build the owner answered the questions in the gitignored `.databricks/bundle/dev/variable-overrides.json` at `build_root` (P1-8: `sdk_catalog`, `sdk_schema`, `sdk_consumer_group`, `warehouse_id`). Development mode prefixes the schema name (`dev_<user>_<sdk_schema>`).
* Deploying the volume now (wave 1-0) also avoids a first-deploy ordering problem: `workspace.artifact_path` must point at a volume that already exists when session 23b's deploy uploads the wheel.
* Authorized: `bundle.deploy` of the SDK bundle (target dev). Load the `dabs` skill before writing `databricks.yml`; follow the repo conventions (`${resources.schemas.<name>.*}` in resource definitions, `bundle validate --strict`).

## Tasks
1. `pyproject.toml`: `[tool.ruff]` (line length 120, target py311, rules `E,F,W,I,B,UP` at minimum) and `[tool.mypy]` (`python_version = 3.11`, `ignore_missing_imports = true`, strict optional). Add `ruff`, `mypy`, `types-PyYAML` to a `dev` optional-dependency group.
2. Run `ruff check --fix`, `ruff format`, `mypy src`; fix the rest by hand. Annotate rather than restructure; no behavior change (pytest must stay green).
3. Set the `databricks-sdk` range; record each API and its first release in `ci/README.md`.
4. `tests/test_sdk_services.py`: imports every SDK service and method the code uses (attribute checks on `WorkspaceClient`), so the floor is tested.
5. `ci/github/workflows/genie-ontology-modeled-knowledge-sdk-ci.yml`: on pull requests touching `genie-ontology-modeled-knowledge-sdk/**`; jobs `lint` (ruff), `typecheck` (mypy), `test` (matrix: the floor and the latest `databricks-sdk`; checks out the repo so `GENIE_BUILD_WAVES_DIR=genie-build-waves`), `bundle-validate` (both templates with placeholder overrides, `databricks bundle validate --strict`, GitHub OIDC to a dev workspace, no stored secret; `if:` the OIDC variables are set). Session 23 adds the wheel step.
6. `ci/README.md`: what each file is, where it moves at the repo root, the OIDC service principal and branch-protection setup (owner step P1-7).
7. **SDK bundle bootstrap** (`databricks.yml` + `resources/sdk.schema.yml`):
   * `bundle.name: genie_ontology_modeled_knowledge_sdk`; variables `sdk_catalog`, `sdk_schema` (default `ontology_sdk`, the recommended new schema), `sdk_consumer_group` (no default), `warehouse_id`; tag variables per the repo convention;
   * resources: `schemas.sdk` (`catalog_name: ${var.sdk_catalog}`, `name: ${var.sdk_schema}`, grants `USE_SCHEMA` to `${var.sdk_consumer_group}`) and `volumes.sdk_wheels` in `${resources.schemas.sdk.name}` (grant `READ_VOLUME` to `${var.sdk_consumer_group}`);
   * **existing-schema mode** for customers who choose an existing schema: a documented alternative that omits the schema resource and places the volume in `${var.sdk_schema}` (for example an include file switched per target); both modes pass `bundle validate --strict`;
   * targets `dev` (`mode: development`, default) and `prod` (`mode: production`, explicit `root_path`), no hosts or ids committed;
   * `sync` limited to the bundle's own files (no `examples/`, `templates/`, `docs/`).
8. `bundle validate --strict -t dev`, then `bundle deploy -t dev` (max 3 attempts); record the resolved schema and volume names only in your session summary (committed files use `<sdk_catalog>.<sdk_schema>`).
9. `docs/distribution/README.md`: what the SDK bundle holds, the setup questions (catalog, schema, consumer group; new schema recommended), both modes, and the deploy command.
10. `tests/test_sdk_bundle.py`: the YAML declares the schema and volume resources, references the schema through `${resources.schemas.sdk.*}`, has no committed workspace values, and the existing-schema mode omits the schema resource.

## Acceptance Criteria
- [ ] Gate checks `pytest`, `run_kit_not_skipped`, `ruff`, `mypy` pass from a `/tmp` copy.
- [ ] The workflow YAML parses and has the four jobs; a deliberately seeded lint error, type error and failing test each fail the corresponding local command (record the three commands and outcomes in the summary).
- [ ] `databricks-sdk` floor and upper bound set, with the API table in `ci/README.md`.
- [ ] Gate check `sdk_schema_deployed`: the SDK schema and its `sdk_wheels` volume exist after the dev deploy; `validate_bundles` for `.` passes.

## Owned Paths / Assets
- `pyproject.toml`, `databricks.yml`, `resources/**`, `src/genie_ontology_modeled_knowledge_sdk/**`, `tests/**`, `ci/**`, `docs/distribution/**`
- Dev deployment of the SDK bundle (schema + volume).

## Dependencies
- Build-0 (archived session 17).
