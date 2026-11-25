# Session 07: Genie Agent Bundle Template (DAB 2)

## Scope
Create `templates/ontology-genie-agents/`, the reusable Declarative Automation Bundle that deploys Genie Agents from `.geniespace.json` files with the `genie_spaces` resource (`engine: direct`). It must pass `bundle validate --strict --target dev` after the documented render step. Start from `examples/dab2_genie_agents/`, but do not edit `examples/`.

## Context
* [L200-G](../../design/L200-G-genie-agent-curator.md) Wave 7; [research/genie-agent-api-deployment.md](../../research/genie-agent-api-deployment.md). Docs: `genie_spaces` keys are `title`, `description`, `warehouse_id` (required), `file_path` (takes precedence over `serialized_space`), `parent_path`, `permissions`. Direct engine only; CLI >= 1.3.0.
* Example defects to fix: undeclared `${var.dev_warehouse_id}` / host variables, `file_path: ./agents/...` with no `agents/` folder, and hardcoded group names in targets.
* Identifier problem: metric view names differ per target (catalog + dev-prefixed schema), but a `file_path` JSON may not get `${var.*}` interpolation.
  * **First task:** find out. Write a tiny space JSON containing `${var.catalog}`, run `bundle validate --output json`, and check whether `resources.genie_spaces.*` shows the value resolved. Record the result in the template README.
  * If it is interpolated, use `${var.catalog}.${var.schema}` directly in the agent files.
  * If not, keep committed agent files tokenized (`${target_catalog}.${target_schema}`, session 03 contract). Render them with `python -m genie_ontology_modeled_knowledge_sdk.geniespace render agents .rendered --params .databricks/bundle/<target>/variable-overrides.json`, and point `file_path` at `./.rendered/<agent>.geniespace.json` (`.rendered/` gitignored).
* Variables: `warehouse_id`, `catalog`, `schema` (the full metric view schema name, including any dev prefix), `consumer_group` (default `account users`), `curator_group` (required, no default: a permissions entry cannot be conditionally omitted, so the user must name a group). Dev target placeholders make validate pass.
* Genie Agents get the dev-mode title prefix in `dev`, like jobs.

## Tasks
1. Run the interpolation experiment (scratch copy under `/tmp`, nothing committed) and pick the approach.
2. `databricks.yml` (`engine: direct`, dev + prd targets, no hosts) + `resources/genie_agents.yml` with one agent `ontology_agent`. `parent_path` is `${workspace.root_path}/genie` in dev and a variable in prd.
3. `agents/ontology_agent.geniespace.json`: a minimal valid v2 space over one placeholder metric view (tokenized per the chosen approach). It must pass `geniespace.validate_space`.
4. `README.md` (variables, overrides file, render step if used, deploy, how to add agents: one resource entry per `.geniespace.json`), `.gitignore` (`.databricks/`, `.rendered/`).
5. `tests/test_template_agent_bundle.py`: the YAML parses, every `file_path` source exists (pre-render source when rendering is used), no hosts or user names, `engine: direct`.

## Acceptance Criteria
- [ ] The interpolation result is recorded in `templates/ontology-genie-agents/README.md`, with the CLI version.
- [ ] With a scratch `variable-overrides.json` (in `/tmp` or the gitignored `.databricks/` folder) and the render step if needed, `bundle validate --strict --target dev` exits 0 (runDatabricksCli tool with `workingDirectory`).
- [ ] pytest (from a `/tmp` copy) passes.
- [ ] No deploy in this session.

## Owned Paths / Assets
- `templates/ontology-genie-agents/**`
- `tests/test_template_agent_bundle.py`

## Dependencies
- Session 03: `validate_space`, `render_space_file` / `render` CLI.
