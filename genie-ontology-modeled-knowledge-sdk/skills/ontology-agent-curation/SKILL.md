---
name: ontology-agent-curation
description: Genie Ontology Modeled Knowledge SDK agent curation stage. Groups a run project's registered metric views into Genie Agents with geniespace.plan_agents (split at min(max_metric_views_per_agent, 30)) and writes tokenized ontology-genie-agents/agents/*.geniespace.json plus a proposed docs/domain_manifest.yml. Load only inside an SDK run project (sdk_config.json present) or when a build-waves plan names this stage; not for general Genie space authoring.
---

# Ontology Genie Agent Curation

Turn the registered metric views of a Genie Ontology run into Genie Agent configuration files for the agents bundle, using the SDK `geniespace` module. You write files only; deploying the bundle is a later stage.

Core principle: **the metric views carry the semantics.** Synonyms, comments, display names and measures live in the metric view YAML. Agent instructions only cover what a metric view cannot express. If you are tempted to add an instruction, first ask whether a metric view change would do it, and record that as a request for the tuning stage instead.

## Unattended-session rules

* No Git commands, no file deletion, no deploys, no Genie API writes.
* Write only `ontology-genie-agents/agents/*.geniespace.json`, the agent entries of `ontology-genie-agents/resources/genie_agents.yml` and `docs/domain_manifest.yml` in the run project (or the paths your session owns).
* Committed agent files stay **tokenized** (`${target_catalog}.${target_schema}.<view>`, optional `${warehouse_id}`). Never write a resolved catalog, schema or warehouse id into a committed file.

## 1. Read the inputs

| Input | Use it for |
|---|---|
| `sdk_config.json` | `domain_name`, `max_metric_views_per_agent` (default 50; agents split at 30 at most, see section 2) |
| `ontology-metric-views/metric_views/manifest.json` | the metric views: `name`, `domain`, `subdomain` |
| Registration results under `docs/registration/`, including `resolved_target.json` (`catalog`, `schema`, `warehouse_id` where the metric-views bundle registered) | which views actually registered; curate only those |
| `docs/research/*.md` (KPI definitions, domain/subdomain proposal) | sample questions, agent names and descriptions |
| `docs/context/*.md` | business rules that the metric views could not encode |
| `docs/data_profiles/data_model_summary.md` | verified relationships between metric view grains (for `join_specs`) |
| The metric view YAML files | what each view already explains (do not duplicate it) |

## 2. Plan the agents

Build the metric view list from the manifest (only registered views), with `fq_name` = `${target_catalog}.${target_schema}.<name>`, and call:

```python
from genie_ontology_modeled_knowledge_sdk import geniespace
plans = geniespace.plan_agents(mvs, max_per_agent=cfg.max_metric_views_per_agent)
```

`mvs` items carry `name`, `fq_name`, `domain`, `subdomain` (check the exact type with `help(geniespace.plan_agents)`). The agent-size rule uses `geniespace.effective_max_per_agent(max_per_agent)` = `min(max_metric_views_per_agent, 30)`, because a Genie Agent holds at most 30 data sources (`validate_space`):

* <= that limit: **one agent** for the domain. Its `domain_manifest.yml` still lists every real subdomain of its views, all pointing at the same agent.
* More: split by subdomain into chunks of at most the limit, each view in exactly one agent, cross-domain views assigned to their own subdomain. Similar measures stay together in one agent.
* `config_warnings(sdk_config)` warns when `max_metric_views_per_agent > 30`; record the warning in the summary (behaviour is the 30 split).

Do not override the plan by hand. If it looks wrong (for example a subdomain is missing), the subdomain comments in the YAML are wrong: record a request for the metric view owner.

## 3. Write the content of each agent

**Sample questions (5-10 per agent).** Derive them from the research KPIs this agent's views answer, phrased as a business user would ask ("What was revenue by market segment last quarter?"). Each one must be answerable from the agent's views alone. Cover single measures, breakdowns, time comparisons and one ratio.

**Text instructions (minimal).** Add a line only for:
* a term that stays genuinely ambiguous after the metric view synonyms and comments ("'last month' means the previous calendar month"),
* a business rule from `docs/context/` that no metric view `filter` or measure encodes,
* which agent to use for a related question, when the domain is split.

Do not restate measure comments, synonyms, formatting or table descriptions. Zero instructions is a valid result. No duplicate lines (`validate_space` rejects them).

