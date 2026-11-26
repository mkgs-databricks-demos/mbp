-- Ground truth for report: fulfillment_quality
-- Persona: Fulfillment and quality lead reviewing shipping performance and returns
-- Source: samples.tpch base tables only (no metric views). Read-only. One statement per turn.

-- turn 1: What is the overall on-time shipping rate across all line items?
SELECT AVG(CASE WHEN l_shipdate <= l_commitdate THEN 1 ELSE 0 END) AS on_time_rate FROM samples.tpch.lineitem;

-- turn 2: Break that down by ship mode.
SELECT l_shipmode AS ship_mode, AVG(CASE WHEN l_shipdate <= l_commitdate THEN 1 ELSE 0 END) AS on_time_rate FROM samples.tpch.lineitem GROUP BY 1 ORDER BY 2 DESC;

-- turn 3: Which ship mode performs worst?
SELECT l_shipmode AS ship_mode, AVG(CASE WHEN l_shipdate <= l_commitdate THEN 1 ELSE 0 END) AS on_time_rate FROM samples.tpch.lineitem GROUP BY 1 ORDER BY 2 ASC LIMIT 1;

-- turn 4: How many line items were received after their commit date?
SELECT SUM(CASE WHEN l_receiptdate > l_commitdate THEN 1 ELSE 0 END) AS late_receipts FROM samples.tpch.lineitem;

-- turn 5: Show those late receipts by ship mode for line items received in 1994.
SELECT l_shipmode AS ship_mode, SUM(CASE WHEN l_receiptdate > l_commitdate THEN 1 ELSE 0 END) AS late_receipts FROM samples.tpch.lineitem WHERE year(l_receiptdate) = 1994 GROUP BY 1 ORDER BY 2 DESC;

-- turn 6: What is the overall return rate as the share of quantity returned?
SELECT SUM(CASE WHEN l_returnflag = 'R' THEN l_quantity ELSE 0 END) / SUM(l_quantity) AS return_rate FROM samples.tpch.lineitem;

-- turn 7: Break the return rate down by order priority.
SELECT o_orderpriority AS order_priority, SUM(CASE WHEN l_returnflag = 'R' THEN l_quantity ELSE 0 END) / SUM(l_quantity) AS return_rate FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey GROUP BY 1 ORDER BY 1;

-- turn 8: Same breakdown, but only for orders placed in 1993.
SELECT o_orderpriority AS order_priority, SUM(CASE WHEN l_returnflag = 'R' THEN l_quantity ELSE 0 END) / SUM(l_quantity) AS return_rate FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey WHERE year(o_orderdate) = 1993 GROUP BY 1 ORDER BY 1;

-- turn 9: What is the average order fulfillment cycle time in days, from order date to receipt date, per line item?
SELECT AVG(datediff(l_receiptdate, o_orderdate)) AS avg_cycle_days FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey;

-- turn 10: Break the cycle time down by order priority.
SELECT o_orderpriority AS order_priority, AVG(datediff(l_receiptdate, o_orderdate)) AS avg_cycle_days FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey GROUP BY 1 ORDER BY 1;
