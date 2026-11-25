# ontology-genie-agents (DAB 2)

Declarative Automation Bundle that deploys the Genie Agents of a Genie Ontology project. Each agent is one `agents/<name>.geniespace.json` file (a serialized v2 Genie space) and one `genie_spaces` resource entry. It is the second bundle of a project: deploy the `ontology-metric-views` bundle (DAB 1) first, because the agents point at its metric views.

* Engine: `engine: direct` (the `genie_spaces` resource needs the direct deployment engine; Databricks CLI >= 1.3.0).
* Targets: `dev` (`mode: development`, default) and `prd` (`mode: production`). No workspace hosts are set: select the workspace with your CLI profile.
* In `dev`, agent titles get the development prefix (`[dev <user>] Ontology Agent`), like jobs.

## Layout

| Path | Contents |
|---|---|
| `databricks.yml` | Bundle, variables, targets |
| `resources/genie_agents.yml` | One `genie_spaces` entry per agent (`ontology_agent` to start) |
| `agents/*.geniespace.json` | Committed, **tokenized** space files (`${target_catalog}.${target_schema}.<metric_view>`) |
| `.rendered/` | Rendered space files with real names. Gitignored; produced by the render step |
| `.databricks/bundle/<target>/variable-overrides.json` | Your workspace-specific variable values. Gitignored |

## Interpolation experiment (why there is a render step)

Question: does the CLI apply `${var.*}` interpolation inside a `genie_spaces` `file_path` JSON?

Test (Databricks CLI v1.27.0, 2026-11-24): a scratch bundle with `variables.catalog`/`schema` and a space file whose identifier was `${var.catalog}.${var.schema}.mv_exp`. `bundle validate --output json` showed `resources.genie_spaces.exp.serialized_space` with the literal text `${var.catalog}.${var.schema}.mv_exp`.

**Result: not interpolated.** The CLI inlines the file content as `serialized_space` unchanged. So the committed agent files stay tokenized and are rendered per target before validate/deploy, and `file_path` points at the rendered copy (`../.rendered/<agent>.geniespace.json`, relative to `resources/genie_agents.yml`).

## Variables

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `warehouse_id` | yes | | SQL warehouse the agents query with |
| `catalog` | yes | | Catalog of the metric views (the environment discriminator) |
| `schema` | yes | | Full metric view schema name, including any dev prefix that DAB 1 applies in `dev` |
| `consumer_group` | no | `account users` | Group granted `CAN_RUN` |
| `curator_group` | yes | | Group granted `CAN_EDIT`. No default: a permissions entry cannot be omitted conditionally, so you must name a group |
| `genie_parent_path` | `prd` only | `dev`: `${workspace.root_path}/genie` | Workspace folder the agents are created in |

## 1. Write the overrides file

Create `.databricks/bundle/dev/variable-overrides.json` (gitignored; never commit it):

```json
{
  "warehouse_id": "<warehouse id>",
  "catalog": "<metric view catalog>",
  "schema": "<metric view schema, with dev prefix>",
  "curator_group": "<curator group>"
}
```

For `prd`, write `.databricks/bundle/prd/variable-overrides.json` with the same keys plus `genie_parent_path`. For a validate-only check, placeholder values are fine.

## 2. Render the agent files

From this folder, with the SDK on `PYTHONPATH` (or installed):

```bash
python -m genie_ontology_modeled_knowledge_sdk.geniespace render agents .rendered --params .databricks/bundle/dev/variable-overrides.json
```

The command maps `catalog` -> `${target_catalog}` and `schema` -> `${target_schema}`, writes every `agents/*.geniespace.json` to `.rendered/`, and exits 1 (writing nothing) if any token is unresolved. Re-run it after every agent file change and when you switch targets.

## 3. Validate and deploy

```bash
databricks bundle validate --strict --target dev
databricks bundle deploy --target dev
```

Validate fails with `failed to read serialized genie space from file_path` until step 2 has run.

## Adding an agent

1. Generate `agents/<name>.geniespace.json` with `genie_ontology_modeled_knowledge_sdk.geniespace` (`plan_agents` -> `build_space` -> `space_to_json`). Keep identifiers tokenized and check it with `validate_space` (at most 30 data sources per agent).
2. Add one entry under `resources.genie_spaces` in `resources/genie_agents.yml`, with `file_path: ../.rendered/<name>.geniespace.json`, the same `warehouse_id`, `parent_path` and `permissions` as `ontology_agent`, and its own `title` / `description`.
3. Render (step 2) and validate (step 3).

The template's `ontology_agent` points at a placeholder metric view `mv_placeholder`; replace it with your agents.

Note for Databricks workspace Git folders: the workspace file editor cannot create files ending in `.geniespace.json` ("Requested node type [UNKNOWN] is not supported"). Write them from a terminal, the render CLI, or the workspace import API with `format: RAW`.
