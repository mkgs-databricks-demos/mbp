# Inputs Report — bakehouse (bakehouse_retail_sales)

Written by session 01 (wave 0, Inputs Check). Later waves read the source table list from this report.

Checks used the installed SDK wheel `genie_ontology_modeled_knowledge_sdk` 0.1.1: `config.load_config`, `config.validate_config` (0 errors), `config.expand_tables` (4 tables), `config.check_access` (0 problems). Cross-checked with Unity Catalog `tables.get` and a `COUNT(*)` per table.

## Config

| Field | Value |
|---|---|
| `domain_name` | `bakehouse_retail_sales` |
| `domain_context` | Bakehouse retail franchise sales: customers buy baked goods at franchise stores; each franchise sources ingredients from one supplier. Model sales revenue, quantity, basket and payment mix by product, franchise, city, country and time, plus customer and supplier coverage. |
| `target_catalog` | `hls_fde_dev` (exists) |
| `target_schema` | `bakehouse_ontology` (does not exist yet; created by the metric-views bundle in wave 3) |
| `source_tables` | 4 entries, no wildcards (see below) |
| `warehouse_id` | `24087b85239cacac` (resolves; serverless PRO, currently stopped, starts on demand) |
| `max_metric_views_per_agent` | 30 |
| `sdk_distribution` | `wheel` |
| `pages_domain_id` | `domains/d3e01d7d-3bd8-4049-80f2-a4f9a1ffc8c3` |
| `skills` | catalog `hls_fde_dev`, schema `dev_matthew_giglia_ontology_sdk` |
| `validate_config` errors | 0 |

No secrets are stored in `sdk_config.json`.

## Source tables

* `samples.bakehouse.sales_customers` — 12 columns (300 rows, MANAGED)
* `samples.bakehouse.sales_franchises` — 10 columns (48 rows, MANAGED)
* `samples.bakehouse.sales_suppliers` — 10 columns (27 rows, MANAGED)
* `samples.bakehouse.sales_transactions` — 10 columns (3333 rows, MANAGED)

## Supplemental inputs

* `supplemental_volume_dirs`: none provided.
* `dashboard_inputs`: none provided.

## Access problems

none

## Date

2026-11-27 (UTC 03:11), build run 38498872047824.
