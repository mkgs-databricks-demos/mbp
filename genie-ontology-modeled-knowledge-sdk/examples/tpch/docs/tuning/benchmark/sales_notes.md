# Sales benchmark notes (session 32)

Question file: `sales.yml` (ids `s001`-`s059`). Session 32, build 1, wave 1-6, job run 1020175336236697.

## How the SQL was run

* `expected_sql` is tokenized (`${target_catalog}.${target_schema}`). For the run, the tokens were rendered from `examples/tpch/docs/registration/resolved_target.json` (session 30, `source: bundle_summary`) and each statement ran read-only (SELECT only) through the Statement Execution API on that file's warehouse.
* After writing, the file on disk was loaded with `benchmark.load_questions`. Every rendered `expected_sql` was string-equal to the statement that ran.
* `expected_answer` is set for the scalar questions that return non-NULL values (first row; a list when the row has two measures). s040 and s058 return NULL (no rows in scope by design), so they have no `expected_answer`.

## Coverage per view

| View | Questions | simple | breakdown | time | filter | ratio | synonym | edge |
|---|---|---|---|---|---|---|---|---|
| mv_tpch_supply_chain_orders | 19 | 3 | 3 | 3 | 2 | 3 | 2 | 3 |
| mv_tpch_supply_chain_revenue | 23 | 4 | 3 | 4 | 3 | 3 | 3 | 3 |
| mv_tpch_supply_chain_market_share | 17 | 2 | 3 | 2 | 2 | 3 | 2 | 3 |
| Total | 59 | 9 | 9 | 9 | 7 | 9 | 7 | 9 |

* Every measure and dimension of the three views is asked at least once (orders: 5 measures and 9 dimensions; revenue: 9 and 12; market_share: 2 and 5). Measure and dimension tags are view-qualified (`measure:<mv>.<name>`), so `Order Count` and `Line Item Count`, which appear in more than one view, are credited to the right view.
* `python -m genie_ontology_modeled_knowledge_sdk.benchmark coverage`, run on this file alone and the three view YAMLs, reports only the 3 problems that apply to the whole set: fewer than 100 questions, 0% cross-view, and type `cross_view` unused. Sessions 33 and 34 cover those. It reports no missing measure or dimension.
* All questions are single-view. Cross-view questions are session 34's.

## Statement states

