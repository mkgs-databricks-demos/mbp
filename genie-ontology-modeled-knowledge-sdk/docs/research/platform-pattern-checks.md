# Platform Pattern Checks (build-1 session 25)

Metric view YAML patterns that `ontology-mv-synthesis` documents, checked on the platform by registering scratch metric views (`CREATE OR REPLACE VIEW <sdk_schema>.scratch_* WITH METRICS LANGUAGE YAML`) over `samples.tpch` and querying them. Every query result was cross-checked against the same aggregate written in plain SQL over the source tables. Runtime: serverless, DBR 19.x. `<sdk_schema>` is the SDK bundle's schema (from `databricks bundle summary -t dev`); no catalog or schema names are recorded here.

Patterns in [skills/ontology-mv-synthesis/references/yaml-patterns.md](../../skills/ontology-mv-synthesis/references/yaml-patterns.md) that cite a check id below are **verified**.

## Results

| Id | Observation | Pattern | Scratch view | Result | Evidence / error text |
|---|---|---|---|---|---|
| C1 | 16 | Share of total with a **window measure** (`window: [{order: <dim>, range: all}]`) as the denominator, and a ratio ``MEASURE(`Part`) / MEASURE(`Part All <dim>`)`` | `scratch_share_window` | **pass** | Registers. Grouped by order year and supplier nation, the share matches plain SQL `v / SUM(v) OVER (PARTITION BY year)` to 6 decimals (e.g. 1995: 0.039179, 0.040847, 0.039684 for the first three nations), and the shares sum to 1.0 per year in the years checked (1992-1994: 1.000000, 1.000001, 1.000001, rounding). The denominator keeps every other grouped dimension, so it is "share within the rest of the query grain" |
| C2 | 16 | Share of total with a **fixed LOD dimension** (`SUM(x) OVER (PARTITION BY <expr>)`) and ``MEASURE(`Part`) / ANY_VALUE(`Total Dim`)`` | `scratch_share_fixed_lod` | **pass** (with caveat) | Registers and queries; grouped at the partition grain (order year) it returns 1.000000 as expected. Caveat (platform skill): fixed LOD ignores query filters, so the denominator does not follow a `WHERE` on another dimension. Use C1 for user-facing share KPIs |
| C3 | 16 | Naive share: ``MEASURE(`Volume`) / MEASURE(`Total Volume`)`` where both are plain aggregates | `scratch_share_naive` | **fail (as a share)** | Registers, but returns 1.0000000000 at every grain (both sides resolve at the same GROUP BY). Not a share-of-total pattern; documented as an anti-pattern |
| C4 | 16, 30 | `FILTER (WHERE <dim> = '<value>')` measure and a ratio over it (fixed-member share, TPC-H Q8 style), plus a `FILTER` count ratio | `scratch_filter_ratio` | **pass** | Brazil share by ship year matches plain SQL `SUM(CASE ...) / SUM(...)` (1992: 0.039594, 1993: 0.039569, 1994: 0.039592); `Return Line Rate` matches `AVG(CASE WHEN l_returnflag = 'R' ...)` exactly. The `FILTER` may reference a dimension by name (`` `Supplier Nation` ``) |
| C5 | 30 | `format: {type: percentage}` (with and without `decimal_places: {type: exact, places: 2}`) on a ratio measure | `scratch_filter_ratio` | **pass** | Registers; `DESCRIBE TABLE EXTENDED ... AS JSON` shows `metadata.format.percentage` on both ratio measures. The query value stays a 0-1 fraction (0.0396, 0.5000); format is display metadata only, so the comment must still say "fraction 0-1" |
| C6 | 17 | Snowflake dimension through a **nested join path**: `joins` nested three deep (lineitem -> orders -> customer -> customer_nation), dimension `expr: orders.customer.customer_nation.n_name`; also a nested supplier -> supplier_nation path `supplier.supplier_nation.n_name` (C1, C4) | `scratch_nested_join` | **pass** | Registers; revenue by customer nation matches plain SQL over the four joined tables for the nations compared (ALGERIA 43267609726.3182, ARGENTINA 43787525060.6422, BRAZIL 43548078846.5385) |
| C7 | 17 | Nested join referenced by the **leaf join name only** (`customer_nation.n_name`) | none created (registration failed) | **fail** (expected) | `[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter with name `customer_nation`.`n_name` cannot be resolved. ... SQLSTATE: 42703` |
| C8 | 20 | `EXPLAIN CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML` as a cheap dry run, on a valid definition and on five broken ones | none created | **fail** (EXPLAIN catches nothing) | On every definition, valid or broken, `EXPLAIN` returns a plan `Execute CreateMetricViewCommand` with the YAML as a literal: it neither parses the YAML nor resolves columns. No view is created by `EXPLAIN`. The table below lists what registration caught and `EXPLAIN` did not |

