# L200-B — Domain Research Engine

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24

**Parent:** [L100 — Genie Ontology SDK](L100-genie-ontology-sdk.md)
**Wave:** Wave 1

## Scope

This component performs automated domain research using web search:

1. **Industry terminology** — search for standard definitions of terms in the `domain_context`
2. **Common KPIs** — identify industry-standard metrics and benchmarks
3. **Regulatory context** — find relevant regulations, compliance requirements, reporting standards
4. **Competitive landscape** — identify how similar organizations measure and report
5. **Domain/subdomain candidates** — propose UC organizational structure
6. **UC Pages candidates** — identify glossary terms structured for UC Pages

### Research Document Structure

Each research thread gets its own markdown file in `docs/research/`:

- `01_domain_overview.md` — high-level domain landscape
- `02_kpi_definitions.md` — standard KPIs with definitions and formulas
- `03_regulatory_context.md` — applicable regulations and reporting requirements
- `04_industry_benchmarks.md` — benchmark values and ranges
- `05_domain_subdomain_proposal.md` — proposed UC organizational structure

### Glossary Candidate Structure

Each term in `docs/semantics/` follows the UC Pages format:

```markdown
## Term Name

**Definition:** ...
**Business Context:** ...
**Data Usage:** ...
**Related Terms:** ...
**Source:** ...
```

## Dependencies

- L100 system-level patterns (governance, observability, security, error handling)
- Previous waves' outputs (see L100 wave descriptions)

## Open Questions

_To be resolved during L200 detailed design._

## Testing Strategy

_To be defined per component._

## Deployment

Deployed as part of the Genie Build Waves pipeline. See L100 for the overall orchestration model.
