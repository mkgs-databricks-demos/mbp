# L200-C — Supplemental Context Parser

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24

**Parent:** [L100 — Genie Ontology SDK](L100-genie-ontology-sdk.md)
**Wave:** Wave 2

## Scope

This component extracts business context from supplemental materials:

1. **File parsing** — read markdown, PDF, DOCX, CSV, JSON from volume directories
2. **Dashboard extraction** — parse PowerBI (.pbix metadata), Tableau (.twb/.tds) for:
   - Measure definitions and calculated fields
   - Join relationships and cardinality
   - Filter logic and parameters
   - Dimension hierarchies
3. **Semantic capture** — extract KPI definitions, business rules, join criteria
4. **Context synthesis** — organize extracted context by domain/subdomain

### Supported File Types

| Type | Parser | Extracts |
|---|---|---|
| `.md` | Direct read | Business rules, definitions, requirements |
| `.pdf` | `ai_extract` or text extraction | Business requirements, data dictionaries |
| `.docx` | python-docx | Business requirements, specifications |
| `.csv` | pandas | Data dictionaries, mapping tables |
| `.json` | Direct parse | API specs, configuration, metadata |
| `.pbix` (metadata) | Custom parser | Measures, relationships, filters |
| `.twb` / `.tds` | XML parser | Calculated fields, joins, hierarchies |

### Output Structure

- `docs/context/` — one markdown per source file with extracted context
- `docs/semantics/` — additional glossary candidates from business materials

## Dependencies

- L100 system-level patterns (governance, observability, security, error handling)
- Previous waves' outputs (see L100 wave descriptions)

## Open Questions

_To be resolved during L200 detailed design._

## Testing Strategy

_To be defined per component._

## Deployment

Deployed as part of the Genie Build Waves pipeline. See L100 for the overall orchestration model.
