# 2026-11-24 — Wave 0-5, Session 11: TPC-H Metric View Synthesis

Build run `701596191246320`, task `w0-5_session`, branch `mg-genie-ontology-modeled-knowledge-sdk` (checked read-only). Mode: edit (`allow_execute`). This session ran only read-only SQL and created no UC objects.

## What was done
I used `skills/ontology-mv-synthesis` and the platform `metric-views` skill to write 7 parameterized metric view YAMLs under `examples/tpch/ontology-metric-views/metric_views/tpch_supply_chain/`, then wrote `manifest.json`.

| View | Subdomain | Grain / source | Joins (all verified many_to_one, `rely.at_most_one_match`) | Materialization |
|---|---|---|---|---|
| mv_tpch_supply_chain_revenue | sales | lineitem | orders -> customer -> nation -> region | 2 aggregated MVs |
| mv_tpch_supply_chain_orders | sales | orders | customer -> nation -> region | 1 |
| mv_tpch_supply_chain_market_share | sales | lineitem | orders -> customer -> nation -> region; supplier -> nation; part | 1 |
| mv_tpch_supply_chain_fulfillment | fulfillment | lineitem | orders | 1 |
| mv_tpch_supply_chain_returns | fulfillment | lineitem | orders -> customer -> nation | 1 |
| mv_tpch_supply_chain_profit | procurement | lineitem | partsupp (composite key), part, supplier -> nation, orders | 1 |
| mv_tpch_supply_chain_supply_cost | procurement | partsupp | part; supplier -> nation -> region | 1 |

View names and subdomains follow `docs/research/05_domain_subdomain_proposal.md`. Every join has a `# verified:` line taken from a row in `docs/data_profiles/data_model_summary.md`; every row there is `many_to_one` with orphan_rate 0.0. Nation and region are joined under separate aliases (`customer_nation` / `supplier_nation`).

## KPI -> metric view mapping
| KPI (research 02 / glossary) | Metric view | Measure |
|---|---|---|
| Revenue | revenue | `Revenue` |
| Gross Charge | revenue | `Gross Charge` |
| Discount Revenue | revenue | `Discount Revenue` |
| Extended Price (gross sales) | revenue | `Gross Sales` |
| Average Order Value (line-item basis) | revenue | `Average Order Value` |
| Order Volume | orders | `Order Count` |
| National Market Share | market_share | `Market Volume` by `Supplier Nation` (share computed at query time, see gaps) |
| On-Time Shipping Rate / delivery performance | fulfillment | `On-Time Shipping Rate` (ship-based), `On-Time Delivery Rate` (receipt-based) |
| Late Receipt (Q12) | fulfillment | `Late Receipt Count`, `Q12 Late Receipt Count` |
| Order Fulfillment Cycle Time | fulfillment | `Average Fulfillment Cycle Days` |
| Return Rate | returns | `Return Rate` (quantity), `Return Line Rate` (lines) |
| Returned item revenue lost (Q10) | returns | `Returned Revenue` |
| Profit (Q9) | profit | `Profit` |
| Inventory Value (Q11) | supply_cost | `Inventory Value` |
| Supply Cost | supply_cost | `Average Supply Cost`, `Minimum Supply Cost` |
| Perfect Order Rate | not mapped | TPC-H has no damage, documentation or invoice data (glossary: "Not yet mapped") |

The orders view also has the header-basis `Average Order Total` (`o_totalprice`). It has a different name so AOV maps to only one view. Research 02 leaves the AOV basis as an open question for the owner.

## Decisions
* **Materialization.** All 7 views meet a skill threshold. The 5 lineitem views exceed 10M rows (29,999,795 rows). Orders (3 joins) and supply_cost (4 joins) meet the >= 3 joins threshold. Every entry is `type: aggregated` with `refresh_policy: auto` and `cluster_by: auto`, and uses only categorical or month/quarter/year dimensions. No view has a `parameters:` block.
* **Data quality flags followed.** `o_totalprice` is summed only in the orders view, never through lineitem. `o_shippriority` (a constant) is left out. Inventory and offer counts come from `partsupp`.
* **On-time basis.** Both the ship-based (seed) and receipt-based (SCOR) rates are exposed. Research 02 leaves the choice open.

## Checks
| Check | Result |
|---|---|
| `PYTHONPATH=src python -m genie_ontology_sdk.mv_yaml validate examples/tpch/ontology-metric-views/metric_views` | pass: 7 files, 0 errors, 0 warnings, exit 0 |
| `manifest.build_manifest` + `validate_manifest_json` | pass: 7 entries, 0 problems; written with `write_manifest` |
| `grep -r 'samples.tpch'` over metric_views | pass: no matches (grep exit 1) |
| `render_ddl` with source_catalog=samples, source_schema=tpch | pass: no `${` left in any DDL (not executed) |
| Column references vs `samples.information_schema.columns` (tpch) | pass: no unknown columns |
| Read-only dry SELECT of the revenue join path (LIMIT 5) | pass: returned 5 rows |
| `bundle validate --strict` | skipped: no bundle YAML touched; the wave gate runs it |

## Skill gaps (ontology-mv-synthesis)
1. **Share-of-total KPIs.** National market share needs a ratio over a total that ignores the `Supplier Nation` grouping. The skill gives no pattern for this. A fixed-LOD dimension (`SUM(...) OVER ()`) or a window measure with `range: all` could work but was not verified on the platform, so the view exposes `Market Volume` and the share is left to the query. Add a verified pattern to `references/yaml-patterns.md`.
2. **Nested join reference paths.** Snowflake dimensions must be referenced by the full join path (`orders.customer.customer_nation.n_name`). The skill does not say this, and `yaml-patterns.md` has no nested-join example.
3. **Materialization thresholds are loose.** In a star schema almost every view meets ">= 3 joins" or ">= 10M rows", so every view got a materialization block. The skill could rank candidates or cap blocks per domain.
4. **One KPI to one view vs alternative bases.** The skill does not say how to handle a KPI with two candidate formulas (AOV header vs line basis, on-time ship vs receipt). I used distinct measure names and noted them here. The skill should say how to do this.
5. **No platform dry-run.** The skill's checks are static only. Nested-join syntax, `FILTER` measures and materialization are first tested at registration (session 12).

## Files
* `examples/tpch/ontology-metric-views/metric_views/tpch_supply_chain/mv_tpch_supply_chain_{revenue,orders,market_share,fulfillment,returns,profit,supply_cost}.yml`
* `examples/tpch/ontology-metric-views/metric_views/manifest.json`

## Requests
None. Session 12 should check that nested joins (up to 4 levels) and the `FILTER (WHERE ...)` measures register on the platform.
