# L200-F — Metric View & Pages Registration Pipeline

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24

**Parent:** [L100 — Genie Ontology Modeled Knowledge SDK](L100-genie-ontology-modeled-knowledge-sdk.md)
**Wave:** Waves 5 + 5.5

## Scope

This component handles the registration of metric views and UC Pages:

### Wave 5: Metric View Registration

Uses the DAB 1 forEach workflow:

1. **generate-manifest** — reads `metric_views/` directory, outputs JSON array as task value
2. **register-each-mv** — forEach task with concurrency 4:
   - Reads YAML from repo
   - Substitutes `${var.source_catalog}`, `${var.source_schema}`, `${var.target_catalog}`, `${var.target_schema}`
   - Executes `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`
   - Validates view was created
3. **smoke-test** — queries each MV with `MEASURE()` syntax
4. **cardinality-test** — verifies join cardinality doesn't inflate measures

> See [Diagram 04 — forEach Registration Flow](../diagrams/mermaid/04_foreach_registration_flow.md)

### Wave 5.5: UC Pages Registration

Uses a Genie Code workflow task (not SQL DDL):

1. Reads glossary candidates from `docs/semantics/`
2. Formats each as a UC Page (definition, business context, data usage, related terms, source)
3. Calls the Pages API to register each page
4. Associates pages with domain/subdomain (if created via opt-in Domain Wave)

### Testing Strategy

| Test | Level | What It Validates |
|---|---|---|
| YAML structure | Static | Required keys, unique names, no hardcoded catalogs |
| Bundle validate | Deploy | `databricks bundle validate -t dev` |
| Smoke query | Runtime | Each MV is queryable with `MEASURE()` |
| Cardinality | Runtime | Joins don't inflate measures |
| Type check | Runtime | Measures return expected types |

## Dependencies

- L100 system-level patterns (governance, observability, security, error handling)
- Previous waves' outputs (see L100 wave descriptions)

## Open Questions

_To be resolved during L200 detailed design._

## Testing Strategy

_To be defined per component._

## Deployment

Deployed as part of the Genie Build Waves pipeline. See L100 for the overall orchestration model.
