CREATE OR REPLACE VIEW ${target_catalog}.${target_schema}.mv_tpch_supply_chain_fulfillment
WITH METRICS
LANGUAGE YAML
AS $$
# subdomain: fulfillment
# Line-item-grain shipping and delivery metrics (TPC-H Q12, SCOR RL.3.1 / RS.3.111 proxies).
# KPIs: On-Time Shipping Rate, Late Receipt, Order Fulfillment Cycle Time.
version: 1.1
comment: "Fulfillment metrics at order-line grain: on-time shipping and delivery against the commit date, late receipts and order-to-receipt cycle time, by ship mode, order priority and ship/receipt month. Commit date stands in for the customer request date (TPC-H has no request date)."

source: samples.tpch.lineitem

joins:
  # verified: lineitem -> orders on l_orderkey = o_orderkey, orphan_rate 0.0
  - name: orders
    source: samples.tpch.orders
    on: source.l_orderkey = orders.o_orderkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true

dimensions:
  - name: Ship Date
    expr: source.l_shipdate
    comment: "Date the line item shipped"
    format:
      type: date
      date_format: year_month_day
  - name: Ship Month
    expr: DATE_TRUNC('MONTH', source.l_shipdate)
    comment: "Calendar month the line item shipped"
  - name: Receipt Date
    expr: source.l_receiptdate
    comment: "Date the customer received the line item"
    format:
      type: date
      date_format: year_month_day
  - name: Receipt Month
    expr: DATE_TRUNC('MONTH', source.l_receiptdate)
    comment: "Calendar month the line item was received"
  - name: Receipt Year
    expr: YEAR(source.l_receiptdate)
    comment: "Calendar year the line item was received (Q12 filters one receipt year)"
  - name: Ship Mode
    expr: source.l_shipmode
    synonyms:
      - shipping mode
      - transport mode
  - name: Line Status
    expr: source.l_linestatus
    comment: "Line status code ('O' open, 'F' fulfilled)"
  - name: Order Priority
    expr: orders.o_orderpriority
    synonyms:
      - priority
  - name: High Priority
    expr: orders.o_orderpriority IN ('1-URGENT', '2-HIGH')
    comment: "True for 1-URGENT and 2-HIGH orders (TPC-H Q12 high-priority definition)"

measures:
  - name: Line Item Count
    expr: COUNT(1)
    comment: "Number of order lines"
  - name: On-Time Shipped Line Count
    expr: COUNT(1) FILTER (WHERE source.l_shipdate <= source.l_commitdate)
    comment: "Lines shipped on or before their commit date"
  - name: On-Time Shipping Rate
    expr: MEASURE(`On-Time Shipped Line Count`) / MEASURE(`Line Item Count`)
    comment: "Share of lines shipped on or before the commit date (ship-based proxy for SCOR delivery performance; seed definition)"
    synonyms:
      - on-time shipping
      - OTS
    format:
      type: percentage
  - name: Late Receipt Count
    expr: COUNT(1) FILTER (WHERE source.l_receiptdate > source.l_commitdate)
    comment: "Lines received after their commit date"
    synonyms:
      - late deliveries
      - received after commit date
  - name: On-Time Delivery Rate
    expr: 1 - MEASURE(`Late Receipt Count`) / MEASURE(`Line Item Count`)
    comment: "Share of lines received on or before the commit date (receipt-based proxy for SCOR RL.3.1; line basis, not order basis)"
    synonyms:
      - on-time delivery rate
      - delivery performance
      - OTD
    format:
      type: percentage
  - name: Q12 Late Receipt Count
    expr: COUNT(1) FILTER (WHERE source.l_receiptdate > source.l_commitdate AND source.l_shipdate < source.l_commitdate)
    comment: "Lines shipped before the commit date but still received after it (TPC-H Q12 basis); group by Ship Mode and High Priority"
  - name: Average Fulfillment Cycle Days
    expr: AVG(DATEDIFF(source.l_receiptdate, orders.o_orderdate))
    comment: "Mean days from order date to line receipt (proxy for SCOR order fulfillment cycle time, line basis)"
    synonyms:
      - order cycle time
      - lead time
      - OFCT
  - name: Average Ship Lag Days
    expr: AVG(DATEDIFF(source.l_shipdate, orders.o_orderdate))
    comment: "Mean days from order date to line shipment"
  - name: Average Transit Days
    expr: AVG(DATEDIFF(source.l_receiptdate, source.l_shipdate))
    comment: "Mean days from shipment to receipt"

