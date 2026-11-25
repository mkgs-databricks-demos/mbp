# Semantic Metadata Strategy

Matthew Giglia | Databricks Field Engineering
Version: 1.0 | Date: 2026-11-24

## Summary

Semantic metadata on metric view dimensions and measures improves usability in dashboards and AI tools (Genie Agents, Genie One, Genie Code). This document defines when and how the SDK should generate metadata.

## Available Metadata Fields

| Field | Purpose | When to Add |
|---|---|---|
| `comment` | Business meaning, units, caveats, logic | When `expr` doesn't make the meaning obvious |
| `display_name` | Human-readable label (max 255 chars) | When it differs meaningfully from `name` |
| `synonyms` | Alternative names for AI/LLM discovery (up to 10) | Genuinely different terms a user might search for |
| `format` | Display formatting (currency, percentage, date, etc.) | When it changes how the value displays for business users |

## When NOT to Add Metadata

- `display_name` that is just `name` in Title Case (`order_date` → `Order Date`)
- `comment` that restates the name (`Order date` for `order_date`)
- `synonyms` that are rewordings of the name (`order date`, `date of order` for `order_date`)
- `format` on counts, integer sums, IDs, or string dimensions
- `decimal_places` on an integer result

## SDK Generation Rules

### Wave 1 (Domain Research) → Synonyms

Web search identifies industry-standard terminology. Map these to metric view synonyms:

```yaml
measures:
  - name: Revenue
    expr: SUM(source.order_amount)
    synonyms:
      - sales
      - net sales
      - order revenue
      - top line
```

### Wave 2 (Supplemental Context) → Comments

Business requirements and dashboard definitions provide the business logic:

```yaml
measures:
  - name: Revenue
    expr: SUM(source.order_amount)
    comment: "Completed-order revenue in USD after order-level exclusions. Excludes refunds and cancellations."
```

### Wave 3 (Deep EDA) → Format

Data profiling reveals the appropriate display format:

```yaml
measures:
  - name: Revenue
    expr: SUM(source.order_amount)
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
```

### Composite Example

```yaml
measures:
  - name: Revenue
    expr: SUM(source.order_amount)
    comment: "Completed-order revenue in USD after order-level exclusions"
    display_name: "Total Revenue"
    synonyms:
      - sales
      - net sales
      - order revenue
    format:
      type: currency
      currency_code: USD
      abbreviation: compact
```

## Tuning Priority (Wave 8)

1. **Synonyms** — most impactful for Genie Agent accuracy. If a user says "sales" and the metric is called "revenue," synonyms bridge the gap.
2. **Comments** — second most impactful. Genie uses comments to disambiguate between similar measures.
3. **Display names** — cosmetic but important for dashboard readability.
4. **Format** — cosmetic. Affects rendering, not AI understanding.

## Key Principle

Tune the metric views first, not the agent. Synonyms and comments in metric view YAML are the first lever for improving Genie Agent accuracy. Agent-specific instructions are overfitting.

## Sources

- Databricks documentation: Agent metadata in metric views
- Databricks documentation: Metric view YAML syntax reference
