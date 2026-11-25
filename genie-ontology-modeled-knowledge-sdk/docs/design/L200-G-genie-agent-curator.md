# L200-G — Genie Agent Curator

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24

**Parent:** [L100 — Genie Ontology Modeled Knowledge SDK](L100-genie-ontology-modeled-knowledge-sdk.md)
**Wave:** Waves 6–7

## Scope

This component handles Genie Agent organization, configuration generation, and deployment:

### Wave 6: Agent Curation

#### Organization Logic

- If ≤ 50 metric views → single agent for the domain
- If > 50 → split by subdomain:
  - Minimize redundancy (no MV in multiple agents unless cross-domain)
  - Minimize ambiguity (similar measures in the same agent, not split)
  - Maximize usability (group by business function, not technical structure)
- Cross-domain MVs assigned to the most natural subdomain agent
- Related agents get join instructions pointing to each other

#### `.geniespace.json` Generation

For each agent, generate:

| Section | Source |
|---|---|
| `data_sources.tables` | Registered metric views from Wave 5 |
| `instructions.text_instructions` | Synthesized from research + business rules |
| `instructions.example_question_sqls` | Generated from common KPI patterns |
| `instructions.join_specs` | Verified join relationships from Wave 3 |
| `config.sample_questions` | Domain-relevant business questions from Wave 1 |

#### Domain Manifest (Hybrid)

Generate `docs/domain_manifest.yml` — proposed domain/subdomain structure:

```yaml
domains:
  - name: Sales Analytics
    description: Revenue, customer, and order metrics
    subdomains:
      - name: Revenue
        metric_views: [mv_sales_revenue, mv_monthly_revenue]
        agent: sales_revenue_agent
      - name: Customer
        metric_views: [mv_customer_retention, mv_customer_ltv]
        agent: sales_customer_agent
```

### Wave 7: Agent Deployment

- Deploys DAB 2 with generated `.geniespace.json` files
- Uses native `genie_spaces` resource with `file_path`
- Validates each agent is accessible and responds to sample questions

## Dependencies

- L100 system-level patterns (governance, observability, security, error handling)
- Previous waves' outputs (see L100 wave descriptions)

## Open Questions

_To be resolved during L200 detailed design._

## Testing Strategy

_To be defined per component._

## Deployment

Deployed as part of the Genie Build Waves pipeline. See L100 for the overall orchestration model.
