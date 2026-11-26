# Report-perspective simulation: personas and report briefs

Build 1, wave 1-14, session 42 (final evaluation). Written before any Genie conversation was started. Each report is asked as **one** multi-turn conversation with the deployed `tpch_supply_chain_agent` (dev). Ground truth per turn is pre-registered in `ground_truth/<report>.sql` over `samples.tpch` base tables only (no metric views).

Independence: built from `examples/tpch/docs/semantics/` (glossary definitions), `docs/domain_manifest.yml` and `docs/deployment/agent_validation.md` only. Nothing under `examples/tpch/docs/tuning/` and no agent instructions, example SQL or benchmarks were read.

Definitions used for ground truth (glossary seed definitions): Revenue = `sum(l_extendedprice * (1 - l_discount))`; Profit = revenue - `ps_supplycost * l_quantity`; Inventory Value = `sum(ps_supplycost * ps_availqty)`; On-Time Shipping Rate = share of line items with `l_shipdate <= l_commitdate`; Late Receipt = `l_receiptdate > l_commitdate`; Return Rate = returned quantity share (`l_returnflag = 'R'`); Average Order Value = revenue / distinct orders; Order Fulfillment Cycle Time = `avg(datediff(l_receiptdate, o_orderdate))` per line item. Order year/quarter come from `o_orderdate` unless a turn says otherwise.

| # | Report | Persona | Brief | Turns | Dependent follow-ups |
|---|---|---|---|---|---|
| 1 | `exec_quarterly_review` | VP Supply Chain | 1997 annual and quarterly review: revenue vs 1996, regional mix and growth, order volume, AOV, quarter trend, shipping reliability | 10 | turns 2, 4, 8, 10 |
| 2 | `regional_sales_europe` | Regional sales manager, Europe | 1995 regional report: region totals, drill into Europe by nation, top nation by segment, prior year, customers, returns vs Asia, multi-year trend | 10 | turns 2, 3, 4, 5, 9 |
| 3 | `procurement_supplier_profit` | Procurement lead | Supplier profitability and stock value: profit by supplier region and nation, Germany by year, inventory value and top parts, unit costs, a part-line profit view | 10 | turns 3, 7, 9 |
| 4 | `fulfillment_quality` | Fulfillment and quality lead | Shipping performance and returns: on-time rate by ship mode, late receipts, return rate by priority with a year cut, cycle time | 10 | turns 2, 3, 5, 7, 8, 10 |

The exact turn wording is the `-- turn N:` comment above each statement in the ground-truth file.

## Grading rubric

* `correct`: every number within 1e-4 relative tolerance of ground truth, right grain and filters.
* `partial`: right numbers but wrong presentation or a missing part (for example one of two requested values, or a percent expressed differently but numerically consistent).
* `wrong`: numbers, grain or filters differ.
* `no_answer`: no SQL result returned (text-only reply, error or timeout).
* Per report score = (correct + 0.5 x partial) / turns. Overall = same over all turns. Target 80% (recorded, not gated).
