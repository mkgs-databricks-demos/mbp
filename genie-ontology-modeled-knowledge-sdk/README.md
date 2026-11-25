# genie-ontology-modeled-knowledge-sdk

A developer toolkit that automates the end-to-end standup of modeled knowledge for Genie Ontology — from raw Unity Catalog assets and supplemental business context through to registered metric views, UC Pages, curated Genie Agents, and an initial tuning plan.

Codifies the Rapid Ontology Standup methodology into a repeatable, metadata-driven pipeline orchestrated by [genie-build-waves](../genie-build-waves/README.md) Lakeflow Jobs and deployed as Declarative Automation Bundles.

**Status: build-0 complete** (waves 0-0 to 0-10 passed their gates; wave 0-10 wrote these docs). The library, six skills, two bundle templates, the run kit and the init tool exist, and the SDK was dogfooded end to end on `samples.tpch` (7 metric views registered, 1 Genie Agent deployed, 93.3% baseline benchmark accuracy). UC Pages were dry-run only (no Discover domain). Gaps for build 1: [build-0 observations](docs/build-0-observations.md) and [build-1 requests](docs/plans/build-1/REQUESTS.md).

## Quickstart

1. Read the [usage guide](docs/usage.md) (prerequisites, overrides files, running a build).
2. Run the `notebooks/init_ontology_project` notebook on serverless: fill the widgets, fix any `validate_config` / `check_access` problem, then set `target_dir` and scaffold your project.
3. Write the two gitignored `variable-overrides.json` files, render the agent files and run `databricks bundle validate --strict` on both bundles.
4. Deploy a genie-build-waves instance for the project with the [run kit](templates/run/README.md) manifest and start the build.
5. Compare your outputs with the [TPC-H example](examples/tpch/README.md).

Local checks from the SDK root:

```bash
pip install pyyaml jsonschema pytest
python -m pytest -q
PYTHONPATH=src python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate <project>/ontology-metric-views/metric_views
```

## Getting the SDK

The SDK is a pure-Python wheel, `genie_ontology_modeled_knowledge_sdk-<version>-py3-none-any.whl` (version in `pyproject.toml`, history in [CHANGELOG.md](CHANGELOG.md)). Three ways to use it:

| Way | When | How |
|---|---|---|
| **Wheel (default)** | Every project | The SDK bundle at this folder's root builds the wheel on `bundle deploy` and uploads it to its `sdk_wheels` volume ([docs/distribution/README.md](docs/distribution/README.md)). Project bundles install it through a job environment (`sdk_volume_path`, `sdk_wheel_subpath`, `sdk_version`, `sdk_wheel` in `templates/ontology-metric-views`). Notebooks: `%pip install --upgrade databricks-sdk <wheel path>` then `dbutils.library.restartPython()` |
| **Vendored (opt-in)** | Workspaces without package egress or that cannot read the volume | `scaffold_project(..., vendor=True)` / `gos-scaffold --vendor` copies the import closure of the SDK modules the project notebooks use into `ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored/` with a `VENDORED_VERSION` file |
| **Editable (SDK development)** | Working on the SDK itself | `pip install -e ".[dev]"` from this folder |

Console scripts installed with the wheel: `gos-check-config`, `gos-validate-mv`, `gos-build-manifest`, `gos-render-agents`, `gos-scaffold`, `gos-resolve-target`, `gos-benchmark`. `python -m genie_ontology_modeled_knowledge_sdk.<module>` keeps working.

## Layout

| Path | Contents |
|---|---|
| `src/genie_ontology_modeled_knowledge_sdk/` | Python library (see Library) and `schemas/sdk_config.schema.json` |
| `tests/` | pytest suite with fixtures for every module, the templates and the run kit |
| `skills/` | six Genie Code skills, one per pipeline stage |
| `templates/` | `ontology-metric-views` (DAB 1), `ontology-genie-agents` (DAB 2), `run` (run kit) |
| `notebooks/` | `init_ontology_project` init and scaffold notebook |
| `examples/tpch/` | build-0 dogfood project on `samples.tpch` |
| `docs/` | design, research, plans, sessions, reviews, diagrams, pitch |
| `Genie Code Start Session - DO NOT EDIT.ipynb` | Genie Code start-session notebook for this project (do not edit) |

