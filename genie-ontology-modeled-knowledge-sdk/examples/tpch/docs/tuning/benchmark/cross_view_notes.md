# Cross-View Benchmark Notes (session 34)

File: `cross_view.yml`, 105 questions (`x001`-`x105`). 90 need 2 views, 14 need 3 views and 1 needs 4 views. Each question's first tag is `type:cross_view`, and a second `type:` tag gives the secondary type (`breakdown`, `time`, `ratio`, `filter`, `synonym`, `edge`). `benchmark.coverage` counts only the first `type:` tag, so the other question types have to come from `sales.yml` and `fulfillment_procurement.yml`.

Method: one CTE per metric view selects `MEASURE()` grouped by the shared dimension, renamed to a common alias. The CTEs are joined with `USING` on that alias, or `CROSS JOIN` for scalar CTEs. SQL is tokenized with `${target_catalog}.${target_schema}`. Each statement was rendered with `examples/tpch/docs/registration/resolved_target.json` and run read-only on that file's SQL warehouse through the Statement Execution API. It was run twice: once from the generator, then again after loading the questions back from the workspace file.

## View pairs

Shared dimensions come from the registered metric view definitions (`DESCRIBE TABLE EXTENDED ... AS JSON`).

| View A | View B | Shared dimension(s) used | Questions |
|---|---|---|---|
| orders | revenue | Order Year/Month/Date, Customer Region/Nation, Market Segment, Order Priority, Order Status vs Line Status | 18 |
| orders | returns | Order Month (and derived quarter), Market Segment, Customer Nation | 10 |
| orders | fulfillment | Order Priority, High Priority | 7 |
| orders | market_share | Order Year, Customer Region/Nation | 9 |
| orders | profit | Order Year | 7 |
| orders | supply_cost | Customer Nation/Region vs Supplier Nation/Region (demand vs supply base) | 5 |
| revenue | returns | Ship Mode, Market Segment, Order Month, Customer Nation, Return Flag | 14 |
| revenue | fulfillment | Ship Mode, Ship Month/Date, Line Status, Order Priority | 11 |
| revenue | market_share | Customer Region/Nation, Order Year | 6 |
| revenue | profit | Order Year | 8 |
| returns | fulfillment | Ship Mode | 6 |
| returns | market_share | Customer Nation | 6 |
| returns | profit | Order Year (derived from Order Month/Quarter) | 5 |
| market_share | profit | Supplier Nation, Part Type, Order Year | 8 |
| market_share | supply_cost | Supplier Nation, Part Type | 8 |
| profit | supply_cost | Manufacturer, Part Brand, Part Type, Supplier Nation | 10 |

Every pair with a business meaning has at least 3 questions (the minimum is 5). A question with 3 or more views counts once for each pair it contains.

Pairs left out, with no shared dimension that has a business meaning:

* revenue / supply_cost: the only link is customer nation vs supplier nation, which is already covered by orders / supply_cost and market_share / supply_cost.
* returns / supply_cost: no shared part or supplier dimension.
* fulfillment / market_share: fulfillment has only ship, receipt and priority dimensions; market_share has order year, nations and part type.
* fulfillment / profit: same reason.
* fulfillment / supply_cost: same reason.

## Questions and statement state

