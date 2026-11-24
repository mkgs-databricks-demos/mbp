# L100 — Genie Ontology SDK

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24 | Status: Design Phase 1

## Executive Summary

The **Genie Ontology SDK** is a developer toolkit that automates the end-to-end standup of modeled knowledge for Genie Ontology — from raw Unity Catalog assets and supplemental business context through to registered metric views, UC Pages, curated Genie Agents, and an initial tuning plan. It codifies the **Rapid Ontology Standup** methodology into a repeatable, metadata-driven pipeline orchestrated by **Genie Build Waves** workflows deployed as **Databricks Asset Bundles (DABs)**.

**Core value proposition:** What currently takes an experienced FDE 2–5 days of interactive Genie Code sessions becomes a parameterized, CI/CD-ready pipeline that any SA, FDE, or customer data engineer can execute against their own Unity Catalog assets.

## Inputs & Interface Contract

### Required Inputs

| Input | Type | Description |
|---|---|---|
| `source_catalogs` | `ARRAY<STRING>` | UC catalogs to evaluate |
| `source_schemas` | `ARRAY<STRING>` | UC schemas to evaluate (optional if catalogs provided) |
| `source_tables` | `ARRAY<STRING>` | Specific UC tables, 3-part names (optional if catalogs/schemas provided) |
| `repo_path` | `STRING` | Workspace repo path the developer has access to |
| `target_catalog` | `STRING` | Target catalog for metric view registration |
| `target_schema` | `STRING` | Target schema for metric view registration |
| `domain_context` | `STRING` | Free-text description of the domain/use case being modeled |

### Optional Inputs

| Input | Type | Description |
|---|---|---|
| `supplemental_volume_dirs` | `ARRAY<STRING>` | UC Volume directories with supplemental context |
| `dashboard_inputs` | `ARRAY<STRING>` | Volume paths to PowerBI/Tableau/dashboard exports |
| `source_catalog_for_reads` | `STRING` | Source catalog override for MV YAML `source:` references |
| `source_schema_for_reads` | `STRING` | Source schema override |
| `warehouse_id` | `STRING` | SQL warehouse for registration and deployment |
| `max_metric_views_per_agent` | `INT` | Threshold for agent splitting (default: 50) |

### Zero Hardcoding Rule

Nothing is hardcoded. Metric view YAMLs use parameterized `source:` references so the same YAML deploys to dev, tst, uat, and prd by changing only `target_catalog` and `source_catalog_for_reads`. The catalog is the environment discriminator.

## Architecture: Two DABs

### DAB 1: Metric View Registration Bundle

Owns the metric view YAML definitions and the forEach workflow that registers them.

> See [Diagram 03 — Two-DAB Deployment Model](../diagrams/mermaid/03_two_dab_deployment.md)
> See [Example DAB 1](../../examples/dab1_metric_views/)

### DAB 2: Genie Agent Bundle

Owns the Genie Agent definitions (`.geniespace.json` files) and deployment. Uses the native DAB `genie_spaces` resource type with `file_path`. Requires `engine: direct`.

> See [Example DAB 2](../../examples/dab2_genie_agents/)

## Genie Build Waves

> See [Diagram 01 — SDK Architecture Overview](../diagrams/mermaid/01_sdk_architecture_overview.md)
> See [Diagram 02 — Genie Build Waves Sequence](../diagrams/mermaid/02_genie_build_waves_sequence.md)

### Wave 0: Initialization
- Creates feature branch `ontology-sdk/<domain>-<timestamp>`
- Scaffolds folder structure
- Validates all inputs

### Wave 1: Domain Research
- Web search for semantic definitions, KPIs, industry trends, regulatory context
- Identifies candidate domains, sub-domains, UC Pages
- Output: `docs/research/*.md`

### Wave 2: Supplemental Context Extraction
- Reads supplemental volume directories
- Parses markdown, PDF, DOCX, CSV
- Extracts from dashboard inputs (PowerBI/Tableau)
- Output: `docs/context/*.md` + `docs/semantics/*.md`

### Wave 3: Deep Exploratory Data Analysis
- Profiles each source table: structure, integrity, quality, lineage, usage, update cadence, grain, primary/foreign keys, cardinality, volume
- Output: `docs/data_profiles/*.md`

