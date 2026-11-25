# Build Plan Index — Genie Ontology Modeled Knowledge SDK

> **Build 1:** see [build-1/INDEX.md](build-1/INDEX.md) (waves `1-0`..`1-17`, sessions 18-45). This file is the build-0 index; its waves are archived in `waves.json`.

## Overview

**Build-0** builds the reusable Genie Ontology Modeled Knowledge SDK:
* a Python library
* Genie Code skills for each pipeline stage
* two bundle templates
* a pipeline-run kit
* an init notebook

Then it dogfoods the SDK end to end on the public `samples.tpch` data, into `examples/tpch/`.

* Manifest: [waves.json](waves.json) (genie-build-waves, `hybrid` workflow, `build: "0"`, waves `0-0` .. `0-10`).
* Plans: [build-0/](build-0/).
* `build_root` = this SDK folder; the build branch is a job parameter. Sessions never run Git; the integrator is the only committer.
* Design inputs: [L100](../design/L100-genie-ontology-modeled-knowledge-sdk.md), L200-A..H, and the original pipeline-run plans in [l300-pipeline/](../design/l300-pipeline/README.md) (reference only).
* Workspace-specific values (catalog, warehouse, ids) never go in committed files outside `docs/sessions/`. Dogfood bundles read them from gitignored `.databricks/bundle/dev/variable-overrides.json` files.

## Wave Map

### Wave 0-0: Foundation
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [01](build-0/01_sdk_foundation.md) | SDK foundation & input contract | edit | — |

### Wave 0-1: Core libraries + skills
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [02](build-0/02_mv_yaml_library.md) | Metric view YAML library & manifest | edit | 01 |
| [03](build-0/03_geniespace_builder.md) | Genie Agent config builder | edit | 01 |
| [04](build-0/04_pages_and_benchmark.md) | UC Pages & benchmark helpers | edit | 01 |
| [05a](build-0/05a_discovery_skills.md) | Discovery skills (research, context, EDA) | edit | 01 |
| [05b](build-0/05b_synthesis_skills.md) | Synthesis skills (MV synthesis, curation, tuning) | edit | 01 |

### Wave 0-2: Templates + run kit
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [06](build-0/06_mv_bundle_template.md) | Metric view bundle template (DAB 1) | edit | 02 |
| [07](build-0/07_agent_bundle_template.md) | Genie Agent bundle template (DAB 2) | edit | 03 |
| [08](build-0/08_run_kit.md) | Pipeline-run kit | edit | 05a, 05b |

### Wave 0-3: Init tool (manual prerequisite: overrides files)
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [09](build-0/09_init_and_tpch_scaffold.md) | Init tool & TPC-H scaffold | edit (allow_execute) | 06, 07, 08 |

### Wave 0-4: Dogfood discovery
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [10a](build-0/10a_tpch_domain_research.md) | TPC-H domain research & glossary | edit (allow_execute) | 09 |
| [10b](build-0/10b_tpch_deep_eda.md) | TPC-H deep EDA | edit (allow_execute) | 09 |

### Wave 0-5: Dogfood synthesis
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [11](build-0/11_tpch_mv_synthesis.md) | TPC-H metric view synthesis | edit (allow_execute) | 10a, 10b |

### Wave 0-6: Dogfood registration
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [12](build-0/12_tpch_mv_registration.md) | TPC-H metric view registration | edit (allow_execute, allow_deploy) | 11 |

### Wave 0-7: UC Pages + agent curation
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [13](build-0/13_tpch_uc_pages.md) | TPC-H UC Pages registration | edit (allow_execute) | 10a, 12 |
| [14](build-0/14_tpch_agent_curation.md) | TPC-H Genie Agent curation | edit (allow_execute) | 12 |

### Wave 0-8: Agent deployment
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [15](build-0/15_tpch_agent_deployment.md) | TPC-H Genie Agent deployment | edit (allow_execute, allow_deploy) | 14 |

### Wave 0-9: Tuning
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [16](build-0/16_tpch_tuning.md) | TPC-H benchmark & tuning | edit (allow_execute, allow_deploy) | 15 |

### Wave 0-10: Docs
| Session | Title | Mode | Depends On |
|---|---|---|---|
| [17](build-0/17_build0_docs.md) | Build-0 documentation & observations | edit | 16 |

Dogfood sessions use `edit` mode with `allow_execute`, not `execute`. They write files the integrator must credit and commit, and only `edit`/`converge` sessions have enforced `owned_paths`.

## Shared Files