| Id | Views | State | Rows |
|---|---|---|---|
| x001 | O+R | SUCCEEDED | 7 |
| x002 | O+R | SUCCEEDED | 5 |
| x003 | O+R | SUCCEEDED | 5 |
| x004 | O+R | SUCCEEDED | 12 |
| x005 | O+R | SUCCEEDED | 5 |
| x006 | O+R | SUCCEEDED | 5 |
| x007 | O+R | SUCCEEDED | 5 |
| x008 | O+R | SUCCEEDED | 1 |
| x009 | O+R | SUCCEEDED | 2 |
| x010 | O+T | SUCCEEDED | 5 |
| x011 | O+T | SUCCEEDED | 25 |
| x012 | O+T | SUCCEEDED | 12 |
| x013 | O+T | SUCCEEDED | 10 |
| x014 | O+T | SUCCEEDED | 4 |
| x015 | O+T | SUCCEEDED | 5 |
| x016 | O+F | SUCCEEDED | 5 |
| x017 | O+F | SUCCEEDED | 2 |
| x018 | O+F | SUCCEEDED | 5 |
| x019 | O+F | SUCCEEDED | 1 |
| x020 | O+F | SUCCEEDED | 1 |
| x021 | O+M | SUCCEEDED | 5 |
| x022 | O+M | SUCCEEDED | 7 |
| x023 | O+M | SUCCEEDED | 25 |
| x024 | O+M | SUCCEEDED | 5 |
| x025 | O+P | SUCCEEDED | 7 |
| x026 | O+P | SUCCEEDED | 7 |
| x027 | O+P | SUCCEEDED | 1 |
| x028 | O+P | SUCCEEDED | 7 |
| x029 | O+C | SUCCEEDED | 25 |
| x030 | O+C | SUCCEEDED | 5 |
| x031 | O+C | SUCCEEDED | 5 |
| x032 | O+C | SUCCEEDED | 0 (edge: the expected answer is no rows) |
| x033 | R+T | SUCCEEDED | 7 |
| x034 | R+T | SUCCEEDED | 5 |
| x035 | R+T | SUCCEEDED | 12 |
| x036 | R+T | SUCCEEDED | 5 |
| x037 | R+T | SUCCEEDED | 3 |
| x038 | R+T | SUCCEEDED | 5 |
| x039 | R+T | SUCCEEDED | 7 |
| x040 | R+F | SUCCEEDED | 7 |
| x041 | R+F | SUCCEEDED | 12 |
| x042 | R+F | SUCCEEDED | 2 |
| x043 | R+F | SUCCEEDED | 5 |
| x044 | R+F | SUCCEEDED | 7 |
| x045 | R+F | SUCCEEDED | 1 |
| x046 | R+F | SUCCEEDED | 7 |
| x047 | R+M | SUCCEEDED | 5 |
| x048 | R+M | SUCCEEDED | 7 |
| x049 | R+M | SUCCEEDED | 1 |
| x050 | R+M | SUCCEEDED | 25 |
| x051 | R+P | SUCCEEDED | 7 |
| x052 | R+P | SUCCEEDED | 7 |
| x053 | R+P | SUCCEEDED | 1 |
| x054 | R+P | SUCCEEDED | 7 |
| x055 | T+F | SUCCEEDED | 7 |
| x056 | T+F | SUCCEEDED | 1 |
| x057 | T+F | SUCCEEDED | 7 |
| x058 | T+F | SUCCEEDED | 2 |
| x059 | T+M | SUCCEEDED | 25 |
| x060 | T+M | SUCCEEDED | 5 |
| x061 | M+T | SUCCEEDED | 5 |
| x062 | T+M | SUCCEEDED | 14 |
| x063 | T+P | SUCCEEDED | 7 |
| x064 | T+P | SUCCEEDED | 7 |
| x065 | T+P | SUCCEEDED | 1 |
| x066 | M+P | SUCCEEDED | 25 |
| x067 | M+P | SUCCEEDED | 7 |
| x068 | M+P | SUCCEEDED | 10 |
| x069 | M+P | SUCCEEDED | 30 |
| x070 | M+P | SUCCEEDED | 1 |
| x071 | M+C | SUCCEEDED | 25 |
| x072 | M+C | SUCCEEDED | 10 |
| x073 | M+C | SUCCEEDED | 25 |
| x074 | C+M | SUCCEEDED | 5 |
| x075 | M+C | SUCCEEDED | 10 |
| x076 | P+C | SUCCEEDED | 5 |
| x077 | P+C | SUCCEEDED | 10 |
| x078 | P+C | SUCCEEDED | 25 |
| x079 | P+C | SUCCEEDED | 10 |
| x080 | P+C | SUCCEEDED | 5 |
| x081 | P+C | SUCCEEDED | 5 |
| x082 | P+C | SUCCEEDED | 1 |
| x083 | O+R+T | SUCCEEDED | 5 |
| x084 | O+R+T | SUCCEEDED | 25 |
| x085 | R+T+F | SUCCEEDED | 7 |
| x086 | M+P+C | SUCCEEDED | 25 |
| x087 | M+P+C | SUCCEEDED | 10 |
| x088 | O+M+T | SUCCEEDED | 25 |
| x089 | O+R+P | SUCCEEDED | 7 |
| x090 | O+R+F | SUCCEEDED | 5 |
| x091 | O+R+M+P | SUCCEEDED | 7 |
| x092 | O+C+M | SUCCEEDED | 25 |
| x093 | O+R+T | SUCCEEDED | 12 |
| x094 | R+T+F | SUCCEEDED | 7 |
| x095 | P+C | SUCCEEDED | 5 |
| x096 | O+R+M | SUCCEEDED | 5 |
| x097 | R+T+P | SUCCEEDED | 7 |
| x098 | O+R+F | SUCCEEDED | 2 |
| x099 | O+M | SUCCEEDED | 7 |
| x100 | R+P | SUCCEEDED | 7 |
| x101 | O+P | SUCCEEDED | 7 |
| x102 | M+T | SUCCEEDED | 5 |
| x103 | T+P | SUCCEEDED | 4 |
| x104 | O+R | SUCCEEDED | 7 |
| x105 | R+T | SUCCEEDED | 7 |

Key: O orders, R revenue, T returns, F fulfillment, M market_share, P profit, C supply_cost.

## Dropped or changed questions

* None were dropped.
* Changed before they were finalized:
  * x014 moved from 1996 to 1993, because `Return Line Rate` was 0 for every 1996 quarter.
  * x103 moved from 1997 to 1993, because `Returned Quantity` was NULL in 1997.
  * Both changes follow from the same data fact: in TPC-H, only older line items carry `R`, so returns questions use years before 1995.
* Kept on purpose as edge questions:
  * x032 returns no rows.
  * x065 returns 0 returned lines for 1998.
  * x047, x096 and x100 reconcile revenue across views: the views agree, so the difference is 0.
  * x104 and x105 reconcile counts across views: the views agree, so the difference is 0.

## Coverage on this file alone

I ran `python -m genie_ontology_modeled_knowledge_sdk.benchmark coverage examples/tpch/docs/tuning/benchmark examples/tpch/ontology-metric-views/metric_views` from a /tmp copy that held only `cross_view.yml`. The results:

* 105 questions, cross-view share 100%.
* Per-view counts: orders 45, revenue 45, returns 34, profit 32, market_share 30, fulfillment 20, supply_cost 20.
* Every measure of the 7 views is tagged at least once.
* Dimensions still open, all single-view, for sessions 32 and 33:
  * fulfillment: Receipt Date, Receipt Month, Receipt Year
  * profit: Part Name
  * returns: Customer Name
  * supply_cost: Part Key, Part Size, Supplier Name
* Type mix: only `cross_view` is counted, as expected for this file.

Cross-view share of the full set is 105 / (105 + n32 + n33). It stays at 25% or more while sessions 32 and 33 together write at most 315 questions; the total cap is 498.
