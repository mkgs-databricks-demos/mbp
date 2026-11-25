---
term: Order Volume
synonyms: [order count, number of orders]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Average Order Value, Order Priority, Customer, Line Item]
sources:
  - https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf
---

## Definition
The number of distinct customer orders in a period. Each order is one ORDERS row, placed by one customer and made of LINEITEM rows ([TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf)). No external formula was sourced; this is a plain count.

## Business context
A demand measure for sales, and the denominator of Average Order Value. Usually sliced by order date, priority, market segment and nation.

## Data usage
`count(distinct o_orderkey)` over `samples.tpch.orders`, by `o_orderdate`. When it is computed from `lineitem`, use `count(distinct l_orderkey)`. A plain row count on `lineitem` gives line items, not orders.
