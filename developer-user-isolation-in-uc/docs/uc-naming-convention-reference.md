# Unity Catalog Naming Convention & DAB Deployment Best Practices

**Author:** Matthew Giglia | Databricks Field Engineering  
**Version:** 1.0 | October 2026

---

## Overview

This document defines the standard naming convention for Unity Catalog catalogs and schemas when using Databricks Asset Bundles (DABs) for multi-environment deployment. It covers catalog naming, schema personalization, privilege grants, workspace binding, parameterization rules, and lifecycle management.

This convention is designed to be referenced by Genie Code for contextual understanding of your environment topology.

---

## Catalog Naming Convention

### Pattern

| Environment | Catalog Name | Example |
|---|---|---|
| **Production** | `<business_function>` | `hedis` |
| **UAT** | `<business_function>_uat` | `hedis_uat` |
| **Test** | `<business_function>_tst` | `hedis_tst` |
| **Development** | `<business_function>_dev` | `hedis_dev` |

**Key principle:** The catalog is the environment discriminator. Production uses the clean, undecorated name. Non-production environments append `_<env>` as a suffix.

### Schema Naming

| Environment | Schema Name | Personalized? |
|---|---|---|
| **Production** | `pa` | No |
| **UAT** | `pa` | No |
| **Test** | `pa` | No |
| **Development** | `dev_<userid>_pa` | Yes — DAB dev-mode prefix |

Schema names are **exact matches across tst, uat, and prd**. Only the development environment has personalized schema names, applied automatically by DAB's development mode prefix (`dev_<userid>_`).

### Fully Qualified Examples

```
hedis.pa.claims              -- Production
hedis_uat.pa.claims          -- UAT (schema matches prod)
hedis_tst.pa.claims          -- Test (schema matches prod)
hedis_dev.dev_ah23297_pa.claims  -- Dev (schema personalized)
```

---

## Promotion Path

```
dev  (personalized schemas, iterate fast)
 ↓   target_catalog changes, schema prefix drops
tst  (exact schema names, integration test)
 ↓   target_catalog changes only
uat  (exact schema names, business validation)
 ↓   target_catalog changes only
prd  (exact schema names, canonical)
```

The schema name discontinuity happens **exactly once** — at the dev → tst boundary. This is the natural boundary where code transitions from an individual developer's sandbox to a shared, validated artifact. From tst onward, promotion is a clean catalog swap with zero schema renaming.

---

## Zero Hardcoding Rule

> **Nothing in the bundle should ever be hardcoded — catalog names, schema names, table references — everything must be parameterized.**

This is the foundational rule that makes the entire promotion path work. If anything is hardcoded, the bundle is welded to one environment and the single-variable promotion model breaks down.

### What Must Be Parameterized

| Artifact | Parameterization Method |
|---|---|
| **databricks.yml resources** | Use `${var.catalog}`, `${var.schema_prefix}`, etc. |
| **Resource references** | `${resources.<type>.<resource_id>.<element>}` — never literal names |
| **SQL queries** | `USE CATALOG ${catalog}; USE SCHEMA ${schema};` at the top, then unqualified table names |
| **Metric view YAML** | Catalog and schema references must use variables |
| **Pipeline configurations** | All catalog/schema references interpolated |
| **Notebook widgets** | Parameterized via DAB task parameters |
| **Any other artifact** | If it references a catalog or schema, it uses a variable |

### Example: databricks.yml

```yaml
variables:
  catalog:
    description: Target catalog for deployment
    default: hedis_dev

resources:
  schemas:
    pa_schema:
      catalog_name: ${var.catalog}
      name: pa
```

### Example: SQL in Notebooks

```sql
-- Set context once at the top
USE CATALOG ${catalog};
USE SCHEMA ${schema};

-- All subsequent queries use unqualified names
SELECT * FROM claims WHERE measure_year = 2026;
```

### Example: Resource References in Jobs/Pipelines

```yaml
tasks:
  - task_key: load_claims
    notebook_task:
      notebook_path: ${resources.notebooks.load_claims.path}
      base_parameters:
        catalog: ${resources.schemas.pa_schema.catalog_name}
        schema: ${resources.schemas.pa_schema.name}
```

---

## Workspace Binding

Each catalog must be bound to its designated workspace. By default, all catalogs in a metastore are accessible from every attached workspace — workspace binding overrides this to enforce hard isolation.

