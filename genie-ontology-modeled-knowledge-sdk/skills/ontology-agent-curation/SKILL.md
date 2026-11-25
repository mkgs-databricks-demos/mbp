---
name: ontology-agent-curation
description: Organize registered ontology metric views into Genie Agents (at most 50 per agent, else split by subdomain) and generate tokenized .geniespace.json files plus a proposed domain_manifest.yml, with minimal instructions. Load for the Genie Ontology Modeled Knowledge SDK agent curation stage or when asked to draft Genie Agent configs from metric views.
---

# Ontology Genie Agent Curation

Turn the registered metric views of a Genie Ontology run into Genie Agent configuration files for the agents bundle, using the SDK `geniespace` module. You write files only; deploying the bundle is a later stage.

Core principle: **the metric views carry the semantics.** Synonyms, comments, display names and measures live in the metric view YAML. Agent instructions only cover what a metric view cannot express. If you are tempted to add an instruction, first ask whether a metric view change would do it, and record that as a request for the tuning stage instead.

## Unattended-session rules

* No Git commands, no file deletion, no deploys, no Genie API writes.
* Write only `ontology-genie-agents/agents/*.geniespace.json` and `docs/domain_manifest.yml` in the run project (or the paths your session owns).
* Committed agent files stay **tokenized** (`${target_catalog}.${target_schema}.<view>`, optional `${warehouse_id}`). Never write a resolved catalog, schema or warehouse id into a committed file.

## 1. Read the inputs

| Input | Use it for |
|---|---|
| `sdk_config.json` | `domain_name`, `max_metric_views_per_agent` (default 50) |
| `ontology-metric-views/metric_views/manifest.json` | the metric views: `name`, `domain`, `subdomain` |
| Registration results under `docs/registration/` | which views actually registered; curate only those |
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

`mvs` items carry `name`, `fq_name`, `domain`, `subdomain` (check the exact type with `help(geniespace.plan_agents)`). The 50-MV rule:

* <= `max_per_agent` views: **one agent** for the domain.
* More: one agent per subdomain, each view in exactly one agent, cross-domain views assigned to their own subdomain. Similar measures stay together in one agent.

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

Check that the files resolve: render them to a scratch folder outside the repo with the dev overrides and confirm no `${` remains:

```bash
PYTHONPATH=<sdk src> python -m genie_ontology_modeled_knowledge_sdk.geniespace render ontology-genie-agents/agents /tmp/agents_rendered --params ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json
```

(`render_space_file` is the per-file form.) Never commit the rendered output.

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

- [ ] Agent count follows the rule: 1 agent if views <= `max_metric_views_per_agent`, else 1 per subdomain with no view in two agents (from `plan_agents`).
- [ ] One `ontology-genie-agents/agents/<agent>.geniespace.json` per plan; every table identifier is a registered metric view, tokenized.
- [ ] 5-10 sample questions per agent, each traceable to a research KPI.
- [ ] Text instructions only for ambiguous terms or unencoded rules (list each with its reason in the summary); no restated metric view metadata.
- [ ] Example SQL only for multi-step questions, using `MEASURE()`.
- [ ] `validate_space` returns no errors for every file; `geniespace render` leaves no `${`.
- [ ] `docs/domain_manifest.yml` written by `write_domain_manifest`, marked as a proposal in the summary.
