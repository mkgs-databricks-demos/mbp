---
name: ontology-mv-synthesis
description: Genie Ontology Modeled Knowledge SDK metric view synthesis stage. Writes tokenized metric view YAML under a run project's ontology-metric-views/metric_views/ plus the forEach manifest.json, from the project's docs/research, docs/context and docs/data_profiles. Load only inside an SDK run project (sdk_config.json present) or when a build-waves plan names this stage; for general metric view work use the platform metric-views skill.
---

# Ontology Metric View Synthesis

Turn the discovery outputs of a Genie Ontology run into metric view YAML files under the metric-views bundle, then validate them and write `manifest.json`. You write files only; registration (`CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`) is a later stage run by the bundle's forEach job.

For YAML syntax (keys, joins, `rely`, window measures, level of detail, materialization, semantic metadata) load the platform `metric-views` skill and its `joins-correctness.md`, `level-of-detail.md`, `materialization.md` and `semantic-metadata.md`. This skill does not restate the spec; it adds the SDK rules on top: parameter tokens, `# verified:` joins, `# subdomain:` comments, the manifest, materialization ranking, and MV-first (semantics live in the metric view, not in agent instructions). **Precedence:** when both load, the platform skill wins on syntax and this skill wins on SDK rules. Worked SDK patterns, several verified on the platform: [references/yaml-patterns.md](references/yaml-patterns.md).

## Unattended-session rules

* No Git commands, no file deletion, read-only SQL only (no DDL; registration is not your job).
* Write only under `ontology-metric-views/metric_views/` in the run project (or the paths your session owns).
* Never put a literal catalog or schema in `source:` or `joins[].source`; never put workspace-specific values (hosts, user names, warehouse ids) in YAML.

## 1. Read the inputs

All paths are relative to the run project root (the layout `scaffold_project` creates).

| Input | Use it for |
|---|---|
| `sdk_config.json` | `domain_name`, source tables, `max_metric_views_per_agent` |
| `docs/research/*.md` (KPI definitions, domain/subdomain proposal) | which KPIs exist, the subdomain of each, industry-standard measure formulas |
| `docs/semantics/*.md` (glossary: front matter `term`, `synonyms`, `domain`, `subdomain`, `related_terms`, `sources`) | `synonyms`, `display_name`, measure/dimension `comment` text |
| `docs/context/*.md` (business rules, KPI formulas, join criteria) | `filter`, filtered measures, business-logic comments |
| `docs/data_profiles/<table>.md` | grain, data types, categorical vs continuous columns, row counts, `format` |
| `docs/data_profiles/data_model_summary.md` | the join table (`left`, `right`, `keys`, `verified_cardinality`, `orphan_rate`, `query_used`) and materialization signals |

If an input is missing, say so in your session summary and continue with what exists. Never invent a join, a cardinality or a KPI formula that the inputs do not support.

## 2. Plan the metric views

* **One metric view per business process and grain.** A business process is an event the business measures (order placed, line shipped, inventory held). Its grain is the fact table row (one row per order, per line item, per part-supplier). Measures at different grains go in different metric views; never mix an order-grain fact and a line-item-grain fact in one `source`.
* Map each KPI from research to exactly one metric view (the one whose grain it aggregates). Record the KPI -> metric view mapping in your summary.
* Name files and views `mv_<domain>_<process>` (snake_case). The file stem is the view name.
* File layout, one folder per domain: `ontology-metric-views/metric_views/<domain>/<view_name>.yml`. Record each view's subdomain (from the research domain/subdomain proposal) the way `manifest.build_manifest` reads it: check `help(manifest.build_manifest)`; if it documents nothing else, use a leading YAML comment `# subdomain: <name>`. Agent curation splits agents by this value.

## 3. Write each YAML

Apply these rules (the validator rule that enforces each one is in brackets):

1. **Version and required keys** `version: 1.1`, `source`, a view-level `comment`, and dimensions/measures. [MV001]
2. **Parameter tokens, not literals.** `source: ${source_catalog}.${source_schema}.<table>` and the same for every `joins[].source`. Use only `${source_catalog}`, `${source_schema}`, `${target_catalog}`, `${target_schema}`; they are substituted at registration time by `mv_yaml.substitute`. [MV004]
3. **Explicit fields.** One `expr` entry per exposed column, each with a business-friendly `name` (`Order Date`, `Revenue`), unique across dimensions and measures. The SDK forbids wildcards even where the platform allows them, because the metadata must be per column. [MV002, MV003]
4. **Nested joins** (snowflake dimensions) are referenced by the full join path from `source` (`orders.customer.customer_nation.n_name`); role-name a dimension table joined twice (`customer_nation`, `supplier_nation`). See the verified pattern in `yaml-patterns.md`.
5. **Joins only with verified cardinality.** Add a join only when `data_model_summary.md` has a row for it. Copy its `verified_cardinality`:
   * `many_to_one` / `one_to_one`: `cardinality: many_to_one` and `rely: { at_most_one_match: true }`, with a comment line `# verified: <left> -> <right> on <keys>, orphan_rate <x>` directly above the join. [MV005]
   * `many_to_many` or no row: no `rely` block. Prefer leaving the join out and modelling the other table as its own metric view.
   * Every join has `on` or `using`. [MV005]
