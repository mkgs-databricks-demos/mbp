# Genie Agent API & DAB Deployment

Matthew Giglia | Databricks Field Engineering
Version: 1.0 | Date: 2026-11-24

## Summary

Genie Agents (formerly Genie Spaces) can be created, configured, and deployed programmatically via the Management API and natively through Declarative Automation Bundles. This document captures the deployment patterns for CI/CD.

## Management API

The GA management API endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/2.0/genie/spaces` | Create a new agent |
| `GET` | `/api/2.0/genie/spaces/{space_id}?include_serialized_space=true` | Export (with full config) |
| `PATCH` | `/api/2.0/genie/spaces/{space_id}` | Update/replace |
| `DELETE` | `/api/2.0/genie/spaces/{space_id}` | Trash |

### `serialized_space` Format

The `serialized_space` is a **JSON string** (not a nested object) containing the full agent configuration:

```json
{
  "version": 2,
  "config": {
    "sample_questions": [...]
  },
  "data_sources": {
    "tables": [
      {
        "identifier": "catalog.schema.table",
        "description": ["..."],
        "column_configs": [...]
      }
    ]
  },
  "instructions": {
    "text_instructions": [...],
    "example_question_sqls": [...],
    "join_specs": [...],
    "sql_snippets": { "filters": [...], "expressions": [...] }
  }
}
```

**Key rules:**
- IDs must be lowercase, 32-character hexadecimal strings without hyphens
- At least one data source (table or metric view) is required
- `PATCH` replaces the entire `serialized_space` — it is atomic, not field-level
- Use `etag` for safe updates (prevents overwriting newer changes)

## Native DAB `genie_spaces` Resource (Preferred)

The preferred CI/CD approach uses the native DAB resource type:

```yaml
# resources/genie_agents.yml
resources:
  genie_spaces:
    sales_analytics:
      title: Sales Analytics
      description: Natural-language analysis of sales data
      warehouse_id: ${var.warehouse_id}
      parent_path: /Workspace/Shared/Genie
      file_path: ./agents/sales_analytics.geniespace.json
      permissions:
        - level: CAN_RUN
          group_name: analysts
        - level: CAN_EDIT
          group_name: bi-engineering
```

**Requirements:**
- `engine: direct` in `databricks.yml` (required for Genie resources)
- `file_path` takes precedence over inline `serialized_space`
- Store only the raw serialized definition in Git (the `.geniespace.json` file)

## Export Existing Agent to Git

For agents initially created in the UI:

```bash
databricks bundle generate genie-space \
  --existing-id <space-id> \
  --force
```

This generates a Bundle resource YAML and a `.geniespace.json` file.

For ongoing sync while making UI changes:

```bash
databricks bundle generate genie-space \
  --resource sales_analytics \
  --watch \
  --force
```

## Deployment Flow

```bash
# Validate
databricks bundle validate -t dev

# Deploy to dev
databricks bundle deploy -t dev

# Promote to prod (same definition, different target)
databricks bundle validate -t prod
databricks bundle deploy -t prod
```

## SDK Design Implications

1. The SDK generates `.geniespace.json` files in Wave 6 (Agent Curation)
2. DAB 2 deploys them using the native `genie_spaces` resource
3. Warehouse IDs, workspace hosts, and permissions are target-specific variables
4. Stable IDs in the serialized definition make diffs and updates predictable
5. Referenced metric views must exist before agent deployment (DAB 1 runs first)

## Sources

- Databricks documentation: Use the Genie Agents API
- Databricks documentation: Manage AI/BI assets using APIs
- Databricks documentation: Curate an effective Genie Agent
- Databricks API reference: Genie Space
