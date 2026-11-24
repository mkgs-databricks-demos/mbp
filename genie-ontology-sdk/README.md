# genie-ontology-sdk

A developer toolkit that automates the end-to-end standup of modeled knowledge for Genie Ontology — from raw Unity Catalog assets and supplemental business context through to registered metric views, UC Pages, curated Genie Agents, and an initial tuning plan.

Codifies the [Rapid Ontology Standup](../genie-build-waves) methodology into a repeatable, metadata-driven pipeline orchestrated by [Genie Build Waves](../genie-build-waves) workflows deployed as Databricks Asset Bundles (DABs).

## Documents

| Document | Description |
|---|---|
| [L100 — System Architecture](docs/design/L100-genie-ontology-sdk.md) | System-level overview, input contract, two-DAB architecture, 10 Genie Build Waves, resolved design decisions |
| [L200-A — Input Validation & Repo Scaffolding](docs/design/L200-A-input-validation.md) | Wave 0: input contract, branch creation, folder structure |
| [L200-B — Domain Research Engine](docs/design/L200-B-domain-research.md) | Wave 1: web search orchestration, research document generation |
| [L200-C — Supplemental Context Parser](docs/design/L200-C-supplemental-context.md) | Wave 2: file parsing, dashboard extraction, semantic capture |
| [L200-D — Deep Exploratory Data Analyzer](docs/design/L200-D-deep-eda.md) | Wave 3: table profiling, relationship detection, quality assessment |
| [L200-E — Metric View Synthesizer](docs/design/L200-E-metric-view-synthesizer.md) | Wave 4: context synthesis, YAML generation, materialization auto-detect |
| [L200-F — Metric View & Pages Registration](docs/design/L200-F-registration-pipeline.md) | Waves 5 + 5.5: forEach MV workflow, Genie Code Pages task, DAB 1 |
| [L200-G — Genie Agent Curator](docs/design/L200-G-genie-agent-curator.md) | Waves 6–7: agent organization, `.geniespace.json` generation, DAB 2 |
| [L200-H — Tuning Engine](docs/design/L200-H-tuning-engine.md) | Wave 8: benchmark generation, tuning plan, iterative improvement |

## Research

| Document | Description |
|---|---|
| [Metric View CI/CD Best Practices](docs/research/metric-view-cicd-best-practices.md) | YAML-as-contract, `CREATE OR REPLACE VIEW`, parameterization, testing levels |
| [Genie Agent API & DAB Deployment](docs/research/genie-agent-api-deployment.md) | Management API, `serialized_space`, native DAB `genie_spaces` resource |
| [Semantic Metadata Strategy](docs/research/semantic-metadata-strategy.md) | When and how to add comments, synonyms, display_names, formats |

## Semantics

| Document | Description |
|---|---|
| [SDK Glossary](docs/semantics/sdk-glossary.md) | Terms and definitions used throughout the SDK design |

## Pitch

| Document | Description |
|---|---|
| [SDK Overview (HTML)](docs/pitch/genie-ontology-sdk-overview.html) | Customer-facing standalone HTML presentation — Databricks branded, 4 sections (Overview, How It Works, What You Get, Why It Matters) |
| [SDK Overview (Genie Artifact)](genie_artifacts/Genie%20Ontology%20Modeled%20Knowledge%20SDK.ga) | Interactive Genie artifact version with tabbed navigation — same content, viewable in Genie One side panel |

## Diagrams

| Diagram | Description |
|---|---|
| [01 — SDK Architecture Overview](docs/diagrams/mermaid/01_sdk_architecture_overview.md) | High-level system architecture |
| [02 — Genie Build Waves Sequence](docs/diagrams/mermaid/02_genie_build_waves_sequence.md) | Wave execution flow |
| [03 — Two-DAB Deployment Model](docs/diagrams/mermaid/03_two_dab_deployment.md) | DAB 1 + DAB 2 deployment architecture |
| [04 — forEach Registration Flow](docs/diagrams/mermaid/04_foreach_registration_flow.md) | Metric view forEach task detail |
| [05 — CI/CD Promotion Path](docs/diagrams/mermaid/05_cicd_promotion_path.md) | Dev → Tst → UAT → Prd promotion |

## Examples

| Example | Description |
|---|---|
| [DAB 1 — Metric View Registration Bundle](examples/dab1_metric_views/) | Complete example DAB for metric view registration with forEach |
| [DAB 2 — Genie Agent Bundle](examples/dab2_genie_agents/) | Complete example DAB for Genie Agent deployment |
| [Sample Metric View YAML](examples/metric_views/sales/) | Example parameterized metric view YAMLs |
| [Sample Genie Agent Config](examples/agents/) | Example `.geniespace.json` |


## Plans (L300 — Genie Code Session Documents)

| Plan | Wave | Session | Mode | Effort |
|---|---|---|---|---|
| [waves.json](docs/plans/waves.json) | — | Manifest | — | — |
| [INDEX](docs/plans/INDEX.md) | — | Session map & dependency graph | — | — |
| [01 Input Validation](docs/plans/01_input_validation_scaffolding.md) | 0 | Init & scaffold | execute | Light |
| [02 Domain Research](docs/plans/02_domain_research.md) | 1 | Web search, KPIs, glossary | execute | Medium |
| [03 Supplemental Context](docs/plans/03_supplemental_context.md) | 2 | File parsing, dashboard extraction | execute | Medium |
| [04 Deep EDA](docs/plans/04_deep_eda.md) | 3 | Table profiling, relationships | execute | Heavy |
| [05 MV Synthesis](docs/plans/05_metric_view_synthesis.md) | 4 | YAML generation, materialization | edit | Heavy |
| [06 MV Registration](docs/plans/06_metric_view_registration.md) | 5 | forEach CREATE OR REPLACE VIEW | execute | Medium |
| [07 Pages Registration](docs/plans/07_pages_registration.md) | 5.5 | UC Pages via Pages API | execute | Light |
| [08 Agent Curation](docs/plans/08_genie_agent_curation.md) | 6 | .geniespace.json generation | edit | Heavy |
| [09 Agent Deployment](docs/plans/09_genie_agent_deployment.md) | 7 | Deploy via Genie API | execute | Medium |
| [10 Tuning](docs/plans/10_tuning_engine.md) | 8 | Benchmark, diagnose, fix MVs | execute | Heavy |

## Sessions

| Session | Description |
|---|---|
| [2026-11-24 — Initial Design](docs/sessions/2026-11-24_initial-design.md) | L100 design, open question resolution, file creation |

## Cross-References

- **[genie-build-waves](../genie-build-waves)** — The orchestration engine this SDK uses
- **[developer-user-isolation-in-uc](../developer-user-isolation-in-uc)** — UC naming convention and zero-hardcoding rule
- **[sdlc-best-practices](../sdlc-best-practices)** — DAB deployment patterns and CI/CD
