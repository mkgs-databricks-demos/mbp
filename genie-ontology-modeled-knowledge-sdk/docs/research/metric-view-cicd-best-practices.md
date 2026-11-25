# Metric View CI/CD Best Practices

Matthew Giglia | Databricks Field Engineering
Version: 1.0 | Date: 2026-11-24

## Summary

Metric views are governed, versioned enterprise assets — not just context for text-to-SQL tools. They live in Git and are deployed only with DABs. This document captures the best practices for CI/CD of metric view YAMLs.

## Core Principles

### 1. YAML-as-Contract

The metric view YAML is a **semantic contract** consumed by dashboards, Genie Agents, notebooks, and downstream applications. Treat metric names and definitions as an API:

**Safe changes:**
- Add a new field or measure
- Add synonyms or descriptions
- Improve an expression without changing business meaning

**Breaking changes:**
- Rename a measure or field used by dashboards
- Change a measure's grain or filter logic
- Change currency, timezone, or fiscal-calendar logic
- Change join cardinality

### 2. `CREATE OR REPLACE VIEW` — Idempotent Deployment

```sql
CREATE OR REPLACE VIEW
  ${target_catalog}.${target_schema}.${mv_name}
WITH METRICS
LANGUAGE YAML
AS
$$
${yaml_content}
$$;
```

- Re-running converges on the desired definition
- No dependency on whether the view already exists
- Rollback = redeploy the previous Git commit
- No separate "drop" and "create" steps (avoids outage window)

Do NOT use `DROP VIEW` followed by `CREATE VIEW` unless there is a specific reason.

### 3. Separate DAB YAML from Metric View YAML

These are two different YAML formats:

- **Metric view YAML** — business definitions (`version`, `source`, `fields`, `measures`)
- **DAB YAML** — infrastructure (`resources`, `jobs`, `tasks`, `targets`)

The Bundle owns the job, task, permissions, and environment configuration. The SQL task owns execution of the metric-view DDL.

### 4. Parameterize Everything

```yaml
# targets/prod.yml
targets:
  prod:
    mode: production
    variables:
      catalog: analytics_prod
      schema: semantic
      source_schema: silver
      warehouse_id: ${var.prod_warehouse_id}
```

Use separate Unity Catalog catalogs or schemas for dev, staging, and production. The same Git commit promotes across environments with only target configuration changing.

### 5. Prefer Explicit Fields Over Wildcards

In certified metric views, avoid `expr: source.*`. Wildcards can:
- Change unexpectedly when upstream schema changes
- Expose sensitive or irrelevant columns
- Create name collisions across joins

Use explicit fields with `EXCEPT` if wildcards are needed:

```yaml
fields:
  - expr: source.* EXCEPT (internal_notes, customer_id)
  - name: Customer ID
    expr: source.customer_id
    comment: Primary customer identifier
```

## Three-Level CI Checks

### Level A: Static YAML Checks (every PR)

- YAML parser validation
- Required keys: `version`, `source`, `fields`/`dimensions`, `measures`
- Unique field and measure names
- No hardcoded production catalog names
- No wildcard usage in certified views (unless approved)

### Level B: Bundle Validation (every PR)

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

### Level C: Semantic & Data-Contract Tests (post-deploy)

- Metric view exists and is queryable
- Required dimensions and measures exist
- Measures return expected types
- Join cardinality does not inflate measures
- Results match reference query on fixture dataset

```sql
SELECT
  `Order Month`,
  MEASURE(`Revenue`) AS revenue,
  MEASURE(`Order Count`) AS order_count
FROM ${catalog}.${schema}.sales_metrics
GROUP BY ALL
ORDER BY `Order Month`;
```

## forEach Registration Pattern

The SDK uses a forEach task to register metric views:

1. **generate-manifest** task reads `metric_views/` directory, outputs JSON array as task value
2. **register-each-mv** forEach task iterates over the manifest
3. Each iteration reads YAML, substitutes parameters, executes `CREATE OR REPLACE VIEW`
4. **smoke-test** task validates all views are queryable

Adding a new metric view = adding a YAML file to the repo. No code changes to the pipeline.

## Sources

- Databricks documentation: Create a metric view
- Databricks documentation: Metric view YAML syntax reference
- Databricks documentation: CI/CD on Databricks
- Databricks documentation: Developer best practices
