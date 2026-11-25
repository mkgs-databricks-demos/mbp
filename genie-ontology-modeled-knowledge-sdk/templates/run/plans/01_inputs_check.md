# Session 01: Inputs Check & Report

## Scope
Confirm the run inputs for `{{project_name}}` (domain `{{domain_name}}`) are valid and readable, and write `docs/inputs_report.md`. Later waves read the table list from this report. The project folder is already scaffolded and the build branch is a job parameter, so this session does no scaffolding and no Git.

## Context
* Skill: none (uses the SDK library only).
* SDK functions (`genie_ontology_modeled_knowledge_sdk.config`): `load_config(path)`, `validate_config(d) -> list[str]`, `expand_tables(cfg, ws) -> list[str]`, `check_access(cfg, ws) -> list[str]`.
* Import path: the vendored copy at `ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored/` (add `ontology-metric-views/src` to `sys.path`) or an installed `genie_ontology_modeled_knowledge_sdk`. If `config` is not vendored, read the input contract from `sdk_config.json` and check access with `readTable` / `information_schema` instead, and say so in the summary.
* `sdk_config.json` is input, not output: never edit it. Report problems; the owner fixes them.

## Tasks
1. Load `sdk_config.json` and run `validate_config`. Record every error.
2. Build a `WorkspaceClient()` and run `expand_tables(cfg, ws)` and `check_access(cfg, ws)`.
3. Check that `target_catalog` exists and that `supplemental_volume_dirs` / `dashboard_inputs` (if any) are listable. Read-only: no `CREATE`, no grants.
4. Write `docs/inputs_report.md` with sections `## Config` (field values, no secrets), `## Source tables` (one line per expanded table with its column count), `## Supplemental inputs`, `## Access problems` (`none`, or one bullet per problem), `## Date`.

## Acceptance Criteria
- [ ] `validate_config` returns 0 errors.
- [ ] `docs/inputs_report.md` lists every expanded source table.
- [ ] `## Access problems` says `none`. Otherwise stop with `status: "blocked"` and name the missing access in `blocking` (an owner action).

## Owned Paths
- `docs/inputs_report.md`

## Dependencies
- None (first wave). The scaffold (`genie_ontology_modeled_knowledge_sdk.scaffold.scaffold_project`) created this project before the build.
