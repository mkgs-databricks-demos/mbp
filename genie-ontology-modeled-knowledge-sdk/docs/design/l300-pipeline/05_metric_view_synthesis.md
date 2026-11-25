# Session 05 — Metric View YAML Synthesis

**Wave:** 4 — Metric View Synthesis
**Mode:** edit
**Depends on:** 02, 03, 04
**Estimated effort:** Heavy (~30+ min, may need continuation)

## Goal

Synthesize all context from Waves 1-3 into parameterized metric view YAML files and a registration manifest.

## Context

Read before starting: `sdk_config.json`, `docs/research/02_kpi_definitions.md`, `docs/research/05_domain_subdomain_proposal.md`, `docs/context/*.md`, `docs/data_profiles/data_model_summary.md`, `docs/semantics/*.md`, `examples/metric_views/sales/mv_sales_revenue.yml` (reference).

## Tasks

### 1. Map KPIs to Metric Views

For each KPI: identify source table(s), determine measure expression, identify dimensions, identify joins, determine filters.

### 2. Generate YAML Files

Rules:
- **Parameterization:** `source: ${source_catalog}.${source_schema}.table_name`
- **Semantic metadata:** comments from business rules, synonyms from research, display_name only when different from name, format for currency/percentage/date
- **Joins:** `rely: at_most_one_match: true` ONLY where Wave 3 confirmed many-to-one
- **Materialization:** auto-generate blocks for flagged MVs with `refresh_policy: auto`, `cluster_by: { auto: true }`
- **Version:** always `1.1`

### 3. Generate manifest.json

JSON array of objects: `{name, yaml_path, domain, subdomain}` for each MV.

### 4. Organize by Domain/Subdomain

Place YAMLs in `ontology-metric-views/metric_views/<domain>/`.

## Pass Criteria

- [ ] At least one YAML per domain area
- [ ] All YAMLs parameterized (no hardcoded catalogs)
- [ ] All joins have rely annotations matching Wave 3 cardinality
- [ ] Materialization blocks on threshold MVs
- [ ] manifest.json is valid JSON array
- [ ] YAML version 1.1 in every file