materialization:
  mode: relaxed
  schedule: every 6 hours
  materialized_views:
    - name: fulfillment_by_ship_month_mode_priority
      type: aggregated
      dimensions:
        - Ship Month
        - Ship Mode
        - Order Priority
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
$$;

CREATE OR REPLACE VIEW ${target_catalog}.${target_schema}.mv_tpch_supply_chain_market_share
WITH METRICS
LANGUAGE YAML
AS $$
# subdomain: sales
# Line-item-grain market volume with both customer and supplier geography (TPC-H Q8).
# KPIs: National Market Share (supplier nation volume / total volume).
version: 1.1
comment: "Market volume at order-line grain with supplier geography and customer geography side by side, for national market share analysis (TPC-H Q8): the share of volume supplied by one supplier nation within a customer region, by order year and part type."

source: samples.tpch.lineitem

joins:
  # verified: lineitem -> orders on l_orderkey = o_orderkey, orphan_rate 0.0
  - name: orders
    source: samples.tpch.orders
    on: source.l_orderkey = orders.o_orderkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      # verified: orders -> customer on o_custkey = c_custkey, orphan_rate 0.0
      - name: customer
        source: samples.tpch.customer
        on: orders.o_custkey = customer.c_custkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
        joins:
          # verified: customer -> nation on c_nationkey = n_nationkey, orphan_rate 0.0
          - name: customer_nation
            source: samples.tpch.nation
            on: customer.c_nationkey = customer_nation.n_nationkey
            cardinality: many_to_one
            rely:
              at_most_one_match: true
            joins:
              # verified: nation -> region on n_regionkey = r_regionkey, orphan_rate 0.0
              - name: customer_region
                source: samples.tpch.region
                on: customer_nation.n_regionkey = customer_region.r_regionkey
                cardinality: many_to_one
                rely:
                  at_most_one_match: true
  # verified: lineitem -> supplier on l_suppkey = s_suppkey, orphan_rate 0.0
  - name: supplier
    source: samples.tpch.supplier
    on: source.l_suppkey = supplier.s_suppkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      # verified: supplier -> nation on s_nationkey = n_nationkey, orphan_rate 0.0
      - name: supplier_nation
        source: samples.tpch.nation
        on: supplier.s_nationkey = supplier_nation.n_nationkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
  # verified: lineitem -> part on l_partkey = p_partkey, orphan_rate 0.0
  - name: part
    source: samples.tpch.part
    on: source.l_partkey = part.p_partkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true

dimensions:
  - name: Order Year
    expr: YEAR(orders.o_orderdate)
    comment: "Calendar year the order was placed (Q8 compares 1995 and 1996)"
  - name: Customer Nation
    expr: orders.customer.customer_nation.n_name
    comment: "Nation of the ordering customer"
  - name: Customer Region
    expr: orders.customer.customer_nation.customer_region.r_name
    comment: "Region of the ordering customer; Q8 restricts the market to one customer region"
  - name: Supplier Nation
    expr: supplier.supplier_nation.n_name
    comment: "Nation of the supplier that fulfilled the line; the numerator nation of national market share"
    synonyms:
      - supplying nation
      - vendor country
  - name: Part Type
    expr: part.p_type
    comment: "Part type; Q8 restricts the market to one part type"
    synonyms:
      - product type

measures:
  - name: Market Volume
    expr: SUM(source.l_extendedprice * (1 - source.l_discount))
    comment: "Discounted line revenue in USD used as market volume (TPC-H Q8 volume)"
    synonyms:
      - volume
      - market revenue
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Line Item Count
    expr: COUNT(1)
    comment: "Number of order lines in the market"

materialization:
  mode: relaxed
  schedule: every 6 hours
  materialized_views:
    - name: volume_by_year_region_supplier_nation
      type: aggregated
      dimensions:
        - Order Year
        - Customer Region
        - Supplier Nation
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
$$;

