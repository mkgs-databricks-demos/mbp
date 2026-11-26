-- Ground truth for report: procurement_supplier_profit
-- Persona: Procurement lead reviewing supplier profitability and stock value across all years
-- Source: samples.tpch base tables only (no metric views). Read-only. One statement per turn.

-- turn 1: What is total profit across all years, where profit is revenue minus supply cost?
SELECT SUM(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity) AS profit FROM samples.tpch.lineitem JOIN samples.tpch.partsupp ON l_partkey = ps_partkey AND l_suppkey = ps_suppkey;

-- turn 2: Break profit down by supplier region.
SELECT sr.r_name AS supplier_region, SUM(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity) AS profit FROM samples.tpch.lineitem JOIN samples.tpch.partsupp ON l_partkey = ps_partkey AND l_suppkey = ps_suppkey JOIN samples.tpch.supplier ON l_suppkey = s_suppkey JOIN samples.tpch.nation sn ON s_nationkey = sn.n_nationkey JOIN samples.tpch.region sr ON sn.n_regionkey = sr.r_regionkey GROUP BY 1 ORDER BY 2 DESC;

-- turn 3: For the most profitable region, show profit by supplier nation.
WITH top AS (SELECT sr.r_name AS r FROM samples.tpch.lineitem JOIN samples.tpch.partsupp ON l_partkey = ps_partkey AND l_suppkey = ps_suppkey JOIN samples.tpch.supplier ON l_suppkey = s_suppkey JOIN samples.tpch.nation sn ON s_nationkey = sn.n_nationkey JOIN samples.tpch.region sr ON sn.n_regionkey = sr.r_regionkey GROUP BY 1 ORDER BY SUM(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity) DESC LIMIT 1) SELECT sn.n_name AS supplier_nation, SUM(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity) AS profit FROM samples.tpch.lineitem JOIN samples.tpch.partsupp ON l_partkey = ps_partkey AND l_suppkey = ps_suppkey JOIN samples.tpch.supplier ON l_suppkey = s_suppkey JOIN samples.tpch.nation sn ON s_nationkey = sn.n_nationkey JOIN samples.tpch.region sr ON sn.n_regionkey = sr.r_regionkey WHERE sr.r_name = (SELECT r FROM top) GROUP BY 1 ORDER BY 2 DESC;

-- turn 4: Show profit for suppliers in Germany by order year.
SELECT year(o_orderdate) AS year, SUM(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity) AS profit FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.partsupp ON l_partkey = ps_partkey AND l_suppkey = ps_suppkey JOIN samples.tpch.supplier ON l_suppkey = s_suppkey JOIN samples.tpch.nation sn ON s_nationkey = sn.n_nationkey JOIN samples.tpch.region sr ON sn.n_regionkey = sr.r_regionkey WHERE sn.n_name = 'GERMANY' GROUP BY 1 ORDER BY 1;

-- turn 5: What is the total inventory value, supply cost times available quantity, across all part suppliers?
SELECT SUM(ps_supplycost * ps_availqty) AS inventory_value FROM samples.tpch.partsupp;

-- turn 6: Break inventory value down by supplier region.
SELECT sr.r_name AS supplier_region, SUM(ps_supplycost * ps_availqty) AS inventory_value FROM samples.tpch.partsupp JOIN samples.tpch.supplier ON ps_suppkey = s_suppkey JOIN samples.tpch.nation sn ON s_nationkey = sn.n_nationkey JOIN samples.tpch.region sr ON sn.n_regionkey = sr.r_regionkey GROUP BY 1 ORDER BY 2 DESC;

-- turn 7: Now only suppliers in Germany: which 10 parts have the highest inventory value?
SELECT ps_partkey AS part_key, SUM(ps_supplycost * ps_availqty) AS inventory_value FROM samples.tpch.partsupp JOIN samples.tpch.supplier ON ps_suppkey = s_suppkey JOIN samples.tpch.nation sn ON s_nationkey = sn.n_nationkey WHERE sn.n_name = 'GERMANY' GROUP BY 1 ORDER BY 2 DESC LIMIT 10;

-- turn 8: How many suppliers are based in Germany?
SELECT COUNT(*) AS suppliers FROM samples.tpch.supplier JOIN samples.tpch.nation sn ON s_nationkey = sn.n_nationkey WHERE sn.n_name = 'GERMANY';

-- turn 9: What is the average unit supply cost for those German suppliers compared with all suppliers?
SELECT AVG(CASE WHEN sn.n_name = 'GERMANY' THEN ps_supplycost END) AS avg_cost_germany, AVG(ps_supplycost) AS avg_cost_all FROM samples.tpch.partsupp JOIN samples.tpch.supplier ON ps_suppkey = s_suppkey JOIN samples.tpch.nation sn ON s_nationkey = sn.n_nationkey;

-- turn 10: What was profit by order year for parts whose name contains 'green'?
SELECT year(o_orderdate) AS year, SUM(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity) AS profit FROM samples.tpch.lineitem JOIN samples.tpch.orders ON l_orderkey = o_orderkey JOIN samples.tpch.partsupp ON l_partkey = ps_partkey AND l_suppkey = ps_suppkey JOIN samples.tpch.part ON l_partkey = p_partkey WHERE p_name LIKE '%green%' GROUP BY 1 ORDER BY 1;
