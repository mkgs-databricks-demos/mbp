# Run Plan Index — {{project_name}} ({{domain_name}})

## Overview

This is a genie-build-waves manifest that runs the Genie Ontology Modeled Knowledge SDK pipeline for one domain. It goes from Unity Catalog source tables plus supplemental business context to parameterized metric views, then UC Pages, curated Genie Agents and a tuning pass.

* Manifest: [waves.json](waves.json) (`hybrid` workflow, bundle target `{{bundle_target}}`, waves `0`..`6`).
* Plans: [plans/](plans/).
* `build_root` = this project's root (the folder with `sdk_config.json`). The build branch is a job parameter. Sessions never run Git; the wave integrator is the only committer.
* Workspace-specific values (catalog, warehouse, groups, ids) never go in committed files. The bundles read them from gitignored `.databricks/bundle/<target>/variable-overrides.json` files written by the owner.

## Wave Map

| Wave | Name | Sessions (parallel) | Mode | Deploys |
|---|---|---|---|---|
| `0` | Inputs check | [01](plans/01_inputs_check.md) | edit + allow_execute | no |
| `1` | Discovery | [02](plans/02_domain_research.md) research, [03](plans/03_supplemental_context.md) context, [04](plans/04_deep_eda.md) EDA | edit + allow_execute | no |
| `2` | Metric view synthesis | [05](plans/05_metric_view_synthesis.md) | edit + allow_execute | no |
| `3` | Registration | [06](plans/06_metric_view_registration.md) | edit + allow_execute + allow_deploy | `ontology-metric-views` |
| `4` | UC Pages + agent curation | [07](plans/07_uc_pages.md) pages, [08](plans/08_agent_curation.md) curation | edit + allow_execute | no |
| `5` | Agent deployment | [09](plans/09_agent_deployment.md) | edit + allow_execute + allow_deploy | `ontology-genie-agents` |
| `6` | Tuning | [10](plans/10_tuning.md) | edit + allow_execute + allow_deploy | both |

Waves run one after another, and sessions within a wave run in parallel. Each deploying wave has a single session (the single-writer rule).

## Ownership

| Session | Owned paths | Skill |
|---|---|---|
| 01 | `docs/inputs_report.md` | — |
| 02 | `docs/research/**`, `docs/semantics/**` | `ontology-domain-research` |
| 03 | `docs/context/**` | `ontology-context-extraction` |
| 04 | `docs/data_profiles/**` | `ontology-deep-eda` |
| 05 | `ontology-metric-views/metric_views/**` | `ontology-mv-synthesis` |
| 06 | `docs/registration/**` | — |
| 07 | `docs/pages/**` | (platform `discover-pages`) |
| 08 | `ontology-genie-agents/agents/**`, `ontology-genie-agents/resources/**`, `docs/domain_manifest.yml` | `ontology-agent-curation` |
| 09 | `docs/deployment/**` | — |
| 10 | `docs/tuning/**`, `ontology-metric-views/metric_views/**`, `ontology-genie-agents/agents/**` | `ontology-tuning` |

Owned paths are disjoint within each wave. Session 10 takes over files from 05 and 08, which ran in earlier waves.

## Contracts

| Artifact | Producer | Consumers | Shape |
|---|---|---|---|
| `docs/inputs_report.md` | 01 | all | sections Config, Source tables, Supplemental inputs, Access problems, Date |
| `docs/semantics/<term>.md` | 02 | 05, 07, 10 | front matter `term`, `synonyms`, `domain`, `subdomain`, `related_terms`, `sources`; body Definition / Business context / Data usage |
| `docs/context/glossary_candidates/*.md` | 03 | 07 | same as semantics |
| `docs/data_profiles/data_model_summary.md` | 04 | 05, 08 | join table `left`, `right`, `keys`, `verified_cardinality`, `orphan_rate`, `query_used` |
| `ontology-metric-views/metric_views/manifest.json` | 05 (10) | 06, 08 | `[{name, yaml_path, domain, subdomain}]` sorted by `name` |
| `docs/registration/registration_results.md` | 06 | 07, 08 | run id + state, per-view registered, smoke / cardinality results |
| `ontology-genie-agents/agents/*.geniespace.json` | 08 (10) | 09 | tokenized `${target_catalog}.${target_schema}.<view>` |
| `docs/deployment/deployment_results.md` | 09 | 10 | per agent: resource key, space id, probe result |
| `docs/tuning/benchmark_questions.yml` | 10 | 10 | `[{id, question, expected_sql?, expected_answer?, tags}]`, tag `agent:<name>` |

SDK modules: `config` (01), `mv_yaml` + `manifest` (05, 10), `pages` (07), `geniespace` (08), `benchmark` (10). Projects import them from the vendored copy under `ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored/`.

## Required checks

| Wave | Check | Evidence |
|---|---|---|
| `3` | `registration_job` | the `register_metric_views` run is SUCCESS, after the build run started |
| `3` | `mv_smoke` | every view registered; smoke and cardinality tasks SUCCESS |
| `5` | `agent_probe` | every agent answered with a SUCCEEDED query attachment |
| `6` | `benchmark_results` | final run has every agent at >= 70% accuracy |

Waves `2`-`6` also list both project bundles in `validate_bundles`, so the integrator runs `bundle validate --strict` on each.

## Dependency Graph

```
0  [01]
    |
1  [02] [03] [04]
      \  |  /
2      [05]
        |
3      [06]  (deploy + run metric views bundle)
       /  \
4   [07]  [08]
            |
5          [09]  (deploy agents bundle)
            |
6          [10]  (benchmark, tune, redeploy)
```