CREATE OR REPLACE VIEW ${target_catalog}.${target_schema}.mv_tpch_supply_chain_orders
WITH METRICS
LANGUAGE YAML
AS $$
# subdomain: sales
# Order-grain metrics. One row of source = one order header.
# KPIs: Order Volume. Header-basis order value lives here; line-item AOV is in mv_tpch_supply_chain_revenue.
version: 1.1
comment: "Order header metrics at order grain: order volume, order total price and ordering customers, by order date, status, priority, customer segment and customer geography. Customer counts here cover only customers who ordered (one third of customers have no orders)."

source: samples.tpch.orders

joins:
  # verified: orders -> customer on o_custkey = c_custkey, orphan_rate 0.0
  - name: customer
    source: samples.tpch.customer
    on: source.o_custkey = customer.c_custkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      # verified: customer -> nation on c_nationkey = n_nationkey, orphan_rate 0.0
      - name: customer_nation
        source: samples.tpch.nation
        on: customer.c_nationkey = customer_nation.n_nationkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
        joins:
          # verified: nation -> region on n_regionkey = r_regionkey, orphan_rate 0.0
          - name: customer_region
            source: samples.tpch.region
            on: customer_nation.n_regionkey = customer_region.r_regionkey
            cardinality: many_to_one
            rely:
              at_most_one_match: true

dimensions:
  - name: Order Date
    expr: source.o_orderdate
    comment: "Date the order was placed (1992-01-01 to 1998-08-02)"
    format:
      type: date
      date_format: year_month_day
  - name: Order Month
    expr: DATE_TRUNC('MONTH', source.o_orderdate)
    comment: "Calendar month the order was placed"
  - name: Order Year
    expr: YEAR(source.o_orderdate)
    comment: "Calendar year the order was placed"
  - name: Order Status
    expr: source.o_orderstatus
    comment: "Order status code ('F' all lines fulfilled, 'O' all lines open, 'P' partially fulfilled)"
  - name: Order Priority
    expr: source.o_orderpriority
    synonyms:
      - priority
  - name: High Priority
    expr: source.o_orderpriority IN ('1-URGENT', '2-HIGH')
    comment: "True for 1-URGENT and 2-HIGH orders (TPC-H Q12 high-priority definition)"
  - name: Market Segment
    expr: customer.c_mktsegment
    synonyms:
      - customer segment
  - name: Customer Nation
    expr: customer.customer_nation.n_name
    comment: "Nation of the ordering customer"
    synonyms:
      - customer country
  - name: Customer Region
    expr: customer.customer_nation.customer_region.r_name
    comment: "Region of the ordering customer"

measures:
  - name: Order Count
    expr: COUNT(1)
    comment: "Number of orders (one source row per order)"
    synonyms:
      - order volume
      - number of orders
  - name: Order Total Price
    expr: SUM(source.o_totalprice)
    comment: "Sum of order header totals in USD (after discount, including tax). Never sum this through line items"
    synonyms:
      - order value
      - bookings
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Average Order Total
    expr: MEASURE(`Order Total Price`) / MEASURE(`Order Count`)
    comment: "Header-basis average order total in USD; the line-item-basis Average Order Value is in mv_tpch_supply_chain_revenue"
    format:
      type: currency
      currency_code: USD
  - name: Ordering Customer Count
    expr: COUNT(DISTINCT source.o_custkey)
    comment: "Distinct customers with at least one order in scope"
  - name: Orders per Customer
    expr: MEASURE(`Order Count`) / MEASURE(`Ordering Customer Count`)
    comment: "Average orders per ordering customer"

materialization:
  mode: relaxed
  schedule: every 6 hours
  materialized_views:
    - name: orders_by_month_segment_region
      type: aggregated
      dimensions:
        - Order Month
        - Order Status
        - Order Priority
        - Market Segment
        - Customer Region
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
$$;

CREATE OR REPLACE VIEW ${target_catalog}.${target_schema}.mv_tpch_supply_chain_profit
WITH METRICS
LANGUAGE YAML
AS $$
# subdomain: procurement
# Line-item-grain profit metrics (TPC-H Q9). Supply cost is read per line through the
# composite lineitem -> partsupp join (many_to_one), so partsupp measures are not fanned out.
# KPIs: Profit (product type profit).
version: 1.1
comment: "Profit metrics at order-line grain: discounted revenue minus supply cost of goods (supply cost x quantity), by part type, brand, manufacturer, supplier nation and order year (TPC-H Q9 product type profit)."

source: samples.tpch.lineitem

