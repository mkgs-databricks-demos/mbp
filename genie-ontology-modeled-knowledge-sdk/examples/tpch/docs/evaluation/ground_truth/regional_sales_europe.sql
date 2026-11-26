-- Ground truth for report: regional_sales_europe
-- Persona: Regional sales manager for Europe preparing a 1995 regional performance report
-- Source: samples.tpch base tables only (no metric views). Read-only. One statement per turn.

-- turn 1: What was revenue by customer region for orders placed in 1995?
SELECT cr.r_name AS region, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 GROUP BY 1 ORDER BY 2 DESC;

-- turn 2: Now only Europe, broken down by customer nation.
SELECT cn.n_name AS nation, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cr.r_name = 'EUROPE' GROUP BY 1 ORDER BY 2 DESC;

-- turn 3: Which nation was the top one?
SELECT cn.n_name AS nation, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cr.r_name = 'EUROPE' GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

-- turn 4: For that nation, show 1995 revenue by market segment.
WITH top AS (SELECT cn.n_name AS nation FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cr.r_name = 'EUROPE' GROUP BY 1 ORDER BY SUM(l_extendedprice * (1 - l_discount)) DESC LIMIT 1) SELECT c_mktsegment AS segment, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cn.n_name = (SELECT nation FROM top) GROUP BY 1 ORDER BY 2 DESC;

-- turn 5: And the same breakdown for 1994?
WITH top AS (SELECT cn.n_name AS nation FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cr.r_name = 'EUROPE' GROUP BY 1 ORDER BY SUM(l_extendedprice * (1 - l_discount)) DESC LIMIT 1) SELECT c_mktsegment AS segment, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1994 AND cn.n_name = (SELECT nation FROM top) GROUP BY 1 ORDER BY 2 DESC;

-- turn 6: How many distinct customers in Europe placed orders in 1995?
SELECT COUNT(DISTINCT o_custkey) AS customers FROM samples.tpch.orders JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cr.r_name = 'EUROPE';

-- turn 7: Who were the top 5 European customers by 1995 revenue?
SELECT c_name AS customer, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cr.r_name = 'EUROPE' GROUP BY 1 ORDER BY 2 DESC LIMIT 5;

-- turn 8: What was the return rate, as the share of quantity returned, for European customers on 1995 orders?
SELECT SUM(CASE WHEN l_returnflag = 'R' THEN l_quantity ELSE 0 END) / SUM(l_quantity) AS return_rate FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cr.r_name = 'EUROPE';

-- turn 9: How does that compare with Asia?
SELECT cr.r_name AS region, SUM(CASE WHEN l_returnflag = 'R' THEN l_quantity ELSE 0 END) / SUM(l_quantity) AS return_rate FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE year(o_orderdate) = 1995 AND cr.r_name IN ('EUROPE','ASIA') GROUP BY 1 ORDER BY 1;

-- turn 10: Show European revenue by order year for all years.
SELECT year(o_orderdate) AS year, SUM(l_extendedprice * (1 - l_discount)) AS revenue FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.customer ON o_custkey = c_custkey JOIN samples.tpch.nation cn ON c_nationkey = cn.n_nationkey JOIN samples.tpch.region cr ON cn.n_regionkey = cr.r_regionkey WHERE cr.r_name = 'EUROPE' GROUP BY 1 ORDER BY 1;
