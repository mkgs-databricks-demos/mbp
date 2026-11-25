# 03 Regulatory Context — tpch_supply_chain

## Summary
TPC-H is a public benchmark with synthetic data, so no industry regulator or mandatory reporting regime applies to it. The data must be produced by the TPC-provided DBGen software ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)), which generates the benchmark's table load files ([tpch-dbgen README](https://github.com/databricks/tpch-dbgen/blob/master/README)). Databricks ships it as the `samples.tpch` sample dataset ([Sample datasets | Databricks on AWS](https://docs.databricks.com/aws/en/discover/databricks-datasets)). Following the skill's rule for benchmark datasets, the regulatory search budget was spent on terminology and KPIs instead.

## Findings

### Data origin
* DBGen "must be used to produce the data used to populate the database" ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).
* The DBGen README describes it as the database population program for TPC-H that generates the `.tbl` load files ([tpch-dbgen README](https://github.com/databricks/tpch-dbgen/blob/master/README)).

### Privacy
* Names, addresses and phone numbers (`c_name`, `c_address`, `c_phone`, `s_name`, `s_address`, `s_phone`) are generated values, not collected from real people. This is an inference from the generation rules above: no source states "contains no personal data" in those words.
* No privacy regime (for example GDPR or CCPA) is cited because no source ties one to this dataset: not found.

### Required metrics
* None. The only "mandatory" metrics are the benchmark's own reporting rules, which concern query performance, not business KPIs ([TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf)).

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| Synthetic contact fields | `customer.c_name`, `c_address`, `c_phone`; `supplier.s_name`, `s_address`, `s_phone` | not sensitive in TPC-H; a real deployment of the same model would need PII tagging and masking |
| No regulatory metric | all tables | no compliance measures or pages needed |

## Open questions
* If this SDK example is reused on a real wholesale dataset, the owner must add the applicable privacy and financial-reporting rules.

## Sources
1. [TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf) — Transaction Processing Performance Council
2. [TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf) — Transaction Processing Performance Council
3. [tpch-dbgen README](https://github.com/databricks/tpch-dbgen/blob/master/README) — GitHub
4. [Sample datasets | Databricks on AWS](https://docs.databricks.com/aws/en/discover/databricks-datasets) — Databricks
