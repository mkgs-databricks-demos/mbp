# Using the Genie Ontology SDK

This guide runs the SDK pipeline end to end for one domain: scaffold a project, set the workspace overrides, run the pipeline with a genie-build-waves instance and the run kit, and check the outputs of each wave. The [TPC-H example](../examples/tpch/README.md) is a complete project produced this way by build-0.

Build-0 dogfooded the SDK through its own manifest ([docs/plans/waves.json](plans/waves.json)), not through the run kit. Known run-kit gaps are listed in [build-1 request R3](plans/build-1/REQUESTS.md) and in [build-0 observations](build-0-observations.md); read them before a customer run.

## 1. Prerequisites

* A Unity Catalog workspace with serverless compute (jobs and notebooks) and a SQL warehouse.
* Genie (Genie Agents) enabled, and Discover domains if you want UC Pages.
* A target catalog where you can create a schema and views. Source tables need `SELECT` only; they are never written.
* Databricks CLI with Declarative Automation Bundles support for `genie_spaces` and `engine: direct` (build-0 used v1.27.0).
* Python 3.10+ with `pyyaml` and `jsonschema` for the local CLIs and tests (`pip install pyyaml jsonschema pytest`).
* A Git folder for the project, on a feature branch (never `main`).
* A [genie-build-waves](../../genie-build-waves/README.md) checkout, to deploy a build instance for the run.
* The six SDK skills in `skills/` available to the build's run-as user (see step 4).

## 2. Scaffold a project with the init notebook

Open the `notebooks/init_ontology_project` notebook from the SDK folder on serverless and run it top to bottom:

1. The first cell installs the dependencies (`databricks-sdk`, `pyyaml`, `jsonschema`) and restarts Python.
2. Fill the widgets: one per `sdk_config` field (`domain_name`, `source_tables` or catalogs/schemas, `target_catalog`, `target_schema`, `domain_context`, optional inputs) plus the scaffold options. Leave `target_dir` empty for a check-only run.
3. The notebook runs `config.validate_config` and `config.check_access`. Fix every reported problem (for example a target catalog you cannot use) before you scaffold.
4. Set `target_dir` to the project folder and run the scaffold cell. It calls `scaffold.scaffold_project` and prints a JSON summary of written, unchanged and skipped files.

The same is available from a terminal at the SDK root:

```bash
PYTHONPATH=src python -m genie_ontology_sdk.scaffold --config <project>/sdk_config.json --target <project> --project-name <name>
```

The scaffold writes:

| Path in the project | Contents |
|---|---|
| `sdk_config.json` | validated inputs |
| `PROJECT_MEMORY.md` | run memory starter |
| `ontology-metric-views/` | metric view bundle (DAB 1) with vendored SDK modules under `src/genie_ontology_sdk_vendored/` |
| `ontology-genie-agents/` | Genie Agent bundle (DAB 2) |
| `docs/plans/` | run kit: `waves.json`, `INDEX.md`, `README.md`, `plans/*.md` |
| `docs/{research,semantics,context,data_profiles,registration,pages,deployment,tuning,sessions}/` | empty output folders |

Re-running the scaffold writes nothing unless `force` is set, and it never touches `.databricks/` or `.rendered/`.

## 3. Write the overrides files

Both bundles read workspace-specific values from gitignored files. Write them by hand and never commit them:

| File | Keys |
|---|---|
| `ontology-metric-views/.databricks/bundle/<target>/variable-overrides.json` | `catalog`, `warehouse_id` |
| `ontology-genie-agents/.databricks/bundle/<target>/variable-overrides.json` | `catalog`, `schema`, `warehouse_id`, `curator_group` |

The agents bundle `schema` must be the schema DAB 1 actually registers into. In the `dev` target that is the dev-prefixed schema (`dev_<user>_<schema_name>`, `schema_name` defaults to `ontology`), not the `target_schema` in `sdk_config.json`. A mismatch blocked build-0 wave 0-8 once; check it with `information_schema.tables` after registration. Variable details are in the [metric views template README](../templates/ontology-metric-views/README.md) and the [Genie Agents template README](../templates/ontology-genie-agents/README.md).

Check both bundles before the run:

```bash
cd <project>/ontology-metric-views && databricks bundle validate --strict --target dev
cd ../ontology-genie-agents
PYTHONPATH=<sdk>/src python -m genie_ontology_sdk.geniespace render agents .rendered --params .databricks/bundle/dev/variable-overrides.json
databricks bundle validate --strict --target dev
```

