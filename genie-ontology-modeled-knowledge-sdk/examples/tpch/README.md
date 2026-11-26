# TPC-H dogfood project

This folder is a Genie Ontology run project for the public `samples.tpch` data set, scaffolded by the SDK itself. Build-0 uses it to dogfood the SDK end to end: domain research, deep EDA, metric view synthesis and registration, UC Pages, Genie Agent curation, deployment and tuning. It holds no workspace-specific values.

## Inputs

`sdk_config.json` (validated by `genie_ontology_modeled_knowledge_sdk.config.validate_config`):

* `domain_name`: `tpch_supply_chain`
* `source_tables`: `samples.tpch.{customer,orders,lineitem,part,partsupp,supplier,nation,region}`
* `target_catalog`: `main`, `target_schema`: `ontology_tpch`. These are documented example values. The real dev catalog and schema come from the gitignored bundle overrides at deploy time
* `max_metric_views_per_agent`: `50`

`samples` is read-only. Metric view `source:` references stay `${source_catalog}.${source_schema}` (bundle variables, `samples` / `tpch` in the `dev` target), and registration writes into the overrides' catalog.

## Layout

| Path | From |
|---|---|
| `sdk_config.json` | the inputs above |
| `PROJECT_MEMORY.md` | `templates/run/PROJECT_MEMORY.md` |
| `ontology-metric-views/` | `templates/ontology-metric-views` + vendored `src/genie_ontology_modeled_knowledge_sdk_vendored/{mv_yaml,manifest,geniespace}.py` |
| `ontology-genie-agents/` | `templates/ontology-genie-agents` |
| `docs/plans/` | run kit: `waves.json`, `INDEX.md`, `README.md`, `plans/` |
| `docs/research/` | domain research and KPI definitions (build-0 session 10a) |
| `docs/semantics/` | glossary term files, 23 terms (session 10a) |
| `docs/context/` | business rules and join criteria from supplemental context; empty here (the example has no supplemental documents) |
| `docs/data_profiles/` | one profile per source table plus `data_model_summary.md` with verified joins (session 10b) |
| `docs/registration/` | metric view registration and smoke / cardinality test results (session 12) |
| `docs/pages/` | UC Pages dry-run results and the owner publish cell, `pages_registration.md` (session 13; publishing deferred to build 1) |
| `docs/deployment/` | Genie Agent deployment and probe results, `agent_validation.md` (session 15) |
| `docs/tuning/` | benchmark questions, results and tuning plan (session 16) |
| `docs/sessions/` | the run project's own session summaries; empty here (build-0 wrote its summaries in the SDK's `docs/sessions/`) |

The scaffold creates these folders empty (`.gitkeep`); in this example the build-0 sessions above filled them. Session 14 also wrote `docs/domain_manifest.yml`.

## Reproduce

From the SDK root, either run the `notebooks/init_ontology_project` notebook with the TPC-H defaults and `target_dir` set to this folder, or:

```bash
PYTHONPATH=src python -m genie_ontology_modeled_knowledge_sdk.scaffold --config examples/tpch/sdk_config.json --target examples/tpch --project-name tpch
```

The scaffold never overwrites existing files (unless `--force`) and never touches `.databricks/`, so re-running it writes 0 files.

## Overrides files (owner, gitignored)

Both bundles read workspace-specific values from gitignored files. Never commit them:

* `ontology-metric-views/.databricks/bundle/dev/variable-overrides.json`: `catalog`, `warehouse_id`
* `ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json`: `catalog`, `schema` (the dev-prefixed metric view schema), `warehouse_id`; optional `agent_permissions`

## Validate

```bash
cd examples/tpch/ontology-metric-views && databricks bundle validate --strict --target dev
cd ../ontology-genie-agents
PYTHONPATH=../../../src python -m genie_ontology_modeled_knowledge_sdk.geniespace render agents .rendered --params .databricks/bundle/dev/variable-overrides.json
databricks bundle validate --strict --target dev
```

The agents bundle needs the render step first (see its README): the CLI does not interpolate `${...}` inside `genie_spaces` space files.
