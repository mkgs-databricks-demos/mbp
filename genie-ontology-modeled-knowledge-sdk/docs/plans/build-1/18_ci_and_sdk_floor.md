# Session 18: CI, Lint/Type Config & databricks-sdk Floor (R5, R7)

## Scope
Add `ruff` and `mypy` configuration and fix their findings, raise the `databricks-sdk` floor to the first release with every API the SDK calls, add a test that imports every SDK service used, and write the CI workflow (staged under `ci/`, moved to the repo root by the owner). No Git commands.

## Context
* [REQUESTS R5, R7](REQUESTS.md#r5-add-ci); review gaps G3, G4.
* Build-0 note (session 08): the gate's `/tmp` pytest copy cannot find genie-build-waves, so the `validate_manifest` test in `tests/test_run_kit.py` skips. Fix: every gate and CI job sets `GENIE_BUILD_WAVES_DIR` (the repo's `genie-build-waves/` folder). Keep the sibling-folder fallback.
* APIs to cover for the floor: `w.genie.start_conversation_and_wait`, `w.genie.get_message_attachment_query_result`, the Genie eval-runs API used by session 22 (`/api/2.0/genie/spaces/{id}/eval-runs`; if the SDK has no wrapper, `w.api_client.do` is fine and needs no floor), the skills create/finalize API used by session 27, `w.files`, `w.statement_execution`, `w.workspace`. Find the first release with each from the databricks-sdk-py changelog; set `databricks-sdk>=<floor>,<next major>`.
* Repo-root files: sessions write only inside `build_root` ([INDEX](INDEX.md#repository-root-files)).

## Tasks
1. `pyproject.toml`: `[tool.ruff]` (line length 120, target py311, rules `E,F,W,I,B,UP` at minimum) and `[tool.mypy]` (`python_version = 3.11`, `ignore_missing_imports = true`, strict optional). Add `ruff`, `mypy`, `types-PyYAML` to a `dev` optional-dependency group.
2. Run `ruff check --fix`, `ruff format`, `mypy src`; fix the rest by hand. Annotate rather than restructure; no behavior change (pytest must stay green).
3. Set the `databricks-sdk` range; record each API and its first release in `ci/README.md`.
4. `tests/test_sdk_services.py`: imports every SDK service and method the code uses (attribute checks on `WorkspaceClient`), so the floor is tested.
5. `ci/github/workflows/genie-ontology-modeled-knowledge-sdk-ci.yml`: on pull requests touching `genie-ontology-modeled-knowledge-sdk/**`; jobs `lint` (ruff), `typecheck` (mypy), `test` (matrix: the floor and the latest `databricks-sdk`; checks out the repo so `GENIE_BUILD_WAVES_DIR=genie-build-waves`), `bundle-validate` (both templates with placeholder overrides, `databricks bundle validate --strict`, GitHub OIDC to a dev workspace, no stored secret; `if:` the OIDC variables are set). Session 23 adds the wheel step.
6. `ci/README.md`: what each file is, where it moves at the repo root, the OIDC service principal and branch-protection setup (owner step P1-7).

## Acceptance Criteria
- [ ] Gate checks `pytest`, `run_kit_not_skipped`, `ruff`, `mypy` pass from a `/tmp` copy.
- [ ] The workflow YAML parses and has the four jobs; a deliberately seeded lint error, type error and failing test each fail the corresponding local command (record the three commands and outcomes in the summary).
- [ ] `databricks-sdk` floor and upper bound set, with the API table in `ci/README.md`.

## Owned Paths
- `pyproject.toml`, `src/genie_ontology_modeled_knowledge_sdk/**`, `tests/**`, `ci/**`

## Dependencies
- Build-0 (archived session 17).