### C8 detail: EXPLAIN vs registration

Each broken definition is the C6 view with one change.

| Broken definition | `EXPLAIN` | Registration (`CREATE OR REPLACE`) error |
|---|---|---|
| Unknown column (`orders.customer.c_nope`) | plan returned, no error | `[FIELD_NOT_FOUND] No such struct field `c_nope` in `c_custkey`, ... SQLSTATE: 42704` |
| Leaf-only nested path (`customer_nation.n_name`) | plan returned, no error | `[UNRESOLVED_COLUMN.WITH_SUGGESTION] ... `customer_nation`.`n_name` cannot be resolved ... SQLSTATE: 42703` |
| `FILTER` on an undefined dimension | plan returned, no error | `[UNRESOLVED_COLUMN.WITH_SUGGESTION] ... `No Such Dim` cannot be resolved ... SQLSTATE: 42703` |
| `version: 1` | plan returned, no error | `[METRIC_VIEW_INVALID_VIEW_DEFINITION] ... Invalid YAML version: 1. SQLSTATE: 42K0E` |
| Materialization dimension not defined | plan returned, no error | `[METRIC_VIEW_INVALID_VIEW_DEFINITION] ... Invalid dimensions in materialized view: No Such Dim. SQLSTATE: 42K0E` |
| Valid definition | plan returned, no error | (not registered under the EXPLAIN name; `information_schema.tables` shows no such view afterwards) |

**Conclusion for obs 20:** `EXPLAIN` of the rendered DDL is not a dry run for metric views. The platform dry run is registration into a scratch name in a scratch schema (`scratch_<view>`), then a `SELECT ... MEASURE(...) ... LIMIT 1` per view. A failed registration creates nothing.

## Statements run

Only `CREATE OR REPLACE VIEW <sdk_schema>.scratch_* WITH METRICS LANGUAGE YAML` (DDL), `EXPLAIN` of the same statements, and read-only `SELECT` / `DESCRIBE`. No `DROP`.

| Statement | Outcome |
|---|---|
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_share_window ...` | created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_share_fixed_lod ...` | created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_filter_ratio ...` | created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_nested_join ...` | created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_share_naive ...` | created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_broken_column ...` | failed, nothing created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_broken_path ...` | failed, nothing created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_broken_filter_ref ...` | failed, nothing created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_broken_version ...` | failed, nothing created |
| `CREATE OR REPLACE VIEW <sdk_schema>.scratch_broken_materialization ...` | failed, nothing created |
| `EXPLAIN` of the five broken statements and of `... scratch_explain_valid ...` | plan only, nothing created |

Cleanup (owner step after the build): drop the five created `scratch_*` views.

## C1 YAML (reference)

```yaml
version: 1.1
source: samples.tpch.lineitem
joins:
  - name: supplier
    source: samples.tpch.supplier
    on: source.l_suppkey = supplier.s_suppkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      - name: supplier_nation
        source: samples.tpch.nation
        on: supplier.s_nationkey = supplier_nation.n_nationkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
  - name: orders
    source: samples.tpch.orders
    on: source.l_orderkey = orders.o_orderkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
dimensions:
  - name: Order Year
    expr: YEAR(orders.o_orderdate)
  - name: Supplier Nation
    expr: supplier.supplier_nation.n_name
measures:
  - name: Market Volume
    expr: SUM(source.l_extendedprice * (1 - source.l_discount))
  - name: Market Volume All Nations
    expr: SUM(source.l_extendedprice * (1 - source.l_discount))
    window:
      - order: Supplier Nation
        range: all
  - name: Nation Market Share
    expr: MEASURE(`Market Volume`) / MEASURE(`Market Volume All Nations`)
    format:
      type: percentage
```

(The scratch views used literal `samples.tpch` sources because they were registered directly; SDK YAML uses the `${source_catalog}.${source_schema}` tokens.)
