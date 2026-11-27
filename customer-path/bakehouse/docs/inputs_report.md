# Inputs Report — bakehouse (bakehouse_retail_sales)

Produced by build session `01` (wave `0`, run `531733719859424`) with the installed SDK wheel `genie_ontology_modeled_knowledge_sdk` `0.1.1` (`config.load_config`, `validate_config`, `expand_tables`, `check_access`). Read-only on Unity Catalog.

## Config

| Field | Value |
|---|---|
| `target_catalog` | `hls_fde_dev` |
| `target_schema` | `bakehouse_ontology` |
| `domain_name` | `bakehouse_retail_sales` |
| `domain_context` | Bakehouse retail franchise sales: customers buy baked goods at franchise stores; each franchise sources ingredients from one supplier. Model sales revenue, quantity, basket and payment mix by product, franchise, city, country and time, plus customer and supplier coverage. |
| `source_tables` | 4 explicit tables (see below) |
| `source_catalogs` / `source_schemas` | none |
| `warehouse_id` | `24087b85239cacac` |
| `max_metric_views_per_agent` | `30` |
| `sdk_distribution` | `wheel` |
| `pages_domain_id` | `domains/d3e01d7d-3bd8-4049-80f2-a4f9a1ffc8c3` |
| `skills` | catalog `hls_fde_dev`, schema `dev_matthew_giglia_ontology_sdk` |
| `supplemental_volume_dirs` | none |
| `dashboard_inputs` | none |

`validate_config`: **0 errors**.

## Source tables

Expanded by `expand_tables` (4 tables). Column counts from `ws.tables.get`; row counts from a read-only `COUNT(*)` that confirms SELECT access.

* `samples.bakehouse.sales_customers` — 12 columns (MANAGED, 300 rows)
* `samples.bakehouse.sales_franchises` — 10 columns (MANAGED, 48 rows)
* `samples.bakehouse.sales_suppliers` — 10 columns (MANAGED, 27 rows)
* `samples.bakehouse.sales_transactions` — 10 columns (MANAGED, 3333 rows)

## Supplemental inputs

No supplemental inputs provided: `supplemental_volume_dirs` and `dashboard_inputs` are empty, so there was nothing to list.

Note (informational, not an access problem): target catalog `hls_fde_dev` exists; target schema `hls_fde_dev.bakehouse_ontology` does not exist yet. The plan checks only the catalog; the schema is expected to be created by the `ontology-metric-views` bundle at registration (wave `3`).

## Access problems

none

## Date

2026-11-27