6. **Semantic metadata from the SDK inputs** (rules for when and how: platform `semantic-metadata.md`): `synonyms` from glossary `synonyms` and research terminology; a `comment` on every measure with business meaning, units and exclusions from `docs/context/` [MV006]; `format` from the EDA data types. Every ratio's comment states its unit ("fraction 0-1"), because `format: percentage` is display-only and the query still returns 0-1 (build-0 obs 30).
7. **Business rules** from `docs/context/` go into the YAML (`filter` for all measures, `FILTER (WHERE ...)` for one), never into agent instructions.
8. **Share-of-total KPIs** use the verified window-measure denominator pattern in `yaml-patterns.md`; never divide by a second plain measure (it is 1.0 at every grain).
9. **Two candidate formulas for one KPI** (header vs line basis, ship vs receipt date): one measure per basis, each named for its basis (`Average Order Value (Header)`, `Average Order Value (Line Revenue)`), and an owner decision note in the session summary listing both formulas and their sources. Never pick one silently.

## 4. Materialization blocks

A view is a **candidate** when the EDA evidence meets at least one threshold:

| Signal (from `data_model_summary.md` / table profiles) | Threshold |
|---|---|
| Source fact row count | >= 10,000,000 rows |
| Joins in the metric view | >= 3 joins (including nested) |
| KPI frequency | the view backs a KPI that research or context marks as a headline / dashboard KPI |

If the profiles state different thresholds, use theirs and say so in the summary.

In a star schema almost every view meets a threshold, so **rank and cap** (build-0 obs 18):

1. Score each candidate as `joins x source rows` (joins including nested; rows from the fact table profile). Headline-KPI views break ties upward.
2. Add blocks to **at most 3 views per domain**, highest score first. A fourth or later block needs a one-line justification in the summary (for example a measured slow query).
3. Record the ranking table (view, joins, rows, score, materialized yes/no) in the summary.

The block (syntax: platform `materialization.md`) has these SDK rules:

* `mode: relaxed`, a `schedule` (default `every 6 hours`), and one `type: aggregated` entry per common grouping.
* `refresh_policy: auto` and `cluster_by: { auto: true }` on every entry. [MV007]
* `dimensions`: **only categorical grouping dimensions** (low-cardinality strings, month/quarter buckets), each defined in the view. [MV007]
* The `${...}` registration tokens are not a `parameters:` block, so they do not block materialization.

## 5. Validate and write the manifest

From the metric-views bundle root, with the `genie_ontology_modeled_knowledge_sdk` package installed (the SDK wheel; `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml` is the same command):

```bash
gos-validate-mv validate metric_views/
```

It prints findings and exits 1 on any error. Fix every error and re-run until it exits 0. Fix warnings unless the summary explains why one is acceptable (for example MV005 on a join you could not verify, which should not be there).

Then write the forEach input with the `manifest` module:

```python
from genie_ontology_modeled_knowledge_sdk import manifest
entries = manifest.build_manifest("metric_views")   # [{name, yaml_path, domain, subdomain}], sorted by name
assert not manifest.validate_manifest_json(entries)  # unique names, files exist
manifest.write_manifest(...)                         # check the signature with help(manifest.write_manifest)
```

`manifest.json` goes where the metric-views bundle template expects it (its README; by default `ontology-metric-views/metric_views/manifest.json`). `yaml_path` is relative to the bundle root.

Static dry check: `mv_yaml.render_ddl(text, fq_name, params)` with the dev values must leave no `${` in the DDL.

## 6. Optional platform dry run

The validator is static: nested join paths, `FILTER` references, window measures and materialization are first checked by the platform at registration (build-0 obs 20). `EXPLAIN` of the rendered DDL is **not** a dry run: it returns a plan for broken definitions too (see `yaml-patterns.md`, "Errors only registration catches").

Only when your session is authorized for `sql.ddl` on a scratch schema (an `Owner authorizations` line naming it; never assume it):

1. Render each YAML with `mv_yaml.render_ddl` to the name `<scratch_schema>.scratch_<view>`.
2. Execute it (`CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`), then `SELECT` one dimension and every measure with `MEASURE()` and `LIMIT 1`.
3. Fix the YAML for every error, re-run, and list every `scratch_*` view you created in the summary (cleanup is an owner step). Never `DROP`, never register under the real view name.

Without that authorization, skip this step and say so in the summary; registration (the bundle's forEach job) is then the first platform check.

## Output checklist

- [ ] One YAML per business process/grain under `ontology-metric-views/metric_views/<domain>/`, each with `version: 1.1` and a `# subdomain:` comment.
- [ ] Every research KPI maps to exactly one metric view (mapping table in the session summary).
- [ ] No literal catalog/schema in any `source:`; only the four parameter tokens.
- [ ] No wildcard fields; every measure has a `comment`.
- [ ] Every join has a `# verified:` line traceable to a `data_model_summary.md` row; `rely` only on `many_to_one`/`one_to_one`.
- [ ] Materialization: ranking table in the summary; at most 3 blocks per domain unless justified; `refresh_policy: auto`, `cluster_by: { auto: true }`, categorical dimensions only.
- [ ] Ratios say "fraction 0-1" in their comment; share-of-total measures use the window-measure pattern; two-formula KPIs have one measure per basis and an owner decision note.
- [ ] `gos-validate-mv validate` exits 0 (record the output).
- [ ] Platform dry run done (list of `scratch_*` views) or recorded as skipped (no authorization).
- [ ] `manifest.json` written by `manifest.write_manifest`, and `manifest.validate_manifest_json` returns no errors.
