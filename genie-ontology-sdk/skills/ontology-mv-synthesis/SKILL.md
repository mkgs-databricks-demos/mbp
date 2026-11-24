---
name: ontology-mv-synthesis
description: Synthesize parameterized Unity Catalog metric view YAML (one per business process and grain) plus the forEach manifest.json from domain research, supplemental context and deep EDA profiles. Load for the Genie Ontology SDK metric view synthesis stage, or when asked to draft or regenerate ontology metric views.
---

# Ontology Metric View Synthesis

Turn the discovery outputs of a Genie Ontology run into metric view YAML files under the metric-views bundle, then validate them and write `manifest.json`. You write files only; registration (`CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`) is a later stage run by the bundle's forEach job.

For YAML syntax (keys, joins, `rely`, materialization, semantic metadata) load the platform `metric-views` skill and its `joins-correctness.md`, `materialization.md` and `semantic-metadata.md`. This skill does not restate the spec; it adds the SDK rules on top. Worked patterns: [references/yaml-patterns.md](references/yaml-patterns.md).

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
3. **Explicit fields.** One `expr` entry per exposed column. No `source.*` / `<join>.*` wildcards in dimensions or measures. [MV003]
4. **Unique names** across dimensions and measures, business-friendly (`Order Date`, `Revenue`). [MV002]
5. **Joins only with verified cardinality.** Add a join only when `data_model_summary.md` has a row for it. Copy its `verified_cardinality`:
   * `many_to_one` / `one_to_one`: `cardinality: many_to_one` and `rely: { at_most_one_match: true }`, with a comment line `# verified: <left> -> <right> on <keys>, orphan_rate <x>` directly above the join. [MV005]
   * `many_to_many` or no row: no `rely` block. Prefer leaving the join out and modelling the other table as its own metric view.
   * Every join has `on` or `using`. [MV005]
6. **Semantic metadata from the inputs**, following the platform `semantic-metadata.md` rules (do not restate the name):
   * `synonyms` from glossary `synonyms` and research terminology (genuinely different words, up to 10).
   * `comment` on every measure: business meaning, units, exclusions, from context business rules. [MV006]
   * `display_name` only when it differs meaningfully from `name`.
   * `format` for currency, percentage and date values (from EDA data types); never on counts or IDs.
7. **Business rules** that apply to every measure go in the top-level `filter`; rules for one measure go in a measure-level `FILTER (WHERE ...)`.
8. **Compose measures** with ``MEASURE(`Name`)`` instead of repeating expressions.

## 4. Materialization blocks

Add a `materialization` block only when the EDA evidence meets at least one threshold:

| Signal (from `data_model_summary.md` / table profiles) | Threshold |
|---|---|
| Source fact row count | >= 10,000,000 rows |
| Joins in the metric view | >= 3 joins (including nested) |
| KPI frequency | the view backs a KPI that research or context marks as a headline / dashboard KPI |

If the profiles state different thresholds, use theirs and say so in the summary. The block:

* `mode: relaxed`, a `schedule` (default `every 6 hours`), and one `type: aggregated` entry per common grouping.
* `refresh_policy: auto` and `cluster_by: { auto: true }` on every entry. [MV007]
* `dimensions`: **only categorical grouping dimensions** (low-cardinality strings, month/quarter buckets). Never raw timestamps, amounts, or near-unique keys. [MV007]
* `measures`: `"*"` or the named measures.
* Never combine `materialization:` with a `parameters:` block (the platform rejects it). The `${...}` registration tokens are not a `parameters:` block and are fine.

## 5. Validate and write the manifest

From the metric-views bundle root, with the SDK on the path (the vendored copy `src/genie_ontology_sdk_vendored/` or the SDK `src/`):

```bash
PYTHONPATH=<sdk src> python -m genie_ontology_sdk.mv_yaml validate metric_views/
```

It prints findings and exits 1 on any error. Fix every error and re-run until it exits 0. Fix warnings unless the summary explains why one is acceptable (for example MV005 on a join you could not verify, which should not be there).

Then write the forEach input with the `manifest` module:

```python
from genie_ontology_sdk import manifest
entries = manifest.build_manifest("metric_views")   # [{name, yaml_path, domain, subdomain}], sorted by name
assert not manifest.validate_manifest_json(entries)  # unique names, files exist
manifest.write_manifest(...)                         # check the signature with help(manifest.write_manifest)
```

`manifest.json` goes where the metric-views bundle template expects it (its README; by default `ontology-metric-views/metric_views/manifest.json`). `yaml_path` is relative to the bundle root.

Optional dry check: `mv_yaml.render_ddl(text, fq_name, params)` with the dev values must leave no `${` in the DDL. Do not execute the DDL.

## Output checklist

- [ ] One YAML per business process/grain under `ontology-metric-views/metric_views/<domain>/`, each with `version: 1.1` and a `# subdomain:` comment.
- [ ] Every research KPI maps to exactly one metric view (mapping table in the session summary).
- [ ] No literal catalog/schema in any `source:`; only the four parameter tokens.
- [ ] No wildcard fields; every measure has a `comment`.
- [ ] Every join has a `# verified:` line traceable to a `data_model_summary.md` row; `rely` only on `many_to_one`/`one_to_one`.
- [ ] Materialization blocks only where a threshold is met, with `refresh_policy: auto`, `cluster_by: { auto: true }` and categorical dimensions only.
- [ ] `python -m genie_ontology_sdk.mv_yaml validate` exits 0 (record the output).
- [ ] `manifest.json` written by `manifest.write_manifest`, and `manifest.validate_manifest_json` returns no errors.