joins:
  # verified: lineitem -> partsupp on l_partkey = ps_partkey, l_suppkey = ps_suppkey, orphan_rate 0.0
  - name: partsupp
    source: samples.tpch.partsupp
    on: source.l_partkey = partsupp.ps_partkey AND source.l_suppkey = partsupp.ps_suppkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
  # verified: lineitem -> part on l_partkey = p_partkey, orphan_rate 0.0
  - name: part
    source: samples.tpch.part
    on: source.l_partkey = part.p_partkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
  # verified: lineitem -> supplier on l_suppkey = s_suppkey, orphan_rate 0.0
  - name: supplier
    source: samples.tpch.supplier
    on: source.l_suppkey = supplier.s_suppkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      # verified: supplier -> nation on s_nationkey = n_nationkey, orphan_rate 0.0
      - name: supplier_nation
        source: samples.tpch.nation
        on: supplier.s_nationkey = supplier_nation.n_nationkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
  # verified: lineitem -> orders on l_orderkey = o_orderkey, orphan_rate 0.0
  - name: orders
    source: samples.tpch.orders
    on: source.l_orderkey = orders.o_orderkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true

dimensions:
  - name: Order Year
    expr: YEAR(orders.o_orderdate)
    comment: "Calendar year the order was placed (Q9 reports profit by nation and year)"
  - name: Part Type
    expr: part.p_type
    synonyms:
      - product type
  - name: Part Brand
    expr: part.p_brand
    synonyms:
      - brand
  - name: Manufacturer
    expr: part.p_mfgr
    synonyms:
      - mfgr
  - name: Part Name
    expr: part.p_name
    comment: "Part name; Q9 filters parts whose name contains a color word"
  - name: Supplier Nation
    expr: supplier.supplier_nation.n_name
    comment: "Nation of the supplier that fulfilled the line"
    synonyms:
      - vendor country

measures:
  - name: Revenue
    expr: SUM(source.l_extendedprice * (1 - source.l_discount))
    comment: "Net revenue in USD: extended price after discount, before tax"
    synonyms:
      - net revenue
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Cost of Goods Sold
    expr: SUM(partsupp.ps_supplycost * source.l_quantity)
    comment: "Supply cost in USD of the units sold: the supplier's unit supply cost for the part times line quantity"
    synonyms:
      - COGS
      - supply cost of goods
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Profit
    expr: MEASURE(`Revenue`) - MEASURE(`Cost of Goods Sold`)
    comment: "Net revenue minus cost of goods sold in USD (TPC-H Q9 amount)"
    synonyms:
      - product type profit
      - gross profit
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Profit Margin
    expr: MEASURE(`Profit`) / MEASURE(`Revenue`)
    comment: "Profit as a share of net revenue"
    synonyms:
      - margin
    format:
      type: percentage
  - name: Quantity
    expr: SUM(source.l_quantity)
    comment: "Units sold"

materialization:
  mode: relaxed
  schedule: every 6 hours
  materialized_views:
    - name: profit_by_year_nation_mfgr
      type: aggregated
      dimensions:
        - Order Year
        - Supplier Nation
        - Manufacturer
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
$$;

CREATE OR REPLACE VIEW ${target_catalog}.${target_schema}.mv_tpch_supply_chain_returns
WITH METRICS
LANGUAGE YAML
AS $$
# subdomain: fulfillment
# Line-item-grain return metrics (TPC-H Q10, SCOR AM.3.8 proxy).
# KPIs: Return Rate, Returned Item Revenue Lost.
version: 1.1
comment: "Return metrics at order-line grain: returned revenue lost, returned quantity and return rates by quantity and by line, by customer, customer nation, ship mode and order month. A line is returned when its return flag is 'R'; TPC-H has no weight column, so return rate uses quantity or line count."

source: samples.tpch.lineitem

joins:
  # verified: lineitem -> orders on l_orderkey = o_orderkey, orphan_rate 0.0
  - name: orders
    source: samples.tpch.orders
    on: source.l_orderkey = orders.o_orderkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      # verified: orders -> customer on o_custkey = c_custkey, orphan_rate 0.0
      - name: customer
        source: samples.tpch.customer
        on: orders.o_custkey = customer.c_custkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
        joins:
          # verified: customer -> nation on c_nationkey = n_nationkey, orphan_rate 0.0
          - name: customer_nation
            source: samples.tpch.nation
            on: customer.c_nationkey = customer_nation.n_nationkey
            cardinality: many_to_one
            rely:
              at_most_one_match: true

