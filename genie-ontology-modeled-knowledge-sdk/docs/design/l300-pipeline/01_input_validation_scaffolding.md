# Session 01 — Input Validation & Repo Scaffolding

**Wave:** 0 — Initialization
**Mode:** execute
**Estimated effort:** Light (~15 min)

## Goal

Validate all SDK inputs, create a feature branch, scaffold the project folder structure, and write the configuration file that downstream waves consume.

## Context

This is the first session in the SDK pipeline. It establishes the working environment for all subsequent waves. Read `sdk_config.json` (once written) as the single source of truth for all input parameters.

## Tasks

### 1. Validate Inputs

For each input, verify accessibility:

```python
# Catalogs
for catalog in source_catalogs:
    spark.sql(f"USE CATALOG `{catalog}`")  # Fails if no access

# Schemas
for schema in source_schemas:
    spark.sql(f"USE SCHEMA `{schema}`")

# Tables
for table in source_tables:
    spark.sql(f"DESCRIBE TABLE `{table}`")

# Volumes
for vol_dir in supplemental_volume_dirs:
    dbutils.fs.ls(vol_dir)  # Fails if not readable

# Target catalog/schema
spark.sql(f"USE CATALOG `{target_catalog}`")
spark.sql(f"USE SCHEMA `{target_schema}`")
```

Collect the full list of tables to profile (expand catalogs to schemas to tables).

### 2. Create Feature Branch

```bash
cd ${repo_path}
git checkout -b ontology-sdk/${domain_name}-$(date +%Y%m%d%H%M%S)
```

### 3. Scaffold Folder Structure

Create:
```
ontology-metric-views/
  metric_views/${domain_name}/
  sql/
  notebooks/
  tests/
  targets/
ontology-genie-agents/
  agents/
  notebooks/
  targets/
docs/
  research/
  context/
  semantics/
  data_profiles/
  tuning/
```

### 4. Write sdk_config.json

Write a JSON file with all input parameters plus the expanded `all_tables` list and the branch name.

## Pass Criteria

- [ ] All inputs validated without errors
- [ ] Feature branch created and checked out
- [ ] All directories exist
- [ ] `sdk_config.json` written with complete configuration
- [ ] `all_tables` list populated (expanded from catalogs/schemas)
