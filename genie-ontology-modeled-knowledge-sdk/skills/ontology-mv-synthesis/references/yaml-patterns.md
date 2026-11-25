# Metric View YAML Patterns (SDK conventions)

Patterns for `ontology-mv-synthesis` (Genie Ontology Modeled Knowledge SDK). Syntax is the platform `metric-views` skill's; these show the SDK conventions layered on it. Table and column names are illustrative (TPC-H style).

A pattern marked **verified (Cn)** was registered and queried on the platform, with results cross-checked against plain SQL; evidence is in `docs/research/platform-pattern-checks.md` of the SDK repository, check `Cn`.

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

## Snowflake dimension through a nested join (verified C6, C7)

A dimension reached through another join is nested under its parent, and every reference uses the **full join path** from `source`. Each nested join gets its own `# verified:` line.

```yaml
# subdomain: fulfillment
version: 1.1
comment: "Line-item-grain revenue by customer geography."
source: ${source_catalog}.${source_schema}.lineitem
joins:
  # verified: lineitem -> orders on l_orderkey = o_orderkey, orphan_rate 0.0
  - name: orders
    source: ${source_catalog}.${source_schema}.orders
    on: source.l_orderkey = orders.o_orderkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      # verified: orders -> customer on o_custkey = c_custkey, orphan_rate 0.0
      - name: customer
        source: ${source_catalog}.${source_schema}.customer
        on: orders.o_custkey = customer.c_custkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
        joins:
          # verified: customer -> nation on c_nationkey = n_nationkey, orphan_rate 0.0
          - name: customer_nation
            source: ${source_catalog}.${source_schema}.nation
            on: customer.c_nationkey = customer_nation.n_nationkey
            cardinality: many_to_one
            rely:
              at_most_one_match: true
dimensions:
  - name: Customer Nation
    expr: orders.customer.customer_nation.n_name   # full path; `customer_nation.n_name` fails (UNRESOLVED_COLUMN)
  - name: Market Segment
    expr: orders.customer.c_mktsegment
measures:
  - name: Revenue
    expr: SUM(source.l_extendedprice * (1 - source.l_discount))
    comment: "Discounted line revenue in USD"
```

When the same dimension table plays two roles (customer nation, supplier nation), give each join a role name (`customer_nation`, `supplier_nation`) and a dimension name that says the role.

## Share of total (verified C1, C3)

For "share of X" KPIs (national market share, segment share of revenue), put the denominator in a **window measure** with `range: all` over the dimension the share is taken across, then divide with `MEASURE()`. The denominator keeps every other grouped dimension (share of a nation within its year), and the query's other filters still apply.

```yaml
dimensions:
  - name: Order Year
    expr: YEAR(orders.o_orderdate)
  - name: Supplier Nation
    expr: supplier.supplier_nation.n_name
measures:
  - name: Market Volume
    expr: SUM(source.l_extendedprice * (1 - source.l_discount))
    comment: "Discounted line revenue in USD"
  - name: Market Volume All Nations
    expr: SUM(source.l_extendedprice * (1 - source.l_discount))
    comment: "Market volume across all supplier nations in the same query group (denominator of Nation Market Share)"
    window:
      - order: Supplier Nation
        range: all
  - name: Nation Market Share
    expr: MEASURE(`Market Volume`) / MEASURE(`Market Volume All Nations`)
    comment: "Fraction 0-1 of market volume supplied by the nation, within the other grouped dimensions"
    format:
      type: percentage
```

Do **not** divide by a second plain measure (``MEASURE(`Volume`) / MEASURE(`Total Volume`)``): it registers but is 1.0 at every grain (C3). A fixed LOD dimension (`SUM(x) OVER (PARTITION BY ...)` + `ANY_VALUE`) also registers (C2) but ignores query filters, so prefer the window measure for user-facing shares.

## Fixed-member share with FILTER, and ratio format (verified C4, C5)

For a share of one named member (TPC-H Q8: Brazil's share), use a `FILTER (WHERE ...)` measure; the filter may reference a dimension by name. Ratios carry `format: {type: percentage}` and a comment saying the value is a fraction 0-1: the format is display metadata and the query still returns 0-1 (build-0 obs 30).

```yaml
measures:
  - name: Brazil Volume
    expr: SUM(source.l_extendedprice * (1 - source.l_discount)) FILTER (WHERE `Supplier Nation` = 'BRAZIL')
    comment: "Discounted line revenue from Brazilian suppliers, USD"
  - name: Brazil Market Share
    expr: MEASURE(`Brazil Volume`) / MEASURE(`Market Volume`)
    comment: "Fraction 0-1 of market volume supplied from Brazil"
    format:
      type: percentage
      decimal_places:
        type: exact
        places: 2
  - name: Returned Line Count
    expr: COUNT(1) FILTER (WHERE source.l_returnflag = 'R')
    comment: "Line items with return flag R"
  - name: Return Line Rate
    expr: MEASURE(`Returned Line Count`) / COUNT(1)
    comment: "Fraction 0-1 of line items returned (not a percentage value)"
    format:
      type: percentage
```

## KPI with two candidate formulas

When research gives two defensible formulas (AOV on order header vs line basis; on-time by ship date vs receipt date), define **one measure per basis**, each named for its basis, and record an owner decision note in the session summary. Never pick one silently or reuse one name.

```yaml
# owner decision pending: AOV basis (header o_totalprice vs line revenue); both exposed
measures:
  - name: Average Order Value (Header)
    expr: MEASURE(`Revenue`) / MEASURE(`Order Count`)
    comment: "Order header total price per non-cancelled order, USD"
  - name: Average Order Value (Line Revenue)
    expr: MEASURE(`Line Revenue`) / MEASURE(`Order Count`)
    comment: "Discounted line revenue per order, USD"
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

## Errors only registration catches (verified C7, C8)

The static validator and `EXPLAIN` of the rendered DDL do not catch these; the platform dry run (register under `scratch_<view>`, then query) does:

| Pattern | Registration error |
|---|---|
| Unknown column in a join path | `FIELD_NOT_FOUND` |
| Nested join referenced by the leaf name only | `UNRESOLVED_COLUMN.WITH_SUGGESTION` |
| `FILTER (WHERE ...)` on an undefined dimension | `UNRESOLVED_COLUMN.WITH_SUGGESTION` |
| `version: 1` | `METRIC_VIEW_INVALID_VIEW_DEFINITION ... Invalid YAML version` |
| Materialization dimension that is not defined | `METRIC_VIEW_INVALID_VIEW_DEFINITION ... Invalid dimensions in materialized view` |