The render step is needed because the bundle CLI does not interpolate `${...}` inside `genie_spaces` space files. Agent files stay tokenized (`${target_catalog}.${target_schema}.<view>`); `.rendered/` is gitignored.

## 4. Deploy genie-build-waves for the run

Commit the scaffolded files on the feature branch, then follow the [run kit README](../templates/run/README.md):

1. Deploy a genie-build-waves instance for the project ([genie-build-waves README](../../genie-build-waves/README.md)) with:
   * `build_root` = the project root (the folder with `sdk_config.json`)
   * `manifest_path` = `<build_root>/docs/plans/waves.json`
   * `branch` = the feature branch
2. Make the SDK skills loadable by build sessions: copy `skills/ontology-*` into the run-as user's workspace skills folder, or use `skills` overrides in the manifest. Publishing them to Unity Catalog is build-1 request R1.
3. Run setup and check that `validate_manifest` reports 0 errors. Review the rendered session authorizations. Deploying sessions need `bundle.deploy` on their bundle, and the registration and tuning sessions also need a run of `register_metric_views` (in build-0, deploy approval alone was not enough).
4. UC Pages need an existing Discover domain. If there is none, the pages session stops blocked by design; create or choose a domain first, or publish pages later from the owner cell in `docs/pages/pages_registration.md`.
5. Start the build job and watch each wave gate. Review and merge the feature branch PR yourself; sessions never push to `main`.

To redo part of a run, start the job with `only` set to the wave task keys you need (for example the deployment and tuning waves after a metric view fix).

## 5. Expected outputs per wave

Wave ids and sessions are those of the run kit ([run kit INDEX](../templates/run/INDEX.md)). The last column links the matching TPC-H output from build-0.

| Wave | Session(s) | Outputs | Gate evidence | TPC-H example |
|---|---|---|---|---|
| `0` Inputs check | 01 | `docs/inputs_report.md` | config valid, sources readable | `examples/tpch/sdk_config.json` |
| `1` Discovery | 02, 03, 04 | `docs/research/*.md`, `docs/semantics/<term>.md`, `docs/context/**`, `docs/data_profiles/*.md` + `data_model_summary.md` | research sources, glossary parses, verified join cardinalities | [data model summary](../examples/tpch/docs/data_profiles/data_model_summary.md) |
| `2` Metric view synthesis | 05 | `ontology-metric-views/metric_views/<domain>/*.yml` + `manifest.json` | `mv_yaml validate` exit 0, no literal source names | [manifest.json](../examples/tpch/ontology-metric-views/metric_views/manifest.json) |
| `3` Registration | 06 | registered metric views; `docs/registration/registration_results.md` | `registration_job`, `mv_smoke` | [registration results](../examples/tpch/docs/registration/registration_results.md) |
| `4` Pages + curation | 07, 08 | UC Pages; `docs/pages/pages_registration.md`; `ontology-genie-agents/agents/*.geniespace.json`, `resources/genie_agents.yml`, `docs/domain_manifest.yml` | `validate_space` 0 errors, tokenized agent files | [pages registration](../examples/tpch/docs/pages/pages_registration.md), [domain manifest](../examples/tpch/docs/domain_manifest.yml) |
| `5` Agent deployment | 09 | deployed Genie Agents; deployment results with probe answers | `agent_probe` | [agent validation](../examples/tpch/docs/deployment/agent_validation.md) |
| `6` Tuning | 10 | `docs/tuning/benchmark_questions.yml`, `benchmark_results.md`, `tuning_plan.md`; re-registered views if changed | `benchmark_results` (>= 70% accuracy) | [benchmark results](../examples/tpch/docs/tuning/benchmark_results.md), [tuning plan](../examples/tpch/docs/tuning/tuning_plan.md) |

Build-0 TPC-H results: 23 glossary terms, 8 table profiles with 10 verified joins, 7 metric views registered with smoke and cardinality pass, 1 Genie Agent with 3/3 probes, baseline benchmark 93.3% on 15 questions. UC Pages were not written (no Discover domain; dry run only).

## 6. Promote

Only `catalog`, `warehouse_id` and the deployment target change between environments. Add a target to each bundle, write its overrides file, and deploy with `--target <env>`. Users other than the owner need `USE CATALOG`, `USE SCHEMA` and `SELECT` on the metric views to use an agent.