dimensions:
  - name: Order Month
    expr: DATE_TRUNC('MONTH', orders.o_orderdate)
    comment: "Calendar month the order was placed (Q10 filters one order quarter)"
  - name: Order Quarter
    expr: DATE_TRUNC('QUARTER', orders.o_orderdate)
    comment: "Calendar quarter the order was placed"
  - name: Return Flag
    expr: source.l_returnflag
    comment: "'R' = returned"
    synonyms:
      - returned indicator
  - name: Ship Mode
    expr: source.l_shipmode
    synonyms:
      - shipping mode
  - name: Customer Key
    expr: orders.o_custkey
    comment: "Customer identifier (Q10 ranks customers by returned revenue)"
  - name: Customer Name
    expr: orders.customer.c_name
    comment: "Synthetic customer name"
  - name: Market Segment
    expr: orders.customer.c_mktsegment
    synonyms:
      - customer segment
  - name: Customer Nation
    expr: orders.customer.customer_nation.n_name
    comment: "Nation of the ordering customer"

measures:
  - name: Returned Revenue
    expr: SUM(source.l_extendedprice * (1 - source.l_discount)) FILTER (WHERE source.l_returnflag = 'R')
    comment: "Discounted revenue in USD on returned lines (TPC-H Q10 revenue lost)"
    synonyms:
      - revenue lost to returns
      - returned item revenue
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Returned Quantity
    expr: SUM(source.l_quantity) FILTER (WHERE source.l_returnflag = 'R')
    comment: "Units on returned lines"
  - name: Shipped Quantity
    expr: SUM(source.l_quantity)
    comment: "Units on all lines in scope"
  - name: Return Rate
    expr: MEASURE(`Returned Quantity`) / MEASURE(`Shipped Quantity`)
    comment: "Returned units over all units (quantity proxy for SCOR return rate, which is weight based)"
    synonyms:
      - product return rate
      - returns percentage
    format:
      type: percentage
  - name: Returned Line Count
    expr: COUNT(1) FILTER (WHERE source.l_returnflag = 'R')
    comment: "Number of returned lines"
  - name: Line Item Count
    expr: COUNT(1)
    comment: "Number of order lines"
  - name: Return Line Rate
    expr: MEASURE(`Returned Line Count`) / MEASURE(`Line Item Count`)
    comment: "Returned lines over all lines (line-count basis)"
    format:
      type: percentage

materialization:
  mode: relaxed
  schedule: every 6 hours
  materialized_views:
    - name: returns_by_quarter_nation_segment
      type: aggregated
      dimensions:
        - Order Quarter
        - Customer Nation
        - Market Segment
        - Return Flag
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
$$;

CREATE OR REPLACE VIEW ${target_catalog}.${target_schema}.mv_tpch_supply_chain_revenue
WITH METRICS
LANGUAGE YAML
AS $$
# subdomain: sales
# Line-item-grain sales metrics (TPC-H Q1, Q5, Q6). One row of source = one order line.
# KPIs: Revenue, Gross Charge, Discount Revenue, Average Order Value (line-item basis).
version: 1.1
comment: "Sales revenue metrics at order-line grain: discounted revenue, gross sales, discount amount and charged amount (with tax), by order date, customer segment and customer geography. Never sums the order header total, so there is no fan-out double counting."

source: samples.tpch.lineitem

joins:
  # verified: lineitem -> orders on l_orderkey = o_orderkey, orphan_rate 0.0
  - name: orders
    source: samples.tpch.orders
    on: source.l_orderkey = orders.o_orderkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      # verified: orders -> customer on o_custkey = c_custkey, orphan_rate 0.0
      - name: customer
        source: samples.tpch.customer
        on: orders.o_custkey = customer.c_custkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
        joins:
          # verified: customer -> nation on c_nationkey = n_nationkey, orphan_rate 0.0
          - name: customer_nation
            source: samples.tpch.nation
            on: customer.c_nationkey = customer_nation.n_nationkey
            cardinality: many_to_one
            rely:
              at_most_one_match: true
            joins:
              # verified: nation -> region on n_regionkey = r_regionkey, orphan_rate 0.0
              - name: customer_region
                source: samples.tpch.region
                on: customer_nation.n_regionkey = customer_region.r_regionkey
                cardinality: many_to_one
                rely:
                  at_most_one_match: true