Package layout and module contracts: [docs/design/sdk-layout.md](docs/design/sdk-layout.md). Packaging: [pyproject.toml](pyproject.toml).

## Library

| Module | Purpose |
|---|---|
| [config.py](src/genie_ontology_modeled_knowledge_sdk/config.py) | `sdk_config.json` input contract: load, `validate_config`, `check_access` |
| [mv_yaml.py](src/genie_ontology_modeled_knowledge_sdk/mv_yaml.py) | metric view YAML: load, token substitution, rules MV001-MV007, `render_ddl`, `validate` CLI |
| [manifest.py](src/genie_ontology_modeled_knowledge_sdk/manifest.py) | `manifest.json` for the forEach registration job |
| [geniespace.py](src/genie_ontology_modeled_knowledge_sdk/geniespace.py) | Genie Agent planning (50-view rule), `build_space`, `validate_space`, domain manifest, `render` CLI |
| [pages.py](src/genie_ontology_modeled_knowledge_sdk/pages.py) | glossary parsing and UC Pages upsert (dry run first) |
| [benchmark.py](src/genie_ontology_modeled_knowledge_sdk/benchmark.py) | benchmark questions, Genie runs and scoring |
| [scaffold.py](src/genie_ontology_modeled_knowledge_sdk/scaffold.py) | `scaffold_project` and CLI: copies templates, run kit and vendored modules into a project |

## Skills

| Skill | Stage |
|---|---|
| [ontology-domain-research](skills/ontology-domain-research/SKILL.md) | web research, KPI definitions, glossary, domain/subdomain proposal |
| [ontology-context-extraction](skills/ontology-context-extraction/SKILL.md) | supplemental files and dashboard exports |
| [ontology-deep-eda](skills/ontology-deep-eda/SKILL.md) | table profiles, grains, verified join cardinalities |
| [ontology-mv-synthesis](skills/ontology-mv-synthesis/SKILL.md) | parameterized metric view YAML and materialization blocks |
| [ontology-agent-curation](skills/ontology-agent-curation/SKILL.md) | `.geniespace.json` agents, sample questions, example SQL |
| [ontology-tuning](skills/ontology-tuning/SKILL.md) | benchmark, metric-view-first tuning plan |

The skills live only in this folder in build-0. Build sessions load them from the run-as user's workspace skills folder; publishing them to Unity Catalog is build-1 request R1.

## Templates

| Template | Contents |
|---|---|
| [ontology-metric-views](templates/ontology-metric-views/README.md) | DAB 1: schema resource, `register_metric_views` job (manifest, forEach registration, smoke and cardinality tests) |
| [ontology-genie-agents](templates/ontology-genie-agents/README.md) | DAB 2: `genie_spaces` resources (`engine: direct`), tokenized agent files rendered into gitignored `.rendered/` |

## Run kit

[templates/run](templates/run/README.md) is a genie-build-waves manifest ([waves.json](templates/run/waves.json)) with 10 session plans in 7 waves (inputs check, discovery, synthesis, registration, pages + curation, agent deployment, tuning). The scaffold copies it into `docs/plans/` of each project. Wave map and contracts: [run kit INDEX](templates/run/INDEX.md).

## TPC-H example

[examples/tpch](examples/tpch/README.md) was scaffolded by the SDK and filled by build-0 waves 0-4 to 0-9:

| Output | Result |
|---|---|
| [Domain/subdomain proposal](examples/tpch/docs/research/05_domain_subdomain_proposal.md) | `tpch_supply_chain`: sales, fulfillment, procurement; 23 glossary terms |
| [Data model summary](examples/tpch/docs/data_profiles/data_model_summary.md) | 8 table profiles, 10 verified many-to-one joins |
| [Registration results](examples/tpch/docs/registration/registration_results.md) | 7 metric views registered, smoke and cardinality pass |
| [Pages registration](examples/tpch/docs/pages/pages_registration.md) | dry run only; needs a Discover domain |
| [Agent validation](examples/tpch/docs/deployment/agent_validation.md) | 1 Genie Agent, 3/3 probes succeeded |
| [Benchmark results](examples/tpch/docs/tuning/benchmark_results.md) | 15 questions, 93.3% baseline accuracy |

