# L200-D — Deep Exploratory Data Analyzer

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24

**Parent:** [L100 — Genie Ontology Modeled Knowledge SDK](L100-genie-ontology-modeled-knowledge-sdk.md)
**Wave:** Wave 3

## Scope

This component performs comprehensive profiling of every source table:

### Per-Table Analysis

| Analysis | Method | Output |
|---|---|---|
| Structure | `DESCRIBE EXTENDED`, schema inspection | Column types, nested structs, partitioning |
| Integrity | `COUNT(*)`, null rate per column, uniqueness | Null rates, duplicate detection |
| Quality | Value distributions, outlier detection | Histograms, anomaly flags |
| Lineage | `system.access.table_lineage` | Upstream/downstream dependencies |
| Usage | `system.query.history` | Query frequency, common joins, popular columns |
| Update cadence | `DESCRIBE HISTORY`, partition freshness | Last modified, streaming vs batch |
| Grain | Uniqueness analysis on column combinations | Primary key candidates, composite keys |
| Foreign keys | Column name matching + value overlap | Cross-table join key candidates |
| Cardinality | `COUNT(DISTINCT)` per column | Many-to-one vs many-to-many detection |
| Volume | Row counts, `DESCRIBE DETAIL` | Storage size, growth rate |

### Cross-Table Analysis

- **Join key detection** — match column names across tables, verify value overlap
- **Cardinality verification** — for each candidate join, verify many-to-one vs many-to-many
- **Referential integrity** — check for orphan keys
- **Star schema detection** — identify fact vs dimension tables

### Materialization Signals

Flag tables/joins that suggest materialization:
- Source table > configurable row count threshold
- Complex multi-table joins
- One-to-many relationships requiring careful aggregation
- High estimated query frequency (from domain research KPIs)

### Output

- `docs/data_profiles/<table_name>.md` — one per table
- `docs/data_profiles/data_model_summary.md` — consolidated cross-table analysis

## Dependencies

- L100 system-level patterns (governance, observability, security, error handling)
- Previous waves' outputs (see L100 wave descriptions)

## Open Questions

_To be resolved during L200 detailed design._

## Testing Strategy

_To be defined per component._

## Deployment

Deployed as part of the Genie Build Waves pipeline. See L100 for the overall orchestration model.