### Wave 4: Synthesis & Metric View Candidate Generation
- Synthesizes all context into parameterized metric view YAMLs
- Auto-generates `materialization:` blocks for MVs meeting cost/complexity thresholds
- Output: `metric_views/<domain>/*.yml` + `manifest.json`

### Wave 5: Metric View Registration
- Executes DAB 1 forEach workflow
- `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`
- Smoke tests + join cardinality tests
- Output: Registered metric views

> See [Diagram 04 — forEach Registration Flow](../diagrams/mermaid/04_foreach_registration_flow.md)

### Wave 5.5: UC Pages Registration
- Formats glossary candidates as UC Pages
- Deploys via Genie Code workflow task (Pages API)
- Output: Registered UC Pages

### Wave 6: Genie Agent Curation
- Determines agent organization (≤50 MVs = single agent; >50 = split by subdomain)
- Generates `.geniespace.json` for each agent
- Output: `agents/*.geniespace.json`

### Wave 7: Genie Agent Deployment
- Deploys DAB 2 with generated `.geniespace.json` files
- Validates agents are accessible
- Output: Deployed Genie Agents

### Wave 8: Tuning Plan & Execution
- Tune metric views first (synonyms, comments, measures)
- Agent instructions only for genuinely ambiguous terms
- Generate and run 10–20 benchmark questions per agent
- Output: `docs/tuning/tuning_plan.md` + updated YAMLs

## Resolved Design Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Pages deployment | Include — full automation | Pages are core to Genie Ontology. Wave 5.5 added. |
| 2 | Domain/Subdomain | Hybrid — generate proposal, opt-in creation | Domain taxonomy is an enterprise governance decision. |
| 3 | Materialization | Include — auto-generate blocks | Wave 3 EDA feeds Wave 4 synthesis. Carelon $60K/yr proof point. |
| 4 | SGT App integration | Defer — separate products | No coupling between codebases. |
| 5 | Observability | Defer — separate concern | Wait for native Genie Agent tracing. |
| 6 | Incremental re-runs | Full regeneration | Idempotent via `CREATE OR REPLACE VIEW`. |
| 7 | Multi-workspace | Single workspace v1 | Parameterized DABs are already portable. |

## CI/CD: Target Portability

> See [Diagram 05 — CI/CD Promotion Path](../diagrams/mermaid/05_cicd_promotion_path.md)

```
dev (personalized schemas) → tst → uat → prd
```

Only `target_catalog`, `source_catalog`, `warehouse_id`, and `workspace.host` change between environments.

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Two DABs, not one | Different deployment lifecycles |
| forEach for MV registration | Adding a MV = adding a YAML file |
| Parameterized YAML | Same YAML deploys to any catalog/schema |
| Tune MVs before agents | Agent instructions are overfitting |
| Genie Build Waves via DABs | `genie_task` works inside `for_each` |
| `CREATE OR REPLACE VIEW` | Idempotent, no outage window |
| Native DAB `genie_spaces` | `file_path` to `.geniespace.json`, `engine: direct` |
| 50 MV threshold | Empirical limit for agent usability |
| Web search for research | Ground ontology in real-world business language |

## L200 Decomposition

| L200 | Scope |
|---|---|
| [L200-A](L200-A-input-validation.md) | Wave 0 — Input validation & repo scaffolding |
| [L200-B](L200-B-domain-research.md) | Wave 1 — Domain research engine |
| [L200-C](L200-C-supplemental-context.md) | Wave 2 — Supplemental context parser |
| [L200-D](L200-D-deep-eda.md) | Wave 3 — Deep exploratory data analyzer |
| [L200-E](L200-E-metric-view-synthesizer.md) | Wave 4 — Metric view synthesizer |
| [L200-F](L200-F-registration-pipeline.md) | Waves 5 + 5.5 — Registration pipeline |
| [L200-G](L200-G-genie-agent-curator.md) | Waves 6–7 — Genie Agent curator |
| [L200-H](L200-H-tuning-engine.md) | Wave 8 — Tuning engine |

## Cross-References

| Asset | Relationship |
|---|---|
| Rapid Ontology Standup | The SDK automates L200-A (MV Standup) and L200-B (Agent Standup) |
| mbp/genie-build-waves | Orchestration engine |
| mbp/genie-production-readiness | Deployed agents should meet the 9 requirements |
| Frictionless Analyst Deployments | SDK is the data engineer counterpart |
| Lattice | Produces the Genie Ontology that Lattice consumes |