| File | Owner | Readers |
|---|---|---|
| `pyproject.toml`, `tests/conftest.py` | 01 | all code sessions (add tests in their own files; ask 01's summary for changes) |
| `src/genie_ontology_modeled_knowledge_sdk/__init__.py` | 01 | all |
| `docs/design/sdk-layout.md` | 01 | all |
| `templates/ontology-metric-views/**` | 06 | 09 (copies), 12 (reports template fixes) |
| `templates/ontology-genie-agents/**` | 07 | 09, 14, 15 |
| `templates/run/**` | 08 | 09 |
| `examples/tpch/ontology-metric-views/metric_views/**` | 11, then 16 | 12, 14 |
| `examples/tpch/ontology-metric-views/**` (rest) | 09, then 12 | 16 |
| `examples/tpch/ontology-genie-agents/agents/**` | 14, then 16 | 15 |
| `examples/tpch/ontology-genie-agents/**` (rest) | 09, then 14 (resources), 15 | 16 |
| `README.md`, `PROJECT_MEMORY.md`, L100 | 17 (build-time); planner before the build | all |
| `examples/tpch/*/.databricks/bundle/dev/variable-overrides.json` | **owner** (manual, gitignored) | 09, 12, 14, 15, 16 |

## Cross-Session Contracts

### Package and modules (`src/genie_ontology_modeled_knowledge_sdk/`)

| Module | Public API | Owner |
|---|---|---|
| `config` | `SdkConfig`, `load_config(path)`, `config_from_dict(d)`, `validate_config(d) -> list[str]`, `check_access(cfg, ws) -> list[str]`, `expand_tables(cfg, ws) -> list[str]` | 01 |
| `mv_yaml` | `load_mv(path)`, `substitute(text, params)`, `validate_mv(doc, name=) -> list[Finding]`, `render_ddl(doc_text, fq_name, params)`, CLI `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate <dir>` | 02 |
| `manifest` | `build_manifest(metric_views_dir)`, `write_manifest(...)`, `validate_manifest_json(list)` | 02 |
| `geniespace` | `plan_agents(mvs, max_per_agent=50)`, `build_space(plan, ...)`, `validate_space(doc)`, `write_domain_manifest(plans, path)`, `render_space_file(src, dst, params)`, CLI `python -m genie_ontology_modeled_knowledge_sdk.geniespace render <src> <dst> --params <json>` | 03 |
| `pages` | `parse_glossary(dir)`, `to_page_payload(term, domain_id=None)`, `upsert_pages(terms, client, dry_run=True)`, `PagesClient`, `RestPagesClient(ws)` | 04 |
| `benchmark` | `load_questions(path)`, `run_benchmark(space_id, questions, ws, timeout_s=120)`, `score(results)`, `write_results_md(summary, results, path)` | 04 |
| `scaffold` | `scaffold_project(cfg, target_dir, sdk_root, force=False) -> ScaffoldReport` | 09 |

### Metric view YAML parameters
`${source_catalog}`, `${source_schema}`, `${target_catalog}`, `${target_schema}`, substituted by `mv_yaml.substitute` at registration. Literal catalogs in `source:` are rule MV004 errors.

### `manifest.json` (forEach input)
```json
[{"name": "mv_tpch_revenue", "yaml_path": "metric_views/tpch_supply_chain/mv_tpch_revenue.yml", "domain": "tpch_supply_chain", "subdomain": "sales"}]
```
`yaml_path` is relative to the metric-views bundle root, and entries are sorted by `name`.

### Glossary term file (`docs/semantics/<term>.md`)
Front matter: `term`, `synonyms` (list), `domain`, `subdomain`, `related_terms` (list), `sources` (list of URLs). The body has sections Definition, Business context, Data usage.

### Benchmark questions (`docs/tuning/benchmark_questions.yml`)
List of `{id, question, expected_sql?, expected_answer?, tags}`.

### Data profile join table (`docs/data_profiles/data_model_summary.md`)
Columns: `left`, `right`, `keys`, `verified_cardinality` (`many_to_one` / `one_to_one` / `many_to_many`), `orphan_rate`, `query_used`.

### Run project layout (what `scaffold_project` creates, and the dogfood `examples/tpch/`)
```
<project>/
├── sdk_config.json
├── PROJECT_MEMORY.md
├── ontology-metric-views/      # from templates/ontology-metric-views (+ src/genie_ontology_modeled_knowledge_sdk_vendored/)
│   └── metric_views/<domain>/*.yml, manifest.json
├── ontology-genie-agents/      # from templates/ontology-genie-agents
│   └── agents/*.geniespace.json
└── docs/
    ├── plans/ (run kit: waves.json, INDEX.md, plans)
    ├── research/  semantics/  context/  data_profiles/
    ├── registration/  pages/  deployment/  tuning/
    └── domain_manifest.yml
```

### TPC-H dogfood config (example values)
`domain_name: tpch_supply_chain`; `source_tables`: `samples.tpch.{customer,orders,lineitem,part,partsupp,supplier,nation,region}`; `target_catalog: main`, `target_schema: ontology_tpch` (documented placeholders; the real dev catalog comes from overrides); `max_metric_views_per_agent: 50`.

## Dependency Graph

```
0-0  [01]
       |
0-1  [02] [03] [04] [05a] [05b]
       |    |          \   /
0-2  [06] [07]          [08]
        \   |           /
0-3        [09]  <- manual prereq: overrides files
           /  \
0-4    [10a]  [10b]
           \  /
0-5        [11]
            |
0-6        [12]  (deploy MV bundle)
           /  \
0-7     [13]  [14]
               |
0-8           [15]  (deploy agent bundle)
               |
0-9           [16]  (tune + re-register)
               |
0-10          [17]
```