dimensions:
  - name: Order Date
    expr: orders.o_orderdate
    comment: "Date the order was placed (1992-01-01 to 1998-08-02)"
    format:
      type: date
      date_format: year_month_day
  - name: Order Month
    expr: DATE_TRUNC('MONTH', orders.o_orderdate)
    comment: "Calendar month the order was placed"
  - name: Order Year
    expr: YEAR(orders.o_orderdate)
    comment: "Calendar year the order was placed"
  - name: Ship Date
    expr: source.l_shipdate
    comment: "Date the line item shipped"
    format:
      type: date
      date_format: year_month_day
  - name: Ship Month
    expr: DATE_TRUNC('MONTH', source.l_shipdate)
    comment: "Calendar month the line item shipped (TPC-H Q1 cuts on ship date)"
  - name: Return Flag
    expr: source.l_returnflag
    comment: "'R' = returned; TPC-H Q1 groups pricing by return flag and line status"
    synonyms:
      - returned indicator
  - name: Line Status
    expr: source.l_linestatus
    comment: "Line status code ('O' open, 'F' fulfilled)"
  - name: Ship Mode
    expr: source.l_shipmode
    synonyms:
      - shipping mode
      - transport mode
  - name: Order Priority
    expr: orders.o_orderpriority
    synonyms:
      - priority
  - name: Market Segment
    expr: orders.customer.c_mktsegment
    synonyms:
      - customer segment
  - name: Customer Nation
    expr: orders.customer.customer_nation.n_name
    comment: "Nation of the ordering customer"
    synonyms:
      - customer country
  - name: Customer Region
    expr: orders.customer.customer_nation.customer_region.r_name
    comment: "Region of the ordering customer (TPC-H Q5 local supplier volume filters on it)"

measures:
  - name: Revenue
    expr: SUM(source.l_extendedprice * (1 - source.l_discount))
    comment: "Net revenue in USD: extended price after discount, before tax (TPC-H sum_disc_price)"
    synonyms:
      - net revenue
      - discounted revenue
      - sum_disc_price
      - volume
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Gross Sales
    expr: SUM(source.l_extendedprice)
    comment: "Undiscounted extended price in USD (quantity x retail price; never multiply by quantity again)"
    synonyms:
      - extended price
      - gross price
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Discount Revenue
    expr: SUM(source.l_extendedprice * source.l_discount)
    comment: "Revenue given up through discounts in USD (TPC-H Q6 forecast revenue change)"
    synonyms:
      - discount amount
      - forecast revenue change
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Gross Charge
    expr: SUM(source.l_extendedprice * (1 - source.l_discount) * (1 + source.l_tax))
    comment: "Amount charged to customers in USD after discount and including tax (TPC-H sum_charge)"
    synonyms:
      - sum_charge
      - charged amount
      - revenue including tax
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Quantity
    expr: SUM(source.l_quantity)
    comment: "Units ordered across order lines"
  - name: Line Item Count
    expr: COUNT(1)
    comment: "Number of order lines"
  - name: Order Count
    expr: COUNT(DISTINCT source.l_orderkey)
    comment: "Distinct orders with at least one line in scope"
  - name: Average Order Value
    expr: MEASURE(`Revenue`) / MEASURE(`Order Count`)
    comment: "Net revenue per order (line-item basis); differs from the header-basis Average Order Total in mv_tpch_supply_chain_orders by discount and tax"
    synonyms:
      - AOV
      - revenue per order
    format:
      type: currency
      currency_code: USD
  - name: Average Discount
    expr: AVG(source.l_discount)
    comment: "Mean line discount rate (0.00 to 0.10)"
    format:
      type: percentage

materialization:
  mode: relaxed
  schedule: every 6 hours
  materialized_views:
    - name: revenue_by_month_segment_region
      type: aggregated
      dimensions:
        - Order Month
        - Market Segment
        - Customer Region
        - Order Priority
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
    - name: pricing_summary_by_ship_month
      type: aggregated
      dimensions:
        - Ship Month
        - Return Flag
        - Line Status
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
$$;

