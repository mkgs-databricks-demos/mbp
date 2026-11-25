# TPC-H Genie Agent validation (dev)

Build 0, wave 0-8, session 15. Bundle `examples/tpch/ontology-genie-agents`, target `dev`, agent `tpch_supply_chain_agent`. Identifiers below are tokenized (`${target_catalog}.${target_schema}`); resolved names and ids are in the session summary only.

## Deployment checks

| Check | Result |
|---|---|
| `bundle validate --strict --target dev` (after render) | pass |
| `bundle plan --target dev` | 2 to add (space + permissions), 0 change, 0 delete |
| `bundle deploy --target dev` | exit 0 (2 created) |
| Space warehouse equals `warehouse_id` override | pass |
| `DESCRIBE` each of the 7 table identifiers in the space | pass (7/7 resolve) |
| `EXPLAIN` each of the 3 example SQLs in the space | pass (3/3 physical plans) |

## Probe questions

Run with `genie_ontology_modeled_knowledge_sdk.benchmark.run_benchmark` (new conversation per question, timeout 300 s). Pass = Genie returned SQL and the statement SUCCEEDED; answer content is judged in session 16.

**Result: 3 of 3 probes generated SQL and the statement SUCCEEDED.**

| ID | Question | Message status | SQL generated | Statement status | Rows | Seconds |
|---|---|---|---|---|---|---|
| p1 | What is the on-time shipping rate by ship mode? | COMPLETED | yes | SUCCEEDED | 7 | 26.5 |
| p2 | What is the return rate by customer nation? | COMPLETED | yes | SUCCEEDED | 25 | 18.1 |
| p3 | What was revenue by market segment for each order year? | COMPLETED | yes | SUCCEEDED | 35 | 17.9 |

## SQL generated

### p1

```sql
SELECT
  `Ship Mode`,
  MEASURE(`On-Time Shipping Rate`) AS `On-Time Shipping Rate`
FROM `${target_catalog}`.`${target_schema}`.`mv_tpch_supply_chain_fulfillment`
WHERE `Ship Mode` IS NOT NULL
GROUP BY ALL
ORDER BY `On-Time Shipping Rate` DESC
```

### p2

```sql
SELECT
  `Customer Nation`,
  MEASURE(`Return Rate`) AS `return_rate`
FROM `${target_catalog}`.`${target_schema}`.`mv_tpch_supply_chain_returns`
WHERE `Customer Nation` IS NOT NULL
GROUP BY ALL
ORDER BY `return_rate` DESC
```

### p3

```sql
SELECT
  `Order Year`,
  `Market Segment`,
  MEASURE(`Revenue`) AS `Revenue`
FROM `${target_catalog}`.`${target_schema}`.`mv_tpch_supply_chain_revenue`
WHERE `Order Year` IS NOT NULL
  AND `Market Segment` IS NOT NULL
GROUP BY ALL
ORDER BY `Order Year` ASC, `Revenue` DESC
```

## Notes for prd

Users other than the owner need `USE CATALOG`, `USE SCHEMA` and `SELECT` on the metric views (plus `CAN_RUN` on the agent, granted to `consumer_group` by the bundle) to use the agent. Dev is owner-only.
