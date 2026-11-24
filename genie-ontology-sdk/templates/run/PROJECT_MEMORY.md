# Project Memory — {{project_name}}

This is the living memory for the Genie Ontology run of domain `{{domain_name}}`. Every build session reads it (it is listed in `docs/plans/waves.json` `context_files`). Keep it generic: specific IDs (runs, jobs, Genie spaces, page ids) belong in `docs/sessions/` and the `docs/*/..._results.md` files, not here.

## Purpose

This project stands up modeled knowledge for `{{domain_name}}`. It takes Unity Catalog source tables plus supplemental business context and produces parameterized metric views, then UC Pages, curated Genie Agents and an initial tuning pass. The work is driven by the Genie Ontology SDK run kit and executed by genie-build-waves.

## Status

* Phase: **scaffolded, no build run yet.**
* Bundle target: `{{bundle_target}}`.
* History: see `docs/sessions/INDEX.md`.

## Layout

| Path | Contents |
|---|---|
| `sdk_config.json` | Run inputs (source tables, target catalog/schema, domain context). Owner-edited |
| `ontology-metric-views/` | Bundle 1: metric view YAML + `register_metric_views` forEach job |
| `ontology-genie-agents/` | Bundle 2: `.geniespace.json` agents via the `genie_spaces` resource |
| `docs/plans/` | Run manifest `waves.json`, `INDEX.md`, `plans/` |
| `docs/research/`, `docs/semantics/`, `docs/context/`, `docs/data_profiles/` | Discovery outputs (wave 1) |
| `docs/registration/`, `docs/pages/`, `docs/deployment/`, `docs/tuning/` | Runtime results (waves 3-6) |
| `docs/sessions/` | Session summaries + INDEX |

## Owner prerequisites (before the build)

* `ontology-metric-views/.databricks/bundle/{{bundle_target}}/variable-overrides.json` and `ontology-genie-agents/.databricks/bundle/{{bundle_target}}/variable-overrides.json` hold the workspace values (see each bundle README). They are gitignored. Sessions never print, edit or commit them.
* Read access to every source table and volume. The `inputs_report` session (wave `0`) checks this.

## Conventions

* Feature branches only; never commit to `main`. Sessions never run Git.
* No workspace-specific identifiers in committed files. Metric view YAML uses `${source_catalog}`, `${source_schema}`, `${target_catalog}`, `${target_schema}`. Agent files are tokenized.
* Tune metric views (comments, synonyms, measures) before adding Genie Agent instructions.
* Notebook paths in bundle YAML must match the extension on disk. Run `bundle validate --strict` after YAML edits.

## Decisions

| # | Topic | Decision |
|---|---|---|
| 1 | Agent split | One agent unless there are more than `max_metric_views_per_agent` views; otherwise split by subdomain |
| 2 | Domains/subdomains | Proposed in `docs/research/05_domain_subdomain_proposal.md`. Creating them is opt-in |
| 3 | Re-runs | Full regeneration (idempotent) |

## Findings

(Add findings here as the run progresses.)