CREATE OR REPLACE VIEW ${target_catalog}.${target_schema}.mv_tpch_supply_chain_supply_cost
WITH METRICS
LANGUAGE YAML
AS $$
# subdomain: procurement
# Part-supplier-offer-grain supply and inventory metrics (TPC-H Q2, Q11). One row of source = one offer.
# KPIs: Inventory Value, Supply Cost. Offer and stock counts must come from partsupp (1,950 offers have no line items).
version: 1.1
comment: "Supply and inventory metrics at part-supplier offer grain: available stock, inventory value at supply cost, and unit supply cost, by part attributes and supplier geography. Snapshot data: there is no date column."

source: samples.tpch.partsupp

joins:
  # verified: partsupp -> part on ps_partkey = p_partkey, orphan_rate 0.0
  - name: part
    source: samples.tpch.part
    on: source.ps_partkey = part.p_partkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
  # verified: partsupp -> supplier on ps_suppkey = s_suppkey, orphan_rate 0.0
  - name: supplier
    source: samples.tpch.supplier
    on: source.ps_suppkey = supplier.s_suppkey
    cardinality: many_to_one
    rely:
      at_most_one_match: true
    joins:
      # verified: supplier -> nation on s_nationkey = n_nationkey, orphan_rate 0.0
      - name: supplier_nation
        source: samples.tpch.nation
        on: supplier.s_nationkey = supplier_nation.n_nationkey
        cardinality: many_to_one
        rely:
          at_most_one_match: true
        joins:
          # verified: nation -> region on n_regionkey = r_regionkey, orphan_rate 0.0
          - name: supplier_region
            source: samples.tpch.region
            on: supplier_nation.n_regionkey = supplier_region.r_regionkey
            cardinality: many_to_one
            rely:
              at_most_one_match: true

dimensions:
  - name: Part Key
    expr: source.ps_partkey
    comment: "Part identifier (Q11 computes inventory value per part)"
  - name: Part Type
    expr: part.p_type
    synonyms:
      - product type
  - name: Part Brand
    expr: part.p_brand
    synonyms:
      - brand
  - name: Manufacturer
    expr: part.p_mfgr
    synonyms:
      - mfgr
  - name: Part Size
    expr: part.p_size
    comment: "Part size (1 to 50); Q2 filters one size"
  - name: Supplier Name
    expr: supplier.s_name
    comment: "Synthetic supplier name"
    synonyms:
      - vendor
  - name: Supplier Nation
    expr: supplier.supplier_nation.n_name
    comment: "Nation of the supplier (Q11 filters one supplier nation)"
    synonyms:
      - vendor country
  - name: Supplier Region
    expr: supplier.supplier_nation.supplier_region.r_name
    comment: "Region of the supplier (Q2 filters one supplier region)"

measures:
  - name: Offer Count
    expr: COUNT(1)
    comment: "Number of part-supplier offers"
  - name: Available Quantity
    expr: SUM(source.ps_availqty)
    comment: "Units available across offers"
    synonyms:
      - stock on hand
      - available stock
  - name: Inventory Value
    expr: SUM(source.ps_supplycost * source.ps_availqty)
    comment: "Value in USD of available stock at supply cost (TPC-H Q11 important stock value)"
    synonyms:
      - stock value
      - available stock value
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
  - name: Average Supply Cost
    expr: AVG(source.ps_supplycost)
    comment: "Mean unit supply cost in USD per offer"
    synonyms:
      - supplier cost
      - unit cost
    format:
      type: currency
      currency_code: USD
  - name: Minimum Supply Cost
    expr: MIN(source.ps_supplycost)
    comment: "Lowest unit supply cost in USD (TPC-H Q2 minimum cost supplier)"
    format:
      type: currency
      currency_code: USD
  - name: Supplier Count
    expr: COUNT(DISTINCT source.ps_suppkey)
    comment: "Distinct suppliers with offers in scope"
  - name: Part Count
    expr: COUNT(DISTINCT source.ps_partkey)
    comment: "Distinct parts with offers in scope"

materialization:
  mode: relaxed
  schedule: every 6 hours
  materialized_views:
    - name: inventory_by_nation_mfgr
      type: aggregated
      dimensions:
        - Supplier Region
        - Supplier Nation
        - Manufacturer
      measures:
        - "*"
      refresh_policy: auto
      cluster_by:
        auto: true
$$;
