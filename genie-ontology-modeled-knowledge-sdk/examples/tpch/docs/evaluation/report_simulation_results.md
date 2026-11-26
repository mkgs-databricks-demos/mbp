# Report simulation results: TPC-H Supply Chain Agent (build-1 final evaluation)

Build 1, wave 1-14, session 42, run 2026-11-26 (UTC). Agent: `tpch_supply_chain_agent` (dev space, found by title `[dev matthew_giglia] TPC-H Supply Chain Agent`). Personas and briefs: [personas.md](personas.md). Ground truth: [ground_truth/](ground_truth/). Reports as Genie produced them: [reports/](reports/).

**Overall score: 33.5 / 40 = 83.75%** (target 80%: met).

## Rubric

* `correct`: every ground-truth number within 1e-4 relative tolerance in Genie's result, right grain and filters.
* `partial`: right numbers, wrong presentation or a missing part.
* `wrong`: numbers, grain or filters differ.
* `no_answer`: no SQL result (text-only reply, error or timeout).
* Score = (correct + 0.5 x partial) / turns.

Grading method: an automatic numeric match of every ground-truth value (and every label) against Genie's statement result, then a manual review of each turn that was not an exact match (exec 2, 7, 8; regional 7, 8; procurement 2; fulfillment 8).

## Ground truth registration (before any Genie run)

All 40 ground-truth statements ran read-only on the space's SQL warehouse through the Statement Execution API, over `samples.tpch` base tables only, with **state SUCCEEDED (40/40)**. The SQL files were written first, checked byte for byte (md5) against the executed statements, then run, then Genie was asked.

| Report | Ground-truth file | GT ran (UTC) | Genie conversation started (UTC) | GT statements SUCCEEDED |
|---|---|---|---|---|
| exec_quarterly_review | `ground_truth/exec_quarterly_review.sql` | 18:45:06-18:45:29 | 18:46:39 | 10/10 |
| regional_sales_europe | `ground_truth/regional_sales_europe.sql` | 18:45:30-18:45:47 | 18:49:20 | 10/10 |
| procurement_supplier_profit | `ground_truth/procurement_supplier_profit.sql` | 18:45:49-18:46:05 | 18:52:14 | 10/10 |
| fulfillment_quality | `ground_truth/fulfillment_quality.sql` | 18:46:07-18:46:18 | 18:54:41 | 10/10 |

Ground-truth statement ids (turn: id):

* exec_quarterly_review: 1 `01f1e9c9-7f99-191c-a720-d21a48b68fae`, 2 `01f1e9c9-8545-1b3f-9444-2d090a53abf8`, 3 `01f1e9c9-8679-1e58-bc77-902d7db4a463`, 4 `01f1e9c9-8837-1165-bc91-979be0c3b21c`, 5 `01f1e9c9-8977-165a-9acf-7dfb29e5b096`, 6 `01f1e9c9-89fd-14f8-b2f7-470caed9897b`, 7 `01f1e9c9-8ace-1257-afc5-f91bf2912857`, 8 `01f1e9c9-8bc7-1a80-940b-1bd559a977bb`, 9 `01f1e9c9-8c82-1e10-8e8b-3ef81c61aa2e`, 10 `01f1e9c9-8d50-1602-9202-5ff0f7e61b3e`
* regional_sales_europe: 1 `01f1e9c9-8e07-1904-be08-7fbaf309efa1`, 2 `01f1e9c9-8eff-15ad-8c67-d4a4a91bf210`, 3 `01f1e9c9-8fd8-1439-85c3-761c507b7cef`, 4 `01f1e9c9-90b4-1110-b754-62049d424bc8`, 5 `01f1e9c9-9285-1ff8-b07e-d1ab667d9c84`, 6 `01f1e9c9-93fd-1be3-9a1b-81e27c5f1d05`, 7 `01f1e9c9-9528-191d-8a98-bcd934835a54`, 8 `01f1e9c9-9665-1fb3-a1ce-4728b9c0233f`, 9 `01f1e9c9-9740-1e8d-b275-7f39f38854e4`, 10 `01f1e9c9-981e-1cde-b3b8-03c599d19a6c`
* procurement_supplier_profit: 1 `01f1e9c9-990c-153f-8efb-6730e26006a5`, 2 `01f1e9c9-9a56-1466-928a-dc70a7eaeadb`, 3 `01f1e9c9-9bd8-13ab-9b43-aa9b6670458a`, 4 `01f1e9c9-9d6c-1d4d-8111-def2846af638`, 5 `01f1e9c9-9f45-197d-a04a-afebcb355923`, 6 `01f1e9c9-9fe3-101e-948c-f07a52bc749c`, 7 `01f1e9c9-a0f8-122e-a468-67028c4ab711`, 8 `01f1e9c9-a191-1be3-8b0c-dcc0a259593c`, 9 `01f1e9c9-a218-1126-b3c2-22662cb47ed9`, 10 `01f1e9c9-a2f5-1a06-913d-2c7ba8626fcc`
* fulfillment_quality: 1 `01f1e9c9-a453-10c7-823c-a386cf446419`, 2 `01f1e9c9-a500-1d85-899f-4a1d7189189a`, 3 `01f1e9c9-a590-1dca-abc5-004a4da3eb70`, 4 `01f1e9c9-a68d-1f04-b2e9-fad1e3c73885`, 5 `01f1e9c9-a741-1dd2-8284-05b1cb1757c9`, 6 `01f1e9c9-a7c4-16ea-8666-b569e40383a7`, 7 `01f1e9c9-a856-1ace-994b-1b73475a4245`, 8 `01f1e9c9-a966-11e0-bf84-ef38747a58bf`, 9 `01f1e9c9-aa29-18ef-87b5-aef9e900bf3f`, 10 `01f1e9c9-aaca-1afe-a759-789f87c1a7b5`