The older hand-written examples (`examples/dab1_metric_views/`, `examples/dab2_genie_agents/`, `examples/metric_views/`, `examples/agents/`) are kept as history; the templates replace them.

## Documents

| Document | Description |
|---|---|
| [L100 — System Architecture](docs/design/L100-genie-ontology-modeled-knowledge-sdk.md) | System-level overview, input contract, two-DAB architecture, 10 Genie Build Waves, resolved design decisions |
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
| [SDK Overview (HTML)](docs/pitch/genie-ontology-modeled-knowledge-sdk-overview.html) | Customer-facing standalone HTML presentation — Databricks branded, 4 sections (Overview, How It Works, What You Get, Why It Matters) |

## Diagrams

| Diagram | Description |
|---|---|
| [01 — SDK Architecture Overview](docs/diagrams/mermaid/01_sdk_architecture_overview.md) | High-level system architecture |
| [02 — Genie Build Waves Sequence](docs/diagrams/mermaid/02_genie_build_waves_sequence.md) | Wave execution flow |
| [03 — Two-DAB Deployment Model](docs/diagrams/mermaid/03_two_dab_deployment.md) | DAB 1 + DAB 2 deployment architecture |
| [04 — forEach Registration Flow](docs/diagrams/mermaid/04_foreach_registration_flow.md) | Metric view forEach task detail |
| [05 — CI/CD Promotion Path](docs/diagrams/mermaid/05_cicd_promotion_path.md) | Dev → Tst → UAT → Prd promotion |

## Plans

Build-0 built the SDK, then dogfooded it on `samples.tpch` (`examples/tpch/`). See the [build-0 plan index](docs/plans/INDEX.md) for the wave map, contracts and dependency graph. Waves 0-0 to 0-10 passed their gates; wave 0-10 is this documentation pass. Wave 0-7 failed its gate at first, because the UC Pages session (13) was blocked on the missing Discover domain, and passed after the owner deferred publishing to build 1 (see [build-1 request R3 item 3](docs/plans/build-1/REQUESTS.md#r3-fix-the-run-kit)).

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

Manifest: [docs/plans/waves.json](docs/plans/waves.json). The original pipeline-run plans (Waves 0-8 of the L100 design) are kept as reference in [docs/design/l300-pipeline/](docs/design/l300-pipeline/README.md); the run kit was built from them.

| Next | Document |
|---|---|
| Build-0 wrap-up (verdict, owner decisions, open items) | [docs/sessions/2026-11-25_build-0-wrap-up.md](docs/sessions/2026-11-25_build-0-wrap-up.md) |
| Build-0 code review | [docs/reviews/2026-11-25_build-0-sdk-review.md](docs/reviews/2026-11-25_build-0-sdk-review.md) |
| Build-1 requests (R1-R9, owner-accepted) | [docs/plans/build-1/REQUESTS.md](docs/plans/build-1/REQUESTS.md) |
| Build-0 observations (skill gaps, template fixes) | [docs/build-0-observations.md](docs/build-0-observations.md) |

## Project Memory

[PROJECT_MEMORY.md](PROJECT_MEMORY.md): status, decisions, conventions and open items. Read it before any session.

## Sessions

Session summaries (one per build session, with run and resource ids) are indexed in [docs/sessions/INDEX.md](docs/sessions/INDEX.md), newest first.

## Cross-References

* **[genie-build-waves](../genie-build-waves/README.md)**: the orchestration engine this SDK uses
* **developer-user-isolation-in-uc** (sibling folder in this repository): UC naming convention and zero-hardcoding rule
* **[sdlc-best-practices](../sdlc-best-practices/README.md)**: bundle deployment patterns and CI/CD