**Example SQL (multi-step questions only).** Add an `example_question_sqls` entry only for a question that needs more than one step (top-N with ranking, a ratio across two views, a period-over-period comparison). Use `MEASURE()` syntax and backtick-quoted names exactly as in the YAML. No examples for single-view, single-measure questions.

**Join specs.** Only between metric views in the same agent whose relationship has a `verified_cardinality` row in `data_model_summary.md`. Joins inside one metric view are already in its YAML.

## 4. Build, validate and write

```python
space = geniespace.build_space(
    plan,
    warehouse_id=None,               # or "${warehouse_id}"; never a literal id
    sample_questions=questions,
    text_instructions=instructions,
    example_sqls=example_sqls,
    join_specs=join_specs,
)
errors = geniespace.validate_space(space)   # version 2, 1-30 tables, unique ids, 3-part identifiers
```

Fix every error, then write `ontology-genie-agents/agents/<agent_name>.geniespace.json` (snake_case name, ending `_agent`). `build_space` is deterministic (ids from question text, sorted keys), so a re-run with the same inputs gives identical files.

**Writing the file from an unattended session (build-0 obs 23).** The workspace file editor cannot create `*.geniespace.json` ("Requested node type [UNKNOWN] is not supported"). Write it with the workspace import API, `format: RAW`, overwrite on, then read it back and compare a sha256 with the `space_to_json` text:

```python
import base64, hashlib
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat
text = geniespace.space_to_json(space)
w = WorkspaceClient()
w.workspace.import_(path, content=base64.b64encode(text.encode()).decode(), format=ImportFormat.RAW, overwrite=True)
back = w.workspace.download(path).read()
assert hashlib.sha256(back).hexdigest() == hashlib.sha256(text.encode()).hexdigest()
```

`path` is the absolute `/Workspace/...` path of the agent file. Outside a workspace (a local checkout), write the file normally.

**Replace the scaffold placeholder (build-0 obs 27).** In `ontology-genie-agents/resources/genie_agents.yml`, replace the template `ontology_agent` entry with one entry per agent you wrote (same warehouse, parent path and permissions; `file_path` to its rendered file). New scaffolds no longer copy the placeholder `agents/ontology_agent.geniespace.json`; if an older project still has it, leave it (no file deletion) and record an owner request to delete it.

**Check the target schema holds the views (build-0 obs 26), then render.** The agents bundle must point at the schema where the metric-views bundle registered the views. Use `docs/registration/resolved_target.json` (written by `gos-resolve-target` / `targets resolve`), never hand-typed overrides, and render to a gitignored folder with `--check`:

```bash
gos-render-agents render ontology-genie-agents/agents ontology-genie-agents/.rendered --params docs/registration/resolved_target.json --check
```

`--check` queries `system.information_schema` for the target schema and every table identifier before writing and exits 1 listing the missing ones (nothing written). It needs a `warehouse_id` (in the file or `--warehouse-id`). Run it before any `EXPLAIN` of example SQL; a missing schema means the overrides drifted from DAB 1, so fix the target, not the agent file. (`render_space_file` / `render_text` are the per-file and per-string forms.) Never commit the rendered output.

## 5. Domain manifest (proposal only)

Write the proposed structure with `geniespace.write_domain_manifest(plans, "docs/domain_manifest.yml")`:

```yaml
domains:
  - name: <Domain display name>
    description: <one line>
    subdomains:
      - name: <Subdomain>
        metric_views: [mv_..., mv_...]
        agent: <agent_name>
```

This is a **proposal**. Creating Unity Catalog domains/subdomains is opt-in and done by the owner; never call a domain-creation API from this stage.

## Output checklist

- [ ] Agent count follows the rule: 1 agent if views <= `min(max_metric_views_per_agent, 30)`, else split by subdomain with no view in two agents (from `plan_agents`).
- [ ] One `ontology-genie-agents/agents/<agent>.geniespace.json` per plan, written with the import API (read-back hash matches); every table identifier is a registered metric view, tokenized.
- [ ] `resources/genie_agents.yml` lists the curated agents and no longer the `ontology_agent` placeholder; an old placeholder file is an owner request, not a deletion.
- [ ] 5-10 sample questions per agent, each traceable to a research KPI.
- [ ] Text instructions only for ambiguous terms or unencoded rules (list each with its reason in the summary); no restated metric view metadata.
- [ ] Example SQL only for multi-step questions, using `MEASURE()`.
- [ ] `validate_space` returns no errors for every file; `gos-render-agents render ... --params docs/registration/resolved_target.json --check` exits 0.
- [ ] `docs/domain_manifest.yml` written by `write_domain_manifest`, marked as a proposal in the summary.
