# Metric View YAML Patterns (SDK conventions)

Patterns for `ontology-mv-synthesis`. Syntax is the platform `metric-views` skill's; these show the SDK conventions layered on it. Table and column names are illustrative (TPC-H style).

## Fact view with a verified many-to-one join

```yaml
# subdomain: sales
# Order-grain revenue metrics. One row of source = one order.
version: 1.1
comment: "Order-grain revenue and volume metrics. Excludes orders with status 'X' (cancelled)."

source: ${source_catalog}.${source_schema}.orders

joins:
  # verified: orders -> customer on o_custkey = c_custkey, orphan_rate 0.0
  - name: customer
    source: ${source_catalog}.${source_schema}.customer
    on: source.o_custkey = customer.c_custkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true

filter: source.o_orderstatus <> 'X'

dimensions:
  - name: Order Date
    expr: source.o_orderdate
    format:
      type: date
      date_format: year_month_day
  - name: Order Month
    expr: DATE_TRUNC('MONTH', source.o_orderdate)
  - name: Market Segment
    expr: customer.c_mktsegment
    synonyms:
      - customer segment
      - industry

measures:
  - name: Order Count
    expr: COUNT(1)
    comment: "Number of non-cancelled orders"
  - name: Revenue
    expr: SUM(source.o_totalprice)
    comment: "Gross order value in USD, before returns"
    synonyms:
      - sales
      - gross sales
      - bookings
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Average Order Value
    expr: MEASURE(`Revenue`) / MEASURE(`Order Count`)
    comment: "Revenue divided by order count"
    synonyms:
      - AOV
```

## Unverified or many-to-many relationship

No `rely`, and usually no join at all: model the other table as its own metric view at its own grain.

```yaml
# data_model_summary.md: partsupp -> lineitem verified_cardinality many_to_many
# -> no join here; inventory metrics live in mv_<domain>_inventory at partsupp grain.
```

## Materialization (threshold met: source >= 10M rows)

```yaml
materialization:
  mode: relaxed
  schedule: every 6 hours
  materialized_views:
    - name: revenue_by_month_segment
      type: aggregated
      dimensions:          # categorical grouping only: no dates at day grain, amounts or keys
        - Order Month
        - Market Segment
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
```

## Anti-patterns the validator rejects

| Pattern | Rule |
|---|---|
| `source: samples.tpch.orders` (literal catalog) | MV004 error |
| `- expr: source.*` | MV003 error |
| Two measures named `Revenue` | MV002 error |
| `rely.at_most_one_match: true` without a `# verified:` line | MV005 warning |
| Measure without `comment` | MV006 warning |
| Materialization entry without `refresh_policy`, or listing `Order Date` (day grain) / `o_orderkey` | MV007 |
