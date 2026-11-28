# Benchmark Group B Notes (session 10b)

* Date: 2026-11-28. Build run `409860738864401`, wave 6.
* View group B = second half of `ontology-metric-views/metric_views/manifest.json` by name, taken as `names[n//2:]` of 3 views: `mv_bakehouse_sales`, `mv_bakehouse_supplier_coverage`. (`mv_bakehouse_customer_activity` is group A.) With an odd count this choice keeps the middle view in group B so it is covered whichever way 10a rounds; any overlap is harmless because ids are prefixed.
* File: `docs/tuning/benchmark/group_b.yml`, 48 questions, ids `b-001`..`b-048`, tokenized `${target_catalog}.${target_schema}`.
* Execution: every `expected_sql` rendered with `docs/registration/resolved_target.json` (catalog `hls_fde_dev`, the dev bundle schema) and run read-only through the Statement Execution API on the warehouse in `resolved_target.json`.

## Statement states

| id | view | type | state | rows | statement_id |
|---|---|---|---|---|---|
| b-001 | mv_bakehouse_sales | simple | SUCCEEDED | 1 | 01f1eaf0-4248-1ca2-8bc0-5b260f487210 |
| b-002 | mv_bakehouse_sales | simple | SUCCEEDED | 1 | 01f1eaf0-42e4-1076-a4e2-87b1fa49b772 |
| b-003 | mv_bakehouse_sales | simple | SUCCEEDED | 1 | 01f1eaf0-435c-19d6-b4a1-ffb044d26b30 |
| b-004 | mv_bakehouse_sales | simple | SUCCEEDED | 1 | 01f1eaf0-43d9-1409-bd8b-7e31df3dc691 |
| b-005 | mv_bakehouse_sales | simple | SUCCEEDED | 1 | 01f1eaf0-4456-1af2-b763-7fbe7eb121a6 |
| b-006 | mv_bakehouse_sales | synonym | SUCCEEDED | 1 | 01f1eaf0-44ce-1282-9daa-2b1a5a0493bf |
| b-007 | mv_bakehouse_sales | synonym | SUCCEEDED | 1 | 01f1eaf0-4542-11d0-aed0-23f0e3c4e0e4 |
| b-008 | mv_bakehouse_sales | synonym | SUCCEEDED | 6 | 01f1eaf0-45c8-1769-b71c-6088f8069408 |
| b-009 | mv_bakehouse_sales | breakdown | SUCCEEDED | 6 | 01f1eaf0-4644-11d1-9a32-61ac03a7d92a |
| b-010 | mv_bakehouse_sales | ratio | SUCCEEDED | 6 | 01f1eaf0-46bd-1fcb-b6f9-b19e7038ec32 |
| b-011 | mv_bakehouse_sales | synonym | SUCCEEDED | 3 | 01f1eaf0-476f-119d-a190-41a2fa635439 |
| b-012 | mv_bakehouse_sales | ratio | SUCCEEDED | 9 | 01f1eaf0-4811-1676-8482-8232bb9f1f52 |
| b-013 | mv_bakehouse_sales | time | SUCCEEDED | 7 | 01f1eaf0-48d9-18e0-b3fd-32125de21aa5 |
| b-014 | mv_bakehouse_sales | time | SUCCEEDED | 3 | 01f1eaf0-4958-11c5-b1e3-77809364ffd6 |
| b-015 | mv_bakehouse_sales | time | SUCCEEDED | 1 | 01f1eaf0-49c9-1ed4-86c9-2d999b7d071f |
| b-016 | mv_bakehouse_sales | time | SUCCEEDED | 17 | 01f1eaf0-4a4a-1f9b-96e0-f968657fcc9b |
| b-017 | mv_bakehouse_sales | synonym | SUCCEEDED | 17 | 01f1eaf0-4ae8-142f-877c-0f716c4ab64e |
| b-018 | mv_bakehouse_sales | breakdown | SUCCEEDED | 5 | 01f1eaf0-4ba5-1640-a5ae-ada2a2e4d92f |
| b-019 | mv_bakehouse_sales | edge | SUCCEEDED | 46 | 01f1eaf0-4c28-1e5f-8f64-5e7113cb2cf1 |
| b-020 | mv_bakehouse_sales | filter | SUCCEEDED | 1 | 01f1eaf0-4cbd-1c88-b409-5f09caa078fc |
| b-021 | mv_bakehouse_sales | ratio | SUCCEEDED | 9 | 01f1eaf0-4d56-1d1c-b7a9-410542890c80 |
| b-022 | mv_bakehouse_sales | breakdown | SUCCEEDED | 5 | 01f1eaf0-4e04-1159-a443-77d04fff92cf |
| b-023 | mv_bakehouse_sales | edge | SUCCEEDED | 1 | 01f1eaf0-4e9c-1656-b5fd-908f228ed2e8 |
| b-024 | mv_bakehouse_sales | filter | SUCCEEDED | 1 | 01f1eaf0-4f22-1614-a8c1-cf571342735c |
| b-025 | mv_bakehouse_sales | breakdown | SUCCEEDED | 3 | 01f1eaf0-4fad-1de5-8384-326e1f5d7738 |
| b-026 | mv_bakehouse_sales | filter | SUCCEEDED | 1 | 01f1eaf0-5048-1231-9d98-c36d99ba59cc |
| b-027 | mv_bakehouse_sales | breakdown | SUCCEEDED | 2 | 01f1eaf0-50eb-19e4-9448-6ee03d76cd4f |
| b-028 | mv_bakehouse_sales | edge | SUCCEEDED | 1 | 01f1eaf0-517f-136a-a15a-bdf62afe8db2 |
| b-029 | mv_bakehouse_sales | ratio | SUCCEEDED | 54 | 01f1eaf0-51f6-191f-a88a-04bf71e3ad11 |
| b-030 | mv_bakehouse_sales | filter | SUCCEEDED | 1 | 01f1eaf0-52a8-1292-9785-855ef5b0b724 |
| b-031 | mv_bakehouse_supplier_coverage | simple | SUCCEEDED | 1 | 01f1eaf0-5324-16db-8c68-719a4df78647 |
| b-032 | mv_bakehouse_supplier_coverage | simple | SUCCEEDED | 1 | 01f1eaf0-53f9-1598-a75e-f48133517204 |
| b-033 | mv_bakehouse_supplier_coverage | simple | SUCCEEDED | 1 | 01f1eaf0-54a7-195c-8ed4-a84484748eb4 |
| b-034 | mv_bakehouse_supplier_coverage | synonym | SUCCEEDED | 1 | 01f1eaf0-5526-1129-a06d-5395213e0865 |
| b-035 | mv_bakehouse_supplier_coverage | ratio | SUCCEEDED | 9 | 01f1eaf0-55a8-13fc-ad50-642d43aa2182 |
| b-036 | mv_bakehouse_supplier_coverage | ratio | SUCCEEDED | 1 | 01f1eaf0-5629-1e77-bcbb-6805ff75c52f |
| b-037 | mv_bakehouse_supplier_coverage | simple | SUCCEEDED | 1 | 01f1eaf0-56b1-15eb-8612-66da52153a89 |
| b-038 | mv_bakehouse_supplier_coverage | ratio | SUCCEEDED | 1 | 01f1eaf0-5736-183d-87eb-80984df1bd24 |
| b-039 | mv_bakehouse_supplier_coverage | edge | SUCCEEDED | 1 | 01f1eaf0-57bf-15dd-873f-cc288f201867 |
| b-040 | mv_bakehouse_supplier_coverage | edge | SUCCEEDED | 2 | 01f1eaf0-5851-13b3-9a75-459202f01d4a |
| b-041 | mv_bakehouse_supplier_coverage | breakdown | SUCCEEDED | 5 | 01f1eaf0-590b-11bf-81d1-0dcb3aa4030d |
| b-042 | mv_bakehouse_supplier_coverage | filter | SUCCEEDED | 1 | 01f1eaf0-5984-1bdc-a455-5af6b6bd37d3 |
| b-043 | mv_bakehouse_supplier_coverage | breakdown | SUCCEEDED | 7 | 01f1eaf0-5a20-1284-a6f7-c2c9519c33a3 |
| b-044 | mv_bakehouse_supplier_coverage | filter | SUCCEEDED | 1 | 01f1eaf0-5ab0-12c5-992d-8eef831fea42 |
| b-045 | mv_bakehouse_supplier_coverage | breakdown | SUCCEEDED | 6 | 01f1eaf0-5b4b-1fa4-83ee-afe992f04273 |
| b-046 | mv_bakehouse_supplier_coverage | breakdown | SUCCEEDED | 2 | 01f1eaf0-5be1-15d8-97ef-dbcacf5d50f3 |
| b-047 | mv_bakehouse_supplier_coverage | ratio | SUCCEEDED | 9 | 01f1eaf0-5c67-11b5-8966-d47d18612711 |
| b-048 | mv_bakehouse_supplier_coverage | filter | SUCCEEDED | 1 | 01f1eaf0-5cef-1152-8ee0-36b46b4cc023 |

## Coverage (own file only)

`benchmark.coverage(load_questions('docs/tuning/benchmark/group_b.yml'), [mv_bakehouse_sales.yml, mv_bakehouse_supplier_coverage.yml])`, installed SDK wheel 0.1.1:

* 48 questions; per view: `mv_bakehouse_sales` 30, `mv_bakehouse_supplier_coverage` 18 (both at least `MIN_PER_VIEW`).
* Every measure and dimension of both views tagged at least once (no zero counters).
* Types: breakdown 9, edge 5, filter 7, ratio 8, simple 9, synonym 6, time 4.
* Problems reported, which the combined set must clear and this file alone cannot: total 48 < 100; cross-view share 0%; type `cross_view` unused. These come from 10a and 10c (cross-view) in the wave gate. If the combined set is still below 100, 10c or a follow-up needs to add questions.
