-- Ground truth for report: exec_quarterly_review
-- Persona: Executive (VP Supply Chain) preparing the 1997 annual and quarterly business review
-- Source: samples.tpch base tables only (no metric views). Read-only. One statement per turn.

-- turn 1: What was total revenue for orders placed in 1997?
SELECT SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey WHERE year(o_orderdate) = 1997;

-- turn 2: How does that compare with 1996? Show both years and the percent change.
SELECT SUM(CASE WHEN year(o_orderdate)=1996 THEN l_extendedprice * (1 - l_discount) END) AS revenue_1996, SUM(CASE WHEN year(o_orderdate)=1997 THEN l_extendedprice * (1 - l_discount) END) AS revenue_1997, (SUM(CASE WHEN year(o_orderdate)=1997 THEN l_extendedprice * (1 - l_discount) END) / SUM(CASE WHEN year(o_orderdate)=1996 THEN l_extendedprice * (1 - l_discount) END) - 1) * 100 AS pct_change FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey WHERE year(o_orderdate) IN (1996, 1997);

-- turn 3: Break the 1997 revenue down by customer region.
SELECT cr.r_name AS region, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1997 GROUP BY 1 ORDER BY 2 DESC;

-- turn 4: Which of those regions grew the most in revenue from 1996 to 1997, in percent?
SELECT cr.r_name AS region, (SUM(CASE WHEN year(o_orderdate)=1997 THEN l_extendedprice * (1 - l_discount) END) / SUM(CASE WHEN year(o_orderdate)=1996 THEN l_extendedprice * (1 - l_discount) END) - 1) * 100 AS pct_change FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) IN (1996,1997) GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

-- turn 5: How many orders were placed in 1997?
SELECT COUNT(*) AS orders FROM samples.tpch.orders WHERE year(o_orderdate) = 1997;

-- turn 6: What was the average order value in 1997, as revenue per order?
SELECT SUM(l_extendedprice * (1 - l_discount)) / COUNT(DISTINCT o_orderkey) AS avg_order_value FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey WHERE year(o_orderdate) = 1997;

-- turn 7: Show 1997 revenue by quarter.
SELECT quarter(o_orderdate) AS quarter, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey WHERE year(o_orderdate) = 1997 GROUP BY 1 ORDER BY 1;

-- turn 8: Which quarter was the strongest?
SELECT quarter(o_orderdate) AS quarter, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey WHERE year(o_orderdate) = 1997 GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

-- turn 9: What was the on-time shipping rate for line items on orders placed in 1997?
SELECT AVG(CASE WHEN l_shipdate <= l_commitdate THEN 1 ELSE 0 END) AS on_time_rate FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey WHERE year(o_orderdate) = 1997;

-- turn 10: And the same rate for 1996?
SELECT AVG(CASE WHEN l_shipdate <= l_commitdate THEN 1 ELSE 0 END) AS on_time_rate FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey WHERE year(o_orderdate) = 1996;