| id | view | type | state | statement_id | rows |
|---|---|---|---|---|---|
| s001 | orders | simple | SUCCEEDED | `01f1e948-2077-1344-8a4f-bdffe6bcd371` | 1 |
| s002 | orders | simple | SUCCEEDED | `01f1e948-219f-1fef-ab2d-0de06a858364` | 1 |
| s003 | orders | simple | SUCCEEDED | `01f1e948-2265-196a-a5e1-a92b09073a66` | 1 |
| s004 | orders | breakdown | SUCCEEDED | `01f1e948-2349-1b66-ba9d-60ac9d445343` | 3 |
| s005 | orders | breakdown | SUCCEEDED | `01f1e948-23e7-1a97-adc4-d6d97de024e5` | 5 |
| s006 | orders | breakdown | SUCCEEDED | `01f1e948-2487-11ee-81c4-262fd47b16c9` | 5 |
| s007 | orders | time | SUCCEEDED | `01f1e948-25dc-1f0a-b610-134c3de11b3c` | 7 |
| s008 | orders | time | SUCCEEDED | `01f1e948-2699-19b5-b965-b99b3976f5fd` | 12 |
| s009 | orders | time | SUCCEEDED | `01f1e948-275e-1e1d-908b-ee549b41d4ee` | 1 |
| s010 | orders | filter | SUCCEEDED | `01f1e948-27f5-1c4d-9182-380a7c81ca90` | 1 |
| s011 | orders | filter | SUCCEEDED | `01f1e948-2896-16aa-8a10-07abeff2dd7f` | 1 |
| s012 | orders | ratio | SUCCEEDED | `01f1e948-2934-1a3c-a528-55c2422049de` | 5 |
| s013 | orders | ratio | SUCCEEDED | `01f1e948-29e6-1cb7-a77e-70dc6107cc8d` | 5 |
| s014 | orders | ratio | SUCCEEDED | `01f1e948-2af3-11c1-a416-19fd176a2676` | 1 |
| s015 | orders | synonym | SUCCEEDED | `01f1e948-2b9a-1e32-bd86-bafe7502b062` | 1 |
| s016 | orders | synonym | SUCCEEDED | `01f1e948-2c22-197e-9c6f-e198e04491d2` | 25 |
| s017 | orders | edge | SUCCEEDED | `01f1e948-2d0c-1fe2-99d5-66c8222112d4` | 1 |
| s018 | orders | edge | SUCCEEDED | `01f1e948-2dc7-1112-be4d-8f65b91bbcba` | 1 |
| s019 | orders | edge | SUCCEEDED | `01f1e948-2e7e-1840-8b93-bd8f8f3cb676` | 1 |
| s020 | revenue | simple | SUCCEEDED | `01f1e948-2f10-1eac-9ba2-069cb7ca7853` | 1 |
| s021 | revenue | simple | SUCCEEDED | `01f1e948-300e-1861-be87-e4ee2e618ec0` | 1 |
| s022 | revenue | simple | SUCCEEDED | `01f1e948-30ab-12da-9634-0a53ea3ae42b` | 1 |
| s023 | revenue | simple | SUCCEEDED | `01f1e948-314f-12d8-ac88-06a399535cf0` | 1 |
| s024 | revenue | breakdown | SUCCEEDED | `01f1e948-31ef-1274-a962-49de53709de4` | 5 |
| s025 | revenue | breakdown | SUCCEEDED | `01f1e948-32a6-1733-ab0c-630a8e1091e3` | 4 |
| s026 | revenue | breakdown | SUCCEEDED | `01f1e948-3399-1080-b17b-480c911996b6` | 7 |
| s027 | revenue | time | SUCCEEDED | `01f1e948-3465-15a8-a8fc-9fd35fdb69ba` | 7 |
| s028 | revenue | time | SUCCEEDED | `01f1e948-35bc-168b-af03-c2350d8ab09b` | 12 |
| s029 | revenue | time | SUCCEEDED | `01f1e948-3669-194c-bfcf-cc04030bd7fb` | 1 |
| s030 | revenue | time | SUCCEEDED | `01f1e948-373a-10fb-ba9e-d2f49c615c86` | 3 |
| s031 | revenue | filter | SUCCEEDED | `01f1e948-37fd-1084-928b-15e46fc5b380` | 1 |
| s032 | revenue | filter | SUCCEEDED | `01f1e948-38be-1644-b496-62e93c0f3a2a` | 5 |
| s033 | revenue | filter | SUCCEEDED | `01f1e948-39f8-1424-a837-60c02e7e67ed` | 1 |
| s034 | revenue | ratio | SUCCEEDED | `01f1e948-3b71-18ec-8def-4eb594d34a37` | 5 |
| s035 | revenue | ratio | SUCCEEDED | `01f1e948-3d2a-16f5-ad59-89823a6d46b9` | 7 |
| s036 | revenue | ratio | SUCCEEDED | `01f1e948-3e18-14b4-8af1-6b908d0eb277` | 1 |
| s037 | revenue | synonym | SUCCEEDED | `01f1e948-3ed5-1926-80ee-51620f6de1ea` | 1 |
| s038 | revenue | synonym | SUCCEEDED | `01f1e948-4025-1e41-af6c-aedd37b2ddf3` | 3 |
| s039 | revenue | synonym | SUCCEEDED | `01f1e948-40c7-1dda-95e0-f426604a06bc` | 7 |
| s040 | revenue | edge | SUCCEEDED | `01f1e948-41e7-13fb-952d-3bcd51febd5c` | 1 |
| s041 | revenue | edge | SUCCEEDED | `01f1e948-4320-1fca-9dc8-3b2b8733374b` | 1 |
| s042 | revenue | edge | SUCCEEDED | `01f1e948-43da-121f-b369-a473755d7c3a` | 1 |
| s043 | market_share | simple | SUCCEEDED | `01f1e948-44cb-132c-9a4e-2286cb1776ae` | 1 |
| s044 | market_share | simple | SUCCEEDED | `01f1e948-45b7-1304-9537-cf24ab93e20b` | 1 |
| s045 | market_share | breakdown | SUCCEEDED | `01f1e948-4641-1e0c-8b2a-d9a3cc33823d` | 25 |
| s046 | market_share | breakdown | SUCCEEDED | `01f1e948-46df-1323-a1d3-1674e7ec008e` | 5 |
| s047 | market_share | breakdown | SUCCEEDED | `01f1e948-478a-164e-b577-9255cc5ba9d8` | 10 |
| s048 | market_share | time | SUCCEEDED | `01f1e948-48fa-1a6b-bfbb-f5e4c0c906ac` | 7 |
| s049 | market_share | time | SUCCEEDED | `01f1e948-49b4-125e-9e31-f93d1281b5b0` | 2 |
| s050 | market_share | filter | SUCCEEDED | `01f1e948-4a56-16af-9804-db5fc326cae3` | 1 |
| s051 | market_share | filter | SUCCEEDED | `01f1e948-4ba1-1845-8611-71666283b6a1` | 1 |
| s052 | market_share | ratio | SUCCEEDED | `01f1e948-4cca-1882-ab97-d67065b41b76` | 2 |
| s053 | market_share | ratio | SUCCEEDED | `01f1e948-4e6a-1e1e-9926-4d2c55410852` | 5 |
| s054 | market_share | ratio | SUCCEEDED | `01f1e948-4f2b-131e-b063-78916e69f853` | 25 |
| s055 | market_share | synonym | SUCCEEDED | `01f1e948-4fcd-10e4-ba48-3365b18ddfeb` | 25 |
| s056 | market_share | synonym | SUCCEEDED | `01f1e948-5090-19f7-a904-029e0d2096c5` | 5 |
| s057 | market_share | edge | SUCCEEDED | `01f1e948-51a3-1acc-8a3e-cca0ca2b3962` | 1 |
| s058 | market_share | edge | SUCCEEDED | `01f1e948-52e5-166d-84b2-808d697914dd` | 1 |
| s059 | market_share | edge | SUCCEEDED | `01f1e948-5395-1dc5-a494-b2dabad7f406` | 1 |

59 of 59 SUCCEEDED.

## Dropped questions

None.

## Observations for tuning

* s018 returns 0 and s058 returns NULL for 1999 (no orders after 1998-08-02). s040 returns NULL because every line ordered before 1995 is fulfilled. Graders should treat NULL and 0 as "none" for these.
* s041: ship dates run to 1998-12-01, after the last order date, so lines shipped after 1998-08-02 do exist.
* s059 uses `MEASURE(...) FILTER (WHERE ...)` over the metric view. It ran SUCCEEDED, so the FILTER form is available for ratio-type expected SQL.
* s020 Revenue (revenue view) equals s043 Market Volume (market_share view): 1089835179247.2155 for both, the same discounted-revenue expression at the same grain. s034 and s012 are the line-item vs header-basis order value pair (see the view comments).
