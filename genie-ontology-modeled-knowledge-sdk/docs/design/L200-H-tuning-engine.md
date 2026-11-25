# L200-H — Tuning Engine

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24

**Parent:** [L100 — Genie Ontology Modeled Knowledge SDK](L100-genie-ontology-modeled-knowledge-sdk.md)
**Wave:** Wave 8

## Scope

This component generates and executes a tuning plan following the core principle: **tune the metric views first, not the agent**.

### Tuning Plan Structure

#### Phase 1: Metric View Tuning (Priority)

| Check | Action |
|---|---|
| Synonym coverage | Are synonyms comprehensive enough for natural language? |
| Comment clarity | Do comments explain business logic clearly? |
| Display name quality | Are display names business-friendly? |
| Edge cases | Null handling, zero denominators, time zone boundaries |
| Filter accuracy | Do filtered measures match business intent? |
| Missing measures | Would common questions need measures that don't exist? |

#### Phase 2: Agent Tuning (Minimal — Avoid Overfitting)

- Add text instructions ONLY for genuinely ambiguous terms
- Add example SQLs ONLY for complex multi-step queries the agent consistently gets wrong
- Do NOT add instructions that duplicate MV comments/synonyms
- Do NOT add example SQLs for straightforward single-MV queries

#### Phase 3: Benchmark Questions

- Generate 10–20 benchmark questions per agent from domain research
- Run benchmarks via the Genie conversation API
- Evaluate accuracy: correct SQL, correct results, correct interpretation
- Iterate on MV definitions (not agent instructions) for failures

### Output

- `docs/tuning/tuning_plan.md` — the plan with specific actions per MV and agent
- `docs/tuning/benchmark_results.md` — benchmark question results and accuracy scores
- Updated metric view YAMLs (synonyms, comments, measures)
- Updated `.geniespace.json` (only if Phase 2 changes are needed)

## Dependencies

- L100 system-level patterns (governance, observability, security, error handling)
- Previous waves' outputs (see L100 wave descriptions)

## Open Questions

_To be resolved during L200 detailed design._

## Testing Strategy

_To be defined per component._

## Deployment

Deployed as part of the Genie Build Waves pipeline. See L100 for the overall orchestration model.
