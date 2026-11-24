# genie-ontology-sdk

A developer toolkit that automates the end-to-end standup of modeled knowledge for Genie Ontology — from raw Unity Catalog assets and supplemental business context through to registered metric views, UC Pages, curated Genie Agents, and an initial tuning plan.

Codifies the Rapid Ontology Standup methodology into a repeatable, metadata-driven pipeline orchestrated by [Genie Build Waves](../genie-build-waves) workflows deployed as Declarative Automation Bundles (DABs).

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


## Build Plans (genie-build-waves)

Build-0 builds the SDK, then dogfoods it on `samples.tpch` (`examples/tpch/`). See the [plan index](docs/plans/INDEX.md) for the wave map, contracts and dependency graph.

| Wave | Sessions | Delivers |
|---|---|---|
| 0-0 | [01](docs/plans/build-0/01_sdk_foundation.md) | Package skeleton, input contract (`config.py`), pytest scaffold |
| 0-1 | [02](docs/plans/build-0/02_mv_yaml_library.md), [03](docs/plans/build-0/03_geniespace_builder.md), [04](docs/plans/build-0/04_pages_and_benchmark.md), [05a](docs/plans/build-0/05a_discovery_skills.md), [05b](docs/plans/build-0/05b_synthesis_skills.md) | MV YAML library, Genie Agent builder, Pages + benchmark helpers, six pipeline skills |
| 0-2 | [06](docs/plans/build-0/06_mv_bundle_template.md), [07](docs/plans/build-0/07_agent_bundle_template.md), [08](docs/plans/build-0/08_run_kit.md) | Two bundle templates, pipeline-run kit |
| 0-3 | [09](docs/plans/build-0/09_init_and_tpch_scaffold.md) | Init notebook + scaffold, TPC-H project |
| 0-4 | [10a](docs/plans/build-0/10a_tpch_domain_research.md), [10b](docs/plans/build-0/10b_tpch_deep_eda.md) | TPC-H research, glossary, data profiles |
| 0-5 | [11](docs/plans/build-0/11_tpch_mv_synthesis.md) | TPC-H metric view YAMLs |
| 0-6 | [12](docs/plans/build-0/12_tpch_mv_registration.md) | Registered TPC-H metric views (dev) |
| 0-7 | [13](docs/plans/build-0/13_tpch_uc_pages.md), [14](docs/plans/build-0/14_tpch_agent_curation.md) | UC Pages, Genie Agent config |
| 0-8 | [15](docs/plans/build-0/15_tpch_agent_deployment.md) | Deployed TPC-H Genie Agent (dev) |
| 0-9 | [16](docs/plans/build-0/16_tpch_tuning.md) | Benchmark + MV-first tuning |
| 0-10 | [17](docs/plans/build-0/17_build0_docs.md) | Docs and build-0 observations |

Manifest: [docs/plans/waves.json](docs/plans/waves.json). The original pipeline-run plans (Waves 0-8 of the L100 design) are kept as reference in [docs/design/l300-pipeline/](docs/design/l300-pipeline/README.md).

## Project Memory

[PROJECT_MEMORY.md](PROJECT_MEMORY.md): status, decisions, conventions and open items. Read it before any session.

## Sessions

| Session | Description |
|---|---|
| [2026-11-24 — Build-0 Planning](docs/sessions/2026-11-24_build-0-planning.md) | Fresh build-0 plan set, manifest, original plans moved to reference |
| [2026-11-24 — Initial Design](docs/sessions/2026-11-24_initial-design.md) | L100 design, open question resolution, file creation, design review |

## Cross-References

- **[genie-build-waves](../genie-build-waves)** — The orchestration engine this SDK uses
- **[developer-user-isolation-in-uc](../developer-user-isolation-in-uc)** — UC naming convention and zero-hardcoding rule
- **[sdlc-best-practices](../sdlc-best-practices)** — DAB deployment patterns and CI/CD