| Catalog | Bound To | Access Mode |
|---|---|---|
| `hedis_dev` | Development / Interactive workspace | Read-Write |
| `hedis_tst` | Test workspace | Read-Write |
| `hedis_uat` | UAT workspace | Read-Write |
| `hedis` (prod) | Production workspace | Read-Write |

Once bound, access from any other workspace is **denied at the platform level**, regardless of privilege grants. This is a hard boundary, not a convention.

Binding is configured via the Workspace-Catalog Bindings API or Catalog Explorer — not via SQL.

---

## Grants — Development Catalog

For a per-developer development catalog, the minimal correct grant set is:

```sql
GRANT USE CATALOG, CREATE SCHEMA
ON CATALOG hedis_dev
TO `developer@company.com`;
```

### Why This Is Sufficient

| Action | Authorization |
|---|---|
| Create schemas | `CREATE SCHEMA` grant on catalog |
| Create tables/views/volumes inside their schemas | **Ownership** — developer created the schema |
| SELECT / MODIFY data in their schemas | **Ownership** inheritance |
| Drop their schemas and contents | **Ownership** |
| Grant access to a teammate | **Ownership** — schema owners can grant on their schemas |
| Create tables in schemas they don't own | Blocked — no catalog-level `CREATE TABLE` |

### What NOT to Grant

| Privilege | Why Not |
|---|---|
| `CREATE TABLE` at catalog level | Would allow creating tables in any schema, including those owned by service principals or other developers |
| `MANAGE` | Not needed — ownership inheritance handles everything within developer-created schemas |
| `ALL PRIVILEGES` | Overly broad; dynamically evaluated and expands as new privilege types are added |

### Service Principal Consideration

If a DAB's service principal creates schemas (not the developer), the SP is the owner. Options:
1. Structure the DAB so the developer identity creates schemas
2. Have the SP transfer ownership post-deploy: `ALTER SCHEMA ... OWNER TO developer`
3. Grant explicit privileges on SP-owned schemas to the developer

---

## Lifecycle Cleanup

Lower environments can be cleaned up after a project ends using DAB's built-in destroy command:

```bash
# Tear down a specific environment
databricks bundle destroy -t dev
databricks bundle destroy -t tst
databricks bundle destroy -t uat
```

`bundle destroy` is DAB-aware — it tears down exactly what the bundle deployed (schemas, tables, volumes, pipelines, jobs) without manual hunting.

For development specifically:
- Individual developer schemas: `databricks bundle destroy` in dev mode
- Entire dev catalog: `DROP CATALOG hedis_dev CASCADE` (admin operation)

This addresses the metastore clutter concern: lower-environment catalogs are ephemeral and have a built-in, automated teardown path.

---

## Metastore Visibility Note

Metastore admins and workspace admins will see all catalogs across all environments. With many developers, the metastore catalog list may appear busy.

**Mitigations:**
- Consistent `<business_function>_<env>` naming makes dev catalogs instantly recognizable and filterable
- `INFORMATION_SCHEMA` queries can filter with `WHERE catalog_name NOT LIKE '%_dev'`
- Automated cleanup via `bundle destroy` keeps the catalog count proportional to active projects, not accumulated history
- Unity Catalog does not impose practical limits on catalog count at typical team sizes

---

## Quick Reference Card

```
+-----------------------------------------------------+
|  CATALOG NAMING                                      |
|  Prod:     <business_function>         e.g. hedis    |
|  Non-prod: <business_function>_<env>   e.g. hedis_dev|
|                                                      |
|  SCHEMA NAMING                                       |
|  Tst/UAT/Prd: exact match to prod     e.g. pa       |
|  Dev only:    DAB dev-mode prefix      e.g. dev_*_pa |
|                                                      |
|  GRANTS (Dev)                                        |
|  USE CATALOG + CREATE SCHEMA -- nothing more         |
|                                                      |
|  PARAMETERIZATION                                    |
|  Zero hardcoding. Everything uses variables.         |
|  ${var.catalog}, ${resources.<type>.<id>.<element>}  |
|                                                      |
|  CLEANUP                                             |
|  databricks bundle destroy -t <env>                  |
|                                                      |
|  WORKSPACE BINDING                                   |
|  Each catalog bound to its designated workspace      |
+-----------------------------------------------------+
```
