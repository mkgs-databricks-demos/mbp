# Run Plan Index — {{project_name}} ({{domain_name}})

## Overview

This is a genie-build-waves manifest that runs the Genie Ontology Modeled Knowledge SDK pipeline for one domain. It goes from Unity Catalog source tables plus supplemental business context to parameterized metric views, then UC Pages, curated Genie Agents, exhaustive MV-first tuning until accuracy flattens, and an independent report simulation.

* Manifest: [waves.json](waves.json) (`hybrid` workflow, branch `{{branch}}`, bundle target `{{bundle_target}}`, SDK `{{sdk_version}}`, waves `0`..`14`).
* Plans: [plans/](plans/).
* `build_root` = this project's root (the folder with `sdk_config.json`). The build branch is the manifest's top-level `branch` (also the job parameter).
* Approvals: `authorization_policy.monitor_may_authorize` covers `jobs.run_now`, `bundle.deploy`, `volume.write` and `workspace.write` on each session's `owned_assets`. Every deploying session names its project bundle in an explicit `bundle.deploy` authorization, and every session that runs `register_metric_views` has `jobs.run_now`.
* Skills: sessions load each SDK skill by its Unity Catalog id from `sdk_config.json` `skills`, falling back to `skills/<folder>/SKILL.md` in the SDK checkout. Sessions never run Git; the wave integrator is the only committer.
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
| `6` | Benchmark authoring | [10a, 10b, 10c](plans/10_benchmark_authoring.md) view group A, view group B, cross-view | edit + allow_execute | no |
| `7` | Benchmark baseline | [11](plans/11_benchmark_baseline.md) | edit + allow_execute + allow_deploy | `ontology-genie-agents` |
| `8`-`10` | Tuning iterations 1-3 (mandatory) | [12, 13, 14](plans/12_tuning_iteration.md) | edit + allow_execute + allow_deploy | both |
| `11`-`13` | Tuning iterations 4-6 (conditional; converged -> pass without change; asymptote gate on `13`) | [15, 16, 17](plans/12_tuning_iteration.md) | edit + allow_execute + allow_deploy | both |
| `14` | Independent report simulation | [18](plans/13_report_simulation.md) | edit + allow_execute | no |

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
| 10a / 10b / 10c | `docs/tuning/benchmark/{group_a,group_b,cross_view}.yml` + `_notes.md` | `ontology-tuning` |
| 11 | `docs/tuning/**`, `ontology-genie-agents/agents/**` | `ontology-tuning` |
| 12-17 | `docs/tuning/**`, `docs/semantics/**`, `docs/pages/**`, `ontology-metric-views/metric_views/**`, `ontology-genie-agents/agents/**` | `ontology-tuning` |
| 18 | `docs/evaluation/**` | — |

Owned paths are disjoint within each wave. Tuning sessions take over files from 02, 05, 07 and 08, which ran in earlier waves.

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
| `docs/registration/resolved_target.json` | 06 | 09, 11-17 | `{catalog, schema, warehouse_id}` from `bundle summary`; input to `geniespace render --params ... --check` |
| `docs/tuning/benchmark/*.yml` | 10a-10c | 11-17 | `[{id, question, expected_sql, tags}]` |
| `docs/tuning/accuracy_history.json` | 11-17 | 12-17 | baseline + one entry per iteration, tuning and holdout accuracy |
| `docs/tuning/tuning_plan_0N.md` | 11-16 | next iteration | failed tuning-split questions with category and ladder step |

SDK modules: `config` (01), `mv_yaml` + `manifest` (05, 12-17), `pages` (07), `geniespace` (08, 09, 11), `benchmark` (10-17). Projects use the installed SDK wheel `{{sdk_version}}` (registration wave `manual_prereqs` `P-wheel`); only a project scaffolded with vendor=True loads the vendored copy through `load_sdk()`.

## Required checks

| Wave | Check | Evidence |
|---|---|---|
| `3` | `registration_job` | the `register_metric_views` run is SUCCESS, after the build run started |
| `3` | `mv_smoke` | every view registered; smoke and cardinality tasks SUCCESS; installed wheel imported |
| `3` | `resolved_target` | `docs/registration/resolved_target.json` written |
| `5` | `agent_probe` | every agent answered with a SUCCEEDED query attachment |
| `6` | `benchmark_coverage`, `expected_sql_runs` | 100-498 questions, >= 12 per view, every measure/dimension, >= 25% cross-view; every expected_sql SUCCEEDED |
| `7` | `baseline_results`, `tuning_plan_01` | baseline entry after the build started; plan cites no holdout question |
| `8`-`12` | `iteration_0N`, `mv_first` (+ `next_plan` on `8`-`10`) | plan applied or converged; agent changes have exhaustion records |
| `13` | `iteration_06`, `asymptote`, `tuning_summary`, `mv_first` | `benchmark.asymptote` reached with >= 3 fix iterations |
| `14` | `report_simulation`, `ground_truth` | 4-5 reports graded against pre-registered ground truth |

Accuracy targets (tuning, report simulation 80%) are recorded, not gated. Wave `4` has a `manual_prereqs` entry for `sdk_config.json` `pages_domain_id`; without it session 07 ends `pass` with "publishing deferred". Live page upserts pass `domain_id` and `status=DRAFT` unless `pages_status` says otherwise.

Waves `2`-`5` and `7`-`13` also list both project bundles in `validate_bundles`, so the integrator runs `bundle validate --strict` on each.

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
6     [10a] [10b] [10c]  (benchmark authoring)
          \   |   /
7          [11]  (baseline, deploy agents)
            |
8-10   [12]->[13]->[14]  (mandatory iterations)
            |
11-13  [15]->[16]->[17]  (conditional iterations, asymptote gate)
            |
14         [18]  (independent report simulation)
```