## Per-turn grades

| Turn | exec_quarterly_review | regional_sales_europe | procurement_supplier_profit | fulfillment_quality |
|---|---|---|---|---|
| 1 | correct | correct | correct | correct |
| 2 | correct | correct | no_answer | correct |
| 3 | correct | correct | correct | correct |
| 4 | correct | correct | correct | correct |
| 5 | correct | correct | correct | correct |
| 6 | correct | correct | correct | correct |
| 7 | correct | wrong | correct | correct |
| 8 | partial | wrong | correct | wrong |
| 9 | no_answer | correct | correct | correct |
| 10 | no_answer | correct | correct | correct |

Genie asked each turn in one conversation per report; every message reached `COMPLETED`. Follow-up turns that depend on earlier turns ("those regions", "that nation", "same for 1994", "most profitable region", "same breakdown for 1993") were graded correct or partial in 16 of the 18 pre-registered dependent turns listed in personas.md (exceptions: fulfillment 8, wrong basis; exec 10, which repeated the exec 9 refusal). Regional 8, not pre-registered as dependent, also leaked the France filter from turns 3-5.

## Scorecard

| Report | Turns | Correct | Partial | Wrong | No answer | Score | Send as-is |
|---|---|---|---|---|---|---|---|
| exec_quarterly_review | 10 | 7 | 1 | 0 | 2 | 75.0% | no: shipping reliability section missing |
| regional_sales_europe | 10 | 8 | 0 | 2 | 0 | 80.0% | no: top customers given as nations; Europe return rate is France only |
| procurement_supplier_profit | 10 | 9 | 0 | 0 | 1 | 90.0% | no: profit by supplier region missing |
| fulfillment_quality | 10 | 9 | 0 | 1 | 0 | 90.0% | no: 1993 return rate on a line-count basis |
| **Overall** | **40** | **33** | **1** | **3** | **3** | **83.75%** | **0 of 4** |

By turn, the agent clears the 80% target; by report, none of the four narratives could be sent unedited. Every report has at least one gap that a reader would notice.

## Failure themes and likely fix layer

| # | Theme | Turns | Likely fix layer |
|---|---|---|---|
| 1 | Fulfillment view has no order date or order year, so on-time rate by order year is refused | exec 9, 10 | metric view (`mv_tpch_supply_chain_fulfillment`: add `Order Date` / `Order Year` from `orders`) |
| 2 | Profit view has supplier nation but not supplier region | procurement 2 | metric view (`mv_tpch_supply_chain_profit`: add `Supplier Region`) |
| 3 | No customer-level dimension for revenue, so "top customers" falls back to nations | regional 7 | metric view (`mv_tpch_supply_chain_revenue`: add customer name/key) |
| 4 | Filter carried over from an earlier turn (France) where the question names a wider scope (European customers) | regional 8 | agent (follow-up scoping); glossary note that a region filter replaces an earlier nation filter |
| 5 | Return rate basis drifts in a follow-up: quantity share in turn 7, line-count share in turn 8 (both from the revenue view, not the returns view) | fulfillment 8 | glossary (pin the return rate basis) and possibly metric view (Genie used the revenue view, not the returns view, for both turns; whether the returns view lacks `Order Priority` was not checked, since agent and metric view definitions were out of bounds) |
| 6 | Quarter shown as a truncated date/timestamp rather than Q1-Q4 | exec 8 | metric view (add an `Order Quarter` dimension) |

Themes 1-3, 5 and 6 point at metric view coverage gaps (missing dimensions) rather than wrong measure logic: no turn failed because a metric view measure returned a different number from base-table ground truth for the same basis and filters. Recorded as a build-1 backlog input for session 45, even though the 80% target was met.
